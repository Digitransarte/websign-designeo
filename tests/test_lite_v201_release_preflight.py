"""Candidate release preflight: a green token test is NOT a release approval."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_lite_v201_token_aligned_candidate import build
from scripts.preflight_lite_v201_candidate import audit_candidate


class LiteReleasePreflightTests(unittest.TestCase):
    def test_normalized_candidate_still_flags_interactive_placeholders(self):
        with tempfile.TemporaryDirectory() as folder:
            zip_path=Path(folder)/"designeo-lite-v201-check.zip"
            build(ROOT,zip_path)
            result=audit_candidate(zip_path)
            self.assertFalse(result["release_ready"])
            self.assertFalse(result["wordpress_runtime_tested"])
            self.assertFalse(result["static_content_approved"])
            checks={(item["code"],item.get("path")):item["count"]
                    for item in result["release_blockers"] if "count" in item}
            self.assertEqual(checks[("buttons_without_urls", "patterns/hero.php")], 2)
            self.assertEqual(checks[("buttons_without_urls", "patterns/about.php")], 1)
            self.assertEqual(checks[("buttons_without_urls", "patterns/cta.php")], 1)
            self.assertEqual(checks[("images_without_sources", "patterns/about.php")], 1)
            self.assertFalse(any(item["code"]=="forms_with_placeholder_actions"
                                 for item in result["release_blockers"]))
            warnings={item["code"] for item in result["review_items"]}
            self.assertIn("named_font_families_not_bundled_or_loaded",warnings)
            self.assertIn("license_distribution_review_required",warnings)
            self.assertTrue(result["runtime_gates_pending"])

    def test_original_zip_has_structural_and_contact_blockers(self):
        result=audit_candidate(ROOT/"Templates/designeo-lite-v2.0.1.zip")
        codes={item["code"] for item in result["release_blockers"]}
        self.assertIn("missing_essential_file",codes)
        self.assertIn("block_theme_fallback_missing",codes)
        self.assertIn("forms_with_placeholder_actions",codes)

    def test_empty_temporary_dir_has_invalid_zip(self):
        with tempfile.TemporaryDirectory() as folder:
            fake=Path(folder)/"fake.zip"
            fake.write_bytes(b"not zip")
            with self.assertRaises(Exception):
                audit_candidate(fake)


if __name__=="__main__":
    unittest.main()
