"""WRL → DesignOS evidence export v0.1, pure and intentionally restrictive.

Accepts only the already-computed factual WRL research_summary.
Never crawls websites, reads HTML/screenshots/SQLite, invokes LLMs or writes files.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
import re

EXPORT_VERSION = "wrl_evidence.v0.1"
AREAS = ("identidade_contexto", "arquitetura_informacao", "tecnologia_codigo",
         "seo", "acessibilidade", "conversao_confianca")
PAGE_TYPES = {"home", "service", "portfolio", "case_study", "pricing", "about",
              "contact", "blog_index", "article", "legal"}
CONVERSION_FEATURES = {"commercial_cta", "contact", "quote_request", "portfolio",
                       "form", "whatsapp", "phone", "email"}
QUALITY_INDICATORS = {"missing_h1", "missing_meta_description", "inputs_without_labels",
                      "images_without_alt", "duplicate_ids"}
KNOWN_TECHNOLOGIES = {"WordPress", "Elementor", "WooCommerce", "Shopify", "Wix",
                      "Squarespace", "Webflow", "Bootstrap", "Tailwind CSS", "React",
                      "Vue.js", "Next.js", "Nuxt", "Cloudflare", "Google Analytics",
                      "Google Tag Manager", "Meta Pixel"}
DOMAIN = re.compile(r"(?i)^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
MAX_WEBSITES = 250


def _count(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("WRL counters must be nonnegative integers")
    return value


def _coverage(obj: Any, total: int) -> dict[str, int]:
    if not isinstance(obj, Mapping):
        raise ValueError("Missing WRL analysis coverage")
    result = {k: _count(obj.get(k)) for k in ("analyzed", "partial", "not_analyzed")}
    if _count(obj.get("total")) != total or sum(result.values()) != total:
        raise ValueError("Inconsistent WRL coverage")
    return {**result, "total": total}


def _rows(rows: Any, allowed: set[str], source_ids: set[int], total: int) -> list[dict]:
    if not isinstance(rows, list):
        raise ValueError("Expected list of factual WRL observations")
    seen = set()
    output = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("Invalid WRL observation")
        label = row.get("label")
        if label not in allowed or label in seen:
            raise ValueError("Unknown or duplicate WRL observation label")
        seen.add(label)
        counts = {key: _count(row.get(key)) for key in
                  ("present", "absent", "partial_unknown", "not_analyzed")}
        if sum(counts.values()) != total:
            raise ValueError("Observation coverage does not match corpus")
        ids = row.get("website_ids")
        if not isinstance(ids, list) or any(type(i) is not int or i not in source_ids for i in ids):
            raise ValueError("Invalid website evidence references")
        if len(set(ids)) != len(ids) or len(ids) != counts["present"]:
            raise ValueError("Evidence IDs do not match observed presence")
        output.append({
            "feature": label,
            **counts,
            "evidence_refs": [f"WRL-WEB-{id_:06d}" for id_ in ids],
        })
    return output


def export_research_summary(summary: Mapping, *, research_id: int,
                            exported_at: str, source_schema_version: str = "0.2.2") -> dict:
    """Return privacy-minimized observations, never prose/HTML/media/user-entered notes."""
    if type(research_id) is not int or research_id <= 0:
        raise ValueError("Invalid research identifier")
    try:
        dt = datetime.fromisoformat(exported_at.replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("Timestamp must include timezone")
    except (TypeError, AttributeError) as exc:
        raise ValueError("Invalid export timestamp") from exc
    if source_schema_version != "0.2.2":
        raise ValueError("Unsupported WRL source schema")
    if not isinstance(summary, Mapping):
        raise ValueError("Invalid WRL summary")
    corpus = summary.get("corpus")
    if not isinstance(corpus, Mapping):
        raise ValueError("Missing corpus")
    total = _count(corpus.get("website_count"))
    if total > MAX_WEBSITES:
        raise ValueError("Corpus exceeds export limit")
    domains = corpus.get("domains")
    if not isinstance(domains, list) or len(domains) != total:
        raise ValueError("Corpus list and count mismatch")
    references = []
    ids = set()
    for item in domains:
        if not isinstance(item, Mapping):
            raise ValueError("Invalid corpus reference")
        wid = item.get("website_id")
        if type(wid) is not int or wid <= 0 or wid in ids:
            raise ValueError("Duplicate/invalid website reference")
        ids.add(wid)
        raw_domain = item.get("domain", "")
        host = raw_domain.strip().lower().rstrip(".") if isinstance(raw_domain, str) else ""
        references.append({
            "ref": f"WRL-WEB-{wid:06d}",
            "domain": host if DOMAIN.fullmatch(host) and len(host) <= 253 else None,
            "capture_timestamp": None,  # Not supplied by research_summary; never invent.
        })
    covered = corpus.get("coverage")
    if not isinstance(covered, Mapping):
        raise ValueError("Missing source coverage")
    coverage = {a: _coverage(covered.get(a), total) for a in AREAS}
    def section(key: str) -> Mapping:
        val = summary.get(key)
        if not isinstance(val, Mapping):
            raise ValueError(f"Missing WRL section: {key}")
        return val
    architecture = section("architecture")
    conversion = section("conversion")
    quality = section("quality")
    technologies = section("technologies")
    _coverage(architecture.get("coverage"), total)
    _coverage(conversion.get("coverage"), total)
    tech_rows = technologies.get("items")
    if not isinstance(tech_rows, list):
        raise ValueError("Invalid WRL technologies")
    tech = []
    for row in tech_rows:
        if isinstance(row, Mapping) and row.get("label") in KNOWN_TECHNOLOGIES:
            label = row["label"]
            count = _count(row.get("count"))
            if count > total:
                raise ValueError("Invalid technology count")
            tech.append({"technology": label, "websites_observed": count})
    return {
        "export_version": EXPORT_VERSION,
        "source": {"application": "Website Research Lab", "source_schema_version": source_schema_version,
                   "research_ref": f"WRL-RESEARCH-{research_id:06d}", "exported_at": exported_at},
        "corpus": {"website_count": total, "references": references, "coverage": coverage},
        "observations": {
            "page_types": _rows(architecture.get("page_types"), PAGE_TYPES, ids, total),
            "conversion_features": _rows(conversion.get("features"), CONVERSION_FEATURES, ids, total),
            "quality_indicators": _rows(quality.get("metrics"), QUALITY_INDICATORS, ids, total),
            "technologies": tech,
        },
        "interpretation": None,
        "limitations": ["Incomplete/partial WRL coverage is not observed absence",
                        "Technology and page classification are heuristic",
                        "No semantic copying of competitor design or assets",
                        "No raw HTML, screenshots, contact values, website names or free-text notes"],
        "action_authorized": False,
    }
