## Parent PRD

`issues/prd.md`

## What to build

Add normalized tag behavior and multi-tag filtering across storage and the existing sidebar flow. Tags should be trimmed, split on commas or semicolons, deduplicated case-insensitively, listed from normalized records, and applied as selectable filters using AND semantics.

## Acceptance criteria

- [ ] `list_tags` returns normalized, deduplicated tags sorted case-insensitively.
- [ ] `list_notes` accepts multiple selected tags and returns only notes that contain every selected tag.
- [ ] Search still works together with selected tags.
- [ ] Reset clears both search text and all selected tag filters.
- [ ] The UI allows tag controls to toggle on and off independently.
- [ ] The UI can display selected filters and distinguish all-note counts from filtered result counts.
- [ ] Tests cover multi-tag AND filtering and normalized tag listing.

## Blocked by

- Blocked by `issues/001-migrate-note-schema-and-metadata.md`
- Blocked by `issues/002-unify-note-storage-model.md`

## User stories addressed

- User story 15
- User story 16
- User story 17
- User story 18
- User story 19
- User story 20
- User story 21
- User story 22
- User story 53
