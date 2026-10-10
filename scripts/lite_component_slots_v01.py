"""Private, lossless SiteDocument -> Designeo Lite Component Slots v0.1.

The pattern suggestion layer identifies structural candidates. This layer binds
*actual* user copy/links/media locally, but NEVER publishes it or interpolates
static legacy PHP patterns. Each source leaf must be accounted for exactly once,
or the section is rejected with a reason.

Requires Websign's native SiteDocument validator, supplied explicitly.
No file/network/WordPress access, no model calls, no client data logging.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
import re
from typing import Any
from urllib.parse import urlsplit

from scripts.plan_lite_patterns_from_site_document_v01 import (
    LiteSelectionError, plan_lite_patterns,
)

SCHEMA = "designeo.lite.component-slots.v0.1"
# Shapes are capability contracts, not assertions that legacy PHP patterns
# can already be parametrized or that their styling is visually equivalent.
CAPABILITIES = {
    "hero": {
        "fields": {"headline": "string", "description": "string",
                   "actions": "list[label,url]"},
        "min_actions": 1, "max_actions": 2, "media": False,
        "legacy_pattern_has_dynamic_slots": False,
    },
    "services": {
        "fields": {"items": "list[title,description]"},
        "min_items": 2, "max_items": 3,
        "media": False, "legacy_pattern_has_dynamic_slots": False,
    },
    "about": {
        "fields": {"headline": "string", "description": "string",
                   "image": "src,alt", "actions": "list[label,url]"},
        "min_actions": 0, "max_actions": 1,
        "media": True, "legacy_pattern_has_dynamic_slots": False,
    },
    "cta": {
        "fields": {"headline": "string", "description": "optional_string",
                   "action": "label,url"},
        "min_actions": 1, "max_actions": 1,
        "media": False, "legacy_pattern_has_dynamic_slots": False,
    },
}
ALLOWED_NODES = frozenset({"section", "container", "columns", "column",
                           "heading", "paragraph", "button", "image"})
CONTAINER_NODES = frozenset({"section", "container", "columns", "column"})
NODE_LIMIT = 200
NODE_DEPTH = 18


class LiteBindingError(ValueError):
    """Invalid private slot value or unsupported layout."""


def _safe_link(value: Any, *, image: bool = False) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise LiteBindingError("URL is missing or has surrounding whitespace")
    if len(value) > 2048 or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise LiteBindingError("URL contains control characters or is too long")
    if value.startswith("//") or "\\" in value or value in ("#", "/#"):
        raise LiteBindingError("Ambiguous or placeholder link")
    u = urlsplit(value)
    if u.username or u.password or u.fragment and image:
        raise LiteBindingError("Credential-bearing or fragment image URL")
    if value.startswith("/"):
        if u.scheme or u.netloc:
            raise LiteBindingError("Invalid relative path")
        return value
    if u.scheme != "https" or not u.hostname or u.port == 0:
        raise LiteBindingError("Only site-local or HTTPS external URLs allowed")
    return value


def _str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 5000:
        raise LiteBindingError(f"Missing/invalid {label}")
    return value


def _walk(section: Any):
    stack = [(section, 0)]
    seen: set[str] = set()
    n = 0
    while stack:
        node, depth = stack.pop()
        if depth > NODE_DEPTH or not isinstance(node, dict):
            raise LiteBindingError("Section is too deep or invalid")
        n += 1
        if n > NODE_LIMIT or node.get("type") not in ALLOWED_NODES:
            raise LiteBindingError("Unknown or excessive components")
        node_id = _str(node.get("id"), "node id")
        if node_id in seen:
            raise LiteBindingError("Duplicate component identifiers")
        seen.add(node_id)
        if node["type"] in CONTAINER_NODES:
            children = node.get("children")
            if not isinstance(children, list) or not children:
                raise LiteBindingError("Empty structural container")
            stack.extend((x, depth + 1) for x in reversed(children))
        else:
            yield node


def _action(node: dict) -> dict[str, str]:
    return {"label": _str(node.get("label"), "button label"),
            "url": _safe_link(node.get("url"))}


def _shape(leaves: list[dict], shape: dict[str, int]) -> bool:
    count: dict[str, int] = {}
    for node in leaves:
        kind = node["type"]
        count[kind] = count.get(kind, 0) + 1
    return count == shape


def _level(node: dict, valid: tuple[int, ...]) -> str:
    if node.get("type") != "heading" or node.get("level") not in valid:
        raise LiteBindingError("Heading is not compatible with the component")
    return _str(node.get("text"), "heading")


def _bind_hero(leaves: list[dict]) -> dict:
    if sum(n["type"]=="image" for n in leaves):
        raise LiteBindingError("Hero with media needs a new image-capable pattern")
    headings=[n for n in leaves if n["type"]=="heading"]
    paragraphs=[n for n in leaves if n["type"]=="paragraph"]
    buttons=[n for n in leaves if n["type"]=="button"]
    if len(headings)!=1 or len(paragraphs)!=1 or not 1 <= len(buttons) <= 2:
        raise LiteBindingError("Hero requires H1, one paragraph, 1–2 buttons, no other leaves")
    if len(leaves)!=len(headings)+len(paragraphs)+len(buttons):
        raise LiteBindingError("Unexpected hero content")
    return {"headline":_level(headings[0],(1,)),
            "description":_str(paragraphs[0].get("text"),"paragraph"),
            "actions":[_action(n) for n in buttons]}


def _bind_cta(leaves: list[dict]) -> dict:
    headings=[n for n in leaves if n["type"]=="heading"]
    paragraphs=[n for n in leaves if n["type"]=="paragraph"]
    buttons=[n for n in leaves if n["type"]=="button"]
    if len(headings)!=1 or len(paragraphs)>1 or len(buttons)!=1:
        raise LiteBindingError("CTA requires one H2/H3, at most one paragraph, one button")
    if len(leaves)!=len(headings)+len(paragraphs)+len(buttons):
        raise LiteBindingError("CTA includes an incompatible leaf, such as an image")
    return {"headline":_level(headings[0],(2,3)),
            "description":_str(paragraphs[0].get("text"),"description") if paragraphs else None,
            "action":_action(buttons[0])}


def _columns(section: dict) -> list[dict]:
    """Find a unique 2–3 column group; reject anything not accounted for."""
    groups = []
    structural = []
    stack=[section]
    while stack:
        node=stack.pop()
        if node["type"]=="columns":
            groups.append(node)
        elif node["type"] in CONTAINER_NODES:
            children=node.get("children",[])
            if not isinstance(children,list):
                raise LiteBindingError("Invalid container children")
            stack.extend(reversed(children))
        else:
            structural.append(node)
    if len(groups)!=1 or structural:
        raise LiteBindingError("Component needs one columns group with no sibling leaves")
    group=groups[0]
    cols=group.get("children")
    if not isinstance(cols,list) or not 2<=len(cols)<=3 or any(
            not isinstance(c,dict) or c.get("type")!="column" for c in cols):
        raise LiteBindingError("Component needs two or three valid columns")
    return cols


def _bind_services(section: dict, leaves: list[dict]) -> dict:
    cols=_columns(section)
    if not 2<=len(cols)<=3:
        raise LiteBindingError("Services supports two or three items")
    items=[]
    used=[]
    for col in cols:
        contents=list(_walk(col))
        if len(contents)!=2 or {n["type"] for n in contents}!={"heading","paragraph"}:
            raise LiteBindingError("Service item must have one heading and one paragraph")
        h=next(n for n in contents if n["type"]=="heading")
        p=next(n for n in contents if n["type"]=="paragraph")
        items.append({"title":_level(h,(2,3)),
                      "description":_str(p.get("text"),"service description")})
        used+=contents
    if {n["id"] for n in used}!={n["id"] for n in leaves}:
        raise LiteBindingError("Service shape left content unbound")
    return {"items":items}


def _bind_about(section: dict, leaves: list[dict]) -> dict:
    cols=_columns(section)
    if len(cols)!=2:
        raise LiteBindingError("About needs two columns")
    first=list(_walk(cols[0]))
    second=list(_walk(cols[1]))
    sets=[first,second]
    media=[i for i,x in enumerate(sets) if len(x)==1 and x[0]["type"]=="image"]
    if len(media)!=1:
        raise LiteBindingError("About needs one image in its own column")
    other=sets[1-media[0]]
    titles=[x for x in other if x["type"]=="heading"]
    bodies=[x for x in other if x["type"]=="paragraph"]
    buttons=[x for x in other if x["type"]=="button"]
    if len(titles)!=1 or len(bodies)!=1 or len(buttons)>1 or len(other)!=2+len(buttons):
        raise LiteBindingError("About needs H2/H3, text and up to one CTA")
    if len(leaves)!=len(other)+1:
        raise LiteBindingError("About leaves content unbound")
    img=sets[media[0]][0]
    return {"headline":_level(titles[0],(2,3)),
            "description":_str(bodies[0].get("text"),"about description"),
            "image":{"src":_safe_link(img.get("src"),image=True),
                     "alt":_str(img.get("alt"),"image alt")},
            "actions":[_action(n) for n in buttons],
            "image_position":"left" if media[0]==0 else "right"}


BINDERS = {"hero":lambda section,leaves:_bind_hero(leaves),
           "cta":lambda section,leaves:_bind_cta(leaves),
           "services":_bind_services, "about":_bind_about}


def bind_lite_component_slots(document: Any, manifest: Any, *,
                              validate_site_document: Callable[[Any],None]) -> dict:
    """Return private bindings for compatible sections; reject mismatches.

    Deliberately includes copy, URLs, image paths in the RETURN VALUE.
    Must not be uploaded to public GitHub, logs or third-party agents without
    client consent and a separate privacy policy.
    """
    if not callable(validate_site_document):
        raise LiteBindingError("Native Websign validator is mandatory")
    plan=plan_lite_patterns(document,manifest,
                            validate_site_document=validate_site_document)
    bindings=[]
    blocked=[]
    for p_index,page in enumerate(document["pages"]):
        for s_index,section in enumerate(page["nodes"]):
            result=plan["pages"][p_index]["sections"][s_index]
            ref=result["section_ref"]
            chosen=result["suggested_pattern"]
            if not chosen:
                blocked.append({"section_ref":ref,"reason":result.get(
                    "reason","pattern_not_selected")})
                continue
            leaves=[]
            try:
                leaves=list(_walk(section))
                slots=BINDERS[chosen](section,leaves)
            except (LiteBindingError,ValueError,TypeError) as exc:
                # Never report private content in diagnostics.
                reason="incompatible_component_capabilities"
                if chosen=="hero" and any(n["type"]=="image" for n in leaves):
                    reason="hero_requires_media_capability"
                blocked.append({"section_ref":ref,"pattern":chosen,"reason":reason})
                continue
            bindings.append({
                "section_ref":ref,
                "pattern":chosen,
                "slots":slots,
                "source_leaf_refs":[f"{ref}/leaf-{i+1:02d}" for i in range(len(leaves))],
                "leaf_count":len(leaves),
                "binding_status":"private_data_review_required",
                "legacy_php_pattern_rendered":False,
            })
    return {
        "schema":SCHEMA,
        "source_schema":plan["site_document_schema"],
        "pattern_library_schema":plan["library_schema"],
        "capabilities":deepcopy(CAPABILITIES),
        "bindings":bindings,
        "blocked_sections":blocked,
        "section_count":sum(len(p["nodes"]) for p in document["pages"]),
        "bound_sections":len(bindings),
        "all_sections_bound":len(blocked)==0,
        "source_content_included":True,
        "publish_ready":False,
        "wordpress_rendering_done":False,
        "requires_human_review":True,
    }
