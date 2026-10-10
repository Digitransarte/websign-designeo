"""Private-only component slot bindings, no WP, media writes or remote calls."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_lite_core_library_v01 import build_packages,LIBRARY_ROOT,_load
from scripts.lite_component_slots_v01 import (
    LiteBindingError,bind_lite_component_slots,CAPABILITIES,
)
from test_lite_site_document_selection_v01 import example_document,fake_validator


class LiteComponentSlotsTests(unittest.TestCase):
    def _manifest(self,folder):
        core=Path(folder)/"core.zip"
        library=Path(folder)/"library.zip"
        build_packages(ROOT,core,library)
        return json.loads(_load(library)[LIBRARY_ROOT+"manifest.json"])

    def test_all_four_component_slots_are_bound_without_loss(self):
        with tempfile.TemporaryDirectory() as folder:
            doc=example_document()
            previous=deepcopy(doc)
            result=bind_lite_component_slots(doc,self._manifest(folder),
                                             validate_site_document=fake_validator)
            self.assertEqual(doc,previous)
            self.assertTrue(result["all_sections_bound"])
            self.assertEqual(result["bound_sections"],4)
            self.assertEqual(result["blocked_sections"],[])
            self.assertEqual([r["pattern"] for r in result["bindings"]],
                             ["hero","cta","services","about"])
            hero,cta,services,about=[r["slots"] for r in result["bindings"]]
            self.assertEqual(hero["headline"],"TITULO_PRIVADO_NAO_EXPORTAR")
            self.assertEqual(hero["description"],"FRASE_PRIVADA_NAO_EXPORTAR")
            self.assertEqual(hero["actions"][0]["url"],"/rota-privada")
            self.assertEqual(cta["action"]["label"],"BOTAO_PRIVADO_NAO_EXPORTAR")
            self.assertEqual(len(services["items"]),2)
            self.assertEqual(services["items"][0]["title"],"TITULO_PRIVADO_NAO_EXPORTAR")
            self.assertEqual(about["image"]["src"],"/assets/privado.jpg")
            self.assertEqual(about["image"]["alt"],"DESCRICAO_PRIVADA_NAO_EXPORTAR")
            self.assertEqual(about["image_position"],"right")
            self.assertTrue(result["source_content_included"])
            self.assertFalse(result["publish_ready"])
            self.assertFalse(result["wordpress_rendering_done"])
            self.assertEqual([r["leaf_count"] for r in result["bindings"]],[3,3,4,3])
            self.assertTrue(all(not r["legacy_php_pattern_rendered"]
                                for r in result["bindings"]))

    def test_case007_image_hero_blocks_instead_of_dropping_media(self):
        with tempfile.TemporaryDirectory() as folder:
            doc=example_document()
            section=doc["pages"][0]["nodes"][0]
            section["children"]=[
                {"id":"outer","type":"container","children":[
                    {"id":"cols","type":"columns","children":[
                        {"id":"col1","type":"column","children":section["children"]},
                        {"id":"col2","type":"column","children":[
                            {"id":"image","type":"image","src":"/assets/hero.jpg","alt":"Picture"}]}
                    ]}
                ]}
            ]
            # structurally valid in native v0.1, but the Lite hero cannot accept media
            out=bind_lite_component_slots(doc,self._manifest(folder),
                                          validate_site_document=fake_validator)
            self.assertFalse(out["all_sections_bound"])
            self.assertEqual(out["blocked_sections"][0]["reason"],
                             "hero_requires_media_capability")
            self.assertEqual([r["pattern"] for r in out["bindings"]],
                             ["cta","services","about"])

    def test_too_many_buttons_is_not_truncated(self):
        with tempfile.TemporaryDirectory() as folder:
            doc=example_document()
            sec=doc["pages"][0]["nodes"][0]
            sec["children"].extend([
                {"id":"two","type":"button","label":"two","url":"/two"},
                {"id":"three","type":"button","label":"three","url":"/three"}
            ])
            out=bind_lite_component_slots(doc,self._manifest(folder),
                                          validate_site_document=fake_validator)
            self.assertFalse(out["all_sections_bound"])
            self.assertEqual(out["blocked_sections"][0]["reason"],
                             "incompatible_component_capabilities")

    def test_unsafe_button_url_is_never_bound(self):
        with tempfile.TemporaryDirectory() as folder:
            doc=example_document()
            doc["pages"][0]["nodes"][0]["children"][2]["url"]="javascript:alert(1)"
            out=bind_lite_component_slots(doc,self._manifest(folder),
                                          validate_site_document=fake_validator)
            self.assertEqual(out["blocked_sections"][0]["reason"],
                             "incompatible_component_capabilities")
            self.assertNotIn("javascript",json.dumps(out))

    def test_non_html_scheme_image_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            doc=example_document()
            img=doc["pages"][1]["nodes"][1]["children"][0]["children"][1]["children"][0]
            img["src"]="data:image/svg+xml,private"
            out=bind_lite_component_slots(doc,self._manifest(folder),
                                          validate_site_document=fake_validator)
            self.assertFalse(out["all_sections_bound"])
            self.assertEqual(out["blocked_sections"][0]["pattern"],"about")

    def test_unmatched_sections_need_review_no_pattern_invented(self):
        with tempfile.TemporaryDirectory() as folder:
            doc=example_document()
            doc["pages"][0]["nodes"].append(
                {"id":"other","type":"section","children":[
                    {"id":"other-p","type":"paragraph","text":"PRIVATE"}]})
            out=bind_lite_component_slots(doc,self._manifest(folder),
                                          validate_site_document=fake_validator)
            self.assertEqual(out["bound_sections"],4)
            self.assertEqual(out["blocked_sections"][-1]["reason"],
                             "no_supported_structural_match")
            self.assertFalse(out["all_sections_bound"])

    def test_nested_id_collision_causes_section_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            doc=example_document()
            doc["pages"][0]["nodes"][0]["children"][1]["id"]="home-h1"
            out=bind_lite_component_slots(doc,self._manifest(folder),
                                          validate_site_document=fake_validator)
            self.assertFalse(out["all_sections_bound"])
            self.assertEqual(out["blocked_sections"][0]["reason"],
                             "incompatible_component_capabilities")

    def test_link_policy_accepts_https_and_rejects_credentials_and_placeholders(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest=self._manifest(folder)
            doc=example_document()
            action=doc["pages"][0]["nodes"][0]["children"][2]
            action["url"]="https://example.org/contacto"
            ok=bind_lite_component_slots(doc,manifest,
                                         validate_site_document=fake_validator)
            self.assertEqual(ok["bindings"][0]["slots"]["actions"][0]["url"],
                             "https://example.org/contacto")
            for invalid in ("#", "//untrusted.example/a",
                            "https://user:pass@example.org/x",
                            "http://example.org", "/foo\\bar", "/some\npage"):
                with self.subTest(invalid=invalid):
                    action["url"]=invalid
                    out=bind_lite_component_slots(doc,manifest,
                                                  validate_site_document=fake_validator)
                    self.assertNotIn("hero",[r["pattern"] for r in out["bindings"]])

    def test_capability_schema_never_claims_php_dynamic_slots(self):
        for spec in CAPABILITIES.values():
            self.assertIs(spec["legacy_pattern_has_dynamic_slots"],False)

    def test_requires_native_validator_argument(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(LiteBindingError):
                bind_lite_component_slots(example_document(),self._manifest(folder),
                                          validate_site_document=None)


if __name__=="__main__":unittest.main()
