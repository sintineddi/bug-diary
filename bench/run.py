from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

from bugdiary import check, diffs, learn
from bugdiary.memory import Diary
from bugdiary.ollama import Ollama, OllamaError
from bugdiary.render import report_json

from . import github, snapshots
from .blind import review

ROOT = Path(__file__).resolve().parent
FAMILIES = ROOT / "families.json"
EXTRA = ROOT / "extra.json"
RESULTS = ROOT / "results"
VARIANTS = {
    "code": ("code",),
    "code+tests": ("tests", "code"),
    "code+tests+message": ("message", "changelog", "tests", "code"),
    "full": ("message", "notes", "changelog", "tests", "code"),
}
FOLLOW_UP = re.compile(r"follow-up|part|^tests", re.IGNORECASE)
FOLLOW_UP_DAYS = 30


def follow_up(instance: dict) -> str | None:
    primary = next(commit for commit in instance["fix_commits"] if commit["sha"] == instance["primary_fix_commit"])
    started = datetime.fromisoformat(primary["committer_date"].replace("Z", "+00:00"))
    later = []
    for commit in instance["fix_commits"]:
        when = datetime.fromisoformat(commit["committer_date"].replace("Z", "+00:00"))
        if commit is primary or not commit["on_default_branch"] or not FOLLOW_UP.search(commit["role"]):
            continue
        if timedelta(0) <= when - started <= timedelta(days=FOLLOW_UP_DAYS):
            later.append((when, commit["sha"]))
    return max(later)[1] if later else None


def load_cases() -> dict:
    research = json.loads(FAMILIES.read_text())
    extra = json.loads(EXTRA.read_text())
    fixes = []
    for family in research["families"]:
        for instance in family["instances"]:
            if instance["status"] != "verified":
                continue
            ghsa = next((item["ghsa"] for item in instance["advisories"] if item.get("ghsa")), None)
            fixes.append(
                {
                    "id": instance["id"],
                    "repo": instance["repo"],
                    "sha": instance["primary_fix_commit"],
                    "until": follow_up(instance),
                    "family": family["id"],
                    "advisory": ghsa,
                    "advisory_published": instance["advisory_published"],
                    "language": instance["language"],
                }
            )
    for number, item in enumerate(extra["fixes"], 1):
        fixes.append({"id": f"X-{number:02d}", "family": None, "advisory": None, **item})
    healthy = [{"id": f"H-{number:02d}", **item} for number, item in enumerate(extra["healthy"], 1)]
    return {"cutoff": research["cutoff"], "fixes": fixes, "healthy": healthy}


def project_of(repo: str) -> str:
    return repo.split("/")[-1]


def results_dir(model: str, variant: str) -> Path:
    return RESULTS / model.replace(":", "-").replace("/", "-") / variant


def fix_date(case: dict) -> str:
    return github.commit(case["repo"], case["sha"])["date"]


def split(cases: dict) -> tuple[list[dict], list[dict]]:
    cutoff = cases["cutoff"]
    fixes = sorted(cases["fixes"], key=fix_date)
    memory = [case for case in fixes if fix_date(case) < cutoff]
    evaluated = [case for case in fixes if fix_date(case) >= cutoff and case.get("family")]
    return memory, evaluated


def fix_data(case: dict) -> dict:
    data = github.commit(case["repo"], case["sha"])
    if not case.get("until"):
        return {**data, "head": data["sha"]}
    combined = github.compare(case["repo"], data["parent"], case["until"])
    return {**data, "head": case["until"], "diff": combined["diff"], "message": "\n\n".join(combined["messages"])}


def notes_for(case: dict, data: dict, cutoff: str) -> list[learn.Note]:
    notes = []
    published = case.get("advisory_published") or "9999"
    if case.get("advisory") and published < cutoff:
        advisory = github.advisory(case["advisory"])
        notes.append(learn.Note("advisory", advisory["summary"], advisory["description"], advisory["ghsa"]))
    for pull in data["pulls"]:
        notes.append(learn.Note("pull request", pull["title"], pull["body"], f"#{pull['number']}"))
    return notes


def build_fix(case: dict, cutoff: str) -> learn.Fix:
    data = fix_data(case)
    return learn.Fix(
        project=project_of(case["repo"]),
        revision=data["sha"],
        fixed_at=data["date"],
        message=data["message"],
        files=diffs.parse(data["diff"]),
        notes=notes_for(case, data, cutoff),
    )


def append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def done(path: Path, key: str) -> set:
    if not path.exists():
        return set()
    return {json.loads(line)[key] for line in path.read_text().splitlines() if line.strip()}


def run_learn(llm: Ollama, variant: str) -> None:
    cases = load_cases()
    memory, _ = split(cases)
    folder = results_dir(llm.model, variant)
    diary = Diary(folder / "diary.db")
    log = folder / "learn.jsonl"
    finished = done(log, "case")
    for case in memory:
        if case["id"] in finished:
            continue
        fix = build_fix(case, cases["cutoff"])
        try:
            learned = learn.learn(llm, fix, include=VARIANTS[variant])
        except (learn.LearnError, OllamaError) as error:
            append(log, {"case": case["id"], "error": str(error)})
            continue
        learn.remember(diary, llm, learned.card)
        card = learned.card
        append(
            log,
            {
                "case": case["id"],
                "family": case.get("family"),
                "card": card.label,
                "project": card.project,
                "fixed_at": card.fixed_at,
                "is_bug_fix": learned.is_bug_fix,
                "seconds": round(learned.seconds, 1),
                **card.body(),
            },
        )
        print(f"{variant} {case['id']}: {card.label} {card.pattern} ({learned.seconds:.0f} s)", flush=True)


def items(cases: dict, evaluated: list[dict]) -> list[dict]:
    out = []
    for case in evaluated:
        data = fix_data(case)
        pairs = []
        for path in snapshots.code_paths(data["diff"]):
            before = github.file_at(case["repo"], data["parent"], path)
            after = github.file_at(case["repo"], data["head"], path)
            if before is not None and after is not None:
                pairs.append(snapshots.pair(path, before, after))
        if not pairs:
            continue
        vulnerable = snapshots.merge([vulnerable for vulnerable, _ in pairs])
        fixed = snapshots.merge([fixed for _, fixed in pairs])
        base = {"case": case["id"], "repo": case["repo"], "family": case["family"]}
        out.append({**base, "item": f"{case['id']}:vulnerable", "kind": "vulnerable", **vars(vulnerable)})
        out.append({**base, "item": f"{case['id']}:fixed", "kind": "fixed", **vars(fixed)})
    for case in cases.get("healthy", []):
        data = github.commit(case["repo"], case["sha"])
        code = [file for file in diffs.parse(data["diff"]) if file.role == "code"]
        if code:
            out.append(
                {
                    "case": case["id"],
                    "repo": case["repo"],
                    "family": None,
                    "item": f"{case['id']}:healthy",
                    "kind": "healthy",
                    "diff": data["diff"],
                    "touched": {},
                }
            )
    return out


def run_detect(llm: Ollama, variant: str, top: int) -> None:
    cases = load_cases()
    _, evaluated = split(cases)
    folder = results_dir(llm.model, variant)
    diary = Diary(folder / "diary.db")
    log = folder / f"detect-top{top}.jsonl"
    finished = done(log, "item")
    for item in items(cases, evaluated):
        if item["item"] in finished:
            continue
        files = diffs.parse(item["diff"])
        report = check.check(llm, diary, files, project_of(item["repo"]), top=top)
        record = {key: item[key] for key in ("item", "case", "repo", "family", "kind", "touched")}
        record["report"] = check_record(report)
        append(log, record)
        alerts = [finding.card.label for finding in report.alerts]
        print(f"{variant} {item['item']}: {alerts or 'silent'} ({report.seconds:.0f} s)", flush=True)


def check_record(report: check.Report) -> dict:
    record = report_json(report)
    for finding, data in zip(report.findings, record["findings"]):
        data["card_project"] = finding.card.project
        data["card_revision"] = finding.card.revision
    return record


def run_blind(llm: Ollama) -> None:
    cases = load_cases()
    _, evaluated = split(cases)
    log = results_dir(llm.model, "blind") / "blind.jsonl"
    finished = done(log, "item")
    for item in items(cases, evaluated):
        if item["item"] in finished:
            continue
        started = time.monotonic()
        problems = review(llm, diffs.parse(item["diff"]))
        record = {key: item[key] for key in ("item", "case", "repo", "family", "kind", "touched")}
        record["problems"] = problems
        record["seconds"] = round(time.monotonic() - started, 1)
        append(log, record)
        print(f"blind {item['item']}: {len(problems)} problems", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m bench.run")
    parser.add_argument("step", choices=["fetch", "learn", "detect", "blind"])
    parser.add_argument("--variant", choices=sorted(VARIANTS), default="full")
    parser.add_argument("--model", default="gemma4:26b")
    parser.add_argument("--top", type=int, default=check.DEFAULT_TOP)
    args = parser.parse_args()
    llm = Ollama(model=args.model)
    if args.step == "fetch":
        cases = load_cases()
        memory, evaluated = split(cases)
        listed = items(cases, evaluated)
        print(f"{len(memory)} fixes for the memory, {len(listed)} items to check")
    elif args.step == "learn":
        run_learn(llm, args.variant)
    elif args.step == "detect":
        run_detect(llm, args.variant, args.top)
    else:
        run_blind(llm)


if __name__ == "__main__":
    main()
