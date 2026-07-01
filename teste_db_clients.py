import db_clients

print("=== listar_clientes() ===")
clientes = db_clients.listar_clientes()
for c in clientes:
    print(f"  [{c['id']}] {c['nome']} / {c['empresa']} / slug={c['nome_ficheiro']}")

print(f"\nTotal: {len(clientes)} cliente(s)")

print("\n=== obter_cliente(1) ===")
print(db_clients.obter_cliente(1))

print("\n=== obter_cliente(999) (inexistente) ===")
print(db_clients.obter_cliente(999))

print("\n=== obter_por_slug('edgar_correia') ===")
print(db_clients.obter_por_slug("edgar_correia"))