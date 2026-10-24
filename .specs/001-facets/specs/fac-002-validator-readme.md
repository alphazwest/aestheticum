# fac-002: Validator and README

## Context
See `../overview.md` and `../plan.md` §3. **Depends on**: fac-001. **Stream**: A

## Goals
- One validator checks the whole faceted file: schema, then rules across entries and facets.
- The README describes the faceted model.

## Relevant Files
**New**: `validate.py` - the validator.
**Modify**: `tests/test_validator.py` - cases for facets and relations.
**Modify**: `README.md` - data model, facets, relations, files and validation sections.
**Modify**: `.github/workflows/ci.yml` - runs `validate.py` before pytest.
**Remove**: `validate_styles.py`.
**Reference**: `validate_styles.py` - the existing rules and messages.

## What to Implement
### 1. Rules
- All rules of `plan.md` §3. Messages name the facet and entry: `techniques/yakisugi: unknown relation target 'minka-x'`.
- The style rules (parents, cycles, domains and media, aliases, id systems) keep their behaviour.

### 2. Source-tier rule
- Checked for every entry, variant, domain expression and relation target that has sources.
- One tier 2 source alone is a warning, not an error; tier 3 alone is an error.

### 3. Output
- `uv run python validate.py [path]` prints errors and warnings, then one line: entries per facet, errors, warnings. Exit status 1 on any error.

### 4. README
- Data model table: facet, entry, relation, predicate, variant.
- A facets table from `vocab.facets` and a relations table from `vocab.relations`.
- The yakisugi entry as the technique example.
- Files and validation sections name `aestheticum.json`, `schema/aestheticum.schema.json` and `validate.py`.
- Timeless voice; no migration notes.

## Edge Cases
- A relation key that is a predicate of another facet - error naming the predicate's `from` facet.
- A relation target in the wrong facet (a technique `produces` a style) - error.
- The same id in two facets - error naming both facets.
- An entry in a facet section held empty by the schema - schema error.
- A relation target listed twice - error.

## Testing
- Each rule has a failing fixture and the real dataset passes.
- Tests use small in-memory documents built from a minimal valid v3 fixture.

## Implementation Details
<!-- TO BE FILLED IN AFTER IMPLEMENTATION -->
