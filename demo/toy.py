from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

IDENTITY = {
    "GIT_AUTHOR_NAME": "Demo",
    "GIT_AUTHOR_EMAIL": "demo@example.com",
    "GIT_COMMITTER_NAME": "Demo",
    "GIT_COMMITTER_EMAIL": "demo@example.com",
}

SESSION = """import { AuthApi, Token } from "./api";

export class Session {
  constructor(private api: AuthApi, private token: Token) {}

  async getToken(): Promise<string> {
    if (this.token.expired) {
      this.token = await this.api.refresh(this.token.refreshToken);
    }
    return this.token.access;
  }
}
"""

SESSION_FIXED = """import { AuthApi, Token } from "./api";

export class Session {
  private refreshing: Promise<Token> | null = null;

  constructor(private api: AuthApi, private token: Token) {}

  async getToken(): Promise<string> {
    if (this.token.expired) {
      this.refreshing ??= this.api.refresh(this.token.refreshToken).finally(() => (this.refreshing = null));
      this.token = await this.refreshing;
    }
    return this.token.access;
  }
}
"""

SESSION_TEST = """import { Session } from "../src/auth/session";
import { expiredToken, fakeAuthApi } from "./fakes";

test("concurrent requests with an expired token refresh it once", async () => {
  const api = fakeAuthApi();
  const session = new Session(api, expiredToken());
  await Promise.all([session.getToken(), session.getToken()]);
  expect(api.refreshCalls).toBe(1);
});
"""

FIX_MESSAGE = """fix: users logged out when two requests refresh an expired token at once

Refresh tokens are single use. The second refresh sent a token the first
one had already rotated, so the server revoked the whole session."""

CLIENT = """import { Http } from "./http";

export class BillingClient {
  constructor(private http: Http) {}

  async invoices(): Promise<Invoice[]> {
    return this.http.get("/invoices");
  }
}
"""

CLIENT_REPEATS = """import { Http } from "./http";
import { AuthApi, Token } from "@acme/auth";

export class BillingClient {
  constructor(private http: Http, private auth: AuthApi, private token: Token) {}

  private async bearer(): Promise<string> {
    if (this.token.expired) {
      this.token = await this.auth.refresh(this.token.refreshToken);
    }
    return `Bearer ${this.token.access}`;
  }

  async invoices(): Promise<Invoice[]> {
    return this.http.get("/invoices", { Authorization: await this.bearer() });
  }

  async payments(): Promise<Payment[]> {
    return this.http.get("/payments", { Authorization: await this.bearer() });
  }
}
"""

CLIENT_GUARDED = """import { Http } from "./http";
import { AuthApi, Token } from "@acme/auth";

export class BillingClient {
  private refreshing: Promise<Token> | null = null;

  constructor(private http: Http, private auth: AuthApi, private token: Token) {}

  private async bearer(): Promise<string> {
    if (this.token.expired) {
      this.refreshing ??= this.auth.refresh(this.token.refreshToken).finally(() => (this.refreshing = null));
      this.token = await this.refreshing;
    }
    return `Bearer ${this.token.access}`;
  }

  async invoices(): Promise<Invoice[]> {
    return this.http.get("/invoices", { Authorization: await this.bearer() });
  }

  async payments(): Promise<Payment[]> {
    return this.http.get("/payments", { Authorization: await this.bearer() });
  }
}
"""


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, env={**os.environ, **IDENTITY}, capture_output=True)


def commit(repo: Path, message: str, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)


def bugdiary(repo: Path, memory: Path, *args: str) -> None:
    print(f"\n{repo.name} $ bugdiary {' '.join(args)}", flush=True)
    subprocess.run(
        [sys.executable, "-m", "bugdiary", *args], cwd=repo, env={**os.environ, "BUGDIARY_HOME": str(memory)}
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="python demo/toy.py")
    parser.add_argument("--keep", action="store_true", help="keep the demo repositories and print where they are")
    args = parser.parse_args()
    root = Path(tempfile.mkdtemp(prefix="bugdiary-demo-"))
    memory = root / "diary"
    api, billing = root / "api", root / "billing-worker"
    for repo in (api, billing):
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
    commit(api, "Session with token refresh", {"src/auth/session.ts": SESSION})
    commit(api, FIX_MESSAGE, {"src/auth/session.ts": SESSION_FIXED, "test/session.test.ts": SESSION_TEST})
    commit(billing, "Billing client", {"src/client.ts": CLIENT})
    bugdiary(api, memory, "learn", "HEAD", "--origin", "production")
    (billing / "src" / "client.ts").write_text(CLIENT_REPEATS)
    bugdiary(billing, memory, "check")
    (billing / "src" / "client.ts").write_text(CLIENT_GUARDED)
    bugdiary(billing, memory, "check")
    if args.keep:
        print(f"\nDemo repositories and diary: {root}")
    else:
        shutil.rmtree(root)


if __name__ == "__main__":
    main()
