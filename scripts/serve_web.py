"""
Local Web Dashboard Server Launcher
Runs a simple HTTP server hosting the interactive Graph & Benchmark Explorer.
"""
import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8000
DIRECTORY = Path(__file__).resolve().parent.parent / "web"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

def main():
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    for p in range(PORT, PORT + 20):
        try:
            httpd = socketserver.TCPServer(("", p), Handler)
            url = f"http://localhost:{p}"
            print("=" * 60)
            print(f"  GraphBench Interactive Web Explorer is running!")
            print(f"  Open in browser: {url}")
            print("=" * 60)
            try:
                webbrowser.open(url)
            except Exception:
                pass
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down server.")
            return
        except OSError:
            continue
    print(f"Error: Could not bind to any port between {PORT} and {PORT+20}")

if __name__ == "__main__":
    main()
