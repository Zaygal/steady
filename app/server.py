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
import threading  # noqa: E402
import steady  # noqa: E402

# Render (and most PaaS) inject PORT. Fall back to STEADY_PORT for local runs.
PORT = int(os.environ.get("PORT") or os.environ.get("STEADY_PORT") or 8765)


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
        except ValueError as exc:                      # bad input, not a server fault
            return self._json(400, {"error": str(exc)})
        except Exception as exc:                       # pragma: no cover
            return self._json(500, {"error": f"{type(exc).__name__}: {exc}"})
        return self._json(200, out)

    def do_GET(self):
        if self.path == "/api/models":
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            ids = steady.gemma_model_ids(key) if key else []
            return self._json(200, {"open_weight_models": ids,
                                    "in_use": steady._PICKED.get("model")})
        return super().do_GET()

    def log_message(self, *args):
        pass


def _warm():
    """One throwaway turn at boot so model discovery happens before a person taps a button."""
    try:
        steady.session("craving", "")
    except Exception:
        pass


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    # threaded: a single-threaded server stalls when a phone holds a connection open
    with http.server.ThreadingHTTPServer(("", PORT), Handler) as httpd:
        print(f"Steady listening on http://0.0.0.0:{PORT}  (open that on your phone)")
        # Without this, request #1 after every restart tries a model that never answers, times
        # out, and retries - so the very first click was the slowest thing in the product.
        threading.Thread(target=_warm, daemon=True).start()
        httpd.serve_forever()
