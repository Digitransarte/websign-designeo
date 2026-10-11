"""SiteDocument selection: strict contract and no false publishing claims."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.site_document_lite_v01 import SCHEMA, load_document, select_patterns


def sample():
    return {"schema": SCHEMA, "pages": [{"slug": "home", "sections": [
        {"pattern": "hero"}, {"pattern": "services"}, {"pattern": "cta"}
    ]}]}


class SiteDocumentSelectionTests(unittest.TestCase):
    def test_known_order(self):
        self.assertEqual(select_patterns(sample()), ["hero", "services", "cta"])

    def test_reject_unknown_and_duplicates(self):
        for patterns in [["hero", "contact"], ["hero", "hero"], [], ["hero", 2]]:
            doc = sample()
            doc["pages"][0]["sections"] = [{"pattern": p} for p in patterns]
            with self.subTest(patterns=patterns), self.assertRaises(ValueError):
                select_patterns(doc)

    def test_reject_extra_fields_and_multiple_pages(self):
        for mutate in [
            lambda d: d.update({"publish": True}),
            lambda d: d["pages"][0]["sections"][0].update({"html": "<script>x</script>"}),
            lambda d: d["pages"].append({"slug": "about", "sections": []}),
            lambda d: d["pages"][0].update({"slug": "../admin"}),
        ]:
            doc = sample()
            mutate(doc)
            with self.assertRaises(ValueError):
                select_patterns(doc)

    def test_reject_wrong_schema_and_structure(self):
        for doc in [None, [], {}, {"schema": "future", "pages": []},
                    {"schema": SCHEMA, "pages": "home"}]:
            with self.assertRaises(ValueError):
                select_patterns(doc)

    def test_file_size_guard(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "document.json"
            path.write_text(json.dumps(sample()), encoding="utf-8")
            self.assertEqual(load_document(path), sample())
            path.write_bytes(b" " * 65537)
            with self.assertRaises(ValueError):
                load_document(path)


if __name__ == "__main__":
    unittest.main()
