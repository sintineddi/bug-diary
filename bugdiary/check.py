from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from . import diffs
from .card import Card
from .diffs import FileDiff, Hit
from .memory import Diary
from .ollama import Ollama
from .prompts import COMPARE_SCHEMA, COMPARE_SYSTEM, DESCRIBE_SCHEMA, DESCRIBE_SYSTEM

CHANGE_BUDGET = 30_000
VERDICTS = ("repeats", "protected", "unrelated", "unclear")
DEFAULT_TOP = 3
DEFAULT_FLOOR = 0.0
EMBED_BATCH = 32


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


@dataclass
class Report:
    project: str
    files: list[str]
    summary: str = ""
    behaviors: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    diary_size: int = 0
    seconds: float = 0.0

    @property
    def alerts(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.verdict == "repeats"]


def code_files(files: list[FileDiff]) -> list[FileDiff]:
    return [file for file in files if file.role == "code" and file.hunks]


def cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    norm = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return dot / norm if norm else 0.0


def ensure_vectors(llm: Ollama, diary: Diary, cards: list[Card]) -> dict[int, list[float]]:
    vectors = diary.vectors(llm.embed_model)
    missing = [card for card in cards if card.id not in vectors]
    for start in range(0, len(missing), EMBED_BATCH):
        batch = missing[start : start + EMBED_BATCH]
        for card, vector in zip(batch, llm.embed([card.document() for card in batch])):
            diary.put_vector(card.id, llm.embed_model, vector)
            vectors[card.id] = vector
    return vectors


def query_text(text: str) -> str:
    return f"task: search result | query: {text}"


def retrieve(
    llm: Ollama, diary: Diary, queries: list[str], top: int = DEFAULT_TOP, floor: float = DEFAULT_FLOOR
) -> list[tuple[Card, float]]:
    cards = diary.cards()
    queries = [query for query in queries if query.strip()]
    if not cards or not queries:
        return []
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
    return scored[:top]


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


def compare_prompt(card: Card, change: str, project: str) -> str:
    elsewhere = ""
    if card.project != project:
        elsewhere = " The diary card comes from another project: names and languages may differ, compare mechanisms."
    return f"DIARY CARD\n{card_text(card)}\n\nCHANGE UNDER REVIEW · project {project}.{elsewhere}\n{change}"


def strings(value: object) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def compare(llm: Ollama, card: Card, score: float, change: str, files: list[FileDiff], project: str) -> Finding:
    raw = llm.chat_json(COMPARE_SYSTEM, compare_prompt(card, change, project), COMPARE_SCHEMA)
    verdict = raw.get("verdict") if raw.get("verdict") in VERDICTS else "unclear"
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
    )


def describe(llm: Ollama, change: str) -> tuple[str, list[str]]:
    raw = llm.chat_json(DESCRIBE_SYSTEM, change, DESCRIBE_SCHEMA)
    return str(raw.get("summary") or "").strip(), strings(raw.get("behaviors"))[:6]


def check(
    llm: Ollama,
    diary: Diary,
    files: list[FileDiff],
    project: str,
    top: int = DEFAULT_TOP,
    floor: float = DEFAULT_FLOOR,
) -> Report:
    started = time.monotonic()
    code = code_files(files)
    report = Report(project, [file.path for file in code], diary_size=len(diary.cards()))
    if not code or not report.diary_size:
        return report
    change = diffs.render(code, CHANGE_BUDGET)
    report.summary, report.behaviors = describe(llm, change)
    for card, score in retrieve(llm, diary, [report.summary, *report.behaviors], top, floor):
        report.findings.append(compare(llm, card, score, change, code, project))
    report.seconds = time.monotonic() - started
    return report
