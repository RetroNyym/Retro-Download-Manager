import http.server
import os
import shutil
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from download_manager import DownloadManager
from download_manager.gui import (
    AddDialog,
    App,
    GrabberDialog,
    PropertiesDialog,
    SettingsDialog,
)

ROOT = tempfile.mkdtemp(prefix="pdm_gui_")
DATA_DIR = os.path.join(ROOT, "data")
DL_DIR = os.path.join(ROOT, "dl")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DL_DIR, exist_ok=True)

RESULTS = []
PAGE = b'<html><a href="/files/a.zip">a</a><img src="/files/b.mp4"><a href="/files/c.pdf">c</a></html>'


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
        if self.path.startswith("/page"):
            body = PAGE
        else:
            body = b"x" * 4096
        self.send_response(200)
        self.send_header("Content-Type", "text/html" if self.path.startswith("/page")
                         else "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    mgr = DownloadManager(data_dir=DATA_DIR)
    mgr.apply_settings({"download_dir": DL_DIR, "bridge_enabled": False,
                        "auto_start": False, "queue_running": False})
    app = App(mgr)
    root = app.root

    def pump(count=8, delay=0.03):
        for _ in range(count):
            root.update()
            time.sleep(delay)

    pump()

    site_buttons = getattr(app, "site_buttons", [])
    check("site butonlari", len(site_buttons) >= 6, str(len(site_buttons)))
    check("site buton yazilari",
          any(b.cget("text") == "YouTube" for b in site_buttons),
          ",".join(b.cget("text") for b in site_buttons))
    site_dialog = AddDialog(root, mgr, site="YouTube")
    check("site penceresi basligi", "YouTube" in site_dialog.title(),
          site_dialog.title())
    check("site penceresi url alani",
          site_dialog.var_url.get() == "" and site_dialog.winfo_exists())
    site_dialog.destroy()

    dialog = AddDialog(root, mgr, initial=f"{base}/files/one.zip")
    check("ekle penceresi acildi", dialog.winfo_exists())
    dialog.var_url.set(f"{base}/files/two.zip")
    dialog.var_time.set("23:55")
    dialog.var_sched.set(True)
    dialog.var_segments.set(6)
    dialog.var_speed.set(1024)
    dialog.txt_headers.insert("1.0", "X-Test: 1")
    dialog._ok()
    result = dialog.result
    check("ekle sonucu olustu", bool(result), str(bool(result)))
    if result:
        check("ekle zamanlandirildi", result["scheduled_at"] is not None)
        check("ekle parca/hiz", result["segments"] == 6 and result["speed_limit"] == 1024,
              f"{result['segments']} {result['speed_limit']}")
        check("ekle ek baslik", result["extra_headers"].get("X-Test") == "1",
              str(result["extra_headers"]))
        app._create_tasks(result)
    pump()
    check("gorev listeye eklendi", len(mgr.tasks) == 1, str(len(mgr.tasks)))
    check("satir olustu", len(app._rows) == 1, str(len(app._rows)))

    batch = AddDialog(root, mgr, batch=True)
    batch.txt_urls.insert("1.0", f"{base}/a.zip\n{base}/b.zip\n# yorum\nbozuk satir\n")
    batch._ok()
    if batch.result:
        app._create_tasks(batch.result)
    pump()
    check("toplu ekleme", len(mgr.tasks) == 3, str(len(mgr.tasks)))

    settings = SettingsDialog(root, mgr)
    settings.var_segments.set(12)
    settings.var_concurrent.set(4)
    settings.var_limit.set(4096)
    settings.var_ftp_user.set("kullanici")
    settings.var_ftp_pass.set("sifre")
    settings.var_bridge.set(True)
    settings.var_bridge_port.set(8901)
    settings.var_folders["other"].set("DigerKlasor")
    settings._ok()
    values = settings.result
    check("ayarlar sonucu", values is not None)
    if values:
        check("ayarlar ftp alani", values["ftp_user"] == "kullanici",
              str(values.get("ftp_user")))
        check("ayarlar kopru alani",
              values["bridge_port"] == 8901 and values["bridge_enabled"] is True,
              str((values.get("bridge_port"), values.get("bridge_enabled"))))
        check("ayarlar kategori klasoru",
              values["category_folders"].get("other") == "DigerKlasor",
              str(values["category_folders"].get("other")))
        mgr.apply_settings(values)
        check("ayarlar uygulandi",
              mgr.settings.segments == 12 and mgr.settings.speed_limit == 4096,
              f"{mgr.settings.segments} {mgr.settings.speed_limit}")

    grabber = GrabberDialog(root, mgr)
    grabber.var_url.set(f"{base}/page")
    grabber.var_depth.set(1)
    grabber._start()
    deadline = time.time() + 20
    while time.time() < deadline and grabber._worker_result is None:
        root.update()
        time.sleep(0.05)
    pump()
    check("grabber tarandi", grabber._worker_result is not None)
    check("grabber sonuc sayisi", grabber.listbox.size() == 3,
          str(grabber.listbox.size()))
    grabber.destroy()

    task = mgr.tasks[0]
    props = PropertiesDialog(root, mgr, task)
    props.var_subdir.set("alt/klasor")
    props.var_speed.set(2048)
    props._save()
    check("ozellikler kaydedildi",
          task.subdir == "alt/klasor" and task.speed_limit == 2048,
          f"{task.subdir} {task.speed_limit}")

    app._sync_rows()
    app._update_details()
    app._update_status()
    app._drain_logs()
    app._refresh_history()
    pump()
    check("arayuz yenilendi", len(app._rows) == 3, str(len(app._rows)))
    check("durum cubugu", "Kuyruk" in app.var_status_left.get(),
          app.var_status_left.get()[:60])
    check("gunluk dolu", len(app.log_text.get("1.0", "end")) > 10)

    app._apply("pause")
    pump()
    check("toplu duraklat hatasi vermedi", True)

    root.destroy()
    mgr.shutdown()
    server.shutdown()

    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} gui test gecti")
    shutil.rmtree(ROOT, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())


