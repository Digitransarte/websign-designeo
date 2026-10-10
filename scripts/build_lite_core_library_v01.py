"""Split Designeo Lite into an installable Core and an authoring-only pattern library.

Inputs: immutable Designeo Lite source ZIPs and reviewed overlay from WEB-01.
Outputs: distinct, deterministic ZIP files in an isolated destination.

No WordPress or network operations. This does not certify a release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from scripts.build_lite_v201_token_aligned_candidate import build as build_normalized

ROOT = "designeo-lite-base/"
LIBRARY_ROOT = "designeo-lite-pattern-library/"
SCHEMA = "designeo.lite.library.v0.1"
ALLOWED = ("hero", "services", "about", "cta")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load(path: Path) -> dict[str, bytes]:
    with ZipFile(path, "r") as archive:
        if archive.testzip() is not None:
            raise ValueError(f"Corrupted ZIP: {path.name}")
        names = [n for n in archive.namelist() if not n.endswith("/")]
        if len(set(names)) != len(names):
            raise ValueError("Duplicate ZIP entries")
        if any(n.startswith("/") or "\\" in n or ".." in n.split("/")
               for n in names):
            raise ValueError("Unsafe ZIP entry")
        return {n: archive.read(n) for n in names}


def _zip(path: Path, files: dict[str, bytes]) -> None:
    if path.exists():
        raise FileExistsError("Never overwrite an existing candidate archive")
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "x", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            metadata = ZipInfo(filename=name, date_time=(1980, 1, 1, 0, 0, 0))
            metadata.compress_type = ZIP_DEFLATED
            metadata.external_attr = (0o100644 << 16)
            archive.writestr(metadata, files[name], compress_type=ZIP_DEFLATED,
                             compresslevel=9)
    if _load(path) != files:
        raise ValueError("Archive verification failed")


def _manifest(items: dict[str, bytes]) -> dict:
    return {
        "schema": SCHEMA,
        "family": "Designeo Lite",
        "compatible_theme_directory": ROOT.removesuffix("/"),
        "theme_version_reference": "2.0.1",
        "distribution": "authoring_library_not_wordpress_installable",
        "patterns": [
            {
                "slug": name,
                "path": f"patterns/{name}.php",
                "sha256": _digest(items[f"{ROOT}patterns/{name}.php"]),
                "contains_placeholders": True,
                "publish_ready": False,
            }
            for name in ALLOWED
        ],
        "warning": ("Components are templates for editorial work only. "
                    "Replace links, copy and media and pass release preflight "
                    "before publishing. No working contact form is supplied."),
    }


def build_packages(repo: Path, core_output: Path, library_output: Path) -> dict:
    repo = repo.resolve()
    core_output = core_output.resolve()
    library_output = library_output.resolve()
    if core_output == library_output:
        raise ValueError("Core and library must be separate archives")
    if core_output.exists() or library_output.exists():
        raise FileExistsError("Refuse to overwrite an existing output")
    for output in (core_output, library_output):
        if repo == output or repo in output.parents:
            raise ValueError("Output must be outside source repository")
    with tempfile.TemporaryDirectory(prefix="lite_normalized_") as tmp:
        normalized_path = Path(tmp) / "normalized.zip"
        result = build_normalized(repo, normalized_path)
        items = _load(normalized_path)
    if result["candidate_unresolved_tokens"]:
        raise ValueError("Token-alignment contract not met")
    patterns = {k: v for k, v in items.items() if k.startswith(ROOT + "patterns/")}
    wanted = {f"{ROOT}patterns/{name}.php" for name in ALLOWED}
    if set(patterns) != wanted:
        raise ValueError("Unknown/missing patterns: manual review required")
    core = {k: v for k, v in items.items() if k not in patterns}
    essential = {"style.css", "functions.php", "theme.json", "index.php",
                 "templates/index.html", "templates/page.html",
                 "parts/header.html", "parts/footer.html"}
    if not {ROOT + name for name in essential}.issubset(core):
        raise ValueError("Missing Lite Core essential file")
    if len(items) != 20 or len(core) != 16 or len(patterns) != 4:
        raise ValueError("Unexpected base package size")
    metadata = _manifest(items)
    library: dict[str, bytes] = {
        f"{LIBRARY_ROOT}manifest.json":
            (json.dumps(metadata, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    }
    for name in ALLOWED:
        library[f"{LIBRARY_ROOT}patterns/{name}.php"] = patterns[
            f"{ROOT}patterns/{name}.php"
        ]
    _zip(core_output, core)
    _zip(library_output, library)
    return {
        "result": "static_core_and_optional_library_built",
        "core_files": len(core),
        "optional_patterns": list(ALLOWED),
        "core_sha256": _digest(core_output.read_bytes()),
        "library_sha256": _digest(library_output.read_bytes()),
        "core_path": str(core_output),
        "library_path": str(library_output),
        "source_zip_modified": False,
        "core_has_editorial_placeholders": False,
        "library_has_editorial_placeholders": True,
        "wordpress_runtime_tested": False,
        "release_ready": False,
    }


def compose_variant(core_zip: Path, library_zip: Path, selected: list[str],
                    output: Path) -> dict:
    """Create optional authoring preview, not a sector-specific published site."""
    output = output.resolve()
    if output.exists() or output in (core_zip.resolve(), library_zip.resolve()):
        raise FileExistsError("Refuse to replace an existing archive")
    if len(selected) != len(set(selected)) or any(p not in ALLOWED for p in selected):
        raise ValueError("Only unique, known optional patterns may be selected")
    core = _load(core_zip)
    library = _load(library_zip)
    if not all(k.startswith(ROOT) for k in core) or any(
        k.startswith(ROOT + "patterns/") for k in core
    ):
        raise ValueError("Not a Lite Core archive")
    for path in (ROOT + "theme.json", ROOT + "templates/index.html"):
        if path not in core:
            raise ValueError("Missing Lite Core required file")
    manifest_key = f"{LIBRARY_ROOT}manifest.json"
    if manifest_key not in library:
        raise ValueError("Missing pattern library manifest")
    metadata = json.loads(library[manifest_key].decode("utf-8"))
    if metadata.get("schema") != SCHEMA or metadata.get(
            "compatible_theme_directory") != ROOT.removesuffix("/"):
        raise ValueError("Incompatible library")
    catalog = metadata.get("patterns")
    if not isinstance(catalog, list) or {r.get("slug") for r in catalog} != set(ALLOWED):
        raise ValueError("Unexpected library patterns")
    patterns = {}
    for entry in catalog:
        name, relative = entry["slug"], entry["path"]
        key = LIBRARY_ROOT + relative
        if relative != f"patterns/{name}.php" or key not in library:
            raise ValueError("Malformed library reference")
        if _digest(library[key]) != entry.get("sha256"):
            raise ValueError("Modified library pattern")
        if name in selected:
            patterns[ROOT + relative] = library[key]
    composed = {**core, **patterns}
    _zip(output, composed)
    return {
        "result": "static_authoring_preview_only",
        "pattern_selection": selected,
        "theme_files": len(composed),
        "sha256": _digest(output.read_bytes()),
        "output": str(output),
        "editorial_review_needed": bool(selected),
        "wordpress_runtime_tested": False,
        "release_ready": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--core", type=Path, required=True)
    p.add_argument("--library", type=Path, required=True)
    args = p.parse_args()
    repo = Path(__file__).resolve().parents[1]
    print(json.dumps(build_packages(repo, args.core, args.library),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
