import os, json, base64, zipfile, time, re
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from gutenberg import build_page_blocks

# ─── Configuração ────────────────────────────────────────────────────────────
ANTHROPIC_API_URL  = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL    = "claude-sonnet-4-6"
PLAN_MAX_TOKENS    = 8000
CONTENT_MAX_TOKENS = 6000

CLAUDE_TIMEOUT     = 90
WP_GET_TIMEOUT     = 10
WP_POST_TIMEOUT    = 30
WP_DESIGN_TIMEOUT  = 20

FLASK_PORT         = 5050
THEME_ZIP_PATH     = Path(__file__).parent / "Templates" / "designeo-lite-v2.0.1.zip"
THEME_JSON_PATH    = "designeo-lite-base/theme.json"

# Estado de publicação no WordPress para novas páginas
# "publish" — página fica imediatamente visível no site
# "draft"   — página fica como rascunho, requer clique manual no WP
WP_DEFAULT_STATUS  = "publish"

app = Flask(__name__, static_folder=".")
CORS(app)

DATA_FILE = Path("clients.json")

# ── helpers ──────────────────────────────────────────────────────────────────

def load_clients():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []

def save_clients(clients):
    DATA_FILE.write_text(json.dumps(clients, ensure_ascii=False, indent=2), encoding="utf-8")

def find_client(clients, cid):
    return next((c for c in clients if c["id"] == cid), None)

def extract_json_from_claude(raw_text: str) -> dict:
    """
    Extrai JSON da resposta do Claude com múltiplas estratégias.
    Lança ValueError com mensagem útil se nenhuma estratégia funcionar.

    Estratégias por ordem:
    1. json.loads directo (caso o Claude tenha respondido só com JSON)
    2. find primeiro '{' e rfind último '}', tentar json.loads
    3. Mesmo recorte + remoção de control chars (U+0000-U+001F
       excepto \t \n \r), tentar json.loads
    """
    last_err = None

    # Estratégia 1: json.loads directo
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        last_err = e

    # Estratégias 2 e 3: recorte por delimitadores
    start, end = raw_text.find("{"), raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = raw_text[start:end + 1]

        # Estratégia 2: recorte directo
        try:
            return json.loads(snippet)
        except json.JSONDecodeError as e:
            last_err = e

        # Estratégia 3: recorte + remoção de control chars
        clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', snippet)
        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            last_err = e

        diag = clean[:200]
    else:
        diag = raw_text[:200]

    raise ValueError(
        f"Não foi possível extrair JSON válido da resposta. "
        f"Último erro: {last_err}. "
        f"Texto (200 chars): {diag!r}"
    )

def extract_anthropic_error(data: dict) -> "str | None":
    """
    Devolve mensagem de erro se data tiver campo 'error', senão None.
    Aceita data['error'] como dict (com 'message') ou como string.
    """
    if "error" not in data:
        return None
    err = data["error"]
    if isinstance(err, dict):
        return err.get("message", str(err))
    if isinstance(err, str):
        return err
    return str(err)

def log(tag: str, msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] [{tag}] {msg}", flush=True)

# ── static ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# ── clients CRUD ─────────────────────────────────────────────────────────────

@app.route("/api/clients", methods=["GET"])
def get_clients():
    try:
        return jsonify(load_clients())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/clients", methods=["POST"])
def create_client():
    try:
        clients = load_clients()
        data = request.json
        data["id"] = str(int(time.time() * 1000))
        data.setdefault("plan", None)
        data.setdefault("pages_content", {})
        data.setdefault("wp", {"url": "", "user": "", "password": ""})
        clients.append(data)
        save_clients(clients)
        return jsonify(data), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/clients/<cid>", methods=["PUT"])
def update_client(cid):
    try:
        clients = load_clients()
        client = find_client(clients, cid)
        if not client:
            return jsonify({"error": "not found"}), 404
        client.update(request.json)
        save_clients(clients)
        return jsonify(client)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/clients/<cid>", methods=["DELETE"])
def delete_client(cid):
    try:
        clients = load_clients()
        clients = [c for c in clients if c["id"] != cid]
        save_clients(clients)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Claude: gerar plano ───────────────────────────────────────────────────────

@app.route("/api/generate/plan", methods=["POST"])
def generate_plan():
    try:
        api_key = request.headers.get("X-Api-Key", "").strip()
        if not api_key:
            return jsonify({"error": "API key em falta"}), 400

        b = request.json or {}
        log("plan", f"start — negócio={b.get('nomeNegocio', '?')!r}")
        tipo = b.get("tipoCustom") if b.get("tipoNegocio") == "Outro" else b.get("tipoNegocio", "")

        prompt = f"""Actua como especialista em arquitectura de websites. Cria um plano completo para um website com base neste briefing:

- Nome do negócio: {b.get('nomeNegocio', '')}
- Nome do cliente: {b.get('nomeCliente', 'n/d')}
- Tipo de negócio: {tipo}
- Localização: {b.get('localizacao', '')}
- Público-alvo: {b.get('publicoAlvo', '')}
- Proposta de valor: {b.get('propostaValor', '')}
- Tom de voz: {b.get('tomVoz', '')}
- Páginas pedidas: {b.get('paginasPedidas', 'sugestão automática')}
- Funcionalidades especiais: {b.get('funcionalidades', 'nenhuma')}
- Referências: {b.get('referencias', 'não fornecidas')}

Devolve APENAS um objecto JSON válido, sem markdown:
{{
  "resumo": "Resumo estratégico em 2-3 frases",
  "paginas": [
    {{
      "id": "slug",
      "nome": "Nome",
      "descricao": "Propósito da página",
      "secoes": [{{"nome":"Nome da Secção","descricao":"O que contém e para que serve"}}],
      "copy": {{"headline":"Headline principal","tagline":"Frase de apoio","intro":"Parágrafo de introdução de 2-3 frases"}},
      "seo": {{"title":"Meta title até 60 chars","description":"Meta description até 155 chars"}},
      "ctas": ["CTA 1","CTA 2"]
    }}
  ]
}}

Gera entre 4 e 7 páginas adequadas ao negócio. Tudo em português europeu.
IMPORTANTE: O JSON deve ser válido. Não uses aspas nem apóstrofos dentro dos valores de texto — usa apenas texto simples sem caracteres especiais que possam partir o JSON."""

        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": ANTHROPIC_MODEL, "max_tokens": PLAN_MAX_TOKENS, "messages": [{"role": "user", "content": prompt}]},
            timeout=CLAUDE_TIMEOUT
        )
        data = resp.json()
        err_msg = extract_anthropic_error(data)
        if err_msg:
            return jsonify({"error": err_msg}), 500

        stop_reason = data.get("stop_reason")
        if stop_reason == "max_tokens":
            log("plan", "FAIL truncated — stop_reason=max_tokens")
            return jsonify({
                "error": (
                    "O modelo gerou uma resposta demasiado longa para o "
                    "limite actual. Tenta um briefing mais detalhado e "
                    "específico, ou contacta o administrador para aumentar "
                    "o limite de tokens."
                )
            }), 500

        raw = "".join(item.get("text", "") for item in data.get("content", []))
        try:
            result = extract_json_from_claude(raw)
            log("plan", "ok")
            return jsonify(result)
        except ValueError as e:
            log("plan", f"json-error: {str(e)[:100]}")
            return jsonify({"error": f"Erro ao processar resposta da API: {str(e)[:200]}. Tenta novamente."}), 500

    except requests.exceptions.Timeout:
        log("plan", "timeout")
        return jsonify({"error": "Timeout — a API demorou demasiado. Tenta novamente."}), 500
    except requests.exceptions.ConnectionError:
        log("plan", "connection-error")
        return jsonify({"error": "Sem ligação à API da Anthropic. Verifica a internet."}), 500
    except Exception as e:
        log("plan", f"exception: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

# ── Claude: gerar conteúdo completo de uma página ────────────────────────────

@app.route("/api/generate/page-content", methods=["POST"])
def generate_page_content():
    try:
        api_key = request.headers.get("X-Api-Key", "")
        if not api_key:
            return jsonify({"error": "API key em falta"}), 400

        body = request.json
        briefing = body.get("briefing", {})
        page = body.get("page", {})
        log("content", f"start — página={page.get('nome', '?')!r}")

        tipo = briefing.get("tipoCustom") if briefing.get("tipoNegocio") == "Outro" else briefing.get("tipoNegocio", "")

        prompt = f"""És um copywriter especialista em websites para pequenos negócios portugueses.
O conteúdo que geras vai ser publicado directamente no WordPress com o tema Designeo Lite,
um tema de blocos Gutenberg com as seguintes secções disponíveis:
- hero: página de entrada com headline grande, subtítulo e CTAs
- sobre: texto em duas colunas (texto + imagem) para apresentar o negócio
- servicos: grid de 3 serviços ou características com número e descrição
- cta: chamada à acção com fundo escuro, centrada, um botão
- contacto: informações de contacto + formulário
- texto: secção de texto corrido para qualquer outro conteúdo

Contexto do negócio:
- Nome: {briefing.get('nomeNegocio', '')}
- Tipo: {tipo}
- Localização: {briefing.get('localizacao', '')}
- Público-alvo: {briefing.get('publicoAlvo', '')}
- Proposta de valor: {briefing.get('propostaValor', '')}
- Tom de voz: {briefing.get('tomVoz', '')}

Página a desenvolver: {page.get('nome', '')}
Propósito: {page.get('descricao', '')}
Secções planeadas: {json.dumps(page.get('secoes', []), ensure_ascii=False)}
Copy de arranque: {json.dumps(page.get('copy', {}), ensure_ascii=False)}

Devolve APENAS JSON válido, sem markdown:
{{
  "titulo": "Título da página para o WordPress",
  "meta_title": "SEO title final (max 60 chars)",
  "meta_description": "SEO description final (max 155 chars)",
  "secoes": [
    {{
      "nome": "Nome da secção",
      "tipo": "hero|sobre|servicos|cta|contacto|texto",
      "conteudo": {{
        "headline": "Headline principal da secção",
        "subheadline": "Para hero: eyebrow (ex: Loja · Leiria). Para texto: subtítulo de apoio",
        "corpo": "Texto completo. Para hero: 1 frase de impacto. Para sobre/texto: 2-3 parágrafos separados por \\n\\n",
        "lista": ["Para servicos: 'Título do serviço — Descrição do benefício'. Máx 3 items.",
                  "Para contacto: 'Email: geral@negocio.pt', 'Tel: 244 000 000'"],
        "cta_texto": "Texto do botão principal",
        "cta_nota": "Texto do botão secundário (só para hero)"
      }}
    }}
  ],
  "notas_wp": "Notas de implementação: imagens necessárias, plugins recomendados, etc."
}}

Tom: {briefing.get('tomVoz', 'profissional')}. Português europeu. Conteúdo real e completo."""

        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": ANTHROPIC_MODEL, "max_tokens": CONTENT_MAX_TOKENS, "messages": [{"role": "user", "content": prompt}]},
            timeout=CLAUDE_TIMEOUT
        )
        data = resp.json()
        err_msg = extract_anthropic_error(data)
        if err_msg:
            return jsonify({"error": err_msg}), 500

        stop_reason = data.get("stop_reason")
        if stop_reason == "max_tokens":
            log("content", "FAIL truncated — stop_reason=max_tokens")
            return jsonify({
                "error": (
                    "O modelo gerou uma resposta demasiado longa para o "
                    "limite actual. Tenta um briefing mais detalhado e "
                    "específico, ou contacta o administrador para aumentar "
                    "o limite de tokens."
                )
            }), 500

        raw = "".join(b.get("text", "") for b in data.get("content", []))
        try:
            result = extract_json_from_claude(raw)
            log("content", "ok")
            return jsonify(result)
        except ValueError as e:
            log("content", f"json-error: {str(e)[:100]}")
            return jsonify({"error": f"Erro ao processar resposta da API: {str(e)[:200]}. Tenta novamente."}), 500

    except requests.exceptions.Timeout:
        log("content", "timeout")
        return jsonify({"error": "Timeout — a API demorou demasiado. Tenta novamente."}), 500
    except requests.exceptions.ConnectionError:
        log("content", "connection-error")
        return jsonify({"error": "Sem ligação à API da Anthropic. Verifica a internet."}), 500
    except Exception as e:
        log("content", f"exception: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

# ── WordPress: testar ligação ─────────────────────────────────────────────────

@app.route("/api/wp/test", methods=["POST"])
def wp_test():
    body = request.json
    url = body.get("url", "").rstrip("/")
    user = body.get("user", "")
    password = body.get("password", "")

    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    try:
        resp = requests.get(
            f"{url}/wp-json/wp/v2/users/me",
            headers={"Authorization": f"Basic {token}"},
            timeout=WP_GET_TIMEOUT
        )
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({"ok": True, "name": data.get("name", user), "roles": data.get("roles", [])})
        return jsonify({"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ── WordPress: criar/actualizar página ───────────────────────────────────────

@app.route("/api/wp/push-page", methods=["POST"])
def wp_push_page():
    body = request.json
    wp = body.get("wp", {})
    page_data = body.get("page", {})
    content_data = body.get("content", {})

    url = wp.get("url", "").rstrip("/")
    user = wp.get("user", "")
    password = wp.get("password", "")
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    wp_status = wp.get("status") or WP_DEFAULT_STATUS
    if wp_status not in ("publish", "draft", "private"):
        wp_status = WP_DEFAULT_STATUS

    log("push", f"start — slug={page_data.get('id', '?')!r} wp_page_id={page_data.get('wp_page_id')} status={wp_status}")

    # Gera markup Gutenberg real a partir do conteúdo
    try:
        gutenberg_content = build_page_blocks(content_data)
    except Exception as e:
        return jsonify({"error": f"Falha a gerar markup Gutenberg: {e}"}), 500

    payload_update = {
        "title":   content_data.get("titulo", page_data.get("nome", "")),
        "content": gutenberg_content,
        "slug":    page_data.get("id", ""),
        "meta": {
            "_yoast_wpseo_title":    content_data.get("meta_title", ""),
            "_yoast_wpseo_metadesc": content_data.get("meta_description", ""),
            # Rank Math
            "rank_math_title":       content_data.get("meta_title", ""),
            "rank_math_description": content_data.get("meta_description", ""),
        }
    }
    payload_create = {**payload_update, "status": wp_status}

    # ── PRIORIDADE 1: wp_page_id conhecido ───────────────────────────────────
    known_id = page_data.get("wp_page_id")
    if known_id:
        try:
            check = requests.get(
                f"{url}/wp-json/wp/v2/pages/{known_id}",
                headers=headers, timeout=WP_GET_TIMEOUT,
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            return jsonify({"error": f"Não foi possível verificar página WP#{known_id}: {e}"}), 502

        if check.status_code == 200:
            try:
                resp = requests.post(
                    f"{url}/wp-json/wp/v2/pages/{known_id}",
                    headers=headers, json=payload_update, timeout=WP_POST_TIMEOUT,
                )
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 500
            if resp.status_code in (200, 201):
                result = resp.json()
                pid = result.get("id")
                log("push", f"P1 actualizada — WP#{pid}")
                return jsonify({
                    "ok": True, "action": "actualizada",
                    "page_id": pid, "link": result.get("link"),
                    "edit_link": f"{url}/wp-admin/post.php?post={pid}&action=edit",
                })
            log("push", f"P1 error: HTTP {resp.status_code}")
            return jsonify({"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}), 400
        elif check.status_code != 404:
            log("push", f"P1 verify-error: HTTP {check.status_code}")
            return jsonify({"error": f"Erro a verificar página WP#{known_id}: HTTP {check.status_code}"}), 502
        # 404: cliente apagou a página no WP, cai para prioridade 2
        log("push", f"P1 WP#{known_id} 404 → fallback P2")

    # ── PRIORIDADE 2: slug-check ──────────────────────────────────────────────
    try:
        slug_resp = requests.get(
            f"{url}/wp-json/wp/v2/pages?slug={page_data.get('id', '')}",
            headers=headers, timeout=WP_GET_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        return jsonify({"error": "Não foi possível verificar se a página já existe: timeout"}), 502
    except requests.exceptions.ConnectionError as e:
        return jsonify({"error": f"Não foi possível verificar se a página já existe: {e}"}), 502

    if slug_resp.status_code != 200:
        return jsonify({"error": f"Não foi possível verificar se a página já existe: HTTP {slug_resp.status_code}"}), 502

    try:
        existing = slug_resp.json()
    except Exception:
        return jsonify({"error": "Não foi possível verificar se a página já existe: resposta não é JSON válido"}), 502

    if not isinstance(existing, list):
        return jsonify({"error": "Não foi possível verificar se a página já existe: resposta inesperada do WordPress"}), 502

    try:
        if existing and isinstance(existing, list) and len(existing) > 0:
            page_id = existing[0]["id"]
            resp = requests.post(f"{url}/wp-json/wp/v2/pages/{page_id}", headers=headers, json=payload_update, timeout=WP_POST_TIMEOUT)
            action = "actualizada"
        else:
            resp = requests.post(f"{url}/wp-json/wp/v2/pages", headers=headers, json=payload_create, timeout=WP_POST_TIMEOUT)
            action = "criada"

        if resp.status_code in (200, 201):
            result = resp.json()
            pid = result.get("id")
            log("push", f"P2 {action} — WP#{pid}")
            return jsonify({
                "ok": True,
                "action": action,
                "page_id": pid,
                "link": result.get("link"),
                "edit_link": f"{url}/wp-admin/post.php?post={pid}&action=edit"
            })
        log("push", f"P2 error: HTTP {resp.status_code}")
        return jsonify({"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}), 400
    except Exception as e:
        log("push", f"exception: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ── WordPress: aplicar design system via Global Styles ───────────────────────

def _hex_blend(hex1, hex2, t):
    """Linear interpolation between two hex colours. t=0 → hex1, t=1 → hex2."""
    h1, h2 = hex1.lstrip("#"), hex2.lstrip("#")
    r1, g1, b1 = int(h1[0:2], 16), int(h1[2:4], 16), int(h1[4:6], 16)
    r2, g2, b2 = int(h2[0:2], 16), int(h2[2:4], 16), int(h2[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(
        round(r1 + (r2 - r1) * t),
        round(g1 + (g2 - g1) * t),
        round(b1 + (b2 - b1) * t),
    )

def _build_theme_json(primary, bg, accent, dark, display_font, body_font):
    with zipfile.ZipFile(THEME_ZIP_PATH) as z:
        theme = json.loads(z.read(THEME_JSON_PATH))

    palette_map = {
        "surface":           bg,
        "surface-alt":       _hex_blend(bg, accent, 0.5),
        "surface-inverse":   dark,
        "on-surface":        primary,
        "on-surface-muted":  _hex_blend(primary, bg, 0.45),
        "on-surface-subtle": _hex_blend(primary, bg, 0.65),
        "on-inverse":        "#ffffff",
        "on-inverse-muted":  _hex_blend("#ffffff", dark, 0.35),
        "border":            _hex_blend(primary, bg, 0.88),
        "accent":            primary,
        "accent-surface":    accent,
    }
    for entry in theme["settings"]["color"]["palette"]:
        if entry["slug"] in palette_map:
            entry["color"] = palette_map[entry["slug"]]

    for ff in theme["settings"]["typography"]["fontFamilies"]:
        if ff["slug"] == "display":
            ff["fontFamily"] = display_font
        elif ff["slug"] == "body":
            ff["fontFamily"] = body_font

    return theme

FONT_STACKS = {
    "playfair-dm":     ("'Playfair Display', Georgia, serif", "'DM Sans', system-ui, sans-serif"),
    "cormorant-inter": ("'Cormorant Garamond', Georgia, serif", "Inter, system-ui, sans-serif"),
    "fraunces-dm":     ("'Fraunces', Georgia, serif", "'DM Sans', system-ui, sans-serif"),
    "inter-inter":     ("Inter, system-ui, sans-serif", "Inter, system-ui, sans-serif"),
    "libre-source":    ("'Libre Baskerville', Georgia, serif", "'Source Sans 3', system-ui, sans-serif"),
}

def _try_wp_global_styles(url, headers, primary, bg, accent, dark, display_font, body_font):
    """Tenta aplicar o design via API. Devolve None em sucesso ou str de erro."""
    try:
        gs_resp = requests.get(f"{url}/wp-json/wp/v2/global-styles", headers=headers, timeout=WP_GET_TIMEOUT)
        gs_data = gs_resp.json()
        if not isinstance(gs_data, list) or len(gs_data) == 0:
            return "Global Styles não encontrado — confirma que o tema Designeo Lite está activo."
        gs_id = gs_data[0].get("id")
        payload = {
            "settings": {
                "color": {
                    "palette": [
                        {"name": "Texto",          "slug": "texto",          "color": primary},
                        {"name": "Fundo",          "slug": "fundo",          "color": bg},
                        {"name": "Destaque",       "slug": "destaque",       "color": primary},
                        {"name": "Destaque claro", "slug": "destaque-claro", "color": accent},
                        {"name": "Fundo escuro",   "slug": "fundo-escuro",   "color": dark},
                        {"name": "Fundo suave",    "slug": "fundo-suave",    "color": accent},
                    ]
                }
            },
            "styles": {
                "color": {"background": bg, "text": primary},
                "typography": {"fontFamily": body_font},
                "elements": {
                    "h1": {"typography": {"fontFamily": display_font}},
                    "h2": {"typography": {"fontFamily": display_font}},
                    "h3": {"typography": {"fontFamily": display_font}},
                },
            },
        }
        resp = requests.post(
            f"{url}/wp-json/wp/v2/global-styles/{gs_id}",
            headers=headers, json=payload, timeout=WP_DESIGN_TIMEOUT,
        )
        if resp.status_code in (200, 201):
            return None  # sucesso
        return f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return str(e)


@app.route("/api/wp/push-design", methods=["POST"])
def wp_push_design():
    body     = request.json
    wp       = body.get("wp", {})
    palette  = body.get("palette", {})   # backward compat
    colors   = body.get("colors", {})
    primary  = colors.get("primary") or palette.get("primary", "#1a1a18")
    bg       = colors.get("bg")      or palette.get("bg",      "#ffffff")
    accent   = colors.get("accent")  or palette.get("accent",  "#f0efe9")
    dark     = colors.get("dark")    or primary
    fonts_id = body.get("fonts", {}).get("id", "playfair-dm")

    url      = wp.get("url", "").rstrip("/")
    token    = base64.b64encode(f"{wp.get('user','')}:{wp.get('password','')}".encode()).decode()
    headers  = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
    display_font, body_font = FONT_STACKS.get(fonts_id, FONT_STACKS["playfair-dm"])

    # ── 1. Tenta aplicar via Global Styles API ────────────────────────────────
    wp_error = _try_wp_global_styles(url, headers, primary, bg, accent, dark, display_font, body_font)
    if wp_error is None:
        return jsonify({"ok": True})

    # ── 2. Fallback: gera theme.json para instalação manual ───────────────────
    print(f"[push-design] WP falhou: {wp_error!r}")
    print(f"[push-design] ZIP={THEME_ZIP_PATH}  exists={THEME_ZIP_PATH.exists()}")
    try:
        theme = _build_theme_json(primary, bg, accent, dark, display_font, body_font)
        print(f"[push-design] theme.json gerado ({len(theme['settings']['color']['palette'])} cores)")
        return jsonify({
            "ok": False,
            "fallback": True,
            "theme_json": theme,
            "message": (
                f"Ligação ao WordPress falhou ({wp_error}). "
                "Descarrega o theme.json e substitui em wp-content/themes/designeo-lite/."
            ),
        })
    except Exception as build_err:
        print(f"[push-design] _build_theme_json falhou: {build_err!r}")
        return jsonify({"ok": False, "error": wp_error})



if __name__ == "__main__":
    print("\n  Designeo Studio")
    print("  → http://localhost:5050\n")
    app.run(port=FLASK_PORT, debug=False)
