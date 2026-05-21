"""
gutenberg.py v2 — Converte conteúdo gerado pelo Claude em markup Gutenberg
alinhado com o Designeo Lite v2.0 (tokens semânticos: surface, on-surface, etc.)
"""

import html as _html


def esc(text: str) -> str:
    return _html.escape(str(text or ""), quote=False)

def _cv(slug): return f"var(--wp--preset--color--{slug})"
def _sv(slug): return f"var(--wp--preset--font-size--{slug})"
def _spv(slug): return f"var(--wp--preset--spacing--{slug})"


# ── Constantes ────────────────────────────────────────────────────────────────

BORDER_STYLE     = "border-top:0.5px solid var(--wp--preset--color--border)"
MAX_WIDTH_HERO   = "700px"
MAX_WIDTH_NARROW = "600px"
MAX_WIDTH_TEXT   = "720px"
GAP_DEFAULT      = "4"


# ── Blocos atómicos ───────────────────────────────────────────────────────────

def overline(text, class_name="dl-overline", letter_spacing="0.12em"):
    if not text: return ""
    return (
        f'<!-- wp:paragraph {{"className":"{class_name}","style":{{"color":{{"text":"var:preset|color|on-surface-muted"}},'
        f'"typography":{{"fontSize":"var:preset|font-size|xs","fontWeight":"500","letterSpacing":"{letter_spacing}","textTransform":"uppercase"}}}}}} -->\n'
        f'<p class="{class_name} has-text-color has-on-surface-muted-color" '
        f'style="color:{_cv("on-surface-muted")};font-size:{_sv("xs")};font-weight:500;letter-spacing:{letter_spacing};text-transform:uppercase">'
        f'{esc(text)}</p>\n<!-- /wp:paragraph -->'
    )

def heading(text, level=2, size="3xl", color_hex=""):
    if not text or not text.strip(): return ""
    size_class = f" has-{size}-font-size" if size else ""
    color_style = f' style="color:{color_hex}"' if color_hex else ""
    color_class = " has-text-color" if color_hex else ""
    return (
        f'<!-- wp:heading {{"level":{level}}} -->\n'
        f'<h{level} class="wp-block-heading{size_class}{color_class}"{color_style}>{esc(text)}</h{level}>\n'
        f'<!-- /wp:heading -->'
    )

def lead(text):
    if not text or not text.strip(): return ""
    return (
        '<!-- wp:paragraph {"className":"dl-lead","style":{"color":{"text":"var:preset|color|on-surface-muted"},'
        '"typography":{"fontSize":"var:preset|font-size|lg","lineHeight":"1.65"}}} -->\n'
        f'<p class="dl-lead has-text-color has-on-surface-muted-color" '
        f'style="color:{_cv("on-surface-muted")};font-size:{_sv("lg")};line-height:1.65">'
        f'{esc(text)}</p>\n<!-- /wp:paragraph -->'
    )

def body_text(text):
    if not text or not text.strip(): return ""
    return f'<!-- wp:paragraph -->\n<p>{esc(text)}</p>\n<!-- /wp:paragraph -->'

def muted_text(text):
    if not text or not text.strip(): return ""
    return (
        f'<!-- wp:paragraph {{"style":{{"color":{{"text":"var:preset|color|on-surface-muted"}}}}}} -->\n'
        f'<p class="has-text-color has-on-surface-muted-color" style="color:{_cv("on-surface-muted")}">'
        f'{esc(text)}</p>\n<!-- /wp:paragraph -->'
    )

def ul_list(items):
    if not items: return ""
    lis = "\n".join(f"<li>{esc(i)}</li>" for i in items if i)
    return f'<!-- wp:list -->\n<ul class="wp-block-list">{lis}</ul>\n<!-- /wp:list -->'

def separator():
    return '<!-- wp:separator -->\n<hr class="wp-block-separator has-alpha-channel-opacity"/>\n<!-- /wp:separator -->'

def button_primary(text, url="#"):
    return f'<!-- wp:button -->\n<div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="{esc(url)}">{esc(text)}</a></div>\n<!-- /wp:button -->'

def button_outline(text, url="#"):
    return f'<!-- wp:button {{"className":"is-style-outline"}} -->\n<div class="wp-block-button is-style-outline"><a class="wp-block-button__link wp-element-button" href="{esc(url)}">{esc(text)}</a></div>\n<!-- /wp:button -->'

def button_ghost(text, url="#"):
    return f'<!-- wp:button {{"className":"is-style-ghost"}} -->\n<div class="wp-block-button is-style-ghost"><a class="wp-block-button__link wp-element-button" href="{esc(url)}">{esc(text)}</a></div>\n<!-- /wp:button -->'

def buttons_wrap(*btns, align="left"):
    inner = "\n".join(b for b in btns if b)
    justify = f'"justifyContent":"{align}",' if align != "left" else ""
    return (
        f'<!-- wp:buttons {{"layout":{{"type":"flex",{justify}"flexWrap":"wrap"}},'
        f'"style":{{"spacing":{{"blockGap":"var:preset|spacing|2","margin":{{"top":"var:preset|spacing|5"}}}}}}}} -->\n'
        f'<div class="wp-block-buttons" style="margin-top:{_spv("5")}">\n{inner}\n</div>\n<!-- /wp:buttons -->'
    )

def inner_group(*blocks, gap="4", max_width=""):
    inner = "\n".join(b for b in blocks if b)
    width = f',"contentSize":"{max_width}"' if max_width else ""
    return (
        f'<!-- wp:group {{"style":{{"spacing":{{"blockGap":"var:preset|spacing|{gap}"}}}},'
        f'"layout":{{"type":"constrained"{width}}}}} -->\n'
        f'<div class="wp-block-group">\n{inner}\n</div>\n<!-- /wp:group -->'
    )


# ── Helpers de estrutura ──────────────────────────────────────────────────────

def section_wrapper(variant: str, inner_html: str, content_size: str = "") -> str:
    _V = {
        "hero":            ("dl-section-hero",          "surface",         "has-surface-background-color",         False),
        "surface":         ("dl-section dl-border-top", "surface",         "has-surface-background-color",         True),
        "surface-alt":     ("dl-section dl-border-top", "surface-alt",     "has-surface-alt-background-color",     True),
        "surface-inverse": ("dl-section",               "surface-inverse", "has-surface-inverse-background-color", False),
    }
    class_name, bg_slug, bg_class, has_border = _V[variant]
    cs = f',"contentSize":"{content_size}"' if content_size else ""
    border_attr = f' style="{BORDER_STYLE}"' if has_border else ""
    return (
        f'<!-- wp:group {{"align":"full","className":"{class_name}","backgroundColor":"{bg_slug}",'
        f'"layout":{{"type":"constrained"{cs}}}}} -->\n'
        f'<div class="wp-block-group alignfull {class_name} {bg_class} has-background"{border_attr}>\n'
        f'{inner_html}\n</div>\n<!-- /wp:group -->'
    )


def two_column(col_a: str, col_b: str, gap: str = GAP_DEFAULT, vertical_align: bool = False) -> str:
    va_attr = ',"verticalAlignment":"center"' if vertical_align else ""
    va_class = " are-vertically-aligned-center" if vertical_align else ""
    return (
        f'<!-- wp:columns {{"isStackedOnMobile":true{va_attr},'
        f'"style":{{"spacing":{{"blockGap":{{"left":"var:preset|spacing|{gap}"}}}}}}}} -->\n'
        f'<div class="wp-block-columns is-not-stacked-on-mobile{va_class}">\n'
        f'{col_a}\n{col_b}\n</div>\n<!-- /wp:columns -->'
    )


# ── Secções ───────────────────────────────────────────────────────────────────

def build_hero(sec):
    c = sec.get("conteudo", {})
    blocks = []
    if c.get("subheadline"): blocks.append(overline(c["subheadline"]))
    if c.get("headline"):
        blocks.append(
            f'<!-- wp:heading {{"level":1,"fontSize":"5xl"}} -->\n'
            f'<h1 class="wp-block-heading has-5-xl-font-size">{esc(c["headline"])}</h1>\n'
            f'<!-- /wp:heading -->'
        )
    if c.get("corpo"): blocks.append(lead(c["corpo"]))
    if c.get("cta_texto"):
        btns = [button_primary(c["cta_texto"])]
        if c.get("cta_nota"): btns.append(button_outline(c["cta_nota"]))
        blocks.append(buttons_wrap(*btns))
    return section_wrapper("hero", inner_group(*blocks, gap=GAP_DEFAULT, max_width=MAX_WIDTH_HERO))


def build_sobre(sec):
    c = sec.get("conteudo", {})
    nome = sec.get("nome", "Sobre nós")
    paras = [p.strip() for p in (c.get("corpo") or "").split("\n\n") if p.strip()]

    text_blocks = [overline(nome)]
    if c.get("headline"): text_blocks.append(heading(c["headline"], level=2, size="3xl"))
    for p in paras: text_blocks.append(body_text(p))
    if c.get("cta_texto"): text_blocks.append(buttons_wrap(button_ghost(c["cta_texto"])))

    text_col = (
        '<!-- wp:column {"width":"55%"} -->\n<div class="wp-block-column" style="flex-basis:55%">\n'
        + "\n".join(text_blocks) + '\n</div>\n<!-- /wp:column -->'
    )
    img_col = (
        '<!-- wp:column {"width":"45%"} -->\n<div class="wp-block-column" style="flex-basis:45%">\n'
        '<!-- wp:image {"sizeSlug":"large","style":{"border":{"radius":"4px"}}} -->\n'
        '<figure class="wp-block-image size-large" style="border-radius:4px">'
        '<img src="" alt="" style="aspect-ratio:4/5;object-fit:cover"/></figure>\n'
        '<!-- /wp:image -->\n</div>\n<!-- /wp:column -->'
    )
    return section_wrapper("surface-alt", two_column(text_col, img_col, gap="10", vertical_align=True))


def build_servicos(sec):
    c = sec.get("conteudo", {})
    nome = sec.get("nome", "Serviços")
    headline = c.get("headline", "O que fazemos.")
    items = list(c.get("lista", []))
    while len(items) < 3: items.append("Serviço — Descrição do benefício.")

    def col(num, title, desc):
        return (
            '<!-- wp:column -->\n<div class="wp-block-column">\n'
            + overline(num, class_name="dl-service-number") + "\n"
            + separator() + "\n"
            + heading(title, level=3, size="xl") + "\n"
            + muted_text(desc) +
            '\n</div>\n<!-- /wp:column -->'
        )

    cols_html = []
    for i, item in enumerate(items[:3]):
        parts = item.split(" — ", 1) if " — " in item else [item, ""]
        cols_html.append(col(f"0{i+1}", parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""))

    header = (
        f'<!-- wp:group {{"style":{{"spacing":{{"margin":{{"bottom":"var:preset|spacing|8"}}}}}},'
        f'"layout":{{"type":"constrained","contentSize":"{MAX_WIDTH_NARROW}"}}}} -->\n'
        f'<div class="wp-block-group" style="margin-bottom:{_spv("8")}">\n'
        f'{overline(nome)}\n{heading(headline, level=2, size="3xl")}\n'
        f'</div>\n<!-- /wp:group -->'
    )
    grid = (
        '<!-- wp:columns {"isStackedOnMobile":true,'
        '"style":{"spacing":{"blockGap":{"top":"var:preset|spacing|6","left":"var:preset|spacing|8"}}}} -->\n'
        '<div class="wp-block-columns is-not-stacked-on-mobile">\n'
        + "\n".join(cols_html) + '\n</div>\n<!-- /wp:columns -->'
    )
    return section_wrapper("surface", header + "\n" + grid)


def build_cta(sec):
    c = sec.get("conteudo", {})
    blocks = []
    if c.get("headline"):
        blocks.append(
            f'<!-- wp:heading {{"level":2,"textAlign":"center","fontSize":"3xl",'
            f'"style":{{"color":{{"text":"var:preset|color|on-inverse"}}}}}} -->\n'
            f'<h2 class="wp-block-heading has-text-align-center has-3-xl-font-size has-text-color has-on-inverse-color" '
            f'style="color:{_cv("on-inverse")}">{esc(c["headline"])}</h2>\n<!-- /wp:heading -->'
        )
    if c.get("corpo"):
        blocks.append(
            f'<!-- wp:paragraph {{"align":"center","style":{{"color":{{"text":"var:preset|color|on-inverse-muted"}},'
            f'"typography":{{"fontSize":"var:preset|font-size|lg","lineHeight":"1.65"}}}}}} -->\n'
            f'<p class="has-text-align-center has-text-color has-on-inverse-muted-color" '
            f'style="color:{_cv("on-inverse-muted")};font-size:{_sv("lg")};line-height:1.65">'
            f'{esc(c["corpo"])}</p>\n<!-- /wp:paragraph -->'
        )
    if c.get("cta_texto"):
        blocks.append(
            f'<!-- wp:buttons {{"layout":{{"type":"flex","justifyContent":"center"}},'
            f'"style":{{"spacing":{{"margin":{{"top":"var:preset|spacing|5"}}}}}}}} -->\n'
            f'<div class="wp-block-buttons" style="margin-top:{_spv("5")}">\n'
            f'<!-- wp:button {{"style":{{"color":{{"background":"var:preset|color|on-inverse","text":"var:preset|color|surface-inverse"}},"border":{{"radius":"2px"}}}}}} -->\n'
            f'<div class="wp-block-button"><a class="wp-block-button__link wp-element-button has-on-inverse-background-color has-surface-inverse-color has-text-color has-background" '
            f'style="color:{_cv("surface-inverse")};background-color:{_cv("on-inverse")};border-radius:2px">'
            f'{esc(c["cta_texto"])}</a></div>\n<!-- /wp:button -->\n</div>\n<!-- /wp:buttons -->'
        )
    return section_wrapper("surface-inverse", inner_group(*blocks, gap=GAP_DEFAULT, max_width=MAX_WIDTH_NARROW))


def build_contacto(sec):
    c = sec.get("conteudo", {})
    nome = sec.get("nome", "Contacto")
    paras = [p.strip() for p in (c.get("corpo") or "").split("\n\n") if p.strip()]
    lista = c.get("lista", [])

    info = [overline(nome), heading(c.get("headline", "Fala connosco."), level=2, size="3xl")]
    for p in paras[:1]: info.append(body_text(p))

    if lista:
        items_html = []
        for item in lista:
            parts = item.split(":", 1)
            label = parts[0].strip() if len(parts) > 1 else "Info"
            value = parts[1].strip() if len(parts) > 1 else item
            items_html.append(
                f'<!-- wp:group {{"style":{{"spacing":{{"blockGap":"var:preset|spacing|1"}}}}}} -->\n'
                f'<div class="wp-block-group">\n'
                f'<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"var:preset|font-size|xs","fontWeight":"500","letterSpacing":"0.1em","textTransform":"uppercase"}},"color":{{"text":"var:preset|color|on-surface-muted"}}}}}} -->\n'
                f'<p class="has-text-color has-on-surface-muted-color" style="font-size:{_sv("xs")};font-weight:500;letter-spacing:0.1em;text-transform:uppercase;color:{_cv("on-surface-muted")}">{esc(label)}</p>\n'
                f'<!-- /wp:paragraph -->\n'
                f'<!-- wp:paragraph -->\n<p>{esc(value)}</p>\n<!-- /wp:paragraph -->\n'
                f'</div>\n<!-- /wp:group -->'
            )
        info.append(
            f'<!-- wp:group {{"style":{{"spacing":{{"blockGap":"var:preset|spacing|4","margin":{{"top":"var:preset|spacing|5"}}}}}}}} -->\n'
            f'<div class="wp-block-group" style="margin-top:{_spv("5")}">\n'
            + "\n".join(items_html) + '\n</div>\n<!-- /wp:group -->'
        )

    info_col = (
        '<!-- wp:column {"width":"40%"} -->\n<div class="wp-block-column" style="flex-basis:40%">\n'
        + "\n".join(info) + '\n</div>\n<!-- /wp:column -->'
    )
    form_col = (
        '<!-- wp:column {"width":"60%"} -->\n<div class="wp-block-column" style="flex-basis:60%">\n'
        '<!-- wp:html -->\n<div class="dl-contact-form">\n<form action="#" method="post">\n'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:{_spv("5")};margin-bottom:{_spv("5")}">\n'
        f'<div><label class="dl-contact-label">Nome</label><input type="text" name="nome" required></div>\n'
        f'<div><label class="dl-contact-label">Email</label><input type="email" name="email" required></div>\n'
        f'</div>\n<div style="margin-bottom:{_spv("6")}">'
        f'<label class="dl-contact-label">Mensagem</label>'
        f'<textarea name="mensagem" rows="5" required></textarea></div>\n'
        f'<button type="submit" style="padding:12px 28px;font-size:0.75rem;font-weight:500;'
        f'letter-spacing:0.08em;text-transform:uppercase;'
        f'background:var(--wp--preset--color--on-surface);color:var(--wp--preset--color--surface);'
        f'border:none;border-radius:2px;cursor:pointer">Enviar mensagem</button>\n'
        f'</form>\n</div>\n<!-- /wp:html -->\n</div>\n<!-- /wp:column -->'
    )
    return section_wrapper("surface", two_column(info_col, form_col, gap="10"))


def build_texto(sec):
    c = sec.get("conteudo", {})
    blocks = []
    if sec.get("nome"): blocks.append(overline(sec["nome"]))
    if c.get("headline"): blocks.append(heading(c["headline"], level=2, size="2xl"))
    if c.get("subheadline"): blocks.append(lead(c["subheadline"]))
    if c.get("corpo"):
        for p in c["corpo"].split("\n\n"):
            if p.strip(): blocks.append(body_text(p.strip()))
    if c.get("lista"): blocks.append(ul_list(c["lista"]))
    if c.get("cta_texto"): blocks.append(buttons_wrap(button_primary(c["cta_texto"])))
    return section_wrapper("surface", "\n".join(b for b in blocks if b), content_size=MAX_WIDTH_TEXT)


# ── Dispatcher ────────────────────────────────────────────────────────────────

BUILDERS = {
    "hero": build_hero, "sobre": build_sobre, "about": build_sobre,
    "servicos": build_servicos, "services": build_servicos,
    "cta": build_cta, "contacto": build_contacto, "contact": build_contacto,
    "texto": build_texto, "text": build_texto,
    "faq": build_texto, "testemunho": build_texto, "galeria": build_texto,
}


def build_page_blocks(content_data: dict) -> str:
    """Converte conteúdo gerado em markup Gutenberg alinhado com Designeo Lite v2.0."""
    blocks = []
    for sec in content_data.get("secoes", []):
        tipo = (sec.get("tipo") or "texto").lower().strip()
        builder = BUILDERS.get(tipo, build_texto)
        try:
            block = builder(sec)
            if block: blocks.append(block)
        except Exception as e:
            blocks.append(f"<!-- dl:error tipo='{tipo}' msg='{esc(str(e))}' -->")
    return "\n\n".join(blocks)
