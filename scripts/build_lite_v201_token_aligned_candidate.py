"""Construct isolated Designeo Lite v2.0.1 candidate with original token references aligned.

This is an experimental static compatibility pass, NOT visual approval or
proof of Gutenberg editor/WordPress behavior.
Original ZIPs, installed WordPress sites, and other files remain untouched.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED
from scripts.build_lite_v201_fse_candidate import (
    EXPECTED_SHA256, NEW_ENTRY, OVERLAY_RELATIVE, SOURCE_RELATIVE,
    THEME_ROOT, verify_balanced_blocks,
)

# Preserve approximate intended v1.1 geometry; not a creative design decision.
# For old 12px spacing token "2", v2.x has no exact preset (8px or 16px).
COLOR = {
    "fundo": "surface", "fundo-suave": "surface-alt",
    "fundo-escuro": "surface-inverse",
    "texto": "on-surface", "texto-suave": "on-surface-muted",
    "destaque": "accent", "destaque-claro": "accent-surface",
    "borda": "border",
}
FONT_SIZE = {
    "xs": "xs", "pequeno": "sm", "base": "base", "medio": "lg",
    "grande": "xl", "xl": "2xl", "2xl": "3xl",
    "3xl": "4xl", "4xl": "5xl",
}
SPACING = {
    "1": "1", "2": "2", "3": "2", "4": "3",
    "5": "4", "6": "6", "7": "8", "8": "12", "9": "16",
}
FAMILY = {"display": "display", "corpo": "body"}
MAPPING = {"color": COLOR, "font-size": FONT_SIZE, "spacing": SPACING,
           "font-family": FAMILY}
ATTRIBUTE_KIND = {"backgroundColor": "color", "textColor": "color",
                  "fontSize": "font-size", "fontFamily": "font-family"}
TOKEN = re.compile(
    r"(?P<css>var\(--wp--preset--(?P<css_kind>color|font-size|font-family|spacing)--(?P<css_slug>[a-z0-9-]+)\))"
    r"|(?P<ref>var:preset\|(?P<ref_kind>color|font-size|font-family|spacing)\|(?P<ref_slug>[a-z0-9-]+))"
    r'|(?P<attr>"(?P<attr_name>backgroundColor|textColor|fontSize|fontFamily)":"(?P<attr_slug>[a-z0-9-]+)")'
    r"|(?P<class>has-(?P<class_slug>[a-z0-9-]+)-(?P<class_type>background-color|color|font-size|font-family))"
)
# WP renders a slug starting with a digit as has-3-xl-font-size, not has-3xl.
def from_class(value: str) -> str:
    return re.sub(r"^(\d+)-xl$", r"\1xl", value)


def as_class(value: str) -> str:
    return re.sub(r"^(\d+)xl$", r"\1-xl", value)


def palette(theme: dict) -> dict[str, set[str]]:
    s=theme.get("settings",{})
    return {"color": {a["slug"] for a in s.get("color",{}).get("palette",[])},
            "font-size": {a["slug"] for a in s.get("typography",{}).get("fontSizes",[])},
            "font-family": {a["slug"] for a in s.get("typography",{}).get("fontFamilies",[])},
            "spacing": {a["slug"] for a in s.get("spacing",{}).get("spacingSizes",[])}}


def audit_references(data: str, target: dict[str, set[str]]) -> list[str]:
    issues=[]
    for match in TOKEN.finditer(data):
        if match.group("css"):
            kind,slug=match.group("css_kind"),match.group("css_slug")
        elif match.group("ref"):
            kind,slug=match.group("ref_kind"),match.group("ref_slug")
        elif match.group("attr"):
            kind,slug=ATTRIBUTE_KIND[match.group("attr_name")],match.group("attr_slug")
        else:
            kind={"background-color":"color","color":"color",
                  "font-size":"font-size","font-family":"font-family"}[match.group("class_type")]
            slug=from_class(match.group("class_slug"))
        if slug not in target[kind]:
            issues.append(f"{kind}/{slug}")
    return sorted(set(issues))


def remap_pattern(data: str, source: dict[str,set[str]], target: dict[str,set[str]]) -> str:
    """Only token references and WP presets. Never touch free text or arbitrary CSS."""
    def replace(match: re.Match) -> str:
        if match.group("css"):
            kind,slug=match.group("css_kind"),match.group("css_slug")
            typ="css"
        elif match.group("ref"):
            kind,slug=match.group("ref_kind"),match.group("ref_slug")
            typ="ref"
        elif match.group("attr"):
            kind,slug=ATTRIBUTE_KIND[match.group("attr_name")],match.group("attr_slug")
            typ="attr"
        else:
            kind={"background-color":"color","color":"color",
                  "font-size":"font-size","font-family":"font-family"}[match.group("class_type")]
            slug=from_class(match.group("class_slug"))
            typ="class"
        if slug not in source[kind]:
            raise ValueError(f"Unexpected source {kind}/{slug}")
        new=MAPPING[kind].get(slug)
        if not new or new not in target[kind]:
            raise ValueError(f"No known target token for {kind}/{slug}")
        if typ=="css":
            return f"var(--wp--preset--{kind}--{new})"
        if typ=="ref":
            return f"var:preset|{kind}|{new}"
        if typ=="attr":
            return f'"{match.group("attr_name")}":"{new}"'
        return f"has-{as_class(new)}-{match.group('class_type')}"
    result=TOKEN.sub(replace,data)
    errors=audit_references(result,target)
    if errors:
        raise ValueError(f"Unresolved tokens: {errors}")
    return result


def build(repo: Path, output: Path) -> dict:
    repo=repo.resolve()
    output=output.resolve()
    src=repo/SOURCE_RELATIVE
    v1=repo/"Templates/designeo-lite-v1.1.zip"
    if not v1.is_file():
        raise FileNotFoundError("Reference v1.1 token definitions unavailable")
    if output.exists():
        raise FileExistsError("Refuse to overwrite candidate")
    if output==src or output==v1 or repo==output or repo in output.parents:
        raise ValueError("Output must be outside source checkout")
    if hashlib.sha256(src.read_bytes()).hexdigest()!=EXPECTED_SHA256:
        raise ValueError("Unexpected v2.0.1 input")
    with ZipFile(src) as z, ZipFile(v1) as old:
        if z.testzip() is not None or old.testzip() is not None:
            raise ValueError("Corrupt source archive")
        theme=json.loads(z.read(THEME_ROOT+"theme.json"))
        old_theme=json.loads(old.read("designeo-lite/theme.json"))
        entries={k:z.read(k) for k in z.namelist() if not k.endswith("/")}
    source_tokens=palette(old_theme)
    target_tokens=palette(theme)
    # Force mappings to be complete for all v1.1 token names used in patterns.
    patterns=[k for k in entries if k.startswith(THEME_ROOT+"patterns/") and k.endswith(".php")]
    assert len(patterns)==5
    demo_contact=THEME_ROOT+"patterns/contact.php"
    if b'action="#"' not in entries[demo_contact] or b"<form" not in entries[demo_contact]:
        raise ValueError("Contact demo changed: inspect before excluding")
    repaired={}
    before_issues={}
    for key in patterns:
        text=entries[key].decode("utf-8-sig")
        before_issues[key.split("/")[-1]]=audit_references(text,target_tokens)
        if key!=demo_contact:
            result=remap_pattern(text,source_tokens,target_tokens)
            verify_balanced_blocks(result)
            repaired[key]=result.encode("utf-8")
    if not all(before_issues.values()):
        raise ValueError("Unexpected no-drift pattern requires review")
    fallback=(repo/OVERLAY_RELATIVE).read_text(encoding="utf-8")
    verify_balanced_blocks(fallback)
    if NEW_ENTRY in entries:
        raise ValueError("Fallback already exists")
    # Candidate intentionally excludes non-functional demo form.
    out={key:value for key,value in entries.items() if key!=demo_contact}
    out.update(repaired)
    out[NEW_ENTRY]=fallback.encode("utf-8")
    if len(out)!=len(entries):
        raise ValueError("Expected 4 amended patterns, one excluded demo and one new fallback")
    for key,value in out.items():
        if key.startswith(THEME_ROOT+"patterns/"):
            issues=audit_references(value.decode("utf-8"),target_tokens)
            if issues:raise ValueError(f"{key}: {issues}")
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,"x",compression=ZIP_DEFLATED,compresslevel=9) as z:
        for name in sorted(out):
            z.writestr(name,out[name])
    with ZipFile(output) as z:
        if z.testzip() is not None:
            raise ValueError("Invalid candidate zip")
        actual={name:z.read(name) for name in z.namelist()}
    if actual!=out:raise ValueError("Packaging verification failed")
    unchanged=[k for k in entries if k in out and entries[k]==out[k]]
    if len(unchanged)!=15 or len(repaired)!=4:
        raise ValueError("Unexpected changes outside scoped overlay")
    return {
        "result":"static_candidate_token_aligned_not_wp_tested",
        "source_files":20,"candidate_files":len(out),
        "unchanged_files":len(unchanged),
        "repaired_patterns":[k.removeprefix(THEME_ROOT) for k in sorted(repaired)],
        "excluded_patterns":["patterns/contact.php"],
        "added":["templates/index.html"],
        "source_unresolved_tokens":before_issues,
        "candidate_unresolved_tokens":[],
        "candidate_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
        "output":str(output),
        "visual_approved":False,"wordpress_runtime_tested":False,
        "form_submissions_functional":False,
        "deploy_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[1],a.output),
                     indent=2,ensure_ascii=False))
if __name__=="__main__": main()
