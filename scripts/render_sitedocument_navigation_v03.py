"""SiteDocument v0.3 navigation contract, independent from page block content.

No site writes. Produces native Gutenberg navigation markup from explicit links.
"""
from __future__ import annotations

import html
import json

from scripts.render_sitedocument_gutenberg_v01 import _text, _url, render as render_page

SCHEMA = "designeo.site-document.v0.3"
PAGE_SCHEMA = "designeo.site-document.v0.2"


def render_site(document: object) -> dict[str, str]:
    if not isinstance(document, dict) or set(document) != {"schema", "page", "navigation"} or document["schema"] != SCHEMA:
        raise ValueError("Invalid v0.3 SiteDocument")
    navigation = document["navigation"]
    if not isinstance(navigation, dict) or set(navigation) != {"header", "footer"}:
        raise ValueError("Expected explicit header and footer navigation")
    result = {"page": render_page({"schema": PAGE_SCHEMA, "page": document["page"]})}
    for region in ("header", "footer"):
        links = navigation[region]
        if not isinstance(links, list) or len(links) > 8:
            raise ValueError("Invalid navigation links")
        seen = set()
        blocks = []
        for link in links:
            if not isinstance(link, dict) or set(link) != {"label", "url"}:
                raise ValueError("Invalid navigation link")
            label = _text(link["label"], 60)
            url = _url(link["url"])
            if url in seen:
                raise ValueError("Duplicate navigation URL")
            seen.add(url)
            attributes = json.dumps({"label": html.unescape(label), "url": html.unescape(url), "kind": "custom"},
                                    ensure_ascii=False, separators=(",", ":"))
            # prevent block-comment termination and HTML attribute injection
            if "-->" in attributes or "<" in attributes:
                raise ValueError("Unsafe Gutenberg attribute")
            blocks.append(f"<!-- wp:navigation-link {attributes} /-->")
        # Empty navigation is represented explicitly and must not fallback to a page list.
        result[region] = ('<!-- wp:navigation {"overlayMenu":"mobile"} -->\n' +
                          "\n".join(blocks) + '\n<!-- /wp:navigation -->\n')
    return result
