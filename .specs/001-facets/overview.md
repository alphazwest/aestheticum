# Facets: a faceted vocabulary of visual aesthetics

## Summary

Aestheticum grows from one facet (styles and periods) into a faceted vocabulary modelled on the
Getty Art & Architecture Thesaurus (AAT). An entry belongs to one facet. Entries link to each other
through typed, one-direction relations. Every entry is sourced under the same tier rules as styles.

The first release fills two new facets:

- **Techniques** (AAT Activities › Processes and Techniques): a process applied to a substrate
  that sets its look. Examples: yakisugi, tadelakt, limewash, cerusing, fumed oak, French polish,
  urushi, kintsugi, raku, shibori, sgraffito, gilding, board-formed concrete.
- **Effects** (AAT Physical Attributes › Conditions and Effects): a surface condition, made on
  purpose or by time. Examples: charred, patina, verdigris, weathered, distressed, crackle.

The other AAT facets (materials, design elements, objects, agents) are defined in the vocabulary
and stay empty until a consumer needs them (see `ROADMAP.md`).

## Problem

A style entry describes a whole aesthetic across domains. Some concepts that consumers need are
not styles: yakisugi is a cladding and paneling technique linked to Japanese, Minka, Japandi and
Wabi-Sabi, with its own grades (Suyaki, Gendai, Pika-Pika) and finishes. Without a place for
these concepts, consumers write their own loose text ("burnt, blackened surface with alligatored
char"), which drifts from what the technique is.

## Goals

1. One file, `aestheticum.json`, with one schema: a shared `vocab` and one section per facet.
2. Styles keep their content, ids, tags, domains and popularity.
3. Techniques and effects use the style entry shape: `id`, `name`, `description`, `tags`,
   `sources`, `ids`, `aliases`, `markers`, `domains`, `variants`, plus `relations`.
4. Relations are stored once, on the owning entry; the vocabulary names each predicate and its
   inverse label.
5. A repeatable worker pipeline researches, sources and drafts facet entries for review.
6. rendernode-assets reads `aestheticum.json`; its material treatments take their prompt, variants
   and tags from a technique or an effect. Charred wood becomes Shou Sugi Ban: charred, brushed
   once and oiled, with Suyaki, Pika-Pika and unoiled variants.

## Out of scope

- Filled materials, design-element, object and agent facets.
- Demand scores (`popularity`) for techniques and effects.
- Techniques and effects in environment and decor generation (focal assets, facet variants).
- A database.

All four are in `ROADMAP.md`.

## Data model

| Concept | What it is | Example |
|---|---|---|
| Facet | A top-level class of concept, from `vocab.facets`, anchored on an AAT facet. | `techniques` |
| Entry | One concept in one facet. Ids are unique across all facets. | `yakisugi` |
| Relation | A typed link from an owning entry to target entries, with optional sources. | `yakisugi.relations.associated_styles → japanese` |
| Predicate | A relation type in `vocab.relations`: its owning facet, target facet and inverse label. | `associated_styles` (techniques → styles), inverse `techniques` |
| Variant | A named nuance inside an entry (a grade, a finish, a regional form). | Yakisugi › Suyaki |

## Example: yakisugi

```json
{
  "id": "yakisugi",
  "name": "Yakisugi",
  "description": "Japanese technique of charring the surface of wood boards, traditionally sugi, then brushing and oiling them, for cladding and paneling.",
  "tags": ["japanese", "vernacular", "dark"],
  "aliases": [{"name": "Shou sugi ban", "sources": [...]}],
  "markers": "Charred, wire-brushed once and oiled: deep matte black-brown, silky low sheen, subtle burnt-grain shadows.",
  "domains": {
    "architecture": {"media": ["buildings"], "markers": "Vertical charred-board cladding on farmhouses and storehouses."},
    "interior": {"markers": "Charred-board feature walls and ceilings in deep matte black."}
  },
  "relations": {
    "associated_styles": [{"id": "minka", "sources": [...]}, {"id": "japanese"}, {"id": "japandi"}, {"id": "wabi-sabi"}],
    "produces": [{"id": "charred"}]
  },
  "variants": [
    {"name": "Suyaki", "markers": "Unbrushed: thick soot layer, cracked alligator char."},
    {"name": "Pika-Pika", "markers": "Brushed twice: burnt latewood ridges, lighter earlywood between them."},
    {"name": "Gendai", "markers": "Brushed once, unoiled: smooth, silky, deep black, soot-dry surface."}
  ],
  "sources": [...]
}
```

## Implementation Guidelines for AI Agents

- **Repositories.** `~/dev/aestheticum/aestheticum` (public dataset, MIT, branch `master`),
  `~/dev/aestheticum/aestheticum-worker` (private collectors; writes into the sibling dataset
  checkout, override with `AESTHETICUM_DIR`), `~/dev/rendernode-assets/rendernode-assets` (first
  consumer; `catalog/builders/aestheticum.py` loads the dataset, `catalog/builders/materials.py`
  builds material swatches).
- **Canonical docs** (README, schema descriptions) describe what the dataset is, in timeless voice:
  no "currently", no history, no rationale. Journey notes go in the worker's `ref/logs/`.
- **Sources.** Tier 1 authoritative, tier 2 commercial or editorial, tier 3 open. An entry, a
  variant or a domain expression with sources cites at least one tier 1 or tier 2 source; one tier 2
  alone is flagged; tier 3 alone is excluded. Every URL resolves to the cited page.
- **Identifiers and aliases** follow the README rules: AAT and Wikidata ids only when the record's
  label is the entry's name; aliases from AAT or two independent systems.
- **Python.** uv (never `uv pip`), ruff, modern typing, pytest. Run the validator and the tests
  before every commit.
- **Git.** No `Co-Authored-By` or agent attribution in commits. Confirm with the owner before a
  commit or push to the dataset repo. Never force-push `master`.
- **Worker context.** `ref/seed/design-styles-authoritative-reference.md` is the style seed list;
  `ref/logs/2026-10-14-popularity-model.md` defines the popularity model that facet demand reuses
  later; `tools/aliases/` is the pattern for collect → reconcile → apply pipelines with dated raw
  snapshots and an overrides file with reasons.
- **Consumer rules (rendernode-assets).** Changes are additive; never reset or rewrite existing
  images or metadata. No live provider calls or generation runs without the owner's approval.
  Run only the tests for changed code locally; CI runs the full suite.
