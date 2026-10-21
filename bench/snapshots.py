from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from bugdiary import diffs

CONTEXT = 30


@dataclass
class Snapshot:
    diff: str
    touched: dict[str, list[int]] = field(default_factory=dict)


def as_new_code(path: str, blocks: list[tuple[int, list[str]]]) -> str:
    out = [f"diff --git a/{path} b/{path}", "--- /dev/null", f"+++ b/{path}"]
    for start, lines in blocks:
        out.append(f"@@ -0,0 +{start + 1},{len(lines)} @@")
        out.extend("+" + line for line in lines)
    return "\n".join(out) + "\n"


def pair(path: str, before: str, after: str, context: int = CONTEXT) -> tuple[Snapshot, Snapshot]:
    old, new = before.splitlines(), after.splitlines()
    matcher = SequenceMatcher(None, old, new, autojunk=False)
    old_blocks, new_blocks = [], []
    old_touched, new_touched = set(), set()
    for group in matcher.get_grouped_opcodes(context):
        old_blocks.append((group[0][1], old[group[0][1] : group[-1][2]]))
        new_blocks.append((group[0][3], new[group[0][3] : group[-1][4]]))
        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                continue
            old_touched.update(range(i1 + 1, i2 + 1) if i2 > i1 else (i1, i1 + 1))
            new_touched.update(range(j1 + 1, j2 + 1) if j2 > j1 else (j1, j1 + 1))
    return (
        Snapshot(as_new_code(path, old_blocks), {path: sorted(old_touched)}),
        Snapshot(as_new_code(path, new_blocks), {path: sorted(new_touched)}),
    )


def merge(snapshots: list[Snapshot]) -> Snapshot:
    merged = Snapshot("".join(item.diff for item in snapshots))
    for item in snapshots:
        merged.touched.update(item.touched)
    return merged


def code_paths(fix_diff: str) -> list[str]:
    return [file.path for file in diffs.parse(fix_diff) if file.role == "code" and file.old_path and file.new_path]


def near(hit_line: int | None, touched: list[int], slack: int = 3) -> bool:
    return hit_line is not None and any(abs(hit_line - line) <= slack for line in touched)
