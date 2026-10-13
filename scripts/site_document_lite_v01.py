"""Fail-closed SiteDocument v0.1 selection adapter for Designeo Lite.

Only selects already-approved pattern identifiers for an internal preview.
It does NOT render page content, translate tokens, import media, install, or publish.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.build_lite_core_library_v01 import ALLOWED, compose_variant

SCHEMA = "designeo.site-document.v0.1"
MAX_BYTES = 65536


def select_patterns(document: object) -> list[str]:
    if not isinstance(document, dict):
        raise ValueError("SiteDocument must be a JSON object")
    if set(document) != {"schema", "pages"} or document["schema"] != SCHEMA:
        raise ValueError("Unsupported schema or unexpected document fields")
    pages = document["pages"]
    if not isinstance(pages, list) or len(pages) != 1:
        raise ValueError("v0.1 supports exactly one page")
    page = pages[0]
    if not isinstance(page, dict) or set(page) != {"slug", "sections"}:
        raise ValueError("Invalid page fields")
    if page["slug"] != "home":
        raise ValueError("v0.1 supports only home")
    sections = page["sections"]
    if not isinstance(sections, list) or not 1 <= len(sections) <= len(ALLOWED):
        raise ValueError("Invalid sections")
    result = []
    for section in sections:
        if not isinstance(section, dict) or set(section) != {"pattern"}:
            raise ValueError("Each section must select one pattern only")
        pattern = section["pattern"]
        if not isinstance(pattern, str) or pattern not in ALLOWED:
            raise ValueError("Pattern not allowlisted")
        if pattern in result:
            raise ValueError("Duplicate pattern")
        result.append(pattern)
    return result


def load_document(path: Path) -> dict:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("SiteDocument exceeds maximum size")
    data = json.loads(path.read_text(encoding="utf-8"))
    select_patterns(data)
    return data


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--document", type=Path, required=True)
    p.add_argument("--core", type=Path, required=True)
    p.add_argument("--library", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    selected = select_patterns(load_document(args.document))
    report = compose_variant(args.core, args.library, selected, args.output)
    report["site_document_schema"] = SCHEMA
    report["site_document_rendered"] = False
    report["wordpress_runtime_tested"] = False
    report["publish_ready"] = False
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
