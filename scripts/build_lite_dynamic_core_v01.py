"""Build an isolated Designeo Lite Core with style parity bridge for native Websign blocks.

The existing WP theme enqueues global.css and editor.css; append one scoped
overlay to each. No new Gutenberg renderer, PHP hooks, theme registration, site
changes, deployment or network calls. This is NOT WP runtime certification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

from scripts.build_lite_core_library_v01 import _load, _zip, build_packages, ROOT


STYLESHEET = "Templates/lite-runtime-overlay/assets/css/websign-lite-bridge.css"
FRONT_CSS = ROOT + "assets/css/global.css"
EDITOR_CSS = ROOT + "assets/css/editor.css"
CSS_START = "/* Designeo Lite / Websign Native Block Style Bridge v0.1."
PREFIX = b"\n\n/* BEGIN DESIGNEO LITE DYNAMIC BRIDGE v0.1 */\n"
SUFFIX = b"\n/* END DESIGNEO LITE DYNAMIC BRIDGE v0.1 */\n"
ALLOWED_CLASS_PREFIX = "websign-"
REQUIRED_STYLES = frozenset({
    "websign-section-spacing-none", "websign-section-spacing-compact",
    "websign-section-spacing-normal", "websign-section-spacing-spacious",
    "websign-section-background-surface", "websign-section-background-muted",
    "websign-section-background-inverse",
    "websign-container-width-narrow", "websign-container-width-content",
    "websign-container-width-wide", "websign-container-alignment-left",
    "websign-container-alignment-center",
    "websign-columns-gap-compact", "websign-columns-gap-normal",
    "websign-columns-gap-spacious",
    "websign-heading-role-display", "websign-heading-role-section",
    "websign-heading-role-subsection",
    "websign-paragraph-role-body", "websign-paragraph-role-lead",
    "websign-paragraph-role-muted",
    "websign-button-style-primary", "websign-button-style-secondary",
    "websign-button-style-outline",
})
WP_VARIABLE = re.compile(r"var\(\s*(--wp--preset--(color|font-size|spacing|font-family)--([a-z0-9-]+))")
CSS_CLASS = re.compile(r"(?<![a-zA-Z0-9_-])\.(websign-[a-z0-9_-]+)")
CSS_DECLARATION = re.compile(r"(?<![a-zA-Z0-9_-])(--dlw-[a-z0-9_-]+)\s*:")
CSS_USE = re.compile(r"var\(\s*(--dlw-[a-z0-9_-]+)")


def validate_bridge(overlay: str, theme: dict) -> dict:
    if CSS_START not in overlay or "@import" in overlay or "url(" in overlay:
        raise ValueError("Unexpected CSS bridge source")
    if overlay.count("{") != overlay.count("}") or "{" not in overlay:
        raise ValueError("Unbalanced CSS braces")
    classes=set(CSS_CLASS.findall(overlay))
    missing=REQUIRED_STYLES-classes
    if missing:
        raise ValueError(f"Missing Websign classes: {sorted(missing)}")
    unknown=classes-REQUIRED_STYLES
    if unknown:
        raise ValueError(f"Unknown Websign classes: {sorted(unknown)}")
    tokens={
        "color":{row["slug"] for row in theme["settings"]["color"]["palette"]},
        "font-size":{row["slug"] for row in theme["settings"]["typography"]["fontSizes"]},
        "spacing":{row["slug"] for row in theme["settings"]["spacing"]["spacingSizes"]},
        "font-family":{row["slug"] for row in theme["settings"]["typography"]["fontFamilies"]},
    }
    used=list(WP_VARIABLE.finditer(overlay))
    not_found=sorted({f"{m[2]}/{m[3]}" for m in used if m[3] not in tokens[m[2]]})
    if not_found:
        raise ValueError(f"Missing Lite design presets: {not_found}")
    own_defined=set(CSS_DECLARATION.findall(overlay))
    own_used=set(CSS_USE.findall(overlay))
    if own_used-own_defined:
        raise ValueError(f"Undefined local CSS vars: {sorted(own_used-own_defined)}")
    if any(v in overlay for v in ("!important", "fonts.googleapis.com",
                                 "http://", "https://")):
        raise ValueError("Bridge may not add important overrides or remote dependencies")
    return {
        "selector_classes":len(classes),
        "known_websign_classes":sorted(classes),
        "word_press_preset_uses":len(used),
        "unknown_preset_references":[],
        "external_assets":False,
        "important_overrides_in_overlay":0,
    }


def build_lite_dynamic_core(repo:Path, output:Path)->dict:
    repo=repo.resolve()
    output=output.resolve()
    if output.exists():
        raise FileExistsError("Refuse overwrite")
    if output==repo or repo in output.parents:
        raise ValueError("Candidate must be outside source checkout")
    overlay=(repo/STYLESHEET).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="lite_bridge_") as tmp:
        core=Path(tmp)/"core.zip"
        lib=Path(tmp)/"library.zip"
        build_packages(repo,core,lib)
        entries=_load(core)
    if FRONT_CSS not in entries or EDITOR_CSS not in entries:
        raise ValueError("Lite CSS files missing")
    functions=entries[ROOT+"functions.php"].decode("utf-8-sig")
    if ("wp_enqueue_style(" not in functions or
        "'assets/css/editor.css'" not in functions or
        "'/assets/css/global.css'" not in functions):
        raise ValueError("Lite Core does not currently load both stylesheets")
    theme=json.loads(entries[ROOT+"theme.json"])
    coverage=validate_bridge(overlay,theme)
    appended=PREFIX+overlay.encode("utf-8")+SUFFIX
    merged=dict(entries)
    for key in (FRONT_CSS,EDITOR_CSS):
        if PREFIX in merged[key]:
            raise ValueError("Existing style bridge duplicate")
        merged[key]=merged[key].rstrip()+appended
    if len(merged)!=len(entries):
        raise ValueError("Cannot change file count")
    changed={name for name in merged if entries[name]!=merged[name]}
    if changed!={FRONT_CSS,EDITOR_CSS}:
        raise ValueError("Unexpected theme mutation")
    _zip(output,merged)
    return {
        "result":"lite_native_style_bridge_static_candidate",
        "source_theme_files":len(entries),
        "candidate_theme_files":len(merged),
        "changed_files":sorted(name[len(ROOT):] for name in changed),
        "untouched_files":len(entries)-len(changed),
        "css_classes_covered":coverage["selector_classes"],
        "missing_preset_references":0,
        "source_core_modified":False,
        "theme_functions_modified":False,
        "editor_stylesheet_already_registered":True,
        "frontend_stylesheet_already_enqueued":True,
        "candidate_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
        "output":str(output),
        "native_gutenberg_renderer_reused":True,
        "legacy_php_patterns_interpolated":False,
        "wordpress_runtime_tested":False,
        "style_parity_visually_verified":False,
        "release_ready":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    print(json.dumps(build_lite_dynamic_core(Path(__file__).resolve().parents[1],
                                              args.output),indent=2))


if __name__=="__main__":
    main()
