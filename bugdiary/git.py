from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
CONTEXT_LINES = 20
UNTRACKED_MAX_BYTES = 200_000


class GitError(RuntimeError):
    pass


@dataclass
class Commit:
    sha: str
    date: str
    message: str


def run(repo: Path, *args: str, ok: tuple[int, ...] = (0,)) -> str:
    command = ["git", "-c", "core.quotepath=off", "-C", str(repo), *args]
    try:
        result = subprocess.run(command, capture_output=True, text=True, errors="replace")
    except FileNotFoundError:
        raise GitError("git is not installed") from None
    if result.returncode not in ok:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def toplevel(path: Path) -> Path:
    return Path(run(path, "rev-parse", "--show-toplevel").strip())


def remote_name(repo: Path) -> str | None:
    url = run(repo, "config", "--get", "remote.origin.url", ok=(0, 1)).strip()
    if not url:
        return None
    name = url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    return name[:-4] if name.endswith(".git") else name


def resolve(repo: Path, rev: str) -> str:
    sha = run(repo, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}", ok=(0, 1)).strip()
    if not sha:
        raise GitError(f"unknown revision {rev}")
    return sha


def commit(repo: Path, sha: str) -> Commit:
    out = run(repo, "show", "-s", "--format=%H%x00%cI%x00%B", sha)
    full, date, message = out.split("\x00", 2)
    return Commit(full.strip(), date.strip(), message.strip())


def fix_range(repo: Path, rev: str) -> tuple[str, str, list[Commit]]:
    if ".." in rev:
        start, _, end = rev.partition("..")
        base = resolve(repo, start or "HEAD")
        head = resolve(repo, end or "HEAD")
        shas = run(repo, "rev-list", "--reverse", f"{base}..{head}").split()
        if not shas:
            raise GitError(f"no commits in {rev}")
        return base, head, [commit(repo, sha) for sha in shas]
    head = resolve(repo, rev)
    parent = run(repo, "rev-parse", "--verify", "--quiet", f"{head}^", ok=(0, 1)).strip()
    return parent or EMPTY_TREE, head, [commit(repo, head)]


def diff(repo: Path, *args: str) -> str:
    return run(repo, "diff", "--no-color", "--no-ext-diff", "-M", f"-U{CONTEXT_LINES}", *args)


def worktree_diff(repo: Path) -> str:
    has_head = bool(run(repo, "rev-parse", "--verify", "--quiet", "HEAD", ok=(0, 1)).strip())
    tracked = diff(repo, "HEAD") if has_head else diff(repo, "--cached")
    return tracked + untracked_diff(repo)


def untracked_diff(repo: Path) -> str:
    parts = []
    for name in run(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\x00"):
        path = repo / name
        if not name or not path.is_file() or path.stat().st_size > UNTRACKED_MAX_BYTES:
            continue
        parts.append(run(repo, "diff", "--no-color", "--no-index", "--", "/dev/null", name, ok=(0, 1)))
    return "".join(parts)


def staged_diff(repo: Path) -> str:
    return diff(repo, "--cached")


def branch_diff(repo: Path, base: str) -> str:
    return diff(repo, f"{base}...HEAD")


def commit_diff(repo: Path, rev: str) -> str:
    base, head, _ = fix_range(repo, rev)
    return diff(repo, base, head)
