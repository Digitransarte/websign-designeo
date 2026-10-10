"""Pure Lite-SiteDocument planning tests; native Websign validation tested separately."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_lite_core_library_v01 import build_packages, _load, LIBRARY_ROOT
from scripts.compose_lite_site_document_preview_v01 import plan_and_optionally_compose
from scripts.plan_lite_patterns_from_site_document_v01 import (
    LiteSelectionError, plan_lite_patterns,
)


def example_document():
    def text(kind, suffix, **kw):
        return {"id":suffix,"type":kind,**kw}
    def section(key,children):
        return text("section", key, children=children)
    def para(key):
        return text("paragraph",key,text="FRASE_PRIVADA_NAO_EXPORTAR")
    def heading(key,level):
        return text("heading",key,level=level,text="TITULO_PRIVADO_NAO_EXPORTAR")
    def button(key):
        return text("button",key,label="BOTAO_PRIVADO_NAO_EXPORTAR",
                    url="/rota-privada")
    def image(key):
        return text("image",key,src="/assets/privado.jpg",
                    alt="DESCRICAO_PRIVADA_NAO_EXPORTAR")
    home=[
        section("home-first",[heading("home-h1",1),para("home-p"),button("home-b")]),
        section("home-last",[heading("home-h2",2),para("home-p2"),button("home-b2")]),
    ]
    service_grid=section("services-grid",[text("container","c1",children=[
        text("columns","cols",children=[
            text("column","co1",children=[heading("s-h1",2),para("s-p1")]),
            text("column","co2",children=[heading("s-h2",2),para("s-p2")]),
        ])])])
    about=section("service-about",[text("container","c2",children=[
        text("columns","cols2",children=[
            text("column","co3",children=[heading("a-h",2),para("a-p")]),
            text("column","co4",children=[image("a-img")])
        ])])])
    return {
        "schema_version":"websign.site.v0.1",
        "site_id":"FICTITIOUS_PRIVATE_ID",
        "pages":[
            {"id":"home","slug":"home","title":"PAGINA_PRIVADA", "nodes":home},
            {"id":"services","slug":"services","title":"OUTRA_PAGINA_PRIVADA",
             "nodes":[service_grid,about]}
        ]
    }


def fake_validator(doc):
    """Unit-only sentinel; real validator is used in external integration run."""
    if doc.get("schema_version")!="websign.site.v0.1":
        raise ValueError("Bad native input")
    if not isinstance(doc.get("pages"),list):
        raise ValueError("Missing pages")


class LiteSiteDocumentSelectionTests(unittest.TestCase):
    def _assets(self,temp):
        core=Path(temp)/"core.zip"
        library=Path(temp)/"library.zip"
        build_packages(ROOT, core, library)
        manifest=json.loads(_load(library)[LIBRARY_ROOT+"manifest.json"])
        return core,library,manifest

    def test_selects_four_patterns_without_copying_content(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,manifest=self._assets(td)
            source=example_document()
            before=deepcopy(source)
            plan=plan_lite_patterns(source,manifest,
                                    validate_site_document=fake_validator)
            self.assertEqual(source,before)
            self.assertEqual(plan["pattern_selection"],
                             ["hero","cta","services","about"])
            self.assertEqual(plan["page_count"],2)
            self.assertEqual(plan["unmatched_sections"],0)
            self.assertEqual(plan["ambiguous_sections"],0)
            self.assertFalse(plan["patterns_inserted_into_wordpress_pages"])
            self.assertFalse(plan["source_text_or_assets_exported"])
            self.assertFalse(plan["publish_ready"])
            rendered=json.dumps(plan,ensure_ascii=False)
            for private in ("PRIVADO","privado","FICTITIOUS_PRIVATE_ID","/assets/"):
                self.assertNotIn(private,rendered)
            home=plan["pages"][0]["sections"]
            self.assertEqual([r["suggested_pattern"] for r in home],["hero","cta"])
            self.assertTrue(all(r["status"]=="proposal_not_inserted" for r in home))

    def test_pure_plan_composes_authoring_zip_only(self):
        with tempfile.TemporaryDirectory() as td:
            core,library,_=self._assets(td)
            output=Path(td)/"preview.zip"
            result=plan_and_optionally_compose(
                example_document(),core,library,output,validator=fake_validator)
            self.assertEqual(result["composition"]["theme_files"],20)
            self.assertEqual(result["composition"]["pattern_selection"],
                             ["hero","cta","services","about"])
            self.assertTrue(output.exists())
            self.assertFalse(result["composition"]["release_ready"])
            self.assertFalse(result["plan"]["site_document_content_transferred_to_patterns"])
            serialized=b"".join(_load(output).values())
            self.assertNotIn(b"FRASE_PRIVADA_NAO_EXPORTAR",serialized)
            self.assertNotIn(b"/rota-privada",serialized)

    def test_plan_only_writes_no_archive(self):
        with tempfile.TemporaryDirectory() as td:
            core,library,_=self._assets(td)
            result=plan_and_optionally_compose(
                example_document(),core,library,None,validator=fake_validator)
            self.assertIsNone(result["composition"])
            self.assertEqual(result["plan"]["pattern_selection"],
                             ["hero","cta","services","about"])

    def test_actual_validator_is_mandatory(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,manifest=self._assets(td)
            with self.assertRaises(LiteSelectionError):
                plan_lite_patterns(example_document(),manifest,
                                   validate_site_document=None)

    def test_validator_rejection_propagated(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,manifest=self._assets(td)
            def reject(_):raise ValueError("native schema validation failure")
            with self.assertRaisesRegex(ValueError,"native schema"):
                plan_lite_patterns(example_document(),manifest,
                                   validate_site_document=reject)

    def test_duplicate_catalog_entry_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,manifest=self._assets(td)
            manifest["patterns"].append(deepcopy(manifest["patterns"][0]))
            with self.assertRaises(LiteSelectionError):
                plan_lite_patterns(example_document(),manifest,
                                   validate_site_document=fake_validator)

    def test_incomplete_schema_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,manifest=self._assets(td)
            bad=example_document()
            bad["schema_version"]="websign.site.v10"
            with self.assertRaises(ValueError):
                plan_lite_patterns(bad,manifest,validate_site_document=fake_validator)

    def test_modified_library_digest_rejected_by_zip_composer(self):
        with tempfile.TemporaryDirectory() as td:
            core,lib,_=self._assets(td)
            modified=_load(lib)
            modified[f"{LIBRARY_ROOT}patterns/hero.php"]+=b"altered"
            bad=Path(td)/"modified.zip"
            from zipfile import ZipFile
            with ZipFile(bad,"w") as archive:
                for name,content in modified.items():
                    archive.writestr(name,content)
            with self.assertRaises(ValueError):
                plan_and_optionally_compose(example_document(),core,bad,
                                            Path(td)/"preview.zip",
                                            validator=fake_validator)

    def test_unsupported_structure_unmatched_not_invented(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,manifest=self._assets(td)
            doc=example_document()
            doc["pages"][0]["nodes"].append({
                "type":"section","id":"extra",
                "children":[{"type":"paragraph","id":"n","text":"PRIVATE"}]
            })
            plan=plan_lite_patterns(doc,manifest,validate_site_document=fake_validator)
            self.assertEqual(plan["unmatched_sections"],1)
            self.assertIsNone(plan["pages"][0]["sections"][-1]["suggested_pattern"])

    def test_ambiguity_is_not_silently_resolved(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,manifest=self._assets(td)
            doc=example_document()
            sect=doc["pages"][1]["nodes"][1]
            sect["children"][0]["children"][0]["children"].append({
                "id":"another-heading","type":"heading","level":3,"text":"PRIVATE"})
            sect["children"][0]["children"][0]["children"].append({
                "id":"another-paragraph","type":"paragraph","text":"PRIVATE"})
            plan=plan_lite_patterns(doc,manifest,validate_site_document=fake_validator)
            self.assertEqual(plan["ambiguous_sections"],1)
            self.assertEqual(plan["pages"][1]["sections"][1]["status"],
                             "human_review_required")


if __name__=="__main__":unittest.main()
