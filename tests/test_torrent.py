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
from download_manager.torrent import TorrentEngine, aria2_yolu

ROOT = tempfile.mkdtemp(prefix="pdm_torrent_")
DATA_DIR = os.path.join(ROOT, "data")
DL_DIR = os.path.join(ROOT, "dl")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DL_DIR, exist_ok=True)

PAYLOAD = os.urandom(512 * 1024)
EXPECTED = hashlib.sha256(PAYLOAD).hexdigest()
RESULTS = []
BRIDGE_PORT = 8898
RPC_PORT = 6900


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition)))
    print(f"[{'OK  ' if condition else 'FAIL'}] {name} {detail}")


def wait_for(predicate, timeout=45):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.2)
    return False


def get_json(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)


def main():
    yol = aria2_yolu()
    check("aria2 yolu bulundu", bool(yol) and os.path.isfile(yol), yol)

    engine = TorrentEngine(DATA_DIR, lambda: DL_DIR, port=RPC_PORT)
    check("motor baslatildi", engine.baslat(), "bekle=10")
    try:
        surum = engine._rpc("aria2.getVersion").get("result", {}).get("version", "")
        check("rpc ping (getVersion)", bool(surum), surum)
    except Exception as exc:
        check("rpc ping (getVersion)", False, str(exc))

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # --- engine: HTTP uzerinden tam indirme (aria2 calisiyor mu) ---
    url = f"http://127.0.0.1:{port}/dosya.bin"
    try:
        gid = engine.ekle(url)
        check("engine ekle (http uri)", bool(gid), gid[:16])
        bitti = wait_for(
            lambda: any(k["gid"] == gid and k["durum"] == "complete"
                        for k in engine.liste()), timeout=30)
        check("engine indirme tamamlandi", bitti)
        if bitti:
            indirilen = None
            for kok, _d, dosyalar in os.walk(DL_DIR):
                for d in dosyalar:
                    indirilen = os.path.join(kok, d)
            if indirilen:
                h = hashlib.sha256(open(indirilen, "rb").read()).hexdigest()
                check("engine sha256", h == EXPECTED)
            else:
                check("engine sha256", False, "dosya yok")
    except Exception as exc:
        check("engine ekle (http uri)", False, str(exc))

    try:
        engine.durdur()
        time.sleep(0.6)
        check("motor durdu", not engine.ayakta())
    except Exception as exc:
        check("motor durdu", False, str(exc))

    # --- DownloadManager + magnet + bridge uclari ---
    mgr = DownloadManager(data_dir=DATA_DIR)
    mgr.apply_settings({"download_dir": DL_DIR, "auto_start": True,
                        "queue_running": True, "bridge_enabled": True,
                        "bridge_port": BRIDGE_PORT, "torrent_enabled": True,
                        "torrent_port": RPC_PORT + 10})
    time.sleep(0.6)

    try:
        status = get_json(f"http://127.0.0.1:{BRIDGE_PORT}/status")
        check("kopru ayakta", status.get("ok") is True, str(status))
    except Exception as exc:
        check("kopru ayakta", False, str(exc))

    magnet = "magnet:?xt=urn:btih:" + "ab" * 20 + "&dn=deneme-testi"
    try:
        gid = mgr.torrent_add(magnet)
        check("torrent_add magnet", bool(gid), gid[:16])
    except Exception as exc:
        check("torrent_add magnet", False, str(exc))
        gid = ""

    try:
        liste = mgr.torrent_list()
        check("torrent_list dolu", len(liste) >= 1, str(len(liste)))
        if liste:
            k = liste[0]
            gerekli = ("gid", "ad", "durum", "durum_str", "yuzde",
                       "indirme_hizi_str", "yukleme_hizi_str", "boyut_str")
            check("liste alanlari",
                  all(key in k for key in gerekli),
                  str([key for key in gerekli if key not in k]))
    except Exception as exc:
        check("torrent_list dolu", False, str(exc))

    try:
        kayit = json.loads(open(os.path.join(DATA_DIR, "torrents.json"),
                                encoding="utf-8").read())
        check("torrents.json yazildi", any(k.get("gid") == gid for k in kayit),
              str(len(kayit)))
    except Exception as exc:
        check("torrents.json yazildi", False, str(exc))

    # bridge /torrent
    try:
        sonuc = get_json("http://127.0.0.1:%d/torrent?url=%s"
                         % (BRIDGE_PORT, quote(magnet + "2", safe="")))
        check("kopru /torrent ekleme", sonuc.get("ok") is True, str(sonuc))
    except Exception as exc:
        check("kopru /torrent ekleme", False, str(exc))

    # bridge /torrents
    try:
        sonuc = get_json(f"http://127.0.0.1:{BRIDGE_PORT}/torrents")
        check("kopru /torrents listesi",
              sonuc.get("ok") and len(sonuc.get("torrents", [])) >= 2,
              str(sonuc)[:160])
    except Exception as exc:
        check("kopru /torrents listesi", False, str(exc))

    # bridge /torrent eksik parametre
    try:
        sonuc = get_json(f"http://127.0.0.1:{BRIDGE_PORT}/torrent")
        check("kopru /torrent eksik param", sonuc.get("ok") is False, str(sonuc))
    except Exception as exc:
        check("kopru /torrent eksik param", False, str(exc))

    # duraklat / devam / kaldir + kalici kayit siliniyor mu
    if gid:
        try:
            mgr.torrent_action(gid, "duraklat")
            mgr.torrent_action(gid, "devam")
            check("duraklat/devam", True)
        except Exception as exc:
            check("duraklat/devam", False, str(exc))
        try:
            mgr.torrent_action(gid, "kaldir")
            kalan = [k for k in mgr.torrent_list() if k.get("gid") == gid]
            check("kaldir listeden atildi", not kalan, str(kalan)[:120])
            kayit = json.loads(open(os.path.join(DATA_DIR, "torrents.json"),
                                    encoding="utf-8").read())
            check("kaldir kalici kaydi sildi",
                  not any(k.get("gid") == gid for k in kayit),
                  str([k.get("gid") for k in kayit]))
        except Exception as exc:
            check("kaldir", False, str(exc))

    # motor kapaliyken liste bos doner, ekleme hata verir
    try:
        mgr.apply_settings({"torrent_enabled": False})
        time.sleep(0.3)
        check("kapaliyken liste", mgr.torrent_list() == [])
        try:
            mgr.torrent_add(magnet + "3")
            check("kapaliyken ekleme hata", False, "hata vermedi")
        except RuntimeError:
            check("kapaliyken ekleme hata", True)
    except Exception as exc:
        check("torrent kapali ayar", False, str(exc))

    try:
        mgr.apply_settings({"torrent_enabled": True, "torrent_port": RPC_PORT + 20})
        time.sleep(0.3)
        motor = mgr._torrent_engine()  # baslat=True: yeni portta baslamali
        check("tekrar acildi", motor is not None and motor.ayakta())
        eksik = []
        if motor is not None:
            time.sleep(1.0)
            eksik = mgr._torrent_kayit.eksikler()
        check("eksik uri tekrar eklendi",
              all(any(k.get("kaynak") == u for k in mgr.torrent_list())
                  for u in eksik) if eksik else True, str(eksik)[:160])
    except Exception as exc:
        check("tekrar acildi", False, str(exc))

    mgr.shutdown()
    time.sleep(0.8)
    server.shutdown()

    # shutdown'tan sonra hicbir portta aria2 kalmamali
    import socket

    def port_acik(p):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex(("127.0.0.1", p)) == 0

    kalan = [p for p in (RPC_PORT, RPC_PORT + 10, RPC_PORT + 20) if port_acik(p)]
    check("shutdown'ta motor durdu", not kalan, str(kalan))

    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} torrent test gecti")
    shutil.rmtree(ROOT, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
