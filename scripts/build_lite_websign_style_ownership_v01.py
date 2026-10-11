"""Assign Websign styles to Lite theme only when Lite is active in WordPress.

The current Websign Runtime plugin v0.1.0 enqueues CSS for frontend/editor
unconditionally. Lite's own native bridge defines 22 of the same selectors.
This isolated build *only* adds late theme hooks to dequeue that stylesheet,
keeping the plugin installed and untouched for every non-Lite theme.
Lite's bridge gains the runtime's scoped 768px columns fallback.

This is a candidate; activation, admin editor and visual QA are separate gates.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.build_lite_core_library_v01 import ROOT, _load, _zip
from scripts.build_lite_dynamic_core_v01 import FRONT_CSS, EDITOR_CSS
from scripts.audit_lite_css_cascade_v01 import build_cascade_safe_core, parse_css

FUNCTIONS = ROOT + "functions.php"
CSS_MARKER = "/* DESIGNEO LITE / WEBSIGN RESPONSIVE OWNERSHIP v0.1 */"
HOOK_MARKER = "// Designeo Lite / Websign Runtime stylesheet ownership v0.1."

PHP_HOOK = r'''
// Designeo Lite / Websign Runtime stylesheet ownership v0.1.
// Loaded only when this theme is ACTIVE. Retain the plugin installation;
// on Twenty Twenty-Five and other themes the plugin keeps all its styles.
// Lite itself provides the Websign class bridge in global.css/editor.css.
// Run after Websign Runtime's default priority-10 enqueue callbacks.
function designeo_lite_own_websign_styles() {
    wp_dequeue_style( 'websign-runtime' );
}
add_action( 'wp_enqueue_scripts', 'designeo_lite_own_websign_styles', 1000 );
add_action( 'enqueue_block_editor_assets', 'designeo_lite_own_websign_styles', 1000 );
'''

# Keep the useful narrow-screen columns fallback after retiring runtime.css.
# No !important and only class-scoped columns, not site-wide .wp-block-columns.
MOBILE = r'''
/* DESIGNEO LITE / WEBSIGN RESPONSIVE OWNERSHIP v0.1 */
@media (max-width: 768px) {
  .wp-block-columns.websign-columns-gap-compact,
  .wp-block-columns.websign-columns-gap-normal,
  .wp-block-columns.websign-columns-gap-spacious {
    flex-direction: column;
  }
  .wp-block-columns.websign-columns-gap-compact > .wp-block-column,
  .wp-block-columns.websign-columns-gap-normal > .wp-block-column,
  .wp-block-columns.websign-columns-gap-spacious > .wp-block-column {
    flex-basis: auto;
  }
}
'''


def build_style_ownership_core(repo: Path, output: Path) -> dict:
    repo = repo.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError("Cannot replace an existing candidate")
    if repo == output or repo in output.parents:
        raise ValueError("Build output must be outside source checkout")

    with TemporaryDirectory(prefix="lite_style_owner_") as temp:
        source_zip = Path(temp) / "previous-cascade-safe.zip"
        build_cascade_safe_core(repo, source_zip)
        baseline = _load(source_zip)

    if set(baseline) != set(baseline.keys()) or len(baseline) != 16:
        raise ValueError("Unexpected Lite Core source file count")
    existing_php = baseline[FUNCTIONS].decode("utf-8-sig")
    if HOOK_MARKER in existing_php or "designeo_lite_own_websign_styles" in existing_php:
        raise ValueError("Style ownership hook already present")
    if "add_editor_style( 'assets/css/editor.css' );" not in existing_php:
        raise ValueError("Theme editor CSS registration contract missing")
    if "'designeo-lite-global'" not in existing_php:
        raise ValueError("Theme frontend CSS enqueue contract missing")

    updated = dict(baseline)
    updated[FUNCTIONS] = (existing_php.rstrip() + "\n" + PHP_HOOK).encode("utf-8")
    for path in (FRONT_CSS, EDITOR_CSS):
        original = baseline[path].decode("utf-8-sig")
        if CSS_MARKER in original or "BEGIN DESIGNEO LITE DYNAMIC BRIDGE v0.1" not in original:
            raise ValueError("Unexpected Websign bridge state")
        new_css = original.rstrip() + "\n\n" + MOBILE.lstrip()
        parse_css(new_css)
        if new_css.count("!important") != original.count("!important"):
            raise ValueError("New CSS may not add !important declarations")
        updated[path] = new_css.encode("utf-8")

    expected_changes = {FUNCTIONS, FRONT_CSS, EDITOR_CSS}
    if {name for name in baseline if baseline[name] != updated[name]} != expected_changes:
        raise ValueError("Unexpected changed theme files")
    if len(updated) != 16:
        raise ValueError("Theme file count changed")
    for hook in ("wp_enqueue_scripts", "enqueue_block_editor_assets"):
        expected = f"add_action( '{hook}', 'designeo_lite_own_websign_styles', 1000 );"
        if expected not in updated[FUNCTIONS].decode("utf-8"):
            raise ValueError("Missing frontend/editor Websign ownership hook")
    _zip(output, updated)
    return {
        "status": "style_ownership_candidate_static",
        "theme_files": len(updated),
        "changed_files": sorted(x[len(ROOT):] for x in expected_changes),
        "unchanged_files": len(updated) - len(expected_changes),
        "old_plugin_version_supported": "0.1.0",
        "plugin_handle_removed_only_if_lite_theme_active": "websign-runtime",
        "plugin_source_modified": False,
        "wordpress_active_site_modified": False,
        "hooks_priority": 1000,
        "frontend_and_editor_styles_owned_by_theme": True,
        "new_important_rules": 0,
        "local_test_css_parses": True,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "output": str(output),
        "wordpress_activation_tested": False,
        "visual_gutenberg_qa_passed": False,
        "release_ready": False,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    print(json.dumps(build_style_ownership_core(
        Path(__file__).resolve().parents[1], args.output
    ), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
