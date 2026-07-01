import app  # importa o Flask app do app.py

cliente_teste = app.app.test_client()
resposta = cliente_teste.get("/api/clients")

print("Status:", resposta.status_code)
print("Corpo:")
import json
print(json.dumps(resposta.get_json(), ensure_ascii=False, indent=2))