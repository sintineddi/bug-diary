from __future__ import annotations

import hashlib
import math
import os
import re
import subprocess
import tempfile
from pathlib import Path

from bugdiary.prompts import COMPARE_SYSTEM, DESCRIBE_SYSTEM, FAMILY_SYSTEM, LEARN_SYSTEM

GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}

TOKEN_CARD = {
    "message_matches": "yes",
    "message_mismatch": "",
    "is_bug_fix": True,
    "not_a_bug_fix_reason": "",
    "symptom": {
        "text": "Users were logged out when two requests refreshed an expired token.",
        "basis": "stated",
        "source": "message",
        "quote": "users logged out when two requests refresh an expired token",
    },
    "root_cause": {
        "text": "Each caller refreshed the token on its own.",
        "basis": "inferred",
        "source": "code",
        "quote": "",
    },
    "pattern": "race between concurrent token refreshes",
    "fix": "getToken shares one refresh promise.",
    "guard": "the refreshing promise in Session.getToken",
    "lesson": "Share one in-flight refresh between concurrent callers.",
    "regression": {"given": "an expired token", "when": "two calls run at once", "then": "refresh runs once"},
    "identifiers": ["getToken", "refreshing", "NotInTheCode"],
}


class FakeLLM:
    def __init__(
        self,
        card: dict | None = None,
        verdict: dict | None = None,
        behaviors: list[str] | None = None,
        cards: list[dict] | None = None,
    ):
        self.model = "fake-model"
        self.embed_model = "fake-embed"
        self.card = card or TOKEN_CARD
        self.cards = list(cards or [])
        self.verdict = verdict or {
            "reason": "The new bearer method refreshes the token without the shared promise.",
            "verdict": "repeats",
            "evidence": ["this.token = await this.auth.refresh(this.token.refreshToken);"],
            "protection": [],
            "check": "Do concurrent calls share one refresh?",
            "test": "Call invoices and payments at once with an expired token.",
        }
        self.behaviors = behaviors or ["refreshes an expired access token before each request"]
        self.prompts: list[tuple[str, str]] = []

    def chat_json(self, system: str, user: str, schema: dict, model: str | None = None) -> dict:
        self.prompts.append((system, user))
        if system == LEARN_SYSTEM:
            return self.cards.pop(0) if self.cards else self.card
        if system == DESCRIBE_SYSTEM:
            return {"summary": "Adds a token refresh to the billing client.", "behaviors": self.behaviors}
        if system in (COMPARE_SYSTEM, FAMILY_SYSTEM):
            return self.verdict
        raise AssertionError("unexpected prompt")

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [bag_of_words(text) for text in texts]

    def seconds(self, kind: str | None = None) -> float:
        return 0.0


def bag_of_words(text: str, size: int = 64) -> list[float]:
    vector = [0.0] * size
    for word in re.findall(r"[a-z]{4,}", text.lower()):
        vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % size] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def git(repo: Path, *args: str) -> str:
    environment = {**os.environ, **GIT_IDENTITY}
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=environment)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout


def write(repo: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def make_repo(root: Path, name: str, commits: list[tuple[str, dict[str, str]]]) -> Path:
    repo = root / name
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    for message, files in commits:
        write(repo, files)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", message)
    return repo


SESSION_BEFORE = """export class Session {
  async getToken() {
    if (this.token.expired) {
      this.token = await this.api.refresh(this.token.refreshToken);
    }
    return this.token.access;
  }
}
"""

SESSION_AFTER = """export class Session {
  private refreshing = null;

  async getToken() {
    if (this.token.expired) {
      this.refreshing ??= this.api.refresh(this.token.refreshToken).finally(() => (this.refreshing = null));
      this.token = await this.refreshing;
    }
    return this.token.access;
  }
}
"""

SESSION_TEST = """test("concurrent requests with an expired token refresh it once", async () => {
  await Promise.all([session.getToken(), session.getToken()]);
  expect(api.refreshCalls).toBe(1);
});
"""

BILLING_CHANGE = """export class BillingClient {
  private async bearer() {
    if (this.token.expired) {
      this.token = await this.auth.refresh(this.token.refreshToken);
    }
    return this.token.access;
  }
}
"""


def token_repos(root: Path) -> tuple[Path, Path]:
    api = make_repo(
        root,
        "api",
        [
            ("Session", {"src/session.ts": SESSION_BEFORE}),
            (
                "fix: users logged out when two requests refresh an expired token at once",
                {"src/session.ts": SESSION_AFTER, "test/session.test.ts": SESSION_TEST},
            ),
        ],
    )
    billing = make_repo(
        root, "billing-worker", [("Billing client", {"src/client.ts": "export class BillingClient {}\n"})]
    )
    write(billing, {"src/client.ts": BILLING_CHANGE})
    return api, billing


def added_file(path: str, count: int, width: int = 60) -> str:
    body = "\n".join(f'+let value{index} = "{"x" * width}";' for index in range(count))
    return f"--- /dev/null\n+++ b/{path}\n@@ -0,0 +1,{count} @@\n{body}\n"


def temporary_directory() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(prefix="bugdiary-test-")
