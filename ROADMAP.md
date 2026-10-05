# EmberVault Save Manager Roadmap

## Current state

The module is an embedded, profile-scoped, backup-gated Save Manager. Backup
and restore planning already exists. The first read-only inspection slice now
discovers synthetic save fixtures, hashes files, reports missing or unreadable
files, and rejects invalid contexts or roots. No real save locations have been
inspected.

## Next slices

1. Add inspection schemas, format detection, and approved-root contract tests.
2. Add backup plan records without performing filesystem mutation.
3. Define the Control Center execution boundary and verification manifests.
4. Add restore preview, conflict reporting, and current-state backup gates.
5. Add recovery, corruption, clean-install, packaging, and CI checks.

## Safety boundary

Control Center remains the authority for filesystem changes. Save Manager must
not modify, move, delete, or restore live save files until the shared contracts,
permissions, backup verification, rollback, and recovery evidence are complete.
