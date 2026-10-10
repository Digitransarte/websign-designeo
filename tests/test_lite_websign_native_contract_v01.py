"""Optional REAL local Websign VNext validator contract.

Skipped if the unpublished websign_vnext source is not available; isolated
Windows verification must additionally assert that these tests DO run, not skip.
"""
import json
from pathlib import Path
import unittest

from scripts.build_lite_core_library_v01 import _load, build_packages, LIBRARY_ROOT
from scripts.plan_lite_patterns_from_site_document_v01 import plan_lite_patterns

try:
    from websign_vnext.validation import validate_site_document
    import websign_vnext
except ImportError:
    validate_site_document = None
    websign_vnext = None


@unittest.skipUnless(validate_site_document is not None,
                     "Native Websign VNext validation module unavailable")
class NativeWebsignLiteTests(unittest.TestCase):
    def test_existing_case007_fixture_validates_and_suggests_hero(self):
        repo = Path(websign_vnext.__file__).resolve().parents[1]
        fixture=repo/"fixtures/vnext/case007/expected_site_document.json"
        if not fixture.exists():
            self.skipTest("Local Case007 source fixture unavailable")
        document=json.loads(fixture.read_text(encoding="utf-8"))
        validate_site_document(document)
        with __import__("tempfile").TemporaryDirectory() as td:
            core=Path(td)/"core.zip"
            library=Path(td)/"library.zip"
            build_packages(Path(__file__).resolve().parents[1],core,library)
            manifest=json.loads(_load(library)[LIBRARY_ROOT+"manifest.json"])
            plan=plan_lite_patterns(document,manifest,
                                    validate_site_document=validate_site_document)
            self.assertEqual(plan["pattern_selection"],["hero"])
            warnings=plan["pages"][0]["sections"][0]["review_warnings"]
            self.assertIn("hero_pattern_has_no_image_slot",warnings)
            self.assertFalse(plan["site_document_content_transferred_to_patterns"])
            self.assertFalse(plan["publish_ready"])

    def test_rejects_document_not_accepted_by_native_validator(self):
        invalid={
            "schema_version":"websign.site.v0.1","site_id":"synthetic",
            "pages":[{"id":"p1","slug":"home","title":"Synthetic",
                      "nodes":[{"id":"s","type":"section","children":[
                          {"id":"bad","type":"heading","level":9,"text":"Bad"}]}]}]}
        with self.assertRaises(ValueError):
            validate_site_document(invalid)


if __name__=="__main__":unittest.main()
