"""Strict tests for Gutenberg serializer (WordPress runtime still pending)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.render_sitedocument_gutenberg_v01 import SCHEMA, render, _url

def document():
    return {"schema": SCHEMA, "page": {"slug": "home", "blocks": [
        {"type": "heading", "level": 1, "text": "Olá & <Mundo>"},
        {"type": "paragraph", "text": "Serviços para pessoas."},
        {"type": "button", "text": "Ver serviços", "url": "/servicos?x=1&y=2"}]}}

class GutenbergSerializerTests(unittest.TestCase):
    def test_markup_and_escape(self):
        result = render(document())
        self.assertIn("Olá &amp; &lt;Mundo&gt;", result)
        self.assertIn("/servicos?x=1&amp;y=2", result)
        self.assertIn("<!-- wp:button -->", result)
        self.assertEqual(result, render(document()))

    def test_reject_extra_fields(self):
        d = document()
        d["page"]["blocks"][1]["html"] = "<script>x</script>"
        with self.assertRaises(ValueError): render(d)

    def test_reject_unsafe_urls(self):
        for url in ["javascript:alert(1)", "//evil.invalid", "/\\evil", "https://user:pass@host.invalid", "mailto:a@b.test", "https://a.invalid/x y", "https://evil.invalid@host.test"]:
            with self.subTest(url=url):
                d = document()
                d["page"]["blocks"][2]["url"] = url
                with self.assertRaises(ValueError): render(d)

    def test_heading_count(self):
        d = document()
        d["page"]["blocks"].append({"type": "heading", "level": 1, "text": "Duplicate"})
        with self.assertRaises(ValueError): render(d)

    def test_heading_boolean_rejected(self):
        d = document()
        d["page"]["blocks"][0]["level"] = True
        with self.assertRaises(ValueError): render(d)

    def test_unknown_block(self):
        d = document()
        d["page"]["blocks"][1] = {"type": "html", "text": "<p>x</p>"}
        with self.assertRaises(ValueError): render(d)

if __name__ == "__main__":
    unittest.main()
