#!/usr/bin/env python3
"""Figma 2:2/3:2 -> existing Websign SiteDocument v0.1 -> native Gutenberg.
Pilot adapter only adds stable section classes/anchors for project-child CSS.
No changes to the neutral parent theme or Websign repository.
"""
from __future__ import annotations
import html
import json
from pathlib import Path
import re
import sys
from websign_vnext.validation import validate_site_document
from websign_vnext.renderers.gutenberg import render_site_document, _render_node
BASE=Path(__file__).resolve().parent
def leaf(t, id, **props):return {"id":id,"type":t,**props}
def block(id, nodes, *, spacing="normal", background="surface"):
    return leaf("section",id,spacing=spacing,background=background,children=nodes)
def container(id, contents, width="wide"):
    return leaf("container",id,width=width,children=contents)
def para(id,text,role="body",figma=None):
    return leaf("paragraph",id,text=text,role=role,figma_node=figma)
def heading(id,text,level=2,role="section",figma=None):
    return leaf("heading",id,text=text,level=level,role=role,figma_node=figma)
def btn(id,label,url,style="primary"):
    return leaf("button",id,label=label,url=url,style=style)
def column(id,items):return leaf("column",id,children=items)
def cols(id,left,right):
    return leaf("columns",id,gap="spacious",children=[column(id+"-left",left),column(id+"-right",right)])
N=[
block("header",[
container("header-container",[
cols("header-columns",[
para("brand","DESIGNEO","lead","2:3")],[
btn("menu-studio","ESTÚDIO","#dps-hero","secondary"),
btn("menu-services","SERVIÇOS","#dps-services","secondary"),
btn("menu-projects","PROJETOS","#dps-exercise","secondary"),
btn("menu-contact","FALAR DE UM PROJETO ↗","#dps-contact","primary")
])])],spacing="compact"),
block("hero",[
container("hero-container",[
cols("hero-columns",[
para("hero-index","DESIGNEO STUDIO   /   01","muted","2:11"),
heading("hero-heading","Design, web\n& produção\ngráfica.",1,"display","2:12"),
para("hero-kicker","Pensados em conjunto.","lead","2:14"),
para("hero-desc","Do primeiro conceito à presença digital e ao objeto físico.\nUma linguagem, vários pontos de contacto.","body","2:15"),
btn("hero-primary","EXPLORAR O TRABALHO ↗","#dps-exercise","primary"),
btn("hero-secondary","O NOSSO PROCESSO ↗","#dps-method","outline"),
],[
para("diagram-index","ESTRUTURA  /  MARCA  /  SUPORTE","muted","2:21"),
heading("diagram-display","D   01",2,"display","2:25"),
para("diagram-legends","01 / IDENTIDADE      02 / WEB      03 / PRINT","muted","2:28"),
para("diagram-footer","SISTEMA DE COMUNICAÇÃO","muted","2:31"),
])])],spacing="spacious"),
block("services",[
container("services-intro",[
para("services-index","02   /   DISCIPLINAS INTEGRADAS","muted","2:33"),
heading("services-title","Três competências.\nUma direção.",2,"section","2:34"),
para("services-lead","A estratégia e a expressão acompanham cada peça,\nindependentemente do meio.","lead","2:35")
]),
container("services-brand",[
para("services-num-1","01  ↗","muted","2:37"),
heading("services-heading-1","Identidade",3,"subsection","2:38"),
para("services-desc-1","Marcas com fundamento,\nlinguagem e reconhecimento.","body","2:39")
]),
container("services-web",[
para("services-num-2","02  ↗","muted","2:41"),
heading("services-heading-2","Web",3,"subsection","2:42"),
para("services-desc-2","Experiências digitais com\nclareza, ritmo e intenção.","body","2:43")
]),
container("services-production",[
para("services-num-3","03  ↗","muted","2:45"),
heading("services-heading-3","Produção",3,"subsection","2:46"),
para("services-desc-3","Design que chega ao papel,\nao tecido e ao espaço.","body","2:47")
]),
container("services-note",[para("services-overall","NÃO SÃO DEPARTAMENTOS. SÃO PARTE DO MESMO PROCESSO.","muted","2:48")])
]),
block("exercise",[
container("exercise-intro",[
para("exercise-index","03   /   DO CONCEITO AO OBJETO","muted","2:50"),
heading("exercise-title","Uma ideia.\nVárias expressões.",2,"section","2:51"),
para("exercise-note","ESTUDO GRÁFICO CONCEPTUAL — NÃO É UM TRABALHO DE CLIENTE","muted","2:52")
]),
container("exercise-brand",[
heading("exercise-AA","Aa",3,"display","2:56"),
para("exercise-brand-label","01    FORMA / VOZ","muted","2:57")
]),
container("exercise-web",[
heading("exercise-wireframe","WEB / UI",3,"subsection","2:58"),
para("exercise-web-label","02    ESTRUTURA / UI","muted","2:67")
]),
container("exercise-print",[
heading("exercise-print-shapes","|||||||||",3,"display","2:68"),
para("exercise-print-label","03    SUPORTE / IMPRESSÃO","muted","2:77")
]),
container("exercise-caption",[para("exercise-caption-text","A MESMA INTENÇÃO, APLICADA A SUPORTES DIFERENTES.","muted","2:78")]),
],background="inverse",spacing="spacious"),
block("method",[
container("method-intro",[
para("method-index","04   /   COMO TRABALHAMOS","muted","2:79"),
heading("method-head","Da pergunta certa\nà entrega certa.",2,"section","2:80")
]),
container("method-1",[para("method-1-n","01","muted","2:82"),heading("method-1-h","Compreender",3,"subsection","2:83")]),
container("method-2",[para("method-2-n","02","muted","2:85"),heading("method-2-h","Desenhar",3,"subsection","2:86")]),
container("method-3",[para("method-3-n","03","muted","2:88"),heading("method-3-h","Validar",3,"subsection","2:89")]),
container("method-4",[para("method-4-n","04","muted","2:91"),heading("method-4-h","Produzir",3,"subsection","2:92")]),
],spacing="spacious"),
block("contact",[
container("contact-content",[
para("contact-index","TEMOS UM PROJETO PARA CONVERSAR?","muted","2:94"),
heading("contact-title","Vamos dar-lhe forma.",2,"section","2:95"),
btn("contact-cta","INICIAR CONVERSA ↗","https://core-stage.designeo.pt/contactos/","primary"),
])],spacing="spacious",background="inverse"),
block("footer",[
container("footer-content",[
para("footer-brand","DESIGNEO     © 2026","muted","2:97"),
para("footer-place","LEIRIA · PORTUGAL","muted","2:98"),
])],spacing="none",background="inverse")
]
doc={
"schema_version":"websign.site.v0.1",
"site_id":"designeo-studio-figma-pilot-20261012",
"source":{"design_url":"https://www.figma.com/design/lC0PI3RGoX8SNuF7aOutKS","desktop_node":"2:2","mobile_node":"3:2","status":"user approved prototype transfer as test"},
"pages":[{"id":"home-pilot","slug":"designeo-studio-figma","title":"Designeo Studio — Estudo Figma → Gutenberg","nodes":N}]
}
validate_site_document(doc)
(BASE/"site-document.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n")
# baseline compiler proof (as-is output)
plain=render_site_document(doc)
(BASE/"compiled-unmodified-gutenberg.html").write_text(plain)
# Non-invasive *pilot* semantic annotation of wrapper groups for the project's child-theme CSS.
# Each wrapper is emitted by existing Websign._render_node, not hand-authored HTML.
anchors={"header":"dps-header","hero":"dps-hero","services":"dps-services","exercise":"dps-exercise","method":"dps-method","contact":"dps-contact","footer":"dps-footer"}
def annotate(section):
    rendered=_render_node(section)
    key=section["id"]
    assert key in anchors
    match=re.search(r"<!-- wp:group (\{.*?\}) -->",rendered)
    assert match,key
    original=json.loads(match.group(1))
    original["className"]=(original.get("className","")+" dps-"+key).strip()
    original["anchor"]=anchors[key]
    comment="<!-- wp:group "+json.dumps(original,ensure_ascii=False,separators=(",",":"))+" -->"
    rendered=rendered[:match.start()]+comment+rendered[match.end():]
    match=re.search(r'<div class="wp-block-group[^"]*"',rendered)
    assert match,key
    start=match.group(0)
    replacement=start[:-1]+" dps-"+key+'" id="'+anchors[key]+'"'
    rendered=rendered[:match.start()]+replacement+rendered[match.end():]
    return rendered
output="\n\n".join(annotate(x) for x in N)+"\n"
assert output.count("<!-- wp:group ")==plain.count("<!-- wp:group ")
assert output.count("<!-- wp:heading ")==plain.count("<!-- wp:heading ")
assert output.count("<!-- wp:button ")==plain.count("<!-- wp:button ")
assert output.count("<!-- wp:paragraph ")==plain.count("<!-- wp:paragraph ")
assert output.count("<!-- wp:columns ")==plain.count("<!-- wp:columns ")
assert output.count("<!-- wp:html ")==0
(BASE/"compiled-pilot-gutenberg.html").write_text(output)
manifest={"renderer":"websign_vnext.renderers.gutenberg.render_site_document",
 "source_file":"Figma desktop 2:2 mobile 3:2",
 "source_node_count":len(N),"supported_nodes":sorted({x["type"] for x in N}),
 "semantic_adapter":"additional section className/anchor only, no new block types",
 "limits":["SiteDocument v0.1 cannot represent artistic vector graphics or precision art direction",
           "3- and 4-column arrangements are styled at child-theme level since renderer only accepts 2-col",
           "editable diagram typography rendered with CSS pseudo-elements and native blocks",
           "page has scoped child CSS; no modifications to Core/theme.json global"] }
(BASE/"pipeline-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
print("SITEDOCUMENT_VALID=PASS", len(N),"sections")
print("RENDERER_REUSED=PASS",len(plain),"native Gutenberg bytes")
print("SCOPED_ADAPTER=PASS",len(output),"native Gutenberg bytes")