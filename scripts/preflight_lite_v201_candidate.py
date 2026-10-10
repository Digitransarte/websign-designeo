"""Read-only release-preflight audit for Designeo Lite WordPress candidates.

Static checks do not replace a live WordPress staging and visual QA.
No file writes, network calls, WordPress commands, or archive extraction.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from zipfile import ZipFile


class InteractiveContentAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.buttons_without_urls = 0
        self.images_without_sources = 0
        self.forms_with_placeholder_actions = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        props = dict(attrs)
        if tag == "a" and "wp-block-button__link" in (props.get("class") or "").split():
            if not (props.get("href") or "").strip() or props.get("href") == "#":
                self.buttons_without_urls += 1
        if tag == "img" and not (props.get("src") or "").strip():
            self.images_without_sources += 1
        if tag == "form" and (not (props.get("action") or "").strip() or
                              props.get("action") == "#"):
            self.forms_with_placeholder_actions += 1


def audit_candidate(theme_archive: Path) -> dict:
    """Return evidence and release blockers, never infer runtime pass from static analysis."""
    with ZipFile(theme_archive) as archive:
        if archive.testzip() is not None:
            raise ValueError("Damaged theme archive")
        names = [n for n in archive.namelist() if not n.endswith("/")]
        if not names or any(n.startswith("/") or ".." in n.split("/") for n in names):
            raise ValueError("Invalid theme archive paths")
        roots = {n.split("/")[0] for n in names}
        if len(roots) != 1 or any("/" not in n for n in names):
            raise ValueError("Expected one theme root directory")
        root = next(iter(roots)) + "/"
        data = {n[len(root):]: archive.read(n) for n in names}

    failures: list[dict] = []
    warnings: list[dict] = []
    evidence: list[dict] = []
    def add(bucket: list[dict], code: str, **kwargs) -> None:
        bucket.append({"code": code, **kwargs})

    for required in ("style.css", "functions.php", "theme.json",
                     "templates/index.html", "templates/page.html",
                     "parts/header.html", "parts/footer.html"):
        if required not in data:
            add(failures, "missing_essential_file", path=required)

    theme = json.loads(data.get("theme.json", b"{}"))
    if theme.get("version") != 3:
        add(failures, "unsupported_theme_json_version", version=theme.get("version"))
    style = data.get("style.css", b"").decode("utf-8-sig")
    if "License: Proprietary" in style:
        add(warnings, "license_distribution_review_required",
            detail="Proprietary license marker: review rights and WP ecosystem requirements before distribution")

    interaction_totals = {"buttons_without_urls": 0, "images_without_sources": 0,
                          "forms_with_placeholder_actions": 0}
    pattern_count = 0
    for path, blob in sorted(data.items()):
        if path.startswith("patterns/") and path.endswith(".php"):
            pattern_count += 1
        if not path.endswith((".html", ".php")):
            continue
        if not (path.startswith(("patterns/", "parts/", "templates/"))):
            continue
        parser = InteractiveContentAudit()
        parser.feed(blob.decode("utf-8-sig"))
        found = {key: getattr(parser, key) for key in interaction_totals}
        for key, value in found.items():
            interaction_totals[key] += value
            if value:
                add(failures, key, path=path, count=value)

    # Core WP stack includes acceptable fallback fonts, but named external fonts
    # won't be guaranteed if neither bundled nor deliberately enqueued.
    families = theme.get("settings", {}).get("typography", {}).get("fontFamilies", [])
    named_families = [item.get("slug") for item in families
                      if isinstance(item, dict) and item.get("slug") in
                      {"display", "body", "mono"}]
    font_assets = [name for name in data if re.search(r"\.(woff2?|ttf|otf)$", name, re.I)]
    css_assets = [v.decode("utf-8-sig") for name, v in data.items() if name.endswith(".css")]
    functions = data.get("functions.php", b"").decode("utf-8-sig")
    font_loader = bool(
        font_assets or
        any("@font-face" in css or "@import" in css for css in css_assets) or
        "fonts.googleapis.com" in functions
    )
    if named_families and not font_loader:
        add(warnings, "named_font_families_not_bundled_or_loaded",
            declared=sorted(named_families),
            effect="System/serif/monospace fallbacks may render instead of named fonts")

    if "templates/index.html" in data:
        index = data["templates/index.html"].decode("utf-8-sig")
        if "<!-- wp:query " not in index or '"inherit":true' not in index:
            add(warnings, "index_template_query_loop_review",
                detail="Verify archive fallback query inherits WordPress main query")
    else:
        add(failures, "block_theme_fallback_missing")

    css_overrides = sum(css.count("!important") for css in css_assets)
    if css_overrides:
        add(warnings, "global_important_overrides_need_visual_qa", count=css_overrides)

    add(evidence, "local_archive_inspected", files=len(data), root=root)
    add(evidence, "static_patterns_inspected", count=pattern_count)
    add(evidence, "interactive_placeholders_checked", **interaction_totals)

    return {
        "product": "Designeo Lite",
        "archive": theme_archive.name,
        "status": "static_preflight_only_not_wordpress_tested",
        "evidence": evidence,
        "release_blockers": failures,
        "review_items": warnings,
        "runtime_gates_pending": [
            "staging isolation and database/files restore test",
            "WordPress full site editor recognition",
            "Gutenberg pattern insertion and frontend rendering",
            "responsive and keyboard accessibility QA",
            "theme slug collision and safe rollback review",
            "content links, images, fonts and licensing acceptance",
        ],
        "static_content_approved": len(failures) == 0,
        "wordpress_runtime_tested": False,
        "release_ready": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", type=Path, required=True)
    p.add_argument("--fail-on-placeholder", action="store_true")
    args = p.parse_args()
    result = audit_candidate(args.zip)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.fail_on_placeholder and result["release_blockers"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
