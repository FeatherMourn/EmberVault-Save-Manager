# Enshrouded Save Format Research

This note records externally documented observations, not a complete parser
specification. It is intentionally conservative: identifying a component is
not the same as proving that it can be edited safely.

## World files

Public Enshrouded tooling describes a world as a base eight-character slot
file, optional `_info`, numbered rolling copies, and `-index` selecting the
latest copy. World export tooling has identified these blob families:

- `CSTR` — custom strings and IDs linked to world state
- `SNAP` — not fully understood; associated with altar/building state
- `WETR` — weather-related data
- `USER` — known characters and last-altar data
- `KNOW` — world/server knowledge
- `EXTS` — not fully understood
- `SRSG` — bulk world data, including altar and voxel/building state

Because several blobs are unknown or cross-linked, EmberVault currently treats
world payloads as opaque and limits editing to validated metadata such as the
world name.

## Character files

Public tooling identifies a single `characters` container holding multiple
characters and describes component blobs including:

- `CHAR` — primary character data, including name and inventory
- `COUT` — cosmetic appearance data
- `FOWR` — fog-of-war mask
- `KNOW` — character knowledge and progression flags

The minimum safe operation for an unknown character payload is whole-container
backup/export/import. Selective character editing requires fixtures, a parser,
cross-component invariants, and round-trip validation in the game.

## Evidence

- [EnshroudedManager technical details](https://github.com/jbostrus/EnshroudedManager)
- [Official save-management guidance](https://enshrouded.zendesk.com/hc/en-us/articles/17764283835677-Save-Game-Management)
- [Interactive save-file guide](https://gamevault.in/save-guide.html)

These references guide discovery and test planning but are not treated as a
substitute for verified local fixtures.

The active `characters-9` fixture and all nine rolling copies share the same
initial tagged layout and declared lengths for the early `COUT`, `FOWR`, and
`CHAR` regions. Their total byte contents differ substantially, so these
lengths are recorded as structural evidence only; no field-level edit is
enabled from this comparison.

The character header records also contain a four-byte value immediately after
the declared length. EmberVault records that value as a reference/check field,
but does not currently assume whether it is a checksum, identity, or pointer.

## Local fixture observation

An opt-in local fixture from world slot 1 was inspected read-only. It begins
with the `KSC1` header and exposes tagged sections in the payload, including
`EXTS`, `KNOW`, `USER`, `SRSG`, `CHNK`, `WETR`, `CSTR`, and `SNAP`. EmberVault
records these tags as an inventory only; it does not infer field layouts or
write any of the sections.
