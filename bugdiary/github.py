from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .learn import Note


class GitHubError(RuntimeError):
    pass


def note(repo: Path, kind: str, number: str) -> Note:
    command = ["gh", kind, "view", str(number), "--json", "title,body,url"]
    try:
        result = subprocess.run(command, cwd=repo, capture_output=True, text=True)
    except FileNotFoundError:
        raise GitHubError("gh is not installed (https://cli.github.com)") from None
    if result.returncode != 0:
        raise GitHubError(result.stderr.strip() or f"gh {kind} view {number} failed")
    data = json.loads(result.stdout)
    title = "pull request" if kind == "pr" else "issue"
    return Note(title, data.get("title") or "", data.get("body") or "", data.get("url") or f"#{number}")
