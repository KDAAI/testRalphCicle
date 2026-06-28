from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


TAG_SPLIT_RE = re.compile(r"[,;]+")


@dataclass(frozen=True)
class Note:
    id: int
    title: str
    body: str
    tags: str


def normalize_tags(value: str) -> str:
    tags: list[str] = []
    seen: set[str] = set()

    for raw_tag in TAG_SPLIT_RE.split(value):
        tag = raw_tag.strip()
        key = tag.casefold()
        if tag and key not in seen:
            tags.append(tag)
            seen.add(key)

    return ", ".join(tags)


class NotesStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        self.connection.close()

    def _ensure_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT ''
            )
            """
        )
        self.connection.commit()

    def list_notes(self, search: str = "", tag: str | None = None) -> list[Note]:
        query = "SELECT id, title, body, tags FROM notes"
        clauses: list[str] = []
        params: list[str] = []

        search = search.strip()
        if search:
            like = f"%{search}%"
            clauses.append("(title LIKE ? OR body LIKE ? OR tags LIKE ?)")
            params.extend([like, like, like])

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY lower(title), id DESC"
        rows = self.connection.execute(query, params).fetchall()
        notes = [self._row_to_note(row) for row in rows]

        if tag:
            tag_key = tag.casefold()
            notes = [
                note
                for note in notes
                if tag_key in {item.casefold() for item in normalize_tags(note.tags).split(", ") if item}
            ]

        return notes

    def get_note(self, note_id: int) -> Note | None:
        row = self.connection.execute(
            "SELECT id, title, body, tags FROM notes WHERE id = ?",
            (note_id,),
        ).fetchone()
        return self._row_to_note(row) if row else None

    def create_note(self, title: str, body: str, tags: str) -> int:
        title = title.strip() or "Без названия"
        normalized_tags = normalize_tags(tags)
        cursor = self.connection.execute(
            "INSERT INTO notes (title, body, tags) VALUES (?, ?, ?)",
            (title, body, normalized_tags),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def update_note(self, note_id: int, title: str, body: str, tags: str) -> None:
        title = title.strip() or "Без названия"
        normalized_tags = normalize_tags(tags)
        self.connection.execute(
            "UPDATE notes SET title = ?, body = ?, tags = ? WHERE id = ?",
            (title, body, normalized_tags, note_id),
        )
        self.connection.commit()

    def delete_note(self, note_id: int) -> None:
        self.connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.connection.commit()

    def list_tags(self) -> list[str]:
        rows = self.connection.execute("SELECT tags FROM notes WHERE tags <> ''").fetchall()
        tags_by_key: dict[str, str] = {}

        for row in rows:
            for tag in normalize_tags(row["tags"]).split(", "):
                if tag:
                    tags_by_key.setdefault(tag.casefold(), tag)

        return sorted(tags_by_key.values(), key=str.casefold)

    @staticmethod
    def _row_to_note(row: sqlite3.Row) -> Note:
        return Note(
            id=int(row["id"]),
            title=str(row["title"]),
            body=str(row["body"]),
            tags=str(row["tags"]),
        )
