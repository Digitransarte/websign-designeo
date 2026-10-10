"""Compose a Designeo Lite authoring preview from one Core and selected patterns.

Example:
python -m scripts.compose_lite_preview_v01 --core lite-core.zip \
    --library lite-pattern-library.zip --pattern hero --pattern cta \
    --output preview.zip

This tool does not publish websites or approve incomplete placeholder content.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.build_lite_core_library_v01 import ALLOWED, compose_variant


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--pattern", choices=ALLOWED, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compose_variant(args.core, args.library, args.pattern, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
