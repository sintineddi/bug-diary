from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "gemma4:26b"
DEFAULT_EMBED_MODEL = "embeddinggemma"
RAW_BYTES = re.compile(r"(?:<0x[0-9A-Fa-f]{2}>)+")
MAX_ANSWER_TOKENS = 2048
SAMPLINGS = ({"temperature": 0, "seed": 7}, {"temperature": 0.6, "seed": 11})


class OllamaError(RuntimeError):
    pass


class AnswerError(OllamaError):
    pass


@dataclass
class Call:
    kind: str
    model: str
    seconds: float
    prompt_tokens: int
    output_tokens: int


class Ollama:
    def __init__(
        self,
        model: str | None = None,
        embed_model: str | None = None,
        host: str | None = None,
        num_ctx: int = 32768,
        timeout: float = 900,
    ):
        host = host or os.environ.get("OLLAMA_HOST") or DEFAULT_HOST
        self.host = (host if host.startswith("http") else "http://" + host).rstrip("/")
        self.model = model or os.environ.get("BUGDIARY_MODEL") or DEFAULT_MODEL
        self.embed_model = embed_model or os.environ.get("BUGDIARY_EMBED_MODEL") or DEFAULT_EMBED_MODEL
        self.num_ctx = num_ctx
        self.timeout = timeout
        self.calls: list[Call] = []

    def post(self, path: str, body: dict) -> dict:
        request = urllib.request.Request(
            self.host + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace").strip()
            if error.code == 404:
                raise OllamaError(f"{detail} (try: ollama pull {body.get('model')})") from None
            raise OllamaError(f"Ollama answered {error.code}: {detail[:300]}") from None
        except (urllib.error.URLError, ConnectionError, TimeoutError) as error:
            raise OllamaError(
                f"cannot reach Ollama at {self.host} ({error}); start the Ollama app or `ollama serve`"
            ) from None

    def chat_json(self, system: str, user: str, schema: dict, model: str | None = None) -> dict:
        body = {
            "model": model or self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "format": schema,
            "stream": False,
            "think": False,
        }
        problem = ""
        for sampling in SAMPLINGS:
            body["options"] = {**sampling, "num_ctx": self.num_ctx, "num_predict": MAX_ANSWER_TOKENS}
            started = time.monotonic()
            reply = self.post("/api/chat", body)
            self.calls.append(
                Call(
                    "chat",
                    body["model"],
                    time.monotonic() - started,
                    reply.get("prompt_eval_count", 0),
                    reply.get("eval_count", 0),
                )
            )
            if reply.get("done_reason") == "length":
                problem = f"the answer ran past {MAX_ANSWER_TOKENS} tokens"
                continue
            try:
                return parse_json(repair_bytes(reply.get("message", {}).get("content", "")))
            except ValueError as error:
                problem = str(error)
        raise AnswerError(f"{body['model']} gave no usable answer twice: {problem}")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        started = time.monotonic()
        reply = self.post("/api/embed", {"model": self.embed_model, "input": texts, "truncate": True})
        self.calls.append(
            Call("embed", self.embed_model, time.monotonic() - started, reply.get("prompt_eval_count", 0), 0)
        )
        vectors = reply.get("embeddings") or []
        if len(vectors) != len(texts):
            raise OllamaError(f"{self.embed_model} returned {len(vectors)} embeddings for {len(texts)} texts")
        return vectors

    def seconds(self, kind: str | None = None) -> float:
        return sum(call.seconds for call in self.calls if kind is None or call.kind == kind)


def repair_bytes(text: str) -> str:
    return RAW_BYTES.sub(
        lambda match: bytes.fromhex(re.sub("<0x|>", "", match.group(0))).decode("utf-8", "ignore"), text
    )


def parse_json(content: str) -> dict:
    text = content.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError(f"no JSON object in {content[:200]!r}")
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise ValueError(f"{error} in {content[:200]!r}") from None
    if not isinstance(value, dict):
        raise ValueError("the JSON value is not an object")
    return value
