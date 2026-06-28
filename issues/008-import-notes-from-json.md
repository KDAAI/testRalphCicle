## Parent PRD

`issues/prd.md`

## What to build

Add JSON import for restoring or merging notes through a standard Windows open-file dialog. Import should add notes without overwriting existing data, skip exact title-and-body duplicates, preserve same-title notes with different bodies, accept flexible tag formats, reset filters, and report results clearly.

## Acceptance criteria

- [ ] Import is available through a standard open-file dialog.
- [ ] Import adds notes and does not overwrite existing notes.
- [ ] Import skips duplicates only when title and body both match an existing note.
- [ ] Import keeps notes that share a title but have different body content.
- [ ] Import accepts tags as either a list of strings or a comma-separated string.
- [ ] Invalid import files show a clear error.
- [ ] After import, search and selected tag filters reset.
- [ ] Import reports how many notes were added and how many duplicates were skipped.
- [ ] Tests cover duplicate handling, same-title different-body handling, and both tag input formats.

## Blocked by

- Blocked by `issues/002-unify-note-storage-model.md`
- Blocked by `issues/003-add-normalized-multi-tag-filtering.md`

## User stories addressed

- User story 31
- User story 32
- User story 33
- User story 34
- User story 35
- User story 36
- User story 37
- User story 38
- User story 53
