# fac-003: Facet research pipeline

## Context
See `../overview.md` and `../plan.md` §5. **Depends on**: fac-001. **Stream**: B

## Goals
- A repeatable collect → draft → report → apply pipeline turns a seed list into sourced draft entries for any facet.

## Relevant Files
**New**: `../aestheticum-worker/tools/facets/collect.py` - network stage; writes the raw snapshot.
**New**: `../aestheticum-worker/tools/facets/draft.py` - pure stage; builds draft entries.
**New**: `../aestheticum-worker/tools/facets/report.py` - writes the review report.
**New**: `../aestheticum-worker/tools/facets/apply.py` - writes accepted drafts into the dataset.
**New**: `../aestheticum-worker/data/facets-seed.json` - candidates per facet.
**New**: `../aestheticum-worker/data/facets-prose.json` - prose per candidate with cited URLs.
**New**: `../aestheticum-worker/data/facets-overrides.json` - manual decisions with reasons.
**New**: `../aestheticum-worker/tests/test_facets_*.py`.
**Reference**: `../aestheticum-worker/tools/aliases/` - pipeline pattern, snapshot naming, overrides.

## What to Implement
### 1. Seed
- Per facet, a list of `{id, name, note, styles, produces?, sources}`: `styles` are the style ids the candidate is expected to relate to; `sources` are 2–4 `{url, publisher, tier}` found by research (the tier set by the publisher class of the README's tier table).

### 2. Collect
- For each candidate: fetch each seed source page and keep URL, final URL, status, title and text; Getty AAT (a seed source on vocab.getty.edu whose English labels include the name) and Wikidata (item by AAT id, else a unique exact label).
- Write `data/raw/facets-YYYY-MM.json`; HTTP responses are cached under `.cache/` (not committed).

### 3. Prose and draft
- Prose fields (`description`, `markers`, domain markers, variant descriptions and markers), tags and associated styles are written in a Claude session from the fetched page texts only, into `data/facets-prose.json`; every text cites the URLs it rests on.
- Draft (pure) merges the seed, the snapshot and the prose: sources from the fetched seed sources, ids from the snapshot, relation targets from the cited associated styles that are styles and from the seed's `produces` that are effects. A text that cites nothing or an unfetched page is dropped and reported; an entry without a description or markers is blocked.
- Aliases come from the alias pipeline, not from the draft.
- Output: draft entries in the v3 facet shape.

### 4. Report and apply
- The report lists each draft, its sources and tiers, failed URLs, rule misses and unsupported relation targets.
- Apply takes the accepted ids, applies `facets-overrides.json`, writes the entries in id order and runs `validate.py`.

## Edge Cases
- A candidate with no AAT or Wikidata record - drafted without `ids`; flagged in the report.
- A page that redirects to a different topic - source dropped; reported.
- A name that matches an existing style or alias - drafted as a conflict; never applied without an override.
- A prose text citing a URL that was not fetched, or citing nothing - dropped; reported.
- Apply run twice - the second run changes nothing.

## Testing
- `draft.py` is pure: tests run it on a small in-memory seed, snapshot and prose and compare with the expected drafts and issues.
- `apply.py` tests run on a temporary copy of a minimal v3 file.
- No network in tests.

## Implementation Details
<!-- TO BE FILLED IN AFTER IMPLEMENTATION -->
