"""app.py — Ponto de entrada da aplicação de demonstração da Bookstore API (P2).

Permite executar a aplicação de demonstração localmente com um servidor HTTP simples
e abrir automaticamente a interface no navegador padrão.
"""

import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path

PORT = int(os.environ.get("DEMO_PORT", 8080))
BASE_DIR = Path(__file__).resolve().parent


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP customizado que serve os arquivos estáticos da pasta demo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def end_headers(self):
        # Habilita CORS para testes locais
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()


def main():
    os.chdir(BASE_DIR)
    url = f"http://localhost:{PORT}/index.html"

    print("=" * 70)
    print("  BOOKSTORE API — APLICAÇÃO DE DEMONSTRAÇÃO (APRESENTAÇÃO P2)")
    print("=" * 70)
    print(f"  Diretório Base: {BASE_DIR}")
    print(f"  Acesse via URL: {url}")
    print("  Pressione CTRL+C para encerrar o servidor da demonstração.")
    print("=" * 70)

    try:
        # Abre o navegador automaticamente
        webbrowser.open(url)
        with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor de demonstração finalizado.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro ao iniciar servidor na porta {PORT}: {e}")
        print("Alternativa: Abra diretamente o arquivo 'demo/pages/01_login.html' no navegador.")


if __name__ == "__main__":
    main()
