import hashlib
import http.server
import os
import shutil
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from download_manager import DownloadManager
from download_manager.engine import COMPLETED, ERROR

ROOT = tempfile.mkdtemp(prefix="pdm_page_")
DATA_DIR = os.path.join(ROOT, "data")
DL_DIR = os.path.join(ROOT, "downloads")

MOVIE = os.urandom(3 * 1024 * 1024)
MOVIE_HASH = hashlib.sha256(MOVIE).hexdigest()

PAGE = (b"<html><head><meta property=\"og:video\" content=\"/files/movie.mp4\">"
        b"</head><body>video sayfasi</body></html>")
BARE_PAGE = b"<html><body>burada medya yok, sadece metin</body></html>"
SAVED_PAGE = b"<html><body>kaydedilecek sayfa</body></html>"


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
        if path == "/watch":
            self._page(PAGE, head)
            return
        if path == "/empty":
            self._page(BARE_PAGE, head)
            return
        if path == "/page.html":
            self._page(SAVED_PAGE, head)
            return
        if path == "/files/movie.mp4":
            data = MOVIE
            ctype = "video/mp4"
        else:
            self.send_error(404)
            return
        rng = self.headers.get("Range")
        total = len(data)
        if rng and rng.startswith("bytes="):
            start_s, _, end_s = rng[6:].partition("-")
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
        self.end_headers()
        if not head:
            self.wfile.write(chunk)

    def _page(self, body, head):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head:
            self.wfile.write(body)


results = []


def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    print(f"[{'OK  ' if condition else 'FAIL'}] {name} {detail}")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def wait_for(predicate, timeout=60, interval=0.15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


def new_manager():
    shutil.rmtree(DATA_DIR, ignore_errors=True)
    shutil.rmtree(DL_DIR, ignore_errors=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DL_DIR, exist_ok=True)
    mgr = DownloadManager(data_dir=DATA_DIR)
    mgr.apply_settings({"download_dir": DL_DIR, "auto_start": True,
                        "queue_running": True, "max_concurrent": 2,
                        "segments": 4, "retries": 3})
    return mgr


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    mgr = new_manager()
    try:
        task = mgr.add(f"{base}/watch")[0]
        wait_for(lambda: task.state in (COMPLETED, ERROR))
        check("video sayfasi indirildi", task.state == COMPLETED,
              task.state + (f" {task.error}" if task.error else ""))
        check("dosya adi movie.mp4", task.filename == "movie.mp4", str(task.filename))
        path = os.path.join(DL_DIR, "Video", "movie.mp4")
        check("video klasorunde", os.path.exists(path), path)
        if os.path.exists(path):
            check("video sha256", sha256(path) == MOVIE_HASH)
        check("video kategorisi", task.category == "video", task.category)

        bare = mgr.add(f"{base}/empty")[0]
        wait_for(lambda: bare.state in (COMPLETED, ERROR))
        check("medyasiz sayfa hata verdi", bare.state == ERROR, str(bare.state))
        check("hata aciklamasi", bool(bare.error) and "medya" in (bare.error or ""),
              str(bare.error))
        check("hatali sayfa dosya olusturmedi",
              not os.path.exists(os.path.join(DL_DIR, "Diğer", "empty")))

        page = mgr.add(f"{base}/page.html")[0]
        wait_for(lambda: page.state in (COMPLETED, ERROR))
        check("uzantili html dosya olarak indi", page.state == COMPLETED,
              str(page.state))
        saved = os.path.join(DL_DIR, "Diğer", "page.html")
        check("html dosyasi olustu", os.path.exists(saved), saved)

        entry = {"url": f"{base}/files/movie.mp4", "filename": "elle-adi.mp4",
                 "headers": {"X-Test": "1"}}
        added = mgr.add([entry])[0]
        check("dict giris filename", added.user_filename == "elle-adi.mp4",
              str(added.user_filename))
        check("dict giris header", added.extra_headers.get("X-Test") == "1",
              str(added.extra_headers))

        from download_manager.extractor import (
            SUPPORTED_SITES,
            site_name,
            sniff_media,
            ytdlp_available,
        )
        found = sniff_media(PAGE.decode(), base + "/watch")
        check("sniff og:video", found == [f"{base}/files/movie.mp4"], str(found))
        check("sniff stream atlama",
              not sniff_media('<video src="https://x.test/a.m3u8"></video>', "https://x.test/"))
        check("yt-dlp gorunurluk", ytdlp_available() is True, str(ytdlp_available()))
        check("site listesi", len(SUPPORTED_SITES) >= 6, str(len(SUPPORTED_SITES)))
        check("site adi youtube",
              site_name("https://www.youtube.com/watch?v=abc") == "YouTube",
              str(site_name("https://www.youtube.com/watch?v=abc")))
        check("site adi kisa youtube",
              site_name("https://youtu.be/abc") == "YouTube",
              str(site_name("https://youtu.be/abc")))
        check("site adi instagram",
              site_name("https://www.instagram.com/p/xyz/") == "Instagram",
              str(site_name("https://www.instagram.com/p/xyz/")))
        check("site adi x",
              site_name("https://x.com/kullanici/status/1") == "X (Twitter)",
              str(site_name("https://x.com/kullanici/status/1")))
        check("site adi bilinmeyen", site_name("https://ornek.com/video.mp4") is None,
              str(site_name("https://ornek.com/video.mp4")))
    finally:
        mgr.shutdown()
        server.shutdown()
        shutil.rmtree(ROOT, ignore_errors=True)

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} sayfa/medya test gecti")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
