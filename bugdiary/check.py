from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from . import diffs
from .card import Card
from .diffs import FileDiff, Hit
from .memory import Diary
from .ollama import AnswerError, Ollama
from .prompts import COMPARE_SCHEMA, COMPARE_SYSTEM, DESCRIBE_SCHEMA, DESCRIBE_SYSTEM, FAMILY_SCHEMA, FAMILY_SYSTEM

CHANGE_BUDGET = 30_000
VERDICTS = ("repeats", "protected", "unrelated", "unclear")
STRENGTH = {"repeats": 3, "protected": 2, "unclear": 1, "unrelated": 0}
DEFAULT_TOP = 3
DEFAULT_FLOOR = 0.0
EMBED_BATCH = 32
QUERY_FALLBACK = 2000
FAMILY_FLOOR = 0.45
FAMILY_SIZE = 6


@dataclass
class Finding:
    card: Card
    score: float
    verdict: str
    reason: str
    evidence: list[Hit] = field(default_factory=list)
    protection: list[Hit] = field(default_factory=list)
    check: str = ""
    test: str = ""
    downgraded: str = ""
    family: list[Card] = field(default_factory=list)
    answered: bool = True


@dataclass
class Report:
    project: str
    files: list[str]
    summary: str = ""
    behaviors: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    partial: list[str] = field(default_factory=list)
    incomplete: list[str] = field(default_factory=list)
    diary_size: int = 0
    seconds: float = 0.0

    @property
    def alerts(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.verdict == "repeats"]


def code_files(files: list[FileDiff]) -> list[FileDiff]:
    return [file for file in files if file.role == "code" and file.hunks]


def batches(files: list[FileDiff], budget: int = CHANGE_BUDGET) -> list[list[FileDiff]]:
    groups: list[list[FileDiff]] = []
    for file in files:
        if groups and not diffs.fit(groups[-1] + [file], budget)[1]:
            groups[-1].append(file)
        else:
            groups.append([file])
    return groups


def cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    norm = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return dot / norm if norm else 0.0


def ensure_vectors(llm: Ollama, diary: Diary, cards: list[Card]) -> dict[int, list[float]]:
    stored = diary.vectors(llm.embed_model)
    vectors = {}
    for card in cards:
        digest, vector = stored.get(card.id, ("", []))
        if digest == card.digest():
            vectors[card.id] = vector
    missing = [card for card in cards if card.id not in vectors]
    for start in range(0, len(missing), EMBED_BATCH):
        batch = missing[start : start + EMBED_BATCH]
        for card, vector in zip(batch, llm.embed([card.document() for card in batch])):
            diary.put_vector(card.id, llm.embed_model, vector, card.digest())
            vectors[card.id] = vector
    return vectors


def query_text(text: str) -> str:
    return f"task: search result | query: {text}"


def rank(
    llm: Ollama, diary: Diary, queries: list[str], floor: float = DEFAULT_FLOOR
) -> tuple[list[Card], dict[int, list[float]], list[tuple[Card, float]]]:
    cards = diary.cards()
    queries = [query for query in queries if query.strip()]
    if not cards or not queries:
        return cards, {}, []
    vectors = ensure_vectors(llm, diary, cards)
    asked = llm.embed([query_text(query) for query in queries])
    scored = []
    for card in cards:
        vector = vectors.get(card.id)
        if vector is not None:
            score = max(cosine(query, vector) for query in asked)
            if score >= floor:
                scored.append((card, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return cards, vectors, scored


def retrieve(
    llm: Ollama, diary: Diary, queries: list[str], top: int = DEFAULT_TOP, floor: float = DEFAULT_FLOOR
) -> list[tuple[Card, float]]:
    return rank(llm, diary, queries, floor)[2][:top]


def kin(card: Card, other: Card, vectors: dict[int, list[float]]) -> float:
    if card.id not in vectors or other.id not in vectors:
        return 0.0
    return cosine(vectors[card.id], vectors[other.id])


def family_of(card: Card, cards: list[Card], vectors: dict[int, list[float]], members: list[Card]) -> list[Card]:
    near = sorted((other for other in cards if other.id != card.id), key=lambda other: -kin(card, other, vectors))
    chosen = [member for member in members if member.id != card.id]
    for other in near:
        if len(chosen) >= FAMILY_SIZE or kin(card, other, vectors) < FAMILY_FLOOR:
            break
        if all(other.id != member.id for member in chosen):
            chosen.append(other)
    return chosen[:FAMILY_SIZE]


def kinds_of_bug(
    ranked: list[tuple[Card, float]], vectors: dict[int, list[float]]
) -> list[tuple[Card, float, list[Card]]]:
    groups: list[tuple[Card, float, list[Card]]] = []
    for card, score in ranked:
        home = next((group for group in groups if kin(group[0], card, vectors) >= FAMILY_FLOOR), None)
        if home is None:
            groups.append((card, score, []))
        else:
            home[2].append(card)
    return groups


def card_text(card: Card) -> str:
    lines = [
        f"{card.label} · project {card.project} · fixed {card.fixed_at[:10] or 'on an unknown date'}",
        f"Pattern: {card.pattern}",
        f"Symptom: {card.symptom.text}",
        f"Root cause: {card.root_cause.text}",
        f"Fix: {card.fix}",
        f"Guard: {card.guard}",
        f"Lesson: {card.lesson}",
    ]
    if card.regression:
        given, when, then = (card.regression.get(key, "") for key in ("given", "when", "then"))
        lines.append(f"Regression test: given {given}; when {when}; then {then}")
    return "\n".join(lines)


def kin_text(card: Card) -> str:
    return f"- {card.label} · project {card.project} · fixed {card.fixed_at[:10] or '?'}: {card.pattern}. Guard: {card.guard} Lesson: {card.lesson}"


def compare_prompt(card: Card, change: str, project: str) -> str:
    elsewhere = ""
    if card.project != project:
        elsewhere = " The diary card comes from another project: names and languages may differ, compare mechanisms."
    return f"DIARY CARD\n{card_text(card)}\n\nCHANGE UNDER REVIEW · project {project}.{elsewhere}\n{change}"


def family_prompt(card: Card, change: str, project: str, family: list[Card]) -> str:
    elsewhere = ""
    if card.project != project or any(other.project != project for other in family):
        elsewhere = " Some diary cards come from other projects: names and languages may differ, compare mechanisms."
    others = ""
    if family:
        others = "\n\nOTHER FIXES OF THE SAME KIND OF BUG\n" + "\n".join(kin_text(other) for other in family)
    return f"DIARY CARD\n{card_text(card)}{others}\n\nCHANGE UNDER REVIEW · project {project}.{elsewhere}\n{change}"


def strings(value: object) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def compare(
    llm: Ollama,
    card: Card,
    score: float,
    change: str,
    files: list[FileDiff],
    project: str,
    family: list[Card] | None = None,
) -> Finding:
    if family is None:
        system, schema, prompt = COMPARE_SYSTEM, COMPARE_SCHEMA, compare_prompt(card, change, project)
    else:
        system, schema, prompt = FAMILY_SYSTEM, FAMILY_SCHEMA, family_prompt(card, change, project, family)
    family = family or []
    try:
        raw = llm.chat_json(system, prompt, schema)
    except AnswerError as error:
        return Finding(card, score, "unclear", "", downgraded=str(error), family=family, answered=False)
    verdict = raw.get("verdict") if raw.get("verdict") in VERDICTS else "unclear"
    shown = {candidate.label: candidate for candidate in [card, *family]}
    named = [
        shown[label] for label in (item.strip().upper() for item in strings(raw.get("precedents"))) if label in shown
    ]
    if verdict == "repeats" and named:
        card, family = named[0], [candidate for candidate in [card, *family] if candidate.id != named[0].id]
    evidence = diffs.find_lines(strings(raw.get("evidence")), files, "+-")
    protection = diffs.find_lines(strings(raw.get("protection")), files, "+ ")
    downgraded = ""
    if verdict == "repeats" and not evidence:
        verdict, downgraded = "unclear", "the lines it quoted are not in the change"
    elif verdict == "protected" and not protection:
        verdict, downgraded = "unclear", "the protection it quoted is not in the change"
    return Finding(
        card=card,
        score=score,
        verdict=verdict,
        reason=str(raw.get("reason") or "").strip(),
        evidence=evidence,
        protection=protection,
        check=str(raw.get("check") or "").strip(),
        test=str(raw.get("test") or "").strip(),
        downgraded=downgraded,
        family=family,
    )


def describe(llm: Ollama, change: str) -> tuple[str, list[str]]:
    try:
        raw = llm.chat_json(DESCRIBE_SYSTEM, change, DESCRIBE_SCHEMA)
    except AnswerError:
        return "", [change[:QUERY_FALLBACK]]
    return str(raw.get("summary") or "").strip(), strings(raw.get("behaviors"))[:6]


def check(
    llm: Ollama,
    diary: Diary,
    files: list[FileDiff],
    project: str,
    top: int = DEFAULT_TOP,
    floor: float = DEFAULT_FLOOR,
    by_kind: bool = False,
) -> Report:
    started = time.monotonic()
    code = code_files(files)
    report = Report(project, [file.path for file in code], diary_size=len(diary.cards()))
    if not code or not report.diary_size:
        return report
    strongest: dict[int, Finding] = {}
    unanswered: set[str] = set()
    summaries = []
    for group in batches(code):
        change, unread = diffs.fit(group, CHANGE_BUDGET)
        report.partial += unread
        summary, behaviors = describe(llm, change)
        summaries.append(summary)
        report.behaviors += behaviors
        cards, vectors, ranked = rank(llm, diary, [summary, *behaviors], floor)
        if by_kind:
            pending = [
                (card, score, family_of(card, cards, vectors, members))
                for card, score, members in kinds_of_bug(ranked[:top], vectors)
            ]
        else:
            pending = [(card, score, None) for card, score in ranked[:top]]
        for card, score, family in pending:
            finding = compare(llm, card, score, change, group, project, family)
            if not finding.answered:
                unanswered.add(finding.card.label)
            if family is None and finding.verdict == "repeats":
                finding.family = family_of(finding.card, cards, vectors, [])
            known = strongest.get(finding.card.id)
            if known is None or STRENGTH[finding.verdict] > STRENGTH[known.verdict]:
                strongest[finding.card.id] = finding
    report.incomplete = sorted(unanswered)
    report.summary = " ".join(summary for summary in summaries if summary)
    report.findings = sorted(strongest.values(), key=lambda finding: (-STRENGTH[finding.verdict], -finding.score))
    report.seconds = time.monotonic() - started
    return report
