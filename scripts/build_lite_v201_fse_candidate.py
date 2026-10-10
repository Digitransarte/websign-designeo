"""Build a disposable Designeo Lite FSE candidate from the exact original v2.0.1 ZIP.

Run: python scripts/build_lite_v201_fse_candidate.py --output <isolated-path>.zip
Does not modify source ZIP, themes, WP installs or repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED

SOURCE_RELATIVE = "Templates/designeo-lite-v2.0.1.zip"
OVERLAY_RELATIVE = "Templates/lite-v201-overlay/templates/index.html"
EXPECTED_SHA256 = "f171f8ed81a3bdd6c993c83dee5b9aa93d25c1a4a2974d6ddb5ebd69bdde95cd"
THEME_ROOT = "designeo-lite-base/"
NEW_ENTRY = THEME_ROOT + "templates/index.html"
BLOCK_TAG = re.compile(r"<!--\s*(/?)wp:([a-z0-9-]+(?:/[a-z0-9-]+)?)\b(.*?)-->", re.S)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_balanced_blocks(content: str) -> None:
    stack: list[str] = []
    for match in BLOCK_TAG.finditer(content):
        closing, name, rest = match.groups()
        if closing:
            if not stack or stack.pop() != name:
                raise ValueError(f"Incorrect block closing: {name}")
        elif rest.rstrip().endswith("/"):
            attributes = rest.strip()[:-1].strip()
            if attributes.startswith("{"):
                json.loads(attributes)
        else:
            attributes = rest.strip()
            if attributes.startswith("{"):
                json.loads(attributes)
            stack.append(name)
    if stack:
        raise ValueError(f"Unclosed Gutenberg blocks: {stack}")


def build(repo: Path, output: Path) -> dict:
    repo = repo.resolve()
    src = repo / SOURCE_RELATIVE
    overlay = repo / OVERLAY_RELATIVE
    output = output.resolve()
    if output.exists():
        raise FileExistsError("Refuse to replace existing artifact")
    if output == src or repo == output or repo in output.parents:
        raise ValueError("Output must remain outside the source repository")
    if sha(src.read_bytes()) != EXPECTED_SHA256:
        raise ValueError("Unrecognized Designeo Lite v2.0.1 input ZIP")
    content = overlay.read_text(encoding="utf-8")
    verify_balanced_blocks(content)
    for token in ('"slug":"header"', '"slug":"footer"', '"inherit":true',
                  "<!-- wp:post-template -->", "<!-- wp:query-no-results -->"):
        if token not in content:
            raise ValueError(f"Missing fallback feature: {token}")
    if re.search(r'href="https?://', content):
        raise ValueError("Fallback must not require third-party links")
    with ZipFile(src) as archive:
        if archive.testzip() is not None:
            raise ValueError("Corrupt original theme ZIP")
        original = {name: archive.read(name) for name in archive.namelist()
                    if not name.endswith("/")}
    if NEW_ENTRY in original:
        raise ValueError("Source already contains a block theme fallback")
    if any(not name.startswith(THEME_ROOT) or ".." in name.split("/")
           for name in original):
        raise ValueError("Unsafe original ZIP path")
    theme = json.loads(original[THEME_ROOT + "theme.json"].decode("utf-8-sig"))
    if theme.get("version") != 3:
        raise ValueError("Unexpected theme.json schema version")
    files = {**original, NEW_ENTRY: content.encode("utf-8")}
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            archive.writestr(name, files[name])
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("Candidate ZIP integrity failed")
        extracted = {name: archive.read(name) for name in archive.namelist()}
    if extracted != files or len(files) != len(original) + 1:
        raise ValueError("Candidate archive failed byte-for-byte verification")
    return {"result": "static_validated_candidate_only", "source_files": len(original),
            "candidate_files": len(files), "added": ["templates/index.html"],
            "existing_files_unchanged": True, "source_sha256": sha(src.read_bytes()),
            "candidate_sha256": sha(output.read_bytes()), "output": str(output),
            "wordpress_runtime_validated": False, "deployment_authorized": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    print(json.dumps(build(repo, arguments.output), indent=2))


if __name__ == "__main__":
    main()
