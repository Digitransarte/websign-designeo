# Briefing — Próxima sessão (Integração Websign + studio.db)

## Onde ficámos (sessão anterior)

Arquitectura **A** confirmada e implementada em parte:
- A `studio.db` pertence ao **designeo-studio** (Business OS). É o único dono e escritor.
- O **Websign** (Flask, esta app) **lê** a identidade dos clientes da base, em `mode=ro`. Nunca escreve.
- O material de produção dos sites (plano, conteúdos, credenciais WP) fica **do lado do Websign**, local.

### Feito e validado
1. Websign separado para repo próprio: `github.com/Digitransarte/websign-designeo`.
   `.gitignore` protege `.env`, `*.db`, `clients.json`.
2. Esquema da `studio.db` inspeccionado. Tabela `clientes` é a fonte de identidade.
3. `db_clients.py` — leitura SO-LEITURA isolada num só módulo. Funções:
   `listar_clientes()`, `obter_cliente(id)`, `obter_por_slug(nome_ficheiro)`,
   `listar_para_frontend()` (traduz campos da base para os nomes que o index.html espera).
4. Rota `GET /api/clients` no `app.py` passou a ler da base via `db_clients.listar_para_frontend()`.
   Validado no browser: lista lateral mostra Sagui / Wild Drop / Designeo vindos da base.
5. Config: `STUDIO_DB_PATH` no `.env` = `C:\projetos\designeo-studio\studio.db`.

### Estado do código
- Ambiente: venv em `.venv`, dependências instaladas (flask, flask-cors, requests, python-dotenv).
- Andaimes de teste na raiz: `teste_config.py`, `teste_db_clients.py`, `teste_rota_clients.py`.
- Chave Claude API: vem do header `X-Api-Key` (input no frontend). NUNCA hardcoded. Confirmado limpo.

---

## Mapa de campos (referência)

| Uso na app de sites       | Coluna em `clientes` (studio.db) |
|---------------------------|----------------------------------|
| Nome do cliente           | `nome`                           |
| Nome do negócio/empresa   | `empresa`                        |
| Sector                    | `sector`                         |
| **Slug / pasta do site**  | **`nome_ficheiro`**              |
| Email                     | `email`                          |
| Chave de ligação          | `id` (inteiro: 1, 2, 3…)         |

O `id` inteiro da base é a **chave mestra** que liga um cliente ao seu conteúdo local.
NÃO reutilizar o antigo `id` gigante do clients.json (`str(int(time.time()*1000))`).

---

## O que falta — próximo ciclo (duas frentes)

### Frente 1 — Material de produção em `sites_data/<id>.json` (CORAÇÃO, fazer primeiro)
Os separadores Briefing / Plano / Conteúdo geram dados que hoje vão para o `clients.json`.
Passam a viver num ficheiro por cliente, indexado pelo `id` da base.

- Estrutura sugerida: `sites_data/<id>.json` com `{ briefing, plan, pages_content }`.
- Credenciais `wp` NÃO vão para este JSON — vão para `.env` (segurança).
- Reapontar no `index.html`: "Guardar briefing" e "Gerar plano" gravam/leem deste ficheiro.
- Ponto de partida da sessão: ver como o "Guardar briefing" está estruturado hoje no
  `index.html` — que campos junta e para onde faz `fetch`.

### Frente 2 — Reconciliar "+ Novo cliente" e "Apagar" com a arquitectura A
Na arquitectura A, criar/apagar clientes é trabalho do **designeo-studio**, não do Websign.
Estes botões chamam `POST`/`DELETE /api/clients`, que ainda escrevem no `clients.json`.

Decisão de produto a tomar (uma destas):
- (a) Esconder os botões no Websign (clientes geridos só no Business OS); ou
- (b) Redireccionar com aviso "isto faz-se no designeo-studio"; ou
- (c) Reconverter para gerir só o *conteúdo de produção*, nunca a identidade.

As rotas `POST` / `PUT` / `DELETE /api/clients` (app.py, ~linhas 125–158) ficam intocadas
até esta decisão. A `GET` já está migrada.

### Fora de âmbito (não fazer já)
- Migrar o conteúdo antigo do `clients.json` para o novo formato (fazer à parte, depois).
- Qualquer escrita na `studio.db`.

---

## Regras não-negociáveis (manter em todo o código novo)
1. Nunca escrever na `studio.db`. Ligação sempre `file:...?mode=ro`.
2. Todo o SQL da studio.db vive em `db_clients.py`. Nada espalhado pelo app.py/gutenberg.py.
3. Caminho da base via `STUDIO_DB_PATH` no `.env`, nunca hardcoded.
4. Credenciais (chave API, password WP) nunca em ficheiros versionados.

## Método de trabalho
- Peças testáveis, uma de cada vez, com confirmação a cada passo.
- Testar cada peça isoladamente (script à parte) antes de ligar ao app.py.
- Parar app.py antes de gravar (o ficheiro fica preso se o servidor estiver a correr).
- Mascarar chaves de API quando aparecerem.
