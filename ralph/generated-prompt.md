Previous commits:
e2105c43924f9559946299bf8da70be02bce6f99
2026-06-29
Fix Russian UI text and docs

Key decisions: keep corrected Russian strings in the existing public formatters and UI flows so tests cover the pinned-note label and stronger delete confirmation; update README around the shipped local-first behavior instead of adding new app surface.

Files changed: app.py, test_app.py, README.md, issues/done/011-fix-russian-ui-text-and-documentation.md (moved from issues/).

Blockers or notes for next iteration: Python unittest discover, py_compile, and git diff --check pass; npm run test and npm run typecheck cannot run because this Python project has no package.json. Remaining open task is final verification and executable build.
---
ca9ac53737d2616d4d12029cddc434d73ac19241
2026-06-29
Add status count readouts

Key decisions: keep result-count and selected-filter copy behind a small public formatter so the sidebar UI and tests share one behavior; preserve the existing compact sidebar/editor layout and status-area import/export messages.

Files changed: app.py, test_app.py, issues/done/010-add-status-counts-and-filter-readouts.md.

Blockers or notes for next iteration: Python unittest discover, py_compile, and git diff --check pass; npm run test and npm run typecheck cannot run because this Python project has no package.json. Remaining open task can fix the broader Russian UI mojibake and documentation.
---
be30741f1a67c66b9ced8212dbd4942092c65c41
2026-06-29
Add top menu shortcuts

Key decisions: route menu items and keyboard shortcuts through the existing safe note flows; guard Delete so it skips editing widgets; keep shortcut behavior covered by a focused public helper test.

Files changed: app.py, test_app.py, issues/done/009-add-top-menu-and-keyboard-shortcuts.md.

Blockers or notes: Python tests and py_compile pass; npm run test/typecheck are not available because this Python project has no package.json.
---
7d7a1267f167ce7e6281b4c1203775f414853745
2026-06-29
Add JSON import for notes

Key decisions: keep import parsing small and testable through read_notes_import; route imported note creation through NotesStore.import_notes so duplicate detection and tag normalization stay below the UI; reset search and selected tag filters after a successful import and report added/skipped counts in the status area.

Files changed: app.py, storage.py, test_app.py, test_storage.py, issues/done/008-import-notes-from-json.md (moved from issues/).

Blockers/notes for next iteration: npm run test and npm run typecheck still cannot run because this Python project has no package.json; Python unittest discover, py_compile, and git diff --check passed. Next task can build the top menu and keyboard shortcuts on top of import/export.
---
16f2be23aaf87ee2662bf9360dec3832c437097f
2026-06-28
Add JSON export for all notes

Key decisions: keep export data behind NotesStore.export_notes for testability; write a readable UTF-8 JSON payload with a top-level notes array; route the File > Export flow through the existing protected leave/export preparation so existing notes flush and new drafts can be saved, discarded, or cancelled.

Files changed: app.py, storage.py, test_app.py, test_storage.py, issues/done/007-export-all-notes-to-json.md (moved from issues/).

Blockers/notes for next iteration: npm run test and npm run typecheck still cannot run because this Python project has no package.json; Python unittest discover and py_compile passed. Next task can build JSON import on top of the export format.
---

Issues:
## Parent PRD

`issues/prd.md`

## What to build

Run the final verification path from the parent PRD after the functional slices are complete. The primary deliverable is tested source behavior; rebuilding the Windows executable is a best-effort step using the existing project build flow if the local environment supports it.

## Acceptance criteria

- [ ] The Python test suite runs successfully.
- [ ] Storage tests cover migration, timestamps, pinning, filtering, and import/export.
- [ ] Key UI flows are manually checked where Tkinter automation is impractical.
- [ ] The existing executable build flow is attempted.
- [ ] If the executable build succeeds, the updated executable is available in the documented output location.
- [ ] If the executable build fails, the failure is documented clearly without blocking the source deliverable.

## Blocked by

- Blocked by `issues/001-migrate-note-schema-and-metadata.md`
- Blocked by `issues/002-unify-note-storage-model.md`
- Blocked by `issues/003-add-normalized-multi-tag-filtering.md`
- Blocked by `issues/004-add-pin-unpin-flow.md`
- Blocked by `issues/005-autosave-existing-notes.md`
- Blocked by `issues/006-protect-new-unsaved-notes.md`
- Blocked by `issues/007-export-all-notes-to-json.md`
- Blocked by `issues/008-import-notes-from-json.md`
- Blocked by `issues/009-add-top-menu-and-keyboard-shortcuts.md`
- Blocked by `issues/010-add-status-counts-and-filter-readouts.md`
- Blocked by `issues/011-fix-russian-ui-text-and-documentation.md`

## User stories addressed

- User story 53
- User story 55
## Problem Statement

Ralph Notes is a local Windows notes application that currently supports basic note creation, editing, deletion, search, and a single active tag filter. The user wants to evolve it into a more reliable personal note manager without making the interface heavy or complicated.

The current app lacks several behaviors expected from a practical notes tool: notes are easy to leave unsaved, there is no visible creation or modification history, important notes cannot be pinned, tag filtering is limited to one tag, tags are stored as a comma-separated field rather than a normalized structure, and there is no built-in backup/import flow. The existing Russian UI text also appears with broken encoding in the source, which makes future UI work unpleasant and user-facing text unreliable.

The goal is to add the requested functionality in a way that preserves the app's local-first nature, keeps the UI simple, protects user data, and leaves the codebase easier to test and extend.

## Solution

Add a focused set of note-management improvements:

- Autosave existing notes after edits.
- Protect new unsaved notes from accidental loss.
- Track and display note creation and modification dates.
- Support pinned notes and sort them above regular notes.
- Allow filtering by multiple selected tags using AND semantics.
- Move tags into dedicated database tables while preserving compatibility with existing data.
- Add JSON import and export for all notes.
- Add a standard top menu with file/edit actions.
- Add keyboard shortcuts for common actions.
- Show useful lightweight status information such as save state, note counts, selected filters, and import/export results.
- Update tests, documentation, and attempt to rebuild the Windows executable.

The experience should remain familiar: the left side stays focused on search, note list, and tag filters; the right side stays focused on editing the selected note. Import/export should live in the top menu rather than as extra buttons in the left panel. Pinning should be available both from the menu and from the note editor.

## User Stories

1. As a note-taking user, I want existing notes to save automatically after I stop typing, so that I do not lose edits if I forget to press Save.
2. As a note-taking user, I want autosave to wait briefly after my last change, so that the app does not save on every keystroke.
3. As a note-taking user, I want autosave to apply to title changes, body changes, and tag changes, so that every part of the note is protected.
4. As a note-taking user, I want new notes not to be created automatically while empty or half-started, so that the database does not fill with accidental blank notes.
5. As a note-taking user, I want the Save button to remain available, so that I can explicitly create a new note or save immediately.
6. As a note-taking user, I want to see when a note was created, so that I can understand its history.
7. As a note-taking user, I want to see when a note was last changed, so that I can tell which notes are current.
8. As a note-taking user, I want the modified date to update when I edit title, body, tags, or pin state, so that it reflects meaningful note changes.
9. As a note-taking user, I want notes sorted by recent activity, so that the newest work is easiest to find.
10. As a note-taking user, I want pinned notes to appear above regular notes, so that important notes stay visible.
11. As a note-taking user, I want pinned notes to be clearly marked in the list, so that I can distinguish them at a glance.
12. As a note-taking user, I want to pin and unpin a note from the editor, so that I can manage importance while reading or editing it.
13. As a note-taking user, I want to pin and unpin a note from the top menu, so that the action is discoverable in a standard place.
14. As a note-taking user, I want deleting a pinned note to show a stricter confirmation message, so that I notice I am deleting something important.
15. As a note-taking user, I want to select multiple tags, so that I can narrow the list to notes matching several topics.
16. As a note-taking user, I want multiple selected tags to filter using AND logic, so that selecting "work" and "urgent" only shows notes containing both tags.
17. As a note-taking user, I want tag buttons to toggle on and off, so that I can adjust filters without typing complex expressions.
18. As a note-taking user, I want the Reset action to clear search and all selected tags, so that I can quickly return to the full list.
19. As a note-taking user, I want to see how many notes are currently shown, so that I understand the size of the current result set.
20. As a note-taking user, I want the count label to distinguish all notes from filtered results, so that I can tell whether filters are active.
21. As a note-taking user, I want to see which tag filters are selected, so that I understand why the list is narrowed.
22. As a note-taking user, I want tags stored as proper related records, so that filtering and future tag features are reliable.
23. As a current user with existing notes, I want old comma-separated tags migrated automatically, so that I do not lose my data.
24. As a current user with an existing database, I want migration to be safe and automatic at app startup, so that I do not need manual database work.
25. As a note-taking user, I want to export all notes to JSON, so that I can create a backup.
26. As a note-taking user, I want export to include title, body, tags, pin state, creation date, and modification date, so that a backup is complete.
27. As a note-taking user, I want export to always include all notes regardless of current filters, so that I do not accidentally create a partial backup.
28. As a note-taking user, I want export to save through a standard Windows "save as" dialog, so that I can choose where the backup goes.
29. As a note-taking user, I want the current existing note saved before export, so that the backup includes the latest text.
30. As a note-taking user, I want the app to ask what to do with a new unsaved note before export, so that I understand whether it will be included.
31. As a note-taking user, I want to import notes from JSON, so that I can restore or merge notes.
32. As a note-taking user, I want import to add notes rather than overwrite my database, so that existing data remains safe.
33. As a note-taking user, I want import to skip duplicates with the same title and body, so that repeated imports do not create obvious duplicates.
34. As a note-taking user, I want import to keep a note with the same title but different body, so that legitimate separate notes are preserved.
35. As a note-taking user, I want import to accept tags as either a list or a comma-separated string, so that older or hand-edited JSON files still work.
36. As a note-taking user, I want filters reset after import, so that I can immediately see the imported results.
37. As a note-taking user, I want import results to report how many notes were added and how many duplicates were skipped, so that I know what happened.
38. As a note-taking user, I want invalid import files to show a clear error, so that I understand why import failed.
39. As a Windows app user, I want a top File menu, so that import, export, new note, and exit are in a familiar place.
40. As a Windows app user, I want a top Edit menu, so that note actions such as pinning and deleting are in a familiar place.
41. As a keyboard-oriented user, I want Ctrl+N to create a new note, so that I can work faster.
42. As a keyboard-oriented user, I want Ctrl+S to save, so that I can explicitly save without using the mouse.
43. As a keyboard-oriented user, I want Ctrl+I to import, so that I can access import quickly.
44. As a keyboard-oriented user, I want Ctrl+E to export, so that I can access backup quickly.
45. As a keyboard-oriented user, I want Ctrl+F to focus search, so that I can find notes quickly.
46. As a keyboard-oriented user, I want Delete to delete the selected note only when focus is not in an editing field, so that normal text editing remains safe.
47. As a note-taking user, I want unsaved changes to show a status message, so that I know whether the current note still needs saving.
48. As a note-taking user, I want autosave success to show the save time, so that I have confidence the note was saved.
49. As a note-taking user, I want autosave errors shown in the status area rather than as disruptive popups, so that I can keep working when possible.
50. As a note-taking user, I want the app to ask before discarding a new unsaved note when switching notes, creating another note, exporting, or closing, so that I do not lose new content by accident.
51. As a note-taking user, I want closing the app to quietly save existing changed notes, so that exit is smooth and safe.
52. As a maintainer, I want the Russian UI text corrected, so that user-facing labels are readable and future UI changes are clear.
53. As a maintainer, I want tests for storage migration, filtering, pinning, and import/export, so that core data behavior is protected.
54. As a maintainer, I want documentation updated, so that users and future developers understand the new behavior.
55. As a Windows user, I want a rebuilt executable if the environment supports it, so that I can run the updated app without starting Python manually.

## Implementation Decisions

- Keep the application local-first and backed by SQLite.
- Preserve the existing general layout: sidebar for search, notes, and tags; editor panel for the selected note.
- Correct broken Russian UI strings while touching the relevant UI and documentation.
- Add creation and modification timestamps to notes.
- Add a pinned flag to notes.
- Sort notes with pinned notes first, then by most recently modified, with stable fallback ordering.
- Display creation and modification dates in the editor, not in every list row.
- Mark pinned notes in the list with a text prefix: `[Закреплено]`.
- Treat pinning and unpinning as note modifications that update the modification timestamp.
- Keep the manual Save button even after autosave is added.
- Autosave only existing notes.
- Autosave after a one-second idle delay following changes to title, body, or tags.
- Do not automatically create a new note via autosave.
- For new unsaved notes with content, ask whether to save, discard, or cancel before leaving the note, creating another note, exporting, or closing.
- For existing notes with unsaved changes, save automatically before closing or exporting.
- Store tags in separate database tables with a note-tag relationship table.
- Automatically migrate existing comma-separated note tags into the new tag tables.
- Keep any legacy tag column physically present if it already exists, but stop using it as the source of truth.
- Normalize tags by trimming whitespace, splitting comma/semicolon-separated input, and deduplicating case-insensitively.
- Multi-tag filtering uses AND semantics.
- Tag controls behave as toggles: click to select, click again to deselect.
- Reset clears both search text and all selected tag filters.
- Show a note count label: `Заметок: N` when unfiltered and `Найдено: N` when filters are active.
- Show selected filters as a compact text line such as `Выбрано: работа, срочно`; show `Все теги` when none are selected.
- Add a top File menu with New Note, Import, Export, and Exit.
- Add a top Edit menu with Pin/Unpin and Delete Note.
- Duplicate pin/unpin in the editor action area.
- Place import and export in the top menu rather than adding more buttons to the sidebar.
- Export all notes, regardless of active search or tag filters.
- Export JSON through a standard save dialog with a date-based default filename.
- Export tags as a JSON list of strings rather than exposing the internal relational schema.
- Import JSON through a standard open-file dialog.
- Import adds notes; it does not overwrite existing notes.
- Import skips duplicates only when both title and body match an existing note.
- Import keeps notes that share a title but have different body content.
- Import accepts tags as either a list of strings or a comma-separated string.
- After import, reset filters and refresh the note list.
- Show import/export results in status or a lightweight message.
- Add keyboard shortcuts: Ctrl+N, Ctrl+S, Ctrl+I, Ctrl+E, Ctrl+F, and context-safe Delete.
- Attempt to rebuild the Windows executable after implementation if the environment supports it.

Major modules to build or modify:

- Storage module: schema migration, note metadata, normalized tag tables, multi-tag filtering, pinning, import/export data operations, duplicate detection.
- Application UI module: menus, shortcuts, autosave orchestration, unsaved-new-note prompts, status messages, date display, pin controls, filter state, file dialogs.
- Test module: storage behavior tests for migration, timestamps, pinning, filtering, and import/export.
- Documentation/build support: update README and run the existing build flow where possible.

Deep module opportunity:

- Keep import/export, tag normalization, duplicate detection, and schema migration logic behind storage-level methods so that these behaviors can be tested without driving the Tkinter UI.

## Testing Decisions

- Tests should focus on externally observable behavior rather than implementation details.
- Storage tests should verify that creating and updating notes stores normalized tags through the new tag structure and returns the same user-visible tag values.
- Storage tests should verify that old databases with comma-separated tags migrate into the new tag tables.
- Storage tests should verify that pinned notes sort above unpinned notes.
- Storage tests should verify that modification timestamps change when note content or pin state changes.
- Storage tests should verify multi-tag AND filtering.
- Storage tests should verify list_tags returns normalized, deduplicated, case-insensitive tags.
- Import/export tests should verify the exported JSON contains all note fields needed for restoration.
- Import/export tests should verify duplicate handling by title and body.
- Import/export tests should verify same-title different-body notes are kept.
- Import/export tests should verify both list-style tags and comma-separated string tags are accepted during import.
- UI behavior that is difficult to automate in Tkinter can be tested manually, but the underlying decision logic should live in testable methods where practical.
- Existing storage tests provide prior art for using temporary SQLite databases and asserting store-level behavior.
- The final verification should include running the Python test suite.
- If available, the final verification should include attempting the existing executable build flow.

## Out of Scope

- Cloud sync or multi-device synchronization.
- User accounts or authentication.
- Rich-text editing, Markdown rendering, or attachments.
- Full tag-management screens such as renaming, merging, or deleting tags globally.
- Exporting only the currently filtered subset of notes.
- Conflict resolution beyond skipping exact duplicate title/body imports.
- Removing legacy database columns through a destructive SQLite table rebuild.
- Replacing Tkinter with another UI framework.
- Adding new external dependencies unless strictly necessary.
- Publishing a GitHub issue or using any external issue tracker.

## Further Notes

- The PRD intentionally favors data safety over silent behavior. Existing notes can autosave quietly, but new notes need explicit handling before they become database records.
- The JSON format should be stable and user-readable. It should not mirror internal database table structure.
- The existing source appears to contain mojibake in Russian strings. Correcting user-facing Russian text is part of making the new functionality shippable, even though it was not the original feature request.
- The executable rebuild is a best-effort final step. Source changes and tests are the primary deliverable if the local build environment cannot produce a new executable.

# ISSUES

Local issue files from `issues/` are provided at start of context. Parse them to understand the open issues.

You will work on the AFK issues only, not the HITL ones.

You've also been passed a file containing the last few commits. Review these to understand what work has been done.

If all AFK tasks are complete, output <promise>NO MORE TASKS</promise>.

# TASK SELECTION

Pick the next task. Prioritize tasks in this order:

1. Critical bugfixes
2. Development infrastructure

Getting development infrastructure like tests and types and dev scripts ready is an important precursor to building features.

3. Tracer bullets for new features

Tracer bullets are small slices of functionality that go through all layers of the system, allowing you to test and validate your approach early. This helps in identifying potential issues and ensures that the overall architecture is sound before investing significant time in development.

TL;DR - build a tiny, end-to-end slice of the feature first, then expand it out.

4. Polish and quick wins
5. Refactors

# EXPLORATION

Explore the repo.

# IMPLEMENTATION

Use /tdd to complete the task.

# FEEDBACK LOOPS

Before committing, run the feedback loops:

- `npm run test` to run the tests
- `npm run typecheck` to run the type checker

# COMMIT

Make a git commit. The commit message must:

1. Include key decisions made
2. Include files changed
3. Blockers or notes for next iteration

# THE ISSUE

If the task is complete, move the issue file to `issues/done/`.

If the task is not complete, add a note to the issue file with what was done.

# FINAL RULES

ONLY WORK ON A SINGLE TASK.
