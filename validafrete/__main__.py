"""Permite executar a aplicação com ``python -m validafrete``."""

from .app import app

if __name__ == "__main__":
    print("ValidaFrete em execução: abra http://127.0.0.1:5050 no navegador (Ctrl+C para sair).")
    app.run(host="127.0.0.1", port=5050, debug=False)
