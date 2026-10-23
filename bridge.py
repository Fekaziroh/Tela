"""Local HTTP bridge: serves the window (ui/) to a normal browser and forwards calls to the Api.

Used when the WebView2 window cannot open (fallback) and by the automated UI tests.
Only answers 127.0.0.1 with a random token, so web pages cannot call it.
"""
import json
import mimetypes
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Bridge:
    def __init__(self, api, ui_folder, port=0):
        self.api = api
        self.ui = Path(ui_folder).resolve()
        self.token = secrets.token_urlsafe(16)
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, code, body, ctype="application/json; charset=utf-8"):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):  # noqa: N802
                path = self.path.split("?", 1)[0].lstrip("/") or "index.html"
                file = (bridge.ui / path).resolve()
                if bridge.ui not in file.parents or not file.is_file():
                    self._send(404, b"not found", "text/plain")
                    return
                ctype = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
                if ctype.startswith("text/") or ctype.endswith("javascript"):
                    ctype += "; charset=utf-8"
                self._send(200, file.read_bytes(), ctype)

            def do_POST(self):  # noqa: N802
                if self.headers.get("X-Tela-Token") != bridge.token:
                    self._send(403, b'{"error":"forbidden"}')
                    return
                name = self.path.rsplit("/", 1)[-1]
                fn = getattr(bridge.api, name, None)
                if name.startswith("_") or not callable(fn):
                    self._send(404, b'{"error":"unknown"}')
                    return
                try:
                    n = int(self.headers.get("Content-Length") or 0)
                    args = json.loads(self.rfile.read(n) or b"[]")
                    result = fn(*args)
                    body = json.dumps({"result": result}, default=str).encode()
                except Exception as e:  # noqa: BLE001
                    body = json.dumps({"error": f"{type(e).__name__}: {e}"}).encode()
                self._send(200, body)

        self.server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True, name="bridge").start()

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}/index.html?t={self.token}"

    def close(self):
        self.server.shutdown()
