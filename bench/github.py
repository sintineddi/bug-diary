from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "cache"


class FetchError(RuntimeError):
    pass


def gh(path: str, accept: str | None = None) -> str:
    command = ["gh", "api", path]
    if accept:
        command[2:2] = ["-H", f"Accept: {accept}"]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace")
    if result.returncode != 0:
        raise FetchError(f"gh api {path}: {result.stderr.strip()[:300]}")
    return result.stdout


def cached(path: Path, produce) -> str:
    if path.exists():
        return path.read_text(errors="replace")
    text = produce()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return text


def repo_dir(repo: str) -> Path:
    return CACHE / repo.replace("/", "__")


def commit(repo: str, sha: str) -> dict:
    folder = repo_dir(repo) / "commits" / sha
    meta = json.loads(cached(folder / "commit.json", lambda: gh(f"repos/{repo}/commits/{sha}")))
    diff = cached(folder / "fix.diff", lambda: gh(f"repos/{repo}/commits/{sha}", "application/vnd.github.diff"))
    pulls = json.loads(cached(folder / "pulls.json", lambda: gh(f"repos/{repo}/commits/{sha}/pulls")))
    return {
        "sha": meta["sha"],
        "date": meta["commit"]["committer"]["date"],
        "message": meta["commit"]["message"],
        "parent": meta["parents"][0]["sha"] if meta["parents"] else None,
        "diff": diff,
        "pulls": [{"number": pull["number"], "title": pull["title"], "body": pull.get("body") or ""} for pull in pulls],
    }


def compare(repo: str, base: str, head: str) -> dict:
    folder = repo_dir(repo) / "compare" / f"{base}...{head}"
    meta = json.loads(cached(folder / "compare.json", lambda: gh(f"repos/{repo}/compare/{base}...{head}")))
    diff = cached(
        folder / "fix.diff", lambda: gh(f"repos/{repo}/compare/{base}...{head}", "application/vnd.github.diff")
    )
    return {"diff": diff, "messages": [item["commit"]["message"] for item in meta.get("commits", [])]}


def file_at(repo: str, ref: str, path: str) -> str | None:
    target = repo_dir(repo) / "files" / ref / path
    missing = target.with_name(target.name + ".missing")
    if target.exists():
        return target.read_text(errors="replace")
    if missing.exists():
        return None
    try:
        text = gh(f"repos/{repo}/contents/{quote(path)}?ref={ref}", "application/vnd.github.raw")
    except FetchError:
        missing.parent.mkdir(parents=True, exist_ok=True)
        missing.write_text("")
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    return text


def advisory(ghsa: str) -> dict:
    data = json.loads(cached(CACHE / "advisories" / f"{ghsa}.json", lambda: gh(f"advisories/{ghsa}")))
    return {
        "ghsa": ghsa,
        "cve": data.get("cve_id"),
        "published": data.get("published_at"),
        "summary": data.get("summary") or "",
        "description": data.get("description") or "",
    }


def commits_between(repo: str, since: str, until: str, pages: int = 3) -> list[dict]:
    out = []
    for page in range(1, pages + 1):
        path = f"repos/{repo}/commits?since={since}&until={until}&per_page=100&page={page}"
        name = f"list-{since[:10]}-{until[:10]}-{page}.json"
        batch = json.loads(cached(repo_dir(repo) / "lists" / name, lambda: gh(path)))
        out += [
            {"sha": item["sha"], "date": item["commit"]["committer"]["date"], "message": item["commit"]["message"]}
            for item in batch
            if len(item.get("parents", [])) == 1
        ]
        if len(batch) < 100:
            break
    return out
