# Roadmap

Planned directions for the dataset. Each item names its trigger: the condition under which the work starts.

## Materials facet

Fill the `materials` facet (AAT Materials): wood and its species (sugi, oak, ash), plaster, stone, clay, metal, glass, textile, paper. Add the `applies_to` predicate (techniques and effects → materials), so a consumer can check that a technique fits a substrate (yakisugi on wood, tadelakt on lime plaster).

**Trigger:** a consumer needs to validate or choose substrates from the dataset.

## Facet demand

Give techniques and effects the `popularity` fields that styles have (`score`, `design_demand`), with the same model: Houzz photo counts, marketplace product counts (Wayfair, Material Bank), design-publication mentions and reference signals, normalized against all entries of the facet. Consumers use `design_demand` to decide how many images a facet earns.

**Trigger:** at least about 100 entries in a facet, so the median and the robust z-scores mean something.

## Facets in scene generation

Use techniques and effects in architecture, interior and decor images. A **focal asset** is the preferred form for architecture and interiors: an asset whose cover shows the facet as the focal point ("Japandi Living Room · Shou Sugi Ban Wall"), selected from the style's linked facets that have markers for the domain, and weighted by facet demand. A focal asset acts as a variant of its style asset: it carries only the primary light condition and the furnished and empty forms, not every day, night and dusk combination. Facet edit variants on existing assets stay possible for small additions.

**Trigger:** facet demand exists for the facet (see Facet demand).

## Design elements and other AAT facets

Fill `design_elements` (motifs and ornament: acanthus, putti, meander, rocaille), `objects` (architectural and furniture elements: cladding, cassone, boiserie) and `agents` (makers and schools). Design elements let consumers control ornament in prompts directly, for example leaving out figurative motifs that image providers refuse.

**Trigger:** a consumer needs one of these facets as its own concept.

## Database

Move the dataset to data models and a database (Django) when the single JSON file becomes too large to edit and review: each facet section becomes a model, `relations` becomes a relation model (subject, predicate, object, sources), `vocab` becomes lookup tables, and slug ids stay the natural keys. The JSON file stays as the published export.

**Trigger:** the file passes about 10 MB, or editing needs concurrent contributors.
