import json
import tempfile
import unittest
from pathlib import Path
from scripts.build_lite_core_library_v01 import build_packages, _load, ROOT
from scripts.lite_landing_contract_v01 import apply_landing_contract

REPO=Path(__file__).resolve().parents[1]

class LandingContractTests(unittest.TestCase):
 def test_build_is_native_and_reproducible(self):
  with tempfile.TemporaryDirectory() as td:
   a,b=Path(td)/"core.zip",Path(td)/"lib.zip"
   build_packages(REPO,a,b)
   original=_load(a)
   first=apply_landing_contract(original,REPO)
   second=apply_landing_contract(original,REPO)
   self.assertEqual(first,second)
   self.assertEqual(len(first),len(original)+1)
   self.assertIn(ROOT+"templates/designeo-landing.html",first)
   self.assertIn("designeo-landing",json.loads(first[ROOT+"theme.json"])["customTemplates"][0]["name"])
   for part in ("header","footer"):
    self.assertIn('wp:site-title {"level":0,',first[ROOT+f"parts/{part}.html"].decode())
    self.assertNotEqual(first[ROOT+f"parts/{part}.html"],original[ROOT+f"parts/{part}.html"])
   for key in original:
    if key not in {ROOT+"theme.json",ROOT+"parts/header.html",ROOT+"parts/footer.html"}:
     self.assertEqual(first[key],original[key])
   with self.assertRaises(ValueError):apply_landing_contract(first,REPO)

if __name__=="__main__":unittest.main()
