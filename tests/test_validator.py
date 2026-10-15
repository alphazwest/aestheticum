import copy
import json
from collections.abc import Callable
from typing import Any

import pytest

from validate_styles import DATA_PATH, validate

type Doc = dict[str, Any]


@pytest.fixture(scope="session")
def dataset() -> Doc:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def minimal() -> Doc:
    source = {"title": "T", "publisher": "P", "url": "https://example.org/a", "tier": 1}
    return {
        "schema_version": 2,
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
            "aat": {"name": "AAT", "url": "https://vocab.getty.edu/page/aat/{ref}", "space": "_"},
            "wikidata": {
                "name": "Wikidata",
                "url": "https://www.wikidata.org/wiki/{ref}",
                "space": "_",
            },
        },
        "tags": {"era": ["historical", "modern"]},
        "styles": [
            {
                "id": "base",
                "name": "Base",
                "parent": None,
                "description": "A base style.",
                "tags": ["historical"],
                "sources": [source],
                "domains": {"interior": {}},
            },
            {
                "id": "child",
                "name": "Child",
                "parent": "base",
                "description": "A child style.",
                "tags": ["modern"],
                "sources": [source],
                "variants": [
                    {
                        "name": "Child Variant",
                        "description": "A narrower look.",
                        "markers": "spindle backs",
                        "domains": ["furniture"],
                        "sources": [source],
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
    }


def test_dataset_is_valid(dataset: Doc) -> None:
    assert validate(dataset) == []


def test_minimal_is_valid(minimal: Doc) -> None:
    assert validate(minimal) == []


def _style(doc: Doc, i: int = 1) -> Doc:
    return doc["styles"][i]


MUTATIONS: dict[str, Callable[[Doc], None]] = {
    "duplicate id": lambda d: _style(d).update(id="base"),
    "duplicate name": lambda d: _style(d).update(name="BASE"),
    "unknown tag": lambda d: _style(d).update(tags=["rustic"]),
    "unknown parent": lambda d: _style(d).update(parent="missing"),
    "self parent": lambda d: _style(d).update(parent="child"),
    "parent cycle": lambda d: _style(d, 0).update(parent="child"),
    "long description": lambda d: _style(d).update(description="x" * 257),
    "too many tags": lambda d: _style(d).update(tags=["a", "b", "c", "d", "e", "f"]),
    "duplicate tags": lambda d: _style(d).update(tags=["modern", "modern"]),
    "no sources": lambda d: _style(d).update(sources=[]),
    "too many sources": lambda d: _style(d).update(sources=_style(d)["sources"] * 5),
    "http url": lambda d: _style(d)["sources"][0].update(url="http://example.org"),
    "bad tier": lambda d: _style(d)["sources"][0].update(tier=4),
    "only tier 3 sources": lambda d: _style(d)["sources"][0].update(tier=3),
    "domain expression only tier 3": lambda d: _style(d)["domains"]["furniture"].update(
        sources=[
            {"title": "W", "publisher": "Wikipedia", "url": "https://en.wikipedia.org/x", "tier": 3}
        ]
    ),
    "bad slug": lambda d: _style(d).update(id="Not A Slug"),
    "unknown field": lambda d: _style(d).update(extra=True),
    "missing field": lambda d: _style(d).pop("description"),
    "no domains": lambda d: _style(d).update(domains={}),
    "missing domains": lambda d: _style(d).pop("domains"),
    "unknown domain": lambda d: _style(d).update(domains={"fashion": {}}),
    "unknown media": lambda d: _style(d)["domains"]["furniture"].update(media=["beds"]),
    "media on domain without media": lambda d: _style(d, 0)["domains"].update(
        interior={"media": ["seating"]}
    ),
    "media_markers for unlisted media": lambda d: _style(d)["domains"]["furniture"].update(
        media_markers={"tables": "x"}
    ),
    "empty markers": lambda d: _style(d)["domains"]["furniture"].update(markers=""),
    "bad aat id": lambda d: d["domains"]["interior"].update(aat="12345"),
    "domain missing media list": lambda d: d["domains"]["interior"].pop("media"),
    "old schema version": lambda d: d.update(schema_version=1),
    "variant name equals entry name": lambda d: _style(d)["variants"][0].update(name="Base"),
    "duplicate variant names": lambda d: _style(d)["variants"].append(
        dict(_style(d)["variants"][0])
    ),
    "variant domain not in entry": lambda d: _style(d)["variants"][0].update(domains=["interior"]),
    "variant without sources": lambda d: _style(d)["variants"][0].update(sources=[]),
    "variant long markers": lambda d: _style(d)["variants"][0].update(markers="x" * 201),
    "duplicate aliases": lambda d: (
        _style(d, 0).update(
            aliases=[{"name": "Same", "sources": [{"source": "aat", "ref": "300000001"}]}]
        ),
        _style(d).update(
            aliases=[{"name": "same", "sources": [{"source": "wikidata", "ref": "Q1"}]}]
        ),
    ),
    "alias equals entry name": lambda d: _style(d).update(
        aliases=[{"name": "Base", "sources": [{"source": "wikidata", "ref": "Q1"}]}]
    ),
    "alias source as a plain string": lambda d: _style(d).update(
        aliases=[{"name": "X", "sources": ["Q1"]}]
    ),
    "alias source from an unknown system": lambda d: _style(d).update(
        aliases=[{"name": "X", "sources": [{"source": "pinterest", "ref": "x"}]}]
    ),
    "bad wikidata id": lambda d: _style(d).update(ids={"wikidata": "1234"}),
    "missing alias_sources": lambda d: d.pop("alias_sources"),
    "popularity score out of range": lambda d: _style(d).update(
        popularity={"score": 1.0, "design_demand": None}
    ),
    "popularity missing design_demand": lambda d: _style(d).update(popularity={"score": 0.5}),
    "alias source url without placeholder": lambda d: d["alias_sources"]["aat"].update(
        url="https://vocab.getty.edu/page/aat/"
    ),
}


@pytest.mark.parametrize("mutate", MUTATIONS.values(), ids=MUTATIONS.keys())
def test_validator_rejects(minimal: Doc, mutate: Callable[[Doc], None]) -> None:
    doc = copy.deepcopy(minimal)
    mutate(doc)
    assert validate(doc)
