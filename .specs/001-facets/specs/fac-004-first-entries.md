# fac-004: First techniques and effects

## Context
See `../overview.md`. **Depends on**: fac-002, fac-003. **Stream**: B

## Goals
- About 30–40 sourced technique and effect entries in `aestheticum.json`, yakisugi among them.

## Relevant Files
**Modify**: `../aestheticum-worker/data/facets-seed.json` - the candidates below.
**Modify**: `../aestheticum-worker/data/facets-overrides.json` - review decisions.
**Modify**: `aestheticum.json` - the applied entries.

## What to Implement
### 1. Seed
- **Techniques:** yakisugi, tadelakt, limewash, cerusing, fumed oak, wire brushing, French polish, urushi, japanning, kintsugi, raku, shibori, batik, sgraffito, gilding, marquetry, intarsia, venetian plaster (marmorino), board-formed concrete, bush-hammering, terrazzo casting, encaustic, decoupage.
- **Effects:** charred, patina, verdigris, weathered, distressed, crackle, sun-bleached, rusted, antiqued, honed, polished.
- Each candidate names its expected styles (yakisugi: japanese, minka, japandi, wabi-sabi).

### 2. Yakisugi
- `markers` (the main look): charred, wire-brushed once and oiled; deep matte black-brown, silky low sheen, subtle burnt-grain shadows.
- Variants: Suyaki (unbrushed, thick soot, alligator char), Pika-Pika (brushed twice, burnt latewood ridges), Gendai (brushed once, unoiled).
- Alias: Shou sugi ban.
- `produces`: charred.

### 3. Review
- Run the pipeline, review the report with the owner, record decisions in overrides, apply.

## Edge Cases
- A seed name that is a material, not a technique (terrazzo) - kept only as the casting technique; the material waits for the materials facet.
- A technique whose sources support no seed style - applied with no `associated_styles`.
- Overlap between a technique and an effect (wire brushing, weathered) - both entries; the technique `produces` the effect.

## Testing
- `validate.py` passes; the summary counts entries per facet.
- Spot check of every URL in the yakisugi entry.

## Implementation Details
<!-- TO BE FILLED IN AFTER IMPLEMENTATION -->
