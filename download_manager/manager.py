"""Indirme yonetimi: ayarlar, kuyruk, zamanlayici, kategoriler, grabber, gecmis."""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from html.parser import HTMLParser
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List
from urllib.parse import parse_qs, unquote_plus, urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter

from . import notify
from .engine import (
    CANCELED,
    COMPLETED,
    DOWNLOADING,
    ERROR,
    PAUSED,
    QUEUED,
    SCHEDULED,
    DownloadTask,
    RateLimiter,
)
from .util import (
    DEFAULT_CATEGORY_FOLDERS,
    PAGE_EXTENSIONS,
    format_bytes,
)
from .whatsapp import WhatsAppWatcher

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class Settings:
    DEFAULTS = {
        "download_dir": str(Path.home() / "Downloads"),
        "category_folders": dict(DEFAULT_CATEGORY_FOLDERS),
        "max_concurrent": 3,
        "segments": 8,
        "speed_limit": 0,
        "retries": 10,
        "timeout_connect": 15,
        "timeout_read": 30,
        "proxy": "",
        "ftp_user": "anonymous",
        "ftp_password": "",
        "user_agent": DEFAULT_USER_AGENT,
        "referer": "",
        "cookies": "",
        "extra_headers": "",
        "queue_running": True,
        "auto_start": True,
        "schedule_enabled": False,
        "schedule_start": "09:00",
        "schedule_end": "18:00",
        "sound_enabled": True,
        "clipboard_monitor": False,
        "clipboard_auto_add": False,
        "bridge_enabled": True,
        "bridge_port": 8877,
        "scan_enabled": False,
        "scan_command": "",
        "exit_when_done": False,
        "update_enabled": True,
        "update_source": "",
        "wa_enabled": False,
        "wa_watch_folder": "",
        "wa_output_folder": "",
        "wa_whitelist": [],
    }

    def __init__(self, path):
        object.__setattr__(self, "path", Path(path))
        object.__setattr__(self, "data", dict(self.DEFAULTS))
        self.load()

    def load(self):
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return
        if isinstance(raw, dict):
            for key, value in raw.items():
                if key in self.DEFAULTS:
                    if key == "category_folders" and isinstance(value, dict):
                        merged = dict(self.DEFAULTS[key])
                        merged.update({k: v for k, v in value.items() if k in merged})
                        self.data[key] = merged
                    else:
                        self.data[key] = value

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = Path(str(self.path) + ".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            import os
            os.replace(tmp, self.path)
        except OSError:
            pass

    def update(self, values):
        for key, value in values.items():
            if key in self.DEFAULTS:
                if key == "category_folders" and isinstance(value, dict):
                    merged = dict(self.DEFAULTS[key])
                    merged.update({k: v for k, v in value.items() if k in merged})
                    self.data[key] = merged
                else:
                    self.data[key] = value
        self.save()

    def to_dict(self):
        return json.loads(json.dumps(self.data))

    def __getattr__(self, item):
        if item.startswith("_"):
            raise AttributeError(item)
        data = object.__getattribute__(self, "data")
        if item in data:
            return data[item]
        defaults = object.__getattribute__(self, "DEFAULTS")
        if item in defaults:
            return defaults[item]
        raise AttributeError(item)

    def __setattr__(self, key, value):
        if key in ("path", "data"):
            object.__setattr__(self, key, value)
            return
        if key in self.DEFAULTS:
            self.data[key] = value
            self.save()
        else:
            object.__setattr__(self, key, value)


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        for key in ("href", "src", "action", "data-src", "data-href", "poster"):
            value = data.get(key)
            if value and isinstance(value, str):
                self.links.append(value.strip())
        srcset = data.get("srcset")
        if srcset:
            for part in str(srcset).split(","):
                candidate = part.strip().split(" ")[0]
                if candidate:
                    self.links.append(candidate)


def extract_links(html, base_url):
    parser = _LinkParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    result = []
    seen = set()
    for raw in parser.links:
        if not raw or raw.startswith(("javascript:", "mailto:", "data:", "#", "tel:")):
            continue
        absolute = urljoin(base_url, raw).split("#")[0]
        if not re.match(r"^https?://", absolute, re.I):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        result.append(absolute)
    return result


def is_file_link(url, extensions=None):
    path = urlparse(url).path
    ext = Path(path).suffix.lower()
    if extensions:
        wanted = {e if e.startswith(".") else "." + e for e in extensions}
        return ext in wanted
    if not ext:
        return False
    return ext not in PAGE_EXTENSIONS


class DownloadManager:
    def __init__(self, data_dir=None):
        base = Path(data_dir) if data_dir else Path(__file__).resolve().parent / "data"
        base.mkdir(parents=True, exist_ok=True)
        self.data_dir = base
        self.settings = Settings(base / "settings.json")
        self.limiter = RateLimiter((self.settings.speed_limit or 0) * 1024)
        self.tasks: List[DownloadTask] = []
        self.lock = threading.RLock()
        self.log_lines = deque(maxlen=3000)
        self._log_seq = 0
        self.history = self._load_json("history.json", [])
        self.queue_running = bool(self.settings.queue_running)
        self._stop = threading.Event()
        self._logger = self._setup_logger()
        self._load_queue()
        self.on_all_done = None
        self._bridge = None
        self._bridge_thread = None
        self._bridge_port = int(self.settings.bridge_port or 8877)
        self._start_bridge()
        self._scheduler = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler.start()
        self.wa_watcher = WhatsAppWatcher(self)
        self.wa_watcher.start()
        self._updater_thread = None
        if bool(getattr(self.settings, "update_enabled", True)) and \
                (self.settings.update_source or "").strip():
            from .updater import start_auto_update
            self._updater_thread = start_auto_update(self)
        self.log("Retro+ Download Manager hazır.", "info")

    def _setup_logger(self):
        logger = logging.getLogger("pdm")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        if not logger.handlers:
            handler = RotatingFileHandler(self.data_dir / "indirme.log", maxBytes=512 * 1024,
                                          backupCount=3, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            logger.addHandler(handler)
        return logger

    def _load_json(self, name, default):
        path = self.data_dir / name
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _save_json(self, name, value):
        try:
            path = self.data_dir / name
            tmp = Path(str(path) + ".tmp")
            tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
            import os
            os.replace(tmp, path)
        except OSError:
            pass

    def _start_bridge(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        self._stop_bridge()
        if not self.settings.bridge_enabled:
            return
        manager = self

        class BridgeHandler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _headers(self, status=200):
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "*")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()

            def _reply(self, payload, status=200):
                self._headers(status)
                try:
                    self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
                except Exception:
                    pass

            def do_OPTIONS(self):
                self._headers(204)

            def do_GET(self):
                self._handle()

            def do_POST(self):
                self._handle()

            def _handle(self):
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                length = int(self.headers.get("Content-Length") or 0)
                body = ""
                if length:
                    try:
                        body = self.rfile.read(length).decode("utf-8", "ignore")
                    except Exception:
                        body = ""
                params = dict(query)
                if body:
                    if body.lstrip().startswith("{"):
                        try:
                            data = json.loads(body)
                            for key, value in data.items():
                                params.setdefault(key, [str(value)])
                        except Exception:
                            pass
                    for part in body.split("&"):
                        if "=" in part:
                            key, value = part.split("=", 1)
                            params.setdefault(key.strip(), [unquote_plus(value.strip())])
                path = parsed.path.rstrip("/") or "/"
                if path in ("/", "/add", "/download", "/geturl"):
                    url = (params.get("url") or [""])[0].strip()
                    if not url:
                        self._reply({"ok": False, "error": "url parametresi gerekli"})
                        return
                    try:
                        tasks = manager.add([url])
                    except Exception as exc:
                        self._reply({"ok": False, "error": str(exc)})
                        return
                    if not tasks:
                        self._reply({"ok": False, "error": "geçersiz URL"})
                        return
                    manager.log(f"Köprü üzerinden eklendi: {url}", "info")
                    self._reply({"ok": True, "id": tasks[0].id,
                                 "filename": tasks[0].filename or url})
                    return
                if path in ("/links", "/grab"):
                    target = (params.get("url") or [""])[0].strip()
                    if not target:
                        self._reply({"ok": False, "error": "url parametresi gerekli"})
                        return
                    depth = int((params.get("depth") or ["1"])[0] or 1)
                    ext_raw = (params.get("extensions") or [""])[0]
                    extensions = [e.strip() for e in ext_raw.split(",") if e.strip()] or None
                    try:
                        links = manager.grab(target, depth=depth, same_domain=True,
                                             extensions=extensions, max_pages=40)
                    except Exception as exc:
                        self._reply({"ok": False, "error": str(exc)})
                        return
                    self._reply({"ok": True, "count": len(links), "links": links})
                    return
                if path in ("/status", "/ping"):
                    stats = manager.stats()
                    self._reply({"ok": True, "queue": manager.queue_running, **stats})
                    return
                self._reply({"ok": False, "error": "bilinmeyen uç nokta"}, status=404)

        port = int(self.settings.bridge_port or 8877)
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), BridgeHandler)
        except OSError as exc:
            self.log(f"Tarayıcı köprüsü başlatılamadı (port {port}): {exc}", "warning")
            self._bridge = None
            self._bridge_thread = None
            return
        self._bridge = server
        self._bridge_thread = threading.Thread(target=server.serve_forever,
                                               kwargs={"poll_interval": 0.5},
                                               daemon=True)
        self._bridge_thread.start()
        self._bridge_port = server.server_address[1]
        self.log(f"Tarayıcı köprüsü hazır: "
                 f"http://127.0.0.1:{self._bridge_port}/add?url=<indirme adresi>",
                 "info")

    def _stop_bridge(self):
        bridge = getattr(self, "_bridge", None)
        if bridge is not None:
            try:
                bridge.shutdown()
                bridge.server_close()
            except Exception:
                pass
        self._bridge = None
        self._bridge_thread = None

    def _restart_bridge(self, values=None):
        if values is None:
            self._start_bridge()
            return
        if "bridge_enabled" in values or "bridge_port" in values:
            self._start_bridge()

    def log(self, message, level="info"):
        stamp = time.strftime("%H:%M:%S")
        self._log_seq += 1
        self.log_lines.append({"seq": self._log_seq, "time": stamp, "level": level,
                               "message": str(message)})
        levelno = {"error": logging.ERROR, "warning": logging.WARNING,
                   "success": logging.INFO}.get(level, logging.INFO)
        try:
            self._logger.log(levelno, message)
        except Exception:
            pass

    def get(self, task_id):
        with self.lock:
            for task in self.tasks:
                if task.id == task_id:
                    return task
        return None

    def snapshot_list(self):
        with self.lock:
            return [task.snapshot() for task in self.tasks]

    def is_part_taken(self, path, owner):
        target = str(path)
        with self.lock:
            for task in self.tasks:
                if task is owner:
                    continue
                if task.part_path and str(task.part_path) == target:
                    if task.is_busy or task.state in (QUEUED, SCHEDULED, PAUSED):
                        return True
        return False

    def _normalize_url(self, url):
        url = (url or "").strip().strip("'\"")
        if not url:
            return None
        if re.match(r"^(https?|ftp)://", url, re.I):
            return url
        if re.match(r"^[a-z0-9-]+(\.[a-z0-9-]+)+(:\d+)?(/|$|\?)", url, re.I):
            return "https://" + url
        return None

    def add(self, urls=None, **kwargs):
        if isinstance(urls, str):
            urls = [urls]
        created = []
        for raw in urls or []:
            entry = raw if isinstance(raw, dict) else None
            source = entry.get("url") if entry else raw
            url = self._normalize_url(source)
            if not url:
                self.log(f"Geçersiz URL atlandı: {source}", "warning")
                continue
            options = dict(kwargs)
            if entry:
                if entry.get("filename") and not options.get("filename"):
                    options["filename"] = entry["filename"]
                headers = dict(entry.get("headers") or {})
                if headers:
                    merged = dict(options.get("extra_headers") or {})
                    merged.update(headers)
                    options["extra_headers"] = merged
            task = DownloadTask(url, self, **options)
            with self.lock:
                self.tasks.append(task)
            created.append(task)
            self.log(f"Eklendi: {url}", "info")
        if created:
            self.save_queue()
            if self.settings.auto_start:
                threading.Thread(target=self._start_immediately, args=(created,),
                                 daemon=True).start()
        return created

    def add_batch(self, text, **kwargs):
        lines = [line.strip() for line in (text or "").splitlines()]
        urls = [line for line in lines if line and not line.startswith("#")]
        return self.add(urls, **kwargs)

    def _start_immediately(self, tasks):
        for task in tasks:
            if task.scheduled_at:
                self._tick()
                return
            with self.lock:
                busy = sum(1 for t in self.tasks if t.is_busy)
                if busy >= int(self.settings.max_concurrent):
                    self._tick()
                    return
            if task.state in (QUEUED, SCHEDULED):
                task.start()
            time.sleep(0.05)

    def remove(self, task_id, delete_files=False):
        task = self.get(task_id)
        if not task:
            return False
        if task.is_busy:
            task.stop(delete_files=delete_files)
            threading.Thread(target=self._remove_after_stop, args=(task,),
                             daemon=True).start()
        else:
            self._remove_from_list(task)
        return True

    def _remove_after_stop(self, task):
        task._wait_idle(60.0)
        self._remove_from_list(task)

    def _remove_from_list(self, task):
        with self.lock:
            if task in self.tasks:
                self.tasks.remove(task)
        self.save_queue()
        self.log(f"Listeden kaldırıldı: {task.filename or task.url}", "info")

    def pause(self, task_id):
        task = self.get(task_id)
        if task:
            task.pause()

    def resume(self, task_id):
        task = self.get(task_id)
        if task:
            task.start()

    def cancel(self, task_id, delete_files=True):
        task = self.get(task_id)
        if task:
            task.cancel(delete_files=delete_files)

    def restart(self, task_id):
        task = self.get(task_id)
        if task:
            task.restart()

    def pause_all(self):
        for task in list(self.tasks):
            if task.is_busy:
                task.pause()

    def resume_all(self):
        for task in list(self.tasks):
            if task.state == PAUSED:
                task.start()

    def clear_finished(self):
        with self.lock:
            keep = [t for t in self.tasks if t.state not in (COMPLETED, CANCELED)]
            removed = len(self.tasks) - len(keep)
            self.tasks = keep
        if removed:
            self.save_queue()
            self.log(f"{removed} kayıt temizlendi.", "info")

    def move(self, task_id, offset):
        with self.lock:
            for index, task in enumerate(self.tasks):
                if task.id == task_id:
                    target = index + offset
                    if 0 <= target < len(self.tasks):
                        self.tasks.pop(index)
                        self.tasks.insert(target, task)
                        break
        self.save_queue()

    def start_queue(self):
        self.queue_running = True
        self.settings.queue_running = True
        self.log("Kuyruk başlatıldı.", "info")
        self._tick()

    def stop_queue(self):
        self.queue_running = False
        self.settings.queue_running = False
        self.log("Kuyruk durduruldu.", "info")

    def toggle_queue(self):
        if self.queue_running:
            self.stop_queue()
        else:
            self.start_queue()

    def set_global_limit(self, kbps):
        self.settings.speed_limit = int(kbps or 0)
        self.limiter.set_limit((int(kbps or 0)) * 1024)

    def apply_settings(self, values=None):
        if values:
            self.settings.update(values)
        self.limiter.set_limit((int(self.settings.speed_limit or 0)) * 1024)
        folder = Path(self.settings.download_dir).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        self._restart_bridge(values)
        if values and any(key.startswith("wa_") for key in values):
            try:
                self.wa_watcher.restart()
            except Exception as exc:
                self.log(f"WhatsApp izleyici yeniden başlatılamadı: {exc}", "error")
        self.save_queue()

    def _in_window(self):
        if not self.settings.schedule_enabled:
            return True
        current = time.strftime("%H:%M")
        start = str(self.settings.schedule_start or "00:00")
        end = str(self.settings.schedule_end or "23:59")
        if start <= end:
            return start <= current < end
        return current >= start or current < end

    def _tick(self):
        if not self.queue_running:
            return
        if not self._in_window():
            return
        with self.lock:
            busy = sum(1 for t in self.tasks if t.is_busy)
            slots = int(self.settings.max_concurrent) - busy
            if slots <= 0:
                return
            now = datetime.now()
            for task in list(self.tasks):
                if slots <= 0:
                    break
                if task.is_busy or task.state in (COMPLETED, CANCELED, PAUSED, ERROR):
                    continue
                if task.state not in (QUEUED, SCHEDULED):
                    continue
                if task.scheduled_at and task.scheduled_at > now:
                    if task.state != SCHEDULED:
                        task.state = SCHEDULED
                        self.log(f"Zamanlandı: {task.filename or task.url} "
                                 f"({task.scheduled_at.strftime('%d.%m.%Y %H:%M')})", "info")
                    continue
                if task.start():
                    slots -= 1
            self._check_all_done()

    def _scheduler_loop(self):
        while not self._stop.wait(1.0):
            try:
                self._tick()
            except Exception as exc:
                self.log(f"Zamanlayıcı hatası: {exc}", "error")

    def _check_all_done(self):
        if not self.queue_running:
            return
        if not self.settings.exit_when_done:
            return
        if any(t.is_busy or t.state in (QUEUED, SCHEDULED, PAUSED, ERROR)
               for t in self.tasks):
            return
        if any(t.state == COMPLETED for t in self.tasks) and self.on_all_done:
            callback, self.on_all_done = self.on_all_done, None
            try:
                callback()
            except Exception:
                pass

    def task_finished(self, task):
        try:
            if task.state == COMPLETED:
                self.history_add(task)
                size = format_bytes(task.size)
                self.log(f"Tamamlandı: {task.filename} ({size})", "success")
                if self.settings.sound_enabled:
                    notify.beep("ok")
                if self.settings.scan_enabled and self.settings.scan_command and task.final_path:
                    threading.Thread(target=self._scan_file,
                                     args=(str(task.final_path),), daemon=True).start()
            elif task.state == ERROR:
                self.log(f"İndirme başarısız: {task.filename or task.url} — {task.error}",
                         "error")
                if self.settings.sound_enabled:
                    notify.beep("error")
            self.save_queue()
            self._tick()
        except Exception as exc:
            self.log(f"Olay işlenemedi: {exc}", "error")

    def _scan_file(self, path):
        command = str(self.settings.scan_command or "").strip()
        if not command:
            return
        import subprocess
        full = command.replace("{file}", f'"{path}"')
        self.log(f"Virüs taraması başlatılıyor: {path}", "info")
        try:
            # CREATE_NO_WINDOW: GUI konsolsuz (pythonw) calisirken tarama
            # penceresinin CMD olarak acilmasini onler.
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            result = subprocess.run(full, shell=True, capture_output=True, text=True,
                                    timeout=900, creationflags=flags)
            if result.returncode == 0:
                self.log(f"Tarama temiz: {path}", "success")
            else:
                output = (result.stdout or result.stderr or "").strip()
                self.log(f"Tarama uyarısı (kod {result.returncode}): {output[:300]}",
                         "warning")
        except Exception as exc:
            self.log(f"Tarama çalıştırılamadı: {exc}", "error")

    @staticmethod
    def detect_defender():
        import os
        candidates = []
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        for base in (program_files, program_files_x86):
            candidates.append(Path(base) / "Windows Defender" / "MpCmdRun.exe")
        local = os.environ.get("ProgramData")
        if local:
            candidates.append(Path(local) / "Microsoft" / "Windows Defender" /
                              "Platform" / "MsMpEng.exe")
        for path in candidates:
            if path.exists() and path.name == "MpCmdRun.exe":
                return f'"{path}" -Scan -ScanType 3 -File {{file}}'
        return ""

    def history_add(self, task):
        entry = {
            "filename": task.filename,
            "url": task.url,
            "size": task.size,
            "category": task.category,
            "path": str(task.final_path or ""),
            "finished_at": time.time(),
        }
        self.history.insert(0, entry)
        del self.history[500:]
        self._save_json("history.json", self.history)

    def history_clear(self):
        self.history = []
        self._save_json("history.json", self.history)
        self.log("Geçmiş temizlendi.", "info")

    def save_queue(self):
        with self.lock:
            payload = [t.to_dict() for t in self.tasks
                       if t.state not in (COMPLETED, CANCELED)]
        self._save_json("queue.json", payload)

    def _load_queue(self):
        payload = self._load_json("queue.json", [])
        if not isinstance(payload, list):
            return
        for item in payload:
            if not isinstance(item, dict) or not item.get("url"):
                continue
            try:
                task = DownloadTask.from_dict(item, self)
            except Exception:
                continue
            if task.url:
                with self.lock:
                    self.tasks.append(task)
        if self.tasks:
            self.log(f"Kuyruk yüklendi: {len(self.tasks)} kayıt.", "info")

    def _http_session(self):
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=16)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        proxy = (self.settings.proxy or "").strip()
        if proxy:
            session.proxies.update({"http": proxy, "https": proxy})
        headers = {"User-Agent": self.settings.user_agent, "Accept": "*/*",
                   "Accept-Encoding": "identity"}
        if self.settings.referer:
            headers["Referer"] = self.settings.referer
        if self.settings.cookies:
            headers["Cookie"] = self.settings.cookies
        session.headers.update(headers)
        return session

    def _fetch_page(self, session, url):
        try:
            response = session.get(url, timeout=(self.settings.timeout_connect,
                                                 self.settings.timeout_read),
                                   allow_redirects=True)
        except Exception:
            return None, None
        try:
            if response.status_code >= 400:
                return None, None
            ctype = str(response.headers.get("Content-Type", "")).lower()
            if "html" not in ctype and "xml" not in ctype:
                return response.url, None
            response.encoding = response.apparent_encoding or response.encoding or "utf-8"
            return response.url, response.text
        finally:
            response.close()

    def grab(self, url, depth=1, same_domain=True, extensions=None, max_pages=80,
             on_progress=None, max_threads=4):
        session = self._http_session()
        base_host = urlparse(url).netloc.lower()
        file_links: Dict[str, bool] = {}
        visited = set()
        frontier = [(url, 0)]
        pages = 0
        wanted = None
        if extensions:
            wanted = [e.strip() for e in extensions if e.strip()]
            if not wanted:
                wanted = None
        try:
            while frontier and pages < max_pages:
                batch = frontier[:max_threads]
                frontier = frontier[max_threads:]
                with ThreadPoolExecutor(max_workers=max_threads) as pool:
                    fetched = list(pool.map(
                        lambda item: self._fetch_page(session, item[0]), batch))
                for (page_url, page_depth), (final_url, html) in zip(batch, fetched):
                    pages += 1
                    key = final_url or page_url
                    visited.add(key)
                    if not html:
                        continue
                    for link in extract_links(html, key):
                        parsed = urlparse(link)
                        if same_domain and parsed.netloc.lower() != base_host:
                            continue
                        if is_file_link(link, wanted):
                            file_links.setdefault(link, True)
                        elif page_depth < depth and link not in visited:
                            if not any(link == u for u, _ in frontier):
                                frontier.append((link, page_depth + 1))
                    if on_progress:
                        try:
                            on_progress(len(file_links), pages)
                        except Exception:
                            pass
        finally:
            session.close()
        return list(file_links.keys())

    def stats(self):
        with self.lock:
            active = [t for t in self.tasks if t.state == DOWNLOADING]
            queued = sum(1 for t in self.tasks if t.state in (QUEUED, SCHEDULED))
            completed = sum(1 for t in self.tasks if t.state == COMPLETED)
            total_speed = sum(t.speed for t in active)
            return {
                "active": len(active),
                "queued": queued,
                "completed": completed,
                "total": len(self.tasks),
                "speed": total_speed,
            }

    def shutdown(self):
        self._stop.set()
        watcher = getattr(self, "wa_watcher", None)
        if watcher is not None:
            try:
                watcher.stop()
            except Exception:
                pass
        if self._scheduler.is_alive():
            self._scheduler.join(timeout=3.0)
        self._stop_bridge()
        for task in list(self.tasks):
            if task.is_busy:
                task.pause()
        deadline = time.time() + 15.0
        while time.time() < deadline:
            if not any(t.is_busy for t in self.tasks):
                break
            time.sleep(0.2)
        self.settings.queue_running = self.queue_running
        self.save_queue()
        self.settings.save()
        self.log("Oturum kapatıldı.", "info")


__all__ = [
    "DownloadManager", "Settings", "extract_links", "is_file_link",
]
