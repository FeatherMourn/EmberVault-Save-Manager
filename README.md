# EmberVault Save Manager

EmberVault Save Manager is an independently packaged, embedded Enshrouded
world-save editor and manager. It supports inspection, backup, organization,
transfer, and carefully gated editing. Mutations require a preview, a verified
backup, and post-operation validation.

## Current development surface

The repository now includes a world-save model, deterministic discovery,
world-library projections, previewable operations, timestamped backups,
portable world packages, metadata name editing, validation, rollback, and a
minimal Tkinter world-library view. The command-line library can be invoked as:

```text
embervault-save-manager <save-directory> --json
```

Character payloads and deeper world-state data remain opaque. They are exposed
for safe discovery and backup/export only until format-specific parsers and
round-trip fixtures are available.
Save Manager For EmberVault
