"""Portal başvuruları için ekran görüntüsü üretir.

Yerel, `Range` destekli bir HTTP sunucusu açar, birkaç indirmeyi aynı anda
çalıştırır ve arayüzün dört farklı ekranını docs/screenshots/ altına PNG olarak
yazar:

    gui-downloads.png   ana pencere (canlı indirme + segment detayları)
    gui-add-link.png    "İndirme Ekle" penceresi
    gui-grabber.png     Site Grabber penceresi (tarama sonucu dolu)
    gui-settings.png    Ayarlar penceresi

Çalıştırma:  python tools/shots.py
Herhangi bir internet bağlantısı kullanılmaz; sunucu yalnızca 127.0.0.1'dedir.
"""
import ctypes
import http.server
import os
import shutil
import sys
import tempfile
import threading
import time
from ctypes import wintypes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PIL import Image, ImageGrab  # noqa: E402

from download_manager import DownloadManager  # noqa: E402
from download_manager.engine import COMPLETED  # noqa: E402
from download_manager.gui import AddDialog, App, GrabberDialog, SettingsDialog  # noqa: E402

OUT_DIR = os.path.join(ROOT, "docs", "screenshots")

GA_ROOT = 2
PW_RENDERFULLCONTENT = 2

MB = 1024 * 1024
CHUNK = 16 * 1024
DELAY = 0.05  # 16 KB başına bekleme -> bağlantı başına ~0.3 MB/sn

PAGE = b"""<html><head><title>Ornek sayfa</title></head><body>
<h1>Medya arsivi</h1>
<a href="/files/tanitim-videosu-4k.mp4">video</a>
<a href="/files/proje-yedekleme-2026.zip">zip</a>
<a href="/files/bolum-01-1080p.mkv">bolum</a>
<a href="/files/ornek-kaynak-kod.pdf">pdf</a>
<img src="/files/tanitim-videosu-4k.mp4" alt="">
</body></html>"""

FILES = {
    "/page.html": {"data": PAGE, "ctype": "text/html", "range": False, "delay": 0},
    "/ornek-dosya.txt": {"data": b"Retro+ Download Manager\n" * 20000,
                         "ctype": "text/plain", "range": True, "delay": 0},
    "/files/tanitim-videosu-4k.mp4": {"data": b"V" * (96 * MB),
                                      "ctype": "video/mp4", "range": True, "delay": DELAY},
    "/files/proje-yedekleme-2026.zip": {"data": b"Z" * (64 * MB),
                                        "ctype": "application/zip", "range": True, "delay": DELAY},
    "/files/bolum-01-1080p.mkv": {"data": b"M" * (48 * MB),
                                  "ctype": "video/x-matroska", "range": True, "delay": DELAY},
    "/files/kaynak-kod-arsivi.zip": {"data": b"K" * (32 * MB),
                                     "ctype": "application/zip", "range": True, "delay": DELAY},
    "/files/ornek-kaynak-kod.pdf": {"data": b"%PDF-1.4\n" + b"P" * (2 * MB),
                                    "ctype": "application/pdf", "range": True, "delay": 0},
}


class QuietServer(http.server.ThreadingHTTPServer):
    """İstemci bağlantıları kapatınca oluşan gürültüyü bastırır."""

    def handle_error(self, request, client_address):
        pass

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def do_HEAD(self):
        self._serve(head=True)

    def do_GET(self):
        self._serve(head=False)

    def _serve(self, head):
        entry = FILES.get(self.path.split("?")[0])
        if not entry:
            self.send_error(404)
            return
        data = entry["data"]
        total = len(data)
        rng = self.headers.get("Range") if entry.get("range") else None
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
        self.send_header("Content-Type", entry.get("ctype", "application/octet-stream"))
        self.send_header("Content-Length", str(len(chunk)))
        if entry.get("range"):
            self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        if head:
            return
        delay = entry.get("delay", 0)
        if delay:
            for offset in range(0, len(chunk), CHUNK):
                self.wfile.write(chunk[offset:offset + CHUNK])
                time.sleep(delay)
        else:
            self.wfile.write(chunk)


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def hwnd_of(widget):
    user32 = ctypes.windll.user32
    return user32.GetAncestor(int(widget.winfo_id()), GA_ROOT)


def capture(widget, path):
    """Pencereyi PrintWindow ile yakalar; başarısız olursa ekran görüntüsüne düşer."""
    user32 = ctypes.windll.user32
    g32 = ctypes.windll.gdi32
    hwnd = hwnd_of(widget)
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
    width, height = right - left, bottom - top
    if width <= 0 or height <= 0:
        raise RuntimeError("pencere ölçüleri geçersiz")

    img = None
    hdc = user32.GetWindowDC(hwnd)
    if hdc:
        mem = g32.CreateCompatibleDC(hdc)
        bmp = g32.CreateCompatibleBitmap(hdc, width, height)
        g32.SelectObject(mem, bmp)
        user32.PrintWindow(hwnd, mem, PW_RENDERFULLCONTENT)
        info = BITMAPINFOHEADER()
        info.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.biWidth = width
        info.biHeight = -height  # yukarıdan aşağıya
        info.biPlanes = 1
        info.biBitCount = 32
        info.biCompression = 0
        buf = ctypes.create_string_buffer(width * height * 4)
        g32.GetDIBits(mem, bmp, 0, height, buf, ctypes.byref(info), 0)
        img = Image.frombuffer("RGB", (width, height), buf.raw, "raw", "BGRX", 0, 1)
        g32.DeleteObject(bmp)
        g32.DeleteDC(mem)
        user32.ReleaseDC(hwnd, hdc)
        extrema = img.convert("L").getextrema()
        if extrema[1] < 16:  # tamamen kara çıktı
            img = None

    if img is None:
        img = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG")
    print(f"[shot] {os.path.relpath(path, ROOT)}  {img.width}x{img.height}")
    return path


def pump(root, seconds=0.2):
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        time.sleep(0.03)


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

    server = QuietServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    tmp = tempfile.mkdtemp(prefix="retro_shots_")
    data_dir = os.path.join(tmp, "data")
    dl_dir = os.path.join(tmp, "indirilenler")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(dl_dir, exist_ok=True)

    mgr = DownloadManager(data_dir=data_dir)
    mgr.apply_settings({"download_dir": dl_dir, "bridge_enabled": False,
                        "auto_start": False, "queue_running": False,
                        "max_concurrent": 3, "segments": 8})

    app = App(mgr)
    root = app.root
    pump(root, 0.4)

    base_url = f"{base}/files"
    tasks = mgr.add([
        {"url": f"{base}/ornek-dosya.txt", "filename": "ornek-dosya.txt"},
        {"url": f"{base_url}/tanitim-videosu-4k.mp4"},
        {"url": f"{base_url}/proje-yedekleme-2026.zip"},
        {"url": f"{base_url}/bolum-01-1080p.mkv"},
        {"url": f"{base_url}/kaynak-kod-arsivi.zip", "filename": "kaynak-kod-arsivi.zip"},
    ])
    mgr.start_queue()
    pump(root, 0.5)

    # Canlı indirme birkaç yüzde ilerlesin; ilk (küçük) dosya da tamamlansın.
    main_task = tasks[1]
    deadline = time.time() + 90
    while time.time() < deadline:
        pump(root, 0.25)
        snap = main_task.snapshot()
        first_state = tasks[0].snapshot().get("state")
        if snap.get("percent", 0) >= 14 and first_state == COMPLETED:
            break
        if snap.get("percent", 0) >= 40:
            break
    pump(root, 1.0)

    try:
        if app.tree.exists(main_task.id):
            app.tree.selection_set(main_task.id)
            app.tree.focus(main_task.id)
    except Exception:
        pass
    app._sync_rows()
    app._update_details()
    app._update_status()
    pump(root, 1.5)
    capture(root, os.path.join(OUT_DIR, "gui-downloads.png"))

    # 2) İndirme Ekle penceresi
    dlg = AddDialog(root, mgr, initial="https://www.youtube.com/watch?v=aqz-KE-bpKQ")
    dlg.var_segments.set(16)
    dlg.var_speed.set(4096)
    dlg.var_subdir.set("videolar")
    pump(root, 0.6)
    capture(dlg, os.path.join(OUT_DIR, "gui-add-link.png"))
    dlg.destroy()

    # 3) Site Grabber penceresi (tarama sonucu dolu)
    grabber = GrabberDialog(root, mgr)
    grabber.var_url.set(f"{base}/page.html")
    grabber.var_depth.set(1)
    pump(root, 0.4)
    grabber._start()
    deadline = time.time() + 30
    while time.time() < deadline and grabber._worker_result is None:
        pump(root, 0.2)
    pump(grabber, 0.8)
    if grabber.listbox.size() >= 4:
        grabber.listbox.selection_set(0, 2)
    pump(grabber, 0.4)
    capture(grabber, os.path.join(OUT_DIR, "gui-grabber.png"))
    grabber.destroy()

    # 4) Ayarlar penceresi
    settings = SettingsDialog(root, mgr)
    pump(root, 0.6)
    capture(settings, os.path.join(OUT_DIR, "gui-settings.png"))
    settings.destroy()

    root.destroy()
    mgr.shutdown()
    server.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)
    print("[done] ekran goruntuleri hazir:", OUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
