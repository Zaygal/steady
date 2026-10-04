#!/usr/bin/env python3
"""Tiny phone-first server for Steady. Stdlib only. Binds all interfaces so a phone on
the same wifi can open it.

Two things are stored, and nothing else:
  1. a watch code -> the time of her last check-in. Not the note, not which button, no history.
  2. that's it.
It lives in memory, so there is nothing on disk to leak, and a restart forgets everyone.
"""
import http.server
import json
import os
import secrets
import socketserver
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "agent"))
import threading  # noqa: E402
import steady  # noqa: E402

# Render (and most PaaS) inject PORT. Fall back to STEADY_PORT for local runs.
PORT = int(os.environ.get("PORT") or os.environ.get("STEADY_PORT") or 8765)

# --------------------------------------------------------------- the partner signal
# ONE fact per code: the epoch of her most recent check-in. Deliberately not the note, not
# the mode, not a count - a timestamp of "she opened it", which is the smallest true thing
# that can still be useful to someone who loves her. In memory only.
_WATCH = {}
_WATCH_LOCK = threading.Lock()


def _signal_for(code):
    """The only thing a supporter can ever learn, derived purely from a timestamp."""
    with _WATCH_LOCK:
        if code not in _WATCH:
            return None                      # no such link
        rec = _WATCH[code]
    if rec is None:
        # she made the link but has not opened the app since. Do not flatter that into a
        # check-in: the supporter must never see activity that did not happen.
        return {"signal": "hasn't checked in yet", "minutes": None}
    mins = int((time.time() - rec) // 60)
    if mins < 45:
        state = "checked in recently"
    elif mins < 360:
        state = "has gone quiet for a bit"
    else:
        state = "hasn't been back today"
    return {"signal": state, "minutes": mins}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    # ------------------------------------------------------------------ POST
    def do_POST(self):
        try:
            payload = self._body()
        except (ValueError, TypeError):
            return self._json(400, {"error": "bad request"})

        # she creates the link she hands to someone she trusts
        if self.path == "/api/watch/new":
            code = secrets.token_urlsafe(9).replace("-", "").replace("_", "")[:12]
            with _WATCH_LOCK:
                _WATCH[code] = None          # deliberately NOT a timestamp: nothing has happened
            return self._json(200, {"code": code, "path": "/w/" + code})

        # she checks in. Deliberately carries NOTHING but the code - no note, no mode.
        if self.path == "/api/watch/ping":
            code = str(payload.get("code") or "")
            with _WATCH_LOCK:
                if code in _WATCH:
                    _WATCH[code] = time.time()
                    return self._json(200, {"ok": True})
            return self._json(404, {"error": "unknown code"})

        if self.path != "/api/steady":
            return self._json(404, {"error": "not found"})

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

    # ------------------------------------------------------------------ GET
    def do_GET(self):
        if self.path == "/api/models":
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            ids = steady.gemma_model_ids(key) if key else []
            return self._json(200, {"open_weight_models": ids,
                                    "in_use": steady._PICKED.get("model")})

        # what the supporter's page polls. Content-free by construction.
        if self.path.startswith("/api/w/"):
            sig = _signal_for(self.path[len("/api/w/"):].strip("/"))
            if sig is None:
                return self._json(404, {"error": "this link is no longer active. "
                                                 "Ask her to make a new one."})
            return self._json(200, sig)

        # the supporter's page itself: a different screen for a different person
        if self.path == "/w" or self.path.startswith("/w/"):
            try:
                with open(os.path.join(HERE, "w.html"), "rb") as fh:
                    body = fh.read()
            except OSError:
                return self._json(500, {"error": "watcher page missing"})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Robots-Tag", "noindex, nofollow")
            self.end_headers()
            self.wfile.write(body)
            return

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
