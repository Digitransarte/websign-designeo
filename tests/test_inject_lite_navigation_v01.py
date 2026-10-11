import unittest
from scripts.inject_lite_navigation_v01 import inject_navigation
T='<!-- wp:group -->\n<!-- wp:navigation {"overlayMenu":"mobile"} -->\n<!-- wp:navigation-link {"label":"old","url":"/old","kind":"custom"} /-->\n<!-- /wp:navigation -->\n<!-- /wp:group -->'
N='<!-- wp:navigation {"overlayMenu":"mobile"} -->\n<!-- wp:navigation-link {"label":"Início","url":"/","kind":"custom"} /-->\n<!-- /wp:navigation -->\n'
class InjectNavigationTests(unittest.TestCase):
 def test_replace_only_navigation(self):
  o=inject_navigation(T,N)
  self.assertIn('Início',o)
  self.assertNotIn('/old',o)
  self.assertTrue(o.startswith('<!-- wp:group -->'))
  self.assertTrue(o.endswith('<!-- /wp:group -->'))
 def test_refuses_missing_or_multiple(self):
  with self.assertRaises(ValueError):inject_navigation('no nav',N)
  with self.assertRaises(ValueError):inject_navigation(T+T,N)
 def test_refuses_page_list(self):
  with self.assertRaises(ValueError):inject_navigation(T,N.replace('<!-- wp:navigation-link','<!-- wp:page-list').replace(' /-->',' /-->'))
if __name__=="__main__":unittest.main()
