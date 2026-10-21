from __future__ import annotations

import os
import shutil
import textwrap
from typing import TextIO

from .card import Card, Claim
from .check import Finding, Report

LABEL_WIDTH = 12
MAX_FILES = 6


class Style:
    def __init__(self, enabled: bool):
        self.enabled = enabled

    @classmethod
    def for_stream(cls, stream: TextIO) -> Style:
        return cls(stream.isatty() and "NO_COLOR" not in os.environ)

    def paint(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def bold(self, text: str) -> str:
        return self.paint("1", text)

    def dim(self, text: str) -> str:
        return self.paint("2", text)

    def yellow(self, text: str) -> str:
        return self.paint("1;33", text)

    def green(self, text: str) -> str:
        return self.paint("32", text)


def width() -> int:
    return max(60, min(100, shutil.get_terminal_size((100, 24)).columns))


def field(label: str, text: str) -> list[str]:
    indent = " " * (2 + LABEL_WIDTH)
    wrapped = textwrap.wrap(text, width() - len(indent)) or [""]
    return [f"  {label:<{LABEL_WIDTH}}{wrapped[0]}"] + [indent + line for line in wrapped[1:]]


def claim_text(claim: Claim) -> str:
    if not claim.known:
        return "unknown"
    if claim.basis == "stated":
        return f'{claim.text} (stated in the {claim.source}: "{claim.quote}")'
    return f"{claim.text} (inferred from the code)"


def listing(paths: list[str]) -> str:
    extra = len(paths) - MAX_FILES
    return ", ".join(paths[:MAX_FILES]) + (f" and {extra} more" if extra > 0 else "")


def card_heading(card: Card) -> str:
    heading = (
        f"{card.label} · {card.project} · {card.short_revision} · fixed {card.fixed_at[:10] or 'on an unknown date'}"
    )
    return heading if card.origin == "unknown" else f"{heading} · {card.origin}"


def card_lines(card: Card, style: Style, seconds: float | None = None) -> list[str]:
    lines = [style.bold(card_heading(card))]
    lines += field("Pattern", card.pattern)
    lines += field("Symptom", claim_text(card.symptom))
    lines += field("Root cause", claim_text(card.root_cause))
    lines += field("Fix", card.fix)
    lines += field("Guard", card.guard)
    lines += field("Lesson", card.lesson)
    if card.regression:
        given, when, then = (card.regression.get(key, "") for key in ("given", "when", "then"))
        lines += field("Regression", f"given {given}; when {when}; then {then} (test found in the fix, not run)")
    if card.files:
        lines += field("Files", listing(card.files))
    if card.test_files:
        lines += field("Tests", listing(card.test_files))
    if card.evidence.get("message_ignored"):
        lines.append(style.yellow(f"  Commit message ignored: {card.evidence['message_ignored']}"))
    sources = ", ".join(card.evidence.get("sources", [])) or "nothing"
    timing = f" in {seconds:.1f} s" if seconds is not None else ""
    lines.append(style.dim(f"  Learned from {sources} with {card.model}{timing}."))
    return lines


def alert_lines(finding: Finding, project: str, style: Style) -> list[str]:
    card = finding.card
    title = (
        "Bug pattern already met in another project" if card.project != project else "Possible return of a known bug"
    )
    lines = [style.yellow(f"⚠ {title}: {card.pattern}")]
    lines += field("Precedent", card_heading(card))
    if card.symptom.known:
        lines += field("Past bug", card.symptom.text)
    if card.root_cause.known:
        lines += field("Cause", card.root_cause.text)
    lines += field("Lesson", card.lesson)
    if finding.family:
        kin = ", ".join(f"{other.label} {other.project} {other.fixed_at[:4]}" for other in finding.family[:4])
        lines += field("Same kind", kin)
    lines.append("  In this change")
    room = width() - 6
    for hit in finding.evidence[:4]:
        location = f"{hit.path}:{hit.line_no}"
        text = (
            hit.text
            if len(location) + len(hit.text) + 2 <= room
            else hit.text[: max(10, room - len(location) - 5)] + "…"
        )
        lines.append(f"    {location}  {text}")
    lines += field("Why", finding.reason)
    if finding.check:
        lines += field("Check", finding.check)
    if finding.test:
        lines += field("Test", finding.test)
    return lines


def report_lines(report: Report, style: Style, show_all: bool = False) -> list[str]:
    if not report.files:
        return ["No code change to check."]
    if not report.diary_size:
        return ["The diary is empty: teach it a fix first with `bugdiary learn <commit>`."]
    lines: list[str] = []
    for finding in report.alerts:
        lines += alert_lines(finding, report.project, style)
        lines.append("")
    if not report.alerts and (report.partial or report.incomplete):
        lines.append(style.green("No known bug pattern in what could be checked."))
    elif not report.alerts:
        lines.append(style.green("No known bug pattern in this change."))
    for finding in report.findings:
        if finding.verdict == "protected":
            where = f"{finding.protection[0].path}:{finding.protection[0].line_no}"
            lines.append(style.green(f"✓ {finding.card.label} ({finding.card.pattern}) is already guarded at {where}"))
    others = [finding for finding in report.findings if finding.verdict in ("unclear", "unrelated")]
    if show_all:
        for finding in others:
            mark = "?" if finding.verdict == "unclear" else "·"
            note = f" [{finding.downgraded}]" if finding.downgraded else ""
            lines.append(style.dim(f"{mark} {finding.card.label} ({finding.card.pattern}): {finding.reason}{note}"))
    elif others:
        lines.append(style.dim(f"{len(others)} other lessons do not apply or stay unclear (--all shows them)."))
    if report.partial:
        lines.append(style.yellow(f"⚠ Too large to read whole: {listing(report.partial)}. Check it in smaller pieces."))
    if report.incomplete:
        lines.append(
            style.yellow(
                f"⚠ Not compared, the model gave no usable answer: {', '.join(report.incomplete)}. Run it again."
            )
        )
    lines.append(
        style.dim(
            f"Compared the change with {len(report.findings)} of {report.diary_size} lessons in {report.seconds:.0f} s."
        )
    )
    return lines


def hit_json(hits: list) -> list[dict]:
    return [{"path": hit.path, "line": hit.line_no, "text": hit.text} for hit in hits]


def report_json(report: Report) -> dict:
    return {
        "project": report.project,
        "files": report.files,
        "summary": report.summary,
        "behaviors": report.behaviors,
        "partial": report.partial,
        "incomplete": report.incomplete,
        "diary_size": report.diary_size,
        "seconds": round(report.seconds, 1),
        "findings": [
            {
                "card": finding.card.label,
                "project": finding.card.project,
                "pattern": finding.card.pattern,
                "similarity": round(finding.score, 3),
                "verdict": finding.verdict,
                "reason": finding.reason,
                "evidence": hit_json(finding.evidence),
                "protection": hit_json(finding.protection),
                "check": finding.check,
                "test": finding.test,
                "downgraded": finding.downgraded,
                "family": [other.label for other in finding.family],
            }
            for finding in report.findings
        ],
    }


def search_lines(ranked: list[tuple[Card, float]], style: Style) -> list[str]:
    if not ranked:
        return ["Nothing in the diary yet."]
    lines = []
    for card, _ in ranked:
        lines.append(style.bold(card_heading(card)))
        lines += field("Pattern", card.pattern)
        lines += field("Lesson", card.lesson)
    return lines


def list_lines(cards: list[Card]) -> list[str]:
    if not cards:
        return ["The diary is empty."]
    return [f"{card.label}  {card.project:<16} {card.fixed_at[:10] or '?':<10}  {card.pattern}" for card in cards]
