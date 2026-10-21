from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from . import git

CONFIG_NAME = "bugdiary.yml"
DIARY_NAME = "diary.db"


@dataclass
class Settings:
    repo: Path | None
    project: str
    memory: Path

    @property
    def diary_path(self) -> Path:
        return self.memory / DIARY_NAME


def read_config(repo: Path | None) -> dict[str, str]:
    if repo is None or not (repo / CONFIG_NAME).is_file():
        return {}
    values = {}
    for line in (repo / CONFIG_NAME).read_text(encoding="utf-8").splitlines():
        content = line.split("#", 1)[0].strip()
        key, separator, value = content.partition(":")
        if separator and key.strip():
            values[key.strip()] = value.strip().strip("'\"")
    return values


def find_repo(path: Path) -> Path | None:
    try:
        return git.toplevel(path)
    except git.GitError:
        return None


def load(path: Path, project: str | None = None, memory: str | None = None) -> Settings:
    repo = find_repo(path)
    config = read_config(repo)
    chosen_memory = memory or os.environ.get("BUGDIARY_HOME") or config.get("memory") or "~/.bugdiary"
    chosen_project = project or config.get("project")
    if not chosen_project and repo is not None:
        chosen_project = git.remote_name(repo) or repo.name
    return Settings(repo, chosen_project or "default", Path(chosen_memory).expanduser())
