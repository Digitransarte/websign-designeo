"""Regression for v2.0.1 pattern tokens, without installing WordPress."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_lite_v201_token_aligned_candidate import (
    audit_references, build, palette, remap_pattern, verify_balanced_blocks,
)

class LiteTokenAlignmentTests(unittest.TestCase):
    def test_packaged_candidate_contains_only_reviewed_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"lite-token-aligned.zip"
            result=build(ROOT,path)
            self.assertEqual(result["result"],"static_candidate_token_aligned_not_wp_tested")
            self.assertEqual(result["source_files"],20)
            self.assertEqual(result["candidate_files"],20)
            self.assertEqual(result["unchanged_files"],15)
            self.assertEqual(len(result["repaired_patterns"]),4)
            self.assertEqual(result["excluded_patterns"],["patterns/contact.php"])
            self.assertEqual(result["added"],["templates/index.html"])
            self.assertFalse(result["visual_approved"])
            self.assertFalse(result["wordpress_runtime_tested"])
            self.assertFalse(result["deploy_authorized"])
            with ZipFile(ROOT/"Templates/designeo-lite-v2.0.1.zip") as z:
                original={k:z.read(k) for k in z.namelist() if not k.endswith("/")}
            with ZipFile(path) as z:
                corrected={k:z.read(k) for k in z.namelist() if not k.endswith("/")}
                self.assertIsNone(z.testzip())
            self.assertNotIn("designeo-lite-base/patterns/contact.php",corrected)
            self.assertIn("designeo-lite-base/templates/index.html",corrected)
            self.assertEqual(original["designeo-lite-base/theme.json"],
                             corrected["designeo-lite-base/theme.json"])
            self.assertEqual(original["designeo-lite-base/functions.php"],
                             corrected["designeo-lite-base/functions.php"])
            for key in original:
                if not key.startswith("designeo-lite-base/patterns/"):
                    self.assertEqual(original[key],corrected[key])
            theme=json.loads(corrected["designeo-lite-base/theme.json"])
            available=palette(theme)
            for key,data in corrected.items():
                if key.startswith("designeo-lite-base/patterns/"):
                    self.assertFalse(audit_references(data.decode("utf-8"),available),key)
                    verify_balanced_blocks(data.decode("utf-8"))

    def test_common_token_mappings_preserve_physical_values(self):
        with ZipFile(ROOT/"Templates/designeo-lite-v1.1.zip") as a, ZipFile(
                ROOT/"Templates/designeo-lite-v2.0.1.zip") as b:
            source=palette(json.loads(a.read("designeo-lite/theme.json")))
            target=palette(json.loads(b.read("designeo-lite-base/theme.json")))
        content=('<!-- wp:heading {"fontSize":"4xl"} -->\n'
                 '<h2 class="has-4-xl-font-size" '
                 'style="margin-top:var(--wp--preset--spacing--8);'
                 'color:var(--wp--preset--color--texto-suave)">Text</h2>\n'
                 '<!-- /wp:heading -->')
        after=remap_pattern(content,source,target)
        self.assertIn('"fontSize":"5xl"',after)
        self.assertIn("has-5-xl-font-size",after)
        self.assertIn("--wp--preset--spacing--12",after)
        self.assertIn("--wp--preset--color--on-surface-muted",after)
        self.assertFalse(audit_references(after,target))

    def test_bad_token_fails_closed(self):
        with ZipFile(ROOT/"Templates/designeo-lite-v1.1.zip") as a,ZipFile(
                ROOT/"Templates/designeo-lite-v2.0.1.zip") as b:
            source=palette(json.loads(a.read("designeo-lite/theme.json")))
            target=palette(json.loads(b.read("designeo-lite-base/theme.json")))
        with self.assertRaises(ValueError):
            remap_pattern('<div style="color:var:preset|color|not-allowed">',source,target)

    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"existing.zip"
            out.write_bytes(b"EXISTING DATA")
            with self.assertRaises(FileExistsError):build(ROOT,out)
            self.assertEqual(out.read_bytes(),b"EXISTING DATA")

    def test_source_still_contains_nonfunctional_demo_form(self):
        with ZipFile(ROOT/"Templates/designeo-lite-v2.0.1.zip") as z:
            c=z.read("designeo-lite-base/patterns/contact.php")
            self.assertIn(b'action="#"',c)
            self.assertIn(b"<form",c)


if __name__=="__main__":
    unittest.main()
