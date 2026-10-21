from __future__ import annotations

import json
import sqlite3
from array import array
from pathlib import Path

from .card import Card

CARDS_TABLE = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    revision TEXT NOT NULL,
    fixed_at TEXT,
    learned_at TEXT NOT NULL,
    origin TEXT NOT NULL,
    model TEXT NOT NULL,
    body TEXT NOT NULL,
    UNIQUE (project, revision)
)
"""
VECTORS_TABLE = """
CREATE TABLE IF NOT EXISTS vectors (
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    model TEXT NOT NULL,
    digest TEXT NOT NULL,
    vector BLOB NOT NULL,
    PRIMARY KEY (card_id, model)
)
"""


class Diary:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(str(path), timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.execute("PRAGMA journal_mode = WAL")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            self.db.execute(CARDS_TABLE)
            self.db.execute(VECTORS_TABLE)
            columns = {row["name"] for row in self.db.execute("PRAGMA table_info(vectors)")}
            if "digest" not in columns:
                self.db.execute("DROP TABLE vectors")
                self.db.execute(VECTORS_TABLE)

    def close(self) -> None:
        self.db.close()

    def save(self, card: Card) -> int:
        values = (
            card.project,
            card.revision,
            card.fixed_at,
            card.learned_at,
            card.origin,
            card.model,
            json.dumps(card.body(), ensure_ascii=False),
        )
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            existing = self.db.execute(
                "SELECT id FROM cards WHERE project = ? AND revision = ?", (card.project, card.revision)
            ).fetchone()
            if existing:
                card.id = existing["id"]
                self.db.execute(
                    "UPDATE cards SET project = ?, revision = ?, fixed_at = ?, learned_at = ?, origin = ?, model = ?,"
                    " body = ? WHERE id = ?",
                    (*values, card.id),
                )
                self.db.execute("DELETE FROM vectors WHERE card_id = ?", (card.id,))
            else:
                cursor = self.db.execute(
                    "INSERT INTO cards (project, revision, fixed_at, learned_at, origin, model, body)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    values,
                )
                card.id = cursor.lastrowid
        return card.id

    def get(self, card_id: int) -> Card | None:
        row = self.db.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        return self.to_card(row) if row else None

    def cards(self, project: str | None = None) -> list[Card]:
        if project:
            rows = self.db.execute("SELECT * FROM cards WHERE project = ? ORDER BY id", (project,))
        else:
            rows = self.db.execute("SELECT * FROM cards ORDER BY id")
        return [self.to_card(row) for row in rows]

    def projects(self) -> list[tuple[str, int]]:
        rows = self.db.execute("SELECT project, COUNT(*) AS n FROM cards GROUP BY project ORDER BY project")
        return [(row["project"], row["n"]) for row in rows]

    def forget(self, card_id: int) -> bool:
        with self.db:
            return self.db.execute("DELETE FROM cards WHERE id = ?", (card_id,)).rowcount > 0

    def put_vector(self, card_id: int, model: str, vector: list[float], digest: str) -> bool:
        blob = array("f", vector).tobytes()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.db.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
            if row is None or self.to_card(row).digest() != digest:
                return False
            self.db.execute(
                "INSERT OR REPLACE INTO vectors (card_id, model, digest, vector) VALUES (?, ?, ?, ?)",
                (card_id, model, digest, blob),
            )
        return True

    def vectors(self, model: str) -> dict[int, tuple[str, list[float]]]:
        rows = self.db.execute("SELECT card_id, digest, vector FROM vectors WHERE model = ?", (model,))
        out = {}
        for row in rows:
            values = array("f")
            values.frombytes(row["vector"])
            out[row["card_id"]] = (row["digest"], values.tolist())
        return out

    @staticmethod
    def to_card(row: sqlite3.Row) -> Card:
        return Card.from_row(dict(row), json.loads(row["body"]))
