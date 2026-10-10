"""Lite Core + optional authoring pattern library: reproducible, isolated tests."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_lite_core_library_v01 import (
    ALLOWED, LIBRARY_ROOT, ROOT as THEME_ROOT,
    _load, build_packages, compose_variant,
)
from scripts.preflight_lite_v201_candidate import audit_candidate


class LiteCoreLibraryTests(unittest.TestCase):
    def _package(self, folder):
        directory = Path(folder)
        core = directory / "designeo-lite-core-preview.zip"
        library = directory / "designeo-lite-pattern-library-preview.zip"
        info = build_packages(ROOT, core, library)
        return core, library, info

    def test_core_is_valid_static_theme_without_editorial_patterns(self):
        with tempfile.TemporaryDirectory() as td:
            core, library, result = self._package(td)
            self.assertEqual(result["core_files"], 16)
            self.assertEqual(result["optional_patterns"], list(ALLOWED))
            self.assertFalse(result["release_ready"])
            entries = _load(core)
            self.assertEqual(len(entries), 16)
            self.assertNotIn("designeo-lite-base/patterns/contact.php", entries)
            self.assertFalse(any("/patterns/" in name for name in entries))
            self.assertIn("designeo-lite-base/templates/index.html", entries)
            self.assertIn("designeo-lite-base/theme.json", entries)
            report = audit_candidate(core)
            self.assertEqual(report["release_blockers"], [])
            self.assertTrue(report["static_content_approved"])
            self.assertFalse(report["release_ready"])
            self.assertFalse(report["wordpress_runtime_tested"])
            self.assertIn("named_font_families_not_bundled_or_loaded",
                          {x["code"] for x in report["review_items"]})

    def test_library_not_installable_and_has_four_declared_patterns(self):
        with tempfile.TemporaryDirectory() as td:
            core, library, result = self._package(td)
            files = _load(library)
            self.assertEqual(len(files), 5)
            self.assertFalse(any(name.endswith("theme.json") for name in files))
            self.assertEqual(result["optional_patterns"], list(ALLOWED))
            meta = json.loads(files[LIBRARY_ROOT+"manifest.json"])
            self.assertEqual(meta["schema"],"designeo.lite.library.v0.1")
            self.assertEqual(meta["distribution"],
                             "authoring_library_not_wordpress_installable")
            self.assertTrue(all(not x["publish_ready"] for x in meta["patterns"]))
            self.assertEqual({x["slug"] for x in meta["patterns"]},set(ALLOWED))
            self.assertEqual({name.split("/")[-1] for name in files
                              if name.endswith(".php")},
                             {name+".php" for name in ALLOWED})

    def test_can_assemble_two_original_pattern_combinations(self):
        with tempfile.TemporaryDirectory() as td:
            core, library, _ = self._package(td)
            examples = [
                ("preview_simple.zip", ["hero", "cta"]),
                ("preview_services.zip", ["hero", "services", "about", "cta"]),
            ]
            original = _load(core)
            for filename, selected in examples:
                with self.subTest(filename=filename):
                    target = Path(td)/filename
                    result = compose_variant(core,library,selected,target)
                    self.assertEqual(result["theme_files"], 16+len(selected))
                    self.assertFalse(result["release_ready"])
                    self.assertEqual(result["pattern_selection"], selected)
                    assembled = _load(target)
                    for key, data in original.items():
                        self.assertEqual(assembled[key],data)
                    self.assertEqual(set(assembled)-set(original),
                                     {f"{THEME_ROOT}patterns/{x}.php" for x in selected})
                    report=audit_candidate(target)
                    self.assertFalse(report["release_ready"])
                    self.assertTrue(any(x["code"] == "buttons_without_urls"
                                        for x in report["release_blockers"]))

    def test_empty_selection_is_core_only(self):
        with tempfile.TemporaryDirectory() as td:
            core, library, _ = self._package(td)
            target = Path(td)/"empty_preview.zip"
            info=compose_variant(core,library,[],target)
            self.assertEqual(_load(target),_load(core))
            self.assertFalse(info["editorial_review_needed"])

    def test_unknown_or_duplicate_component_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            core, library, _ = self._package(td)
            with self.assertRaises(ValueError):
                compose_variant(core,library,["hero","hero"],Path(td)/"dup.zip")
            with self.assertRaises(ValueError):
                compose_variant(core,library,["contact"],Path(td)/"bad.zip")
            self.assertFalse((Path(td)/"dup.zip").exists())
            self.assertFalse((Path(td)/"bad.zip").exists())

    def test_modified_pattern_blob_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            core, library, _ = self._package(td)
            files=_load(library)
            files[f"{LIBRARY_ROOT}patterns/hero.php"] += b"\n<!-- not approved -->"
            altered=Path(td)/"modified_library.zip"
            with ZipFile(altered,"w",compression=ZIP_DEFLATED) as z:
                for k, v in files.items():
                    z.writestr(k,v)
            with self.assertRaises(ValueError):
                compose_variant(core,altered,["hero"],Path(td)/"preview.zip")

    def test_repeated_builds_are_byte_for_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            core1,library1,_=self._package(a)
            core2,library2,_=self._package(b)
            self.assertEqual(core1.read_bytes(),core2.read_bytes())
            self.assertEqual(library1.read_bytes(),library2.read_bytes())

    def test_existing_artifacts_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            first=Path(td)/"immutable.zip"
            first.write_bytes(b"DO NOT REPLACE")
            with self.assertRaises(FileExistsError):
                build_packages(ROOT, first, Path(td)/"library.zip")
            self.assertEqual(first.read_bytes(),b"DO NOT REPLACE")
            self.assertFalse((Path(td)/"library.zip").exists())


if __name__=="__main__":
    unittest.main()
