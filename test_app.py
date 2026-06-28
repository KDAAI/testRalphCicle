import unittest

from app import delete_confirmation_for, format_note_list_label
from storage import Note


def make_note(title: str, tags: str = "", pinned: bool = False) -> Note:
    return Note(
        id=1,
        title=title,
        body="Body",
        tags=tags,
        created_at="2026-06-28T00:00:00+00:00",
        updated_at="2026-06-28T00:00:00+00:00",
        pinned=pinned,
    )


class AppFormattingTest(unittest.TestCase):
    def test_pinned_note_list_label_uses_configured_prefix(self) -> None:
        note = make_note("Important", "work", pinned=True)

        self.assertEqual(format_note_list_label(note), "[Р—Р°РєСЂРµРїР»РµРЅРѕ] Important  [work]")

    def test_pinned_delete_confirmation_is_stronger(self) -> None:
        regular_title, regular_message = delete_confirmation_for(make_note("Regular"))
        pinned_title, pinned_message = delete_confirmation_for(make_note("Important", pinned=True))

        self.assertNotEqual(pinned_title, regular_title)
        self.assertIn("Р·Р°РєСЂРµРїР»РµРЅРЅСѓСЋ", pinned_message)
        self.assertIn("Important", pinned_message)


if __name__ == "__main__":
    unittest.main()
