import hashlib
import http.server
import os
import random
import shutil
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from download_manager import DownloadManager
from download_manager.engine import COMPLETED, PAUSED

random.seed(7)
ROOT = tempfile.mkdtemp(prefix="pdm_restart_")
DATA_DIR = os.path.join(ROOT, "data")
DL_DIR = os.path.join(ROOT, "downloads")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DL_DIR, exist_ok=True)

PAYLOAD = os.urandom(6 * 1024 * 1024)
RESULTS = []


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        data = PAYLOAD
        total = len(data)
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes="):
            spec = rng[6:]
            start_s, _, end_s = spec.partition("-")
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else total - 1
            end = min(end, total - 1)
            chunk = data[start:end + 1]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
        else:
            chunk = data
            self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(chunk)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("ETag", '"restart-etag"')
        self.end_headers()
        if not self.headers.get("Range") or True:
            self.wfile.write(chunk)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def wait_for(predicate, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.15)
    return False


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition)))
    print(f"[{'OK  ' if condition else 'FAIL'}] {name} {detail}")


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}/restartme.bin"

    mgr = DownloadManager(data_dir=DATA_DIR)
    mgr.apply_settings({"download_dir": DL_DIR, "auto_start": True,
                        "queue_running": True, "segments": 6, "max_concurrent": 2})
    task = mgr.add([url], speed_limit=350)[0]
    wait_for(lambda: task.downloaded > 400 * 1024, timeout=60)
    print("duraklatilacak boyut:", task.downloaded)
    mgr.shutdown()
    check("kapanista duraklatildi", task.state == PAUSED, task.state)
    check("part dosyasi kaldi", task.part_path and task.part_path.exists(),
          str(task.part_path))
    expected = hashlib.sha256(PAYLOAD).hexdigest()

    del mgr
    time.sleep(0.5)

    mgr2 = DownloadManager(data_dir=DATA_DIR)
    loaded = [t for t in mgr2.tasks if t.url.endswith("restartme.bin")]
    check("kuyruk yeniden yuklendi", len(loaded) == 1, str(len(mgr2.tasks)))
    if loaded:
        resumed = loaded[0]
        check("durum paused", resumed.state == PAUSED, resumed.state)
        resumed.start()
        ok = wait_for(lambda: resumed.state == COMPLETED, timeout=120)
        check("yeniden baslatma tamamlandi", ok, resumed.state)
        if resumed.final_path and resumed.final_path.exists():
            check("yeniden baslatma sha256",
                  sha256(str(resumed.final_path)) == expected)
            check("kalan part yok",
                  not os.path.exists(str(resumed.final_path) + ".part"))
        else:
            check("dosya olustu", False, str(resumed.final_path))
    mgr2.shutdown()
    server.shutdown()

    try:
        from download_manager import DownloadManager as DM
        real = DM(data_dir=os.path.join(ROOT, "realdata"))
        real.apply_settings({"download_dir": os.path.join(ROOT, "realdl"),
                             "segments": 4})
        target = "https://proof.ovh.net/files/1Mb.dat"
        try:
            tasks = real.add([target])
            task = tasks[0]
            done = wait_for(lambda: task.state in (COMPLETED, "error"), timeout=60)
            check("gercek internet indirmesi", done and task.state == COMPLETED,
                  f"{task.state} {task.error or ''}")
        except Exception as exc:
            print("ag erisimi yok/engellendi:", exc)
        real.shutdown()
    except Exception as exc:
        print("gercek test atlandi:", exc)

    server.shutdown()
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} test gecti")
    shutil.rmtree(ROOT, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

