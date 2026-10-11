"""WEB-02 SiteDocument v0.4: typed three-section Gutenberg homepage.

Pure serialization; no WordPress modifications. Native blocks only. Inputs are
explicit: this deliberately does not infer layout or editorial content.
"""
from __future__ import annotations
import html
import json
from scripts.render_sitedocument_gutenberg_v01 import _text, _url

SCHEMA = "designeo.site-document.v0.4"


def _paragraph(text: str, *, role: str = "normal") -> str:
    if role not in ("normal", "eyebrow", "lead", "inverse"):
        raise ValueError("Unsupported paragraph role")
    attr = {"eyebrow": {"className": "dl-overline"}, "lead": {"fontSize": "lg"}, "inverse": {"textColor": "on-inverse"}, "normal": {}}[role]
    classes = {"normal": "", "eyebrow": "dl-overline", "lead": "has-lg-font-size", "inverse": "has-on-inverse-color has-text-color"}[role]
    comment = " " + json.dumps(attr, ensure_ascii=False, separators=(",", ":")) if attr else ""
    cls = f' class="{classes}"' if classes else ""
    return f'<!-- wp:paragraph{comment} -->\n<p{cls}>{_text(text)}</p>\n<!-- /wp:paragraph -->'


def _heading(level: int, text: str, *, inverse: bool = False) -> str:
    attrs = {"level": level}
    if level in (1, 2):
        attrs["fontSize"] = "5xl" if level == 1 else "3xl"
    if inverse:
        attrs["textColor"] = "on-inverse"
    classes = ["wp-block-heading"]
    if "fontSize" in attrs:
        classes.append("has-" + attrs["fontSize"].replace("xl", "-xl") + "-font-size")
    if inverse:
        classes += ["has-on-inverse-color", "has-text-color"]
    attr_json = json.dumps(attrs, separators=(",", ":"))
    return f'<!-- wp:heading {attr_json} -->\n<h{level} class="{" ".join(classes)}">{_text(text, 200)}</h{level}>\n<!-- /wp:heading -->'


def _button(label: str, url: str, *, inverse: bool = False) -> str:
    t, u = _text(label, 100), _url(url)
    attrs = ' {"backgroundColor":"on-inverse","textColor":"surface-inverse"}' if inverse else ""
    cls = " has-on-inverse-background-color has-background has-surface-inverse-color has-text-color" if inverse else ""
    return ('<!-- wp:buttons -->\n<div class="wp-block-buttons">\n'
            f'<!-- wp:button{attrs} -->\n<div class="wp-block-button">'
            f'<a class="wp-block-button__link wp-element-button{cls}" href="{u}">{t}</a>'
            '</div>\n<!-- /wp:button -->\n</div>\n<!-- /wp:buttons -->')


def _group(body: str, *, anchor: str = "", background: str = "surface", component: str = "") -> str:
    if background not in ("surface","surface-alt","surface-inverse"):
        raise ValueError("Unknown background token")
    if component not in ("", "dl-hero", "dl-services", "dl-cta"):
        raise ValueError("Unknown component")
    classes = "dl-section" + (" " + component if component else "")
    anchor_attr = f',"anchor":"{anchor}"' if anchor else ""
    params = '{"align":"full","backgroundColor":"' + background + f'","className":"{classes}"' + anchor_attr + ',"layout":{"type":"constrained"}}'
    anchor_html = f' id="{anchor}"' if anchor else ""
    return (f'<!-- wp:group {params} -->\n'
            f'<div class="wp-block-group alignfull {classes} has-{background}-background-color has-background"{anchor_html}>\n'
            +body+'\n</div>\n<!-- /wp:group -->')


def render_home(document: object) -> str:
    if not isinstance(document,dict) or set(document)!={"schema","page"} or document["schema"]!=SCHEMA:
        raise ValueError("Invalid schema")
    page=document["page"]
    if not isinstance(page,dict) or set(page)!={"slug","sections"} or page["slug"]!="home":
        raise ValueError("Invalid page")
    sections=page["sections"]
    if not isinstance(sections,list) or len(sections)!=3 or [x.get("type") for x in sections if isinstance(x,dict)]!=["hero","services","cta"]:
        raise ValueError("Expected hero, services, cta")
    hero,services,cta=sections
    if set(hero)!={"type","eyebrow","title","body","button"} or set(services)!={"type","eyebrow","title","items"} or set(cta)!={"type","title","body","button"}:
        raise ValueError("Unexpected section fields")
    for button in (hero["button"],cta["button"]):
        if not isinstance(button,dict) or set(button)!={"label","url"}:
            raise ValueError("Invalid CTA button")
    if not isinstance(services["items"],list) or not 1<=len(services["items"])<=4:
        raise ValueError("Invalid service count")
    cols=[]
    for item in services["items"]:
        if not isinstance(item,dict) or set(item)!={"title","body"}:
            raise ValueError("Invalid service")
        cols.append('<!-- wp:column -->\n<div class="wp-block-column">\n'+_heading(3,item["title"])+'\n'+_paragraph(item["body"])+'\n</div>\n<!-- /wp:column -->')
    columns='<!-- wp:columns -->\n<div class="wp-block-columns">\n'+'\n'.join(cols)+'\n</div>\n<!-- /wp:columns -->'
    a=_group(_paragraph(hero["eyebrow"], role="eyebrow")+'\n'+_heading(1,hero["title"])+'\n'+_paragraph(hero["body"], role="lead")+'\n'+_button(**hero["button"]),background="surface",component="dl-hero")
    b=_group(_paragraph(services["eyebrow"], role="eyebrow")+'\n'+_heading(2,services["title"])+'\n'+columns,anchor="servicos",background="surface-alt",component="dl-services")
    c=_group(_heading(2,cta["title"], inverse=True)+'\n'+_paragraph(cta["body"], role="inverse")+'\n'+_button(**cta["button"], inverse=True),anchor="sobre",background="surface-inverse",component="dl-cta")
    return '\n\n'.join((a,b,c))+'\n'
