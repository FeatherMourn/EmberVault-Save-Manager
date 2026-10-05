# EmberVault Save Manager Roadmap

EmberVault is an Enshrouded save-game editor and manager. It presents worlds as
readable entries, supports safe file management, and progressively adds
structured save editing. Mutating operations must be previewable,
backup-protected, validated, and reversible.

## Product flow

```text
Inspect -> Back up -> Preview -> Apply -> Validate -> Roll back if needed
```

## Planning and development foundation

- [x] Define the minimum viable product and explicitly defer nonessential features
- [x] Document supported Windows, Steam Cloud, and dedicated-server scenarios
- [ ] Establish save-format compatibility and version-detection rules
- [x] Define behavior for unsupported, damaged, partial, and legacy saves
- [x] Design confirmations, previews, undo, rollback, and recovery messaging
- [x] Separate file operations, save parsing, validation, and UI components
- [x] Create fixtures for healthy, partial, corrupt, and legacy saves
- [x] Test interrupted operations and rollback behavior
- [x] Define privacy-safe logging and prevent unnecessary save-content exposure
- [x] Document installation, backups, limitations, and recovery procedures
- [x] Add clean-install, packaging, update, and release checks
- [ ] Define a controlled, opt-in phase for validation against real saves
- [x] Write a product and technical specification covering supported operations,
  safety guarantees, and the first editable save fields

## Core user experience

These features should be easy to find and useful to ordinary players:

- See all worlds with readable names, slots, and locations
- Create a one-click backup
- Restore or roll back a world
- Duplicate a world before experimenting
- Rename and organize worlds
- Move worlds between local storage, Steam Cloud, and a server
- Import and export a world package
- Make a small set of understandable, validated edits
- Warn when Enshrouded is running or a save is incomplete

The primary screen should be a simple world library. Selecting a world should
make its common actions immediately available: back up, duplicate, rename,
restore, import, export, and view save history.

## Milestone 1 — World library and save discovery

- [x] Deterministic file discovery and ordering
- [x] SHA-256 hashes, sizes, timestamps, and basic format detection
- [x] Missing and unreadable file states
- [x] Profile-scoped inspection result through the Module SDK
- [x] Temporary-directory inspection tests
- [x] Reviewable backup-plan model with approved-root enforcement
- [x] Discover local, Steam Cloud, and dedicated-server save locations
- [x] Group world files, metadata, index files, and rolling copies
- [x] Display readable world names, slots, locations, timestamps, and health
- [x] Identify the active rolling save without manual index editing

## Milestone 1A — World-library interface

- [x] Show worlds as readable cards or rows rather than raw filenames
- [x] Show world name, slot, location, last modified time, and health
- [ ] Provide direct actions for backup, duplicate, rename, restore, import, and export
- [ ] Show confirmation and preview before any destructive or replacing action
- [ ] Surface the most recent backup and available rollback point
- [ ] Keep advanced actions secondary so the main screen stays approachable

## Milestone 2 — Core world management

- [x] Duplicate a world into an available slot
- [x] Rename a world through supported metadata
- [x] Move a world between supported locations
- [x] Import and export a world package
- [ ] Archive or remove a world with explicit confirmation
- [x] Preview every affected file before applying an operation
- [ ] Refresh and rescan save locations

## Milestone 3 — One-click backup, restore, and validation

- [x] Create timestamped backups before every mutation
- [x] Record source and destination manifests and hashes
- [x] Validate expected files and destination identity
- [ ] Expose rolling-save history as a readable rollback view
- [x] Verify the result after each operation
- [x] Provide one-click rollback when validation fails
- [ ] Preserve recovery evidence for Control Center and Troubleshooter

## Milestone 4 — World metadata editing

- [x] Edit world display name
- [ ] Edit slot assignment through a managed operation
- [ ] Add user-facing save and backup labels
- [ ] Add source, destination, and import/export notes
- [ ] Validate metadata before writing it

## Milestone 5 — Character management

- [x] Discover character data and metadata
- [x] Back up and export individual characters
- [x] Import characters with conflict warnings
- [ ] Validate character compatibility with the destination world

## Milestone 6 — Deeper save editing

Add structured editors only after the relevant formats are understood and
covered by fixtures and round-trip tests:

- [ ] World progression
- [ ] Quest and knowledge state
- [ ] Map and exploration state
- [ ] Building and inventory-related data
- [ ] Additional validated editor panels

## Milestone 7 — Format research and fixture validation

- [ ] Copy an active character rolling-copy fixture into the private fixture area
- [ ] Inventory character `KSC1` sections without mutation
- [ ] Compare character rolling copies to identify stable and changing regions
- [ ] Determine section boundaries and length/checksum rules
- [ ] Map exact `KSC1` section boundaries and checksum behavior
- [ ] Compare controlled fixture changes against known in-game actions
- [ ] Add round-trip tests for every candidate editable field
- [ ] Document supported save versions and known format limitations

## Milestone 8 — Safe editor expansion

- [ ] Add validated index and rollback editing
- [ ] Add only format-proven character fields
- [ ] Add only format-proven world fields
- [ ] Keep unknown or cross-linked sections read-only
- [ ] Require backup, preview, validation, and rollback for every edit
- [ ] Enable character editing only after safe fields are proven

## Milestone 9 — Interactive operation UX

- [ ] Add destination selection for copy, move, import, and export
- [ ] Add operation preview dialogs
- [ ] Add explicit confirmation for replacement and archive/remove
- [ ] Show backup, validation, and rollback results
- [ ] Wire desktop actions to the operation services
- [ ] Surface operation history and recovery references
- [ ] Add destination pickers for supported source types
- [ ] Connect preview dialogs to actual operation execution

## Milestone 10 — Release readiness

- [ ] Test against private real-save fixtures
- [ ] Add clean-install and packaging verification
- [ ] Add version and compatibility checks
- [ ] Document supported sources, save versions, limitations, and recovery
- [ ] Complete an opt-in validation pass with live saves
- [ ] Add rolling-copy history and controlled index editing
- [ ] Add permissions and compatibility checks to release validation
- [ ] Add structured diagnostics and support output

## Milestone 11 — Release polish and maintenance

- [ ] Discover Steam installations and libraries without assuming the C: drive
- [ ] Detect Steam Cloud conflicts, stale copies, and source divergence
- [ ] Add backup retention and safe cleanup rules
- [ ] Add structured user-facing errors and support-bundle generation
- [ ] Verify permissions and clearly report read-only sources
- [ ] Add accessibility and localization foundations
- [ ] Review licenses and third-party dependency obligations
- [ ] Add update, migration, and future save-format compatibility handling

## Secondary features

Consider these only after the core experience is reliable and simple:

- Save comparison and detailed change reports
- Search, filters, tags, and custom organization
- Extended revision history and operation logs
- Scheduled backups and retention policies
- Advanced diagnostic and support packages
- Plugin or format-adapter support

## Design rules

- Save Manager is an editor and manager, not just a backup utility.
- No operation silently overwrites or deletes user data.
- Every mutation has a preview, pre-operation backup, and post-operation validation.
- Opaque save data is not edited until its format and invariants are understood.
- All behavior is tested against synthetic fixtures before live saves are supported.
