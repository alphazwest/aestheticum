"""Validate aestheticum.json against the dataset contract.

Structure is checked against schema/aestheticum.schema.json. Rules that span entries and facets
(unique ids and names, vocabularies, parent references, relation predicates and targets) are
checked here. A source list whose only source is one tier 2 source is reported as a warning.

Usage: uv run python validate.py [path]
"""

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "aestheticum.json"
SCHEMA_PATH = ROOT / "schema" / "aestheticum.schema.json"

type Doc = dict[str, Any]

TIER_RULE = "needs at least one tier 1 or tier 2 source"


@dataclass(frozen=True)
class Report:
    """
    A validation result.

    Args:
        errors: Contract violations; any error fails the dataset.
        warnings: Source lists flagged for review; computed only for a schema-valid document.
        checked_warnings: False when schema errors stopped the warning check.
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_warnings: bool = True


def validate(doc: Any) -> Report:
    """
    Validate a document: the schema first, then, for a schema-valid document, the rules across
    entries and facets and the source-tier warnings.

    Args:
        doc: The parsed data file.

    Returns:
        The errors and the warnings.
    """
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = _schema_errors(doc, schema)
    if errors:
        return Report(errors=errors, checked_warnings=False)
    return Report(errors=_rule_errors(doc), warnings=_source_warnings(doc))


def _alias_key(s: str) -> str:
    """
    Comparison key: no diacritics, case-folded, punctuation and qualifiers removed. A name with no
    Latin letters or digits keeps its case-folded form, so names in other scripts stay distinct.
    """
    s = re.sub(r"\s*\([^)]*\)", "", s)
    ascii_form = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    key = re.sub(r"[^a-z0-9]+", " ", ascii_form.casefold()).strip()
    return key or re.sub(r"\s+", " ", s.casefold()).strip()


def _where(facet: str, entry_id: str) -> str:
    """The `facet/id` prefix of an entry's messages."""
    return f"{facet}/{entry_id}"


def _iter_entries(doc: Doc) -> Iterator[tuple[str, Doc]]:
    """Every entry with its facet, in facet order."""
    for facet in doc["vocab"]["facets"]:
        for entry in doc[facet]:
            yield facet, entry


# Schema


def _declared_fields(schema: Doc) -> dict[str, frozenset[str]]:
    """Each facet section's entry fields: its item definition's properties and its bases'."""

    def collect(node: Doc) -> set[str]:
        if "$ref" in node:
            return collect(schema["$defs"][node["$ref"].rsplit("/", 1)[1]])
        names = set(node.get("properties", {}))
        for part in node.get("allOf", []):
            names |= collect(part)
        return names

    return {
        facet: frozenset(collect(prop["items"]))
        for facet, prop in schema["properties"].items()
        if "items" in prop
    }


def _path(doc: Any, path: list[Any]) -> str:
    """An error path; an entry's array index is replaced by its id (`facet/id/...`)."""
    parts = list(path)
    if len(parts) >= 2 and isinstance(parts[1], int) and isinstance(doc, dict):
        section = doc.get(parts[0])
        if isinstance(section, list) and parts[1] < len(section):
            entry = section[parts[1]]
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                parts[1] = entry["id"]
    return "/".join(map(str, parts)) or "<root>"


def _schema_errors(doc: Any, schema: Doc) -> list[str]:
    """
    Schema errors, one line each.

    An `unevaluatedProperties` error is reported by the fields the entry definition does not
    declare. When every listed field is declared, the error is a side effect of a failed nested
    rule (it makes every field count as unevaluated) and is left out; the nested error is the cause.
    A source list without a tier 1 or tier 2 source gets the tier rule as its message.
    """
    declared = _declared_fields(schema)
    found = sorted(
        Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(map(str, e.path))
    )
    lines: list[str] = []
    for e in found:
        path = list(e.absolute_path)
        where = _path(doc, path)
        if e.validator == "unevaluatedProperties":
            unknown = sorted(set(e.instance) - declared.get(path[0] if path else "", frozenset()))
            if unknown:
                lines.append(f"{where}: unknown fields {unknown}")
        elif e.validator == "contains" and path and path[-1] == "sources":
            lines.append(f"{where}: {TIER_RULE}")
        else:
            lines.append(f"{where}: {e.message}")
    return lines


# Rules


def _rule_errors(doc: Doc) -> list[str]:
    entries = list(_iter_entries(doc))
    facet_of: dict[str, list[str]] = defaultdict(list)
    for facet, e in entries:
        facet_of[e["id"]].append(facet)
    relations = doc["vocab"]["relations"]
    return [
        *_uniqueness_errors(doc, entries, facet_of),
        *_vocabulary_errors(doc["vocab"], entries),
        *(err for facet, e in entries for err in _relation_errors(facet, e, relations, facet_of)),
        *_parent_errors(doc["styles"]),
    ]


def _uniqueness_errors(
    doc: Doc, entries: list[tuple[str, Doc]], facet_of: dict[str, list[str]]
) -> list[str]:
    """Ids across facets, names within a facet, variant names and aliases across the file."""
    errors: list[str] = []
    for eid, facets in facet_of.items():
        if len(facets) > 1:
            places = " and ".join(dict.fromkeys(facets))
            twice = " (twice)" if len(set(facets)) == 1 else ""
            errors.append(f"duplicate id {eid!r} in {places}{twice}")

    for facet in doc["vocab"]["facets"]:
        by_name: dict[str, list[str]] = defaultdict(list)
        for e in doc[facet]:
            by_name[e["name"].casefold()].append(_where(facet, e["id"]))
        errors.extend(
            f"duplicate name {n!r}: {', '.join(w)}" for n, w in by_name.items() if len(w) > 1
        )

    entry_names = {e["name"].casefold(): _where(f, e["id"]) for f, e in entries}
    variants: dict[str, list[str]] = defaultdict(list)
    for facet, e in entries:
        for v in e.get("variants", []):
            variants[v["name"].casefold()].append(_where(facet, e["id"]))
    errors.extend(
        f"duplicate variant name {n!r}: {', '.join(w)}" for n, w in variants.items() if len(w) > 1
    )
    errors.extend(
        f"{w[0]}: variant name {n!r} is also the name of {entry_names[n]}"
        for n, w in variants.items()
        if n in entry_names
    )

    aliases: dict[str, list[str]] = defaultdict(list)
    for facet, e in entries:
        for a in e.get("aliases", []):
            aliases[_alias_key(a["name"])].append(_where(facet, e["id"]))
    errors.extend(
        f"duplicate alias {k!r}: {', '.join(w)}" for k, w in aliases.items() if len(w) > 1
    )
    name_keys = {_alias_key(n) for n in [*entry_names, *variants]}
    errors.extend(
        f"{aliases[k][0]}: alias {k!r} equals an entry or variant name"
        for k in sorted(set(aliases) & name_keys)
    )
    return errors


def _vocabulary_errors(vocab: Doc, entries: list[tuple[str, Doc]]) -> list[str]:
    """Tags, alias and id systems, domains and media from the vocabularies."""
    errors: list[str] = []
    tags = {t for group in vocab["tags"].values() for t in group}
    systems = set(vocab["alias_sources"])
    for facet, e in entries:
        where = _where(facet, e["id"])
        errors.extend(f"{where}: unknown tag {t!r}" for t in e["tags"] if t not in tags)
        errors.extend(
            f"{where}: unknown alias source {src['source']!r}"
            for a in e.get("aliases", [])
            for src in a["sources"]
            if src["source"] not in systems
        )
        errors.extend(
            f"{where}: unknown id system {k!r}" for k in e.get("ids", {}) if k not in systems
        )
        errors.extend(_domain_errors(where, e.get("domains", {}), vocab["domains"]))
        errors.extend(
            f"{where}: variant {v['name']!r} domain {k!r} not in entry"
            for v in e.get("variants", [])
            for k in v.get("domains", [])
            if k not in e.get("domains", {})
        )
    return errors


def _domain_errors(where: str, expressions: Doc, domains: Doc) -> list[str]:
    errors: list[str] = []
    for key, expr in expressions.items():
        if key not in domains:
            errors.append(f"{where}: unknown domain {key!r}")
            continue
        allowed = set(domains[key]["media"])
        media = expr.get("media", [])
        errors.extend(f"{where}/{key}: unknown media {m!r}" for m in media if m not in allowed)
        errors.extend(
            f"{where}/{key}: media_markers for unlisted media {m!r}"
            for m in expr.get("media_markers", {})
            if m not in media
        )
    return errors


def _relation_errors(
    facet: str, entry: Doc, relations: Doc, facet_of: dict[str, list[str]]
) -> list[str]:
    """Predicates belong to the entry's facet; each target exists, once, in the target facet."""
    where = _where(facet, entry["id"])
    errors: list[str] = []
    predicates = relations.get(facet, {})
    for predicate, targets in entry.get("relations", {}).items():
        if predicate not in predicates:
            owners = sorted(f for f, preds in relations.items() if predicate in preds)
            hint = f" (a predicate of {', '.join(owners)})" if owners else ""
            errors.append(f"{where}: unknown predicate {predicate!r} for {facet}{hint}")
            continue
        to = predicates[predicate]["to"]
        ids = [t["id"] for t in targets]
        errors.extend(
            f"{where}: {predicate} lists {i!r} twice" for i, c in Counter(ids).items() if c > 1
        )
        for i in dict.fromkeys(ids):
            found = facet_of.get(i)
            if not found:
                errors.append(f"{where}: {predicate} target {i!r} does not exist")
            elif to not in found:
                errors.append(f"{where}: {predicate} target {i!r} is in {found[0]}, not {to}")
    return errors


def _parent_errors(styles: list[Doc]) -> list[str]:
    """Style parents exist; a style is not its own parent; no parent chain loops."""
    errors: list[str] = []
    parents = {s["id"]: s["parent"] for s in styles}
    for sid, parent in parents.items():
        if parent == sid:
            errors.append(f"{_where('styles', sid)}: self parent")
        elif parent is not None and parent not in parents:
            errors.append(f"{_where('styles', sid)}: unknown parent {parent!r}")
    for sid, parent in parents.items():
        if parent == sid:
            continue
        seen: set[str] = set()
        cur: str | None = sid
        while cur is not None:
            if cur in seen:
                errors.append(f"{_where('styles', sid)}: parent cycle")
                break
            seen.add(cur)
            cur = parents.get(cur)
    return errors


# Warnings


def _source_lists(where: str, e: Doc) -> Iterator[tuple[str, list[Doc]]]:
    """
    Every source list of an entry, with its location: the uses of `$defs/source_list` in the
    schema (the entry, its domain expressions, its variants and its relation targets).
    """
    yield where, e["sources"]
    for k, expr in e.get("domains", {}).items():
        if "sources" in expr:
            yield f"{where}/{k}", expr["sources"]
    for v in e.get("variants", []):
        yield f"{where}/variant {v['name']!r}", v["sources"]
    for predicate, targets in e.get("relations", {}).items():
        for t in targets:
            if "sources" in t:
                yield f"{where}/{predicate} {t['id']!r}", t["sources"]


def _source_warnings(doc: Doc) -> list[str]:
    """Source lists whose only source is one tier 2 source (flagged for review)."""
    return [
        f"{where}: one tier 2 source only"
        for facet, e in _iter_entries(doc)
        for where, sources in _source_lists(_where(facet, e["id"]), e)
        if [s["tier"] for s in sources] == [2]
    ]


# Command line


def _safe(line: str) -> str:
    """A printable line: control characters escaped, so data never starts a new output line."""
    return "".join(c if c.isprintable() else c.encode("unicode_escape").decode() for c in line)


def _summary(doc: Any, report: Report) -> str:
    """Entries per facet, the error count and the warning count."""
    vocab = doc.get("vocab") if isinstance(doc, dict) else None
    facets = vocab.get("facets") if isinstance(vocab, dict) else None
    if isinstance(facets, dict):
        counts = ", ".join(
            f"{len(doc[f]) if isinstance(doc.get(f), list) else 0} {f}" for f in facets
        )
    else:
        counts = "no facets"
    warnings = (
        f"{len(report.warnings)} warnings" if report.checked_warnings else "warnings not checked"
    )
    return f"{counts}; {len(report.errors)} errors, {warnings}"


def main(argv: list[str]) -> int:
    path = Path(argv[0]) if argv else DATA_PATH
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(_safe(f"error: {path}: {e}"))
        return 1
    report = validate(doc)
    for e in report.errors:
        print(_safe(f"error: {e}"))
    for w in report.warnings:
        print(_safe(f"warning: {w}"))
    print(_safe(_summary(doc, report)))
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
