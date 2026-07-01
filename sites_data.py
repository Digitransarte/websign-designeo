"""
sites_data.py — leitura/escrita do material de PRODUCAO dos sites.

Fronteira de arquitectura:
- Identidade do cliente (nome, empresa, sector, slug) vem da studio.db (so-leitura).
  NUNCA se guarda aqui.
- Material de producao (briefing, plan, pages_content, wp, composition, design_system)
  vive num ficheiro por cliente: sites_data/<id>.json. E' AQUI que se escreve.
- Indexado pelo id inteiro da studio.db (a chave mestra).
"""

import json
from pathlib import Path

PASTA = Path("sites_data")

CAMPOS_PRODUCAO = [
    "briefing",
    "plan",
    "pages_content",
    "wp",
    "composition",
    "design_system",
]


def _caminho(cliente_id):
    return PASTA / f"{cliente_id}.json"


def ler(cliente_id):
    """Le o material de producao de um cliente. Devolve dict (vazio se nao existir)."""
    caminho = _caminho(cliente_id)
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def guardar(cliente_id, dados):
    """
    Guarda SO os campos de producao de 'dados' em sites_data/<id>.json.
    Campos de identidade sao descartados de proposito.
    """
    PASTA.mkdir(exist_ok=True)
    producao = {k: dados[k] for k in CAMPOS_PRODUCAO if k in dados}
    caminho = _caminho(cliente_id)
    caminho.write_text(
        json.dumps(producao, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return producao


def apagar(cliente_id):
    """Apaga o ficheiro de producao de um cliente, se existir. Nunca toca na studio.db."""
    caminho = _caminho(cliente_id)
    if caminho.exists():
        caminho.unlink()
        return True
    return False