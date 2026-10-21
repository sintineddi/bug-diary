from __future__ import annotations

import shlex
import sys
from pathlib import Path

from . import git

MARKER = "-m bugdiary"
FIX_SUBJECTS = "fix*|Fix*|FIX*|hotfix*|Hotfix*|bugfix*|Bugfix*"


class HookError(RuntimeError):
    pass


def hooks_dir(repo: Path) -> Path:
    path = Path(git.run(repo, "rev-parse", "--git-path", "hooks").strip())
    return path if path.is_absolute() else repo / path


def command() -> str:
    return f"{shlex.quote(sys.executable)} {MARKER}"


def pre_commit(strict: bool) -> str:
    check = "check --staged --strict" if strict else "check --staged || true"
    return f"#!/bin/sh\n{command()} {check}\n"


def post_commit() -> str:
    return (
        "#!/bin/sh\n"
        "sha=$(git rev-parse HEAD)\n"
        'subject=$(git log -1 --format=%s "$sha")\n'
        'case "$subject" in\n'
        f'  {FIX_SUBJECTS}) nohup nice {command()} learn "$sha" --quiet >/dev/null 2>&1 & ;;\n'
        "esac\n"
    )


def install(repo: Path, strict: bool = False, learn_fixes: bool = True) -> list[Path]:
    directory = hooks_dir(repo)
    directory.mkdir(parents=True, exist_ok=True)
    scripts = {"pre-commit": pre_commit(strict)}
    if learn_fixes:
        scripts["post-commit"] = post_commit()
    for name in scripts:
        path = directory / name
        if path.exists() and MARKER not in path.read_text(errors="replace"):
            raise HookError(f"{path} already exists and is not Bug Diary's; add a call to `bugdiary` to it yourself")
    written = []
    for name, script in scripts.items():
        path = directory / name
        path.write_text(script)
        path.chmod(0o755)
        written.append(path)
    return written


def uninstall(repo: Path) -> list[Path]:
    removed = []
    for name in ("pre-commit", "post-commit"):
        path = hooks_dir(repo) / name
        if path.exists() and MARKER in path.read_text(errors="replace"):
            path.unlink()
            removed.append(path)
    return removed
