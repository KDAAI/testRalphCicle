## Parent PRD

`issues/prd.md`

## What to build

Add autosave for existing notes while preserving the manual Save button. Changes to title, body, or tags should save after a short idle delay, update save status, and report failures in the status area without interrupting normal editing.

## Acceptance criteria

- [x] Existing notes autosave after a one-second idle delay following title, body, or tag changes.
- [x] Autosave does not run on every keystroke.
- [x] Autosave does not automatically create brand-new notes.
- [x] The Save button remains available and can still save immediately.
- [x] Successful autosave shows a useful saved-at status.
- [x] Autosave errors appear in the status area rather than disruptive popups.
- [x] Closing the app quietly saves changed existing notes where practical.

## Blocked by

- Blocked by `issues/002-unify-note-storage-model.md`

## User stories addressed

- User story 1
- User story 2
- User story 3
- User story 5
- User story 47
- User story 48
- User story 49
- User story 51
