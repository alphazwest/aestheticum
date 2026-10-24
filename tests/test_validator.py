import copy
import json
import re
from collections.abc import Callable
from pathlib import Path

import pytest

from validate import DATA_PATH, Doc, main, validate


@pytest.fixture(scope="session")
def dataset() -> Doc:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


SOURCE = {"title": "T", "publisher": "P", "url": "https://example.org/a", "tier": 1}
EMPTY_FACETS = ("materials", "design_elements", "objects", "agents")


@pytest.fixture
def minimal() -> Doc:
    facets = {
        f: {"name": f.title(), "description": f"The {f}.", "aat": None}
        for f in ("styles", "techniques", "effects", *EMPTY_FACETS)
    }
    return {
        "schema_version": 3,
        "vocab": {
            "facets": facets,
            "relations": {
                "techniques": {
                    "associated_styles": {
                        "to": "styles",
                        "inverse": "techniques",
                        "description": "Characteristic of.",
                    },
                    "produces": {
                        "to": "effects",
                        "inverse": "produced_by",
                        "description": "Gives.",
                    },
                },
                "effects": {
                    "associated_styles": {
                        "to": "styles",
                        "inverse": "effects",
                        "description": "Characteristic of.",
                    }
                },
            },
            "source_tiers": {"1": "Authoritative."},
            "domains": {
                "interior": {"name": "Interior", "description": "Rooms.", "aat": None, "media": []},
                "furniture": {
                    "name": "Furniture",
                    "description": "Furnishings.",
                    "aat": "300435227",
                    "media": ["seating", "tables"],
                },
            },
            "alias_sources": {
                "aat": {
                    "name": "AAT",
                    "url": "https://vocab.getty.edu/page/aat/{ref}",
                    "space": "_",
                },
                "wikidata": {
                    "name": "Wikidata",
                    "url": "https://www.wikidata.org/wiki/{ref}",
                    "space": "_",
                },
            },
            "tags": {"era": ["historical", "modern"], "palette": ["dark"]},
        },
        "styles": [
            {
                "id": "base",
                "name": "Base",
                "parent": None,
                "description": "A base style.",
                "tags": ["historical"],
                "sources": [SOURCE],
                "domains": {"interior": {}},
            },
            {
                "id": "child",
                "name": "Child",
                "parent": "base",
                "description": "A child style.",
                "tags": ["modern"],
                "sources": [SOURCE],
                "variants": [
                    {
                        "name": "Child Variant",
                        "description": "A narrower look.",
                        "markers": "spindle backs",
                        "domains": ["furniture"],
                        "sources": [SOURCE],
                    }
                ],
                "domains": {
                    "furniture": {
                        "media": ["seating"],
                        "markers": "turned legs",
                        "media_markers": {"seating": "spindle backs"},
                    }
                },
            },
        ],
        "techniques": [
            {
                "id": "charring",
                "name": "Charring",
                "description": "Burning the surface of wood.",
                "tags": ["dark"],
                "sources": [SOURCE],
                "markers": "charred, brushed, oiled",
                "domains": {"interior": {"markers": "charred-board walls"}},
                "relations": {
                    "associated_styles": [{"id": "base", "sources": [SOURCE]}],
                    "produces": [{"id": "charred"}],
                },
                "variants": [
                    {
                        "name": "Unbrushed",
                        "description": "Heavy soot.",
                        "markers": "alligator char",
                        "sources": [SOURCE],
                    }
                ],
            }
        ],
        "effects": [
            {
                "id": "charred",
                "name": "Charred",
                "description": "A blackened, carbonized surface.",
                "tags": ["dark"],
                "sources": [SOURCE],
                "markers": "blackened surface",
                "relations": {"associated_styles": [{"id": "child"}]},
            }
        ],
    } | {f: [] for f in EMPTY_FACETS}


def test_dataset_is_valid(dataset: Doc) -> None:
    assert validate(dataset).errors == []


def test_minimal_is_valid(minimal: Doc) -> None:
    report = validate(minimal)
    assert (report.errors, report.warnings) == ([], [])


def _style(doc: Doc, i: int = 1) -> Doc:
    return doc["styles"][i]


def _technique(doc: Doc) -> Doc:
    return doc["techniques"][0]


TIER_3 = {"title": "W", "publisher": "Wikipedia", "url": "https://en.wikipedia.org/x", "tier": 3}

# Each mutation and a fragment of the error it must produce.
MUTATIONS: dict[str, tuple[Callable[[Doc], None], str]] = {
    "duplicate id": (
        lambda d: d["styles"].append({**_style(d, 0), "name": "Other"}),
        "duplicate id 'base' in styles (twice)",
    ),
    "duplicate name": (
        lambda d: _style(d).update(name="BASE"),
        "duplicate name 'base': styles/base, styles/child",
    ),
    "unknown tag": (
        lambda d: _style(d).update(tags=["rustic"]),
        "styles/child: unknown tag 'rustic'",
    ),
    "unknown parent": (
        lambda d: _style(d).update(parent="missing"),
        "styles/child: unknown parent 'missing'",
    ),
    "self parent": (lambda d: _style(d).update(parent="child"), "styles/child: self parent"),
    "parent cycle": (lambda d: _style(d, 0).update(parent="child"), "styles/base: parent cycle"),
    "long description": (
        lambda d: _style(d).update(description="x" * 257),
        "styles/child/description",
    ),
    "too many tags": (
        lambda d: _style(d).update(tags=["a", "b", "c", "d", "e", "f"]),
        "styles/child/tags",
    ),
    "duplicate tags": (
        lambda d: _style(d).update(tags=["modern", "modern"]),
        "non-unique elements",
    ),
    "no sources": (lambda d: _style(d).update(sources=[]), "styles/child/sources"),
    "too many sources": (
        lambda d: _style(d).update(sources=_style(d)["sources"] * 5),
        "is too long",
    ),
    "http url": (
        lambda d: _style(d)["sources"][0].update(url="http://example.org"),
        "does not match",
    ),
    "bad tier": (lambda d: _style(d)["sources"][0].update(tier=4), "styles/child/sources/0/tier"),
    "only tier 3 sources": (
        lambda d: _style(d).update(sources=[TIER_3]),
        "styles/child/sources: needs at least one tier 1 or tier 2 source",
    ),
    "domain expression only tier 3": (
        lambda d: _style(d)["domains"]["furniture"].update(sources=[TIER_3]),
        "styles/child/domains/furniture/sources: needs at least one tier 1 or tier 2 source",
    ),
    "variant only tier 3": (
        lambda d: _style(d)["variants"][0].update(sources=[TIER_3]),
        "styles/child/variants/0/sources: needs at least one tier 1 or tier 2 source",
    ),
    "relation target only tier 3": (
        lambda d: _technique(d)["relations"]["associated_styles"][0].update(sources=[TIER_3]),
        "techniques/charring/relations/associated_styles/0/sources: needs at least one tier 1",
    ),
    "bad slug": (lambda d: _style(d).update(id="Not A Slug"), "does not match"),
    "unknown field": (
        lambda d: _style(d).update(extra=True),
        "styles/child: unknown fields ['extra']",
    ),
    "missing field": (
        lambda d: _style(d).pop("description"),
        "'description' is a required property",
    ),
    "no domains": (lambda d: _style(d).update(domains={}), "styles/child/domains"),
    "missing domains": (lambda d: _style(d).pop("domains"), "'domains' is a required property"),
    "unknown domain": (
        lambda d: _style(d).update(domains={"fashion": {}}),
        "styles/child: unknown domain 'fashion'",
    ),
    "unknown media": (
        lambda d: _style(d)["domains"]["furniture"].update(media=["beds"]),
        "styles/child/furniture: unknown media 'beds'",
    ),
    "media on domain without media": (
        lambda d: _style(d, 0)["domains"].update(interior={"media": ["seating"]}),
        "styles/base/interior: unknown media 'seating'",
    ),
    "media_markers for unlisted media": (
        lambda d: _style(d)["domains"]["furniture"].update(media_markers={"tables": "x"}),
        "media_markers for unlisted media 'tables'",
    ),
    "empty markers": (
        lambda d: _style(d)["domains"]["furniture"].update(markers=""),
        "should be non-empty",
    ),
    "bad aat id": (
        lambda d: d["vocab"]["domains"]["interior"].update(aat="12345"),
        "vocab/domains/interior/aat",
    ),
    "domain missing media list": (
        lambda d: d["vocab"]["domains"]["interior"].pop("media"),
        "'media' is a required property",
    ),
    "old schema version": (lambda d: d.update(schema_version=2), "schema_version: 3 was expected"),
    "variant name equals entry name": (
        lambda d: _style(d)["variants"][0].update(name="Base"),
        "styles/child: variant name 'base' is also the name of styles/base",
    ),
    "duplicate variant names": (
        lambda d: _style(d)["variants"].append(dict(_style(d)["variants"][0])),
        "duplicate variant name 'child variant': styles/child, styles/child",
    ),
    "variant domain not in entry": (
        lambda d: _style(d)["variants"][0].update(domains=["interior"]),
        "styles/child: variant 'Child Variant' domain 'interior' not in entry",
    ),
    "variant without sources": (
        lambda d: _style(d)["variants"][0].update(sources=[]),
        "variants/0/sources",
    ),
    "variant long markers": (
        lambda d: _style(d)["variants"][0].update(markers="x" * 201),
        "is too long",
    ),
    "duplicate aliases": (
        lambda d: (
            _style(d, 0).update(
                aliases=[{"name": "Same", "sources": [{"source": "aat", "ref": "300000001"}]}]
            ),
            _style(d).update(
                aliases=[{"name": "same", "sources": [{"source": "wikidata", "ref": "Q1"}]}]
            ),
        ),
        "duplicate alias 'same': styles/base, styles/child",
    ),
    "alias equals entry name": (
        lambda d: _style(d).update(
            aliases=[{"name": "Base", "sources": [{"source": "wikidata", "ref": "Q1"}]}]
        ),
        "styles/child: alias 'base' equals an entry or variant name",
    ),
    "alias source as a plain string": (
        lambda d: _style(d).update(aliases=[{"name": "X", "sources": ["Q1"]}]),
        "styles/child/aliases/0/sources/0",
    ),
    "alias source from an unknown system": (
        lambda d: _style(d).update(
            aliases=[{"name": "X", "sources": [{"source": "pinterest", "ref": "x"}]}]
        ),
        "styles/child: unknown alias source 'pinterest'",
    ),
    "unknown id system": (
        lambda d: (
            d["vocab"]["alias_sources"].pop("wikidata") and _style(d).update(ids={"wikidata": "Q1"})
        ),
        "styles/child: unknown id system 'wikidata'",
    ),
    "bad wikidata id": (
        lambda d: _style(d).update(ids={"wikidata": "1234"}),
        "styles/child/ids/wikidata",
    ),
    "missing alias_sources": (
        lambda d: d["vocab"].pop("alias_sources"),
        "'alias_sources' is a required property",
    ),
    "popularity score out of range": (
        lambda d: _style(d).update(popularity={"score": 1.0, "design_demand": None}),
        "styles/child/popularity/score",
    ),
    "popularity missing design_demand": (
        lambda d: _style(d).update(popularity={"score": 0.5}),
        "'design_demand' is a required property",
    ),
    "alias source url without placeholder": (
        lambda d: d["vocab"]["alias_sources"]["aat"].update(
            url="https://vocab.getty.edu/page/aat/"
        ),
        "vocab/alias_sources/aat/url",
    ),
    "same id in two facets": (
        lambda d: _technique(d).update(id="charred"),
        "duplicate id 'charred' in techniques and effects",
    ),
    "duplicate name in a facet": (
        lambda d: d["effects"].append({**d["effects"][0], "id": "charred-2"}),
        "duplicate name 'charred': effects/charred, effects/charred-2",
    ),
    "variant name equals a technique name": (
        lambda d: _style(d)["variants"][0].update(name="Charring"),
        "styles/child: variant name 'charring' is also the name of techniques/charring",
    ),
    "technique without markers": (
        lambda d: _technique(d).pop("markers"),
        "techniques/charring: 'markers' is a required",
    ),
    "technique with a parent": (
        lambda d: _technique(d).update(parent=None),
        "techniques/charring: unknown fields ['parent']",
    ),
    "technique with popularity": (
        lambda d: _technique(d).update(popularity={"score": 0.5, "design_demand": None}),
        "techniques/charring: unknown fields ['popularity']",
    ),
    "technique with an unknown tag": (
        lambda d: _technique(d).update(tags=["rustic"]),
        "techniques/charring: unknown tag 'rustic'",
    ),
    "technique with an unknown domain": (
        lambda d: _technique(d).update(domains={"fashion": {}}),
        "techniques/charring: unknown domain 'fashion'",
    ),
    "style with relations": (
        lambda d: _style(d).update(relations={"associated_styles": [{"id": "base"}]}),
        "styles/child: unknown fields ['relations']",
    ),
    "entry in an empty facet": (
        lambda d: d["materials"].append({"id": "wood"}),
        "materials: [{'id': 'wood'}] is expected to be empty",
    ),
    "facet missing from vocab": (
        lambda d: d["vocab"]["facets"].pop("agents"),
        "'agents' is a required property",
    ),
    "relations of an unknown facet": (
        lambda d: d["vocab"]["relations"].update(colors={}),
        "'colors' is not one of",
    ),
    "predicate to an unknown facet": (
        lambda d: d["vocab"]["relations"]["techniques"]["produces"].update(to="moods"),
        "vocab/relations/techniques/produces/to: 'moods' is not one of",
    ),
    "unknown predicate": (
        lambda d: _technique(d)["relations"].update(made_by=[{"id": "base"}]),
        "techniques/charring: unknown predicate 'made_by' for techniques",
    ),
    "predicate of another facet": (
        lambda d: d["effects"][0]["relations"].update(produces=[{"id": "charred"}]),
        "effects/charred: unknown predicate 'produces' for effects (a predicate of techniques)",
    ),
    "relation target does not exist": (
        lambda d: _technique(d)["relations"].update(produces=[{"id": "patina"}]),
        "techniques/charring: produces target 'patina' does not exist",
    ),
    "relation target in the wrong facet": (
        lambda d: _technique(d)["relations"].update(produces=[{"id": "base"}]),
        "techniques/charring: produces target 'base' is in styles, not effects",
    ),
    "relation target listed twice": (
        lambda d: _technique(d)["relations"].update(
            produces=[{"id": "charred"}, {"id": "charred"}]
        ),
        "techniques/charring: produces lists 'charred' twice",
    ),
    "empty relation": (
        lambda d: _technique(d)["relations"].update(produces=[]),
        "techniques/charring/relations/produces: [] should be non-empty",
    ),
}


@pytest.mark.parametrize(("mutate", "expected"), MUTATIONS.values(), ids=MUTATIONS.keys())
def test_validator_rejects(minimal: Doc, mutate: Callable[[Doc], None], expected: str) -> None:
    doc = copy.deepcopy(minimal)
    mutate(doc)
    errors = validate(doc).errors
    assert any(expected in e for e in errors), errors


def test_a_nested_schema_error_carries_no_unevaluated_noise(minimal: Doc) -> None:
    _technique(minimal)["relations"]["produces"] = []
    assert validate(minimal).errors == [
        "techniques/charring/relations/produces: [] should be non-empty"
    ]


def test_an_unknown_field_is_reported_beside_a_nested_error(minimal: Doc) -> None:
    _technique(minimal).update(colour="black", tags=["Not A Slug"])
    errors = validate(minimal).errors
    assert "techniques/charring: unknown fields ['colour']" in errors
    assert any(e.startswith("techniques/charring/tags/0") for e in errors), errors


def test_names_may_repeat_across_facets(minimal: Doc) -> None:
    _technique(minimal)["name"] = "Base"
    assert validate(minimal).errors == []


def test_aliases_in_other_scripts_stay_distinct(minimal: Doc) -> None:
    _technique(minimal)["aliases"] = [
        {"name": "焼杉", "sources": [{"source": "wikidata", "ref": "Q1"}]}
    ]
    minimal["effects"][0]["aliases"] = [
        {"name": "炭化", "sources": [{"source": "wikidata", "ref": "Q2"}]}
    ]
    assert validate(minimal).errors == []


TIER_2 = {**SOURCE, "tier": 2}
WARNED_PLACES: dict[str, tuple[Callable[[Doc], None], str]] = {
    "entry": (lambda d: _technique(d).update(sources=[TIER_2]), "techniques/charring"),
    "domain expression": (
        lambda d: _technique(d)["domains"]["interior"].update(sources=[TIER_2]),
        "techniques/charring/interior",
    ),
    "variant": (
        lambda d: _technique(d)["variants"][0].update(sources=[TIER_2]),
        "techniques/charring/variant 'Unbrushed'",
    ),
    "relation target": (
        lambda d: _technique(d)["relations"]["associated_styles"][0].update(sources=[TIER_2]),
        "techniques/charring/associated_styles 'base'",
    ),
}


@pytest.mark.parametrize(("mutate", "where"), WARNED_PLACES.values(), ids=WARNED_PLACES.keys())
def test_one_tier_2_source_is_a_warning(
    minimal: Doc, mutate: Callable[[Doc], None], where: str
) -> None:
    mutate(minimal)
    report = validate(minimal)
    assert report.errors == []
    assert report.warnings == [f"{where}: one tier 2 source only"]


@pytest.mark.parametrize(
    "sources",
    [[TIER_2, TIER_2], [TIER_2, SOURCE], [SOURCE]],
    ids=["two tier 2", "tier 2 and 1", "tier 1"],
)
def test_other_source_lists_raise_no_warning(minimal: Doc, sources: list[Doc]) -> None:
    _technique(minimal)["sources"] = sources
    assert validate(minimal).warnings == []


def test_warnings_are_reported_beside_rule_errors(minimal: Doc) -> None:
    _technique(minimal).update(sources=[TIER_2], tags=["rustic"])
    report = validate(minimal)
    assert report.errors == ["techniques/charring: unknown tag 'rustic'"]
    assert report.warnings == ["techniques/charring: one tier 2 source only"]


def _write(tmp_path: Path, doc: object) -> str:
    path = tmp_path / "aestheticum.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


def test_main_prints_the_summary_and_exits_0(
    minimal: Doc, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _technique(minimal)["sources"] = [TIER_2]
    assert main([_write(tmp_path, minimal)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "warning: techniques/charring: one tier 2 source only",
        "2 styles, 1 techniques, 1 effects, 0 materials, 0 design_elements, 0 objects, 0 agents; "
        "0 errors, 1 warnings",
    ]


def test_main_exits_1_on_an_error(
    minimal: Doc, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _style(minimal)["tags"] = ["rustic"]
    assert main([_write(tmp_path, minimal)]) == 1
    assert capsys.readouterr().out.splitlines()[0] == "error: styles/child: unknown tag 'rustic'"


@pytest.mark.parametrize(
    "doc", [[], {"vocab": 5}, {"vocab": {"facets": {"styles": {}}}, "styles": 5}]
)
def test_main_summarizes_any_document(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], doc: object
) -> None:
    assert main([_write(tmp_path, doc)]) == 1
    assert "errors, warnings not checked" in capsys.readouterr().out.splitlines()[-1]


def test_main_reports_an_unreadable_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(tmp_path / "missing.json")]) == 1
    assert capsys.readouterr().out.startswith("error: ")


def test_data_cannot_start_an_output_line(
    minimal: Doc, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    minimal["vocab"]["facets"]["x\n::error title=injected::"] = minimal["vocab"]["facets"]["styles"]
    main([_write(tmp_path, minimal)])
    lines = capsys.readouterr().out.splitlines()
    assert not any(line.startswith("::") for line in lines), lines


def test_the_readme_tables_match_the_vocabularies(dataset: Doc) -> None:
    readme = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    for fid, facet in dataset["vocab"]["facets"].items():
        assert re.search(rf"^\| `{fid}` \| {re.escape(facet['name'])} \|", readme, re.M), fid
    for owner, predicates in dataset["vocab"]["relations"].items():
        for name, p in predicates.items():
            row = f"| `{owner}` | `{name}` | `{p['to']}` | `{p['inverse']}` |"
            assert row in readme, row
