from __future__ import annotations

import argparse
import json
import random
import re
from urllib.parse import quote

from bugdiary import diffs

from . import github

FIX_MESSAGE = re.compile(r"^\s*(fix(e[sd])?|bug ?fix|bug)\b|\bfix(es|ed)? #\d+", re.IGNORECASE)
SECURITY_WORDS = re.compile(r"cve|ghsa|security|vulnerab|advisory|redirect|proto|travers|symlink", re.IGNORECASE)
NOT_HEALTHY = re.compile(r"fix|bug|security|cve|revert|regression|leak|crash|broken|wrong", re.IGNORECASE)
TOOLING = re.compile(
    r"test|lint|flake8|mypy|typing|type hint|annotation|ci\b|travis|appveyor|coverage|typo|docs?\b|readme|build|"
    r"release|bump|deprecat|warning|python ?\d|pypy|style|format|chore|refactor|rename|merge branch|license",
    re.IGNORECASE,
)
SOURCE_SUFFIXES = (".py", ".js", ".mjs", ".cjs", ".ts", ".go", ".c", ".h", ".rb", ".java", ".rs")
NOT_SOURCE = re.compile(
    r"^(\.github|scripts?|ci|benchmarks?|examples?|docs?|tools?|types?)/|(^|/)(setup|noxfile|conftest|"
    r"gulpfile|webpack\.config|rollup\.config|eslint\.config)\.|\.d\.ts$",
    re.IGNORECASE,
)


def library_source(file: diffs.FileDiff) -> bool:
    return file.role == "code" and file.path.endswith(SOURCE_SUFFIXES) and not NOT_SOURCE.search(file.path)


def changed_lines(files: list[diffs.FileDiff], role: str) -> int:
    if role == "source":
        return sum(len(file.lines("+-")) for file in files if library_source(file))
    return sum(len(file.lines("+-")) for file in files if file.role == role)


def parsed(repo: str, sha: str) -> list[diffs.FileDiff]:
    try:
        return diffs.parse(github.commit(repo, sha)["diff"])
    except github.FetchError:
        return []


def ordinary_fix(repo: str, sha: str) -> bool:
    files = parsed(repo, sha)
    source = changed_lines(files, "source")
    return 3 <= source <= 120 and source == changed_lines(files, "code") and changed_lines(files, "test") > 0


def healthy_change(repo: str, sha: str) -> bool:
    files = parsed(repo, sha)
    source = changed_lines(files, "source")
    return 10 <= source <= 160 and source == changed_lines(files, "code")


def labeled_fixes(repo: str, label: str, until: str, wanted: int, seed: int) -> list[dict]:
    query = quote(f'repo:{repo} is:pr is:merged label:"{label}" merged:<{until[:10]}')
    name = f"search-{label.encode().hex()}-{until[:10]}.json"
    found = json.loads(
        github.cached(
            github.repo_dir(repo) / "lists" / name, lambda: github.gh(f"search/issues?q={query}&per_page=100")
        )
    )
    pulls = [item["number"] for item in found.get("items", [])]
    random.Random(f"{seed}-{repo}-labeled").shuffle(pulls)
    chosen = []
    for number in pulls:
        pull = json.loads(
            github.cached(
                github.repo_dir(repo) / "pulls" / f"{number}.json", lambda: github.gh(f"repos/{repo}/pulls/{number}")
            )
        )
        sha = pull.get("merge_commit_sha")
        if not sha or SECURITY_WORDS.search(pull.get("title") or ""):
            continue
        if ordinary_fix(repo, sha):
            chosen.append(
                {"repo": repo, "sha": sha, "date": pull["merged_at"], "message": f"#{number} {pull['title']}"}
            )
        if len(chosen) == wanted:
            break
    return chosen


def pick(repo: str, since: str, until: str, wanted: int, healthy: bool, seed: int) -> list[dict]:
    if wanted <= 0:
        return []
    commits = github.commits_between(repo, since, until, pages=5)
    subject = [(item, item["message"].splitlines()[0]) for item in commits]
    if healthy:
        candidates = [item for item, line in subject if not NOT_HEALTHY.search(line) and not TOOLING.search(line)]
    else:
        candidates = [item for item, line in subject if FIX_MESSAGE.search(line) and not TOOLING.search(line)]
        candidates = [item for item in candidates if not SECURITY_WORDS.search(item["message"])]
    random.Random(f"{seed}-{repo}-{healthy}").shuffle(candidates)
    chosen = []
    for item in candidates:
        accepted = healthy_change(repo, item["sha"]) if healthy else ordinary_fix(repo, item["sha"])
        if accepted:
            chosen.append({"repo": repo, "sha": item["sha"], "date": item["date"], "message": item["message"][:120]})
        if len(chosen) == wanted:
            break
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m bench.sample")
    parser.add_argument(
        "repos", nargs="+", help="owner/name, or owner/name=label to use merged pull requests with that label"
    )
    parser.add_argument("--fixes-since", default="2017-01-01T00:00:00Z")
    parser.add_argument("--cutoff", default="2021-01-01T00:00:00Z")
    parser.add_argument("--healthy-until", default="2024-12-31T00:00:00Z")
    parser.add_argument("--fixes", type=int, default=3)
    parser.add_argument("--healthy", type=int, default=2)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    out = {"fixes": [], "healthy": []}
    for spec in args.repos:
        repo, _, label = spec.partition("=")
        if label:
            out["fixes"] += labeled_fixes(repo, label, args.cutoff, args.fixes, args.seed)
        else:
            out["fixes"] += pick(repo, args.fixes_since, args.cutoff, args.fixes, False, args.seed)
        if args.healthy:
            out["healthy"] += pick(repo, args.cutoff, args.healthy_until, args.healthy, True, args.seed)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
