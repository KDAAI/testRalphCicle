from __future__ import annotations

import json
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from storage import Note, NotesStore


APP_NAME = "Ralph Notes"
AUTOSAVE_DELAY_MS = 1000
NEW_DRAFT_SAVE = "save"
NEW_DRAFT_DISCARD = "discard"
NEW_DRAFT_CANCEL = "cancel"


class AutosaveController:
    def __init__(
        self,
        after: Callable[[int, Callable[[], None]], str],
        after_cancel: Callable[[str], None],
        save_note: Callable[[int, str, str, str], None],
        set_status: Callable[[str], None],
        clock: Callable[[], str] | None = None,
        delay_ms: int = AUTOSAVE_DELAY_MS,
    ) -> None:
        self.after = after
        self.after_cancel = after_cancel
        self.save_note = save_note
        self.set_status = set_status
        self.clock = clock or (lambda: datetime.now().strftime("%H:%M:%S"))
        self.delay_ms = delay_ms
        self.current_note_id: int | None = None
        self.saved_snapshot: tuple[str, str, str] | None = None
        self.pending_snapshot: tuple[str, str, str] | None = None
        self.pending_after_id: str | None = None

    def load_existing_note(self, note_id: int, title: str, body: str, tags: str) -> None:
        self.cancel_pending()
        self.current_note_id = note_id
        self.saved_snapshot = (title, body, tags)
        self.pending_snapshot = None

    def clear_current_note(self) -> None:
        self.cancel_pending()
        self.current_note_id = None
        self.saved_snapshot = None
        self.pending_snapshot = None

    def note_changed(self, title: str, body: str, tags: str) -> None:
        if self.current_note_id is None:
            return

        snapshot = (title, body, tags)
        if snapshot == self.saved_snapshot:
            self.cancel_pending()
            self.pending_snapshot = None
            return

        self.pending_snapshot = snapshot
        self.set_status("Есть несохраненные изменения")
        self._schedule()

    def flush(self) -> None:
        if self.pending_snapshot is not None:
            self._save_pending()

    def mark_saved(self, note_id: int, title: str, body: str, tags: str) -> None:
        self.cancel_pending()
        self.current_note_id = note_id
        self.saved_snapshot = (title, body, tags)
        self.pending_snapshot = None

    def cancel_pending(self) -> None:
        if self.pending_after_id is not None:
            self.after_cancel(self.pending_after_id)
            self.pending_after_id = None

    def _schedule(self) -> None:
        self.cancel_pending()
        self.pending_after_id = self.after(self.delay_ms, self._save_pending)

    def _save_pending(self) -> None:
        self.pending_after_id = None
        if self.current_note_id is None or self.pending_snapshot is None:
            return

        title, body, tags = self.pending_snapshot
        try:
            self.save_note(self.current_note_id, title, body, tags)
        except Exception as error:
            self.set_status(f"Ошибка автосохранения: {error}")
            return

        self.saved_snapshot = self.pending_snapshot
        self.pending_snapshot = None
        self.set_status(f"Сохранено автоматически: {self.clock()}")


PINNED_NOTE_PREFIX = "[Р—Р°РєСЂРµРїР»РµРЅРѕ]"


class NewDraftGuard:
    def __init__(
        self,
        prompt: Callable[[], str],
        create_note: Callable[[str, str, str], int],
    ) -> None:
        self.prompt = prompt
        self.create_note = create_note

    def confirm_leave_new_note(
        self,
        current_note_id: int | None,
        title: str,
        body: str,
        tags: str,
    ) -> tuple[bool, int | None]:
        if current_note_id is not None:
            return True, current_note_id

        if not self.has_content(title, body, tags):
            return True, None

        choice = self.prompt()
        if choice == NEW_DRAFT_SAVE:
            note_id = self.create_note(title, body, tags)
            return True, note_id
        if choice == NEW_DRAFT_DISCARD:
            return True, None
        return False, None

    @staticmethod
    def has_content(title: str, body: str, tags: str) -> bool:
        return bool(title.strip() or body.strip() or tags.strip())


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def format_note_list_label(note: Note) -> str:
    label = note.title
    if note.pinned:
        label = f"{PINNED_NOTE_PREFIX} {label}"
    if note.tags:
        label += f"  [{note.tags}]"
    return label


def delete_confirmation_for(note: Note) -> tuple[str, str]:
    title = note.title.strip() or "Р‘РµР· РЅР°Р·РІР°РЅРёСЏ"
    if note.pinned:
        return (
            "РЈРґР°Р»РёС‚СЊ Р·Р°РєСЂРµРїР»РµРЅРЅСѓСЋ Р·Р°РјРµС‚РєСѓ",
            f"Р­С‚Р° Р·Р°РјРµС‚РєР° Р·Р°РєСЂРµРїР»РµРЅР°. РЈРґР°Р»РёС‚СЊ Р·Р°РєСЂРµРїР»РµРЅРЅСѓСЋ Р·Р°РјРµС‚РєСѓ В«{title}В»?",
        )
    return ("РЈРґР°Р»РёС‚СЊ Р·Р°РјРµС‚РєСѓ", f"РЈРґР°Р»РёС‚СЊ Р·Р°РјРµС‚РєСѓ В«{title}В»?")


def write_notes_export(path: str | Path, notes: list[dict[str, object]]) -> None:
    Path(path).write_text(
        json.dumps({"notes": notes}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_notes_import(path: str | Path) -> list[dict[str, object]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("notes"), list):
        raise ValueError("Import file must contain a notes list")

    notes: list[dict[str, object]] = []
    for note in payload["notes"]:
        if not isinstance(note, dict):
            raise ValueError("Import notes must be objects")
        notes.append(note)
    return notes


def delete_shortcut_allows_delete(focused_widget_class: str | None) -> bool:
    editing_widget_classes = {
        "Entry",
        "TEntry",
        "Text",
        "Spinbox",
        "TSpinbox",
        "Combobox",
        "TCombobox",
    }
    return focused_widget_class not in editing_widget_classes


def format_filter_readouts(shown_count: int, search_text: str, selected_tags: list[str]) -> tuple[str, str]:
    filters_active = bool(search_text.strip() or selected_tags)
    count_label = "Найдено" if filters_active else "Заметок"
    count_readout = f"{count_label}: {shown_count}"

    if selected_tags:
        selected = ", ".join(sorted(selected_tags, key=str.casefold))
        return count_readout, f"Выбрано: {selected}"
    return count_readout, "Все теги"


class RalphNotesApp(tk.Tk):
    def __init__(self, store: NotesStore) -> None:
        super().__init__()
        self.store = store
        self.current_note_id: int | None = None
        self.selected_tags: set[str] = set()
        self.notes_by_list_index: dict[int, int] = {}
        self.tag_buttons: dict[str, ttk.Button] = {}
        self.pin_button: ttk.Button | None = None
        self.edit_menu: tk.Menu | None = None
        self.pin_menu_index: int | None = None
        self.delete_menu_index: int | None = None
        self.loading_note = False

        self.title(APP_NAME)
        self.geometry("1040x680")
        self.minsize(840, 540)
        self.configure(bg="#f4f1ea")

        self._configure_styles()
        self._build_menu()
        self._build_layout()
        self.autosave = AutosaveController(
            after=self.after,
            after_cancel=self.after_cancel,
            save_note=self._autosave_existing_note,
            set_status=self.status_var.set,
        )
        self.new_draft_guard = NewDraftGuard(
            prompt=self._ask_new_draft_action,
            create_note=self._save_new_draft_before_action,
        )
        self._bind_events()
        self.refresh_all()
        self.new_note()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f1ea")
        style.configure("Sidebar.TFrame", background="#e7e2d7")
        style.configure("Panel.TFrame", background="#fffdf8")
        style.configure("TLabel", background="#f4f1ea", foreground="#27231d", font=("Segoe UI", 10))
        style.configure("Heading.TLabel", font=("Segoe UI", 12, "bold"), foreground="#27231d")
        style.configure("Muted.TLabel", foreground="#766f63")
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
        style.configure("Primary.TButton", background="#2f6f73", foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", "#255b5f")])
        style.configure("Danger.TButton", background="#9f3f36", foreground="#ffffff")
        style.map("Danger.TButton", background=[("active", "#82332c")])
        style.configure("ActiveTag.TButton", background="#d6a84f", foreground="#1f1a12")
        style.configure("Tag.TButton", background="#fff8e8", foreground="#2b2a26")

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Новая заметка", accelerator="Ctrl+N", command=self.new_note)
        file_menu.add_command(label="Импорт...", accelerator="Ctrl+I", command=self.import_notes)
        file_menu.add_command(label="Экспорт...", accelerator="Ctrl+E", command=self.export_notes)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_close)
        menu_bar.add_cascade(label="Файл", menu=file_menu)

        self.edit_menu = tk.Menu(menu_bar, tearoff=False)
        self.edit_menu.add_command(label=self._pin_action_label(), command=self.toggle_pin_current_note)
        self.pin_menu_index = 0
        self.edit_menu.add_command(label="Удалить", accelerator="Delete", command=self.delete_current_note)
        self.delete_menu_index = 1
        menu_bar.add_cascade(label="РџСЂР°РІРєР°", menu=self.edit_menu)
        self.config(menu=menu_bar)

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding=14)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.rowconfigure(3, weight=1)
        sidebar.columnconfigure(0, weight=1)

        ttk.Label(sidebar, text=APP_NAME, style="Heading.TLabel", background="#e7e2d7").grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(sidebar, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        buttons = ttk.Frame(sidebar, style="Sidebar.TFrame")
        buttons.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)

        ttk.Button(buttons, text="Новая", command=self.new_note).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(buttons, text="Сброс", command=self.clear_filters).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        notes_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        notes_frame.grid(row=3, column=0, sticky="nsew")
        notes_frame.rowconfigure(1, weight=1)
        notes_frame.columnconfigure(0, weight=1)

        ttk.Label(notes_frame, text="Заметки", style="Muted.TLabel", background="#e7e2d7").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self.note_count_var = tk.StringVar(value="Заметок: 0")
        ttk.Label(notes_frame, textvariable=self.note_count_var, style="Muted.TLabel", background="#e7e2d7").grid(
            row=0, column=0, sticky="e", pady=(0, 6)
        )

        self.notes_list = tk.Listbox(
            notes_frame,
            activestyle="none",
            borderwidth=0,
            exportselection=False,
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightcolor="#cfc7b6",
            relief="flat",
            selectbackground="#2f6f73",
            selectforeground="#ffffff",
        )
        self.notes_list.grid(row=1, column=0, sticky="nsew")

        ttk.Label(sidebar, text="Теги", style="Muted.TLabel", background="#e7e2d7").grid(
            row=4, column=0, sticky="w", pady=(14, 6)
        )
        self.selected_filters_var = tk.StringVar(value="Все теги")
        ttk.Label(sidebar, textvariable=self.selected_filters_var, style="Muted.TLabel", background="#e7e2d7").grid(
            row=4, column=0, sticky="e", pady=(14, 6)
        )

        self.tags_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        self.tags_frame.grid(row=5, column=0, sticky="ew")

        editor = ttk.Frame(self, style="Panel.TFrame", padding=18)
        editor.grid(row=0, column=1, sticky="nsew")
        editor.columnconfigure(0, weight=1)
        editor.rowconfigure(3, weight=1)

        self.status_var = tk.StringVar(value="Готово")
        self.title_var = tk.StringVar()
        self.tags_var = tk.StringVar()

        ttk.Label(editor, text="Заголовок", background="#fffdf8").grid(row=0, column=0, sticky="w")
        self.title_entry = ttk.Entry(editor, textvariable=self.title_var, font=("Segoe UI", 13))
        self.title_entry.grid(row=1, column=0, sticky="ew", pady=(4, 12))

        ttk.Label(editor, text="Теги через запятую", background="#fffdf8").grid(row=2, column=0, sticky="w")
        self.tags_entry = ttk.Entry(editor, textvariable=self.tags_var)
        self.tags_entry.grid(row=3, column=0, sticky="new", pady=(4, 12))

        self.body_text = tk.Text(
            editor,
            borderwidth=1,
            font=("Segoe UI", 11),
            highlightthickness=1,
            highlightcolor="#cfc7b6",
            relief="solid",
            undo=True,
            wrap="word",
        )
        self.body_text.grid(row=4, column=0, sticky="nsew")
        editor.rowconfigure(4, weight=1)

        actions = ttk.Frame(editor, style="Panel.TFrame")
        actions.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        actions.columnconfigure(0, weight=1)

        ttk.Label(actions, textvariable=self.status_var, style="Muted.TLabel", background="#fffdf8").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(actions, text="Удалить", style="Danger.TButton", command=self.delete_current_note).grid(
            row=0, column=1, padx=(0, 8)
        )
        self.pin_button = ttk.Button(actions, text=self._pin_action_label(), command=self.toggle_pin_current_note)
        self.pin_button.grid(row=0, column=2, padx=(0, 8))
        ttk.Button(actions, text="Сохранить", style="Primary.TButton", command=self.save_current_note).grid(
            row=0, column=3
        )

    def _bind_events(self) -> None:
        self.search_var.trace_add("write", lambda *_: self.refresh_notes())
        self.title_var.trace_add("write", lambda *_: self._editor_changed())
        self.tags_var.trace_add("write", lambda *_: self._editor_changed())
        self.body_text.bind("<<Modified>>", self._body_changed)
        self.notes_list.bind("<<ListboxSelect>>", self.on_note_selected)
        self.bind_all("<Control-n>", lambda event: self._run_shortcut(event, self.new_note))
        self.bind_all("<Control-N>", lambda event: self._run_shortcut(event, self.new_note))
        self.bind_all("<Control-s>", lambda event: self._run_shortcut(event, self.save_current_note))
        self.bind_all("<Control-S>", lambda event: self._run_shortcut(event, self.save_current_note))
        self.bind_all("<Control-i>", lambda event: self._run_shortcut(event, self.import_notes))
        self.bind_all("<Control-I>", lambda event: self._run_shortcut(event, self.import_notes))
        self.bind_all("<Control-e>", lambda event: self._run_shortcut(event, self.export_notes))
        self.bind_all("<Control-E>", lambda event: self._run_shortcut(event, self.export_notes))
        self.bind_all("<Control-f>", lambda event: self._run_shortcut(event, self.focus_search))
        self.bind_all("<Control-F>", lambda event: self._run_shortcut(event, self.focus_search))
        self.bind_all("<Delete>", self._delete_from_shortcut)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _run_shortcut(self, _event: tk.Event, command: Callable[[], None]) -> str:
        command()
        return "break"

    def _delete_from_shortcut(self, _event: tk.Event) -> str | None:
        focused_widget = self.focus_get()
        focused_widget_class = focused_widget.winfo_class() if focused_widget is not None else None
        if delete_shortcut_allows_delete(focused_widget_class):
            self.delete_current_note()
            return "break"
        return None

    def focus_search(self) -> None:
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)

    def refresh_all(self) -> None:
        self.refresh_notes()
        self.refresh_tags()

    def refresh_notes(self) -> None:
        selected_id = self.current_note_id
        self.notes_list.delete(0, tk.END)
        self.notes_by_list_index.clear()

        notes = self.store.list_notes(search=self.search_var.get(), tags=sorted(self.selected_tags, key=str.casefold))
        self._update_filter_readouts(len(notes))
        for index, note in enumerate(notes):
            label = format_note_list_label(note)
            self.notes_list.insert(tk.END, label)
            self.notes_by_list_index[index] = note.id
            if note.id == selected_id:
                self.notes_list.selection_set(index)
        self._update_pin_action_state()

    def refresh_tags(self) -> None:
        for child in self.tags_frame.winfo_children():
            child.destroy()

        self.tag_buttons.clear()
        tags = self.store.list_tags()
        if not tags:
            ttk.Label(self.tags_frame, text="Пока нет тегов", style="Muted.TLabel", background="#e7e2d7").grid(
                row=0, column=0, sticky="w"
            )
            return

        for index, tag in enumerate(tags):
            style = "ActiveTag.TButton" if tag in self.selected_tags else "Tag.TButton"
            button = ttk.Button(
                self.tags_frame,
                text=tag,
                style=style,
                command=lambda value=tag: self.toggle_tag(value),
            )
            button.grid(row=index, column=0, sticky="ew", pady=(0, 6))
            self.tag_buttons[tag] = button

    def toggle_tag(self, tag: str) -> None:
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)
        else:
            self.selected_tags.add(tag)
        self.current_note_id = None
        self.refresh_all()
        self.status_var.set("Фильтры сброшены" if not self.selected_tags else f"Выбрано тегов: {len(self.selected_tags)}")

    def clear_filters(self) -> None:
        self.search_var.set("")
        self.selected_tags.clear()
        self.refresh_all()
        self.status_var.set("Фильтры сброшены")

    def new_note(self) -> None:
        if not self._prepare_to_leave_current_note():
            return

        self.current_note_id = None
        self.autosave.clear_current_note()
        self.notes_list.selection_clear(0, tk.END)
        self.loading_note = True
        self.title_var.set("")
        self.tags_var.set("")
        self.body_text.delete("1.0", tk.END)
        self.body_text.edit_modified(False)
        self.loading_note = False
        self.title_entry.focus_set()
        self.status_var.set("Новая заметка")
        self._update_pin_action_state()

    def on_note_selected(self, _event: tk.Event) -> None:
        selection = self.notes_list.curselection()
        if not selection:
            return

        note_id = self.notes_by_list_index.get(selection[0])
        if note_id is None or note_id == self.current_note_id:
            return

        note = self.store.get_note(note_id)
        if note:
            if not self._prepare_to_leave_current_note():
                if self.current_note_id is None:
                    self.notes_list.selection_clear(0, tk.END)
                else:
                    self._select_current_note()
                return
            self.load_note(note)

    def load_note(self, note: Note) -> None:
        self.current_note_id = note.id
        self.loading_note = True
        self.title_var.set(note.title)
        self.tags_var.set(note.tags)
        self.body_text.delete("1.0", tk.END)
        self.body_text.insert("1.0", note.body)
        self.body_text.edit_modified(False)
        self.loading_note = False
        self.autosave.load_existing_note(note.id, note.title, note.body, note.tags)
        self.status_var.set(f"Открыта заметка: {note.title}")
        self._update_pin_action_state(note)

    def save_current_note(self) -> None:
        title = self.title_var.get()
        body = self.body_text.get("1.0", "end-1c")
        tags = self.tags_var.get()

        if self.current_note_id is None:
            self.current_note_id = self.store.create_note(title, body, tags)
            self.status_var.set("Заметка создана")
        else:
            self.store.update_note(self.current_note_id, title, body, tags)
            self.status_var.set("Заметка сохранена")

        self.autosave.mark_saved(self.current_note_id, title, body, tags)
        self.refresh_all()
        self._select_current_note()
        self._update_pin_action_state()

    def toggle_pin_current_note(self) -> None:
        if self.current_note_id is None:
            self.status_var.set("РќРµС‡РµРіРѕ Р·Р°РєСЂРµРїР»СЏС‚СЊ")
            return

        note = self.store.get_note(self.current_note_id)
        if note is None:
            self.status_var.set("Р—Р°РјРµС‚РєР° РЅРµ РЅР°Р№РґРµРЅР°")
            self.new_note()
            return

        next_pinned = not note.pinned
        self.store.update_note(
            self.current_note_id,
            self.title_var.get(),
            self.body_text.get("1.0", "end-1c"),
            self.tags_var.get(),
            pinned=next_pinned,
        )
        self.status_var.set("Р—Р°РјРµС‚РєР° Р·Р°РєСЂРµРїР»РµРЅР°" if next_pinned else "Р—Р°РјРµС‚РєР° РѕС‚РєСЂРµРїР»РµРЅР°")
        self.refresh_all()
        self._select_current_note()
        self._update_pin_action_state()

    def _body_changed(self, _event: tk.Event) -> None:
        if self.body_text.edit_modified():
            self.body_text.edit_modified(False)
            self._editor_changed()

    def _editor_changed(self) -> None:
        if self.loading_note:
            return

        self.autosave.note_changed(
            self.title_var.get(),
            self.body_text.get("1.0", "end-1c"),
            self.tags_var.get(),
        )

    def _autosave_existing_note(self, note_id: int, title: str, body: str, tags: str) -> None:
        self.store.update_note(note_id, title, body, tags)
        self.refresh_all()
        self._select_current_note()

    def _current_editor_snapshot(self) -> tuple[str, str, str]:
        return (
            self.title_var.get(),
            self.body_text.get("1.0", "end-1c"),
            self.tags_var.get(),
        )

    def _prepare_to_leave_current_note(self) -> bool:
        if self.current_note_id is not None:
            self.autosave.flush()
            return True

        title, body, tags = self._current_editor_snapshot()
        allowed, note_id = self.new_draft_guard.confirm_leave_new_note(
            self.current_note_id,
            title,
            body,
            tags,
        )
        if note_id is not None:
            self.current_note_id = note_id
        return allowed

    def _save_new_draft_before_action(self, title: str, body: str, tags: str) -> int:
        note_id = self.store.create_note(title, body, tags)
        self.current_note_id = note_id
        self.autosave.mark_saved(note_id, title, body, tags)
        self.refresh_all()
        self._select_current_note()
        self.status_var.set("Р—Р°РјРµС‚РєР° СЃРѕР·РґР°РЅР°")
        return note_id

    def _ask_new_draft_action(self) -> str:
        result = messagebox.askyesnocancel(
            "РќРµСЃРѕС…СЂР°РЅРµРЅРЅР°СЏ Р·Р°РјРµС‚РєР°",
            "РЎРѕС…СЂР°РЅРёС‚СЊ РЅРѕРІСѓСЋ Р·Р°РјРµС‚РєСѓ РїРµСЂРµРґ РїСЂРѕРґРѕР»Р¶РµРЅРёРµРј?\n\nР”Р° - СЃРѕС…СЂР°РЅРёС‚СЊ, РќРµС‚ - РѕС‚Р±СЂРѕСЃРёС‚СЊ, РћС‚РјРµРЅР° - РѕСЃС‚Р°С‚СЊСЃСЏ.",
        )
        if result is True:
            return NEW_DRAFT_SAVE
        if result is False:
            return NEW_DRAFT_DISCARD
        return NEW_DRAFT_CANCEL

    def prepare_for_export(self) -> bool:
        return self._prepare_to_leave_current_note()

    def export_notes(self) -> None:
        if not self.prepare_for_export():
            self.status_var.set("Экспорт отменен")
            return

        export_path = filedialog.asksaveasfilename(
            title="Экспорт заметок",
            defaultextension=".json",
            filetypes=(("JSON", "*.json"), ("Все файлы", "*.*")),
            initialfile=f"ralph-notes-{datetime.now().strftime('%Y-%m-%d')}.json",
        )
        if not export_path:
            self.status_var.set("Экспорт отменен")
            return

        try:
            notes = self.store.export_notes()
            write_notes_export(export_path, notes)
        except Exception as error:
            self.status_var.set(f"Ошибка экспорта: {error}")
            return

        self.status_var.set(f"Экспортировано заметок: {len(notes)}")

    def import_notes(self) -> None:
        if not self._prepare_to_leave_current_note():
            self.status_var.set("Импорт отменен")
            return

        import_path = filedialog.askopenfilename(
            title="Импорт заметок",
            filetypes=(("JSON", "*.json"), ("Все файлы", "*.*")),
        )
        if not import_path:
            self.status_var.set("Импорт отменен")
            return

        try:
            notes = read_notes_import(import_path)
            result = self.store.import_notes(notes)
        except Exception as error:
            self.status_var.set(f"Ошибка импорта: {error}")
            return

        self.search_var.set("")
        self.selected_tags.clear()
        self.refresh_all()
        self.status_var.set(
            f"Импортировано: {result.added}; дубликатов пропущено: {result.skipped_duplicates}"
        )

    def delete_current_note(self) -> None:
        if self.current_note_id is None:
            self.new_note()
            return

        note = self.store.get_note(self.current_note_id)
        if note is None:
            self.new_note()
            return

        title, message = delete_confirmation_for(note)
        confirmed = messagebox.askyesno(title, message)
        if not confirmed:
            return

        self.store.delete_note(self.current_note_id)
        self.refresh_all()
        self.new_note()
        self.status_var.set("Заметка удалена")

    def _select_current_note(self) -> None:
        if self.current_note_id is None:
            return

        for index, note_id in self.notes_by_list_index.items():
            if note_id == self.current_note_id:
                self.notes_list.selection_clear(0, tk.END)
                self.notes_list.selection_set(index)
                self.notes_list.see(index)
                break

    def _pin_action_label(self, note: Note | None = None) -> str:
        if note is None and self.current_note_id is not None:
            note = self.store.get_note(self.current_note_id)
        if note and note.pinned:
            return "РћС‚РєСЂРµРїРёС‚СЊ"
        return "Р—Р°РєСЂРµРїРёС‚СЊ"

    def _update_pin_action_state(self, note: Note | None = None) -> None:
        label = self._pin_action_label(note)
        state = tk.NORMAL if self.current_note_id is not None else tk.DISABLED
        if self.pin_button is not None:
            self.pin_button.configure(text=label, state=state)
        if self.edit_menu is not None and self.pin_menu_index is not None:
            self.edit_menu.entryconfig(self.pin_menu_index, label=label, state=state)
        if self.edit_menu is not None and self.delete_menu_index is not None:
            self.edit_menu.entryconfig(self.delete_menu_index, state=state)

    def _update_filter_readouts(self, shown_count: int) -> None:
        count_readout, filters_readout = format_filter_readouts(
            shown_count,
            self.search_var.get(),
            list(self.selected_tags),
        )
        self.note_count_var.set(count_readout)
        self.selected_filters_var.set(filters_readout)

    def on_close(self) -> None:
        if not self._prepare_to_leave_current_note():
            return

        self.store.close()
        self.destroy()


def main() -> None:
    db_path = app_dir() / "notes.db"
    store = NotesStore(db_path)
    app = RalphNotesApp(store)
    app.mainloop()


if __name__ == "__main__":
    main()
