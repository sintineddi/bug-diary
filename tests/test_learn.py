import unittest
from pathlib import Path

from bugdiary import learn
from bugdiary.card import Claim
from bugdiary.memory import Diary

from .fakes import SESSION_AFTER, TOKEN_CARD, FakeLLM, git, temporary_directory, token_repos, write

MESSAGE = "fix: users logged out when two requests refresh an expired token at once"


class QuoteTest(unittest.TestCase):
    def test_excerpt_returns_the_source_words(self):
        self.assertEqual(
            learn.excerpt("Users Logged Out when two requests", MESSAGE),
            "users logged out when two requests",
        )

    def test_excerpt_survives_one_broken_token_in_a_long_quote(self):
        quote = "users logged out when two�0 requests refresh an expired token at once"
        self.assertEqual(learn.excerpt(quote, MESSAGE), MESSAGE[5:])

    def test_excerpt_rejects_paraphrase_and_short_quotes(self):
        self.assertIsNone(learn.excerpt("customers saw stale prices for hours", MESSAGE))
        self.assertIsNone(learn.excerpt("logged out", MESSAGE))

    def test_locate_prefers_the_named_source_then_others(self):
        texts = {"message": MESSAGE, "tests": '+test("concurrent requests with an expired token refresh it once")'}
        self.assertEqual(learn.locate("expired token refresh it once", texts, "message")[0], "tests")
        self.assertEqual(learn.locate("users logged out ... an expired token at once", texts, "notes")[0], "message")
        self.assertIsNone(learn.locate("users logged out", {"code": MESSAGE}, "code"))

    def test_ground_downgrades_a_quote_it_cannot_find(self):
        rejected = []
        claim = learn.ground(
            {
                "text": "Prices were stale.",
                "basis": "stated",
                "source": "message",
                "quote": "prices were stale for hours",
            },
            {"message": MESSAGE},
            rejected,
        )
        self.assertEqual((claim.basis, claim.source), ("inferred", "code"))
        self.assertEqual(rejected, ["prices were stale for hours"])

    def test_ground_upgrades_a_claim_copied_from_a_source(self):
        claim = learn.ground(
            {"text": "Users logged out when two requests refresh an expired token.", "basis": "inferred", "quote": ""},
            {"message": MESSAGE},
            [],
        )
        self.assertEqual((claim.basis, claim.source), ("stated", "message"))
        self.assertEqual(claim.quote, "users logged out when two requests refresh an expired token")

    def test_ground_unknown(self):
        self.assertEqual(
            learn.ground({"text": "unknown", "basis": "inferred"}, {}, []), Claim("unknown", "unknown", "none", "")
        )
        self.assertEqual(learn.ground(None, {}, []).basis, "unknown")


class LearnFromGitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = temporary_directory()
        self.api, self.billing = token_repos(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_card_is_grounded_in_the_commit(self):
        fix = learn.from_git(self.api, "HEAD", "api")
        learned = learn.learn(FakeLLM(), fix, "production")
        card = learned.card
        self.assertTrue(learned.is_bug_fix)
        self.assertEqual(card.revision, git(self.api, "rev-parse", "HEAD").strip())
        self.assertEqual((card.symptom.basis, card.symptom.source), ("stated", "message"))
        self.assertEqual(card.symptom.quote, "users logged out when two requests refresh an expired token")
        self.assertEqual(card.identifiers, ["getToken", "refreshing"])
        self.assertEqual(card.evidence["dropped_identifiers"], ["NotInTheCode"])
        self.assertEqual(card.files, ["src/session.ts"])
        self.assertEqual(card.test_files, ["test/session.test.ts"])
        self.assertEqual(card.regression["then"], "refresh runs once")
        self.assertFalse(card.evidence["tests_executed"])
        self.assertEqual(card.evidence["sources"], ["message", "tests", "code"])

    def test_without_tests_there_is_no_regression_condition(self):
        fix = learn.from_git(self.api, "HEAD", "api")
        card = learn.learn(FakeLLM(), fix, include=("message", "code")).card
        self.assertIsNone(card.regression)
        self.assertEqual(card.evidence["sources"], ["message", "code"])

    def test_a_range_becomes_one_fix(self):
        head = git(self.api, "rev-parse", "HEAD").strip()
        self.assertEqual(learn.from_git(self.api, "HEAD~1..HEAD", "api").revision, head)
        write(self.api, {"src/session.ts": SESSION_AFTER + "export const retries = 1;\n"})
        git(self.api, "commit", "-qam", "fix: also reset refreshing on failure")
        fix = learn.from_git(self.api, "HEAD~2..HEAD", "api")
        self.assertEqual(
            fix.revision.split(".."),
            [git(self.api, "rev-parse", "HEAD~2").strip(), git(self.api, "rev-parse", "HEAD").strip()],
        )
        self.assertIn("fix: users logged out", fix.message)
        self.assertIn("also reset refreshing", fix.message)

    def test_not_a_bug_fix_is_reported(self):
        card = {**TOKEN_CARD, "is_bug_fix": False, "not_a_bug_fix_reason": "only renames a variable"}
        learned = learn.learn(FakeLLM(card=card), learn.from_git(self.api, "HEAD", "api"))
        self.assertFalse(learned.is_bug_fix)
        self.assertEqual(learned.reason, "only renames a variable")

    def test_a_message_about_another_change_is_ignored(self):
        mismatch = {**TOKEN_CARD, "message_matches": "no", "message_mismatch": "it talks about batches"}
        clean = {**TOKEN_CARD, "message_matches": "no message", "symptom": {"text": "unknown", "basis": "unknown"}}
        llm = FakeLLM(cards=[mismatch, clean])
        card = learn.learn(llm, learn.from_git(self.api, "HEAD", "api")).card
        self.assertEqual(len(llm.prompts), 2)
        self.assertIn("[MESSAGE]", llm.prompts[0][1])
        self.assertNotIn("[MESSAGE]", llm.prompts[1][1])
        self.assertEqual(card.evidence["message_ignored"], "it talks about batches")
        self.assertEqual(card.evidence["sources"], ["tests", "code"])
        self.assertEqual(card.symptom.basis, "unknown")

    def test_a_partly_matching_message_is_ignored_too(self):
        partly = {**TOKEN_CARD, "message_matches": "partly", "message_mismatch": "also mentions logging"}
        llm = FakeLLM(cards=[partly, {**TOKEN_CARD, "message_matches": "no message"}])
        card = learn.learn(llm, learn.from_git(self.api, "HEAD", "api")).card
        self.assertEqual(len(llm.prompts), 2)
        self.assertEqual(card.evidence["message_ignored"], "also mentions logging")

    def test_a_matching_message_is_kept(self):
        llm = FakeLLM()
        card = learn.learn(llm, learn.from_git(self.api, "HEAD", "api")).card
        self.assertEqual(len(llm.prompts), 1)
        self.assertEqual(card.evidence["message_ignored"], "")

    def test_a_fix_without_code_is_refused(self):
        fix = learn.Fix("api", "abc", "", "docs", [])
        with self.assertRaises(learn.LearnError):
            learn.learn(FakeLLM(), fix)

    def test_remember_stores_the_card_and_its_vector(self):
        llm = FakeLLM()
        card = learn.learn(llm, learn.from_git(self.api, "HEAD", "api")).card
        diary = Diary(Path(self.tmp.name) / "memory" / "diary.db")
        self.assertIsNone(learn.remember(diary, llm, card))
        self.assertEqual(diary.get(card.id).pattern, "race between concurrent token refreshes")
        self.assertIn(card.id, diary.vectors("fake-embed"))


if __name__ == "__main__":
    unittest.main()
