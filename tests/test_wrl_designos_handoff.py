"""Synthetic, no-network WRL → DesignOS contract test with strict provenance."""
import copy
import json
import unittest

from integrations.wrl.evidence_export import export_research_summary
from integrations.wrl.designos_adapter import prepare_designos_discovery_briefing

AREAS = ("identidade_contexto", "arquitetura_informacao", "tecnologia_codigo",
         "seo", "acessibilidade", "conversao_confianca")


def _cover(*, partial=False):
    return {"analyzed": 1 if partial else 2, "partial": 1 if partial else 0,
            "not_analyzed": 0, "total": 2}


def _row(label, *, present, absent=0, partial_unknown=0, website_ids):
    return {"label": label, "present": present, "absent": absent,
            "partial_unknown": partial_unknown, "not_analyzed": 0,
            "website_ids": website_ids,
            "websites": {"present": ["DO_NOT_EXPORT_USER_LABEL"]}}


def synthetic_summary():
    return {
        "corpus": {"website_count": 2, "domains": [
            {"website_id": 7, "name": "SECRET_INTERNAL", "domain": "site-a.example"},
            {"website_id": 8, "name": "SECRET_CLIENT", "domain": "site-b.example"}],
            "coverage": {a: _cover(partial=a == "conversao_confianca") for a in AREAS}},
        "architecture": {"coverage": _cover(), "page_types": [
            _row("home", present=2, website_ids=[7, 8]),
            _row("service", present=1, absent=1, website_ids=[7])]},
        "conversion": {"coverage": _cover(partial=True),
                       "features": [
                           _row("commercial_cta", present=1, partial_unknown=1, website_ids=[7]),
                           _row("quote_request", present=0, absent=1,
                                partial_unknown=1, website_ids=[])]},
        "quality": {"metrics": [
            _row("missing_h1", present=1, absent=1, website_ids=[8])],
            "coverage": {"seo": _cover(), "acessibilidade": _cover()}},
        "technologies": {"items": [
            {"label": "WordPress", "count": 2, "website_names": ["SECRET_INTERNAL"]}]},
        "unexpected_raw_html": "<body>SECRET_HTML</body>",
    }


def packet():
    return export_research_summary(synthetic_summary(), research_id=9,
                                   exported_at="2026-10-10T15:00:00+01:00")


def briefing():
    return prepare_designos_discovery_briefing(packet(), sector_key="wellbeing-services")


class ResearchDesignOSContractTests(unittest.TestCase):
    def test_factual_package_to_draft_briefing(self):
        source = packet()
        before = copy.deepcopy(source)
        out = prepare_designos_discovery_briefing(source, sector_key="wellbeing-services")
        self.assertEqual(source, before)
        self.assertEqual(out["format_version"], "designos_wrl_briefing.v0.1")
        self.assertTrue(out["synthetic_input"])
        self.assertEqual(out["sample_size"], 2)
        self.assertFalse(out["handoff"]["generation_allowed"])
        self.assertTrue(out["handoff"]["human_review_required"])
        self.assertFalse(out["commercial_actions_authorized"])
        self.assertEqual(len(out["approved_design_decisions"]), 0)
        self.assertEqual(out["evidence_source"]["research_ref"], "WRL-RESEARCH-000009")
        self.assertGreaterEqual(len(out["research_questions"]), 3)
        self.assertTrue(any(q["supporting_evidence_refs"] for q in out["research_questions"]))
        text = json.dumps(out, ensure_ascii=False)
        for forbidden in ("SECRET", "DO_NOT_EXPORT", "site-a.example", "<body>"):
            self.assertNotIn(forbidden, text)

    def test_missing_evidence_is_not_converted_to_absence(self):
        out = briefing()
        ctas = out["observations"]["conversion_features"]
        quote = next(r for r in ctas if r["feature"] == "quote_request")
        self.assertEqual((quote["present"], quote["absent"], quote["partial_unknown"]),
                         (0, 1, 1))

    def test_no_questions_from_unobserved_feature(self):
        out = briefing()
        self.assertFalse(any("pedido de orçamento" in q["question"].lower()
                             for q in out["research_questions"]))

    def test_provenance_from_two_sources_is_preserved(self):
        out = briefing()
        self.assertEqual(out["evidence_source"]["website_refs"],
                         ["WRL-WEB-000007", "WRL-WEB-000008"])
        home = next(r for r in out["observations"]["page_types"] if r["feature"] == "home")
        self.assertEqual(home["evidence_refs"], ["WRL-WEB-000007", "WRL-WEB-000008"])

    def test_bad_sector_rejected(self):
        with self.assertRaises(ValueError):
            prepare_designos_discovery_briefing(packet(), sector_key="inject")

    def test_unauthorized_packet_rejected(self):
        x = packet()
        x["action_authorized"] = True
        with self.assertRaises(ValueError):
            prepare_designos_discovery_briefing(x, sector_key="wellbeing-services")

    def test_preinterpreted_claim_rejected(self):
        x = packet()
        x["interpretation"] = {"claims": ["copy original design"]}
        with self.assertRaises(ValueError):
            prepare_designos_discovery_briefing(x, sector_key="wellbeing-services")

    def test_fake_evidence_ref_rejected(self):
        x = packet()
        x["observations"]["page_types"][0]["evidence_refs"] = ["WRL-WEB-123456", "WRL-WEB-000008"]
        with self.assertRaises(ValueError):
            prepare_designos_discovery_briefing(x, sector_key="wellbeing-services")

    def test_mismatched_coverage_rejected(self):
        x = packet()
        x["corpus"]["coverage"]["seo"]["not_analyzed"] = 2
        with self.assertRaises(ValueError):
            prepare_designos_discovery_briefing(x, sector_key="wellbeing-services")

    def test_duplicate_website_refs_rejected(self):
        x = packet()
        x["corpus"]["references"][1]["ref"] = "WRL-WEB-000007"
        with self.assertRaises(ValueError):
            prepare_designos_discovery_briefing(x, sector_key="wellbeing-services")

    def test_arbitrary_feature_rejected(self):
        x = packet()
        x["observations"]["page_types"][0]["feature"] = "copy-some-website"
        with self.assertRaises(ValueError):
            prepare_designos_discovery_briefing(x, sector_key="wellbeing-services")

    def test_invalid_corpus_number_rejected(self):
        x = packet()
        x["corpus"]["website_count"] = -1
        with self.assertRaises(ValueError):
            prepare_designos_discovery_briefing(x, sector_key="wellbeing-services")


if __name__ == "__main__":
    unittest.main()
