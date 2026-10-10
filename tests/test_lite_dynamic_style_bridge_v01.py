"""Static, fail-closed checks for Lite Dynamic CSS Bridge candidate."""
from pathlib import Path
import json
import re
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_lite_core_library_v01 import _load, build_packages, ROOT as THEME_ROOT
from scripts.build_lite_dynamic_core_v01 import (
    CSS_START, EDITOR_CSS, FRONT_CSS, PREFIX, REQUIRED_STYLES,
    build_lite_dynamic_core, validate_bridge,
)
from scripts.preflight_lite_v201_candidate import audit_candidate

try:
    from websign_vnext.validation import validate_site_document
    from websign_vnext.renderers.gutenberg import render_site_document
    from websign_vnext.tokens import TOKEN_ENUMS, token_class
except ImportError:
    validate_site_document=render_site_document=TOKEN_ENUMS=token_class=None


class LiteDynamicBridgeTests(unittest.TestCase):
    def test_zip_only_updates_two_existing_stylesheets(self):
        with TemporaryDirectory() as td:
            core=Path(td)/"original.zip"
            library=Path(td)/"library.zip"
            build_packages(ROOT,core,library)
            candidate=Path(td)/"candidate.zip"
            result=build_lite_dynamic_core(ROOT,candidate)
            self.assertEqual(result["candidate_theme_files"],16)
            self.assertEqual(result["untouched_files"],14)
            self.assertEqual(result["changed_files"],[
                "assets/css/editor.css","assets/css/global.css"])
            self.assertFalse(result["theme_functions_modified"])
            self.assertFalse(result["wordpress_runtime_tested"])
            self.assertFalse(result["release_ready"])
            before=_load(core);after=_load(candidate)
            self.assertEqual(set(before),set(after))
            for key in before:
                if key in (EDITOR_CSS,FRONT_CSS):
                    self.assertTrue(after[key].startswith(before[key].rstrip()+PREFIX),key)
                    self.assertIn(CSS_START.encode("utf-8"),after[key])
                else:
                    self.assertEqual(before[key],after[key],key)
            self.assertEqual(audit_candidate(candidate)["release_blockers"],[])
            self.assertFalse(audit_candidate(candidate)["release_ready"])

    def test_builder_reproducible(self):
        with TemporaryDirectory() as a,TemporaryDirectory() as b:
            one=Path(a)/"build.zip"
            two=Path(b)/"build.zip"
            build_lite_dynamic_core(ROOT,one)
            build_lite_dynamic_core(ROOT,two)
            self.assertEqual(one.read_bytes(),two.read_bytes())

    def test_refuse_overwrite(self):
        with TemporaryDirectory() as td:
            path=Path(td)/"prior.zip"
            path.write_bytes(b"important")
            with self.assertRaises(FileExistsError):
                build_lite_dynamic_core(ROOT,path)
            self.assertEqual(path.read_bytes(),b"important")

    def test_undefined_theme_palette_token_rejected(self):
        with TemporaryDirectory() as td:
            core=Path(td)/"core.zip";library=Path(td)/"lib.zip"
            build_packages(ROOT,core,library)
            theme=json.loads(_load(core)[THEME_ROOT+"theme.json"])
            source=(ROOT/"Templates/lite-runtime-overlay/assets/css/websign-lite-bridge.css"
                    ).read_text(encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_bridge(source.replace(
                    "--wp--preset--color--surface", "--wp--preset--color--does-not-exist"),
                    theme)

    def test_bridge_css_prohibits_remote_and_important(self):
        with TemporaryDirectory() as td:
            core=Path(td)/"core.zip";library=Path(td)/"lib.zip"
            build_packages(ROOT,core,library)
            theme=json.loads(_load(core)[THEME_ROOT+"theme.json"])
            source=(ROOT/"Templates/lite-runtime-overlay/assets/css/websign-lite-bridge.css"
                    ).read_text(encoding="utf-8")
            for unsafe in ("!important","@import url(https://untrusted.example/)",
                           "background-image:url(https://untrusted.example/x.png)"):
                with self.subTest(unsafe=unsafe):
                    with self.assertRaises(ValueError):
                        validate_bridge(source+"\n/* check */"+unsafe,theme)

    def test_all_semantic_token_selectors_covered_by_lite_bridge(self):
        if TOKEN_ENUMS is None:
            self.skipTest("Local native Websign VNext token registry not available")
        from_native={
            token_class(kind, field, value)
            for (kind,field),values in TOKEN_ENUMS.items() for value in values
        }
        self.assertEqual(from_native,REQUIRED_STYLES)

    def test_rendered_native_markup_uses_only_bridged_classes(self):
        if validate_site_document is None:
            self.skipTest("Local native Websign VNext renderer absent")
        from test_lite_site_document_selection_v01 import example_document
        document=example_document()
        document["pages"][0]["nodes"][0]["spacing"]="spacious"
        document["pages"][0]["nodes"][0]["background"]="inverse"
        document["pages"][0]["nodes"][0]["children"][0]["role"]="display"
        document["pages"][0]["nodes"][0]["children"][2]["style"]="primary"
        validate_site_document(document)
        rendered=render_site_document(document)
        classes=set(re.findall(r"websign-[a-z0-9-]+",rendered))
        self.assertTrue(classes)
        self.assertTrue(classes.issubset(REQUIRED_STYLES))
        with TemporaryDirectory() as td:
            output=Path(td)/"lite.zip"
            build_lite_dynamic_core(ROOT,output)
            files=_load(output)
            bridge=files[FRONT_CSS].decode("utf-8")
            for name in classes:
                self.assertIn("."+name,bridge)


if __name__=="__main__":unittest.main()
