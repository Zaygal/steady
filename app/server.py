#!/usr/bin/env python3
"""Tiny phone-first server for Steady. Stdlib only. Binds all interfaces so a phone on
the same wifi can open it. Nothing is persisted: no session log exists by design."""
import http.server
import json
import os
import socketserver
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "agent"))
import steady  # noqa: E402

PORT = int(os.environ.get("STEADY_PORT", "8765"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/steady":
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, TypeError):
            return self._json(400, {"error": "bad request"})
        try:
            out = steady.session(
                str(payload.get("mode", "craving")),
                str(payload.get("note") or "")[:500],
                bool(payload.get("partner_signal")),
            )
        except Exception as exc:                       # pragma: no cover
            return self._json(500, {"error": f"{type(exc).__name__}: {exc}"})
        return self._json(200, out)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Steady listening on http://0.0.0.0:{PORT}  (open that on your phone)")
        httpd.serve_forever()
