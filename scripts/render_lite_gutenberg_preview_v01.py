"""Private Gutenberg page preview via the EXISTING Websign VNext native renderer.

The Component Slots schema acts as a strict no-loss gate; compatible sections
render from the SAME validated SiteDocument AST using the native Gutenberg
renderer rather than an unrelated imitation or static pattern with placeholders.

No WordPress install, publication, HTML file write, or client data logging.
Returned markup is PRIVATE client content. Legacy PHP pattern styling is NOT
applied by this method; Websign runtime CSS and WP visual QA still needed.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import html
from typing import Any

from scripts.lite_component_slots_v01 import bind_lite_component_slots


def render_lite_gutenberg_preview(
    document: Any,
    manifest: Any,
    *,
    validate_site_document: Callable[[Any],None],
    render_site_document: Callable[[dict],str],
) -> dict:
    if not callable(render_site_document):
        raise ValueError("Native Websign Gutenberg renderer is mandatory")
    slots = bind_lite_component_slots(
        document, manifest, validate_site_document=validate_site_document)
    if not slots["all_sections_bound"]:
        return {
            "status": "blocked_no_content_rendered",
            "blocked_sections": slots["blocked_sections"],
            "bound_sections": slots["bound_sections"],
            "page_count": len(document["pages"]),
            "native_gutenberg_rendered": False,
            "publish_ready": False,
        }
    copies=deepcopy(document)
    pages=[]
    # A page-level render leaves native block/semantic CSS behavior owned by
    # Websign VNext; pattern PHP placeholders are not interpolated.
    for page in copies["pages"]:
        single={**copies, "pages":[page]}
        markup=render_site_document(single)
        if not isinstance(markup,str) or not markup.strip():
            raise ValueError("Native renderer produced empty output")
        if "<!-- wp:" not in markup or "<!-- /wp:" not in markup:
            raise ValueError("Native renderer did not emit expected blocks")
        pages.append({
            "page_ref":f"page-{len(pages)+1:02d}",
            "gutenberg_markup":markup,
            "rendered_by":"websign_vnext.renderers.gutenberg.render_site_document",
            "content_is_private":True,
            "patterns_php_interpolated":False,
        })
    return {
        "status":"native_gutenberg_private_preview",
        "slot_binding_schema":slots["schema"],
        "bound_sections":slots["bound_sections"],
        "page_count":len(pages),
        "pages":pages,
        "native_gutenberg_rendered":True,
        "site_document_mutated":False,
        "style_parity_with_legacy_lite_patterns_verified":False,
        "wordpress_runtime_tested":False,
        "publish_ready":False,
    }
