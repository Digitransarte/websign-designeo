import app, json

c = app.app.test_client()

# PUT com producao + identidade misturadas, no cliente 1 (Diogo, existe na base)
payload = {
    "id": 1,
    "nomeCliente": "NAO DEVIA SER GRAVADO",
    "nomeNegocio": "NAO DEVIA SER GRAVADO",
    "briefing": {"publicoAlvo": "arboricultores"},
    "plan": {"paginas": ["inicio"]},
}
r = c.put("/api/clients/1", json=payload)
print("PUT status:", r.status_code)
print("Resposta fundida:")
print(json.dumps(r.get_json(), ensure_ascii=False, indent=2))

# Confirma que o ficheiro so tem producao
import sites_data
print("\nFicheiro sites_data/1.json contem:", list(sites_data.ler(1).keys()))
print("Identidade correcta veio da base?", r.get_json().get("nomeCliente") == "Diogo")

# PUT num id que nao existe
r2 = c.put("/api/clients/999", json={"briefing": {}})
print("\nPUT /999 status:", r2.status_code, "(esperado 404)")