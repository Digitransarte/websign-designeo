"""Independent tinycss2/cssselect2 cascade checks for Lite native sections."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from scripts.build_lite_core_library_v01 import _load
from scripts.build_lite_dynamic_core_v01 import FRONT_CSS,EDITOR_CSS
from scripts.audit_lite_css_cascade_v01 import (
    EXAMPLE_XML, LEGACY_XML, EXCLUSION, _first_section_rule,
    _matches_selector, audit_legacy_cascade, build_cascade_safe_core,
    parse_css, scope_first_section_css,
)


class LiteCascadeQATests(unittest.TestCase):
    def test_real_legacy_padding_conflict_and_safe_selector(self):
        with TemporaryDirectory() as td:
            target=Path(td)/"isolated.zip"
            record=build_cascade_safe_core(ROOT,target)
            self.assertTrue(record["legacy_first_section"]["legacy_conflict_reproduced"])
            self.assertTrue(record["legacy_first_section"]["dynamic_first_section_excluded"])
            self.assertTrue(record["legacy_first_section"]["legacy_first_section_still_matched"])
            self.assertEqual(record["theme_files"],16)
            self.assertEqual(record["files_untouched_over_previous"],15)
            self.assertEqual(record["file_changed_over_previous"],"assets/css/global.css")
            self.assertFalse(record["wordpress_runtime_tested"])
            self.assertFalse(record["release_ready"])

    def test_original_lite_legacy_rule_still_applies_to_plain_first_section(self):
        with TemporaryDirectory() as td:
            target=Path(td)/"theme.zip"
            build_cascade_safe_core(ROOT,target)
            files=_load(target)
            global_css=files[FRONT_CSS].decode("utf-8")
            rule=_first_section_rule(global_css)
            self.assertTrue(_matches_selector(rule.prelude,LEGACY_XML,"legacy"))
            self.assertFalse(_matches_selector(rule.prelude,EXAMPLE_XML,"dynamic"))
            self.assertIn(EXCLUSION,global_css)
            self.assertEqual(global_css.count(EXCLUSION),2)
            self.assertEqual(len(files),16)
            self.assertNotIn("designeo-lite-base/patterns/contact.php",files)

    def test_existing_css_parses_in_editor_and_front(self):
        with TemporaryDirectory() as td:
            target=Path(td)/"theme.zip"
            build_cascade_safe_core(ROOT,target)
            files=_load(target)
            self.assertGreater(len(parse_css(files[FRONT_CSS].decode("utf-8"))),50)
            self.assertGreater(len(parse_css(files[EDITOR_CSS].decode("utf-8"))),5)

    def test_source_css_rule_change_requires_review(self):
        with self.assertRaisesRegex(ValueError,"Expected exact old CSS rule"):
            scope_first_section_css(".dl-main { padding-top:0!important; }")
        with self.assertRaises(ValueError):
            scope_first_section_css(
                '.dl-main > .wp-block-group:first-child:not([class*="websign-section-spacing-"]) {padding-top:0!important;}'
            )

    def test_unchanged_editor_css_and_legacy_php_between_builds(self):
        from scripts.build_lite_dynamic_core_v01 import build_lite_dynamic_core
        with TemporaryDirectory() as td:
            old=Path(td)/"prepatch.zip"
            new=Path(td)/"scoped.zip"
            build_lite_dynamic_core(ROOT,old)
            build_cascade_safe_core(ROOT,new)
            original=_load(old)
            candidate=_load(new)
            self.assertEqual(set(original),set(candidate))
            for name in original:
                if name!=FRONT_CSS:
                    self.assertEqual(original[name],candidate[name],name)
            self.assertEqual(original[EDITOR_CSS],candidate[EDITOR_CSS])
            self.assertEqual(
                original[FRONT_CSS].count(b"!important"),
                candidate[FRONT_CSS].count(b"!important")
            )

    def test_reproducible_zip_and_no_overwrite(self):
        with TemporaryDirectory() as a,TemporaryDirectory() as b:
            a_zip=Path(a)/"core.zip"
            b_zip=Path(b)/"core.zip"
            build_cascade_safe_core(ROOT,a_zip)
            build_cascade_safe_core(ROOT,b_zip)
            self.assertEqual(a_zip.read_bytes(),b_zip.read_bytes())
            with self.assertRaises(FileExistsError):
                build_cascade_safe_core(ROOT,a_zip)

    def test_invalid_css_syntax_fails(self):
        with self.assertRaises(ValueError):
            parse_css(".test { color:var(--x);")
        with self.assertRaises(ValueError):
            parse_css(".test { color: }")


if __name__=="__main__":
    unittest.main()
