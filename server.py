#!/usr/bin/env python3
"""
Local gallery server for a denote directory.
Read/arrange-only canvas: browses your denote notes+media spatially,
saves only x/y/size positions back to disk (never touches your notes).

Usage:
    python3 server.py /path/to/your/denote/dir [port]

Then open http://localhost:PORT
"""
import http.server
import json
import os
import re
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
VID_EXT = {".mp4", ".webm", ".mov"}
TEXT_EXT = {".md", ".org", ".txt"}
PDF_EXT = {".pdf"}


HERE = Path(__file__).parent.resolve()
LAYOUT_FILE = HERE / "layout.json"
CONFIG_FILE = HERE / ".config.json"

# --- denote filename parsing: YYYYMMDDTHHMMSS--title-words__tag1_tag2.ext
DENOTE_RE = re.compile(r"^(\d{8}T\d{6})--([^_]+)(?:__(.+))?$")


def parse_denote_name(stem):
    m = DENOTE_RE.match(stem)
    if not m:
        return {"id": stem, "title": stem.replace("-", " "), "tags": []}
    denote_id, title_slug, tags = m.groups()
    return {
        "id": denote_id,
        "title": title_slug.replace("-", " "),
        "tags": tags.split("_") if tags else [],
    }


def text_snippet(path, n=400):
    try:
        raw = path.read_text(errors="ignore")
    except Exception:
        return ""
    # strip org/md front matter-ish lines (#+TITLE:, ---, etc.)
    lines = [l for l in raw.splitlines() if not l.strip().startswith(("#+", "---"))]
    body = "\n".join(lines).strip()
    return body[:n]


ID_RE = re.compile(r"\d{8}T\d{6}")


def build_index(root: Path):
    items = []
    texts = []  # (denote_id, full_text) for link detection
    for p in sorted(root.rglob("*")):
        if p.is_dir() or p.name.startswith("."):
            continue
        ext = p.suffix.lower()
        rel = p.relative_to(root).as_posix()
        if not DENOTE_RE.match(p.stem):
            continue
        meta = parse_denote_name(p.stem)
        if ext in IMG_EXT:
            items.append({**meta, "type": "image", "src": "/media/" + urllib.parse.quote(rel)})
        elif ext in VID_EXT:
            items.append({**meta, "type": "video", "src": "/media/" + urllib.parse.quote(rel)})
        elif ext in PDF_EXT:
            items.append({**meta, "type": "pdf", "src": "/media/" + urllib.parse.quote(rel), "snippet": "[PDF Document]"})
        elif ext in TEXT_EXT:
            try:
                full = p.read_text(errors="ignore")
            except Exception:
                full = ""
            items.append({**meta, "type": "text", "snippet": text_snippet(p),
                          "src": "/media/" + urllib.parse.quote(rel)})
            texts.append((meta["id"], full))

    # detect denote-id cross-references inside note bodies -> link graph
    all_ids = {it["id"] for it in items}
    links = []
    for denote_id, full in texts:
        for match in set(ID_RE.findall(full)):
            if match != denote_id and match in all_ids:
                pair = tuple(sorted([denote_id, match]))
                if pair not in links:
                    links.append(pair)
    return items, links


_index_cache = {"mtime": None, "data": None}


def get_index_cached():
    """Rebuild the index only when the denote dir has actually changed."""
    mtime = DENOTE_DIR.stat().st_mtime
    if _index_cache["mtime"] != mtime or _index_cache["data"] is None:
        items, links = build_index(DENOTE_DIR)
        _index_cache["data"] = {"items": items, "links": links}
        _index_cache["mtime"] = mtime
    return _index_cache["data"]


class Handler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            html = (HERE / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        elif parsed.path == "/api/index":
            self._send_json(get_index_cached())
        elif parsed.path == "/api/stat":
            self._send_json({"mtime": DENOTE_DIR.stat().st_mtime})
        elif parsed.path == "/api/layout":
            if LAYOUT_FILE.exists():
                self._send_json(json.loads(LAYOUT_FILE.read_text()))
            else:
                self._send_json({})
        elif parsed.path.startswith("/media/"):
            rel = urllib.parse.unquote(parsed.path[len("/media/"):])
            fp = (DENOTE_DIR / rel).resolve()
            if not str(fp).startswith(str(DENOTE_DIR.resolve())) or not fp.exists():
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", guess_type(fp))
            self.end_headers()
            self.wfile.write(fp.read_bytes())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/layout":
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length)
            LAYOUT_FILE.write_bytes(data)
            self._send_json({"ok": True})
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        pass  # quiet


def guess_type(fp: Path):
    ext = fp.suffix.lower()
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
        ".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime",
        ".pdf": "application/pdf",
        ".md": "text/plain", ".org": "text/plain", ".txt": "text/plain",
    }.get(ext, "application/octet-stream")


if __name__ == "__main__":
    denote_dir = sys.argv[1] if len(sys.argv) > 1 else None
    port = int(sys.argv[2]) if len(sys.argv) > 2 else None

    cfg = {}
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
        except Exception:
            cfg = {}

    if denote_dir is None:
        denote_dir = cfg.get("denote_dir")
        if denote_dir is None:
            denote_dir = input("Path to your denote folder: ").strip()
    if port is None:
        port = cfg.get("port", 8420)

    DENOTE_DIR = Path(denote_dir).expanduser().resolve()
    if not DENOTE_DIR.is_dir():
        print(f"Not a directory: {DENOTE_DIR}")
        sys.exit(1)

    CONFIG_FILE.write_text(json.dumps({"denote_dir": str(DENOTE_DIR), "port": port}))

    url = f"http://localhost:{port}"
    print(f"Serving {DENOTE_DIR} at {url}")
    print("(local only — not reachable from other machines)")
    if not os.environ.get("DENOTE_SPATIAL_NO_OPEN"):
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    http.server.HTTPServer(("localhost", port), Handler).serve_forever()