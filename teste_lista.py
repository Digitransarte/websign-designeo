import app, json

c = app.app.test_client()
r = c.get("/api/clients")
print("GET status:", r.status_code)

dados = r.get_json()
for cliente in dados:
    tem_briefing = "briefing" in cliente
    tem_plan = "plan" in cliente
    print(f"  [{cliente['id']}] {cliente['nomeCliente']} / {cliente['nomeNegocio']}"
          f"  | briefing={tem_briefing} plan={tem_plan}")