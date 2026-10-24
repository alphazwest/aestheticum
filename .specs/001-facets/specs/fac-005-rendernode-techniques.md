# fac-005: rendernode reader and technique treatments

## Context
See `../overview.md` and `../plan.md` §6. **Depends on**: fac-001 (fixture), fac-004 (content). **Stream**: C

## Goals
- rendernode-assets reads `aestheticum.json`.
- A material treatment takes its prompt, variants and tags from a technique or an effect.
- Charred wood becomes Shou Sugi Ban (charred, brushed once and oiled) with Suyaki, Pika-Pika and Gendai variants.

## Relevant Files
**Modify**: `common/constants.py` - `AESTHETICUM_DATA_FILE`.
**Modify**: `catalog/datatypes.py` - `DatasetFile` (v3 layout), `Dataset.techniques`, `Dataset.effects`, technique and effect models.
**Modify**: `catalog/builders/aestheticum.py` - load the facet sections.
**Modify**: `catalog/spec.py` - a treatment has `prompt`, `technique` or `effect` (exactly one); materials `templates.edit_prompt`.
**Modify**: `catalog/builders/materials.py` - technique and effect treatments; edit variants; tags; attrs.
**Modify**: `spec/materials.yaml` - `edit_prompt`; `charred: {label: "Shou Sugi Ban", technique: yakisugi}`.
**Modify**: `manifests/*.json` - rebuilt.
**Reference**: `catalog/builders/utils.py` (`build_variants`, `fill_template`), `catalog/builders/decor.py` (aestheticum use and versioning).

## What to Implement
### 1. Reader
- Load `vocab.tags` and the `styles`, `techniques` and `effects` sections; style selection is unchanged.

### 2. Treatments
- A treatment with `technique` or `effect` takes its prompt text from the entry's `markers`, as "{entry name}: {markers}".
- One edit variant per entry variant: label = variant name, id suffix = slug of the name, edit text = the variant markers through `templates.edit_prompt`.
- Tags: the base slug, the entry id, the entry's first region tag (`MAX_TAGS` is 3).
- `attrs`: `technique` or `effect` with the entry id.
- An unknown technique or effect id is `SpecInvalid` naming the treatment.

### 3. Version
- The materials manifest records the aestheticum version when any treatment reads a facet entry.

### 4. Rebuild
- Rebuild the three manifests; the charred assets keep their ids (`material.wood.<base>.charred`), so the build relinks them.

## Edge Cases
- A technique with no variants - the asset has the cover only.
- An entry with no region tag - tags are the base slug and the entry id.
- A treatment with both `prompt` and `technique` - `SpecInvalid`.
- The aestheticum checkout on a v2 commit - `DatasetUnreadable` naming `schema_version` and `AESTHETICUM_DIR`.
- Existing approved charred covers - flagged `prompt_changed` by the build; images are kept.

## Testing
- Builder tests with a small v3 fixture: a technique treatment with three variants, an effect treatment, an unknown id, both `prompt` and `technique`.
- Reader test: a v2 file fails with the named error.
- Only the changed tests run locally; CI runs the full suite.

## Implementation Details
<!-- TO BE FILLED IN AFTER IMPLEMENTATION -->
