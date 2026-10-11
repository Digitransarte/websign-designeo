"""Experimental core Gutenberg block serializer. No WordPress writes or publishing."""
from __future__ import annotations
import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "designeo.site-document.v0.2"
MAX_INPUT_BYTES = 65536
MAX_BLOCKS = 30
SLUG = re.compile(r"^[a-z][a-z0-9-]{0,63}$")

def _text(value: object, maximum: int = 1500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError("Invalid text field")
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise ValueError("Control character")
    return html.escape(value.strip(), quote=True)

def _url(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ValueError("Invalid URL")
    if any(ord(c) < 33 or c == "\\" for c in value):
        raise ValueError("Unsafe URL")
    if value.startswith("/") and not value.startswith("//"):
        return html.escape(value, quote=True)
    parsed = urlsplit(value)
    if parsed.scheme not in ("https", "http") or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Unsupported URL")
    if not parsed.hostname or parsed.hostname.endswith(".") or not re.fullmatch(r"[A-Za-z0-9.\-:\[\]]+", parsed.netloc):
        raise ValueError("Invalid URL authority")
    return html.escape(value, quote=True)

def render(document: object) -> str:
    if not isinstance(document, dict) or set(document) != {"schema", "page"} or document["schema"] != SCHEMA:
        raise ValueError("Invalid document")
    page = document["page"]
    if not isinstance(page, dict) or set(page) != {"slug", "blocks"} or not isinstance(page["slug"], str) or not SLUG.fullmatch(page["slug"]):
        raise ValueError("Invalid page")
    blocks = page["blocks"]
    if not isinstance(blocks, list) or not 1 <= len(blocks) <= MAX_BLOCKS:
        raise ValueError("Invalid blocks")
    output = []
    count_h1 = 0
    for block in blocks:
        if not isinstance(block, dict):
            raise ValueError("Invalid block")
        if block.get("type") == "heading":
            if set(block) != {"type", "level", "text"} or type(block["level"]) is not int or block["level"] not in range(1, 7):
                raise ValueError("Invalid heading")
            level = block["level"]
            count_h1 += level == 1
            text = _text(block["text"], 200)
            output.append(f'<!-- wp:heading {{"level":{level}}} -->\n<h{level} class="wp-block-heading">{text}</h{level}>\n<!-- /wp:heading -->')
        elif block.get("type") == "paragraph":
            if set(block) != {"type", "text"}:
                raise ValueError("Invalid paragraph")
            output.append(f'<!-- wp:paragraph -->\n<p>{_text(block["text"])}</p>\n<!-- /wp:paragraph -->')
        elif block.get("type") == "button":
            if set(block) != {"type", "text", "url"}:
                raise ValueError("Invalid button")
            t, u = _text(block["text"], 100), _url(block["url"])
            output.append(f'<!-- wp:buttons -->\n<div class="wp-block-buttons">\n<!-- wp:button -->\n<div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="{u}">{t}</a></div>\n<!-- /wp:button -->\n</div>\n<!-- /wp:buttons -->')
        else:
            raise ValueError("Unsupported block")
    if count_h1 != 1:
        raise ValueError("Exactly one H1 is required")
    return "\n\n".join(output) + "\n"

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.document.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("Document too large")
    content = render(json.loads(args.document.read_text(encoding="utf-8")))
    with args.output.open("x", encoding="utf-8") as out:
        out.write(content)
    print(json.dumps({"publish_ready": False, "wordpress_runtime_tested": False, "output": str(args.output)}))

if __name__ == "__main__":
    main()
