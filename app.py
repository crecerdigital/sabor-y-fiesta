"""
app.py — Servidor de Sabor & Fiesta (Taste-Aware Event Concierge).

Servidor ligero con SOLO la biblioteca estándar de Python 3 (sin pip,
sin frameworks): sirve la página y el endpoint POST /api/plan.

Modos de datos (transparentes, la UI siempre lo declara):
  - "qloo-live":  si existe la variable de entorno QLOO_API_KEY, se piden
                  restaurantes y artistas REALES a la API de Qloo
                  (ver qloo_client.py) y se completa el plan localmente.
  - "local-demo": sin clave (o si la API falla), se usa el motor local
                  con datos curados (engine.py + data/curated.json).

Ejecutar:   python3 app.py            → http://localhost:8000
Puerto:     variable de entorno PORT (por defecto 8000).
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import engine
import qloo_client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")


def build_response(profile):
    """Arma el plan: local como base; si Qloo responde, enriquece en vivo."""
    plan = engine.build_plan(profile)
    if qloo_client.is_configured():
        try:
            live = qloo_client.get_live_picks(profile)
        except Exception:
            live = None
        if live:
            if "restaurant" in live:
                plan["plan"]["restaurant"].update(live["restaurant"])
            if "music" in live:
                plan["plan"]["music"].update(live["music"])
            plan["mode"] = "qloo-live"
    return plan


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # consola limpia
        pass

    def _send(self, code, body, content_type="application/json; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            with open(os.path.join(STATIC_DIR, "index.html"), encoding="utf-8") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/api/health":
            self._send(200, json.dumps({
                "ok": True,
                "qloo_configured": qloo_client.is_configured(),
                "mode": "qloo-live" if qloo_client.is_configured() else "local-demo",
            }))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/plan":
            self._send(404, json.dumps({"error": "not found"}))
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            profile = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._send(400, json.dumps({"error": "invalid json"}))
            return
        try:
            result = build_response(profile)
            self._send(200, json.dumps(result, ensure_ascii=False))
        except Exception as exc:  # nunca tumbar el servidor por un plan
            self._send(500, json.dumps({"error": str(exc)}))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Sabor & Fiesta en http://0.0.0.0:{port} "
          f"(modo: {'qloo-live' if qloo_client.is_configured() else 'local-demo'})")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
