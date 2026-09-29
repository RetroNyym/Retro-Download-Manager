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

from download_manager import DownloadManager, detect_category, format_bytes, format_speed
from download_manager.engine import CANCELED, COMPLETED, PAUSED

random.seed(42)

ROOT = tempfile.mkdtemp(prefix="pdm_test_")
DATA_DIR = os.path.join(ROOT, "data")
DL_DIR = os.path.join(ROOT, "downloads")

FILES = {}
PAGE = b"""<html><body>
<a href="/files/a.zip">a</a>
<img src="/files/b.mp4"></img>
<a href="/files/c.pdf">c</a>
<a href="https://external.example.com/d.zip">ext</a>
<a href="/sub/index.html">sub</a>
<a href="/files/nope.txt">txt</a>
</body></html>"""
SUB_PAGE = b"""<html><body><a href="/files/e.rar">e</a></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def do_HEAD(self):
        self._serve(head=True)

    def do_GET(self):
        self._serve(head=False)

    def _serve(self, head):
        path = self.path.split("?")[0]
        if path == "/page.html":
            body = PAGE
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if not head:
                self.wfile.write(body)
            return
        if path == "/sub/index.html":
            body = SUB_PAGE
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if not head:
                self.wfile.write(body)
            return
        entry = FILES.get(path)
        if not entry:
            self.send_error(404)
            return
        data = entry["data"]
        ctype = entry.get("ctype", "application/octet-stream")
        allow_range = entry.get("range", True)
        delay = entry.get("delay", 0)
        total = len(data)
        rng = self.headers.get("Range")
        if allow_range and rng and rng.startswith("bytes="):
            spec = rng[6:]
            start_s, _, end_s = spec.partition("-")
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else total - 1
            end = min(end, total - 1)
            if start > end or start >= total:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{total}")
                self.end_headers()
                return
            chunk = data[start:end + 1]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
        else:
            chunk = data
            self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(chunk)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("ETag", '"test-etag-1"')
        self.end_headers()
        if head:
            return
        if delay:
            step = 16 * 1024
            for offset in range(0, len(chunk), step):
                self.wfile.write(chunk[offset:offset + step])
                time.sleep(delay)
        else:
            self.wfile.write(chunk)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def wait_for(predicate, timeout=90, interval=0.15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


def new_manager(**kwargs):
    shutil.rmtree(DATA_DIR, ignore_errors=True)
    shutil.rmtree(DL_DIR, ignore_errors=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DL_DIR, exist_ok=True)
    mgr = DownloadManager(data_dir=DATA_DIR)
    mgr.apply_settings({"download_dir": DL_DIR, "auto_start": True,
                        "queue_running": True, "max_concurrent": 3,
                        "segments": 8, "retries": 6})
    return mgr


results = []


def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    status = "OK  " if condition else "FAIL"
    print(f"[{status}] {name} {detail}")


def build_files():
    big = os.urandom(12 * 1024 * 1024)
    FILES["/files/big.bin"] = {"data": big, "ctype": "application/octet-stream"}
    FILES["/files/big.bin.hash"] = {"data": hashlib.sha256(big).hexdigest().encode(),
                                    "ctype": "text/plain"}
    no_range = os.urandom(2 * 1024 * 1024)
    FILES["/files/norange.bin"] = {"data": no_range, "range": False}
    raw = os.urandom(1024 * 1024)
    FILES["/files/raw.dat"] = {"data": raw, "range": False}
    pause_file = os.urandom(2 * 1024 * 1024)
    FILES["/files/pauseme.bin"] = {"data": pause_file}
    cancel_file = os.urandom(3 * 1024 * 1024)
    FILES["/files/cancelme.bin"] = {"data": cancel_file}
    archive = os.urandom(3 * 1024 * 1024)
    FILES["/files/sample.zip"] = {"data": archive}
    small = os.urandom(300 * 1024)
    FILES["/files/small.dat"] = {"data": small}
    return {"big": big, "norange": no_range, "raw": raw, "pause": pause_file,
            "cancel": cancel_file, "archive": archive, "small": small}


def test_multisegment(mgr, base, sources):
    url = base + "/files/big.bin"
    task = mgr.add([url])[0]
    ok = wait_for(lambda: task.state == COMPLETED, timeout=120)
    check("cok parcali indirme tamamlanir", ok, task.state)
    check("boyut eslesir", task.size == len(sources["big"]), str(task.size))
    check("parca sayisi > 1", len(task.segments) > 1, str(len(task.segments)))
    path = os.path.join(task.dest_dir, task.filename)
    check("dosya olustu", os.path.exists(path), path)
    if os.path.exists(path):
        check("sha256 eslesir", sha256(path) == hashlib.sha256(sources["big"]).hexdigest())
    check("part dosyasi temizlendi", not os.path.exists(path + ".part"))
    check("meta dosyasi temizlendi", not os.path.exists(path + ".part.json"))
    check("kategoriler otomatik", task.category == "other", task.category)
    check("gecmise yazildi", any(h["url"] == url for h in mgr.history))
    return task


def test_no_range(mgr, base, sources):
    url = base + "/files/norange.bin"
    task = mgr.add([url])[0]
    ok = wait_for(lambda: task.state == COMPLETED, timeout=90)
    check("range desteklemeyen sunucu", ok, task.state)
    path = os.path.join(task.dest_dir, task.filename)
    if os.path.exists(path):
        check("norange sha256", sha256(path) == hashlib.sha256(sources["norange"]).hexdigest())


def test_unknown_size(mgr, base, sources):
    url = base + "/files/raw.dat"
    task = mgr.add([url])[0]
    ok = wait_for(lambda: task.state == COMPLETED, timeout=90)
    check("bilinmeyen boyut tamamlanir", ok, task.state)
    path = os.path.join(task.dest_dir, task.filename)
    if os.path.exists(path):
        check("bilinmeyen boyut sha256",
              sha256(path) == hashlib.sha256(sources["raw"]).hexdigest())


def test_pause_resume(mgr, base, sources):
    url = base + "/files/pauseme.bin"
    task = mgr.add([url], speed_limit=400)[0]
    wait_for(lambda: task.downloaded > 150 * 1024, timeout=60)
    task.pause()
    wait_for(lambda: not task.is_busy, timeout=30)
    check("duraklatma calisir", task.state == PAUSED, task.state)
    partial = task.downloaded
    check("kismi veri korunur", 0 < partial < len(sources["pause"]), str(partial))
    time.sleep(1.0)
    check("indirme durdu", task.downloaded == partial, f"{task.downloaded} vs {partial}")
    task.start()
    ok = wait_for(lambda: task.state == COMPLETED, timeout=120)
    check("devam ettirme tamamlanir", ok, task.state)
    path = os.path.join(task.dest_dir, task.filename)
    if os.path.exists(path):
        check("devam ettirme sha256",
              sha256(path) == hashlib.sha256(sources["pause"]).hexdigest())


def test_cancel(mgr, base, sources):
    url = base + "/files/cancelme.bin"
    task = mgr.add([url], speed_limit=200)[0]
    wait_for(lambda: task.downloaded > 100 * 1024, timeout=60)
    task.cancel(delete_files=True)
    wait_for(lambda: not task.is_busy, timeout=30)
    check("iptal calisir", task.state == CANCELED, task.state)
    part = task.dest_dir / (task.filename + ".part")
    time.sleep(0.5)
    check("part silindi", not os.path.exists(str(part)), str(part))


def test_queue_and_categories(mgr, base, sources):
    urls = [base + "/files/sample.zip", base + "/files/small.dat",
            base + "/files/raw.dat"]
    tasks = mgr.add(urls)
    max_active = 0
    deadline = time.time() + 90
    while time.time() < deadline:
        max_active = max(max_active, sum(1 for t in mgr.tasks if t.is_busy))
        if all(t.state == COMPLETED for t in tasks):
            break
        time.sleep(0.2)
    check("kuyruk tamamlanir", all(t.state == COMPLETED for t in tasks),
          str([t.state for t in tasks]))
    check("eszamanlilik siniri", max_active <= 3, str(max_active))
    zip_task = tasks[0]
    check("kategori tespiti (archives)", zip_task.category == "archives",
          zip_task.category)
    folder = os.path.join(DL_DIR, "Arşivler")
    check("kategori klasoru", os.path.isdir(folder), folder)


def test_grabber(mgr, base):
    found = mgr.grab(base + "/page.html", depth=0, same_domain=True, extensions=None,
                     max_pages=10)
    names = sorted(u.rsplit("/", 1)[-1] for u in found)
    check("grabber derinlik 0", names == ["a.zip", "b.mp4", "c.pdf"], str(names))

    found1 = mgr.grab(base + "/page.html", depth=1, same_domain=True, extensions=None,
                      max_pages=10)
    names1 = sorted(u.rsplit("/", 1)[-1] for u in found1)
    check("grabber derinlik 1", names1 == ["a.zip", "b.mp4", "c.pdf", "e.rar"],
          str(names1))

    found2 = mgr.grab(base + "/page.html", depth=1, same_domain=True,
                      extensions=[".zip"], max_pages=10)
    names2 = sorted(u.rsplit("/", 1)[-1] for u in found2)
    check("grabber uzanti filtresi", names2 == ["a.zip"], str(names2))
    check("grabber alan adi filtresi",
          all("external.example.com" not in u for u in found1))


def test_settings_and_persistence():
    from download_manager.manager import Settings
    settings = Settings(os.path.join(DATA_DIR, "settings.json"))
    settings.update({"segments": 16, "speed_limit": 2048,
                     "category_folders": {"other": "Diger"}})
    settings2 = Settings(os.path.join(DATA_DIR, "settings.json"))
    check("ayarlar kalici", settings2.segments == 16 and settings2.speed_limit == 2048)
    check("kategori klasoru kalici", settings2.category_folders.get("other") == "Diger")


def test_queue_persistence():
    mgr = DownloadManager(data_dir=DATA_DIR)
    mgr.stop_queue()
    mgr.apply_settings({"auto_start": False, "download_dir": DL_DIR})
    task = mgr.add(["https://example.com/persist.bin"])[0]
    task.pause()
    mgr.save_queue()
    mgr.shutdown()

    mgr2 = DownloadManager(data_dir=DATA_DIR)
    check("kuyruk yuklenir", any(t.url.endswith("persist.bin") for t in mgr2.tasks),
          str(len(mgr2.tasks)))
    loaded = [t for t in mgr2.tasks if t.url.endswith("persist.bin")]
    if loaded:
        check("kuyruk durumu korunur", loaded[0].state == PAUSED, loaded[0].state)
    mgr2.shutdown()


def test_helpers():
    check("kategori: mp4 -> video", detect_category("film.mp4") == "video")
    check("kategori: exe -> programs", detect_category("setup.EXE") == "programs")
    check("kategori: bilinmeyen -> other", detect_category("x.xyz") == "other")
    check("format_bytes", format_bytes(1536) == "1.5 KB", format_bytes(1536))
    check("format_speed", format_speed(0) == "-", format_speed(0))


def main():
    build_files()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    print("sunucu:", base)

    test_helpers()

    mgr = new_manager()
    try:
        test_multisegment(mgr, base, {"big": FILES["/files/big.bin"]["data"]})
        test_no_range(mgr, base, {"norange": FILES["/files/norange.bin"]["data"]})
        test_unknown_size(mgr, base, {"raw": FILES["/files/raw.dat"]["data"]})
        test_pause_resume(mgr, base, {"pause": FILES["/files/pauseme.bin"]["data"]})
        test_cancel(mgr, base, {"cancel": FILES["/files/cancelme.bin"]["data"]})
        test_queue_and_categories(mgr, base,
                                  {"archive": FILES["/files/sample.zip"]["data"]})
        test_grabber(mgr, base)
    finally:
        mgr.shutdown()

    test_settings_and_persistence()
    test_queue_persistence()

    server.shutdown()

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} test gecti")
    if failed:
        print("BASARISIZ:")
        for name, _, detail in failed:
            print(" -", name, detail)
    shutil.rmtree(ROOT, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
