import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app import (
    AutosaveController,
    NewDraftGuard,
    delete_confirmation_for,
    delete_shortcut_allows_delete,
    format_note_list_label,
    read_notes_import,
    write_notes_export,
)
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
    def test_delete_shortcut_ignores_editing_fields(self) -> None:
        self.assertFalse(delete_shortcut_allows_delete("Entry"))
        self.assertFalse(delete_shortcut_allows_delete("TEntry"))
        self.assertFalse(delete_shortcut_allows_delete("Text"))
        self.assertFalse(delete_shortcut_allows_delete("Spinbox"))
        self.assertTrue(delete_shortcut_allows_delete("Listbox"))
        self.assertTrue(delete_shortcut_allows_delete(None))

    def test_pinned_note_list_label_uses_configured_prefix(self) -> None:
        note = make_note("Important", "work", pinned=True)

        self.assertEqual(format_note_list_label(note), "[Р—Р°РєСЂРµРїР»РµРЅРѕ] Important  [work]")

    def test_pinned_delete_confirmation_is_stronger(self) -> None:
        regular_title, regular_message = delete_confirmation_for(make_note("Regular"))
        pinned_title, pinned_message = delete_confirmation_for(make_note("Important", pinned=True))

        self.assertNotEqual(pinned_title, regular_title)
        self.assertIn("Р·Р°РєСЂРµРїР»РµРЅРЅСѓСЋ", pinned_message)
        self.assertIn("Important", pinned_message)

    def test_write_notes_export_writes_readable_json_payload(self) -> None:
        notes = [
            {
                "id": 7,
                "title": "Backup",
                "body": "Body",
                "tags": ["work", "urgent"],
                "pinned": True,
                "created_at": "2026-06-28T10:00:00+00:00",
                "updated_at": "2026-06-28T11:00:00+00:00",
            }
        ]

        with TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "notes.json"
            write_notes_export(export_path, notes)

            payload = json.loads(export_path.read_text(encoding="utf-8"))

        self.assertEqual(payload, {"notes": notes})

    def test_read_notes_import_reads_export_payload(self) -> None:
        notes = [{"title": "Imported", "body": "Body", "tags": ["work"]}]

        with TemporaryDirectory() as temp_dir:
            import_path = Path(temp_dir) / "notes.json"
            import_path.write_text(json.dumps({"notes": notes}), encoding="utf-8")

            self.assertEqual(read_notes_import(import_path), notes)

    def test_read_notes_import_rejects_invalid_payload(self) -> None:
        with TemporaryDirectory() as temp_dir:
            import_path = Path(temp_dir) / "notes.json"
            import_path.write_text(json.dumps({"items": []}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "notes"):
                read_notes_import(import_path)


class FakeScheduler:
    def __init__(self) -> None:
        self.callbacks: dict[str, object] = {}
        self.cancelled: list[str] = []
        self.next_id = 0

    def after(self, _delay_ms: int, callback) -> str:
        self.next_id += 1
        handle = f"after-{self.next_id}"
        self.callbacks[handle] = callback
        return handle

    def after_cancel(self, handle: str) -> None:
        self.cancelled.append(handle)
        self.callbacks.pop(handle, None)

    def run(self, handle: str) -> None:
        callback = self.callbacks.pop(handle)
        callback()


class AutosaveControllerTest(unittest.TestCase):
    def test_existing_note_autosaves_latest_change_after_idle_delay(self) -> None:
        scheduler = FakeScheduler()
        saved: list[tuple[int, str, str, str]] = []
        statuses: list[str] = []
        controller = AutosaveController(
            after=scheduler.after,
            after_cancel=scheduler.after_cancel,
            save_note=lambda note_id, title, body, tags: saved.append((note_id, title, body, tags)),
            set_status=statuses.append,
            clock=lambda: "12:34:56",
        )

        controller.load_existing_note(7, "Old", "Body", "work")
        controller.note_changed("New", "Body", "work")
        first_handle = next(iter(scheduler.callbacks))
        controller.note_changed("New", "Body updated", "work")
        second_handle = next(iter(scheduler.callbacks))

        self.assertNotEqual(first_handle, second_handle)
        self.assertEqual(scheduler.cancelled, [first_handle])

        scheduler.run(second_handle)

        self.assertEqual(saved, [(7, "New", "Body updated", "work")])
        self.assertEqual(statuses[-1], "Сохранено автоматически: 12:34:56")

    def test_new_note_does_not_autosave(self) -> None:
        scheduler = FakeScheduler()
        saved: list[tuple[int, str, str, str]] = []
        statuses: list[str] = []
        controller = AutosaveController(
            after=scheduler.after,
            after_cancel=scheduler.after_cancel,
            save_note=lambda note_id, title, body, tags: saved.append((note_id, title, body, tags)),
            set_status=statuses.append,
        )

        controller.clear_current_note()
        controller.note_changed("Draft", "Body", "tags")

        self.assertEqual(saved, [])
        self.assertEqual(scheduler.callbacks, {})
        self.assertEqual(statuses, [])

    def test_autosave_error_is_reported_in_status(self) -> None:
        scheduler = FakeScheduler()
        statuses: list[str] = []

        def fail_save(_note_id: int, _title: str, _body: str, _tags: str) -> None:
            raise RuntimeError("database locked")

        controller = AutosaveController(
            after=scheduler.after,
            after_cancel=scheduler.after_cancel,
            save_note=fail_save,
            set_status=statuses.append,
        )

        controller.load_existing_note(3, "Old", "Body", "")
        controller.note_changed("Old", "Changed", "")
        scheduler.run(next(iter(scheduler.callbacks)))

        self.assertEqual(statuses[-1], "Ошибка автосохранения: database locked")

    def test_flush_saves_pending_existing_note_without_waiting_for_timer(self) -> None:
        scheduler = FakeScheduler()
        saved: list[tuple[int, str, str, str]] = []
        controller = AutosaveController(
            after=scheduler.after,
            after_cancel=scheduler.after_cancel,
            save_note=lambda note_id, title, body, tags: saved.append((note_id, title, body, tags)),
            set_status=lambda _message: None,
        )

        controller.load_existing_note(9, "Old", "Body", "")
        controller.note_changed("Old", "Changed before close", "")
        controller.flush()

        self.assertEqual(saved, [(9, "Old", "Changed before close", "")])


class NewDraftGuardTest(unittest.TestCase):
    def test_empty_new_note_can_be_abandoned_without_prompt_or_record(self) -> None:
        prompts: list[None] = []
        saved: list[tuple[str, str, str]] = []
        guard = NewDraftGuard(
            prompt=lambda: prompts.append(None) or "cancel",
            create_note=lambda title, body, tags: saved.append((title, body, tags)) or 1,
        )

        allowed, note_id = guard.confirm_leave_new_note(None, "  ", "", " ")

        self.assertTrue(allowed)
        self.assertIsNone(note_id)
        self.assertEqual(prompts, [])
        self.assertEqual(saved, [])

    def test_save_choice_creates_new_note_and_allows_action(self) -> None:
        saved: list[tuple[str, str, str]] = []
        guard = NewDraftGuard(
            prompt=lambda: "save",
            create_note=lambda title, body, tags: saved.append((title, body, tags)) or 42,
        )

        allowed, note_id = guard.confirm_leave_new_note(None, "Draft", "Body", "work")

        self.assertTrue(allowed)
        self.assertEqual(note_id, 42)
        self.assertEqual(saved, [("Draft", "Body", "work")])

    def test_discard_choice_allows_action_without_creating_note(self) -> None:
        saved: list[tuple[str, str, str]] = []
        guard = NewDraftGuard(
            prompt=lambda: "discard",
            create_note=lambda title, body, tags: saved.append((title, body, tags)) or 1,
        )

        allowed, note_id = guard.confirm_leave_new_note(None, "Draft", "", "")

        self.assertTrue(allowed)
        self.assertIsNone(note_id)
        self.assertEqual(saved, [])

    def test_cancel_choice_blocks_action_and_keeps_draft_unsaved(self) -> None:
        saved: list[tuple[str, str, str]] = []
        guard = NewDraftGuard(
            prompt=lambda: "cancel",
            create_note=lambda title, body, tags: saved.append((title, body, tags)) or 1,
        )

        allowed, note_id = guard.confirm_leave_new_note(None, "", "Body", "")

        self.assertFalse(allowed)
        self.assertIsNone(note_id)
        self.assertEqual(saved, [])

    def test_existing_note_does_not_use_new_draft_prompt(self) -> None:
        prompts: list[None] = []
        guard = NewDraftGuard(
            prompt=lambda: prompts.append(None) or "cancel",
            create_note=lambda _title, _body, _tags: 1,
        )

        allowed, note_id = guard.confirm_leave_new_note(7, "Changed", "Body", "work")

        self.assertTrue(allowed)
        self.assertEqual(note_id, 7)
        self.assertEqual(prompts, [])


if __name__ == "__main__":
    unittest.main()
