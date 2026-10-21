from __future__ import annotations

from bugdiary import diffs
from bugdiary.check import CHANGE_BUDGET, code_files, strings
from bugdiary.diffs import FileDiff
from bugdiary.ollama import Ollama

BLIND_SYSTEM = """You review a code change before it is merged. List the bugs and security problems you can see in the changed code. For each one, say what goes wrong in one or two sentences, and copy the lines of the change that cause it, verbatim, one line per item. If you see no problem, return an empty list. Plain English, no markdown."""

BLIND_SCHEMA = {
    "type": "object",
    "properties": {
        "problems": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"what": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}},
                "required": ["what", "evidence"],
            },
        }
    },
    "required": ["problems"],
}


def review(llm: Ollama, files: list[FileDiff]) -> list[dict]:
    code = code_files(files)
    if not code:
        return []
    raw = llm.chat_json(BLIND_SYSTEM, diffs.render(code, CHANGE_BUDGET), BLIND_SCHEMA)
    problems = []
    for problem in raw.get("problems") or []:
        if not isinstance(problem, dict):
            continue
        hits = diffs.find_lines(strings(problem.get("evidence")), code, "+-")
        if hits:
            problems.append(
                {
                    "what": str(problem.get("what") or "").strip(),
                    "evidence": [{"path": hit.path, "line": hit.line_no, "text": hit.text} for hit in hits],
                }
            )
    return problems
