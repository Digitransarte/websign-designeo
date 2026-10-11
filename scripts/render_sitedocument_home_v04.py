"""WEB-02 SiteDocument v0.4: typed three-section Gutenberg homepage.

Pure serialization; no WordPress modifications. Native blocks only. Inputs are
explicit: this deliberately does not infer layout or editorial content.
"""
from __future__ import annotations
import html
import json
from scripts.render_sitedocument_gutenberg_v01 import _text, _url

SCHEMA = "designeo.site-document.v0.4"


def _paragraph(text: str) -> str:
    return f'<!-- wp:paragraph -->\n<p>{_text(text)}</p>\n<!-- /wp:paragraph -->'


def _heading(level: int, text: str) -> str:
    t = _text(text, 200)
    return f'<!-- wp:heading {{"level":{level}}} -->\n<h{level} class="wp-block-heading">{t}</h{level}>\n<!-- /wp:heading -->'


def _button(label: str, url: str) -> str:
    t,u=_text(label,100),_url(url)
    return ('<!-- wp:buttons -->\n<div class="wp-block-buttons">\n'
            '<!-- wp:button -->\n<div class="wp-block-button">'
            f'<a class="wp-block-button__link wp-element-button" href="{u}">{t}</a>'
            '</div>\n<!-- /wp:button -->\n</div>\n<!-- /wp:buttons -->')


def _group(body: str, *, anchor: str = "", background: str = "surface") -> str:
    if background not in ("surface","surface-alt","surface-inverse"):
        raise ValueError("Unknown background token")
    anchor_attr = f',"anchor":"{anchor}"' if anchor else ""
    params = '{"align":"full","backgroundColor":"' + background + '","className":"dl-section"' + anchor_attr + ',"layout":{"type":"constrained"}}'
    anchor_html = f' id="{anchor}"' if anchor else ""
    return (f'<!-- wp:group {params} -->\n'
            f'<div class="wp-block-group alignfull dl-section has-{background}-background-color has-background"{anchor_html}>\n'
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
    a=_group(_paragraph(hero["eyebrow"])+'\n'+_heading(1,hero["title"])+'\n'+_paragraph(hero["body"])+'\n'+_button(**hero["button"]),background="surface")
    b=_group(_paragraph(services["eyebrow"])+'\n'+_heading(2,services["title"])+'\n'+columns,anchor="servicos",background="surface-alt")
    c=_group(_heading(2,cta["title"])+'\n'+_paragraph(cta["body"])+'\n'+_button(**cta["button"]),anchor="sobre",background="surface-inverse")
    return '\n\n'.join((a,b,c))+'\n'
