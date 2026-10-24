# fac-001: Schema v3 and migration

## Context
See `../overview.md` and `../plan.md` §1, §2, §4. **Depends on**: —. **Stream**: A

## Goals
- `aestheticum.json` (schema v3) holds a shared `vocab` and one section per facet.
- Styles move into it with identical content.
- Every reader of the old file in the worker reads the new one.

## Relevant Files
**New**: `aestheticum.json` - the dataset.
**New**: `schema/aestheticum.schema.json` - JSON Schema (draft 2020-12) for the file.
**New**: `../aestheticum-worker/tools/facets/migrate.py` - one-off writer of `aestheticum.json` from `design-styles.json`.
**Modify**: `../aestheticum-worker/paths.py` - `DATASET` names `aestheticum.json`.
**Modify**: `../aestheticum-worker/tools/aliases/{collect,apply}.py`, `../aestheticum-worker/scripts/pop/{collect,compute,export}.py`, `../aestheticum-worker/scripts/houzz_full.py` - read the dataset path from `paths.DATASET`; read styles from `styles` and vocabularies from `vocab`.
**Remove**: `design-styles.json`, `schema/design-styles.schema.json` (the validator moves in fac-002).
**Reference**: `schema/design-styles.schema.json` - field rules to carry over.

## What to Implement
### 1. Vocabulary
- `vocab.facets`: the seven facets of `plan.md` §1 with `name`, `description` and `aat`.
- `vocab.relations`: owning facet → predicate → `to`, `inverse` and `description` (`plan.md` §1).
- `vocab.domains`, `vocab.tags`, `vocab.source_tiers`, `vocab.alias_sources`: moved unchanged.

### 2. Schema
- `$defs.entry_base`, `$defs.surface_entry_base`, `$defs.style`, `$defs.technique`, `$defs.effect` as in `plan.md` §2.
- `$defs.relations`: an object whose keys are predicate names and whose values are lists of `{id, sources?}` (the validator checks keys against `vocab.relations`).
- Empty facets: `$defs.empty_facet` (`maxItems: 0`).

### 3. Migration
- `migrate.py <v2> <v3>` reads `design-styles.json` and writes `aestheticum.json` in the repo's JSON formatting (pre-commit `pretty-format-json --no-sort-keys`: two-space indent, key order kept).
- `schema_version` is 3; `techniques` and `effects` are empty arrays.

### 4. Worker readers
- `dataset.py`: `load` (checks `schema_version`) and `save` (formatting, atomic replace). Every script that reads or writes the dataset uses it.

## Edge Cases
- A style with keys outside the v2 schema - migration fails and names the style.
- A worker script run against a v2 file - it fails with a message naming `schema_version`.
- The dataset repo and the worker change in different commits - the worker change lands after the dataset commit; the worker README names the schema version it reads, and `dataset.load` refuses another version naming `AESTHETICUM_DIR`.
- The migration run on an existing output file - refused; the file is unchanged.
- A v2 document without one of its vocabularies - migration fails naming it.

## Testing
- Worker tests run `migrate()` and `main()` on a small v2 fixture and check the v3 shape, the guards and the file text.
- Worker tests check `dataset.load` refuses a v2 file and a missing file, and `dataset.save` round-trips.
- A one-off check compares each migrated style with its v2 form (equal as JSON objects).
- The new schema validates `aestheticum.json` (fac-002 adds the cross-entry rules).

## Implementation Details
<!-- TO BE FILLED IN AFTER IMPLEMENTATION -->
