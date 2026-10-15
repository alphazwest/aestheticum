"""Validate design-styles.json against the dataset contract.

Structure is checked against schema/design-styles.schema.json. Rules that span
entries (unique ids, tag and domain vocabularies, parent references) are checked here.

Usage: uv run python validate_styles.py [path]
"""

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "design-styles.json"
SCHEMA_PATH = ROOT / "schema" / "design-styles.schema.json"

type Doc = dict[str, Any]


def alias_key(s: str) -> str:
    """Comparison key: no diacritics, case-folded, punctuation and qualifiers removed."""
    s = re.sub(r"\s*\([^)]*\)", "", s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.casefold()).strip()


def load_schema() -> Doc:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_errors(doc: Doc, schema: Doc | None = None) -> list[str]:
    validator = Draft202012Validator(schema or load_schema())
    return [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(doc), key=lambda e: list(map(str, e.path)))
    ]


def rule_errors(doc: Doc) -> list[str]:
    errors: list[str] = []
    styles = doc["styles"]
    vocab = {tag for group in doc["tags"].values() for tag in group}
    ids = [s["id"] for s in styles]
    names = [s["name"].casefold() for s in styles]

    if len(ids) != len(set(ids)):
        errors.append("duplicate ids")
    if len(names) != len(set(names)):
        errors.append("duplicate names")
    variant_names = [v["name"].casefold() for s in styles for v in s.get("variants", [])]
    alias_keys = [alias_key(a["name"]) for s in styles for a in s.get("aliases", [])]
    name_keys = {alias_key(n) for n in names + variant_names}
    if len(alias_keys) != len(set(alias_keys)):
        errors.append("duplicate aliases")
    errors.extend(
        f"alias {a!r} equals an entry or variant name" for a in sorted(set(alias_keys) & name_keys)
    )
    if len(variant_names) != len(set(variant_names)):
        errors.append("duplicate variant names")
    errors.extend(
        f"variant name {n!r} is also an entry name" for n in set(variant_names) & set(names)
    )
    systems = set(doc["alias_sources"])
    for s in styles:
        errors.extend(
            f"{s['id']}: unknown alias source {src['source']!r}"
            for a in s.get("aliases", [])
            for src in a["sources"]
            if src["source"] not in systems
        )
        errors.extend(
            f"{s['id']}: unknown id system {k!r}" for k in s.get("ids", {}) if k not in systems
        )

    id_set = set(ids)
    for s in styles:
        sid = s["id"]
        errors.extend(f"{sid}: unknown tag {t!r}" for t in s["tags"] if t not in vocab)
        if s["parent"] is not None and s["parent"] not in id_set:
            errors.append(f"{sid}: unknown parent {s['parent']!r}")
        if s["parent"] == sid:
            errors.append(f"{sid}: self parent")
        errors.extend(domain_errors(sid, s["domains"], doc["domains"]))
        for v in s.get("variants", []):
            errors.extend(
                f"{sid}: variant {v['name']!r} domain {k!r} not in entry"
                for k in v.get("domains", [])
                if k not in s["domains"]
            )

    parents = {s["id"]: s["parent"] for s in styles}
    for sid in ids:
        seen: set[str] = set()
        cur: str | None = sid
        while cur is not None:
            if cur in seen:
                errors.append(f"{sid}: parent cycle")
                break
            seen.add(cur)
            cur = parents.get(cur)
    return errors


def domain_errors(sid: str, expressions: Doc, domains: Doc) -> list[str]:
    errors: list[str] = []
    for key, expr in expressions.items():
        if key not in domains:
            errors.append(f"{sid}: unknown domain {key!r}")
            continue
        allowed = set(domains[key]["media"])
        media = expr.get("media", [])
        errors.extend(f"{sid}/{key}: unknown media {m!r}" for m in media if m not in allowed)
        errors.extend(
            f"{sid}/{key}: media_markers for unlisted media {m!r}"
            for m in expr.get("media_markers", {})
            if m not in media
        )
    return errors


def validate(doc: Doc, schema: Doc | None = None) -> list[str]:
    # Rule checks assume a structurally valid document.
    return schema_errors(doc, schema) or rule_errors(doc)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_PATH
    doc = json.loads(path.read_text(encoding="utf-8"))
    errors = validate(doc)
    for e in errors:
        print(e)
    print(f"{len(doc.get('styles', []))} styles, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
