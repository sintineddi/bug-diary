from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

from .run import RESULTS, fix_date, load_cases, project_of
from .snapshots import near

VERSIONS = {
    "": "each lesson alone",
    "-by-kind": "by kind of bug (--by-kind)",
    "-v2": "experiment: by kind, told guards can be incomplete",
}
FAMILY_NAMES = {
    "F1": "credentials kept across a redirect",
    "F2": "archive extraction escapes its folder",
    "F3": "prototype pollution",
    "F4": "request smuggling",
}


def read_all(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def latest(path: Path) -> dict:
    return {row.get("item", row.get("case")): row for row in read_all(path)}


def read(path: Path) -> list[dict]:
    return [row for row in latest(path).values() if "error" not in row]


def failures(path: Path) -> int:
    return sum(1 for row in latest(path).values() if "error" in row)


def family_of_cards(learn_log: list[dict]) -> dict[str, str | None]:
    return {row["card"]: row.get("family") for row in learn_log if "card" in row}


def located(hits: list[dict], touched: dict[str, list[int]]) -> bool:
    return any(near(hit["line"], touched.get(hit["path"], [])) for hit in hits)


def later_in_repo(cases: dict) -> dict[str, list[str]]:
    dated = sorted(((fix_date(case), case) for case in cases["fixes"] if case.get("family")), key=lambda item: item[0])
    later = {}
    for date, case in dated:
        later[case["id"]] = [
            other["id"]
            for other_date, other in dated
            if other_date > date and other["repo"] == case["repo"] and other["family"] == case["family"]
        ]
    return later


def judge_detection(row: dict, families: dict[str, str | None]) -> dict:
    project = project_of(row["repo"])
    alerts = [finding for finding in row["report"]["findings"] if finding["verdict"] == "repeats"]
    retrieved = [finding["card"] for finding in row["report"]["findings"]]
    relevant = [card for card in retrieved if row["family"] and families.get(card) == row["family"]]
    right = [alert for alert in alerts if row["family"] and families.get(alert["card"]) == row["family"]]
    return {
        "item": row["item"],
        "kind": row["kind"],
        "family": row["family"],
        "retrieved_relevant": bool(relevant),
        "alerted": bool(alerts),
        "right_precedent": bool(right),
        "same_repo": any(alert["card_project"] == project for alert in right),
        "cross_repo": any(alert["card_project"] != project for alert in right),
        "on_the_spot": any(located(alert["evidence"], row["touched"]) for alert in right),
        "wrong_precedent": len(alerts) - len(right),
        "protected_on_the_spot": any(
            located(finding["protection"], row["touched"])
            for finding in row["report"]["findings"]
            if finding["verdict"] == "protected"
        ),
        "seconds": row["report"]["seconds"],
    }


def judge_blind(row: dict) -> dict:
    return {
        "item": row["item"],
        "kind": row["kind"],
        "family": row["family"],
        "alerted": bool(row["problems"]),
        "on_the_spot": any(located(problem["evidence"], row["touched"]) for problem in row["problems"]),
        "problems": len(row["problems"]),
        "seconds": row["seconds"],
    }


def share(rows: list[dict], key: str) -> str:
    return f"{sum(1 for row in rows if row[key])}/{len(rows)}" if rows else "–"


def family_table(judged: list[dict], blind: list[dict]) -> list[str]:
    lines = [
        "| family | vulnerable snapshots | relevant lesson retrieved | alert, same family | alert on the fixed lines"
        " | no diary: flagged the fixed lines | alerts on fixed code |",
        "|---|---|---|---|---|---|---|",
    ]
    blind_by_item = {row["item"]: row for row in blind}
    for family, name in FAMILY_NAMES.items():
        vulnerable = [row for row in judged if row["family"] == family and row["kind"] == "vulnerable"]
        fixed = [row for row in judged if row["family"] == family and row["kind"] == "fixed"]
        blind_rows = [blind_by_item[row["item"]] for row in vulnerable if row["item"] in blind_by_item]
        lines.append(
            f"| {family} {name} | {len(vulnerable)} | {share(vulnerable, 'retrieved_relevant')} "
            f"| {share(vulnerable, 'right_precedent')} | {share(vulnerable, 'on_the_spot')} "
            f"| {share(blind_rows, 'on_the_spot')} | {share(fixed, 'alerted')} |"
        )
    return lines


def fixed_alerts(judged_rows: list[tuple[dict, dict]], later: dict[str, list[str]]) -> list[str]:
    lines = [
        "| fixed snapshot | lesson cited | same family | a later advisory in the same repository |",
        "|---|---|---|---|",
    ]
    for row, judged in judged_rows:
        if row["kind"] != "fixed" or not judged["alerted"]:
            continue
        for finding in row["report"]["findings"]:
            if finding["verdict"] == "repeats":
                same = "yes" if judged["right_precedent"] else "no"
                follow = ", ".join(later.get(row["case"], [])) or "none"
                lines.append(f"| {row['item']} | {finding['card']} {finding['pattern']} | {same} | {follow} |")
    return lines


def median_seconds(rows: list[dict]) -> str:
    return f"{statistics.median(row['seconds'] for row in rows):.0f} s" if rows else "–"


def detection_table(name: str, judged: list[dict], failed: int = 0) -> list[str]:
    vulnerable = [row for row in judged if row["kind"] == "vulnerable"]
    fixed = [row for row in judged if row["kind"] == "fixed"]
    healthy = [row for row in judged if row["kind"] == "healthy"]
    return [
        f"| {name} | {len(judged)} ({failed} failed) "
        f"| {share(vulnerable, 'retrieved_relevant')} | {share(vulnerable, 'right_precedent')} "
        f"| {share(vulnerable, 'on_the_spot')} | {share(vulnerable, 'same_repo')} | {share(vulnerable, 'cross_repo')} "
        f"| {share(fixed, 'alerted')} | {share(healthy, 'alerted')} "
        f"| {median_seconds(judged)} |"
    ]


def blind_table(judged: list[dict], failed: int = 0) -> list[str]:
    vulnerable = [row for row in judged if row["kind"] == "vulnerable"]
    fixed = [row for row in judged if row["kind"] == "fixed"]
    healthy = [row for row in judged if row["kind"] == "healthy"]
    return [
        f"| no diary | {len(judged)} ({failed} failed) | – | – | {share(vulnerable, 'on_the_spot')} | – | – "
        f"| {share(fixed, 'alerted')} | {share(healthy, 'alerted')} "
        f"| {median_seconds(judged)} |"
    ]


def learn_table(model_dir: Path) -> list[str]:
    lines = [
        "| variant | cards | symptom stated | symptom inferred | symptom unknown | quotes rejected | median time |",
        "|---|---|---|---|---|---|---|",
    ]
    for variant_dir in sorted(path for path in model_dir.iterdir() if (path / "learn.jsonl").exists()):
        rows = [row for row in read(variant_dir / "learn.jsonl") if "card" in row]
        if not rows:
            continue
        basis = defaultdict(int)
        for row in rows:
            basis[row["symptom"]["basis"]] += 1
        rejected = sum(len(row["evidence"]["rejected_quotes"]) for row in rows)
        seconds = statistics.median(row["seconds"] for row in rows)
        lines.append(
            f"| {variant_dir.name} | {len(rows)} | {basis['stated']} | {basis['inferred']} | {basis['unknown']} "
            f"| {rejected} | {seconds:.0f} s |"
        )
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m bench.report")
    parser.add_argument("--model", default="gemma4:26b")
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args()
    cases = load_cases()
    model_dir = RESULTS / args.model.replace(":", "-").replace("/", "-")
    out = [f"# Bug Diary benchmark: {args.model}", "", f"Memory frozen at {cases['cutoff']}.", ""]
    out += ["## Cards", ""] + learn_table(model_dir) + [""]
    out += [
        "## Detection",
        "",
        "| diary built from | items checked | relevant lesson retrieved | alert with a lesson of the same family"
        " | alert on the fixed lines | same repo | other repo | alerts on fixed code | alerts on healthy changes"
        " | median time |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    blind = [judge_blind(row) for row in read(model_dir / "blind" / "blind.jsonl")]
    compared: dict[str, list[tuple[dict, dict]]] = {}
    for variant_dir in sorted(path for path in model_dir.iterdir() if path.is_dir()):
        families = family_of_cards(read(variant_dir / "learn.jsonl"))
        logs = [variant_dir / f"detect-top{args.top}.jsonl", *sorted(variant_dir.glob(f"detect-top{args.top}-*.jsonl"))]
        for log in (path for path in logs if path.exists()):
            version = VERSIONS.get(log.stem.removeprefix(f"detect-top{args.top}"), log.stem)
            rows = read(log)
            judged = [judge_detection(row, families) for row in rows]
            if judged or failures(log):
                out += detection_table(f"{variant_dir.name}, {version}", judged, failures(log))
            if variant_dir.name == "full":
                compared[version] = list(zip(rows, judged))
    blind_failures = failures(model_dir / "blind" / "blind.jsonl")
    if blind or blind_failures:
        out += blind_table(blind, blind_failures)
    out.append("")
    for version, pairs in compared.items():
        out += [f"## By family (full context, {version})", ""]
        out += family_table([judged for _, judged in pairs], blind) + [""]
        out += [f"## Alerts on fixed code ({version})", ""]
        out += fixed_alerts(pairs, later_in_repo(cases)) + [""]
    path = model_dir / "RESULTS.md"
    path.write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
