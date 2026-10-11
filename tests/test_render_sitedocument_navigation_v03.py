import unittest
from scripts.render_sitedocument_navigation_v03 import render_site

BASE = {
 "schema": "designeo.site-document.v0.3",
 "page": {"slug":"home","blocks":[{"type":"heading","level":1,"text":"Hello"}]},
 "navigation": {"header":[{"label":"Início","url":"/"},{"label":"Serviços","url":"/#servicos"}],
                "footer":[]}
}

class NavigationContractTests(unittest.TestCase):
 def test_explicit_navigation_is_native_blocks(self):
  output=render_site(BASE)
  self.assertIn('<!-- wp:navigation-link {"label":"Início","url":"/","kind":"custom"} /-->', output["header"])
  self.assertNotIn("wp:page-list", output["header"])
  self.assertEqual(output["footer"].count("wp:navigation-link"), 0)
  self.assertIn("<!-- /wp:navigation -->",output["footer"])
  self.assertIn("wp:heading",output["page"])
 def test_unsafe_urls_rejected(self):
  for bad in ("javascript:alert(1)","//evil.example","https://user:pass@evil.example","/bad path"):
   test={**BASE,"navigation":{"header":[{"label":"Link","url":bad}],"footer":[]}}
   with self.subTest(bad=bad),self.assertRaises(ValueError):render_site(test)
 def test_unknown_fields_rejected(self):
  with self.assertRaises(ValueError):render_site({**BASE,"new_feature":True})
 def test_duplicate_links_rejected(self):
  with self.assertRaises(ValueError):render_site({**BASE,"navigation":{"header":[{"label":"a","url":"/"},{"label":"b","url":"/"}],"footer":[]}})
 def test_more_than_eight_links_rejected(self):
  with self.assertRaises(ValueError):render_site({**BASE,"navigation":{"header":[{"label":f"Link {n}","url":f"/{n}"} for n in range(9)],"footer":[]}})

if __name__=="__main__":unittest.main()
