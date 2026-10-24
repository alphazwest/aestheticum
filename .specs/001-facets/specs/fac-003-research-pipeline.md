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
**New**: `../aestheticum-worker/data/facets-overrides.json` - manual decisions with reasons.
**New**: `../aestheticum-worker/tests/test_facets_*.py`.
**Reference**: `../aestheticum-worker/tools/aliases/` - pipeline pattern, snapshot naming, overrides.

## What to Implement
### 1. Seed
- Per facet, a list of `{name, note, styles}`: `styles` are the style ids the candidate is expected to relate to.

### 2. Collect
- For each candidate: Getty AAT (label search, then record), Wikidata (item by AAT id, else exact label), and web search restricted to a publisher allow-list per tier (museums, encyclopedias, universities and standards bodies for tier 1; design and trade publications and manufacturers for tier 2).
- Fetch each result page; keep URL, final URL, status, title and text.
- Write `data/raw/facets-YYYY-MM.json`; HTTP responses are cached under `.cache/` (not committed).

### 3. Draft
- Tier per source from the publisher allow-list.
- Ids and aliases by the README identifier and alias rules.
- Prose fields (`description`, `markers`, domain markers, variant markers) are written by a model call that receives only the fetched page texts and must cite the URL of each claim; a claim without a cited URL is dropped.
- Relation targets: the seed's `styles` that the sources support; others go to the report.
- Output: draft entries in the v3 facet shape.

### 4. Report and apply
- The report lists each draft, its sources and tiers, failed URLs, rule misses and unsupported relation targets.
- Apply takes the accepted ids, applies `facets-overrides.json`, writes the entries in id order and runs `validate.py`.

## Edge Cases
- A candidate with no AAT or Wikidata record - drafted without `ids`; flagged in the report.
- A page that redirects to a different topic - source dropped; reported.
- A name that matches an existing style or alias - drafted as a conflict; never applied without an override.
- A model claim citing a URL that was not fetched - dropped.
- Apply run twice - the second run changes nothing.

## Testing
- `draft.py` is pure: tests run it on a small committed snapshot fixture and compare with expected drafts (model calls stubbed).
- `apply.py` tests run on a temporary copy of a minimal v3 file.
- No network in tests.

## Implementation Details
<!-- TO BE FILLED IN AFTER IMPLEMENTATION -->
