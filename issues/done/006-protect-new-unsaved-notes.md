## Parent PRD

`issues/prd.md`

## What to build

Add the explicit safety flow for new unsaved notes. When a new note has content but has not yet been saved, the app should ask whether to save, discard, or cancel before switching notes, creating another note, exporting, or closing.

## Acceptance criteria

- [x] Empty new notes can be abandoned without creating database records.
- [x] New notes with content prompt before note switching.
- [x] New notes with content prompt before creating another note.
- [x] New notes with content prompt before exporting.
- [x] New notes with content prompt before closing.
- [x] Choosing save creates the note and continues the attempted action.
- [x] Choosing discard continues without creating a note.
- [x] Choosing cancel stops the attempted action and keeps the draft visible.

## Blocked by

- Blocked by `issues/005-autosave-existing-notes.md`

## User stories addressed

- User story 4
- User story 5
- User story 30
- User story 50
- User story 51
