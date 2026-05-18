import json
import os
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
HALL_LAYOUTS_JSON = os.path.join(REPO_DIR, "hall_layouts.json")
COMPUTE_PY = os.path.join(REPO_DIR, "compute.py")


def load_json(path, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else fallback
    except Exception:
        return fallback


def normalize_layout_store_payload(payload):
    stores = payload.get("stores") if isinstance(payload, dict) else None
    if not isinstance(stores, dict):
        raise ValueError("stores がありません")

    normalized = {}
    for store, layout in stores.items():
        store_name = str(store or "").strip()
        if not store_name or not isinstance(layout, dict):
            continue
        cols = int(layout.get("cols") or 0)
        placements = layout.get("placements")
        if cols <= 0 or not isinstance(placements, dict):
            continue
        normalized[store_name] = {
            "cols": cols,
            "placements": placements,
        }
    if not normalized:
        raise ValueError("保存できる店舗配置がありません")
    return normalized


def save_hall_layouts(payload):
    current = load_json(HALL_LAYOUTS_JSON, {})
    if not isinstance(current.get("stores"), dict):
        current = {"version": 1, "stores": current if current else {}}
    current["version"] = max(1, int(current.get("version") or 1))
    current["stores"].update(normalize_layout_store_payload(payload))
    with open(HALL_LAYOUTS_JSON, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return current


class DevHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/hall-layouts":
            self.send_error(404, "Not Found")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            saved = save_hall_layouts(payload)
            recompute = bool(payload.get("recompute"))
            compute_result = None
            if recompute:
                proc = subprocess.run(
                    [sys.executable, COMPUTE_PY],
                    cwd=REPO_DIR,
                    capture_output=True,
                    text=True,
                    timeout=240,
                )
                compute_result = {
                    "returncode": proc.returncode,
                    "stdout": proc.stdout[-3000:],
                    "stderr": proc.stderr[-3000:],
                }
                if proc.returncode != 0:
                    self.send_json(500, {
                        "ok": False,
                        "error": "compute.py の再計算に失敗しました",
                        "compute": compute_result,
                    })
                    return
            self.send_json(200, {
                "ok": True,
                "stores": sorted(saved.get("stores", {}).keys()),
                "recomputed": recompute,
                "compute": compute_result,
            })
        except Exception as e:
            self.send_json(400, {"ok": False, "error": str(e)})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4177
    os.chdir(REPO_DIR)
    server = ThreadingHTTPServer(("127.0.0.1", port), DevHandler)
    print(f"Serving Juggler dashboard on http://127.0.0.1:{port}/")
    print("POST /api/hall-layouts saves hall_layouts.json and can recompute data.json")
    server.serve_forever()
