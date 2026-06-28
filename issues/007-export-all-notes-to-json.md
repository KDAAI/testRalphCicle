## Parent PRD

`issues/prd.md`

## What to build

Add JSON export for all notes through a standard Windows save dialog. Export should always include the full database regardless of active filters, include all fields needed for restoration, and ensure current note text is handled according to the save rules in the parent PRD.

## Acceptance criteria

- [ ] Export is available through a standard save-as dialog.
- [ ] Export writes all notes, regardless of current search or tag filters.
- [ ] Export includes title, body, tags, pin state, creation date, and modification date.
- [ ] Tags are exported as a JSON list of strings rather than internal relationship rows.
- [ ] Existing changed notes are saved before export.
- [ ] New unsaved notes trigger the save, discard, or cancel flow before export.
- [ ] Export result is shown in status or a lightweight message.
- [ ] Tests cover exported JSON content.

## Blocked by

- Blocked by `issues/002-unify-note-storage-model.md`
- Blocked by `issues/003-add-normalized-multi-tag-filtering.md`
- Blocked by `issues/005-autosave-existing-notes.md`
- Blocked by `issues/006-protect-new-unsaved-notes.md`

## User stories addressed

- User story 25
- User story 26
- User story 27
- User story 28
- User story 29
- User story 30
- User story 37
- User story 49
