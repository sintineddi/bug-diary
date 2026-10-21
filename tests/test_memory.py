import sqlite3
import threading
import unittest
from pathlib import Path

from bugdiary.card import Card, Claim, label, parse_label
from bugdiary.memory import Diary

from .fakes import temporary_directory


def card(project: str = "api", revision: str = "abc123", pattern: str = "race") -> Card:
    return Card(
        project=project,
        revision=revision,
        fixed_at="2026-10-12T10:00:00+02:00",
        origin="production",
        symptom=Claim("Users logged out.", "stated", "message", "users logged out"),
        root_cause=Claim("Two refreshes.", "inferred", "code", ""),
        pattern=pattern,
        fix="Shared promise.",
        guard="refreshing",
        lesson="Share the refresh.",
        model="fake",
        learned_at="2026-10-20T10:00:00+00:00",
    )


class DiaryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = temporary_directory()
        self.diary = Diary(Path(self.tmp.name) / "nested" / "diary.db")

    def tearDown(self):
        self.diary.close()
        self.tmp.cleanup()

    def test_save_and_read_back(self):
        first = self.diary.save(card())
        second = self.diary.save(card(project="worker"))
        self.assertEqual((first, second), (1, 2))
        stored = self.diary.get(first)
        self.assertEqual(stored.symptom, Claim("Users logged out.", "stated", "message", "users logged out"))
        self.assertEqual(stored.label, "BUG-0001")
        self.assertEqual([item.project for item in self.diary.cards("worker")], ["worker"])
        self.assertEqual(self.diary.projects(), [("api", 1), ("worker", 1)])

    def test_learning_the_same_fix_again_updates_it_and_drops_its_vector(self):
        first = card()
        card_id = self.diary.save(first)
        self.assertTrue(self.diary.put_vector(card_id, "embed", [0.5, 0.25], first.digest()))
        self.assertEqual(self.diary.vectors("embed"), {card_id: (first.digest(), [0.5, 0.25])})
        self.assertEqual(self.diary.save(card(pattern="new pattern")), card_id)
        self.assertEqual(self.diary.get(card_id).pattern, "new pattern")
        self.assertEqual(self.diary.vectors("embed"), {})

    def test_a_vector_of_an_older_version_is_refused(self):
        first = card()
        card_id = self.diary.save(first)
        self.diary.save(card(pattern="relearned meanwhile"))
        self.assertFalse(self.diary.put_vector(card_id, "embed", [0.5], first.digest()))
        self.assertEqual(self.diary.vectors("embed"), {})
        self.assertFalse(self.diary.put_vector(99, "embed", [0.5], first.digest()))

    def test_an_old_vector_table_is_rebuilt(self):
        path = Path(self.tmp.name) / "old" / "diary.db"
        path.parent.mkdir()
        old = sqlite3.connect(str(path))
        old.execute("CREATE TABLE vectors (card_id INTEGER, model TEXT, vector BLOB, PRIMARY KEY (card_id, model))")
        old.execute("INSERT INTO vectors VALUES (1, 'embed', x'00')")
        old.commit()
        old.close()
        diary = Diary(path)
        self.assertEqual(diary.vectors("embed"), {})
        diary.close()

    def test_forget_removes_the_card_and_its_vector(self):
        stored = card()
        card_id = self.diary.save(stored)
        self.diary.put_vector(card_id, "embed", [1.0], stored.digest())
        self.assertTrue(self.diary.forget(card_id))
        self.assertFalse(self.diary.forget(card_id))
        self.assertIsNone(self.diary.get(card_id))
        self.assertEqual(self.diary.vectors("embed"), {})

    def test_concurrent_opens_upgrade_an_old_diary_once(self):
        for attempt in range(10):
            path = Path(self.tmp.name) / f"race-{attempt}" / "diary.db"
            path.parent.mkdir()
            old = sqlite3.connect(str(path))
            old.execute("PRAGMA journal_mode = WAL")
            old.execute("CREATE TABLE vectors (card_id INTEGER, model TEXT, vector BLOB, PRIMARY KEY (card_id, model))")
            old.commit()
            old.close()
            errors = []
            start = threading.Barrier(12)

            def open_diary():
                try:
                    start.wait()
                    Diary(path).close()
                except sqlite3.Error as error:
                    errors.append(error)

            threads = [threading.Thread(target=open_diary) for _ in range(12)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(errors, [])
            upgraded = sqlite3.connect(str(path))
            columns = {row[1] for row in upgraded.execute("PRAGMA table_info(vectors)")}
            upgraded.close()
            self.assertIn("digest", columns)

    def test_labels(self):
        self.assertEqual(label(7), "BUG-0007")
        self.assertEqual(parse_label("bug-0007"), 7)
        self.assertEqual(parse_label("12"), 12)
        with self.assertRaises(ValueError):
            parse_label("BUG-x")


if __name__ == "__main__":
    unittest.main()
