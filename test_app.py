import unittest

from app import AutosaveController, delete_confirmation_for, format_note_list_label
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


if __name__ == "__main__":
    unittest.main()
