"""Retro+ Download Manager Tkinter arayüzü."""

from __future__ import annotations

import json
import os
import threading
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .engine import (
    CANCELED,
    COMPLETED,
    DOWNLOADING,
    ERROR,
    PAUSED,
    PROBING,
    QUEUED,
    SCHEDULED,
    STATE_LABELS,
)
from .extractor import SUPPORTED_SITES
from .manager import DownloadManager
from .whatsapp import normalize_whitelist
from .util import (
    CATEGORIES,
    CATEGORY_LABELS,
    format_bytes,
    format_datetime,
    format_eta,
    format_speed,
    looks_like_url,
)

TREE_COLUMNS = ("filename", "size", "speed", "eta", "segments", "percent", "state")
TREE_HEADINGS = {
    "filename": "Ad",
    "size": "Boyut",
    "speed": "Hız",
    "eta": "Kalan süre",
    "segments": "Parça",
    "percent": "Yüzde",
    "state": "Durum",
}
TREE_WIDTHS = {
    "filename": 360,
    "size": 95,
    "speed": 105,
    "eta": 95,
    "segments": 60,
    "percent": 70,
    "state": 120,
}
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
HEADER_BG = "#0e2a3f"
SITE_ICONS = {
    "YouTube": "youtube",
    "Instagram": "instagram",
    "X (Twitter)": "twitter",
    "Facebook": "facebook",
    "TikTok": "tiktok",
    "Vimeo": "vimeo",
}
CATEGORY_ITEMS = (
    ("all", "Tüm indirmeler"),
    ("active", "Devam eden"),
    ("queued", "Bekleyen"),
    ("done", "Tamamlanan"),
    ("cat:video", "Video"),
    ("cat:audio", "Ses"),
    ("cat:programs", "Programlar"),
    ("cat:archives", "Arşivler"),
    ("cat:documents", "Belgeler"),
    ("cat:other", "Diğer"),
)
STATE_TAGS = {
    QUEUED: "queued",
    SCHEDULED: "scheduled",
    PROBING: "probing",
    DOWNLOADING: "downloading",
    PAUSED: "paused",
    COMPLETED: "completed",
    ERROR: "error",
    CANCELED: "canceled",
}
STATE_COLORS = {
    "queued": "#5f6368",
    "scheduled": "#8e24aa",
    "probing": "#0b57d0",
    "downloading": "#0b57d0",
    "paused": "#b06000",
    "completed": "#137333",
    "error": "#c5221f",
    "canceled": "#9aa0a6",
}


def load_photo(relative, store=None):
    path = ASSETS_DIR / relative
    if not path.exists():
        return None
    try:
        photo = tk.PhotoImage(file=str(path))
    except Exception:
        return None
    if store is not None:
        store[str(path)] = photo
    return photo


def center_window(window, parent=None):
    window.update_idletasks()
    width = window.winfo_reqwidth()
    height = window.winfo_reqheight()
    if parent is not None and parent.winfo_exists():
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    else:
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 2
    window.geometry(f"+{max(0, x)}+{max(0, y)}")


def open_path(path):
    if not path:
        return
    target = Path(path)
    try:
        if target.is_dir():
            os.startfile(str(target))
        elif target.exists():
            os.startfile(str(target))
        elif target.parent.exists():
            os.startfile(str(target.parent))
    except Exception:
        pass


def _grid_label(parent, row, text):
    ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", padx=8, pady=4)


class AddDialog(tk.Toplevel):
    def __init__(self, parent, manager, initial="", batch=False, site=None):
        super().__init__(parent)
        self.manager = manager
        self.batch = batch
        self.site = site
        self.result = None
        if site:
            self.title(f"{site} İndirme Ekle")
        else:
            self.title("Toplu Bağlantı Ekle" if batch else "İndirme Ekle")
        self.transient(parent)
        self.resizable(True, True)

        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        row = 0
        if batch:
            ttk.Label(body, text="Bağlantılar (her satıra bir URL):").grid(
                row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 4))
            self.txt_urls = tk.Text(body, width=66, height=11, wrap="none")
            self.txt_urls.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8)
            body.rowconfigure(1, weight=1)
            if initial:
                self.txt_urls.insert("1.0", initial)
            row = 2
        else:
            _grid_label(body, row, (f"{site} bağlantısı:" if site else "URL:"))
            self.var_url = tk.StringVar(value=initial)
            self.ent_url = ttk.Entry(body, textvariable=self.var_url, width=64)
            self.ent_url.grid(row=row, column=1, sticky="we", padx=8, pady=4)
            row += 1
            if site:
                ttk.Label(body, foreground="#5f6368",
                          text=f"{site} video/post bağlantısını yapıştırın; "
                               "indirme site çözümleyicisiyle otomatik yapılır.").grid(
                    row=row, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 4))
                row += 1

        _grid_label(body, row, "Kategori:")
        self.var_category = tk.StringVar(value="Otomatik")
        values = ["Otomatik"] + [CATEGORY_LABELS[c] for c in CATEGORIES]
        ttk.Combobox(body, textvariable=self.var_category, values=values,
                     state="readonly", width=24).grid(
            row=row, column=1, sticky="w", padx=8, pady=4)
        row += 1

        _grid_label(body, row, "Alt klasör:")
        self.var_subdir = tk.StringVar()
        ttk.Entry(body, textvariable=self.var_subdir, width=40).grid(
            row=row, column=1, sticky="we", padx=8, pady=4)
        row += 1

        _grid_label(body, row, "Dosya adı:")
        self.var_filename = tk.StringVar()
        ttk.Entry(body, textvariable=self.var_filename, width=40).grid(
            row=row, column=1, sticky="we", padx=8, pady=4)
        row += 1

        _grid_label(body, row, "Parça sayısı:")
        self.var_segments = tk.IntVar(value=0)
        ttk.Spinbox(body, from_=0, to=32, textvariable=self.var_segments,
                    width=8).grid(row=row, column=1, sticky="w", padx=(8, 6), pady=4)
        ttk.Label(body, text="(0 = ayarlarımki, en fazla 32)").grid(
            row=row, column=2, sticky="w", pady=4)
        row += 1

        _grid_label(body, row, "Hız sınırı (KB/s):")
        self.var_speed = tk.IntVar(value=0)
        ttk.Spinbox(body, from_=0, to=1000000, increment=256,
                    textvariable=self.var_speed, width=10).grid(
            row=row, column=1, sticky="w", padx=(8, 6), pady=4)
        ttk.Label(body, text="(0 = sınırsız)").grid(row=row, column=2, sticky="w",
                                                    pady=4)
        row += 1

        _grid_label(body, row, "Başlangıç:")
        frame_when = ttk.Frame(body)
        frame_when.grid(row=row, column=1, sticky="w", padx=8, pady=4)
        self.var_sched = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_when, text="Saatte başlat",
                        variable=self.var_sched).pack(side="left")
        self.var_time = tk.StringVar(value=(datetime.now() + timedelta(minutes=5)).strftime("%H:%M"))
        ttk.Entry(frame_when, textvariable=self.var_time, width=6).pack(side="left", padx=6)
        row += 1

        advanced = ttk.LabelFrame(body, text="İleri seçenekler", padding=6)
        advanced.grid(row=row, column=0, columnspan=2, sticky="we", padx=8, pady=(8, 4))
        advanced.columnconfigure(1, weight=1)
        arow = 0
        _grid_label(advanced, arow, "Referer:")
        self.var_referer = tk.StringVar()
        ttk.Entry(advanced, textvariable=self.var_referer).grid(
            row=arow, column=1, sticky="we", pady=3)
        arow += 1
        _grid_label(advanced, arow, "User-Agent:")
        self.var_ua = tk.StringVar(value=self.manager.settings.user_agent)
        ttk.Entry(advanced, textvariable=self.var_ua).grid(
            row=arow, column=1, sticky="we", pady=3)
        arow += 1
        _grid_label(advanced, arow, "Çerez:")
        self.var_cookies = tk.StringVar()
        ttk.Entry(advanced, textvariable=self.var_cookies).grid(
            row=arow, column=1, sticky="we", pady=3)
        arow += 1
        _grid_label(advanced, arow, "Ek başlıklar:")
        self.txt_headers = tk.Text(advanced, height=3, width=52)
        self.txt_headers.grid(row=arow, column=1, sticky="we", pady=3)
        row += 1

        buttons = ttk.Frame(body)
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", padx=8, pady=(10, 0))
        ttk.Button(buttons, text="İndir", command=self._ok).pack(side="left", padx=4)
        ttk.Button(buttons, text="Vazgeç", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Control-Return>", lambda _e: self._ok())
        center_window(self, parent)
        self.after(60, self._focus)

    def _focus(self):
        try:
            if self.batch:
                self.txt_urls.focus_set()
            else:
                self.ent_url.focus_set()
                self.ent_url.select_range(0, "end")
        except Exception:
            pass

    def _parse_time(self):
        raw = (self.var_time.get() or "").strip()
        parts = raw.replace(".", ":").split(":")
        if len(parts) < 2:
            raise ValueError("Saat gg:aa biçiminde olmalı")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Geçersiz saat")
        now = datetime.now()
        moment = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if moment <= now:
            moment += timedelta(days=1)
        return moment

    def _ok(self):
        if self.batch:
            text = self.txt_urls.get("1.0", "end")
            urls = [line.strip() for line in text.splitlines() if line.strip()]
        else:
            urls = [self.var_url.get().strip()]
        urls = [u for u in urls if u and not u.startswith("#")]
        if not urls:
            messagebox.showwarning("Eksik bilgi", "En az bir URL girin.", parent=self)
            return
        scheduled_at = None
        if self.var_sched.get():
            try:
                scheduled_at = self._parse_time()
            except Exception as exc:
                messagebox.showwarning("Geçersiz saat", str(exc), parent=self)
                return
        label = self.var_category.get()
        category = None
        if label != "Otomatik":
            for key, value in CATEGORY_LABELS.items():
                if value == label:
                    category = key
                    break
        headers_text = self.txt_headers.get("1.0", "end").strip()
        self.result = {
            "urls": urls,
            "category": category,
            "subdir": self.var_subdir.get().strip(),
            "filename": self.var_filename.get().strip() or None,
            "segments": int(self.var_segments.get()) or None,
            "speed_limit": int(self.var_speed.get()),
            "scheduled_at": scheduled_at,
            "referer": self.var_referer.get().strip(),
            "user_agent": self.var_ua.get().strip(),
            "cookies": self.var_cookies.get().strip(),
            "extra_headers": _parse_headers(headers_text),
        }
        self.destroy()


def _parse_headers(text):
    out = {}
    for line in (text or "").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key.strip():
                out[key.strip()] = value.strip()
    return out


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, manager, tab=None):
        super().__init__(parent)
        self.manager = manager
        self.result = None
        self.title("Ayarlar")
        self.transient(parent)
        self.resizable(True, True)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self.notebook = notebook
        tabs = {"general": 0, "connection": 1, "queue": 2, "categories": 3,
                "security": 4, "update": 5, "whatsapp": 6}
        if tab in tabs:
            index = tabs[tab]
            self.after(50, lambda: notebook.select(str(index)))

        st = manager.settings

        general = ttk.Frame(notebook, padding=10)
        notebook.add(general, text="Genel")
        general.columnconfigure(1, weight=1)
        row = 0
        _grid_label(general, row, "İndirme klasörü:")
        folder_frame = ttk.Frame(general)
        folder_frame.grid(row=row, column=1, sticky="we", pady=4)
        folder_frame.columnconfigure(0, weight=1)
        self.var_dir = tk.StringVar(value=st.download_dir)
        ttk.Entry(folder_frame, textvariable=self.var_dir).grid(
            row=0, column=0, sticky="we")
        ttk.Button(folder_frame, text="Gözat", command=self._browse).grid(
            row=0, column=1, padx=(6, 0))
        row += 1
        self.var_auto = tk.BooleanVar(value=bool(st.auto_start))
        ttk.Checkbutton(general, text="Eklenen indirmeleri hemen başlat",
                        variable=self.var_auto).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        self.var_sound = tk.BooleanVar(value=bool(st.sound_enabled))
        ttk.Checkbutton(general, text="Tamamlanınca sesli bildir",
                        variable=self.var_sound).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        self.var_clip_monitor = tk.BooleanVar(value=bool(st.clipboard_monitor))
        ttk.Checkbutton(general, text="Panodaki URL'leri izle",
                        variable=self.var_clip_monitor).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        self.var_clip_auto = tk.BooleanVar(value=bool(st.clipboard_auto_add))
        ttk.Checkbutton(general, text="Panodaki URL'yi otomatik indir",
                        variable=self.var_clip_auto).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        self.var_bridge = tk.BooleanVar(value=bool(getattr(st, "bridge_enabled", True)))
        ttk.Checkbutton(general, text="Tarayıcı köprüsü (yerel sunucu) açık",
                        variable=self.var_bridge).grid(row=row, column=1, sticky="w",
                                                       pady=4)
        row += 1
        _grid_label(general, row, "Köprü portu:")
        self.var_bridge_port = tk.IntVar(value=int(getattr(st, "bridge_port", 8877)))
        ttk.Spinbox(general, from_=1024, to=65535, textvariable=self.var_bridge_port,
                    width=8).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        ttk.Label(general, wraplength=460, foreground="#5f6368", text=(
            "Köprü açıkken tarayıcı eklentisi veya yer imi şu adresten bağlantı "
            "gönderir: http://127.0.0.1:PORT/add?url=... — ayrıca "
            "/links?url=... uç noktası sayfadaki tüm indirilebilir bağlantıları "
            "listeler.")
        ).grid(row=row, column=1, sticky="w", pady=(4, 0))
        row += 1
        self.var_exit_done = tk.BooleanVar(value=bool(st.exit_when_done))
        ttk.Checkbutton(general, text="Kuyruk bitince programı kapat",
                        variable=self.var_exit_done).grid(row=row, column=1, sticky="w", pady=4)

        connection = ttk.Frame(notebook, padding=10)
        notebook.add(connection, text="Bağlantı")
        connection.columnconfigure(1, weight=1)
        row = 0
        _grid_label(connection, row, "Eşzamanlı indirme:")
        self.var_concurrent = tk.IntVar(value=int(st.max_concurrent))
        ttk.Spinbox(connection, from_=1, to=10, textvariable=self.var_concurrent,
                    width=6).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(connection, row, "Parça sayısı:")
        self.var_segments = tk.IntVar(value=int(st.segments))
        ttk.Spinbox(connection, from_=1, to=32, textvariable=self.var_segments,
                    width=6).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(connection, row, "Yeniden deneme:")
        self.var_retries = tk.IntVar(value=int(st.retries))
        ttk.Spinbox(connection, from_=0, to=50, textvariable=self.var_retries,
                    width=6).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(connection, row, "Bağlantı zaman aşımı (sn):")
        self.var_tconn = tk.IntVar(value=int(st.timeout_connect))
        ttk.Spinbox(connection, from_=5, to=120, textvariable=self.var_tconn,
                    width=6).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(connection, row, "Okuma zaman aşımı (sn):")
        self.var_tread = tk.IntVar(value=int(st.timeout_read))
        ttk.Spinbox(connection, from_=10, to=600, textvariable=self.var_tread,
                    width=6).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(connection, row, "Hız sınırı (KB/s):")
        self.var_limit = tk.IntVar(value=int(st.speed_limit))
        ttk.Spinbox(connection, from_=0, to=1000000, increment=256,
                    textvariable=self.var_limit, width=10).grid(
            row=row, column=1, sticky="w", padx=(0, 8), pady=4)
        ttk.Label(connection, text="(0 = sınırsız)").grid(row=row, column=2,
                                                          sticky="w", pady=4)
        row += 1
        _grid_label(connection, row, "Proxy:")
        self.var_proxy = tk.StringVar(value=st.proxy)
        ttk.Entry(connection, textvariable=self.var_proxy).grid(
            row=row, column=1, sticky="we", pady=4)
        row += 1
        _grid_label(connection, row, "FTP kullanıcı:")
        self.var_ftp_user = tk.StringVar(value=getattr(st, "ftp_user", "anonymous"))
        ttk.Entry(connection, textvariable=self.var_ftp_user, width=24).grid(
            row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(connection, row, "FTP şifre:")
        self.var_ftp_pass = tk.StringVar(value=getattr(st, "ftp_password", ""))
        ttk.Entry(connection, textvariable=self.var_ftp_pass, width=24,
                  show="*").grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(connection, row, "User-Agent:")
        self.var_ua = tk.StringVar(value=st.user_agent)
        ttk.Entry(connection, textvariable=self.var_ua).grid(
            row=row, column=1, sticky="we", pady=4)
        row += 1
        _grid_label(connection, row, "Referer:")
        self.var_referer = tk.StringVar(value=st.referer)
        ttk.Entry(connection, textvariable=self.var_referer).grid(
            row=row, column=1, sticky="we", pady=4)
        row += 1
        _grid_label(connection, row, "Çerez:")
        self.var_cookies = tk.StringVar(value=st.cookies)
        ttk.Entry(connection, textvariable=self.var_cookies).grid(
            row=row, column=1, sticky="we", pady=4)
        row += 1
        _grid_label(connection, row, "Ek başlıklar:")
        self.txt_headers = tk.Text(connection, height=4, width=56)
        self.txt_headers.grid(row=row, column=1, sticky="we", pady=4)
        self.txt_headers.insert("1.0", st.extra_headers or "")

        queue_frame = ttk.Frame(notebook, padding=10)
        notebook.add(queue_frame, text="Kuyruk ve Zamanlama")
        queue_frame.columnconfigure(1, weight=1)
        row = 0
        self.var_queue = tk.BooleanVar(value=bool(manager.queue_running))
        ttk.Checkbutton(queue_frame, text="Kuyruk çalışıyor",
                        variable=self.var_queue).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        self.var_sched_enabled = tk.BooleanVar(value=bool(st.schedule_enabled))
        ttk.Checkbutton(queue_frame, text="Zaman aralığında çalıştır",
                        variable=self.var_sched_enabled).grid(row=row, column=1,
                                                              sticky="w", pady=4)
        row += 1
        _grid_label(queue_frame, row, "Başlangıç (HH:MM):")
        self.var_sched_start = tk.StringVar(value=str(st.schedule_start))
        ttk.Entry(queue_frame, textvariable=self.var_sched_start, width=8).grid(
            row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(queue_frame, row, "Bitiş (HH:MM):")
        self.var_sched_end = tk.StringVar(value=str(st.schedule_end))
        ttk.Entry(queue_frame, textvariable=self.var_sched_end, width=8).grid(
            row=row, column=1, sticky="w", pady=4)
        row += 1
        ttk.Label(queue_frame, wraplength=420, foreground="#5f6368", text=(
            "Zaman aralığı etkinse indirmeler yalnızca bu saatler arasında başlar. "
            "Zamanlı tekil indirmeler için Ekle penceresindeki \"Saatte başlat\" "
            "seçeneğini kullanın (kuyruk açık olmalıdır).")
        ).grid(row=row, column=1, sticky="w", pady=(10, 4))

        categories = ttk.Frame(notebook, padding=10)
        notebook.add(categories, text="Kategoriler")
        categories.columnconfigure(1, weight=1)
        self.var_folders = {}
        for index, cat in enumerate(CATEGORIES):
            _grid_label(categories, index, CATEGORY_LABELS[cat] + ":")
            var = tk.StringVar(value=str(st.category_folders.get(cat, "")))
            ttk.Entry(categories, textvariable=var).grid(
                row=index, column=1, sticky="we", pady=4)
            self.var_folders[cat] = var

        security = ttk.Frame(notebook, padding=10)
        notebook.add(security, text="Güvenlik")
        security.columnconfigure(1, weight=1)
        row = 0
        self.var_scan = tk.BooleanVar(value=bool(st.scan_enabled))
        ttk.Checkbutton(security, text="İndirme bitince dosyayı virüs taramasından geçir",
                        variable=self.var_scan).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(security, row, "Tarama komutu:")
        self.var_scan_cmd = tk.StringVar(value=str(st.scan_command))
        ttk.Entry(security, textvariable=self.var_scan_cmd).grid(
            row=row, column=1, sticky="we", pady=4)
        row += 1
        ttk.Button(security, text="Windows Defender'ı algıla",
                   command=self._detect_defender).grid(row=row, column=1, sticky="w",
                                                       pady=4)
        row += 1
        ttk.Label(security, wraplength=420, foreground="#5f6368", text=(
            "Komut içinde {file} yer tutucusu kullanılır. Örnek: "
            "\"C:\\Program Files\\Windows Defender\\MpCmdRun.exe\" -Scan "
            "-ScanType 3 -File {file}")
        ).grid(row=row, column=1, sticky="w", pady=(8, 4))

        # -- Güncelleme sekmesi (yerel kaynak: klasör/UNC/HTTP) --------------
        update = ttk.Frame(notebook, padding=10)
        notebook.add(update, text="Güncelleme")
        update.columnconfigure(1, weight=1)
        row = 0
        self.var_update_on = tk.BooleanVar(
            value=bool(getattr(st, "update_enabled", True)))
        ttk.Checkbutton(update, text="Güncelleştirmeleri etkinleştir",
                        variable=self.var_update_on).grid(
            row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(update, row, "Güncelleme kaynağı:")
        self.var_update_src = tk.StringVar(
            value=str(getattr(st, "update_source", "")))
        ttk.Entry(update, textvariable=self.var_update_src).grid(
            row=row, column=1, sticky="we", pady=4)
        row += 1
        ttk.Label(update, wraplength=460, foreground="#5f6368", text=(
            "Kaynak yerel klasör, UNC paylaşımı (\\\\sunucu\\paylasim) veya "
            "http(s) adresi olabilir; içinde version.json + zip paketi bulunur. "
            "Yeni sürüm geldiğinde indirmeler bitince otomatik uygulanır ve "
            "program kendini yeniden başlatır — hiçbir bağlantıya tıklamak "
            "gerekmez.")
        ).grid(row=row, column=1, sticky="w", pady=(0, 6))
        row += 1
        update_btns = ttk.Frame(update)
        update_btns.grid(row=row, column=1, sticky="w", pady=4)
        ttk.Button(update_btns, text="Şimdi kontrol et",
                   command=self._update_check_now).pack(side="left", padx=(0, 6))
        ttk.Button(update_btns, text="Şimdi güncelle",
                   command=self._update_apply_now).pack(side="left")
        row += 1
        self.var_update_status = tk.StringVar(value="Kontrol edilmedi.")
        ttk.Label(update, textvariable=self.var_update_status,
                  wraplength=460).grid(row=row, column=1, sticky="w", pady=4)

        # -- WhatsApp sekmesi ------------------------------------------------
        whatsapp = ttk.Frame(notebook, padding=10)
        notebook.add(whatsapp, text="WhatsApp")
        whatsapp.columnconfigure(1, weight=1)
        row = 0
        self.var_wa_on = tk.BooleanVar(value=bool(getattr(st, "wa_enabled", False)))
        ttk.Checkbutton(whatsapp, text="WhatsApp PDF yakalamayı aç",
                        variable=self.var_wa_on).grid(
            row=row, column=1, sticky="w", pady=4)
        row += 1
        _grid_label(whatsapp, row, "İzleme klasörü:")
        frame_watch = ttk.Frame(whatsapp)
        frame_watch.grid(row=row, column=1, sticky="we", pady=4)
        frame_watch.columnconfigure(0, weight=1)
        self.var_wa_watch = tk.StringVar(
            value=str(getattr(st, "wa_watch_folder", "")))
        ttk.Entry(frame_watch, textvariable=self.var_wa_watch).grid(
            row=0, column=0, sticky="we")
        ttk.Button(frame_watch, text="Gözat", command=self._wa_browse_watch).grid(
            row=0, column=1, padx=(6, 0))
        row += 1
        _grid_label(whatsapp, row, "Hedef klasör:")
        frame_out = ttk.Frame(whatsapp)
        frame_out.grid(row=row, column=1, sticky="we", pady=4)
        frame_out.columnconfigure(0, weight=1)
        self.var_wa_out = tk.StringVar(
            value=str(getattr(st, "wa_output_folder", "")))
        ttk.Entry(frame_out, textvariable=self.var_wa_out).grid(
            row=0, column=0, sticky="we")
        ttk.Button(frame_out, text="Gözat", command=self._wa_browse_out).grid(
            row=0, column=1, padx=(6, 0))
        row += 1
        ttk.Label(whatsapp, text="İzin verilen sohbetler (grup/kişi — beyaz liste):",
                  ).grid(row=row, column=1, sticky="w", pady=(8, 2))
        row += 1
        frame_wl = ttk.Frame(whatsapp)
        frame_wl.grid(row=row, column=1, sticky="nsew", pady=2)
        whatsapp.rowconfigure(row, weight=1)
        frame_wl.columnconfigure(0, weight=1)
        frame_wl.rowconfigure(0, weight=1)
        self.wa_list = tk.Listbox(frame_wl, height=6, activestyle="none",
                                  selectmode="extended")
        self.wa_list.grid(row=0, column=0, sticky="nsew")
        wl_scroll = ttk.Scrollbar(frame_wl, orient="vertical",
                                  command=self.wa_list.yview)
        wl_scroll.grid(row=0, column=1, sticky="ns")
        self.wa_list.configure(yscrollcommand=wl_scroll.set)
        self._whitelist_entries = list(
            normalize_whitelist(getattr(st, "wa_whitelist", [])))
        for entry in self._whitelist_entries:
            self.wa_list.insert("end", f"{entry['label']}  ({entry['jid']})")
        row += 1
        frame_wl_btns = ttk.Frame(whatsapp)
        frame_wl_btns.grid(row=row, column=1, sticky="w", pady=4)
        ttk.Button(frame_wl_btns, text="Sohbetleri yükle",
                   command=self._wa_load_chats).pack(side="left", padx=(0, 6))
        ttk.Button(frame_wl_btns, text="Ekle",
                   command=self._wa_add_entry).pack(side="left", padx=(0, 6))
        ttk.Button(frame_wl_btns, text="Seçileni kaldır",
                   command=self._wa_remove_selected).pack(side="left")
        row += 1
        self.var_wa_status = tk.StringVar(value="Dinleyici durmadı.")
        ttk.Label(whatsapp, textvariable=self.var_wa_status,
                  wraplength=460).grid(row=row, column=1, sticky="w", pady=(6, 2))
        row += 1
        frame_wa_ctrl = ttk.Frame(whatsapp)
        frame_wa_ctrl.grid(row=row, column=1, sticky="w", pady=4)
        ttk.Button(frame_wa_ctrl, text="Dinleyiciyi başlat",
                   command=self._wa_start_listener).pack(side="left", padx=(0, 6))
        ttk.Button(frame_wa_ctrl, text="QR'ı göster",
                   command=self._wa_show_qr).pack(side="left", padx=(0, 6))
        ttk.Button(frame_wa_ctrl, text="Durdur",
                   command=self._wa_stop_listener).pack(side="left")
        row += 1
        ttk.Label(whatsapp, wraplength=460, foreground="#5f6368", text=(
            "Dinleyici telefondaki WhatsApp'ın \"bağlı cihaz\" olarak QR ile "
            "eşleşir; yalnızca beyaz listedeki gruplardan/kişilerden gelen "
            "PDF'leri indirir. Node.js kurulu olmalıdır (node komutu).")
        ).grid(row=row, column=1, sticky="w", pady=(6, 0))

        buttons = ttk.Frame(self, padding=(8, 0, 8, 8))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Kaydet", command=self._ok).pack(side="right", padx=4)
        ttk.Button(buttons, text="Vazgeç", command=self.destroy).pack(side="right", padx=4)

        self.bind("<Escape>", lambda _e: self.destroy())
        center_window(self, parent)

    def _browse(self):
        folder = filedialog.askdirectory(parent=self, initialdir=self.var_dir.get())
        if folder:
            self.var_dir.set(folder)

    def _detect_defender(self):
        command = self.manager.detect_defender()
        if command:
            self.var_scan_cmd.set(command)
            self.var_scan.set(True)
            messagebox.showinfo("Bulundu", "Windows Defender tarama komutu ayarlandı.",
                                parent=self)
        else:
            messagebox.showwarning("Bulunamadı",
                                   "MpCmdRun.exe bulunamadı, komutu elle girin.",
                                   parent=self)

    # -- Güncelleme yardimcilari --------------------------------------------
    def _update_check_now(self):
        source = self.var_update_src.get().strip()
        if not source:
            self.var_update_status.set("Önce bir güncelleme kaynağı girin.")
            return
        if getattr(self, "_update_worker", None) is not None:
            return
        self.var_update_status.set("Kontrol ediliyor…")
        self._update_worker = "pending"

        def work():
            from .updater import check_for_update
            try:
                result = check_for_update(source)
            except Exception as exc:  # pragma: no cover - beklenmedik IO
                result = {"status": "error", "error": str(exc)}
            self._update_worker = result

        threading.Thread(target=work, daemon=True).start()
        self.after(150, self._poll_update_worker)

    def _poll_update_worker(self):
        result = getattr(self, "_update_worker", None)
        if result is None or result == "pending":
            self.after(150, self._poll_update_worker)
            return
        self._update_worker = None
        if result.get("status") == "update_available":
            self.var_update_status.set(
                f"Yeni sürüm var: {result['version']} "
                f"(mevcut: {result['current']}) — \"Şimdi güncelle\" ile kurun.")
        elif result.get("status") == "up_to_date":
            self.var_update_status.set(
                f"Güncel (sürüm {result.get('current', __version__)}).")
        elif result.get("status") == "disabled":
            self.var_update_status.set("Güncelleme kapalı veya kaynak boş.")
        else:
            self.var_update_status.set(
                f"Hata: {result.get('error', 'bilinmeyen')}")

    def _update_apply_now(self):
        source = self.var_update_src.get().strip()
        if not source:
            self.var_update_status.set("Önce bir güncelleme kaynağı girin.")
            return
        if getattr(self, "_update_worker", None) is not None:
            return
        self.var_update_status.set("Paket indirilip doğrulanıyor…")
        self._update_worker = "pending"

        def work():
            from .updater import install_update
            try:
                result = install_update(
                    source,
                    progress=lambda msg: self._update_notes.append(msg))
            except Exception as exc:
                result = {"status": "error", "error": str(exc)}
            self._update_worker = result

        self._update_notes = []
        threading.Thread(target=work, daemon=True).start()
        self.after(150, self._poll_update_apply)

    def _poll_update_apply(self):
        result = getattr(self, "_update_worker", None)
        if result is None or result == "pending":
            self.after(200, self._poll_update_apply)
            return
        self._update_worker = None
        if result.get("status") == "installed":
            self.var_update_status.set(
                f"Sürüm {result.get('version', '?')} uygulandı.")
            if messagebox.askyesno("Güncelleme uygulandı",
                                   "Yeni sürüm hazır. Program şimdi yeniden "
                                   "başlatılsın mı?", parent=self):
                from .updater import prepare_restart
                app_root = Path(__file__).resolve().parent.parent
                self.manager.settings.save()
                self.manager.shutdown()
                self.destroy()
                prepare_restart(app_root)
        elif result.get("status") == "update_available":
            self.var_update_status.set(
                f"Yeni sürüm var: {result.get('version')} — tekrar deneyin.")
        elif result.get("status") == "up_to_date":
            self.var_update_status.set("Zaten güncel.")
        else:
            self.var_update_status.set(f"Hata: {result.get('error', 'bilinmeyen')}")

    # -- WhatsApp yardimcilari ----------------------------------------------
    @property
    def _listener_dir(self):
        return Path(__file__).resolve().parent.parent / "whatsapp_listener"

    def _wa_browse_watch(self):
        folder = filedialog.askdirectory(parent=self,
                                         initialdir=self.var_wa_watch.get() or "")
        if folder:
            self.var_wa_watch.set(folder)

    def _wa_browse_out(self):
        folder = filedialog.askdirectory(parent=self,
                                         initialdir=self.var_wa_out.get() or "")
        if folder:
            self.var_wa_out.set(folder)

    def _wa_load_chats(self):
        path = self._listener_dir / "chats.json"
        if not path.is_file():
            messagebox.showwarning(
                "Sohbet yok",
                "chats.json bulunamadı. Önce \"Dinleyiciyi başlat\" ile QR'ı "
                "okutun, bağlantı kurulunca sohbetler otomatik listelensin.",
                parent=self)
            return
        try:
            chats = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            messagebox.showwarning("Okunamadı", f"chats.json: {exc}", parent=self)
            return
        if not isinstance(chats, list) or not chats:
            messagebox.showwarning("Boş", "Sohbet listesi boş.", parent=self)
            return
        picker = tk.Toplevel(self)
        picker.title("Sohbet seç (beyaz liste)")
        picker.transient(self)
        picker.resizable(True, True)
        ttk.Label(picker, padding=8,
                  text="PDF alınacak grup/kişileri seçin (Ctrl ile çoklu):").pack(
            anchor="w")
        box_frame = ttk.Frame(picker, padding=(8, 0))
        box_frame.pack(fill="both", expand=True)
        listbox = tk.Listbox(box_frame, selectmode="extended", height=14,
                             activestyle="none")
        scroll = ttk.Scrollbar(box_frame, orient="vertical",
                               command=listbox.yview)
        listbox.configure(yscrollcommand=scroll.set)
        listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        labels = []
        for chat in chats:
            if not isinstance(chat, dict) or not chat.get("jid"):
                continue
            label = str(chat.get("label") or chat.get("name") or chat["jid"])
            labels.append({"jid": str(chat["jid"]), "label": label})
            listbox.insert("end", f"{label}  ({chat['jid']})")
        existing = {e["jid"] for e in self._whitelist_entries}
        for index, entry in enumerate(labels):
            if entry["jid"] in existing:
                listbox.selection_set(index)

        def confirm():
            for index in listbox.curselection():
                entry = labels[index]
                if entry["jid"] not in existing:
                    self._whitelist_entries.append(entry)
                    self.wa_list.insert("end",
                                        f"{entry['label']}  ({entry['jid']})")
                    existing.add(entry["jid"])
            picker.destroy()

        buttons = ttk.Frame(picker, padding=8)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Seçilenleri ekle",
                   command=confirm).pack(side="right", padx=4)
        ttk.Button(buttons, text="Vazgeç",
                   command=picker.destroy).pack(side="right", padx=4)
        center_window(picker, self)

    def _wa_add_entry(self):
        from tkinter import simpledialog
        label = simpledialog.askstring("Sohbet adı",
                                       "Grup/kişi adı (günlük görünen ad):",
                                       parent=self)
        if label is None or not label.strip():
            return
        jid = simpledialog.askstring("JID / numara",
                                     "Grup JID'i (ör. 123456789-1111@g.us) veya "
                                     "telefon numarası (ör. 905xx…):", parent=self)
        if jid is None or not jid.strip():
            return
        entry = {"jid": jid.strip(), "label": label.strip()}
        if entry["jid"] not in {e["jid"] for e in self._whitelist_entries}:
            self._whitelist_entries.append(entry)
            self.wa_list.insert("end", f"{entry['label']}  ({entry['jid']})")

    def _wa_remove_selected(self):
        selection = list(self.wa_list.curselection())
        for index in reversed(selection):
            self.wa_list.delete(index)
            del self._whitelist_entries[index]

    def _wa_write_listener_config(self):
        watch = self.var_wa_watch.get().strip()
        if not watch:
            watch = str(Path(self.var_dir.get().strip() or
                             str(Path.home() / "Downloads")) / "WhatsApp PDF")
            self.var_wa_watch.set(watch)
        config = {
            "watchFolder": watch,
            "whitelist": [entry["jid"] for entry in self._whitelist_entries],
        }
        self._listener_dir.mkdir(parents=True, exist_ok=True)
        (self._listener_dir / "config.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return config

    def _wa_start_listener(self):
        import shutil as _shutil
        if not _shutil.which("node"):
            self.var_wa_status.set(
                "Node.js bulunamadı — kurulum: https://nodejs.org (LTS).")
            return
        if not (self._listener_dir / "index.js").is_file():
            self.var_wa_status.set("whatsapp_listener/index.js bulunamadı.")
            return
        process = getattr(self.manager, "wa_listener", None)
        if process is not None and process.poll() is None:
            self.var_wa_status.set("Dinleyici zaten çalışıyor.")
            return
        self._wa_write_listener_config()
        import subprocess
        log_path = self._listener_dir / "listener.log"
        try:
            log_handle = open(log_path, "a", encoding="utf-8", errors="ignore")
            kwargs = {"cwd": str(self._listener_dir),
                      "stdin": subprocess.DEVNULL,
                      "stdout": log_handle, "stderr": log_handle}
            if os.name == "nt":
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            process = subprocess.Popen(["node", "index.js"], **kwargs)
            self.manager.wa_listener = process
            self.var_wa_status.set(
                "Dinleyici başladı — telefonla QR'ı okutun (\"QR'ı göster\").")
        except OSError as exc:
            self.var_wa_status.set(f"Başlatılamadı: {exc}")

    def _wa_show_qr(self):
        qr_path = self._listener_dir / "qr.png"
        if qr_path.is_file():
            open_path(qr_path)
        else:
            self.var_wa_status.set(
                "qr.png yok — dinleyiciyi başlatıp bekleyin (QR üretilince "
                "otomatik açılır).")

    def _wa_stop_listener(self):
        process = getattr(self.manager, "wa_listener", None)
        if process is not None and process.poll() is None:
            process.terminate()
            self.var_wa_status.set("Dinleyici durduruldu.")
        else:
            self.var_wa_status.set("Dinleyici zaten çalışmıyor.")

    def _ok(self):
        values = {
            "download_dir": self.var_dir.get().strip() or str(Path.home() / "Downloads"),
            "auto_start": bool(self.var_auto.get()),
            "sound_enabled": bool(self.var_sound.get()),
            "clipboard_monitor": bool(self.var_clip_monitor.get()),
            "clipboard_auto_add": bool(self.var_clip_auto.get()),
            "bridge_enabled": bool(self.var_bridge.get()),
            "bridge_port": int(self.var_bridge_port.get()),
            "exit_when_done": bool(self.var_exit_done.get()),
            "max_concurrent": max(1, int(self.var_concurrent.get())),
            "segments": max(1, int(self.var_segments.get())),
            "retries": max(0, int(self.var_retries.get())),
            "timeout_connect": max(5, int(self.var_tconn.get())),
            "timeout_read": max(10, int(self.var_tread.get())),
            "speed_limit": max(0, int(self.var_limit.get())),
            "proxy": self.var_proxy.get().strip(),
            "ftp_user": self.var_ftp_user.get().strip() or "anonymous",
            "ftp_password": self.var_ftp_pass.get(),
            "user_agent": self.var_ua.get().strip(),
            "referer": self.var_referer.get().strip(),
            "cookies": self.var_cookies.get().strip(),
            "extra_headers": self.txt_headers.get("1.0", "end").strip(),
            "schedule_enabled": bool(self.var_sched_enabled.get()),
            "schedule_start": self.var_sched_start.get().strip() or "09:00",
            "schedule_end": self.var_sched_end.get().strip() or "18:00",
            "scan_enabled": bool(self.var_scan.get()),
            "scan_command": self.var_scan_cmd.get().strip(),
            "category_folders": {k: v.get().strip() or CATEGORY_LABELS[k]
                                 for k, v in self.var_folders.items()},
            "update_enabled": bool(self.var_update_on.get()),
            "update_source": self.var_update_src.get().strip(),
            "wa_enabled": bool(self.var_wa_on.get()),
            "wa_watch_folder": self.var_wa_watch.get().strip(),
            "wa_output_folder": self.var_wa_out.get().strip(),
            "wa_whitelist": [dict(entry) for entry in self._whitelist_entries],
        }
        self.result = values
        self.destroy()


class GrabberDialog(tk.Toplevel):
    def __init__(self, parent, manager):
        super().__init__(parent)
        self.manager = manager
        self.title("Site Grabber — Bağlantıları Topla")
        self.transient(parent)
        self.resizable(True, True)
        self._worker_result = None
        self._worker_progress = None
        self._scanning = False

        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Sayfa URL:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.var_url = tk.StringVar()
        self.ent_url = ttk.Entry(top, textvariable=self.var_url, width=64)
        self.ent_url.grid(row=0, column=1, sticky="we")
        self.btn_scan = ttk.Button(top, text="Tara", command=self._start)
        self.btn_scan.grid(row=0, column=2, padx=(6, 0))

        options = ttk.Frame(self, padding=(10, 0))
        options.pack(fill="x")
        ttk.Label(options, text="Derinlik:").pack(side="left")
        self.var_depth = tk.IntVar(value=1)
        ttk.Spinbox(options, from_=0, to=5, textvariable=self.var_depth,
                    width=4).pack(side="left", padx=(4, 12))
        self.var_same = tk.BooleanVar(value=True)
        ttk.Checkbutton(options, text="Sadece aynı alan adı",
                        variable=self.var_same).pack(side="left", padx=(0, 12))
        ttk.Label(options, text="Uzantılar:").pack(side="left")
        self.var_ext = tk.StringVar(value=".zip,.rar,.7z,.mp4,.mkv,.mp3,.pdf,.exe")
        ttk.Entry(options, textvariable=self.var_ext, width=34).pack(side="left",
                                                                     padx=(4, 12))
        ttk.Label(options, text="Max sayfa:").pack(side="left")
        self.var_max = tk.IntVar(value=60)
        ttk.Spinbox(options, from_=1, to=500, textvariable=self.var_max,
                    width=6).pack(side="left", padx=(4, 0))

        self.var_status = tk.StringVar(value="URL girip Tara'ya basın.")
        ttk.Label(self, textvariable=self.var_status, padding=(10, 6)).pack(fill="x")

        list_frame = ttk.Frame(self, padding=(10, 0))
        list_frame.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(list_frame, selectmode="extended", height=14,
                                  activestyle="none")
        scroll = ttk.Scrollbar(list_frame, orient="vertical",
                               command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        buttons = ttk.Frame(self, padding=10)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Tümünü Ekle",
                   command=lambda: self._add(selected=False)).pack(side="left", padx=4)
        ttk.Button(buttons, text="Seçilenleri Ekle",
                   command=lambda: self._add(selected=True)).pack(side="left", padx=4)
        ttk.Button(buttons, text="Kapat", command=self.destroy).pack(side="right",
                                                                     padx=4)

        self.bind("<Escape>", lambda _e: self.destroy())
        center_window(self, parent)
        self.after(80, lambda: self.ent_url.focus_set())

    def _start(self):
        url = self.var_url.get().strip()
        if not url:
            messagebox.showwarning("Eksik bilgi", "Bir sayfa URL'si girin.", parent=self)
            return
        if not url.lower().startswith(("http://", "https://")):
            url = "https://" + url
            self.var_url.set(url)
        if self._scanning:
            return
        extensions = [e.strip() for e in self.var_ext.get().split(",") if e.strip()]
        options = {
            "url": url,
            "depth": int(self.var_depth.get()),
            "same_domain": bool(self.var_same.get()),
            "extensions": extensions or None,
            "max_pages": int(self.var_max.get()),
        }
        self._scanning = True
        self._worker_result = None
        self._worker_progress = None
        self.listbox.delete(0, "end")
        self.btn_scan.configure(state="disabled")
        self.var_status.set("Taranıyor...")
        threading.Thread(target=self._worker, args=(options,), daemon=True).start()
        self.after(250, self._poll)

    def _worker(self, options):
        try:
            result = self.manager.grab(
                options["url"],
                depth=options["depth"],
                same_domain=options["same_domain"],
                extensions=options["extensions"],
                max_pages=options["max_pages"],
                on_progress=self._on_progress,
            )
            self._worker_result = result
        except Exception as exc:
            self._worker_progress = ("error", str(exc))
            self._worker_result = []

    def _on_progress(self, files, pages):
        self._worker_progress = (files, pages)

    def _poll(self):
        progress = self._worker_progress
        if progress is not None:
            self._worker_progress = None
            if progress[0] == "error":
                self.var_status.set(f"Hata: {progress[1]}")
            else:
                self.var_status.set(f"{progress[1]} sayfa tarandı, {progress[0]} bağlantı bulundu...")
        if self._worker_result is None:
            self.after(250, self._poll)
            return
        urls = self._worker_result
        for url in urls:
            self.listbox.insert("end", url)
        self._scanning = False
        self.btn_scan.configure(state="normal")
        self.var_status.set(f"{len(urls)} indirilebilir bağlantı bulundu.")

    def _add(self, selected=True):
        if selected:
            urls = [self.listbox.get(i) for i in self.listbox.curselection()]
        else:
            urls = [self.listbox.get(i) for i in range(self.listbox.size())]
        if not urls:
            messagebox.showwarning("Boş", "Eklenecek bağlantı yok.", parent=self)
            return
        self.manager.add(urls)
        messagebox.showinfo("Eklendi", f"{len(urls)} bağlantı indirme listesine eklendi.",
                            parent=self)


class PropertiesDialog(tk.Toplevel):
    def __init__(self, parent, manager, task):
        super().__init__(parent)
        self.manager = manager
        self.task = task
        self.title("Bağlantı Özellikleri")
        self.transient(parent)
        self.resizable(False, False)

        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        info = [
            ("Durum:", STATE_LABELS.get(task.state, task.state)),
            ("Boyut:", format_bytes(task.size)),
            ("İndirilen:", format_bytes(task.downloaded)),
            ("Parça sayısı:", str(len(task.segments))),
            ("Kategori:", CATEGORY_LABELS.get(task.category, task.category)),
            ("Hedef:", task.destination),
            ("Bağlantı:", task.url),
        ]
        row = 0
        for label, value in info:
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="nw", padx=8,
                                             pady=3)
            widget = ttk.Label(body, text=value, wraplength=520, justify="left")
            widget.grid(row=row, column=1, sticky="w", padx=8, pady=3)
            row += 1

        editable = ttk.LabelFrame(body, text="Düzenlenebilir alanlar", padding=6)
        editable.grid(row=row, column=0, columnspan=2, sticky="we", padx=8, pady=(8, 4))
        editable.columnconfigure(1, weight=1)
        erow = 0
        _grid_label(editable, erow, "Alt klasör:")
        self.var_subdir = tk.StringVar(value=task.subdir)
        ttk.Entry(editable, textvariable=self.var_subdir, width=40).grid(
            row=erow, column=1, sticky="we", pady=3)
        erow += 1
        _grid_label(editable, erow, "Hız sınırı (KB/s):")
        self.var_speed = tk.IntVar(value=int(task.speed_limit))
        ttk.Spinbox(editable, from_=0, to=1000000, increment=256,
                    textvariable=self.var_speed, width=10).grid(
            row=erow, column=1, sticky="w", pady=3)
        erow += 1
        _grid_label(editable, erow, "Referer:")
        self.var_referer = tk.StringVar(value=task.referer)
        ttk.Entry(editable, textvariable=self.var_referer, width=48).grid(
            row=erow, column=1, sticky="we", pady=3)
        erow += 1
        _grid_label(editable, erow, "User-Agent:")
        self.var_ua = tk.StringVar(value=task.user_agent or manager.settings.user_agent)
        ttk.Entry(editable, textvariable=self.var_ua, width=48).grid(
            row=erow, column=1, sticky="we", pady=3)
        erow += 1
        _grid_label(editable, erow, "Çerez:")
        self.var_cookies = tk.StringVar(value=task.cookies)
        ttk.Entry(editable, textvariable=self.var_cookies, width=48).grid(
            row=erow, column=1, sticky="we", pady=3)

        buttons = ttk.Frame(body)
        buttons.grid(row=row + 1, column=0, columnspan=2, sticky="e", padx=8, pady=(8, 0))
        ttk.Button(buttons, text="Kaydet", command=self._save).pack(side="left", padx=4)
        ttk.Button(buttons, text="Klasörü Aç",
                   command=lambda: open_path(task.destination)).pack(side="left", padx=4)
        ttk.Button(buttons, text="Kapat", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Escape>", lambda _e: self.destroy())
        center_window(self, parent)

    def _save(self):
        task = self.task
        if task.is_busy:
            messagebox.showwarning("İndirme sürüyor",
                                   "Değişiklikler bir sonraki başlatmada geçerli olacak.",
                                   parent=self)
        task.subdir = self.var_subdir.get().strip()
        task.set_speed_limit(int(self.var_speed.get()))
        task.referer = self.var_referer.get().strip()
        task.user_agent = self.var_ua.get().strip()
        task.cookies = self.var_cookies.get().strip()
        self.manager.log(f"Özellikler güncellendi: {task.filename or task.url}", "info")
        self.manager.save_queue()
        self.destroy()


class App:
    def __init__(self, manager):
        self.mgr = manager
        self.root = self._create_root()
        self.root.title(f"Retro+ Download Manager {__version__}")
        self.root.geometry("1180x700")
        self.root.minsize(940, 560)
        self._photos = {}
        self._filter = "all"
        self._cat_texts = {}

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Treeview", rowheight=25)
        style.configure("Header.TFrame", background=HEADER_BG)

        self._set_window_icon()

        self._rows = {}
        self._log_seq = 0
        self._history_len = -1
        self._last_clip = ""
        self._tick_count = 0
        self._all_done = False
        self._context_menu = None

        self._build_header()
        self._build_menu()
        self._build_toolbar()
        self._build_site_bar()
        self._build_body()
        self._build_statusbar()
        self._bind_keys()
        self._setup_dnd()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.mgr.on_all_done = self._on_all_done
        self._ui_tick()

    def _set_window_icon(self):
        logo = load_photo("logo.png", self._photos)
        if logo is None:
            return
        try:
            self.root.iconphoto(True, logo)
        except Exception:
            pass

    def _build_header(self):
        header = tk.Frame(self.root, background=HEADER_BG, height=54)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        logo = load_photo("logo_small.png", self._photos)
        if logo is not None:
            tk.Label(header, image=logo, background=HEADER_BG).pack(
                side="left", padx=(14, 10), pady=7)
        titles = tk.Frame(header, background=HEADER_BG)
        titles.pack(side="left", fill="y")
        tk.Label(titles, text="Retro+ Download Manager", foreground="#ffffff",
                 background=HEADER_BG, font=("Segoe UI Semibold", 14)).pack(
            anchor="w", pady=(8, 0))
        tk.Label(titles, text="Çok parçalı indirme · duraklat/devam · "
                              "kuyruk ve zamanlama · tarayıcı köprüsü",
                 foreground="#8fd4cb", background=HEADER_BG,
                 font=("Segoe UI", 8)).pack(anchor="w")

        self.var_header_speed = tk.StringVar(value="")
        tk.Label(header, textvariable=self.var_header_speed, foreground="#e8eaed",
                 background=HEADER_BG, font=("Segoe UI", 11, "bold")).pack(
            side="right", padx=18)
        self.var_header_active = tk.StringVar(value="")
        tk.Label(header, textvariable=self.var_header_active, foreground="#8fd4cb",
                 background=HEADER_BG, font=("Segoe UI", 9)).pack(
            side="right", padx=(0, 6))

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="URL Ekle...", accelerator="Ctrl+N",
                              command=self.add_url)
        file_menu.add_command(label="Toplu Ekle...", accelerator="Ctrl+B",
                              command=self.add_batch)
        file_menu.add_command(label="Site Grabber...", command=self.open_grabber)
        file_menu.add_separator()
        file_menu.add_command(label="Panodan Ekle", accelerator="Ctrl+V",
                              command=self.add_from_clipboard)
        file_menu.add_separator()
        file_menu.add_command(label="Ayarlar...", accelerator="Ctrl+,",
                              command=self.open_settings)
        file_menu.add_command(label="Geçmişi Temizle", command=self.clear_history)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", accelerator="Ctrl+Q", command=self._on_close)
        menubar.add_cascade(label="Dosya", menu=file_menu)

        download_menu = tk.Menu(menubar, tearoff=0)
        download_menu.add_command(label="Devam Et", accelerator="Ctrl+R",
                                  command=lambda: self._apply("start"))
        download_menu.add_command(label="Duraklat", accelerator="Ctrl+P",
                                  command=lambda: self._apply("pause"))
        download_menu.add_command(label="Yeniden Başlat",
                                  command=lambda: self._apply("restart"))
        download_menu.add_command(label="İptal Et (dosyayı sil)",
                                  command=lambda: self._apply("cancel"))
        download_menu.add_separator()
        download_menu.add_command(label="Tümünü Duraklat", command=self.mgr.pause_all)
        download_menu.add_command(label="Tümünü Devam Ettir", command=self.mgr.resume_all)
        download_menu.add_separator()
        download_menu.add_command(label="Seçileni Klasörde Aç",
                                  command=self.open_selected_folder)
        download_menu.add_command(label="Seçileni Sil", accelerator="Delete",
                                  command=self.remove_selected)
        menubar.add_cascade(label="İndirme", menu=download_menu)

        queue_menu = tk.Menu(menubar, tearoff=0)
        queue_menu.add_command(label="Kuyruğu Başlat/Durdur",
                               accelerator="Ctrl+Shift+Q", command=self.toggle_queue)
        queue_menu.add_separator()
        queue_menu.add_command(label="Yukarı Taşı", command=lambda: self.move_selected(-1))
        queue_menu.add_command(label="Aşağı Taşı", command=lambda: self.move_selected(1))
        queue_menu.add_separator()
        queue_menu.add_command(label="Bitenleri Temizle",
                               command=self.mgr.clear_finished)
        menubar.add_cascade(label="Kuyruk", menu=queue_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        limit_menu = tk.Menu(tools_menu, tearoff=0)
        for label, kbps in (("Sınırsız", 0), ("512 KB/s", 512), ("1 MB/s", 1024),
                            ("2 MB/s", 2048), ("5 MB/s", 5120), ("10 MB/s", 10240)):
            limit_menu.add_command(
                label=label,
                command=lambda value=kbps: self.mgr.set_global_limit(value))
        tools_menu.add_cascade(label="Toplam Hız Sınırı", menu=limit_menu)
        tools_menu.add_separator()
        tools_menu.add_command(label="Kuyruğu Hemen Güncelle", command=self.mgr._tick)
        menubar.add_cascade(label="Araçlar", menu=tools_menu)

        site_menu = tk.Menu(menubar, tearoff=0)
        for site_name, *_domains in SUPPORTED_SITES:
            site_menu.add_command(label=site_name,
                                  command=lambda n=site_name: self.add_site(n))
        menubar.add_cascade(label="Siteler", menu=site_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hakkında", command=self.show_about)
        menubar.add_cascade(label="Yardım", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_toolbar(self):
        bar = ttk.Frame(self.root, padding=(6, 5))
        bar.pack(fill="x")

        def btn(icon, text, command):
            image = load_photo(f"icons/{icon}.png", self._photos)
            widget = ttk.Button(bar, text=text, image=image, compound="left",
                                command=command)
            widget.pack(side="left", padx=2)
            return widget

        btn("add", "URL Ekle", self.add_url)
        btn("batch", "Toplu Ekle", self.add_batch)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        btn("play", "Başlat", lambda: self._apply("start"))
        btn("pause", "Duraklat", lambda: self._apply("pause"))
        btn("stop", "İptal", lambda: self._apply("cancel"))
        btn("retry", "Yeniden Başlat", lambda: self._apply("restart"))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        btn("delete", "Sil", self.remove_selected)
        btn("folder", "Klasör", self.open_selected_folder)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        btn("grabber", "Site Grabber", self.open_grabber)
        btn("schedule", "Zamanlayıcı", self.open_scheduler)

        self.btn_queue = ttk.Button(bar, text="Kuyruğu Durdur", command=self.toggle_queue)
        self.btn_queue.pack(side="right", padx=2)
        btn("settings", "Ayarlar", self.open_settings).pack(side="right", padx=2)

        self.btn_limit = ttk.Button(bar, text="Hız: Sınırsız", command=self._show_limits)
        self.btn_limit.pack(side="right", padx=6)

    def _build_site_bar(self):
        bar = ttk.Frame(self.root, padding=(6, 0))
        bar.pack(fill="x")
        ttk.Label(bar, text="Hızlı site indirme:", foreground="#5f6368",
                  font=("Segoe UI", 9, "bold")).pack(side="left", padx=(2, 6))
        self.site_buttons = []
        for name, *_domains in SUPPORTED_SITES:
            icon = SITE_ICONS.get(name, "add")
            image = load_photo(f"icons/site_{icon}.png", self._photos)
            widget = ttk.Button(bar, text=name, image=image, compound="left",
                                command=lambda n=name: self.add_site(n))
            widget.pack(side="left", padx=2)
            self.site_buttons.append(widget)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Label(bar, foreground="#9aa0a6", font=("Segoe UI", 8),
                  text="Bağlantıyı yapıştırıp indirin · gizli içerik için "
                       "Ayarlar > Çerez").pack(side="left", padx=4)

    def _show_limits(self):
        menu = tk.Menu(self.root, tearoff=0)
        current = int(getattr(self.mgr.settings, "speed_limit", 0) or 0)
        for label, kbps in (("Sınırsız", 0), ("512 KB/s", 512), ("1 MB/s", 1024),
                            ("2 MB/s", 2048), ("5 MB/s", 5120), ("10 MB/s", 10240)):
            def choose(value=kbps, text=label):
                self.mgr.set_global_limit(value)
                self.btn_limit.configure(
                    text="Hız: Sınırsız" if value == 0 else f"Hız: {text}")
                self.mgr.log(f"Toplam hız sınırı: {text}", "info")
            menu.add_command(label=("\u2713  " if kbps == current else "") + label,
                             command=choose)
        try:
            menu.tk_popup(self.btn_limit.winfo_rootx(),
                          self.btn_limit.winfo_rooty() + self.btn_limit.winfo_height())
        finally:
            menu.grab_release()

    def open_scheduler(self):
        self.open_settings(tab="queue")

    def _build_body(self):
        body = ttk.Panedwindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        left = ttk.Frame(body, width=200)
        body.add(left, weight=0)
        ttk.Label(left, text="  KATEGORİLER", foreground="#5f6368",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=6, pady=(6, 2))
        self.cat_tree = ttk.Treeview(left, show="tree", selectmode="browse",
                                     height=len(CATEGORY_ITEMS))
        self.cat_tree.pack(fill="both", expand=True, padx=(4, 4), pady=(0, 6))
        for iid, label in CATEGORY_ITEMS:
            self.cat_tree.insert("", "end", iid=iid, text=label)
            self._cat_texts[iid] = label
        self.cat_tree.selection_set("all")
        self.cat_tree.bind("<<TreeviewSelect>>", self._on_category)

        right = ttk.Frame(body)
        body.add(right, weight=1)

        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill="both", expand=True)

        downloads = ttk.Frame(self.notebook)
        self.notebook.add(downloads, text=" İndirmeler ")

        tree_frame = ttk.Frame(downloads)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=TREE_COLUMNS, show="headings",
                                 selectmode="extended")
        for column in TREE_COLUMNS:
            self.tree.heading(column, text=TREE_HEADINGS[column])
            self.tree.column(column, width=TREE_WIDTHS[column],
                             minwidth=50,
                             anchor="w" if column == "filename" else "center")
        for tag, color in STATE_COLORS.items():
            self.tree.tag_configure(tag, foreground=color)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="we")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        details = ttk.Frame(downloads, padding=(4, 5))
        details.pack(fill="x")
        details.columnconfigure(0, weight=1)

        self.var_detail = tk.StringVar(value="İndirme seçilmedi.")
        ttk.Label(details, textvariable=self.var_detail).grid(row=0, column=0,
                                                              sticky="w")
        self.var_state_detail = tk.StringVar(value="")
        ttk.Label(details, textvariable=self.var_state_detail, foreground="#5f6368").grid(
            row=0, column=1, sticky="e")

        self.segments_canvas = tk.Canvas(details, height=26, background="#202124",
                                         highlightthickness=1,
                                         highlightbackground="#5f6368")
        self.segments_canvas.grid(row=1, column=0, columnspan=2, sticky="we", pady=(6, 4))

        self.progress = ttk.Progressbar(details, maximum=100)
        self.progress.grid(row=2, column=0, columnspan=2, sticky="we")

        history = ttk.Frame(self.notebook)
        self.notebook.add(history, text=" Tarihçe ")
        columns = ("filename", "size", "category", "finished", "path")
        self.history_tree = ttk.Treeview(history, columns=columns, show="headings")
        for column, label, width in (
                ("filename", "Dosya", 320), ("size", "Boyut", 100),
                ("category", "Kategori", 110), ("finished", "Bitiş", 150),
                ("path", "Yol", 420)):
            self.history_tree.heading(column, text=label)
            self.history_tree.column(column, width=width, anchor="w")
        vsb2 = ttk.Scrollbar(history, orient="vertical",
                             command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=vsb2.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")
        self.history_tree.bind("<Double-1>", self._open_history)

        logs = ttk.Frame(self.notebook)
        self.notebook.add(logs, text=" Günlük ")
        self.log_text = tk.Text(logs, wrap="word", state="normal",
                                background="#202124", foreground="#e8eaed",
                                insertbackground="#e8eaed", font=("Consolas", 9))
        log_scroll = ttk.Scrollbar(logs, orient="vertical",
                                   command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        for tag, color in (("error", "#f28b82"), ("warning", "#fdd663"),
                           ("success", "#81c995"), ("info", "#e8eaed")):
            self.log_text.tag_configure(tag, foreground=color)
        self.log_text.configure(state="disabled")

        self.tree.bind("<Button-3>", self._show_context)
        self.tree.bind("<Double-1>", self._on_double_click)

    def _build_statusbar(self):
        status = ttk.Frame(self.root, padding=(8, 3))
        status.pack(fill="x", side="bottom")
        self.var_status_left = tk.StringVar()
        self.var_status_right = tk.StringVar()
        ttk.Label(status, textvariable=self.var_status_left).pack(side="left")
        ttk.Label(status, textvariable=self.var_status_right, foreground="#0b57d0"
                  ).pack(side="right")

    def _bind_keys(self):
        self.root.bind("<Control-n>", lambda _e: self.add_url())
        self.root.bind("<Control-N>", lambda _e: self.add_url())
        self.root.bind("<Control-b>", lambda _e: self.add_batch())
        self.root.bind("<Control-B>", lambda _e: self.add_batch())
        self.root.bind("<Control-v>", lambda _e: self.add_from_clipboard())
        self.root.bind("<Control-V>", lambda _e: self.add_from_clipboard())
        self.root.bind("<Control-p>", lambda _e: self._apply("pause"))
        self.root.bind("<Control-r>", lambda _e: self._apply("start"))
        self.root.bind("<Control-q>", lambda _e: self._on_close())
        self.root.bind("<Control-comma>", lambda _e: self.open_settings())
        self.root.bind("<Delete>", lambda _e: self.remove_selected())
        self.root.bind("<F5>", lambda _e: self.mgr._tick())

    @staticmethod
    def _create_root():
        try:
            from tkinterdnd2 import TkinterDnD
            return TkinterDnD.Tk()
        except Exception:
            return tk.Tk()

    def _setup_dnd(self):
        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._on_drop)
            self.root.dnd_bind("<<DropEnter>>", lambda _e: "copy")
        except Exception:
            return

    def _on_drop(self, event):
        raw = str(event.data or "")
        chunks = []
        for token in raw.replace("{", " ").replace("}", " ").split():
            token = token.strip()
            if token:
                chunks.append(token)
        urls = [token for token in chunks if looks_like_url(token)]
        if not urls:
            self.mgr.log("Sürüklenen öğede geçerli bağlantı bulunamadı.", "warning")
            return
        dialog = AddDialog(self.root, self.mgr, initial="\n".join(urls),
                           batch=len(urls) > 1)
        self.root.wait_window(dialog)
        if dialog.result:
            self._create_tasks(dialog.result)

    def _selected_ids(self):
        return list(self.tree.selection())

    def _selected_tasks(self):
        tasks = [self.mgr.get(iid) for iid in self._selected_ids()]
        return [t for t in tasks if t]

    def _apply(self, action):
        tasks = self._selected_tasks()
        if not tasks:
            self.mgr.log("Önce bir indirme seçin.", "warning")
            return
        for task in tasks:
            if action == "pause":
                task.pause()
            elif action == "start":
                if task.state in (PAUSED, ERROR, QUEUED, SCHEDULED):
                    task.start()
            elif action == "cancel":
                task.cancel(delete_files=True)
            elif action == "restart":
                task.restart()

    def add_url(self, initial="", site=None):
        dialog = AddDialog(self.root, self.mgr, initial=initial, batch=False,
                           site=site)
        self.root.wait_window(dialog)
        if dialog.result:
            self._create_tasks(dialog.result)
        return dialog

    def add_site(self, site):
        return self.add_url(site=site)

    def add_batch(self):
        dialog = AddDialog(self.root, self.mgr, batch=True)
        self.root.wait_window(dialog)
        if dialog.result:
            self._create_tasks(dialog.result)

    def add_from_clipboard(self):
        try:
            text = self.root.clipboard_get().strip()
        except Exception:
            text = ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        urls = [line for line in lines if looks_like_url(line)]
        if not urls:
            messagebox.showinfo("Panoda URL yok",
                                "Panoda geçerli bir http/https bağlantısı bulunamadı.",
                                parent=self.root)
            return
        dialog = AddDialog(self.root, self.mgr, initial="\n".join(urls), batch=len(urls) > 1)
        self.root.wait_window(dialog)
        if dialog.result:
            self._create_tasks(dialog.result)

    def _create_tasks(self, data):
        kwargs = {key: data[key] for key in (
            "category", "subdir", "filename", "segments", "speed_limit",
            "scheduled_at", "referer", "user_agent", "cookies", "extra_headers")
            if key in data}
        tasks = self.mgr.add(data["urls"], **kwargs)
        if tasks:
            try:
                self._sync_rows()
            except Exception:
                pass
            first = tasks[0].id
            if self.tree.exists(first):
                self.tree.selection_set(first)
                self.tree.focus(first)

    def open_grabber(self):
        GrabberDialog(self.root, self.mgr)

    def open_settings(self, tab=None):
        dialog = SettingsDialog(self.root, self.mgr, tab=tab)
        self.root.wait_window(dialog)
        if dialog.result:
            was_queue = self.mgr.queue_running
            self.mgr.apply_settings(dialog.result)
            want_queue = bool(dialog.result.get("queue_running"))
            if want_queue and not was_queue:
                self.mgr.start_queue()
            elif not want_queue and was_queue:
                self.mgr.stop_queue()
            self.mgr.log("Ayarlar kaydedildi.", "success")

    def clear_history(self):
        if messagebox.askyesno("Geçmiş", "Tüm geçmiş kayıtları silinsin mi?",
                               parent=self.root):
            self.mgr.history_clear()

    def show_about(self):
        about = [
            f"Retro+ Download Manager {__version__}",
            "",
            "Bağımsız Python indirme modülü:",
            "• Çok parçalı (32 parça) indirme, duraklat / devam / iptal",
            "• Web sayfası ve playlist algılama (yt-dlp ile site desteği)",
            "• Kuyruk, zamanlayıcı, görev başına hız sınırı",
            "• Kategoriler, otomatik klasörleme, sol panel filtreleri",
            "• Site Grabber, toplu ekleme, tarayıcı köprüsü, pano izleme",
            "• Proxy, çerez, referer, özel başlıklar, ayna URL destekli",
            "• Otomatik yeniden deneme, virüs tarama, sesli bildirim",
        ]
        logo = load_photo("logo_small.png", self._photos)
        if logo is None:
            messagebox.showinfo("Hakkında", "\n".join(about), parent=self.root)
            return
        box = tk.Toplevel(self.root)
        box.title("Hakkında")
        box.transient(self.root)
        box.resizable(False, False)
        tk.Label(box, image=logo).pack(padx=16, pady=(14, 4))
        tk.Label(box, text="\n".join(about), justify="left",
                 font=("Segoe UI", 10)).pack(padx=16, pady=(0, 8))
        ttk.Button(box, text="Kapat", command=box.destroy).pack(pady=(0, 12))
        center_window(box, self.root)

    def remove_selected(self):
        ids = self._selected_ids()
        if not ids:
            return
        running = [i for i in ids
                   if (self.mgr.get(i) and self.mgr.get(i).is_busy)]
        if running and not messagebox.askyesno(
                "Sil", f"{len(running)} indirme devam ediyor. Silinsin mi?",
                parent=self.root):
            return
        for task_id in ids:
            self.mgr.remove(task_id, delete_files=False)

    def move_selected(self, offset):
        for task_id in reversed(self._selected_ids()):
            self.mgr.move(task_id, offset)

    def open_selected_folder(self):
        tasks = self._selected_tasks()
        if not tasks:
            return
        task = tasks[0]
        path = task.final_path if task.state == COMPLETED else task.destination
        if path:
            open_path(str(path))

    def toggle_queue(self):
        self.mgr.toggle_queue()

    def _on_double_click(self, _event):
        tasks = self._selected_tasks()
        if not tasks:
            return
        task = tasks[0]
        if task.state == COMPLETED:
            open_path(task.destination)
        elif task.state in (PAUSED, ERROR):
            task.start()
        elif task.is_busy:
            task.pause()

    def _open_history(self, _event):
        selection = self.history_tree.selection()
        if not selection:
            return
        values = self.history_tree.item(selection[0], "values")
        path = values[4] if len(values) > 4 else ""
        if path:
            open_path(path)

    def _show_context(self, event):
        row = self.tree.identify_row(event.y)
        if row and row not in self.tree.selection():
            self.tree.selection_set(row)
        if not self.tree.selection():
            return
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Devam Et", command=lambda: self._apply("start"))
        menu.add_command(label="Duraklat", command=lambda: self._apply("pause"))
        menu.add_command(label="Yeniden Başlat", command=lambda: self._apply("restart"))
        menu.add_command(label="İptal Et", command=lambda: self._apply("cancel"))
        menu.add_separator()
        menu.add_command(label="Klasörü Aç", command=self.open_selected_folder)
        menu.add_command(label="Bağlantıyı Kopyala", command=self._copy_url)
        menu.add_command(label="Özellikler...", command=self._open_properties)
        menu.add_separator()
        menu.add_command(label="Yukarı Taşı", command=lambda: self.move_selected(-1))
        menu.add_command(label="Aşağı Taşı", command=lambda: self.move_selected(1))
        menu.add_separator()
        menu.add_command(label="Listeden Sil", command=self.remove_selected)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_url(self):
        tasks = self._selected_tasks()
        if tasks:
            self.root.clipboard_clear()
            self.root.clipboard_append(tasks[0].url)

    def _open_properties(self):
        tasks = self._selected_tasks()
        if tasks:
            PropertiesDialog(self.root, self.mgr, tasks[0])

    def _row_values(self, snap):
        percent = "-" if snap["percent"] < 0 else f"{snap['percent']:.1f}"
        segments = "-" if snap.get("external") else str(len(snap["segments"]))
        return (
            snap["filename"],
            format_bytes(snap["size"]),
            format_speed(snap["speed"]),
            format_eta(snap["eta"]),
            segments,
            percent,
            snap["state_label"],
        )

    def _matches_filter(self, snap):
        key = self._filter
        if key == "all":
            return True
        if key == "active":
            return snap["state"] in (DOWNLOADING, PROBING)
        if key == "queued":
            return snap["state"] in (QUEUED, SCHEDULED, PAUSED, ERROR, CANCELED)
        if key == "done":
            return snap["state"] == COMPLETED
        if key.startswith("cat:"):
            return snap["category"] == key[4:]
        return True

    def _count_snapshot(self, snap, counts):
        counts["all"] += 1
        if snap["state"] in (DOWNLOADING, PROBING):
            counts["active"] += 1
        elif snap["state"] in (QUEUED, SCHEDULED, PAUSED, ERROR, CANCELED):
            counts["queued"] += 1
        elif snap["state"] == COMPLETED:
            counts["done"] += 1
        counts["cat:" + snap["category"]] += 1

    def _update_category_texts(self, counts):
        for iid, label in CATEGORY_ITEMS:
            text = f"{label} ({counts.get(iid, 0)})"
            if self._cat_texts.get(iid) != text:
                self._cat_texts[iid] = text
                if self.cat_tree.exists(iid):
                    self.cat_tree.item(iid, text=text)

    def _on_category(self, _event=None):
        selection = self.cat_tree.selection()
        key = selection[0] if selection else "all"
        if key == self._filter:
            return
        self._filter = key
        self._rows.clear()
        self.tree.delete(*self.tree.get_children())
        self._sync_rows()

    def _sync_rows(self):
        snapshots = self.mgr.snapshot_list()
        counts = {iid: 0 for iid, _label in CATEGORY_ITEMS}
        visible = []
        for snap in snapshots:
            self._count_snapshot(snap, counts)
            if self._matches_filter(snap):
                visible.append(snap)
        seen = set()
        for snap in visible:
            iid = snap["id"]
            seen.add(iid)
            values = self._row_values(snap)
            tag = STATE_TAGS.get(snap["state"], "queued")
            if self.tree.exists(iid):
                for column, value in zip(TREE_COLUMNS, values):
                    if self.tree.set(iid, column) != str(value):
                        self.tree.set(iid, column, value)
                current_tags = self.tree.item(iid, "tags")
                if not current_tags or current_tags[0] != tag:
                    self.tree.item(iid, tags=(tag,))
                self._rows[iid] = values
            else:
                self.tree.insert("", "end", iid=iid, values=values, tags=(tag,))
                self._rows[iid] = values
        for iid in list(self._rows):
            if iid not in seen:
                if self.tree.exists(iid):
                    self.tree.delete(iid)
                del self._rows[iid]
        expected = [snap["id"] for snap in visible]
        current = list(self.tree.get_children(""))
        if current != expected:
            for index, iid in enumerate(expected):
                if self.tree.exists(iid):
                    self.tree.move("", index, iid)
        self._update_category_texts(counts)

    def _update_details(self):
        tasks = self._selected_tasks()
        task = tasks[0] if tasks else None
        if task is None:
            self.var_detail.set("İndirme seçilmedi.")
            self.var_state_detail.set("")
            self.progress["value"] = 0
            self.segments_canvas.delete("all")
            return
        snap = task.snapshot()
        parts = [
            snap["filename"],
            f"Boyut: {format_bytes(snap['size'])}",
            f"İndirilen: {format_bytes(snap['downloaded'])}",
            f"Hız: {format_speed(snap['speed'])}",
            f"Kalan: {format_eta(snap['eta'])}",
        ]
        if snap["segments"] and not snap.get("external"):
            parts.append(f"Parça: {len(snap['segments'])}")
        elif snap.get("external"):
            parts.append("Motor: yt-dlp (ses+video birleştirme)")
        if snap["scheduled_at"]:
            parts.append(f"Başlangıç: {snap['scheduled_at']}")
        self.var_detail.set("   |   ".join(parts))
        extra = snap["state_label"]
        if snap["error"]:
            extra += f" — {snap['error']}"
        self.var_state_detail.set(extra)
        percent = 0 if snap["percent"] < 0 else snap["percent"]
        self.progress["value"] = percent
        self._draw_segments(task)

    def _draw_segments(self, task):
        canvas = self.segments_canvas
        canvas.delete("all")
        width = canvas.winfo_width()
        if width <= 1:
            return
        height = 26
        segments = task.segments
        if not segments:
            canvas.create_rectangle(0, 0, width, height, fill="#202124", outline="")
            return
        count = len(segments)
        gap = 2 if count > 1 else 0
        bar_width = max(1.0, (width - gap * (count - 1)) / count)
        for index, segment in enumerate(segments):
            x0 = index * (bar_width + gap)
            x1 = x0 + bar_width
            canvas.create_rectangle(x0, 0, x1, height, fill="#3c4043", outline="")
            fraction = segment.fraction
            if fraction > 0:
                fill_height = max(1, int((height - 2) * fraction))
                canvas.create_rectangle(x0 + 1, height - 1 - fill_height,
                                        x1 - 1, height - 1,
                                        fill="#2ecc71" if fraction >= 1.0 else "#3aa8f0",
                                        outline="")

    def _update_status(self):
        stats = self.mgr.stats()
        st = self.mgr.settings
        queue_text = "Açık" if self.mgr.queue_running else "Kapalı"
        if st.schedule_enabled:
            schedule_text = f"{st.schedule_start}-{st.schedule_end}"
        else:
            schedule_text = "Kapalı"
        self.var_status_left.set(
            f"Kuyruk: {queue_text}   |   Zamanlama: {schedule_text}   |   "
            f"Eşzamanlı: {stats['active']}/{st.max_concurrent}   |   "
            f"Kayıt: {stats['total']} (kuyrukta {stats['queued']})")
        self.var_status_right.set(f"Toplam hız: {format_speed(stats['speed'])}")
        self.var_header_speed.set(format_speed(stats["speed"]))
        active = int(stats.get("active", 0))
        total = int(stats.get("total", 0))
        done = int(stats.get("completed", 0)) or 0
        self.var_header_active.set(
            f"İndiriliyor: {active}   ·   Tamamlanan: {done}   ·   Toplam: {total}")
        self.btn_queue.configure(
            text="Kuyruğu Durdur" if self.mgr.queue_running else "Kuyruğu Başlat")
        limit = int(getattr(st, "speed_limit", 0) or 0)
        self.btn_limit.configure(
            text="Hız: Sınırsız" if limit <= 0 else f"Hız: {format_speed(limit * 1024)}")

    def _drain_logs(self):
        entries = list(self.mgr.log_lines)
        fresh = [entry for entry in entries if entry["seq"] > self._log_seq]
        if not fresh:
            return
        self._log_seq = fresh[-1]["seq"]
        self.log_text.configure(state="normal")
        for entry in fresh:
            self.log_text.insert("end", f"[{entry['time']}] {entry['message']}\n",
                                 entry["level"])
        lines = int(self.log_text.index("end-1c").split(".")[0])
        if lines > 2000:
            self.log_text.delete("1.0", f"{lines - 1500}.0")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _refresh_history(self):
        if len(self.mgr.history) == self._history_len:
            return
        self._history_len = len(self.mgr.history)
        self.history_tree.delete(*self.history_tree.get_children())
        for entry in self.mgr.history:
            self.history_tree.insert("", "end", values=(
                entry.get("filename", ""),
                format_bytes(entry.get("size", -1)),
                CATEGORY_LABELS.get(entry.get("category"), entry.get("category", "")),
                format_datetime(entry.get("finished_at")),
                entry.get("path", ""),
            ))

    def _poll_clipboard(self):
        if not self.mgr.settings.clipboard_monitor:
            return
        try:
            text = (self.root.clipboard_get() or "").strip()
        except Exception:
            return
        if not text or text == self._last_clip:
            return
        self._last_clip = text
        if not looks_like_url(text):
            return
        if self.mgr.settings.clipboard_auto_add:
            self.mgr.add([text])
            self.mgr.log(f"Panodan otomatik eklendi: {text}", "info")
        else:
            self.var_status_right.set(f"Panoda URL algılandı: {text[:80]}")

    def _ui_tick(self):
        try:
            if self._all_done:
                self._all_done = False
                self.mgr.log("Kuyruk tamamlandı, program kapanıyor.", "success")
                self._on_close()
            self._sync_rows()
            self._update_details()
            self._update_status()
            self._drain_logs()
            self._refresh_history()
            self._tick_count += 1
            if self._tick_count % 3 == 0:
                self._poll_clipboard()
        except Exception as exc:
            print("UI hatası:", exc)
        try:
            self.root.after(400, self._ui_tick)
        except Exception:
            pass

    def _on_all_done(self):
        self._all_done = True

    def _on_close(self):
        active = [t for t in self.mgr.tasks if t.is_busy]
        if active:
            if not messagebox.askyesno(
                    "Çıkış",
                    f"{len(active)} indirme devam ediyor.\n"
                    "Duraklatılıp çıkış yapılsın mı? (Devam ettirmek için Vazgeç)",
                    parent=self.root):
                return
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


def run(argv=None):
    manager = DownloadManager()
    app = App(manager)
    try:
        if os.environ.get("RETRO_SMOKE"):
            app.root.after(1500, app.root.destroy)
        app.run()
    finally:
        manager.shutdown()
    return 0
