# EmberVault Save Manager — Product and Technical Specification

## Product definition

EmberVault is a desktop Enshrouded save-game editor and manager. It helps
players understand, protect, organize, transfer, and make controlled changes
to world saves without requiring them to manage opaque filenames manually.

## MVP

The first usable release will:

1. Discover supported local, Steam Cloud, and dedicated-server save folders.
2. Display worlds by readable name, slot, location, timestamp, and health.
3. Create and restore timestamped backups.
4. Duplicate, rename, move, import, and export worlds.
5. Preview affected files before replacement or deletion.
6. Detect when Enshrouded is running and block unsafe operations by default.
7. Validate file groups, hashes, expected metadata, and operation results.
8. Provide rollback after a failed or unwanted operation.

The MVP will not attempt unrestricted binary editing or opaque world-state
changes.

## Supported save sources

- Local player saves under the user's Enshrouded save directory.
- Steam Cloud's local synchronized save directory.
- Dedicated-server save directories selected by the user.

Each source is modeled as a location with a type, path, access status, and
discovered world groups. The application must not assume that a path exists or
that a source is writable.

## World model

A world consists of a logical slot identity, readable metadata, one or more
world data files, associated metadata files, an index or rolling-save pointer
when present, and any recognized rolling copies. Unknown companion files are
preserved and surfaced as unclassified rather than discarded.

## Core operations

Every mutating operation follows:

```text
Inspect -> Back up -> Preview -> Confirm -> Apply -> Validate -> Record
```

Operations are duplicate, rename, move, import, export, backup, restore, and
rollback. Each operation records its source, destination, expected files,
pre-operation hashes, result hashes, timestamp, and validation result.

## Safety guarantees

- No silent overwrite or deletion.
- A current-state backup precedes replacement, move, restore, or edit.
- Destinations must be inside an explicitly approved save or backup location.
- Path traversal and ambiguous file groups are rejected.
- The game-running check blocks mutations by default.
- Failed validation leaves the prior backup available for rollback.
- Unknown files are preserved unless the user explicitly chooses otherwise.
- Inspection and preview never mutate files.

## First editable fields

The first structured editor should target low-risk metadata only:

- World display name
- Managed world label
- Slot assignment through a controlled operation

Each field requires format validation and a round-trip fixture before being
enabled for real saves. Progression, quests, knowledge, map state, buildings,
inventory, and character data remain later milestones.

## Architecture boundaries

- Discovery identifies sources and world groups.
- Inspection reads files and produces deterministic evidence.
- Planning creates reviewable operation plans.
- Execution performs approved filesystem changes through the application boundary.
- Validation compares results with the plan and source invariants.
- The UI presents worlds, plans, warnings, and recovery actions.

These components should remain independently testable. Save parsing must not
perform file operations, and UI code must not bypass operation planning.

## Testing policy

Use synthetic fixtures for healthy, partial, corrupt, legacy, and unknown-file
cases. Test interruption, hash changes, rejected paths, running-game blocks,
duplicate conflicts, rollback, and clean installation before opt-in testing
against live saves.
