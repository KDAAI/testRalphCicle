## Parent PRD

`issues/prd.md`

## What to build

Add the safe storage foundation for the note-management upgrade described in the parent PRD. Existing SQLite databases should be migrated automatically at app startup to support creation dates, modification dates, pinned notes, normalized tag records, and note-tag relationships while preserving existing note data and leaving any legacy tag column physically present.

## Acceptance criteria

- [x] Existing databases with the current `notes` table open without manual database work.
- [x] Notes gain `created_at`, `updated_at`, and `pinned` storage fields with sensible defaults.
- [x] Dedicated tag and note-tag relationship tables are created automatically.
- [x] Existing comma- or semicolon-separated note tags are migrated into the normalized tag structure.
- [x] Migration is idempotent and safe to run repeatedly.
- [x] Storage tests cover migration from an old database shape.

## Blocked by

None - can start immediately

## User stories addressed

- User story 6
- User story 7
- User story 8
- User story 9
- User story 22
- User story 23
- User story 24
- User story 53
