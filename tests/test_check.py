import unittest
from pathlib import Path

from bugdiary import check, diffs, git, learn
from bugdiary.memory import Diary

from .fakes import FakeLLM, temporary_directory, token_repos


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = temporary_directory()
        root = Path(self.tmp.name)
        self.api, self.billing = token_repos(root)
        self.diary = Diary(root / "memory" / "diary.db")
        llm = FakeLLM()
        learn.remember(self.diary, llm, learn.learn(llm, learn.from_git(self.api, "HEAD", "api")).card)
        self.change = diffs.parse(git.worktree_diff(self.billing))

    def tearDown(self):
        self.diary.close()
        self.tmp.cleanup()

    def test_cross_project_alert_points_at_the_new_lines(self):
        llm = FakeLLM()
        report = check.check(llm, self.diary, self.change, "billing-worker")
        self.assertEqual(report.files, ["src/client.ts"])
        self.assertEqual(len(report.alerts), 1)
        alert = report.alerts[0]
        self.assertEqual(alert.card.project, "api")
        self.assertEqual(
            alert.evidence,
            [diffs.Hit("src/client.ts", 4, "this.token = await this.auth.refresh(this.token.refreshToken);")],
        )
        compare_prompt = llm.prompts[-1][1]
        self.assertIn("comes from another project", compare_prompt)
        self.assertIn("Guard: the refreshing promise in Session.getToken", compare_prompt)

    def test_an_alert_without_real_lines_is_downgraded(self):
        verdict = {**FakeLLM().verdict, "evidence": ["await refreshAllTheThings();"]}
        report = check.check(FakeLLM(verdict=verdict), self.diary, self.change, "billing-worker")
        self.assertEqual(report.alerts, [])
        self.assertEqual(report.findings[0].verdict, "unclear")
        self.assertEqual(report.findings[0].downgraded, "the lines it quoted are not in the change")

    def test_protected_needs_the_protection_in_the_change(self):
        claimed = {**FakeLLM().verdict, "verdict": "protected", "protection": ["this.refreshing ??= refresh()"]}
        report = check.check(FakeLLM(verdict=claimed), self.diary, self.change, "billing-worker")
        self.assertEqual(report.findings[0].verdict, "unclear")
        visible = {**claimed, "protection": ["if (this.token.expired) {"]}
        report = check.check(FakeLLM(verdict=visible), self.diary, self.change, "billing-worker")
        self.assertEqual(report.findings[0].verdict, "protected")

    def test_no_code_or_empty_diary_means_no_model_call(self):
        llm = FakeLLM()
        empty = Diary(Path(self.tmp.name) / "empty" / "diary.db")
        self.assertEqual(check.check(llm, empty, self.change, "billing-worker").findings, [])
        self.assertEqual(check.check(llm, self.diary, [], "billing-worker").files, [])
        self.assertEqual(llm.prompts, [])

    def test_retrieve_ranks_related_lessons_first(self):
        llm = FakeLLM()
        ranked = check.retrieve(llm, self.diary, ["concurrent token refreshes share the refresh"], top=5)
        self.assertEqual(len(ranked), 1)
        self.assertGreater(ranked[0][1], 0.3)
        self.assertEqual(check.retrieve(llm, self.diary, ["   "]), [])
        self.assertEqual(check.retrieve(llm, self.diary, ["token refresh"], floor=1.01), [])

    def test_cosine(self):
        self.assertAlmostEqual(check.cosine([1.0, 0.0], [1.0, 0.0]), 1.0)
        self.assertAlmostEqual(check.cosine([1.0, 0.0], [0.0, 1.0]), 0.0)
        self.assertEqual(check.cosine([0.0], [0.0]), 0.0)


if __name__ == "__main__":
    unittest.main()
