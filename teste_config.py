import os
from dotenv import load_dotenv

load_dotenv()

caminho = os.getenv("STUDIO_DB_PATH")
print("STUDIO_DB_PATH =", caminho)

if not caminho:
    print("ERRO: variável não definida. Confirma o .env.")
elif not os.path.exists(caminho):
    print("ERRO: o ficheiro não existe nesse caminho.")
else:
    print("OK: base encontrada.", os.path.getsize(caminho), "bytes")