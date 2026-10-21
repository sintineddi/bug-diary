import unittest
from pathlib import Path

from bugdiary import check, diffs, git, learn
from bugdiary.memory import Diary
from bugdiary.ollama import AnswerError, OllamaError
from bugdiary.card import Card, Claim
from bugdiary.prompts import COMPARE_SYSTEM, DESCRIBE_SYSTEM, FAMILY_SYSTEM
from bugdiary.render import Style, report_lines

from .fakes import FakeLLM, added_file, temporary_directory, token_repos
from .fakes import git as fakes_git
from .fakes import write as fakes_write


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
        self.assertIn("The diary card comes from another project", compare_prompt)
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

    def test_a_large_change_is_read_in_several_passes(self):
        llm = FakeLLM()
        files = diffs.parse(added_file("src/a.ts", 250) + added_file("src/b.ts", 250))
        self.assertEqual(len(check.batches(check.code_files(files))), 2)
        report = check.check(llm, self.diary, files, "billing-worker")
        self.assertEqual(len([system for system, _ in llm.prompts if system == DESCRIBE_SYSTEM]), 2)
        self.assertEqual(report.partial, [])
        self.assertEqual(len(report.findings), 1)

    def test_a_file_too_large_for_one_pass_is_reported(self):
        files = diffs.parse(added_file("src/huge.ts", 600))
        report = check.check(FakeLLM(), self.diary, files, "billing-worker")
        self.assertEqual(report.partial, ["src/huge.ts"])
        text = "\n".join(report_lines(report, Style(False)))
        self.assertIn("No known bug pattern in what could be checked.", text)
        self.assertIn("Too large to read whole: src/huge.ts", text)

    def test_retrieve_ranks_related_lessons_first(self):
        llm = FakeLLM()
        ranked = check.retrieve(llm, self.diary, ["concurrent token refreshes share the refresh"], top=5)
        self.assertEqual(len(ranked), 1)
        self.assertGreater(ranked[0][1], 0.3)
        self.assertEqual(check.retrieve(llm, self.diary, ["   "]), [])
        self.assertEqual(check.retrieve(llm, self.diary, ["token refresh"], floor=1.01), [])

    def test_stale_vectors_are_computed_again(self):
        llm = FakeLLM()
        card = self.diary.cards()[0]
        self.diary.db.execute("UPDATE vectors SET digest = 'stale'")
        self.diary.db.commit()
        vectors = check.ensure_vectors(llm, self.diary, [card])
        digest, stored = self.diary.vectors(llm.embed_model)[card.id]
        self.assertEqual(digest, card.digest())
        for kept, computed in zip(stored, vectors[card.id]):
            self.assertAlmostEqual(kept, computed, places=6)

    def test_before_the_first_commit_the_working_copy_is_checked(self):
        repo = Path(self.tmp.name) / "fresh"
        repo.mkdir()
        fakes_git(repo, "init", "-q", "-b", "main")
        fakes_write(repo, {"src/a.ts": "const staged = 1;\n"})
        fakes_git(repo, "add", "src/a.ts")
        fakes_write(
            repo, {"src/a.ts": "const staged = 1;\nconst edited = 2;\n", "src/new.ts": "const untracked = 3;\n"}
        )
        text = git.worktree_diff(repo)
        self.assertIn("+const edited = 2;", text)
        self.assertIn("+const untracked = 3;", text)

    def save_card(self, project: str, pattern: str, guard: str) -> int:
        card = Card(
            project=project,
            revision=f"{project}-{pattern}",
            fixed_at="2020-01-01T00:00:00Z",
            origin="unknown",
            symptom=Claim("unknown"),
            root_cause=Claim(pattern, "inferred", "code"),
            pattern=pattern,
            fix=guard,
            guard=guard,
            lesson=pattern,
        )
        llm = FakeLLM()
        learn.remember(self.diary, llm, card)
        return card.id

    def test_each_lesson_is_compared_alone_and_its_kind_is_shown(self):
        sibling = self.save_card(
            "worker", "concurrent token refreshes share the refresh promise", "shared refresh promise"
        )
        stranger = self.save_card(
            "unzip", "archive entries escaping the extraction directory", "resolved path prefix check"
        )
        llm = FakeLLM()
        report = check.check(llm, self.diary, self.change, "billing-worker")
        compares = [user for system, user in llm.prompts if system == COMPARE_SYSTEM]
        self.assertEqual(len(compares), 3)
        self.assertTrue(all("OTHER FIXES" not in prompt for prompt in compares))
        alert = next(alert for alert in report.alerts if alert.card.label == "BUG-0001")
        kin = [card.label for card in alert.family]
        self.assertIn(f"BUG-{sibling:04d}", kin)
        self.assertNotIn(f"BUG-{stranger:04d}", kin)
        self.assertIn("Same kind", "\n".join(report_lines(report, Style(False))))

    def test_by_kind_shows_the_model_the_other_fixes_of_that_kind(self):
        sibling = self.save_card(
            "worker", "concurrent token refreshes share the refresh promise", "shared refresh promise"
        )
        stranger = self.save_card(
            "unzip", "archive entries escaping the extraction directory", "resolved path prefix check"
        )
        llm = FakeLLM()
        check.check(llm, self.diary, self.change, "billing-worker", by_kind=True)
        compares = [user for system, user in llm.prompts if system == FAMILY_SYSTEM]
        self.assertEqual(len(compares), 2)
        tokens = next(prompt for prompt in compares if f"BUG-{sibling:04d}" in prompt)
        archives = next(prompt for prompt in compares if f"BUG-{stranger:04d}" in prompt)
        self.assertIn("OTHER FIXES OF THE SAME KIND OF BUG", tokens)
        self.assertIn("BUG-0001", tokens)
        self.assertNotIn(f"BUG-{stranger:04d}", tokens)
        self.assertNotIn("BUG-0001", archives)
        self.assertNotIn(f"BUG-{sibling:04d}", archives)

    def test_by_kind_alert_names_the_precedent_the_model_chose(self):
        sibling = self.save_card(
            "worker", "concurrent token refreshes share the refresh promise", "shared refresh promise"
        )
        chosen = {**FakeLLM().verdict, "precedents": [f"bug-{sibling:04d}", "BUG-0099"]}
        report = check.check(FakeLLM(verdict=chosen), self.diary, self.change, "billing-worker", by_kind=True)
        self.assertEqual(report.alerts[0].card.id, sibling)
        self.assertEqual([card.label for card in report.alerts[0].family], ["BUG-0001"])
        unknown = {**FakeLLM().verdict, "precedents": ["BUG-0099"]}
        report = check.check(FakeLLM(verdict=unknown), self.diary, self.change, "billing-worker", by_kind=True)
        self.assertIn(report.alerts[0].card.id, (1, sibling))
        self.assertNotEqual(report.alerts[0].card.label, "BUG-0099")

    def failing_compare(self, error: Exception) -> FakeLLM:
        llm = FakeLLM()
        answer = llm.chat_json

        def chat_json(system, user, schema, model=None):
            if system == COMPARE_SYSTEM:
                raise error
            return answer(system, user, schema, model)

        llm.chat_json = chat_json
        return llm

    def test_a_model_without_usable_answer_leaves_the_check_incomplete(self):
        llm = self.failing_compare(AnswerError("gemma4:26b gave no usable answer twice"))
        report = check.check(llm, self.diary, self.change, "billing-worker")
        self.assertEqual(report.findings[0].verdict, "unclear")
        self.assertIn("no usable answer", report.findings[0].downgraded)
        self.assertEqual(report.incomplete, ["BUG-0001"])
        text = "\n".join(report_lines(report, Style(False)))
        self.assertIn("No known bug pattern in what could be checked.", text)
        self.assertIn("Not compared, the model gave no usable answer: BUG-0001", text)

    def test_a_failed_batch_stays_visible_whatever_the_other_batch_says(self):
        evidence = 'let value1 = "' + "x" * 60 + '";'
        repeats = {**FakeLLM().verdict, "evidence": [evidence]}
        files = diffs.parse(added_file("src/a.ts", 250) + added_file("src/b.ts", 250))
        for failing in (1, 2):
            llm = FakeLLM(verdict=repeats)
            answer = llm.chat_json
            compares = []

            def chat_json(system, user, schema, model=None, failing=failing, answer=answer, compares=compares):
                if system == COMPARE_SYSTEM:
                    compares.append(user)
                    if len(compares) == failing:
                        raise AnswerError("gemma4:26b gave no usable answer twice")
                return answer(system, user, schema, model)

            llm.chat_json = chat_json
            report = check.check(llm, self.diary, files, "billing-worker")
            self.assertEqual(len(compares), 2)
            self.assertEqual(report.incomplete, ["BUG-0001"])

    def test_an_unreachable_model_is_an_error(self):
        llm = self.failing_compare(OllamaError("cannot reach Ollama"))
        with self.assertRaises(OllamaError):
            check.check(llm, self.diary, self.change, "billing-worker")

    def test_cosine(self):
        self.assertAlmostEqual(check.cosine([1.0, 0.0], [1.0, 0.0]), 1.0)
        self.assertAlmostEqual(check.cosine([1.0, 0.0], [0.0, 1.0]), 0.0)
        self.assertEqual(check.cosine([0.0], [0.0]), 0.0)


if __name__ == "__main__":
    unittest.main()
