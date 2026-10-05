# Controlled real-save validation protocol

Real-save validation is opt-in and is not part of normal Save Manager startup,
CI, discovery, backup planning, or synthetic tests.

Before a future validation adapter may inspect a private fixture:

1. The user explicitly selects and confirms the fixture root.
2. Enshrouded is closed.
3. A verified current-state backup exists and has an operation ID.
4. Control Center approves the profile and operation.
5. The inspection is read-only and records hashes before and after.
6. No restore, mutation, install, or mod operation occurs during validation.
7. Recovery evidence is written after inspection.
8. The result is classified as observed evidence, partial, blocked, or
   unsupported; it is never promoted automatically.

The current Save Manager implementation only provides the gate and synthetic
fixtures. It does not inspect the user's real save files.
