"""Minimal DesignOS Discovery briefing from an untrusted WRL EvidencePackage.

This does not read websites, execute the Design Agent or approve a design direction.
It only transforms validated, anonymized observations into reviewable questions.
"""
from __future__ import annotations

from collections.abc import Mapping
import re

from .evidence_export import (AREAS, CONVERSION_FEATURES, EXPORT_VERSION,
                              KNOWN_TECHNOLOGIES, PAGE_TYPES, QUALITY_INDICATORS)

SECTORS = {
    "professional-services": "Serviços profissionais",
    "wellbeing-services": "Serviços de bem-estar (hipótese de estudo)",
    "industrial-services": "Serviços industriais (hipótese de estudo)",
}
ALLOWED = {
    "page_types": PAGE_TYPES,
    "conversion_features": CONVERSION_FEATURES,
    "quality_indicators": QUALITY_INDICATORS,
}
REF_PATTERN = re.compile(r"^WRL-WEB-[0-9]{6}$")
RESEARCH_REF = re.compile(r"^WRL-RESEARCH-[0-9]{6}$")
MAX_WEBSITES = 250


def _number(n: object) -> int:
    if type(n) is not int or n < 0:
        raise ValueError("Counter must be a nonnegative integer")
    return n


def prepare_designos_discovery_briefing(
    packet: Mapping,
    *,
    sector_key: str,
) -> dict:
    """Pure function; result fits DesignOS add_briefing(..., content=result).

    All copy in the result is authored locally or drawn from allowlisted labels.
    Untrusted site text, domains, URLs, HTML, images and form values never pass.
    """
    if sector_key not in SECTORS:
        raise ValueError("Unknown sector hypothesis")
    if not isinstance(packet, Mapping) or packet.get("export_version") != EXPORT_VERSION:
        raise ValueError("Unsupported WRL evidence export")
    if packet.get("action_authorized") is not False or packet.get("interpretation") is not None:
        raise ValueError("Only unapproved factual research inputs are accepted")
    source = packet.get("source")
    if not isinstance(source, Mapping) or source.get("application") != "Website Research Lab":
        raise ValueError("Invalid WRL provenance")
    if source.get("source_schema_version") != "0.2.2":
        raise ValueError("Unsupported factual data schema")
    research_ref = source.get("research_ref")
    if not isinstance(research_ref, str) or not RESEARCH_REF.fullmatch(research_ref):
        raise ValueError("Invalid research reference")
    timestamp = source.get("exported_at")
    if not isinstance(timestamp, str) or len(timestamp) > 64:
        raise ValueError("Invalid source timestamp")

    corpus = packet.get("corpus")
    if not isinstance(corpus, Mapping):
        raise ValueError("Missing WRL corpus")
    total = _number(corpus.get("website_count"))
    if total == 0 or total > MAX_WEBSITES:
        raise ValueError("Research must have 1–250 websites")
    refs = corpus.get("references")
    if not isinstance(refs, list) or len(refs) != total:
        raise ValueError("Invalid website references")
    source_refs = []
    for obj in refs:
        if not isinstance(obj, Mapping):
            raise ValueError("Invalid website reference")
        ref = obj.get("ref")
        if not isinstance(ref, str) or not REF_PATTERN.fullmatch(ref) or ref in source_refs:
            raise ValueError("Invalid/duplicate source ref")
        source_refs.append(ref)
    coverage = corpus.get("coverage")
    if not isinstance(coverage, Mapping):
        raise ValueError("Missing coverage")
    safe_coverage = {}
    for area in AREAS:
        item = coverage.get(area)
        if not isinstance(item, Mapping):
            raise ValueError("Missing area coverage")
        c = {k: _number(item.get(k)) for k in
             ("analyzed", "partial", "not_analyzed", "total")}
        if c["total"] != total or c["analyzed"] + c["partial"] + c["not_analyzed"] != total:
            raise ValueError("Inconsistent analysis coverage")
        safe_coverage[area] = c

    observation_groups = packet.get("observations")
    if not isinstance(observation_groups, Mapping):
        raise ValueError("Missing WRL observations")
    observations = {}
    for group, allowed in ALLOWED.items():
        records = observation_groups.get(group)
        if not isinstance(records, list):
            raise ValueError("Invalid observations")
        seen = set()
        observations[group] = []
        for row in records:
            if not isinstance(row, Mapping):
                raise ValueError("Invalid observation row")
            feature = row.get("feature")
            if feature not in allowed or feature in seen:
                raise ValueError("Unknown/duplicate factual feature")
            seen.add(feature)
            counts = {key: _number(row.get(key)) for key in
                      ("present", "absent", "partial_unknown", "not_analyzed")}
            if sum(counts.values()) != total:
                raise ValueError("Inconsistent factual feature coverage")
            evidence_refs = row.get("evidence_refs")
            if not isinstance(evidence_refs, list) or len(evidence_refs) != counts["present"]:
                raise ValueError("Evidence references do not match observation")
            if len(set(evidence_refs)) != len(evidence_refs) or not set(evidence_refs).issubset(source_refs):
                raise ValueError("References outside approved corpus")
            observations[group].append({"feature": feature, **counts,
                                        "evidence_refs": sorted(evidence_refs)})
    tech = observation_groups.get("technologies")
    if not isinstance(tech, list):
        raise ValueError("Invalid technologies")
    seen = set()
    safe_tech = []
    for item in tech:
        if not isinstance(item, Mapping):
            raise ValueError("Invalid technology row")
        name = item.get("technology")
        if name not in KNOWN_TECHNOLOGIES or name in seen:
            raise ValueError("Unknown/duplicate technology")
        seen.add(name)
        count = _number(item.get("websites_observed"))
        if count > total:
            raise ValueError("Inconsistent technology frequency")
        safe_tech.append({"technology": name, "websites_observed": count})
    observations["technologies"] = safe_tech

    # Questions arise from observations, never from copied competitor content.
    prompts = {
        ("page_types", "home"): "Que hierarquia e navegação originais servem a página inicial?",
        ("page_types", "service"): "Como organizar serviços em componentes próprios e reutilizáveis?",
        ("page_types", "about"): "A apresentação da entidade precisa de um modelo editorial distinto?",
        ("page_types", "contact"): "Que padrões de contacto são adequados ao objetivo do website?",
        ("conversion_features", "commercial_cta"): "Que CTA original é justificável pelo briefing do cliente?",
        ("conversion_features", "quote_request"): "Um pedido de orçamento faz sentido para o setor estudado?",
        ("quality_indicators", "missing_h1"): "Que regra de QA evita estruturas de headings incorretas?",
        ("quality_indicators", "inputs_without_labels"): "Que requisito de acessibilidade deve orientar os formulários?",
    }
    questions = [
        {"question": prompts[(group, row["feature"])],
         "supporting_evidence_refs": row["evidence_refs"],
         "basis": "observed_in_sample_not_a_design_requirement"}
        for group in ALLOWED
        for row in observations[group]
        if row["present"] > 0 and (group, row["feature"]) in prompts
    ]
    return {
        "briefing_kind": "research_evidence_discovery",
        "format_version": "designos_wrl_briefing.v0.1",
        "status": "draft_research_only",
        "synthetic_input": True,  # Contract preview only; never implies real market evidence.
        "sector_hypothesis": SECTORS[sector_key],
        "evidence_source": {"research_ref": research_ref,
                            "source_version": packet["export_version"],
                            "source_schema_version": "0.2.2",
                            "exported_at": timestamp,
                            "website_refs": source_refs},
        "sample_size": total,
        "analysis_coverage": safe_coverage,
        "observations": observations,
        "research_questions": questions,
        "design_hypotheses": [],
        "approved_design_decisions": [],
        "unknowns": [
            "O corpus é fictício e não constitui pesquisa de mercado real",
            "As observações não provam eficácia, conversão nem adequação ao cliente",
            "A existência de componentes noutros sites não autoriza cópia",
            "Definir identidade, público e objetivos num briefing próprio antes do design",
        ],
        "handoff": {"next_owner": "DesignOS", "target_stage": "discovery",
                    "generation_allowed": False, "human_review_required": True},
        "commercial_actions_authorized": False,
    }
