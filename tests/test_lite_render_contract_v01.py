"""Regression for the fail-closed Lite Core rendering overlay."""
import unittest

from scripts.lite_render_contract_v01 import ROOT, apply_render_contract

CSS = ".entry-content a {\n  color: var(--wp--preset--color--on-surface);"


class RenderingContractTests(unittest.TestCase):
    def test_scoped_links_and_no_implicit_page_lists(self):
        core = {ROOT + "assets/css/global.css": CSS.encode()}
        for part in ("header", "footer"):
            core[ROOT + f"parts/{part}.html"] = (
                '<!-- wp:navigation {"overlayMenu":"mobile"} /-->'
            ).encode()
        output = apply_render_contract(core)
        self.assertIn(b".entry-content a:not(.wp-block-button__link)",
                      output[ROOT + "assets/css/global.css"])
        for part in ("header", "footer"):
            data = output[ROOT + f"parts/{part}.html"]
            self.assertIn(b"<!-- /wp:navigation -->", data)
            self.assertNotIn(b"<!-- wp:page-list", data)
            self.assertNotIn(b" /-->", data)

    def test_fail_closed_if_css_contract_changes(self):
        core = {ROOT + "assets/css/global.css": b"different"}
        with self.assertRaises(ValueError):
            apply_render_contract(core)

    def test_fail_closed_if_nav_is_missing(self):
        core = {ROOT + "assets/css/global.css": CSS.encode()}
        core[ROOT + "parts/header.html"] = b"no nav"
        core[ROOT + "parts/footer.html"] = b"no nav"
        with self.assertRaises(ValueError):
            apply_render_contract(core)


if __name__ == "__main__":
    unittest.main()
