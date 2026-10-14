"""Torrent destegi — aria2c alt sureci + JSON-RPC sarmalayici.

aria2c.exe `tools/aria2/` altindadir (RETRO_ARIA2 ile disari da verilebilir).
Motor tembel baslar: ilk torrent eklendiginde/istendiginde acilir,
kapatma isleminde surec durdurulur. Kayit (URI + gid) `data/torrents.json`'a
yazilir; motor yeniden baslayinca tamamlanmamis torrentler tekrar eklenir.
"""
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests

RPC_BAS = 6800
RPC_SON = 6819
BILINMEYEN = "Bilinmeyen"
DURUM_ETIKET = {
    "active": "İndiriliyor",
    "waiting": "Sırada",
    "paused": "Duraklatıldı",
    "error": "Hata",
    "complete": "Tamamlandı",
    "removed": "Kaldırıldı",
    "removedComplete": "Tamamlandı",
}
DURUM_ETIKET_GETIR = DURUM_ETIKET.get


def aria2_yolu():
    """aria2c.exe konumunu bul; yoksa bos string."""
    adaylar = []
    env = os.environ.get("RETRO_ARIA2")
    if env:
        adaylar.append(env)
    if getattr(sys, "frozen", False):
        adaylar.append(Path(sys.executable).parent / "tools" / "aria2" / "aria2c.exe")
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        adaylar.append(Path(meipass) / "tools" / "aria2" / "aria2c.exe")
    adaylar.append(Path(__file__).resolve().parent.parent / "tools" / "aria2" / "aria2c.exe")
    yol = shutil.which("aria2c")
    if yol:
        adaylar.append(yol)
    for aday in adaylar:
        try:
            if aday and Path(aday).is_file():
                return str(aday)
        except OSError:
            pass
    return ""


def _sayi(deger, varsayilan=0):
    try:
        return int(deger)
    except (TypeError, ValueError):
        return varsayilan


def _biim(bayt):
    try:
        bayt = float(bayt or 0)
    except (TypeError, ValueError):
        bayt = 0.0
    for birim in ("B", "KB", "MB", "GB", "TB"):
        if bayt < 1024 or birim == "TB":
            if birim == "B":
                return "%d B" % bayt
            return "%.1f %s" % (bayt, birim)
        bayt /= 1024.0
    return "%.1f TB" % bayt


class TorrentEngine:
    """aria2c sureci + JSON-RPC istemcisi."""

    def __init__(self, data_dir, hedef_klasor, port=RPC_BAS):
        self.data_dir = Path(data_dir)
        self.hedef_klasor = hedef_klasor  # callable -> str
        self.port = int(port or RPC_BAS)
        self.token = secrets.token_hex(12)
        self.proc = None
        self._aktif_port = None
        self._lock = threading.RLock()  # baslat -> durdur icin yeniden girilebilir
        self._exe = aria2_yolu()

    # ------------------------------------------------------------- surec ----
    def exe_var(self):
        return bool(self._exe)

    def baslat(self, bekle=8.0):
        """aria2c baslat; RPC'ye kadar bekle. True/False.

        _son_baslat_yeni: bu cagri gercekten yeni surec baslattisa True
        (zaten ayakta iken donulen True'da False) - geri yukleme icin.
        """
        with self._lock:
            if self.ayakta():
                self._son_baslat_yeni = False
                return True
            if not self._exe:
                return False
            # yanit vermeyen ama yas gorunen eski surec varsa once onu temizle
            # (orphan + ek port tuketimi engellenir; ayni port yeniden secilir)
            if self.proc is not None:
                self.durdur(zorla=True)
            klasor = str(self.hedef_klasor() or Path.home() / "Downloads")
            os.makedirs(klasor, exist_ok=True)
            port = None
            for aday in range(self.port, self.port + 20):  # 6800..6819 gibi 20'lik arama
                if self._port_bos(aday):
                    port = aday
                    break
            if port is None:
                return False
            komut = [
                self._exe,
                "--enable-rpc=true",
                "--rpc-listen-all=false",
                "--rpc-listen-port=%d" % port,
                "--rpc-secret=%s" % self.token,
                "--dir=%s" % klasor,
                "--file-allocation=none",
                "--auto-file-renaming=true",
                "--max-concurrent-downloads=3",
                "--max-connection-per-server=4",
                "--split=4",
                "--bt-max-peers=60",
                "--listen-port=6881-6899",
                "--summary-interval=0",
                "--show-console-readout=false",
                "--console-log-level=warn",
                "--log-level=warn",
            ]
            kip = 0x08000000  # CREATE_NO_WINDOW
            try:
                self.proc = subprocess.Popen(
                    komut,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=kip,
                )
            except OSError:
                return False
            self._aktif_port = port
            son = time.time() + bekle
            while time.time() < son:
                if self.ping():
                    self._son_baslat_yeni = True
                    return True
                if self.proc.poll() is not None:
                    break
                time.sleep(0.2)
            self.durdur(zorla=True)
            return False

    def ayakta(self):
        # tek ping yanıtsız kalabilir (yük altında) -> 3 deneme, yanlis-negatif azalt
        for i in range(3):
            if self.ping():
                return True
            if i < 2:
                time.sleep(0.3)
        return False

    def ping(self):
        try:
            yanit = self._rpc("aria2.getVersion", [], timeout=2)
            return bool(yanit and yanit.get("result"))
        except Exception:
            return False

    def durdur(self, zorla=False):
        with self._lock:
            proc, self.proc = self.proc, None
            port, self._aktif_port = self._aktif_port, None
        if proc is None:
            return
        try:
            self._rpc("aria2.shutdown", [], timeout=2, port=port)
        except Exception:
            pass
        son = time.time() + (0.5 if zorla else 3.0)
        while time.time() < son:
            if proc.poll() is not None:
                return
            time.sleep(0.1)
        try:
            proc.kill()
        except OSError:
            pass
        # kill dogrulama: hala yasiyorsa taskkill ile zorla
        son = time.time() + 1.5
        while time.time() < son:
            if proc.poll() is not None:
                return
            time.sleep(0.1)
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=3, creationflags=0x08000000)
        except Exception:
            pass
        # son dogrulama: hala yasiyorsa bir kez daha kill + bekle
        son = time.time() + 2.0
        while time.time() < son:
            if proc.poll() is not None:
                return
            time.sleep(0.1)
        try:
            proc.kill()
        except OSError:
            pass

    @staticmethod
    def _port_bos(port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex(("127.0.0.1", port)) != 0

    # --------------------------------------------------------------- rpc ----
    def _rpc(self, method, params=None, timeout=8, port=None):
        port = port or self._aktif_port
        if not port:
            raise RuntimeError("aria2 baslamadi")
        govde = {
            "jsonrpc": "2.0",
            "id": "retro",
            "method": method,
            "params": ["token:" + self.token] + list(params or []),
        }
        oturum = requests.Session()
        oturum.trust_env = False  # yerel RPC sistem proxy'sine takilmaz
        try:
            yanit = oturum.post(
                "http://127.0.0.1:%d/jsonrpc" % port,
                json=govde,
                timeout=timeout,
            )
        finally:
            oturum.close()
        veri = yanit.json()
        if veri.get("error"):
            raise RuntimeError("aria2: %s" % veri["error"].get("message"))
        return veri

    # ---------------------------------------------------------- islemler ----
    def ekle(self, kaynak):
        """magnet / http(s) .torrent / yerel .torrent yolu -> gid."""
        if not self.ayakta() and not self.baslat():
            raise RuntimeError("aria2 motoru başlatılamadı (tools/aria2/aria2c.exe?)")
        kaynak = (kaynak or "").strip()
        if not kaynak:
            raise ValueError("boş kaynak")
        if kaynak.startswith("magnet:") or kaynak.startswith(("http://", "https://")):
            yanit = self._rpc("aria2.addUri", [[kaynak]])
        else:
            yol = Path(kaynak).expanduser()
            if not yol.is_file():
                raise ValueError("dosya yok: %s" % kaynak)
            veri = yol.read_bytes()
            if veri[:1] == b"d" and b"announce" in veri[:512]:
                import base64
                yanit = self._rpc(
                    "aria2.addTorrent",
                    [base64.b64encode(veri).decode("ascii"), [], {}],
                )
            elif kaynak.startswith("magnet:") or kaynak.startswith("http"):
                yanit = self._rpc("aria2.addUri", [[kaynak]])
            else:
                raise ValueError(".torrent dosyası değil: %s" % kaynak)
        return yanit.get("result") or ""

    def liste(self):
        """Aktif + bekleyen + durmus torrentler (teklesik liste)."""
        if not self.ayakta():
            return []
        klasor = str(self.hedef_klasor() or "")
        parcalar = []
        for yontem in ("aria2.tellActive", "aria2.tellWaiting", "aria2.tellStopped"):
            param = [0, 500] if yontem != "aria2.tellActive" else []
            try:
                yanit = self._rpc(yontem, param)
                parcalar.extend(yanit.get("result") or [])
            except Exception:
                pass
        cikti = []
        for kayit in parcalar:
            gid = kayit.get("gid", "")
            secenek = kayit.get("options") or {}
            uri = ""
            kaynaklar = kayit.get("files") or []
            if kaynaklar:
                uri = (kaynaklar[0].get("uris") or [{}])[0].get("uri", "") \
                    if kaynaklar[0].get("uris") else ""
            tamamlanan = _sayi(kayit.get("completedLength"))
            toplam = _sayi(kayit.get("totalLength"))
            yuzde = (100.0 * tamamlanan / toplam) if toplam else (
                100.0 if _sayi(kayit.get("completedLength")) and
                kayit.get("status") == "complete" else 0.0)
            bitt_mi = kayit.get("status") in ("complete", "removedComplete") or \
                (toplam and tamamlanan >= toplam)
            ad = kayit.get("bittorrent", {}).get("info", {}).get("name") or ""
            if not ad and uri:
                ad = uri.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
            if not ad:
                ad = gid[:8] or BILINMEYEN
            durum = kayit.get("status") or "waiting"
            if durum in ("removed", "removedComplete"):
                continue  # kaldirinan temizlenememis sonuc artigi: gizle
            if bitt_mi and durum in ("active", "waiting", "paused"):
                durum = "complete"
            cikti.append({
                "gid": gid,
                "ad": ad,
                "kaynak": uri or (secenek.get("dir") and "") or "",
                "boyut": _sayi(kayit.get("totalLength")),
                "boyut_str": _biim(toplam),
                "tamamlanan_str": _biim(tamamlanan),
                "yuzde": round(yuzde, 1),
                "indirme_hizi": _sayi(kayit.get("downloadSpeed")),
                "indirme_hizi_str": _biim(kayit.get("downloadSpeed")) + "/sn",
                "yukleme_hizi": _sayi(kayit.get("uploadSpeed")),
                "yukleme_hizi_str": _biim(kayit.get("uploadSpeed")) + "/sn",
                "tohum": _sayi(kayit.get("numSeeders")),
                "es": _sayi(kayit.get("connections")),
                "durum": durum,
                "durum_str": DURUM_ETIKET_GETIR(durum, durum),
                "klasor": (kaynaklar[0].get("path") if kaynaklar else "") or
                          secenek.get("dir") or klasor,
                "hata": (kayit.get("errorMessage") or "")[:300],
            })
        cikti.sort(key=lambda k: (k["durum"] != "active", -k["indirme_hizi"]))
        return cikti

    def _durum(self, gid):
        """GID'in aria2 durumu; bulunamazsa None."""
        try:
            yanit = self._rpc("aria2.tellStatus", [gid])
            return (yanit.get("result") or {}).get("status")
        except RuntimeError:
            return None

    def duraklat(self, gid):
        try:
            self._rpc("aria2.pause", [gid])
            return True
        except RuntimeError:
            pass
        durum = self._durum(gid)
        # zaten durmus sayilan durumlar: hedefe ulasilmissa basari
        if durum in ("paused", "complete", "error", "removed"):
            return True
        if durum is None:
            raise RuntimeError("torrent bulunamadı: %s" % gid[:8])
        # aria2 yarisi: kisa bekle + tekrar dene
        time.sleep(0.3)
        self._rpc("aria2.pause", [gid])
        return True

    def devam(self, gid):
        try:
            self._rpc("aria2.unpause", [gid])
            return True
        except RuntimeError:
            pass
        durum = self._durum(gid)
        if durum in ("active", "waiting"):
            return True
        if durum == "error":
            self._rpc("aria2.retryDownload", [gid])  # hatali indirmeyi yeniden dene
            return True
        if durum is None:
            raise RuntimeError("torrent bulunamadı: %s" % gid[:8])
        time.sleep(0.3)
        self._rpc("aria2.unpause", [gid])
        return True

    def kaldir(self, gid, dosyalar=False):
        # aria2 dosyayi silmez; yalnizca kaydi durdurur ve listeden atar
        try:
            self._rpc("aria2.remove", [gid])
        except RuntimeError:
            try:
                self._rpc("aria2.forceRemove", [gid])
            except RuntimeError:
                pass
        # removed kaydinin result'a dusmesi zaman alir: kisa bekle + tekrar dene
        for _ in range(3):
            time.sleep(0.2)
            try:
                self._rpc("aria2.removeDownloadResult", [gid])
                return True
            except RuntimeError:
                continue
        return True

    def klasoru_ac(self, klasor):
        if not klasor:
            return False
        try:
            if sys.platform == "win32":
                os.startfile(klasor)  # noqa: S606
            else:
                subprocess.Popen(["xdg-open", klasor])
            return True
        except OSError:
            return False


# ------------------------------------------------------------- kalıcılık ---
class TorrentKayit:
    """Eklenen URI'leri saklar; motor yeniden baslayinca eksikleri tekrar ekler."""

    def __init__(self, data_dir):
        self.yol = Path(data_dir) / "torrents.json"
        self._kilit = threading.Lock()
        self.kayitlar = self._oku()

    def _oku(self):
        try:
            veri = json.loads(self.yol.read_text(encoding="utf-8"))
            if isinstance(veri, list):
                return veri
        except (OSError, ValueError):
            pass
        return []

    def kaydet(self):
        try:
            gecici = self.yol.with_suffix(".tmp")
            gecici.write_text(
                json.dumps(self.kayitlar, ensure_ascii=False, indent=1),
                encoding="utf-8",
            )
            os.replace(gecici, self.yol)
        except OSError:
            pass

    def ekle(self, uri, gid=""):
        with self._kilit:
            for kayit in self.kayitlar:
                if kayit.get("uri") == uri:
                    kayit["gid"] = gid or kayit.get("gid", "")
                    kayit["durum"] = "eklendi"
                    self.kaydet()
                    return
            self.kayitlar.append({
                "uri": uri,
                "gid": gid,
                "eklenme": time.strftime("%Y-%m-%d %H:%M:%S"),
                "durum": "eklendi",
            })
            self.kaydet()

    def gid_guncelle(self, uri, gid):
        with self._kilit:
            for kayit in self.kayitlar:
                if kayit.get("uri") == uri:
                    kayit["gid"] = gid
                    self.kaydet()
                    return

    def tamam_isaretle(self, uri):
        with self._kilit:
            for kayit in self.kayitlar:
                if kayit.get("uri") == uri:
                    kayit["durum"] = "tamam"
                    self.kaydet()
                    return

    def sil(self, uri):
        with self._kilit:
            self.kayitlar = [k for k in self.kayitlar if k.get("uri") != uri]
            self.kaydet()

    def uri_bul(self, gid):
        with self._kilit:
            for kayit in self.kayitlar:
                if gid and kayit.get("gid") == gid:
                    return kayit.get("uri") or ""
        return ""

    def gid_bul(self, uri):
        with self._kilit:
            for kayit in self.kayitlar:
                if kayit.get("uri") == uri:
                    return kayit.get("gid") or ""
        return ""

    def eksikler(self):
        """Tamamlanmamis URI'ler (motor yeniden baslarken tekrar eklenir)."""
        with self._kilit:
            return [k.get("uri") for k in self.kayitlar
                    if k.get("uri") and k.get("durum") != "tamam"]
