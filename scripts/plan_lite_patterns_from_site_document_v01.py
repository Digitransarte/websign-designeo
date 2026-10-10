"""Bridge a *validated* Websign SiteDocument v0.1 into Lite pattern suggestions.

Accepts a callable native SiteDocument validator (from the unpublished/local
websign_vnext.validation module) instead of duplicating or publishing it here.
Patterns are *authoring suggestions*, not reconstructed page content.
No I/O, website access, WordPress mutations, rendering or LLM calls.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
import re
from typing import Any

SCHEMA_VERSION = "websign.site.v0.1"
LIBRARY_SCHEMA = "designeo.lite.library.v0.1"
LIBRARY_DIRECTORY = "designeo-lite-base"
SUPPORTED = ("hero", "services", "about", "cta")
CONTAINERS = frozenset({"section", "container", "columns", "column"})
LEAVES = frozenset({"heading", "paragraph", "button", "image"})
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class LiteSelectionError(ValueError):
    """Fail-closed on invalid/unsupported authoring input."""


def _validate_catalog(manifest: Any) -> set[str]:
    if not isinstance(manifest, Mapping):
        raise LiteSelectionError("Library manifest must be an object")
    if (manifest.get("schema") != LIBRARY_SCHEMA or
            manifest.get("compatible_theme_directory") != LIBRARY_DIRECTORY or
            manifest.get("distribution") != "authoring_library_not_wordpress_installable"):
        raise LiteSelectionError("Incompatible or unpublished pattern library")
    patterns = manifest.get("patterns")
    if not isinstance(patterns, list) or not patterns or len(patterns) > len(SUPPORTED):
        raise LiteSelectionError("Invalid pattern catalog")
    allowed: set[str] = set()
    for pattern in patterns:
        if not isinstance(pattern, Mapping):
            raise LiteSelectionError("Malformed catalog entry")
        slug = pattern.get("slug")
        if slug not in SUPPORTED or slug in allowed:
            raise LiteSelectionError("Unknown or duplicate catalog pattern")
        if (pattern.get("path") != f"patterns/{slug}.php" or
                type(pattern.get("publish_ready")) is not bool or
                pattern["publish_ready"] is not False or
                pattern.get("contains_placeholders") is not True):
            raise LiteSelectionError("Pattern safety flags or path missing")
        digest = pattern.get("sha256")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise LiteSelectionError("Missing SHA256 provenance")
        allowed.add(slug)
    return allowed


def _walk_leaves(node: Any, *, depth: int = 0):
    if depth > 18 or not isinstance(node, dict):
        raise LiteSelectionError("Invalid or overly nested SiteDocument structure")
    kind = node.get("type")
    if kind in CONTAINERS:
        children = node.get("children")
        if not isinstance(children, list) or not 1 <= len(children) <= 160:
            raise LiteSelectionError("Invalid SiteDocument children")
        for child in children:
            yield from _walk_leaves(child, depth=depth + 1)
    elif kind in LEAVES:
        yield node
    else:
        raise LiteSelectionError("Unsupported SiteDocument node")


def _analyze_section(section: dict) -> dict[str, int]:
    tally = {"h1": 0, "h2_or_h3": 0, "paragraph": 0,
             "button": 0, "image": 0}
    for node in _walk_leaves(section):
        kind = node["type"]
        if kind == "heading":
            if node.get("level") == 1:
                tally["h1"] += 1
            elif node.get("level") in (2, 3):
                tally["h2_or_h3"] += 1
        else:
            tally[kind] += 1
    return tally


def _candidates(counts: dict[str, int], section_index: int) -> list[tuple[str, str]]:
    found = []
    if (section_index == 0 and counts["h1"] >= 1 and
            counts["paragraph"] >= 1 and counts["button"] >= 1):
        found.append(("hero", "first_section_with_h1_paragraph_and_button"))
    if counts["h2_or_h3"] >= 2 and counts["paragraph"] >= 2:
        found.append(("services", "repeated_subheadings_with_descriptions"))
    if counts["image"] >= 1 and counts["h2_or_h3"] >= 1 and counts["paragraph"] >= 1:
        found.append(("about", "image_and_subheading_with_description"))
    if (section_index > 0 and counts["h2_or_h3"] == 1 and
            counts["button"] >= 1 and counts["image"] == 0 and
            counts["paragraph"] <= 1):
        found.append(("cta", "later_section_with_single_subheading_and_button"))
    return found


def plan_lite_patterns(
    document: Any,
    manifest: Any,
    *,
    validate_site_document: Callable[[Any], None],
) -> dict:
    """Deterministic *suggestions* from an upstream-validated neutral document.

    Caller MUST pass actual Websign validator in integration (not a no-op).
    No source copy, label, URL, image or company name is emitted by this adapter.
    """
    if not callable(validate_site_document):
        raise LiteSelectionError("A native SiteDocument validator is mandatory")
    validate_site_document(document)
    if not isinstance(document, dict) or document.get("schema_version") != SCHEMA_VERSION:
        raise LiteSelectionError("Unsupported SiteDocument schema")
    catalog = _validate_catalog(manifest)
    pages = document.get("pages")
    if not isinstance(pages, list) or not 1 <= len(pages) <= 40:
        raise LiteSelectionError("Invalid page count")
    plan = []
    selected: list[str] = []
    ambiguity_count = 0
    unmatched_count = 0
    for page_index, page in enumerate(pages, 1):
        if not isinstance(page, dict):
            raise LiteSelectionError("Invalid page")
        sections = page.get("nodes")
        if not isinstance(sections, list) or not 1 <= len(sections) <= 32:
            raise LiteSelectionError("Invalid page sections")
        suggestions = []
        for section_index, section in enumerate(sections):
            if not isinstance(section, dict) or section.get("type") != "section":
                raise LiteSelectionError("Top-level nodes must be sections")
            measures = _analyze_section(section)
            candidates = [(name, reason) for name, reason in
                          _candidates(measures, section_index) if name in catalog]
            ref = f"page-{page_index:02d}/section-{section_index+1:02d}"
            if len(candidates) == 1:
                name, reason = candidates[0]
                if name not in selected:
                    selected.append(name)
                warnings = ["source_content_not_transferred"]
                if name == "hero" and measures["image"]:
                    warnings.append("hero_pattern_has_no_image_slot")
                if name == "about" and measures["image"]:
                    warnings.append("about_pattern_image_is_placeholder")
                suggestions.append({
                    "section_ref": ref, "suggested_pattern": name,
                    "rule": reason, "review_warnings": warnings,
                    "status": "proposal_not_inserted",
                })
            elif len(candidates) > 1:
                ambiguity_count += 1
                suggestions.append({
                    "section_ref": ref, "suggested_pattern": None,
                    "reason": "multiple_structural_matches",
                    "candidate_patterns": [name for name, _ in candidates],
                    "status": "human_review_required",
                })
            else:
                unmatched_count += 1
                suggestions.append({
                    "section_ref": ref, "suggested_pattern": None,
                    "reason": "no_supported_structural_match",
                    "status": "human_review_required",
                })
        plan.append({"page_ref": f"page-{page_index:02d}",
                     "sections": suggestions})
    return {
        "plan_schema": "designeo.lite.selection.v0.1",
        "site_document_schema": SCHEMA_VERSION,
        "library_schema": LIBRARY_SCHEMA,
        "source_validation": "caller_supplied_native_validator_executed",
        "page_count": len(pages),
        "pattern_selection": selected,
        "pages": plan,
        "ambiguous_sections": ambiguity_count,
        "unmatched_sections": unmatched_count,
        "source_text_or_assets_exported": False,
        "site_document_mutated": False,
        "site_document_content_transferred_to_patterns": False,
        "patterns_inserted_into_wordpress_pages": False,
        "requires_human_review": True,
        "wordpress_runtime_tested": False,
        "publish_ready": False,
    }
