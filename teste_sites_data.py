import sites_data

payload = {
    "id": 1,
    "nomeCliente": "Diogo",
    "nomeNegocio": "Sagui",
    "briefing": {"publico": "teste"},
    "plan": {"paginas": ["inicio", "sobre"]},
    "wp": {"url": "x", "user": "y", "password": "SEGREDO"},
}

print("=== guardar(1, payload) ===")
guardado = sites_data.guardar(1, payload)
print("Campos guardados:", list(guardado.keys()))
print("nomeCliente foi descartado?", "nomeCliente" not in guardado)

print("\n=== ler(1) ===")
lido = sites_data.ler(1)
print("Campos lidos:", list(lido.keys()))
print("briefing:", lido.get("briefing"))

print("\n=== ler(999) (inexistente) ===")
print("Devolve vazio?", sites_data.ler(999) == {})