from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
