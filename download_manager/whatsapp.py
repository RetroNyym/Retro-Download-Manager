"""WhatsApp PDF yakalama (Python tarafı).

whatsapp_listener (Node/Baileys) beyaz listedeki sohbetlerden gelen PDF'leri
izleme klasörüne (.pdf + yanına .pdf.json üst veri) bırakır; bu modül
klasörü tarar, beyaz liste kontrolünden geçirip hedef klasöre taşır ve
günlüğe yazar.

Üst veri (yan dosya) örneği:
    {"chat": "123456789-1111@g.us", "sender": "905..@s.whatsapp.net",
     "label": "Fatura Grubu", "name": "fatura_ekim.pdf", "timestamp": 1717...}
"""

from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path

SCAN_INTERVAL = 3.0


def load_meta(pdf_path):
    """Yanındaki .json üst verisini okur; yoksa {} döner."""
    sidecar = Path(str(pdf_path) + ".json")
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def is_allowed(meta, whitelist):
    """Beyaz liste kontrolü.

    - whitelist boşsa hiçbir PDF kabul edilmez (seçim yapılmamış = kapalı).
    - eşleşme: meta['chat'] birebir jid veya listedeki jid'in gövdesiyle
      başlıyor (ör. '+905...' gibi numara girdiyse).
    """
    if not whitelist:
        return False
    chat = str((meta or {}).get("chat") or "").strip()
    sender = str((meta or {}).get("sender") or "").strip()
    if not chat and not sender:
        return False
    for entry in whitelist:
        jid = str(entry if isinstance(entry, str)
                  else (entry or {}).get("jid") or "").strip()
        if not jid:
            continue
        body = jid.split("@", 1)[0]
        for value in (chat, sender):
            if not value:
                continue
            if value == jid or value.split("@", 1)[0] == body:
                return True
    return False


def normalize_whitelist(entries):
    """Ayarlar alanındaki listeyi [{'jid','label'}] biçimine getirir."""
    out = []
    for entry in entries or []:
        if isinstance(entry, str):
            jid = entry.strip()
            if jid:
                out.append({"jid": jid, "label": jid.split("@", 1)[0]})
        elif isinstance(entry, dict):
            jid = str(entry.get("jid") or "").strip()
            if jid:
                out.append({"jid": jid,
                            "label": str(entry.get("label") or jid.split("@", 1)[0])})
    return out


def default_output_folder(download_dir):
    return str(Path(download_dir) / "WhatsApp PDF")


class WhatsAppWatcher:
    """İzleme klasöründeki PDF'leri beyaz listeden geçirip hedefe taşır."""

    def __init__(self, manager):
        self.manager = manager
        self._stop = threading.Event()
        self._thread = None
        self.processed = set()
        self.imported = 0
        self._empty_warned = False

    # -- yaşam döngüsü -----------------------------------------------------
    @property
    def enabled(self):
        return bool(getattr(self.manager.settings, "wa_enabled", False))

    @property
    def watch_folder(self):
        return str(getattr(self.manager.settings, "wa_watch_folder", "") or "")

    @property
    def output_folder(self):
        configured = str(getattr(self.manager.settings, "wa_output_folder", "") or "")
        if configured:
            return configured
        return default_output_folder(self.manager.settings.download_dir)

    @property
    def whitelist(self):
        return normalize_whitelist(getattr(self.manager.settings, "wa_whitelist", []))

    def start(self):
        if not self.enabled or self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.manager.log("WhatsApp PDF izleyici başlatıldı.", "info")

    def stop(self):
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread and thread.is_alive():
            thread.join(timeout=5.0)

    def restart(self):
        self.stop()
        self.start()

    # -- tarama ------------------------------------------------------------
    def _loop(self):
        while not self._stop.wait(SCAN_INTERVAL):
            try:
                self.scan_once()
            except Exception as exc:
                self.manager.log(f"WhatsApp tarama hatası: {exc}", "error")

    def scan_once(self):
        if not self.enabled:
            return 0
        folder = Path(self.watch_folder).expanduser()
        if not folder.is_dir():
            return 0
        whitelist = self.whitelist
        if not whitelist and not self._empty_warned:
            self.manager.log("WhatsApp: beyaz liste boş — henüz hiçbir sohbet "
                             "seçilmedi (Ayarlar → WhatsApp).", "warning")
            self._empty_warned = True
        taken = 0
        for pdf in sorted(folder.glob("*.pdf")):
            if str(pdf) in self.processed:
                continue
            meta = load_meta(pdf)
            if not is_allowed(meta, whitelist):
                self.processed.add(str(pdf))
                self.manager.log(f"WhatsApp: beyaz liste dışı PDF atlandı: "
                                 f"{pdf.name}", "warning")
                continue
            if self._deliver(pdf, meta):
                taken += 1
        return taken

    def _deliver(self, pdf_path, meta):
        target_dir = Path(self.output_folder).expanduser()
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.manager.log(f"WhatsApp hedef klasörü açılamadı: {exc}", "error")
            return False
        name = str(meta.get("name") or pdf_path.name)
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        target = target_dir / name
        counter = 1
        while target.exists():
            target = target_dir / f"{Path(name).stem}_{counter}.pdf"
            counter += 1
        try:
            shutil.move(str(pdf_path), str(target))
            sidecar = Path(str(pdf_path) + ".json")
            if sidecar.exists():
                sidecar.unlink()
        except OSError:
            try:
                shutil.copy2(str(pdf_path), str(target))
                pdf_path.unlink()
                sidecar = Path(str(pdf_path) + ".json")
                if sidecar.exists():
                    sidecar.unlink()
            except OSError as exc:
                self.manager.log(f"WhatsApp dosyası taşınamadı: {exc}", "error")
                return False
        source = str(meta.get("label") or meta.get("chat") or "bilinmeyen")
        size = target.stat().st_size
        self.processed.add(str(pdf_path))
        self.imported += 1
        self._empty_warned = False
        self.manager.log(f"WhatsApp PDF alındı: {target.name} "
                         f"({size:,} bayt) — {source}", "success")
        return True


__all__ = ["WhatsAppWatcher", "load_meta", "is_allowed", "normalize_whitelist",
           "default_output_folder", "SCAN_INTERVAL"]
