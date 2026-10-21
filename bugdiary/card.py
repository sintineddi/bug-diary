from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

ORIGINS = ("production", "production-incident", "pre-production", "regression", "unknown")


@dataclass
class Claim:
    text: str
    basis: str = "unknown"
    source: str = "none"
    quote: str = ""

    @property
    def known(self) -> bool:
        return self.basis != "unknown" and self.text.strip().lower() not in ("", "unknown")


@dataclass
class Card:
    project: str
    revision: str
    fixed_at: str
    origin: str
    symptom: Claim
    root_cause: Claim
    pattern: str
    fix: str
    guard: str
    lesson: str
    regression: dict | None = None
    identifiers: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    test_files: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)
    model: str = ""
    learned_at: str = ""
    id: int | None = None

    @property
    def label(self) -> str:
        return label(self.id)

    @property
    def short_revision(self) -> str:
        return "..".join(part[:8] for part in self.revision.split(".."))

    def body(self) -> dict:
        data = asdict(self)
        for key in ("id", "project", "revision", "fixed_at", "origin", "model", "learned_at"):
            data.pop(key)
        return data

    def document(self) -> str:
        return f"title: {self.pattern} | text: {self.root_cause.text} {self.lesson} {self.guard}"

    @classmethod
    def from_row(cls, row: dict, body: dict) -> Card:
        return cls(
            id=row["id"],
            project=row["project"],
            revision=row["revision"],
            fixed_at=row["fixed_at"] or "",
            origin=row["origin"],
            model=row["model"],
            learned_at=row["learned_at"],
            symptom=Claim(**body["symptom"]),
            root_cause=Claim(**body["root_cause"]),
            pattern=body["pattern"],
            fix=body["fix"],
            guard=body["guard"],
            lesson=body["lesson"],
            regression=body.get("regression"),
            identifiers=body.get("identifiers", []),
            files=body.get("files", []),
            test_files=body.get("test_files", []),
            evidence=body.get("evidence", {}),
        )


def label(card_id: int | None) -> str:
    return "BUG-new" if card_id is None else f"BUG-{card_id:04d}"


def parse_label(text: str) -> int:
    match = re.fullmatch(r"(?:BUG-)?0*(\d+)", text.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"not a diary id: {text}")
    return int(match.group(1))
