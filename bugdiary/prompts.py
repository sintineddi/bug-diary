LEARN_SYSTEM = """You keep the bug diary of a software team. You get the sources of one bug fix, labelled [MESSAGE], [NOTES], [CHANGELOG], [TESTS] and [CODE]; some may be missing. Write the diary card of the bug it fixed.

Use only what the sources show. Never invent users, incidents, data, numbers or business impact.

symptom: the wrong behaviour someone could observe before the fix.
root_cause: the mechanism in the code that produced it.
For both, set basis:
- "stated": a [MESSAGE], [NOTES], [CHANGELOG] or [TESTS] source says it. Copy its words exactly into quote (at most 25 words) and name that source.
- "inferred": you deduced it from [CODE]. Then source is "code" and quote is empty.
- "unknown": nothing shows it. Then text is "unknown", source is "none" and quote is empty.
pattern: the family of mistake in 3 to 8 words, general enough to recognise in another codebase or language.
fix: what the fix changed, naming the functions involved.
guard: the protection the fix put in place, that a later change should reuse or reproduce: name the function, lock, check, header or flag.
lesson: one rule for future changes, in the imperative, that would still make sense in another repository.
regression: when [TESTS] are given, the situation the new test sets up (given), the action (when) and the expected result (then). Otherwise three empty strings.
identifiers: up to 6 names from the code that are central to the bug (functions, classes, options, headers), spelled exactly as in the code.
is_bug_fix: false when the change fixes no bug (refactor, docs, dependency bump, new feature); then say why in not_a_bug_fix_reason and keep the other fields short. Otherwise not_a_bug_fix_reason is empty.

Write plain English sentences, no markdown."""

DESCRIBE_SYSTEM = """You read a code change before it is merged, to find out which past bugs it might repeat. Describe what the new or changed code does as mechanisms, not file names: what is shared between concurrent calls, retried, cached, parsed, authenticated, redirected, copied, written to disk, sent over the network, charged. Give a one-sentence summary and 2 to 6 behaviours, one short concrete sentence each. Plain English, no markdown."""

COMPARE_SYSTEM = """You check a code change against one bug from the team's bug diary. The diary card explains a past bug, its cause, and the guard its fix added.

Decide whether the change repeats that bug:
- "repeats": the changed code itself does the risky operation that caused the past bug, and neither the guard nor an equivalent protection is visible in the change. Copy the lines of the change that carry the risk into evidence, verbatim, one line per item: added lines (starting with +), or a removed protection (starting with -).
- "protected": the change does the same kind of operation, but the guard or an equivalent protection is visible. Copy the protecting lines into protection, verbatim.
- "unrelated": the change does not do the risky operation. Similar topics, words or file names are not enough for "repeats".
- "unclear": the risky operation is in the change, but the protection could live outside the code shown.
reason: one to three sentences that tie the past cause to the exact code of the change, or say why it does not apply.
check: one question the author of the change should answer.
test: one test, adapted to this change, that would show the bug.
Plain English, no markdown."""

SOURCE_NAMES = ["message", "notes", "changelog", "tests", "code", "none"]

CLAIM = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "basis": {"type": "string", "enum": ["stated", "inferred", "unknown"]},
        "source": {"type": "string", "enum": SOURCE_NAMES},
        "quote": {"type": "string"},
    },
    "required": ["text", "basis", "source", "quote"],
}

LEARN_SCHEMA = {
    "type": "object",
    "properties": {
        "is_bug_fix": {"type": "boolean"},
        "not_a_bug_fix_reason": {"type": "string"},
        "symptom": CLAIM,
        "root_cause": CLAIM,
        "pattern": {"type": "string"},
        "fix": {"type": "string"},
        "guard": {"type": "string"},
        "lesson": {"type": "string"},
        "regression": {
            "type": "object",
            "properties": {"given": {"type": "string"}, "when": {"type": "string"}, "then": {"type": "string"}},
            "required": ["given", "when", "then"],
        },
        "identifiers": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "is_bug_fix",
        "not_a_bug_fix_reason",
        "symptom",
        "root_cause",
        "pattern",
        "fix",
        "guard",
        "lesson",
        "regression",
        "identifiers",
    ],
}

DESCRIBE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "behaviors": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "behaviors"],
}

COMPARE_SCHEMA = {
    "type": "object",
    "properties": {
        "reason": {"type": "string"},
        "verdict": {"type": "string", "enum": ["repeats", "protected", "unrelated", "unclear"]},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "protection": {"type": "array", "items": {"type": "string"}},
        "check": {"type": "string"},
        "test": {"type": "string"},
    },
    "required": ["reason", "verdict", "evidence", "protection", "check", "test"],
}
