from __future__ import annotations

import re
from dataclasses import dataclass, field
from collections.abc import Iterable

LOCK_FILES = {
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "poetry.lock",
    "Pipfile.lock",
    "uv.lock",
    "Cargo.lock",
    "go.sum",
    "Gemfile.lock",
    "composer.lock",
}
GENERATED_PREFIXES = ("node_modules/", "vendor/", "dist/", "third_party/", ".git/")
BINARY_SUFFIXES = (
    ".min.js",
    ".min.css",
    ".map",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".pdf",
    ".woff",
    ".woff2",
    ".ttf",
    ".zip",
    ".gz",
    ".tgz",
    ".jar",
    ".snap",
)
NOTES_PATH = re.compile(r"(^|/)(changelog|changes|history|news|release[-_ ]?notes)(\.[a-z]+)?$", re.IGNORECASE)
DOCS_PATH = re.compile(r"(^|/)(docs?/|readme)|\.(md|rst|txt|adoc)$", re.IGNORECASE)
TEST_PATH = re.compile(
    r"(^|/)(tests?|__tests__|spec|specs|testing|testdata|fixtures)/"
    r"|(^|/)test_[^/]+\.py$"
    r"|_test\.(py|go|rb|exs?)$"
    r"|\.(test|spec)\.[cm]?[jt]sx?$"
    r"|(Test|Tests|Spec)\.(java|kt|swift|cs|scala)$"
    r"|_spec\.rb$",
    re.IGNORECASE,
)
HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@ ?(.*)$")


@dataclass
class Line:
    kind: str
    text: str
    old_no: int | None
    new_no: int | None


@dataclass
class Hunk:
    header: str
    lines: list[Line] = field(default_factory=list)


@dataclass
class FileDiff:
    old_path: str | None
    new_path: str | None
    hunks: list[Hunk] = field(default_factory=list)
    binary: bool = False

    @property
    def path(self) -> str:
        return self.new_path or self.old_path or "?"

    @property
    def role(self) -> str:
        return file_role(self.path, self.binary)

    def lines(self, kinds: str = "+- ") -> list[Line]:
        return [line for hunk in self.hunks for line in hunk.lines if line.kind in kinds]


@dataclass(frozen=True)
class Hit:
    path: str
    line_no: int | None
    text: str


def file_role(path: str, binary: bool = False) -> str:
    name = path.rsplit("/", 1)[-1]
    lowered = path.lower()
    if binary or name in LOCK_FILES or lowered.endswith(BINARY_SUFFIXES):
        return "noise"
    if path.startswith(GENERATED_PREFIXES) or "/node_modules/" in path:
        return "noise"
    if NOTES_PATH.search(path):
        return "notes"
    if TEST_PATH.search(path):
        return "test"
    if DOCS_PATH.search(path):
        return "docs"
    return "code"


def clean_path(path: str) -> str | None:
    path = path.split("\t")[0].strip()
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
    if path == "/dev/null":
        return None
    if path[:2] in ("a/", "b/"):
        return path[2:]
    return path


def git_header_paths(raw: str) -> tuple[str | None, str | None]:
    pair = raw[len("diff --git ") :]
    old_path, separator, new_path = pair.partition(" b/")
    if not separator:
        return clean_path(pair), clean_path(pair)
    return clean_path(old_path), clean_path("b/" + new_path)


def parse(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    current: FileDiff | None = None
    hunk: Hunk | None = None
    old_no = new_no = old_left = new_left = 0
    for raw in text.splitlines():
        if hunk is not None and (old_left > 0 or new_left > 0):
            kind, body = (raw[0], raw[1:]) if raw else (" ", "")
            if kind == "\\":
                continue
            if kind == "+":
                hunk.lines.append(Line("+", body, None, new_no))
                new_no, new_left = new_no + 1, new_left - 1
            elif kind == "-":
                hunk.lines.append(Line("-", body, old_no, None))
                old_no, old_left = old_no + 1, old_left - 1
            else:
                hunk.lines.append(Line(" ", body, old_no, new_no))
                old_no, new_no = old_no + 1, new_no + 1
                old_left, new_left = old_left - 1, new_left - 1
            continue
        if raw.startswith("diff --git "):
            current = FileDiff(*git_header_paths(raw))
            files.append(current)
            hunk = None
        elif raw.startswith("--- "):
            if current is None or current.hunks:
                current = FileDiff(None, None)
                files.append(current)
            current.old_path = clean_path(raw[4:])
        elif raw.startswith("+++ ") and current is not None:
            current.new_path = clean_path(raw[4:])
        elif raw.startswith("Binary files ") and current is not None:
            current.binary = True
        else:
            match = HUNK_HEADER.match(raw)
            if match is None or current is None:
                continue
            old_no, new_no = int(match.group(1)), int(match.group(3))
            old_left = int(match.group(2)) if match.group(2) is not None else 1
            new_left = int(match.group(4)) if match.group(4) is not None else 1
            hunk = Hunk(header=raw)
            current.hunks.append(hunk)
    return [file for file in files if file.hunks or file.binary or file.path != "?"]


def render_file(file: FileDiff, context: int | None = None) -> str:
    out = [f"--- {file.old_path or '/dev/null'}", f"+++ {file.new_path or '/dev/null'}"]
    for hunk in file.hunks:
        out.append(hunk.header)
        lines = hunk.lines if context is None else trim_context(hunk.lines, context)
        out.extend("..." if line is None else f"{line.kind}{line.text}" for line in lines)
    return "\n".join(out)


def trim_context(lines: list[Line], context: int) -> list[Line | None]:
    keep = set()
    for index, line in enumerate(lines):
        if line.kind != " ":
            keep.update(range(max(0, index - context), min(len(lines), index + context + 1)))
    out: list[Line | None] = []
    for index, line in enumerate(lines):
        if index in keep:
            out.append(line)
        elif not out or out[-1] is not None:
            out.append(None)
    return out


def fit(files: Iterable[FileDiff], budget: int) -> tuple[str, list[str]]:
    files = list(files)
    parts: list[str] = []
    for context in (None, 8, 3, 1, 0):
        parts = [render_file(file, context) for file in files]
        if sum(len(part) + 1 for part in parts) <= budget:
            return "\n".join(parts), []
    kept, dropped, cut, used = [], [], [], 0
    for part, file in zip(parts, files):
        if used + len(part) + 1 <= budget:
            kept.append(part)
            used += len(part) + 1
        else:
            dropped.append(file.path)
    if not kept and parts:
        kept.append(parts[0][:budget])
        cut, dropped = dropped[:1], dropped[1:]
    if dropped:
        kept.append(f"[{len(dropped)} more changed files not shown: {', '.join(dropped[:12])}]")
    return "\n".join(kept), cut + dropped


def render(files: Iterable[FileDiff], budget: int) -> str:
    return fit(files, budget)[0]


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def strip_marker(text: str) -> str:
    text = text.strip()
    if text[:1] in ("+", "-") and not text.startswith(("++", "--")):
        return text[1:]
    return text


def find_lines(evidence: Iterable[str], files: Iterable[FileDiff], kinds: str = "+") -> list[Hit]:
    candidates = [(file.path, line) for file in files for line in file.lines(kinds) if len(squash(line.text)) >= 4]
    found: list[Hit] = []
    for item in evidence:
        for piece in str(item).splitlines():
            needle = squash(strip_marker(piece))
            if len(needle) < 6:
                continue
            for path, line in candidates:
                haystack = squash(line.text)
                if needle in haystack or (len(haystack) >= 12 and haystack in needle):
                    number = line.new_no if line.new_no is not None else line.old_no
                    hit = Hit(path, number, line.text.strip())
                    if hit not in found:
                        found.append(hit)
                    break
    return found
