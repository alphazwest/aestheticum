# Aestheticum

A canonical, sourced reference of visual aesthetics and the domains in which they appear.

Each aesthetic (Art Deco, Bauhaus, Wabi-Sabi, Victorian) is a single entry with a name, a description, tags and citations. Each entry records the domains in which the aesthetic appears (architecture, furniture, fashion, transportation and others) and the visual markers that identify it in each domain.

## Motivation

Style names are used loosely. One retailer's "Boho" is another's "Bohemian"; a museum files the same objects under a period, a movement or a culture; a design magazine coins a new label each season. Systems that generate, search or classify images need one vocabulary of aesthetics with stable identifiers, clear boundaries, the visual features that identify each aesthetic in each medium, and citations that a reader can check. Aestheticum is that vocabulary. It also records how prominent each aesthetic is, so that a consumer can weight common and rare styles.

## Data model

The reference has four parts.

| Concept | What it is | Example |
|---|---|---|
| **Aesthetic** | A canonical style, period or movement. One entry per aesthetic. An optional `parent` gives the hierarchy. | `streamline-moderne` → parent `art-deco` |
| **Domain** | A medium or discipline in which an aesthetic appears. From a fixed list. | `furniture`, `transportation` |
| **Media** | A finer division of a domain. From a fixed list for each domain. | `transportation` → `automotive`, `aviation` |
| **Markers** | The visual features of one aesthetic in one domain. | Art Deco × transportation: "streamlined bodies, chrome speed lines" |
| **Variant** | A named nuance inside an aesthetic: a sub-movement, group or regional form whose look the aesthetic already covers. Not indexed as an entry. | `retro-futurism` → Vaporwave, Cassette Futurism |

A `parent` links two indexed entries; a variant lives inside one entry and has no `id`. Queries return the entry; applications can use a variant's markers for more specific output.

Aesthetic and domain are the two axes of classification. The markers are the observable expression of an aesthetic in a domain. An aesthetic has one entry. Its domains are keys inside that entry, so the entry is never duplicated.

### Focal-point rule

A subject belongs to the domain that is the focal point of the image. An Art Deco lobby with its chandelier as the focal point is `lighting`. The same lobby shown as a whole room is `interior`. Where the focus is unclear, the dataset does not decide; consumers decide (see [Example use](#example-use-assets-and-lenses)).

## Domains

| id | Domain | Description | Media |
|---|---|---|---|
| `architecture` | Architecture | Buildings, landscapes and urban spaces as built form: exteriors, massing, roofs and structure. | buildings, landscape, urban |
| `interior` | Interior | Interior spaces as composed wholes: layout, wall and floor finishes, furnishing and decoration. | — |
| `furniture` | Furniture | Movable furnishings for sitting, lying, storage and work, seen as individual designed objects. | seating, tables, storage, beds |
| `lighting` | Lighting | Light fixtures and the lighting of spaces, where light is the focal point. | indoor, exterior, landscape, public |
| `decorative-arts` | Decorative Arts | Functional and ornamental objects of craft materials. | ceramics, glass, metalwork, textiles, wallcoverings, arms and armor, musical instruments |
| `product` | Product | Mass-produced manufactured objects. | appliances, electronics, tools, toys, housewares |
| `transportation` | Transportation | Vehicles as designed form. | automotive, motorcycles, aviation, rail, marine |
| `fashion` | Fashion | Clothing and personal adornment as worn. | apparel, footwear, accessories, jewelry |
| `visual-design` | Visual Design | Visual communication in print and on screen. | graphic, typography, illustration, digital, games |
| `fine-art` | Fine Art | Autonomous artworks. | painting, drawing, printmaking, sculpture, photography, installation |
| `film` | Film | The cinematic image and the designed worlds of screen and stage. | cinematography, animation, production design |

The domain list is anchored on the Getty Art & Architecture Thesaurus (AAT) Disciplines hierarchy ([300054134](http://vocab.getty.edu/page/aat/300054134)). It is cross-checked against the NCES Classification of Instructional Programs, the BLS Standard Occupational Classification, ISCO-08, the UNESCO Framework for Cultural Statistics, NAICS 5414, and the collection structures of the V&A, The Met, MoMA and Cooper Hewitt.

The data file defines the domain vocabulary under `domains`. Each domain has a `name`, a `description`, an `aat` ID (the closest Getty AAT concept, or `null` when AAT has none) and its `media` list. Interior has no media.

## Aesthetic entry

```json
{
  "id": "art-deco",
  "name": "Art Deco",
  "parent": null,
  "description": "Style of the 1920s–1930s: bold geometry, zigzags and sunbursts, stepped forms, lacquer, chrome, exotic veneers and luxurious materials expressing machine-age glamour.",
  "tags": ["modernist", "glamorous", "geometric", "bold", "gilded"],
  "sources": [
    {"title": "Art Deco", "publisher": "Victoria and Albert Museum", "url": "https://www.vam.ac.uk/collections/art-deco", "tier": 1}
  ],
  "domains": {
    "architecture": {"media": ["buildings"], "markers": "setbacks, spandrels, sunburst spires"},
    "transportation": {"media": ["automotive", "marine"], "markers": "streamlined bodies, chrome speed lines, hood ornaments"},
    "fine-art": {
      "media": ["painting", "sculpture"],
      "markers": "stylized geometric figures, metallic sheen",
      "media_markers": {"sculpture": "chryselephantine and bronze-and-ivory figures"}
    }
  }
}
```

| Field | Type | Rule |
|---|---|---|
| `id` | string | Lowercase slug, unique. |
| `name` | string | Canonical name, unique. One style per entry; no merged names. |
| `parent` | string \| null | `id` of the broader style that this style is a variant, sub-period or regional form of. A revival points to its original style. |
| `description` | string | 256 characters or fewer. Domain-neutral. |
| `tags` | string[] | 1–5 tags from the tag vocabulary. Tags describe the look, not the medium. |
| `sources` | Source[] | Citations for `description`. 1–4 entries. |
| `ids` | object | Optional. External identifiers for the same concept: `aat` (Getty AAT, 9 digits) and `wikidata` (Q-number). |
| `aliases` | Alias[] | Optional. Other names that other sources use for the same aesthetic: reconciliation keys. Each has `name` and `sources`, a list of `{"source", "ref"}` objects; `source` is `aat`, `wikidata`, `enwiki`, `houzz` or `wayfair`, and `ref` is that system's identifier or label. Unique across the dataset; never equal to an entry or variant name. |
| `popularity` | object | `score`: relative prominence of the aesthetic across all evidence, in (0, 1). `design_demand`: relative demand in home and design media and marketplaces, in (0, 1); `null` for an entry outside the architecture, interior, furniture, lighting and decorative-arts domains. Both are relative values within this dataset, not absolute measures. See [Popularity](#popularity). |
| `variants` | Variant[] | Optional. Each variant has `name` (unique across entries and variants), `description` (≤256), `markers` (≤200), optional `domains` (a subset of the entry's domains) and `sources`. |
| `domains` | object | At least one key. Keys are domain ids from the domain vocabulary. Each value is an object with optional fields: `media` (from that domain's list; omitted means the domain as a whole), `markers`, `media_markers` (keys from `media`) and `sources`. |

### Tags

The tag vocabulary is defined in the data file under `tags`, in groups: era, character, form, palette, material, region and setting. Region tags cover Europe, the Americas (including Native North America and the Caribbean), Africa, the Middle East, Central Asia, the Himalaya, South, Southeast and East Asia, and Oceania. Tags describe the character of an aesthetic. Domains and media describe where it appears; they are never tags.

### Sources

Every source has a tier.

| Tier | Kind | Examples |
|---|---|---|
| 1 | Authoritative: museums, encyclopedias, universities, government preservation offices, standards bodies | The Met, V&A, Britannica, Getty, National Park Service |
| 2 | Commercial or editorial | Architectural Digest, Dezeen, auction houses, retailers |
| 3 | Open, contributor-edited | Wikipedia |

Every entry, variant and domain expression with sources cites at least one tier 1 or tier 2 source:

| Sources | Status |
|---|---|
| Tier 1 | Included |
| Tier 2 and tier 3 | Included |
| Two or more tier 2 | Included |
| One tier 2 only | Included and flagged for review |
| Tier 3 only | Not included |

Every URL resolves to the cited page.

## Identifiers and aliases

`alias_sources` in the data file lists the reference systems that identifiers and aliases cite: Getty AAT, Wikidata, English Wikipedia, Houzz and Wayfair. Each has a `url` template with a `{ref}` placeholder and the character that replaces spaces in a `ref`, so every identifier and alias resolves to a page. For example `{"source": "enwiki", "ref": "Style Moderne"}` resolves to `https://en.wikipedia.org/wiki/Style_Moderne`.

**Identifiers.** An entry's Getty AAT ID is a cited AAT record whose English label is the entry's name. Its Wikidata ID is the item linked to that AAT record, else the unique item whose English label is the entry's name. A Wikidata item counts only when it is a style concept (a style, movement, period, culture or genre), not a person, place, people or organization.

**Aliases** are other names that other sources use for the same aesthetic. They are reconciliation keys, not new names. An alias is accepted when Getty AAT gives it, or when two independent systems give it. These are never aliases:

- a spelling variant of the entry's own name (case, diacritics, hyphens, spacing or a trailing "style");
- a derived form of the name (-ism, -ist, -istic, -ian, -esque);
- an inverted index form ("Deco, American");
- a Wikipedia redirect that Wikipedia marks as a misspelling, a plural or a subtopic;
- a name that is another entry's name or variant name, or that two entries claim.

A small number of manual decisions correct identifiers or add marketplace labels. Each has a recorded reason.

## Popularity

Each entry has two values in `popularity`. Both are relative values within this dataset, in (0, 1).

- `score`: how prominent the aesthetic is across reference, museum, editorial and marketplace evidence.
- `design_demand`: how much demand the aesthetic has in home and design media and marketplaces. It applies to entries in the architecture, interior, furniture, lighting and decorative-arts domains, and is `null` for other entries.

### Evidence

| Group | Sources | Signal |
|---|---|---|
| Reference | Wikipedia (all language editions), Wikidata, Wikimedia Commons | Readership over 12 months, number of language editions, incoming links, references, article length, media files, and use of the aesthetic as the style, movement or genre of other items. |
| Museums | The Metropolitan Museum of Art, Victoria and Albert Museum, Art Institute of Chicago, Cleveland Museum of Art | Collection objects associated with the aesthetic. |
| Editorial | Architectural Digest, House Beautiful, Elle Decor, Veranda, Dwell, House & Garden, 1stDibs, ArchDaily, Christie's, Sotheby's, Vogue, British Vogue, WWD, Harper's Bazaar, Creative Bloq, Eye, Hagerty | Published articles and listings about the aesthetic. |
| Marketplaces | Houzz, Wayfair | Project photos and product listings in the aesthetic. |

Evidence counts only where a source covers the aesthetic's domains:

- **Museums:** all aesthetics except contemporary decor styles.
- **Design publications and marketplaces:** architecture, interior, furniture, lighting and decorative arts.
- **Fashion publications:** fashion.
- **Visual-culture publications:** visual design and fine art.
- **Automotive publications:** transportation.

Evidence that is out of scope is missing, not zero.

### Matching

Each source is matched to an entry by the entry's name and its variant names. Some names have more than one meaning: they also name a place, a person, a people or a historical period. For these, the matching uses a qualified term ("Hamptons style"), or a curated term ("Pop art", "Song dynasty"). A source that cannot separate the meanings contributes at most a median value for such a name. A marketplace label counts for the entry of the same style, a synonym ("Boho" for Bohemian), or the marketplace's sub-labels of that style ("Country Farmhouse" for Farmhouse). It never counts for a broader style.

### Calculation

1. **Normalize.** Each source's counts are log-scaled and converted to robust z-scores against the median of all entries, then clipped to ±4. A source that covers only a subset of popular styles is put on the scale of a full-coverage source in the same group.
2. **Group.** A group's value is the weighted mean of its sources' values. The reference signals are weighted: readership 0.30, language editions 0.20, incoming links 0.15, references 0.10, length 0.10, media files 0.10, use by other items 0.05. Sources in the other groups have equal weight.
3. **Combine.** `score` weights the groups reference 0.35, museums 0.25, editorial 0.20 and marketplaces 0.20. `design_demand` weights design publications 0.40 and marketplaces 0.60. A missing group counts as the median: no evidence counts as average evidence.
4. **Smooth over the hierarchy.** Each value is pulled 30% toward its neighbours in the hierarchy (70% the mean of its sub-styles, 30% its parent). A broad style gains from popular sub-styles, and a sub-style gains a little from its parent.
5. **Scale.** Values are scaled to the open interval (0, 1).

### Stability

The rank order of `score` keeps a Spearman correlation of at least 0.99 when any group weight changes by ±25% or the hierarchy weight changes by ±0.1. It keeps at least 0.93 when any single source is removed. The rank order of `design_demand` keeps at least 0.99 when either group weight changes by ±25%. The values come from evidence collected in October 2026.

## Example use: assets and lenses

This repository holds the reference data. Applications that use it add their own layers. The example below shows one way to structure them.

**Assets** are images. Each asset records the aesthetic and domain it was made for (`intent`) and every domain it shows (`depicts`), with a prominence of `focal` or `present`:

```json
{
  "id": "img_0412",
  "intent": {"aesthetic": "bauhaus", "domain": "interior"},
  "depicts": [
    {"domain": "interior", "prominence": "focal"},
    {"domain": "furniture", "prominence": "present"},
    {"domain": "lighting", "prominence": "present"}
  ]
}
```

**Lenses** are named views that an application defines. A lens is a set of domains plus an inclusion rule:

| Lens | Domains | Rule |
|---|---|---|
| Rooms | `interior`, `architecture` | `focal` only |
| Furniture | `furniture` | `focal` first, then `present` |

The Bauhaus room above is a primary result in the Rooms lens and a secondary result in the Furniture lens. One image serves both views, and no entry is duplicated. The focal-point rule sets the default prominence; the lens decides what to show. Disagreement about a view is resolved by changing the lens, not the reference data.

## Files

| Path | Contents |
|---|---|
| `design-styles.json` | The dataset: `schema_version`, `source_tiers`, `domains`, `alias_sources`, `tags` and `styles`. |
| `schema/design-styles.schema.json` | JSON Schema (draft 2020-12) for the dataset structure. |
| `validate_styles.py` | Validator: the JSON Schema plus rules across entries. |
| `tests/` | Validator tests. |

## Validation

```sh
uv sync
uv run python validate_styles.py
uv run pytest
```

The validator checks the dataset against the JSON Schema: required fields, slugs, lengths, tag and source counts, source tiers, value ranges and `https` URLs. It then checks rules across entries: unique ids and names, unique aliases, tag and domain vocabularies, media per domain, alias and identifier systems, and parent references and cycles. It exits with status 1 on any error. CI runs the validator tests on every push to `master`.

## License

[MIT](LICENSE). Cited sources remain the property of their publishers; the dataset links to them and does not reproduce them.
