import contextlib
import io
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from bugdiary import cli, config, hooks

from .fakes import FakeLLM, git, make_repo, temporary_directory, token_repos


def run(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(args))
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = temporary_directory()
        root = Path(self.tmp.name)
        self.api, self.billing = token_repos(root)
        self.memory = str(root / "memory")
        self.llm = FakeLLM()
        patcher = mock.patch.object(cli, "make_llm", return_value=self.llm)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def test_learn_then_check_in_another_repository(self):
        code, out, _ = run("learn", "-C", str(self.api), "--memory", self.memory, "--origin", "production")
        self.assertEqual(code, 0)
        self.assertIn("BUG-0001 · api", out)
        self.assertIn("(stated in the", out)
        self.assertIn('"users logged out when two requests refresh an expired token"', out)
        code, out, _ = run("check", "-C", str(self.billing), "--memory", self.memory, "--strict")
        self.assertEqual(code, 1)
        self.assertIn("⚠ Bug pattern already met in another project", out)
        self.assertIn("src/client.ts:4", out)
        code, out, _ = run("list", "-C", str(self.billing), "--memory", self.memory)
        self.assertIn("Other projects in this diary: api (1)", out)
        code, out, _ = run("show", "BUG-0001", "-C", str(self.billing), "--memory", self.memory)
        self.assertIn("Lesson", out)

    def test_json_outputs(self):
        _, out, _ = run("learn", "-C", str(self.api), "--memory", self.memory, "--json")
        self.assertEqual(json.loads(out)[0]["id"], "BUG-0001")
        _, out, _ = run("check", "-C", str(self.billing), "--memory", self.memory, "--json")
        report = json.loads(out)
        self.assertEqual(report["findings"][0]["verdict"], "repeats")
        self.assertEqual(report["findings"][0]["evidence"][0]["line"], 4)

    def test_dry_run_and_not_a_bug_fix_are_not_saved(self):
        run("learn", "-C", str(self.api), "--memory", self.memory, "--dry-run")
        self.llm.card = {**self.llm.card, "is_bug_fix": False, "not_a_bug_fix_reason": "a rename"}
        _, out, _ = run("learn", "-C", str(self.api), "--memory", self.memory)
        self.assertIn("Not saved", out)
        _, out, _ = run("list", "-C", str(self.api), "--memory", self.memory)
        self.assertIn("The diary is empty.", out)

    def test_check_a_diff_file_and_forget(self):
        run("learn", "-C", str(self.api), "--memory", self.memory)
        patch = Path(self.tmp.name) / "change.diff"
        patch.write_text(git(self.billing, "diff"))
        code, out, _ = run(
            "check", "--diff", str(patch), "-C", self.tmp.name, "--memory", self.memory, "--project", "x"
        )
        self.assertEqual(code, 0)
        self.assertIn("src/client.ts:4", out)
        self.assertEqual(run("forget", "1", "-C", str(self.api), "--memory", self.memory)[1], "Forgot BUG-0001.\n")

    def test_errors_are_short(self):
        code, _, err = run("learn", "nope", "-C", str(self.api), "--memory", self.memory)
        self.assertEqual(code, 2)
        self.assertEqual(err, "bugdiary: unknown revision nope\n")
        code, _, err = run("show", "BUG-0042", "-C", str(self.api), "--memory", self.memory)
        self.assertEqual((code, err), (2, "bugdiary: no card BUG-0042\n"))


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = temporary_directory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_project_comes_from_the_file_then_the_remote_then_the_folder(self):
        repo = make_repo(self.root, "folder-name", [("init", {"a.txt": "a"})])
        with mock.patch.dict(os.environ, {"BUGDIARY_HOME": ""}):
            self.assertEqual(config.load(repo).project, "folder-name")
            git(repo, "remote", "add", "origin", "git@github.com:someone/billing-worker.git")
            self.assertEqual(config.load(repo).project, "billing-worker")
            (repo / "bugdiary.yml").write_text("project: worker  # the queue\nmemory: '~/team-diary'\n")
            settings = config.load(repo)
            self.assertEqual(settings.project, "worker")
            self.assertEqual(settings.memory, Path("~/team-diary").expanduser())
            self.assertEqual(config.load(repo, project="cli", memory="/tmp/x").project, "cli")

    def test_environment_beats_the_file(self):
        repo = make_repo(self.root, "r", [("init", {"bugdiary.yml": "memory: /from/file\n"})])
        with mock.patch.dict(os.environ, {"BUGDIARY_HOME": "/from/env"}):
            self.assertEqual(config.load(repo).memory, Path("/from/env"))

    def test_outside_a_repository(self):
        settings = config.load(self.root, memory="/tmp/m")
        self.assertIsNone(settings.repo)
        self.assertEqual(settings.project, "default")


class HookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = temporary_directory()
        self.repo = make_repo(Path(self.tmp.name), "r", [("init", {"a.txt": "a"})])

    def tearDown(self):
        self.tmp.cleanup()

    def test_install_and_uninstall(self):
        written = hooks.install(self.repo)
        self.assertEqual(sorted(path.name for path in written), ["post-commit", "pre-commit"])
        pre_commit = (self.repo / ".git" / "hooks" / "pre-commit").read_text()
        self.assertIn("-m bugdiary check --staged || true", pre_commit)
        self.assertTrue(os.access(self.repo / ".git" / "hooks" / "pre-commit", os.X_OK))
        self.assertIn("learn HEAD --quiet", (self.repo / ".git" / "hooks" / "post-commit").read_text())
        strict = hooks.pre_commit(strict=True)
        self.assertIn("-m bugdiary check --staged --strict\n", strict)
        self.assertNotIn("|| true", strict)
        self.assertEqual(len(hooks.uninstall(self.repo)), 2)
        self.assertEqual(hooks.uninstall(self.repo), [])

    def test_never_overwrites_someone_elses_hook(self):
        existing = self.repo / ".git" / "hooks" / "pre-commit"
        existing.parent.mkdir(parents=True, exist_ok=True)
        existing.write_text("#!/bin/sh\nmake lint\n")
        with self.assertRaises(hooks.HookError):
            hooks.install(self.repo)
        self.assertEqual(existing.read_text(), "#!/bin/sh\nmake lint\n")
        self.assertFalse((self.repo / ".git" / "hooks" / "post-commit").exists())


if __name__ == "__main__":
    unittest.main()
