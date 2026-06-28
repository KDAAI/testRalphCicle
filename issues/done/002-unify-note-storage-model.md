## Parent PRD

`issues/prd.md`

## What to build

Update the storage-facing note model and core CRUD behavior so all note reads and writes use the upgraded data model from the parent PRD. A note should be returned with user-visible tags, creation and modification dates, and pin state, and note lists should sort pinned notes above regular notes and then by recent modification activity.

## Acceptance criteria

- [x] `create_note`, `update_note`, `get_note`, `delete_note`, and `list_notes` work with the upgraded note model.
- [x] Creating a note stores normalized tags through the tag relationship tables.
- [x] Updating title, body, tags, or pin state updates the modification timestamp.
- [x] Listing notes sorts pinned notes first, then by newest modification date, with stable fallback ordering.
- [x] Returned note data includes title, body, tags, pin state, created date, and modified date.
- [x] Storage tests cover sorting, timestamps, and user-visible tag round-tripping.

## Blocked by

- Blocked by `issues/001-migrate-note-schema-and-metadata.md`

## User stories addressed

- User story 6
- User story 7
- User story 8
- User story 9
- User story 10
- User story 11
- User story 22
- User story 53
