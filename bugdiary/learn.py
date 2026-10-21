from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

from . import diffs, git
from .card import Card, Claim
from .diffs import FileDiff
from .memory import Diary
from .ollama import Ollama, OllamaError
from .prompts import LEARN_SCHEMA, LEARN_SYSTEM

SOURCES = ("message", "notes", "changelog", "tests", "code")
STATED_SOURCES = ("message", "notes", "changelog", "tests")
HEADINGS = {"message": "MESSAGE", "notes": "NOTES", "changelog": "CHANGELOG", "tests": "TESTS", "code": "CODE"}
CODE_BUDGET = 36_000
TEST_BUDGET = 14_000
NOTES_BUDGET = 8_000
SHORTEST_QUOTE = 3
QUOTE_RATIO = 0.9
MAX_IDENTIFIERS = 6
WORD = re.compile(r"\w+")


class LearnError(RuntimeError):
    pass


@dataclass
class Note:
    kind: str
    title: str
    text: str
    ref: str = ""


@dataclass
class Fix:
    project: str
    revision: str
    fixed_at: str
    message: str
    files: list[FileDiff]
    notes: list[Note] = field(default_factory=list)

    def by_role(self, *roles: str) -> list[FileDiff]:
        return [file for file in self.files if file.role in roles]


@dataclass
class Learned:
    card: Card
    is_bug_fix: bool
    reason: str
    seconds: float


def from_git(repo: Path, rev: str, project: str) -> Fix:
    base, head, commits = git.fix_range(repo, rev)
    if len(commits) == 1:
        revision, message = head, commits[0].message
    else:
        revision = f"{base}..{head}"
        message = "\n\n".join(f"{item.sha[:8]} {item.message}" for item in commits)
    return Fix(project, revision, commits[-1].date, message, diffs.parse(git.diff(repo, base, head)))


def source_texts(fix: Fix, include: tuple[str, ...] = SOURCES) -> dict[str, str]:
    texts = {}
    if "message" in include and fix.message.strip():
        texts["message"] = fix.message.strip()
    if "notes" in include and fix.notes:
        texts["notes"] = "\n\n".join(note_text(note) for note in fix.notes)[:NOTES_BUDGET]
    changelog = [line.text.strip() for file in fix.by_role("notes") for line in file.lines("+") if line.text.strip()]
    if "changelog" in include and changelog:
        texts["changelog"] = "\n".join(changelog)[:NOTES_BUDGET]
    if "tests" in include and fix.by_role("test"):
        texts["tests"] = diffs.render(fix.by_role("test"), TEST_BUDGET)
    if "code" in include and fix.by_role("code"):
        texts["code"] = diffs.render(fix.by_role("code"), CODE_BUDGET)
    return texts


def note_text(note: Note) -> str:
    heading = f"{note.kind} {note.ref}".strip()
    title = f": {note.title}" if note.title else ""
    return f"{heading}{title}\n{note.text.strip()}"


def prompt(fix: Fix, texts: dict[str, str]) -> str:
    revision = "..".join(part[:8] for part in fix.revision.split(".."))
    parts = [f"Project: {fix.project}\nFix: {revision}, {fix.fixed_at[:10] or 'date unknown'}"]
    parts.extend(f"[{HEADINGS[name]}]\n{texts[name]}" for name in SOURCES if name in texts)
    return "\n\n".join(parts)


def searchable(name: str, text: str) -> str:
    return re.sub(r"(?m)^[+\- ]", "", text) if name in ("tests", "code") else text


def words(text: str) -> list[tuple[str, int, int]]:
    return [(match.group().lower(), match.start(), match.end()) for match in WORD.finditer(text)]


def excerpt(quote: str, text: str) -> str | None:
    wanted = [word for word, _, _ in words(quote)]
    if len(wanted) < SHORTEST_QUOTE:
        return None
    found = words(text)
    tokens = [word for word, _, _ in found]
    longest = SequenceMatcher(None, tokens, wanted, autojunk=False).find_longest_match(0, len(tokens), 0, len(wanted))
    if longest.size == 0:
        return None
    anchor = longest.a - longest.b
    spans = {
        (max(0, anchor + shift), min(len(tokens), anchor + shift + len(wanted) + grow))
        for shift in (-1, 0, 1)
        for grow in (-1, 0, 1)
    }
    ratio, first, last = max(
        (SequenceMatcher(None, tokens[first:last], wanted, autojunk=False).ratio(), first, last)
        for first, last in spans
        if last > first
    )
    if ratio < QUOTE_RATIO:
        return None
    return re.sub(r"\s+", " ", text[found[first][1] : found[last - 1][2]]).strip()


def locate(quote: str, texts: dict[str, str], preferred: str) -> tuple[str, str] | None:
    fragments = [part for part in re.split(r"\.\.\.|\u2026", quote) if part.strip()]
    order = [preferred] if preferred in STATED_SOURCES else []
    order += [name for name in STATED_SOURCES if name != preferred]
    for name in order:
        if name not in texts or not fragments:
            continue
        pieces = [excerpt(fragment, searchable(name, texts[name])) for fragment in fragments]
        if all(pieces):
            return name, " … ".join(pieces)
    return None


def ground(raw: object, texts: dict[str, str], rejected: list[str]) -> Claim:
    raw = raw if isinstance(raw, dict) else {}
    text = str(raw.get("text") or "").strip()
    basis = str(raw.get("basis") or "")
    quote = str(raw.get("quote") or "").strip()
    if not text or text.lower() == "unknown" or basis == "unknown":
        return Claim("unknown", "unknown", "none", "")
    preferred = str(raw.get("source") or "")
    found = locate(quote, texts, preferred) if quote else None
    if found:
        return Claim(text, "stated", *found)
    if basis == "stated":
        rejected.append(quote or text)
    copied = locate(text, texts, preferred)
    if copied:
        return Claim(text, "stated", *copied)
    return Claim(text, "inferred", "code", "")


def keep_identifiers(names: object, fix: Fix) -> tuple[list[str], list[str]]:
    headers = [hunk.header for file in fix.files for hunk in file.hunks]
    haystack = "\n".join(headers + [line.text for file in fix.files for line in file.lines()])
    kept: list[str] = []
    dropped: list[str] = []
    for name in names if isinstance(names, list) else []:
        name = str(name).strip().strip("`'\"")
        if not name or name in kept:
            continue
        if 2 <= len(name) <= 80 and name in haystack and len(kept) < MAX_IDENTIFIERS:
            kept.append(name)
        else:
            dropped.append(name)
    return kept, dropped


def regression_of(raw: object, has_tests: bool) -> dict | None:
    if not has_tests or not isinstance(raw, dict):
        return None
    parts = {key: str(raw.get(key) or "").strip() for key in ("given", "when", "then")}
    return parts if parts["then"] else None


def text_of(raw: dict, key: str) -> str:
    return re.sub(r"\s+", " ", str(raw.get(key) or "")).strip()


def learn(llm: Ollama, fix: Fix, origin: str = "unknown", include: tuple[str, ...] = SOURCES) -> Learned:
    texts = source_texts(fix, include)
    if "code" not in texts and "tests" not in texts:
        raise LearnError(f"{fix.revision[:8]} changes no code to learn from")
    seconds_before = llm.seconds()
    raw = llm.chat_json(LEARN_SYSTEM, prompt(fix, texts), LEARN_SCHEMA)
    ignored = ""
    if "message" in texts and raw.get("message_matches") in ("no", "partly"):
        ignored = text_of(raw, "message_mismatch") or "it describes another change"
        texts = {name: text for name, text in texts.items() if name != "message"}
        raw = llm.chat_json(LEARN_SYSTEM, prompt(fix, texts), LEARN_SCHEMA)
    rejected: list[str] = []
    identifiers, dropped = keep_identifiers(raw.get("identifiers"), fix)
    card = Card(
        project=fix.project,
        revision=fix.revision,
        fixed_at=fix.fixed_at,
        origin=origin,
        symptom=ground(raw.get("symptom"), texts, rejected),
        root_cause=ground(raw.get("root_cause"), texts, rejected),
        pattern=text_of(raw, "pattern"),
        fix=text_of(raw, "fix"),
        guard=text_of(raw, "guard"),
        lesson=text_of(raw, "lesson"),
        regression=regression_of(raw.get("regression"), "tests" in texts),
        identifiers=identifiers,
        files=[file.path for file in fix.by_role("code")],
        test_files=[file.path for file in fix.by_role("test")],
        evidence={
            "sources": [name for name in SOURCES if name in texts],
            "notes": [{"kind": note.kind, "title": note.title, "ref": note.ref} for note in fix.notes]
            if "notes" in texts
            else [],
            "tests_executed": False,
            "rejected_quotes": rejected,
            "dropped_identifiers": dropped,
            "message_ignored": ignored,
        },
        model=llm.model,
        learned_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    is_bug_fix = raw.get("is_bug_fix") is not False
    return Learned(card, is_bug_fix, text_of(raw, "not_a_bug_fix_reason"), llm.seconds() - seconds_before)


def remember(diary: Diary, llm: Ollama, card: Card) -> str | None:
    diary.save(card)
    try:
        vector = llm.embed([card.document()])[0]
    except OllamaError as error:
        return str(error)
    diary.put_vector(card.id, llm.embed_model, vector, card.digest())
    return None
