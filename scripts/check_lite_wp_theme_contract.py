"""WEB-02 lab theme contract checks (read-only).

Run from any host with access to the theme directory:
  python3 scripts/check_lite_wp_theme_contract.py /path/to/wp-content/themes/designeo-lite-lab-v01

This prevents reintroducing a constrained landing page or site-title H1s.
"""
import json
import sys
from pathlib import Path


def check(root: Path) -> None:
    theme = json.loads((root / "theme.json").read_text())
    templates = {x["name"]: x for x in theme.get("customTemplates", [])}
    assert "designeo-landing" in templates, "Missing registered native landing template"
    assert "page" in templates["designeo-landing"]["postTypes"]
    landing = (root / "templates" / "designeo-landing.html").read_text()
    assert '"type":"default"' in landing, "Landing main must be unconstrained"
    assert "wp:post-content" in landing
    assert "wp:post-title" not in landing, "Landing must not inject page title"
    for part in ("header", "footer"):
        markup = (root / "parts" / f"{part}.html").read_text()
        assert "wp:site-title" in markup, f"Missing {part} site title"
        assert '"level":0' in markup, f"Site title must not add an H1 ({part})"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 check_lite_wp_theme_contract.py <theme_dir>")
    check(Path(sys.argv[1]))
    print("WEB02_THEME_CONTRACT=PASS")
