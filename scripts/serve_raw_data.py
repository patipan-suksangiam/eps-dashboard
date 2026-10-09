#!/usr/bin/env python3
"""Static file server for the EPS Dashboard — two modes.

MODE 1 (data only) — GitHub Pages keeps the app, the NAS serves only the CSVs:
    python3 serve_raw_data.py --port 8091 \
        --dir "/volume1/.../AI Dashboard/RAW_Data" \
        --allow-origin https://patipan-suksangiam.github.io

MODE 2 (whole dashboard from the NAS — GitHub not needed at all) — serves the app AND
the data from one origin, so no CORS is involved:
    python3 serve_raw_data.py --port 8090 --bind 0.0.0.0 \
        --root "/volume1/.../AI Dashboard"

    → http://<nas>:8090/                  (index.html → Dashboard_App/index.html)
    → http://<nas>:8090/RAW_Data/0_EPS_Overview_2026.csv

Stdlib only (runs on the Synology system python3 — no pip needed).

Security (mode 2 is strict on purpose — the folder also holds credentials and source):
  * path segments starting with "." or "_" are refused → .git/ and _CORE_Private/ are unreachable
  * extension allowlist (html/js/css/csv/json/images/fonts) → .py/.md/.env/.log/.xlsx never served
  * no directory listing, GET/HEAD only, paths confined to the root
"""
import argparse
import base64
import hmac
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

DEFAULT_ORIGINS = [
    "https://patipan-suksangiam.github.io",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

DATA_SUFFIX = (".csv", ".json")
APP_SUFFIX = (".html", ".js", ".css", ".csv", ".json", ".svg", ".png", ".jpg",
              ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".map")

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".map": "application/json; charset=utf-8",
}


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        # browsers cancel fetches all the time — don't spam the log with tracebacks
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError)):
            return
        print("error handling %s: %r" % (client_address, exc), flush=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "EPSDashboardHost/2.0"
    root = "."
    origins = DEFAULT_ORIGINS
    app_mode = False          # False = data only, True = the whole dashboard
    allowed = DATA_SUFFIX
    auth = ()                 # () = open · ((user, pass),) = HTTP Basic required

    # ---------- auth ----------
    def _authorized(self):
        if not self.auth:
            return True
        hdr = self.headers.get("Authorization", "")
        if not hdr.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(hdr[6:]).decode("utf-8", "replace")
        except Exception:
            return False
        user, _, pw = decoded.partition(":")
        return any(hmac.compare_digest(user, u) and hmac.compare_digest(pw, p)
                   for u, p in self.auth)

    def _require_auth(self, head_only=False):
        """True when the request may proceed; otherwise answer 401 and return False."""
        if self._authorized():
            return True
        body = b"" if head_only else "401 authentication required\n".encode()
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="EPS Dashboard", charset="UTF-8"')
        self._cors()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)
        return False

    # ---------- helpers ----------
    def _cors(self):
        origin = self.headers.get("Origin", "")
        if origin and (origin in self.origins or "*" in self.origins):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        elif "*" in self.origins:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")

    def _safe_path(self, url_path):
        """Resolve a URL path to a file inside the root, or None when not allowed."""
        rel = unquote(url_path).lstrip("/")
        if "\x00" in rel or "\\" in rel:
            return None
        parts = [p for p in rel.split("/") if p not in ("", ".")]
        if any(p == ".." for p in parts):
            return None
        # never serve dotfiles or underscored folders (.git/, _CORE_Private/, _superseded/)
        if any(p.startswith(".") or p.startswith("_") for p in parts):
            return None

        if self.app_mode:
            if not parts or rel.endswith("/"):
                parts = parts + ["index.html"]
        elif len(parts) != 1:
            return None

        name = parts[-1]
        if not name.lower().endswith(self.allowed):
            return None

        root_real = os.path.realpath(self.root)
        full = os.path.realpath(os.path.join(root_real, *parts))
        if not (full == root_real or full.startswith(root_real + os.sep)):
            return None
        return full

    def _respond(self, code, body, ctype="text/plain; charset=utf-8"):
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    # ---------- HTTP verbs ----------
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_HEAD(self):
        self._serve(head_only=True)

    def do_GET(self):
        self._serve(head_only=False)

    def _serve(self, head_only):
        if not self._require_auth(head_only):
            return
        path = self._safe_path(urlparse(self.path).path)
        if not path or not os.path.isfile(path):
            self._respond(404, b"" if head_only else b"404 not found\n")
            return

        size = os.path.getsize(path)
        ext = os.path.splitext(path)[1].lower()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        rel = os.path.relpath(path, os.path.realpath(self.root)).replace(os.sep, "/")
        print("[%s] %s (%d bytes)" % ("HEAD" if head_only else "GET", rel, size), flush=True)
        if head_only:
            return
        try:
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass  # client went away mid-download (normal for browser fetches)

    def log_message(self, fmt, *args):
        pass  # use the explicit print above instead of the default noise


def main():
    ap = argparse.ArgumentParser(
        description="Serve the EPS dashboard files (data only, or the whole app).")
    ap.add_argument("--port", type=int, default=8091)
    ap.add_argument("--bind", default="127.0.0.1",
                    help="127.0.0.1 behind a tunnel (recommended) · 0.0.0.0 for LAN access")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--dir", help="MODE 1: the RAW_Data folder (app stays on GitHub Pages)")
    src.add_argument("--root", help="MODE 2: the project folder (serves app + data, same origin)")
    ap.add_argument("--allow-origin", action="append", default=None,
                    help="allowed CORS origin (repeatable). Only relevant in MODE 1.")
    ap.add_argument("--auth-file", default=None,
                    help="file with 'user:password' lines — enables HTTP Basic auth for everything")
    a = ap.parse_args()

    root = os.path.realpath(os.path.expanduser(a.root or a.dir))
    if not os.path.isdir(root):
        sys.exit("not a directory: %s" % root)

    Handler.root = root
    Handler.origins = a.allow_origin or DEFAULT_ORIGINS
    Handler.app_mode = bool(a.root)
    Handler.allowed = APP_SUFFIX if a.root else DATA_SUFFIX

    if a.auth_file:
        creds = []
        with open(a.auth_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and ":" in line:
                    u, _, p = line.partition(":")
                    creds.append((u, p))
        Handler.auth = tuple(creds)
        print("auth  : HTTP Basic enabled (%d credential(s))" % len(creds), flush=True)

    if a.root and not os.path.isdir(os.path.join(root, "Dashboard_App")):
        print("warning: %s/Dashboard_App not found — is --root the project folder?" % root,
              flush=True)

    print("mode  : %s" % ("WHOLE APP (same origin)" if a.root else "DATA ONLY (CORS for GitHub Pages)"),
          flush=True)
    print("root  : %s" % root, flush=True)
    print("listen: http://%s:%d" % (a.bind, a.port), flush=True)
    Server((a.bind, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
