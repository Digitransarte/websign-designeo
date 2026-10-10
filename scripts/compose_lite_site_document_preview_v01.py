"""Offline CLI to select Lite patterns from *native validated* SiteDocument JSON.

The Websign VNext native validator is a required runtime dependency. In a
checkout where it is not yet versioned/installed, fail closed instead of
silently accepting a new or partially compatible document schema.

Never posts to WordPress; optional ZIP is an authoring preview only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.build_lite_core_library_v01 import LIBRARY_ROOT, _load, compose_variant
from scripts.plan_lite_patterns_from_site_document_v01 import plan_lite_patterns


def plan_and_optionally_compose(document: dict, core_zip: Path, library_zip: Path,
                                output_zip: Path | None, *, validator) -> dict:
    library = _load(library_zip)
    manifest_key = LIBRARY_ROOT + "manifest.json"
    if manifest_key not in library:
        raise ValueError("Not a Lite Pattern Library")
    manifest = json.loads(library[manifest_key].decode("utf-8"))
    plan = plan_lite_patterns(document, manifest, validate_site_document=validator)
    if output_zip is None:
        return {"plan": plan, "composition": None}
    result = compose_variant(core_zip, library_zip, plan["pattern_selection"], output_zip)
    return {"plan": plan, "composition": result}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-document", type=Path, required=True,
                        help="Local SiteDocument JSON — not uploaded anywhere")
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path,
                        help="Optional authoring preview ZIP; never published")
    args = parser.parse_args()
    try:
        from websign_vnext.validation import validate_site_document
    except ImportError as exc:
        raise SystemExit(
            "BLOCKED: actual Websign VNext validator is unavailable. "
            "Mount the authorized Websign development checkout and retry."
        ) from exc
    document = json.loads(args.site_document.read_text(encoding="utf-8"))
    result = plan_and_optionally_compose(
        document, args.core, args.library, args.output, validator=validate_site_document)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
