from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


TAG_SPLIT_RE = re.compile(r"[,;]+")


@dataclass(frozen=True)
class Note:
    id: int
    title: str
    body: str
    tags: str
    created_at: str
    updated_at: str
    pinned: bool


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
        self.connection.execute("PRAGMA foreign_keys = ON")
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
                tags TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT '',
                pinned INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._ensure_note_column("created_at", "TEXT NOT NULL DEFAULT ''")
        self._ensure_note_column("updated_at", "TEXT NOT NULL DEFAULT ''")
        self._ensure_note_column("pinned", "INTEGER NOT NULL DEFAULT 0")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS note_tags (
                note_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (note_id, tag_id),
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
            """
        )
        self._migrate_existing_notes()
        self.connection.commit()

    def _ensure_note_column(self, name: str, definition: str) -> None:
        columns = {
            str(row["name"])
            for row in self.connection.execute("PRAGMA table_info(notes)").fetchall()
        }
        if name not in columns:
            self.connection.execute(f"ALTER TABLE notes ADD COLUMN {name} {definition}")

    def _migrate_existing_notes(self) -> None:
        now = self._now()
        self.connection.execute("UPDATE notes SET created_at = ? WHERE created_at = ''", (now,))
        self.connection.execute("UPDATE notes SET updated_at = ? WHERE updated_at = ''", (now,))

        rows = self.connection.execute("SELECT id, tags FROM notes").fetchall()
        for row in rows:
            normalized_tags = normalize_tags(str(row["tags"]))
            note_id = int(row["id"])
            self.connection.execute(
                "UPDATE notes SET tags = ? WHERE id = ?",
                (normalized_tags, note_id),
            )
            self._sync_note_tags(note_id, normalized_tags)

    def list_notes(
        self,
        search: str = "",
        tag: str | None = None,
        tags: list[str] | None = None,
    ) -> list[Note]:
        query = "SELECT id, title, body, tags, created_at, updated_at, pinned FROM notes"
        clauses: list[str] = []
        params: list[str] = []

        search = search.strip()
        if search:
            like = f"%{search}%"
            clauses.append("(title LIKE ? OR body LIKE ? OR tags LIKE ?)")
            params.extend([like, like, like])

        selected_tags = self._selected_tag_keys(tag, tags)
        for tag_key in selected_tags:
            clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM note_tags
                    JOIN tags ON tags.id = note_tags.tag_id
                    WHERE note_tags.note_id = notes.id
                    AND tags.normalized_name = ?
                )
                """
            )
            params.append(tag_key)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY pinned DESC, updated_at DESC, id DESC"
        rows = self.connection.execute(query, params).fetchall()
        return [self._row_to_note(row) for row in rows]

    def get_note(self, note_id: int) -> Note | None:
        row = self.connection.execute(
            "SELECT id, title, body, tags, created_at, updated_at, pinned FROM notes WHERE id = ?",
            (note_id,),
        ).fetchone()
        return self._row_to_note(row) if row else None

    def create_note(self, title: str, body: str, tags: str, pinned: bool = False) -> int:
        title = title.strip() or "Без названия"
        normalized_tags = normalize_tags(tags)
        now = self._now()
        cursor = self.connection.execute(
            "INSERT INTO notes (title, body, tags, created_at, updated_at, pinned) VALUES (?, ?, ?, ?, ?, ?)",
            (title, body, normalized_tags, now, now, int(pinned)),
        )
        self._sync_note_tags(int(cursor.lastrowid), normalized_tags)
        self.connection.commit()
        return int(cursor.lastrowid)

    def update_note(
        self,
        note_id: int,
        title: str,
        body: str,
        tags: str,
        pinned: bool | None = None,
    ) -> None:
        title = title.strip() or "Без названия"
        normalized_tags = normalize_tags(tags)
        now = self._now()
        if pinned is None:
            self.connection.execute(
                "UPDATE notes SET title = ?, body = ?, tags = ?, updated_at = ? WHERE id = ?",
                (title, body, normalized_tags, now, note_id),
            )
        else:
            self.connection.execute(
                "UPDATE notes SET title = ?, body = ?, tags = ?, pinned = ?, updated_at = ? WHERE id = ?",
                (title, body, normalized_tags, int(pinned), now, note_id),
            )
        self._sync_note_tags(note_id, normalized_tags)
        self.connection.commit()

    def delete_note(self, note_id: int) -> None:
        self.connection.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
        self.connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self._delete_orphan_tags()
        self.connection.commit()

    def export_notes(self) -> list[dict[str, object]]:
        exported: list[dict[str, object]] = []
        for note in self.list_notes():
            exported.append(
                {
                    "id": note.id,
                    "title": note.title,
                    "body": note.body,
                    "tags": self._tags_to_list(note.tags),
                    "pinned": note.pinned,
                    "created_at": note.created_at,
                    "updated_at": note.updated_at,
                }
            )
        return exported

    def list_tags(self) -> list[str]:
        rows = self.connection.execute("SELECT name FROM tags ORDER BY lower(name)").fetchall()
        return [str(row["name"]) for row in rows]

    def _sync_note_tags(self, note_id: int, tags: str) -> None:
        self.connection.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
        for tag in normalize_tags(tags).split(", "):
            if not tag:
                continue

            key = tag.casefold()
            self.connection.execute(
                "INSERT OR IGNORE INTO tags (name, normalized_name) VALUES (?, ?)",
                (tag, key),
            )
            tag_row = self.connection.execute(
                "SELECT id FROM tags WHERE normalized_name = ?",
                (key,),
            ).fetchone()
            self.connection.execute(
                "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
                (note_id, int(tag_row["id"])),
            )
        self._delete_orphan_tags()

    def _delete_orphan_tags(self) -> None:
        self.connection.execute(
            """
            DELETE FROM tags
            WHERE NOT EXISTS (
                SELECT 1 FROM note_tags WHERE note_tags.tag_id = tags.id
            )
            """
        )

    @staticmethod
    def _selected_tag_keys(tag: str | None, tags: list[str] | None) -> list[str]:
        values: list[str] = []
        if tag:
            values.append(tag)
        if tags:
            values.extend(tags)

        keys: list[str] = []
        seen: set[str] = set()
        for value in values:
            for normalized_tag in normalize_tags(value).split(", "):
                key = normalized_tag.casefold()
                if key and key not in seen:
                    keys.append(key)
                    seen.add(key)
        return keys

    @staticmethod
    def _tags_to_list(tags: str) -> list[str]:
        if not tags:
            return []
        return [tag for tag in normalize_tags(tags).split(", ") if tag]

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds")

    @staticmethod
    def _row_to_note(row: sqlite3.Row) -> Note:
        return Note(
            id=int(row["id"]),
            title=str(row["title"]),
            body=str(row["body"]),
            tags=str(row["tags"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            pinned=bool(row["pinned"]),
        )
