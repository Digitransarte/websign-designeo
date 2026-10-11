import unittest
from scripts.render_sitedocument_home_v04 import render_home
D={"schema":"designeo.site-document.v0.4","page":{"slug":"home","sections":[
{"type":"hero","eyebrow":"Lab","title":"Design e tecnologia","body":"Páginas editáveis.","button":{"label":"Ver serviços","url":"/#servicos"}},
{"type":"services","eyebrow":"Componentes","title":"Serviços","items":[{"title":"Design","body":"Identidade visual."},{"title":"Web","body":"Gutenberg nativo."}]},
{"type":"cta","title":"Da ideia ao site","body":"Uma base reutilizável.","button":{"label":"Saber mais","url":"/#sobre"}}]}}
class HomeTests(unittest.TestCase):
 def test_native_blocks(self):
  x=render_home(D)
  for token in ('wp:group','wp:heading','wp:paragraph','wp:columns','wp:column','wp:button'):
   self.assertIn(token,x)
  self.assertEqual(x.count('<!-- wp:heading {"level":1,"fontSize":"5xl"} -->'),1)
  self.assertEqual(x.count('"fontSize":"3xl"'),2)
  self.assertIn('"fontSize":"lg"',x)
  self.assertEqual(x.count('"className":"dl-overline"'),2)
  self.assertIn('"textColor":"on-inverse"',x)
  self.assertIn('"backgroundColor":"on-inverse","textColor":"surface-inverse"',x)
  self.assertIn('has-surface-inverse-color has-text-color',x)
  self.assertIn('id="servicos"',x)
  self.assertNotIn('wp:html',x)
 def test_invalid_url_rejected(self):
  import copy
  d=copy.deepcopy(D);d["page"]["sections"][0]["button"]["url"]="javascript:evil()"
  with self.assertRaises(ValueError):render_home(d)
 def test_duplicate_or_unknown_section_rejected(self):
  import copy
  d=copy.deepcopy(D);d["page"]["sections"][1]["type"]="hero"
  with self.assertRaises(ValueError):render_home(d)
 def test_escape_untrusted_text(self):
  import copy
  d=copy.deepcopy(D);d["page"]["sections"][0]["title"]="<script>alert(1)</script>"
  result=render_home(d)
  self.assertNotIn("<script>",result)
  self.assertIn("&lt;script&gt;",result)
if __name__=="__main__":unittest.main()
