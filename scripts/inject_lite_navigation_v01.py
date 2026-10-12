"""Inject prevalidated native Gutenberg navigation into an existing template-part.

Pure function: never writes WordPress files or database.
Retains all surrounding template structure and refuses unexpected templates.
"""
from __future__ import annotations
import re

PATTERN = re.compile(r'<!-- wp:navigation \{[^\n]+\} -->[\s\S]*?<!-- /wp:navigation -->')


def inject_navigation(template: str, generated: str) -> str:
    if not isinstance(template, str) or not isinstance(generated, str):
        raise ValueError("Invalid input")
    if len(PATTERN.findall(template)) != 1:
        raise ValueError("Expected exactly one navigation block in template")
    if len(PATTERN.findall(generated)) != 1 or generated.count("<!-- /wp:navigation -->") != 1:
        raise ValueError("Expected exactly one generated navigation block")
    if "wp:page-list" in generated:
        raise ValueError("Implicit page-list is forbidden")
    return PATTERN.sub(lambda _: generated.strip(), template, count=1)
