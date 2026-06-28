from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from storage import NotesStore, normalize_tags


class NotesStoreTest(unittest.TestCase):
    def test_normalize_tags_trims_and_deduplicates(self) -> None:
        self.assertEqual(normalize_tags(" работа, идеи; работа,  Срочно "), "работа, идеи, Срочно")

    def test_create_search_filter_update_and_delete_note(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = NotesStore(Path(temp_dir) / "notes.db")
            try:
                note_id = store.create_note("План", "Купить бумагу", "дом, идеи")

                self.assertEqual(len(store.list_notes(search="бумагу")), 1)
                self.assertEqual(len(store.list_notes(tag="идеи")), 1)
                self.assertEqual(store.list_tags(), ["дом", "идеи"])

                store.update_note(note_id, "План 2", "Купить ручку", "работа")
                updated = store.get_note(note_id)

                self.assertIsNotNone(updated)
                self.assertEqual(updated.title, "План 2")
                self.assertEqual(updated.tags, "работа")
                self.assertEqual(len(store.list_notes(tag="идеи")), 0)

                store.delete_note(note_id)
                self.assertEqual(store.list_notes(), [])
            finally:
                store.close()

    def test_old_database_is_migrated_with_metadata_and_normalized_tags(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "notes.db"
            connection = sqlite3.connect(db_path)
            connection.execute(
                "CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL, tags TEXT NOT NULL DEFAULT '')"
            )
            connection.execute(
                "INSERT INTO notes (title, body, tags) VALUES (?, ?, ?)",
                ("Old note", "Legacy body", "Work, ideas; work"),
            )
            connection.commit()
            connection.close()

            store = NotesStore(db_path)
            store.close()
            store = NotesStore(db_path)
            try:
                note = store.list_notes(tag="ideas")[0]

                self.assertEqual(note.title, "Old note")
                self.assertEqual(note.body, "Legacy body")
                self.assertEqual(note.tags, "Work, ideas")
                self.assertEqual(store.list_tags(), ["ideas", "Work"])

                columns = {
                    row["name"]
                    for row in store.connection.execute("PRAGMA table_info(notes)").fetchall()
                }
                self.assertTrue({"created_at", "updated_at", "pinned"}.issubset(columns))

                tag_rows = store.connection.execute("SELECT name FROM tags ORDER BY lower(name)").fetchall()
                relationship_count = store.connection.execute("SELECT COUNT(*) AS count FROM note_tags").fetchone()
                self.assertEqual([row["name"] for row in tag_rows], ["ideas", "Work"])
                self.assertEqual(relationship_count["count"], 2)
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
