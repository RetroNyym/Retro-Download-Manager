import hashlib
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.request
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from download_manager import DownloadManager
from download_manager.engine import COMPLETED

ROOT = tempfile.mkdtemp(prefix="pdm_bridge_")
DATA_DIR = os.path.join(ROOT, "data")
DL_DIR = os.path.join(ROOT, "dl")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DL_DIR, exist_ok=True)

PAYLOAD = os.urandom(1024 * 1024)
EXPECTED = hashlib.sha256(PAYLOAD).hexdigest()
RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition)))
    print(f"[{'OK  ' if condition else 'FAIL'}] {name} {detail}")


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if self.path.startswith("/page.html"):
            body = b'<html><a href="/files/x.zip">x</a><a href="/files/y.mp4">y</a></html>'
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        data = PAYLOAD
        rng = self.headers.get("Range")
        if rng:
            start = int(rng.split("=")[1].split("-")[0] or 0)
            end = int(rng.split("-")[1]) if "-" in rng.split("=")[1] and rng.split("-")[1] else len(data) - 1
            end = min(end, len(data) - 1)
            chunk = data[start:end + 1]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{len(data)}")
        else:
            chunk = data
            self.send_response(200)
        self.send_header("Content-Length", str(len(chunk)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self.wfile.write(chunk)


def wait_for(predicate, timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.15)
    return False


def get_json(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    mgr = DownloadManager(data_dir=DATA_DIR)
    mgr.apply_settings({"download_dir": DL_DIR, "segments": 4, "auto_start": True,
                        "queue_running": True, "bridge_enabled": True,
                        "bridge_port": 8899})
    time.sleep(0.6)

    try:
        status = get_json("http://127.0.0.1:8899/status")
        check("kopru ayakta", status.get("ok") is True, str(status))
    except Exception as exc:
        check("kopru ayakta", False, str(exc))
        mgr.shutdown()
        server.shutdown()
        return 1

    try:
        result = get_json("http://127.0.0.1:8899/add?url=" +
                          quote(f"{base}/files/x.bin", safe=""))
        check("kopru ile ekleme", result.get("ok") is True, str(result))
    except Exception as exc:
        check("kopru ile ekleme", False, str(exc))

    if wait_for(lambda: any(t.state == COMPLETED for t in mgr.tasks)):
        task = [t for t in mgr.tasks if t.state == COMPLETED][0]
        path = str(task.final_path)
        check("kopru indirmesi tamamlandi", os.path.exists(path))
        if os.path.exists(path):
            h = hashlib.sha256(open(path, "rb").read()).hexdigest()
            check("kopru indirmesi sha256", h == EXPECTED)
    else:
        check("kopru indirmesi tamamlandi", False, str([t.state for t in mgr.tasks]))

    try:
        links = get_json(f"http://127.0.0.1:8899/links?url={base}/page.html&depth=1")
        names = sorted(u.rsplit("/", 1)[-1] for u in links.get("links", []))
        check("kopru links ucu", links.get("ok") and names == ["x.zip", "y.mp4"],
              str(names))
    except Exception as exc:
        check("kopru links ucu", False, str(exc))

    try:
        result = get_json("http://127.0.0.1:8899/add?url=not-a-url")
        check("kopru gecersiz url", result.get("ok") is False, str(result))
    except Exception as exc:
        check("kopru gecersiz url", False, str(exc))

    mgr.apply_settings({"bridge_enabled": False})
    time.sleep(0.4)
    try:
        urllib.request.urlopen("http://127.0.0.1:8899/status", timeout=3)
        check("kopru kapatildi", False, "hala ayakta")
    except Exception:
        check("kopru kapatildi", True)

    mgr.shutdown()
    server.shutdown()
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} kopru test gecti")
    shutil.rmtree(ROOT, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

