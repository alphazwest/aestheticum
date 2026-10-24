# Facets: technical plan

See `overview.md` for scope and the yakisugi example.

## 1. File

`aestheticum.json` replaces `design-styles.json`. `schema_version` is 3.

| Key | Contents |
|---|---|
| `schema_version` | 3 |
| `vocab.facets` | Each facet: `name`, `description`, `aat` (the AAT facet or hierarchy id), `filled` (bool). |
| `vocab.relations` | Each predicate: `from` (facet), `to` (facet), `inverse` (label of the reverse direction), `description`. |
| `vocab.domains`, `vocab.tags`, `vocab.source_tiers`, `vocab.alias_sources` | Moved unchanged from the top level of `design-styles.json`. |
| `styles` | The style entries, unchanged except an optional `relations` object. |
| `techniques`, `effects` | Filled facet sections. |
| `materials`, `design_elements`, `objects`, `agents` | Defined in `vocab.facets` with `filled: false`; their sections are empty arrays. |

### Facets

| id | AAT anchor | Filled in this release |
|---|---|---|
| `styles` | Styles and Periods | yes |
| `techniques` | Activities › Processes and Techniques | yes |
| `effects` | Physical Attributes › Conditions and Effects | yes |
| `materials` | Materials | no |
| `design_elements` | Physical Attributes › Design Elements | no |
| `objects` | Objects | no |
| `agents` | Agents | no |

### Relations in this release

| Predicate | From → to | Inverse label | Meaning |
|---|---|---|---|
| `associated_styles` | techniques → styles | `techniques` | The technique is characteristic of the style. |
| `associated_styles` | effects → styles | `effects` | The effect is characteristic of the style. |
| `produces` | techniques → effects | `produced_by` | The technique gives the effect. |

A predicate may appear in more than one row; `(predicate, from)` is the key. A relation value is a
list of `{id, sources?}`. Relations live on the owning (`from`) entry only.

## 2. Schema

One JSON Schema (draft 2020-12), `schema/aestheticum.schema.json`.

- `$defs.entry_base`: `id`, `name`, `description` (≤256), `tags` (1–5), `sources` (1–4), `ids`,
  `aliases`, `variants`, `domains` — the fields every facet shares.
- `$defs.style`: `entry_base` plus `parent` and `popularity` (required, as today).
- `$defs.technique`, `$defs.effect`: `entry_base` plus `markers` (≤200, required: the look across
  domains) and `relations`. `domains` is optional for these facets. No `popularity` yet.
- `$defs.relation_target`: `{id, sources?}`.
- Each facet section is an array of its definition; empty facets are `maxItems: 0` until filled.

## 3. Validator

`validate.py` replaces `validate_styles.py`. Rules that span entries:

- Ids unique across all facets; names unique within a facet; variant names unique across the file.
- Aliases unique across the file and never equal to an entry or variant name.
- Tags from `vocab.tags`; domains and media from `vocab.domains`; alias and id systems from
  `vocab.alias_sources`.
- Style parent references and cycles (unchanged).
- Each relation key is a predicate whose `from` is the entry's facet; each target exists in the
  predicate's `to` facet; no duplicate targets in one relation.
- Source-tier rule per entry, variant, domain expression and relation target with sources.
- The summary line counts entries per facet.

## 4. Migration

A one-off script in the worker (`tools/facets/migrate.py`) writes `aestheticum.json` from
`design-styles.json`: vocabularies under `vocab`, styles as they are, empty facet sections. The
dataset commit removes `design-styles.json` and its schema and validator. The README describes the
faceted model. Style content is byte-identical after the move (a test compares each style).

## 5. Worker pipeline (`tools/facets/`)

Pattern of `tools/aliases/`: collect (network) → draft (pure) → review report → apply.

1. **Seed** `data/facets-seed.json`: per facet, candidate names with a short note and the target
   styles. About 30–40 techniques and effects for this release.
2. **Collect** writes `data/raw/facets-YYYY-MM.json`: for each candidate, AAT and Wikidata
   lookups (ids, labels, aliases), and web search results from authoritative and editorial sites,
   each page fetched and kept as text with its URL and status.
3. **Draft** (pure): builds an entry per candidate from the snapshot (description, markers,
   domains, variants, relation targets, sources with tiers by publisher class). A model call writes
   the prose fields from the fetched page text only; every claim keeps its source URL.
4. **Report** `data/facets-report-YYYY-MM.md`: each draft entry, its sources and tiers, failed
   URLs, entries that miss the source rule, and relation targets that are not style ids.
5. **Apply** writes the accepted drafts into the dataset and runs the validator.
   `data/facets-overrides.json` holds manual decisions (rejected candidates, corrected text,
   added sources), each with a reason.

## 6. rendernode-assets

- `common/constants.py`: `AESTHETICUM_DATA_FILE = "aestheticum.json"`.
- `catalog/datatypes.py`: `DatasetFile` reads `vocab.tags` and the `styles`, `techniques` and
  `effects` sections; `Dataset` gains `techniques` and `effects` by id. Style selection is unchanged.
- `spec/materials.yaml`: a treatment names `technique: <id>` or `effect: <id>` in place of
  `prompt`; an `edit_prompt` template joins `templates`.
- `catalog/builders/materials.py`: a technique or effect treatment takes its prompt text from the
  entry's `markers`, adds one edit variant per entry variant (label: the variant name; edit text:
  the variant markers) and sets the tags to the base, the entry id and the entry's region tag
  (`MAX_TAGS` is 3). `attrs` records `technique` or `effect`.
- The materials manifest records the aestheticum version, as decor and environments do.
- `charred` becomes `{label: "Shou Sugi Ban", technique: yakisugi}`; asset ids keep the
  `charred` key, so the three assets are relinked, not replaced.

## Specs and streams

| Spec | Repo | Stream | Depends on |
|---|---|---|---|
| `fac-001` Schema v3 and migration | aestheticum, worker | A | — |
| `fac-002` Validator and README | aestheticum | A | fac-001 |
| `fac-003` Facet research pipeline | worker | B | fac-001 |
| `fac-004` First techniques and effects | worker, aestheticum | B | fac-002, fac-003 |
| `fac-005` rendernode reader and technique treatments | rendernode-assets | C | fac-001 (fixture), fac-004 (content) |

Streams A, B and C start together once fac-001 fixes the file shape: B builds against the schema,
C builds against a fixture file.
