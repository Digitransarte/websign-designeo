"""Read-only static CSS cascade QA and isolated Designeo Lite compatibility fix.

An old Lite rule forces padding-top:0!important on the first section of a
.dl-main container. This conflicts with the Websign native dynamic section
spacing. Narrow that old rule for *dynamic* sections only, retaining it for
legacy Lite blocks. No WordPress or source ZIP changes.

Requires tinycss2 and cssselect2 for independent parse and selector matching.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import re
from xml.etree import ElementTree as ET

import cssselect2
import tinycss2
from scripts.build_lite_core_library_v01 import _load, _zip, ROOT
from scripts.build_lite_dynamic_core_v01 import build_lite_dynamic_core,FRONT_CSS,EDITOR_CSS

LEGACY_FIRST_SECTION = re.compile(
    r"(?P<prefix>\.dl-main\s*>\s*\.wp-block-post-content\s*>\s*)"
    r"\.wp-block-group:first-child"
    r"(?P<middle>\s*,\s*\.dl-main\s*>\s*)"
    r"\.wp-block-group:first-child"
    r"(?P<suffix>\s*\{\s*padding-top:\s*0\s*!important;\s*\})"
)
EXCLUSION=':not([class*="websign-section-spacing-"])'
LEGACY_CSS='assets/css/global.css'
EXAMPLE_XML = (
    '<main class="dl-main">'
    '<div class="wp-block-post-content">'
    '<div class="wp-block-group websign-section-spacing-spacious" id="dynamic"/>'
    '<div class="wp-block-group" id="next"/>'
    '</div></main>'
)
LEGACY_XML = (
    '<main class="dl-main">'
    '<div class="wp-block-post-content">'
    '<div class="wp-block-group" id="legacy"/>'
    '</div></main>'
)


def parse_css(css: str) -> list:
    without_comments=re.sub(r"/\\*.*?\\*/", "", css, flags=re.S)
    if without_comments.count("{") != without_comments.count("}"):
        raise ValueError("Unbalanced CSS braces")
    rules=tinycss2.parse_stylesheet(css,skip_comments=True,skip_whitespace=True)
    errors=[r for r in rules if r.type=="error"]
    if errors:
        raise ValueError(f"CSS syntax errors: {errors[:3]}")
    def inspect(seq):
        for node in seq:
            if node.type=="qualified-rule":
                selector_text=tinycss2.serialize(node.prelude)
                try:
                    cssselect2.compile_selector_list(node.prelude)
                except cssselect2.SelectorError as e:
                    # cssselect2 does not implement browser-specific pseudo
                    # elements; that alone is not an invalid CSS selector.
                    if "::-webkit-details-marker" not in selector_text:
                        raise ValueError("Invalid selector") from e
                declarations=tinycss2.parse_declaration_list(
                    node.content,skip_whitespace=True,skip_comments=True)
                if any(d.type=="error" or
                       (d.type=="declaration" and not d.value and
                        not d.name.startswith("--"))
                       for d in declarations):
                    raise ValueError("Invalid CSS declaration")
            elif node.type=="at-rule" and node.content is not None:
                nested=tinycss2.parse_rule_list(
                    node.content,skip_comments=True,skip_whitespace=True)
                if any(n.type=="error" for n in nested):
                    raise ValueError("Malformed @rule block")
                inspect(nested)
    inspect(rules)
    return rules


def _first_section_rule(css:str):
    matches=[r for r in parse_css(css) if
             r.type=="qualified-rule" and ".dl-main" in
             tinycss2.serialize(r.prelude) and "first-child" in
             tinycss2.serialize(r.prelude) and
             any(d.type=="declaration" and d.name=="padding-top" and d.important
                 for d in tinycss2.parse_declaration_list(r.content))]
    if len(matches)!=1:
        raise ValueError("Legacy first-section padding selector changed unexpectedly")
    return matches[0]


def _matches_selector(prelude, tree: str, elem_id:str)->bool:
    root=ET.fromstring(tree)
    selectors=cssselect2.compile_selector_list(prelude)
    wrapped=cssselect2.ElementWrapper.from_xml_root(root)
    for node in wrapped.iter_subtree():
        if node.etree_element.attrib.get("id")==elem_id:
            return any(not selector.never_matches and
                       selector.pseudo_element is None and selector.test(node)
                       for selector in selectors)
    raise AssertionError(f"Missing sample element {elem_id}")


def audit_legacy_cascade(before:str,after:str) -> dict:
    old=_first_section_rule(before)
    scoped=_first_section_rule(after)
    if not _matches_selector(old.prelude,EXAMPLE_XML,"dynamic"):
        raise ValueError("Legacy rule not reproducible against native dynamic section")
    if _matches_selector(scoped.prelude,EXAMPLE_XML,"dynamic"):
        raise ValueError("Native dynamic section still loses first-section padding")
    if not _matches_selector(scoped.prelude,LEGACY_XML,"legacy"):
        raise ValueError("Original Lite first-section behavior lost")
    if EXCLUSION not in tinycss2.serialize(scoped.prelude):
        raise ValueError("Missing explicit native section exclusion")
    return {
        "legacy_conflict_reproduced":True,
        "dynamic_first_section_excluded":True,
        "legacy_first_section_still_matched":True,
        "new_important_rules":0,
    }


def scope_first_section_css(source:str)->str:
    if EXCLUSION in source:
        raise ValueError("Legacy CSS already patched")
    match=LEGACY_FIRST_SECTION.search(source)
    if not match or len(LEGACY_FIRST_SECTION.findall(source))!=1:
        raise ValueError("Expected exact old CSS rule not found exactly once")
    replacement=(match.group("prefix")+".wp-block-group:first-child"+EXCLUSION+
                 match.group("middle")+".wp-block-group:first-child"+EXCLUSION+
                 match.group("suffix"))
    updated=source[:match.start()]+replacement+source[match.end():]
    if updated.count("!important")!=source.count("!important"):
        raise ValueError("Specificity compatibility fix added importance")
    audit_legacy_cascade(source,updated)
    return updated


def build_cascade_safe_core(repo:Path,output:Path)->dict:
    output=output.resolve()
    repo=repo.resolve()
    if output.exists():
        raise FileExistsError("Never overwrite candidate")
    if repo==output or repo in output.parents:
        raise ValueError("Build output must be outside original source checkout")
    with TemporaryDirectory(prefix="lite_cascade_") as td:
        base=Path(td)/"dynamic.zip"
        previous=build_lite_dynamic_core(repo,base)
        source=_load(base)
    unmodified_css=source[FRONT_CSS].decode("utf-8-sig")
    updated_css=scope_first_section_css(unmodified_css)
    report=audit_legacy_cascade(unmodified_css,updated_css)
    candidate={**source,FRONT_CSS:updated_css.encode("utf-8")}
    assert candidate[EDITOR_CSS]==source[EDITOR_CSS]
    if (len(candidate)!=16 or
        {name for name in source if source[name]!=candidate[name]}!={FRONT_CSS}):
        raise ValueError("Unexpected file changes")
    parse_css(candidate[FRONT_CSS].decode("utf-8"))
    parse_css(candidate[EDITOR_CSS].decode("utf-8"))
    _zip(output,candidate)
    return {
        "status":"css_cascade_static_correction_candidate",
        "theme_files":len(candidate),
        "file_changed_over_previous":"assets/css/global.css",
        "files_untouched_over_previous":15,
        "existing_importance_count":unmodified_css.count("!important"),
        "new_importance_count":updated_css.count("!important"),
        "legacy_first_section":report,
        "theme_runtime_functions_modified":False,
        "original_zip_modified":False,
        "zip_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
        "output":str(output),
        "wordpress_runtime_tested":False,
        "visual_approved":False,
        "release_ready":False,
    }


def main()->None:
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(build_cascade_safe_core(Path(__file__).resolve().parents[1],
                                             args.output),indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
