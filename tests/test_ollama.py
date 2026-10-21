import json
import unittest
from unittest import mock

from bugdiary.ollama import MAX_ANSWER_TOKENS, AnswerError, Ollama, OllamaError


def replying(llm: Ollama, replies: list[dict]) -> tuple[mock._patch, list[dict]]:
    sent = []

    def post(path: str, body: dict) -> dict:
        sent.append(json.loads(json.dumps(body)))
        return replies.pop(0)

    return mock.patch.object(llm, "post", side_effect=post), sent


class ChatJsonTest(unittest.TestCase):
    def test_a_runaway_answer_is_tried_again_with_some_randomness(self):
        llm = Ollama(host="http://localhost:1")
        patch, sent = replying(
            llm,
            [
                {"done_reason": "length", "message": {"content": '{"reason": "again and again'}},
                {"done_reason": "stop", "message": {"content": '{"ok": "yes"}'}},
            ],
        )
        with patch:
            self.assertEqual(llm.chat_json("system", "user", {}), {"ok": "yes"})
        self.assertEqual([body["options"]["temperature"] for body in sent], [0, 0.6])
        self.assertEqual({body["options"]["num_predict"] for body in sent}, {MAX_ANSWER_TOKENS})

    def test_two_unusable_answers_raise(self):
        llm = Ollama(host="http://localhost:1")
        patch, _ = replying(
            llm,
            [
                {"done_reason": "stop", "message": {"content": "not json"}},
                {"done_reason": "length", "message": {"content": '{"cut'}},
            ],
        )
        with patch, self.assertRaises(AnswerError) as raised:
            llm.chat_json("system", "user", {})
        self.assertIn("no usable answer twice", str(raised.exception))
        self.assertIsInstance(raised.exception, OllamaError)

    def test_raw_byte_tokens_are_repaired(self):
        llm = Ollama(host="http://localhost:1")
        patch, _ = replying(
            llm, [{"done_reason": "stop", "message": {"content": '{"quote": "two<0xC2><0xA0>requests"}'}}]
        )
        with patch:
            self.assertEqual(llm.chat_json("system", "user", {}), {"quote": "two requests"})


if __name__ == "__main__":
    unittest.main()
