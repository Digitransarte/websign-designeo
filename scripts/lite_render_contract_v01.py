"""Deterministic WEB-02 rendering contract overlay for Lite Core.

Fail closed when upstream immutable theme ZIP changes, instead of silently
patching different content. Navigation is deliberately empty by default:
site-specific links must be supplied through an explicit site contract later.
"""
from __future__ import annotations

import re

ROOT = "designeo-lite-base/"


def _replace_exact(data: bytes, old: str, new: str, label: str) -> bytes:
    text = data.decode("utf-8")
    if text.count(old) != 1:
        raise ValueError(f"Unexpected upstream {label}; stop build for review")
    return text.replace(old, new).encode("utf-8")


def apply_render_contract(core: dict[str, bytes]) -> dict[str, bytes]:
    updated = dict(core)
    css = ROOT + "assets/css/global.css"
    old = ".entry-content a {\n  color: var(--wp--preset--color--on-surface);"
    new = ".entry-content a:not(.wp-block-button__link) {\n  color: var(--wp--preset--color--on-surface);"
    updated[css] = _replace_exact(updated[css], old, new, "link selector")
    # The full-width Gutenberg groups need their own phone-sized inline gutters.
    # Scope to WEB-02 sections; retain the existing desktop theme geometry.
    mobile_gutters = (
        "\\n/* WEB-02 mobile section gutters: native Gutenberg blocks. */\\n"
        "@media (max-width: 600px) {\\n"
        "  .dl-main .dl-section {\\n"
        "    box-sizing: border-box;\\n"
        "    padding-inline: 20px;\\n"
        "  }\\n"
        "}\\n"
    )
    if b"WEB-02 mobile section gutters" in updated[css]:
        raise ValueError("Mobile section gutter contract already present")
    updated[css] += mobile_gutters.encode("utf-8")

    for location in ("header", "footer"):
        key = ROOT + f"parts/{location}.html"
        html = updated[key].decode("utf-8")
        # Do not use implicit navigation: WP will autogenerate a page list.
        pattern = r"<!-- wp:navigation \{[^\n]+\} /-->"
        matches = re.findall(pattern, html)
        if len(matches) != 1:
            raise ValueError(f"Unexpected upstream {location} navigation")
        original = matches[0]
        replacement = original.replace(" /-->", " -->\n<!-- /wp:navigation -->")
        updated[key] = html.replace(original, replacement).encode("utf-8")
    return updated
