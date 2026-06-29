from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import time
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

    def test_notes_return_metadata_and_sort_by_pin_then_modified_time(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = NotesStore(Path(temp_dir) / "notes.db")
            try:
                first_id = store.create_note("First", "Body", "Work; Ideas")
                time.sleep(0.01)
                second_id = store.create_note("Second", "Body", "Ideas")

                first = store.get_note(first_id)
                self.assertIsNotNone(first)
                self.assertEqual(first.tags, "Work, Ideas")
                self.assertFalse(first.pinned)
                self.assertTrue(first.created_at)
                self.assertEqual(first.created_at, first.updated_at)

                time.sleep(0.01)
                store.update_note(first_id, "First", "Body", "Work; Ideas", pinned=True)
                pinned = store.get_note(first_id)
                self.assertIsNotNone(pinned)
                self.assertTrue(pinned.pinned)
                self.assertGreater(pinned.updated_at, pinned.created_at)

                notes = store.list_notes()
                self.assertEqual([note.id for note in notes], [first_id, second_id])

                time.sleep(0.01)
                store.update_note(second_id, "Second updated", "Body", "Ideas")
                notes = store.list_notes()
                self.assertEqual([note.id for note in notes], [first_id, second_id])
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

    def test_list_notes_filters_by_multiple_tags_with_search(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = NotesStore(Path(temp_dir) / "notes.db")
            try:
                store.create_note("Work launch", "Prepare urgent launch checklist", "work, urgent; client")
                store.create_note("Work someday", "Collect ideas", "work, ideas")
                store.create_note("Home urgent", "Buy medicine", "home, urgent")

                notes = store.list_notes(tags=["work", "urgent"])
                self.assertEqual([note.title for note in notes], ["Work launch"])

                notes = store.list_notes(search="checklist", tags=["work", "urgent"])
                self.assertEqual([note.title for note in notes], ["Work launch"])

                notes = store.list_notes(search="medicine", tags=["work", "urgent"])
                self.assertEqual(notes, [])
            finally:
                store.close()

    def test_list_tags_returns_normalized_unique_tags_sorted_case_insensitively(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = NotesStore(Path(temp_dir) / "notes.db")
            try:
                store.create_note("One", "Body", " Beta; alpha, beta ")
                store.create_note("Two", "Body", "ALPHA; Gamma")

                self.assertEqual(store.list_tags(), ["alpha", "Beta", "Gamma"])
            finally:
                store.close()

    def test_export_notes_returns_all_restorable_fields_with_tag_lists(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = NotesStore(Path(temp_dir) / "notes.db")
            try:
                pinned_id = store.create_note("Pinned", "Important body", "work, urgent", pinned=True)
                regular_id = store.create_note("Regular", "Other body", "ideas")

                exported = store.export_notes()

                self.assertEqual([note["id"] for note in exported], [pinned_id, regular_id])
                self.assertEqual(
                    exported[0],
                    {
                        "id": pinned_id,
                        "title": "Pinned",
                        "body": "Important body",
                        "tags": ["work", "urgent"],
                        "pinned": True,
                        "created_at": exported[0]["created_at"],
                        "updated_at": exported[0]["updated_at"],
                    },
                )
                self.assertTrue(exported[0]["created_at"])
                self.assertTrue(exported[0]["updated_at"])
                self.assertEqual(exported[1]["tags"], ["ideas"])
                self.assertFalse(exported[1]["pinned"])
            finally:
                store.close()

    def test_import_notes_adds_new_notes_and_skips_exact_title_body_duplicates(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = NotesStore(Path(temp_dir) / "notes.db")
            try:
                store.create_note("Plan", "Existing body", "work")

                result = store.import_notes(
                    [
                        {"title": "Plan", "body": "Existing body", "tags": ["work", "duplicate"]},
                        {"title": "Plan", "body": "Different body", "tags": ["work"]},
                    ]
                )

                self.assertEqual(result.added, 1)
                self.assertEqual(result.skipped_duplicates, 1)
                self.assertEqual([note.body for note in store.list_notes(search="Plan")], ["Different body", "Existing body"])
                self.assertEqual(store.list_tags(), ["work"])
            finally:
                store.close()

    def test_import_notes_accepts_list_and_comma_separated_tag_formats(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = NotesStore(Path(temp_dir) / "notes.db")
            try:
                result = store.import_notes(
                    [
                        {"title": "List tags", "body": "Body", "tags": ["work", "urgent"]},
                        {"title": "String tags", "body": "Body", "tags": "home, ideas; home"},
                    ]
                )

                self.assertEqual(result.added, 2)
                self.assertEqual(result.skipped_duplicates, 0)
                self.assertEqual(store.get_note(1).tags, "work, urgent")
                self.assertEqual(store.get_note(2).tags, "home, ideas")
                self.assertEqual(store.list_tags(), ["home", "ideas", "urgent", "work"])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
