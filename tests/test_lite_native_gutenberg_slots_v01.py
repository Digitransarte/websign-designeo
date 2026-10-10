"""Native renderer contract. Never stores client markup in GitHub or files."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_lite_core_library_v01 import build_packages,_load,LIBRARY_ROOT
from scripts.render_lite_gutenberg_preview_v01 import render_lite_gutenberg_preview
from test_lite_site_document_selection_v01 import example_document

try:
    from websign_vnext.validation import validate_site_document
    from websign_vnext.renderers.gutenberg import render_site_document
except ImportError:
    validate_site_document=None
    render_site_document=None


@unittest.skipUnless(validate_site_document and render_site_document,
                     "Native Websign VNext renderer/validator absent")
class LiteNativeGutenbergSlotTests(unittest.TestCase):
    def _manifest(self,tmp):
        core=Path(tmp)/"core.zip"
        library=Path(tmp)/"library.zip"
        build_packages(ROOT,core,library)
        return json.loads(_load(library)[LIBRARY_ROOT+"manifest.json"])

    def test_native_gutenberg_preview_preserves_content_from_four_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc=example_document()
            validate_site_document(doc)
            result=render_lite_gutenberg_preview(
                doc,self._manifest(tmp),
                validate_site_document=validate_site_document,
                render_site_document=render_site_document)
            self.assertEqual(result["status"],"native_gutenberg_private_preview")
            self.assertEqual(result["bound_sections"],4)
            self.assertEqual(result["page_count"],2)
            self.assertTrue(result["native_gutenberg_rendered"])
            self.assertFalse(result["publish_ready"])
            self.assertFalse(result["wordpress_runtime_tested"])
            self.assertFalse(result["style_parity_with_legacy_lite_patterns_verified"])
            rendered="\n".join(p["gutenberg_markup"] for p in result["pages"])
            self.assertIn("TITULO_PRIVADO_NAO_EXPORTAR",rendered)
            self.assertIn("FRASE_PRIVADA_NAO_EXPORTAR",rendered)
            self.assertIn('href="/rota-privada"',rendered)
            self.assertIn('src="/assets/privado.jpg"',rendered)
            self.assertIn("<!-- wp:columns",rendered)
            self.assertIn("<!-- wp:button",rendered)
            self.assertTrue(all(p["content_is_private"] for p in result["pages"]))
            self.assertTrue(all(not p["patterns_php_interpolated"]
                                for p in result["pages"]))

    def test_unbound_hero_media_blocks_every_page_before_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture=Path(__import__("websign_vnext").__file__).resolve().parents[1] / (
                "fixtures/vnext/case007/expected_site_document.json")
            if not fixture.exists():
                self.skipTest("Local Websign Case007 fixture unavailable")
            doc=json.loads(fixture.read_text(encoding="utf-8"))
            validate_site_document(doc)
            result=render_lite_gutenberg_preview(
                doc,self._manifest(tmp),
                validate_site_document=validate_site_document,
                render_site_document=render_site_document)
            self.assertEqual(result["status"],"blocked_no_content_rendered")
            self.assertEqual(result["blocked_sections"][0]["reason"],
                             "hero_requires_media_capability")
            self.assertFalse(result["native_gutenberg_rendered"])
            self.assertNotIn("pages",result)
            self.assertFalse(result["publish_ready"])

    def test_missing_renderer_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                render_lite_gutenberg_preview(
                    example_document(),self._manifest(tmp),
                    validate_site_document=validate_site_document,
                    render_site_document=None)


if __name__=="__main__":unittest.main()
