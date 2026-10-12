"""Apply the approved WEB-02 native landing template to an assembled Lite Core.

This is a pure overlay, intentionally separate from the stable WEB-01 core
builder so existing artifact contracts do not silently change.
"""
import json
from pathlib import Path

ROOT = "designeo-lite-base/"
LANDING_PATH = "wordpress/lite/templates/designeo-landing.html"


def apply_landing_contract(files: dict[str, bytes], repo: Path) -> dict[str, bytes]:
    result = dict(files)
    key = ROOT + "theme.json"
    theme = json.loads(result[key])
    templates = theme.setdefault("customTemplates", [])
    if any(t.get("name") == "designeo-landing" for t in templates):
        raise ValueError("Landing template already present: review required")
    templates.append({"name": "designeo-landing",
                      "title": "Designeo Landing · Full-width blocks",
                      "postTypes": ["page"]})
    result[key] = (json.dumps(theme, indent=2, ensure_ascii=False) + "\n").encode()
    target = ROOT + "templates/designeo-landing.html"
    if target in result:
        raise ValueError("Landing template already present")
    template = (repo / LANDING_PATH).read_bytes()
    if b'"type":"default"' not in template or b'wp:post-title' in template:
        raise ValueError("Invalid landing template")
    result[target] = template
    for part in ("header", "footer"):
        name = ROOT + f"parts/{part}.html"
        text = result[name].decode()
        needle = '<!-- wp:site-title {'
        if text.count(needle) != 1:
            raise ValueError(f"Unexpected {part} site-title")
        if '"level":' in text[text.index(needle):text.index("/-->",text.index(needle))]:
            raise ValueError(f"{part} site-title already declares level")
        result[name] = text.replace(needle, '<!-- wp:site-title {"level":0,', 1).encode()
    return result
