## Parent PRD

`issues/prd.md`

## What to build

Add lightweight status information so users can understand the current result set, selected filters, save state, and import/export results without making the interface heavy. This should preserve the current sidebar and editor layout while adding the compact readouts requested in the parent PRD.

## Acceptance criteria

- [ ] The UI shows `Заметок: N` when no filters are active.
- [ ] The UI shows `Найдено: N` when search or tag filters are active.
- [ ] The UI shows selected filters as a compact text line.
- [ ] The UI shows `Все теги` when no tag filters are selected.
- [ ] Save, autosave, import, export, and recoverable error messages use the status area consistently.
- [ ] Import results and export results are visible without adding extra sidebar buttons.

## Blocked by

- Blocked by `issues/003-add-normalized-multi-tag-filtering.md`
- Blocked by `issues/005-autosave-existing-notes.md`
- Blocked by `issues/008-import-notes-from-json.md`

## User stories addressed

- User story 19
- User story 20
- User story 21
- User story 36
- User story 37
- User story 47
- User story 48
- User story 49
