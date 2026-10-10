"""Pure contract tests for the WRL EvidencePackage (no WRL installation/network)."""
import copy
import json
import unittest

from integrations.wrl.evidence_export import export_research_summary


def _coverage(total=2, *, partial=False):
    return {"analyzed": 1 if partial else total,
            "partial": 1 if partial else 0,
            "not_analyzed": 0, "total": total}


def _row(feature, *, present=1, absent=1, partial_unknown=0,
         not_analyzed=0, website_ids=None):
    return {"label": feature, "present": present, "absent": absent,
            "partial_unknown": partial_unknown, "not_analyzed": not_analyzed,
            "website_ids": [7] if website_ids is None else website_ids,
            "websites": {"present": ["PRIVATE_WEBSITE_NAME"]}}


def _summary():
    coverage = {a: _coverage() for a in (
        "identidade_contexto", "arquitetura_informacao", "tecnologia_codigo",
        "seo", "acessibilidade", "conversao_confianca")}
    coverage["conversao_confianca"] = _coverage(partial=True)
    return {
        "corpus": {
            "website_count": 2,
            "domains": [
                {"website_id": 7, "name": "PRIVATE_CLIENT", "domain": "one.example"},
                {"website_id": 8, "name": "PRIVATE_OTHER", "domain": "two.example"}],
            "coverage": coverage, "sensitive_extra": "+351 912 123 123"},
        "architecture": {"coverage": _coverage(),
                         "page_types": [_row("home", present=2, absent=0, website_ids=[7, 8])]},
        "conversion": {"coverage": _coverage(partial=True),
                       "features": [_row("commercial_cta", present=1, absent=0, partial_unknown=1)],
                       "ctas": [{"label": "PRIVATE_CTA_COPY"}]},
        "quality": {"metrics": [_row("missing_h1")],
                    "coverage": {"seo": _coverage(), "acessibilidade": _coverage()}},
        "technologies": {"items": [
            {"label": "WordPress", "count": 2, "website_names": ["PRIVATE_CLIENT"]},
            {"label": "SECRET_CUSTOM_TECH", "count": 1}]},
        "private_html": "<html>SECRET</html>",
    }


def export(summary):
    return export_research_summary(summary, research_id=9,
                                   exported_at="2026-10-10T15:00:00+01:00")


class WRLEvidenceExportContractTests(unittest.TestCase):
    def test_summary_is_read_only_with_sources_and_coverage(self):
        original = _summary()
        before = copy.deepcopy(original)
        packet = export(original)
        self.assertEqual(before, original)
        self.assertEqual(packet["export_version"], "wrl_evidence.v0.1")
        self.assertEqual(packet["corpus"]["website_count"], 2)
        self.assertEqual(packet["corpus"]["references"][0]["ref"], "WRL-WEB-000007")
        self.assertEqual(packet["corpus"]["coverage"]["conversao_confianca"]["partial"], 1)
        self.assertIsNone(packet["interpretation"])
        self.assertFalse(packet["action_authorized"])

    def test_only_safe_factual_labels_are_exported(self):
        packet = export(_summary())
        self.assertEqual(packet["observations"]["technologies"],
                         [{"technology": "WordPress", "websites_observed": 2}])
        self.assertEqual(packet["observations"]["page_types"][0]["present"], 2)
        self.assertEqual(packet["observations"]["conversion_features"][0]["partial_unknown"], 1)
        text = json.dumps(packet, ensure_ascii=False)
        for disallowed in ("PRIVATE", "SECRET", "+351", "<html", "website_names",
                           "contact_points", "sensitive_extra"):
            self.assertNotIn(disallowed, text)

    def test_corrupt_counts_rejected(self):
        s = _summary()
        s["corpus"]["coverage"]["seo"]["analyzed"] = 17
        with self.assertRaises(ValueError):
            export(s)

    def test_unsupported_labels_rejected(self):
        s = _summary()
        s["architecture"]["page_types"][0]["label"] = "fake-hero-ranking"
        with self.assertRaises(ValueError):
            export(s)

    def test_website_refs_must_match_observed_count(self):
        s = _summary()
        s["quality"]["metrics"][0]["website_ids"] = [999]
        with self.assertRaises(ValueError):
            export(s)

    def test_bad_domains_redacted(self):
        s = _summary()
        s["corpus"]["domains"][0]["domain"] = "user:password@private"
        self.assertIsNone(export(s)["corpus"]["references"][0]["domain"])

    def test_timestamp_timezone_required(self):
        with self.assertRaises(ValueError):
            export_research_summary(_summary(), research_id=9,
                                    exported_at="2026-10-10T15:00:00")

    def test_unsupported_schema_rejected(self):
        with self.assertRaises(ValueError):
            export_research_summary(_summary(), research_id=9,
                                    exported_at="2026-10-10T15:00:00Z",
                                    source_schema_version="99.0")


if __name__ == "__main__":
    unittest.main()
