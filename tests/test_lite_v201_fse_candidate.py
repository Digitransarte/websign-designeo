"""Static regression checks for an isolated Designeo Lite block-theme fallback ZIP."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_lite_v201_fse_candidate import build, verify_balanced_blocks


class DesigneoLiteFallbackTests(unittest.TestCase):
    def test_candidate_adds_only_index_template(self):
        with tempfile.TemporaryDirectory() as folder:
            artifact = Path(folder) / "lite-fse-candidate.zip"
            result = build(ROOT, artifact)
            self.assertEqual(result["source_files"], 20)
            self.assertEqual(result["candidate_files"], 21)
            self.assertEqual(result["added"], ["templates/index.html"])
            self.assertTrue(result["existing_files_unchanged"])
            self.assertFalse(result["wordpress_runtime_validated"])
            source = ROOT / "Templates/designeo-lite-v2.0.1.zip"
            with ZipFile(source) as z:
                before = {name:z.read(name) for name in z.namelist()
                          if not name.endswith("/")}
            with ZipFile(artifact) as z:
                after = {name:z.read(name) for name in z.namelist()}
                self.assertIsNone(z.testzip())
            path = "designeo-lite-base/templates/index.html"
            self.assertEqual(set(after), set(before) | {path})
            for name, contents in before.items():
                self.assertEqual(contents, after[name], name)
            self.assertEqual(json.loads(after["designeo-lite-base/theme.json"])["version"], 3)
            fallback = after[path].decode("utf-8")
            verify_balanced_blocks(fallback)
            self.assertIn('"inherit":true',fallback)
            self.assertIn("wp:query-no-results",fallback)
            self.assertNotIn("href=\"https://", fallback)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            existing = Path(folder) / "existing.zip"
            existing.write_bytes(b"DO NOT OVERWRITE")
            with self.assertRaises(FileExistsError):
                build(ROOT, existing)
            self.assertEqual(existing.read_bytes(), b"DO NOT OVERWRITE")

    def test_invalid_fallback_balancing_rejected(self):
        with self.assertRaises(ValueError):
            verify_balanced_blocks("<!-- wp:group --><!-- /wp:query -->")
        with self.assertRaises(ValueError):
            verify_balanced_blocks("<!-- wp:group -->")

    def test_original_archive_does_not_contain_index_html(self):
        with ZipFile(ROOT / "Templates/designeo-lite-v2.0.1.zip") as z:
            self.assertNotIn("designeo-lite-base/templates/index.html", z.namelist())


if __name__ == "__main__":
    unittest.main()
