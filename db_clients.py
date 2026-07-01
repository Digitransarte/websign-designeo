"""
db_clients.py — leitura (SO-LEITURA) dos clientes a partir da studio.db.

Fronteira de arquitectura:
- A studio.db pertence ao designeo-studio (Business OS). Esta app NUNCA escreve.
- Toda a leitura da studio.db passa por este módulo. Nenhum SQL da studio.db
  deve existir no app.py ou gutenberg.py.
- A ligação abre com mode=ro: qualquer tentativa de escrita falha por design.
"""

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

STUDIO_DB_PATH = os.getenv("STUDIO_DB_PATH")


def _ligar():
    """Abre uma ligação SO-LEITURA à studio.db. Erro claro se algo faltar."""
    if not STUDIO_DB_PATH:
        raise RuntimeError("STUDIO_DB_PATH não definido. Confirma o .env.")
    if not os.path.exists(STUDIO_DB_PATH):
        raise FileNotFoundError(f"studio.db não encontrada em: {STUDIO_DB_PATH}")
    con = sqlite3.connect(f"file:{STUDIO_DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


# Colunas que a app de sites consome (o mapa de campos que definimos)
_CAMPOS = "id, nome, empresa, sector, nome_ficheiro, email"


def listar_clientes():
    """Lista todos os clientes para o ecrã de escolha. Devolve list[dict]."""
    con = _ligar()
    try:
        linhas = con.execute(
            f"SELECT {_CAMPOS} FROM clientes ORDER BY nome COLLATE NOCASE"
        ).fetchall()
        return [dict(l) for l in linhas]
    finally:
        con.close()


def obter_cliente(cliente_id):
    """Devolve um cliente pelo id (inteiro), ou None se não existir."""
    con = _ligar()
    try:
        linha = con.execute(
            f"SELECT {_CAMPOS} FROM clientes WHERE id = ?",
            (cliente_id,),
        ).fetchone()
        return dict(linha) if linha else None
    finally:
        con.close()


def obter_por_slug(nome_ficheiro):
    """Devolve um cliente pelo slug (nome_ficheiro), ou None. Útil para pastas."""
    con = _ligar()
    try:
        linha = con.execute(
            f"SELECT {_CAMPOS} FROM clientes WHERE nome_ficheiro = ?",
            (nome_ficheiro,),
        ).fetchone()
        return dict(linha) if linha else None
    finally:
        con.close()