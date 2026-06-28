## Parent PRD

`issues/prd.md`

## What to build

Add the standard top menu and keyboard shortcuts described in the parent PRD. File actions should contain new note, import, export, and exit. Edit actions should contain pin or unpin and delete note. Shortcuts should route to the same user-safe flows as the visible controls.

## Acceptance criteria

- [ ] File menu includes New Note, Import, Export, and Exit.
- [ ] Edit menu includes Pin or Unpin and Delete Note.
- [ ] Ctrl+N creates a new note through the protected new-note flow.
- [ ] Ctrl+S saves the current note.
- [ ] Ctrl+I starts import.
- [ ] Ctrl+E starts export.
- [ ] Ctrl+F focuses search.
- [ ] Delete deletes the selected note only when focus is not in title, tags, body, or another editing field.

## Blocked by

- Blocked by `issues/004-add-pin-unpin-flow.md`
- Blocked by `issues/007-export-all-notes-to-json.md`
- Blocked by `issues/008-import-notes-from-json.md`

## User stories addressed

- User story 13
- User story 39
- User story 40
- User story 41
- User story 42
- User story 43
- User story 44
- User story 45
- User story 46
