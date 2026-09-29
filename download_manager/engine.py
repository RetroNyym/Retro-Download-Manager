"""Cok parcali HTTP indirme motoru (IDM tarzi segmentli indirme)."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from requests.adapters import HTTPAdapter

from .util import (
    detect_category,
    filename_from_headers,
    parse_header_lines,
    sanitize_filename,
    unique_path,
)

CHUNK = 64 * 1024

QUEUED = "queued"
SCHEDULED = "scheduled"
PROBING = "probing"
DOWNLOADING = "downloading"
PAUSED = "paused"
COMPLETED = "completed"
ERROR = "error"
CANCELED = "canceled"

RUNNING_STATES = (PROBING, DOWNLOADING)
STARTABLE_STATES = (QUEUED, SCHEDULED, PAUSED, ERROR)
TERMINAL_STATES = (COMPLETED, CANCELED)

STATE_LABELS = {
    QUEUED: "Kuyrukta",
    SCHEDULED: "Zamanlandı",
    PROBING: "Hazırlanıyor",
    DOWNLOADING: "İndiriliyor",
    PAUSED: "Duraklatıldı",
    COMPLETED: "Tamamlandı",
    ERROR: "Hata",
    CANCELED: "İptal",
}


class RateLimiter:
    def __init__(self, bytes_per_second=0):
        self._lock = threading.Lock()
        self._limit = float(bytes_per_second or 0)
        self._allowance = 0.0
        self._last = time.monotonic()

    @property
    def limit(self):
        return self._limit

    def set_limit(self, bytes_per_second):
        with self._lock:
            self._limit = float(bytes_per_second or 0)
            self._allowance = 0.0
            self._last = time.monotonic()

    def acquire(self, amount):
        with self._lock:
            if self._limit <= 0:
                return
            now = time.monotonic()
            elapsed = now - self._last
            self._last = now
            self._allowance += elapsed * self._limit
            if self._allowance > self._limit:
                self._allowance = self._limit
            if self._allowance >= amount:
                self._allowance -= amount
                return
            deficit = amount - self._allowance
            self._allowance = 0.0
            delay = deficit / self._limit
        time.sleep(delay)


class SpeedMeter:
    def __init__(self, window=4.0, step=0.25):
        self.window = window
        self.step = step
        self.total = 0
        self._samples = deque()
        self._lock = threading.Lock()
        self._last_sample = 0.0

    def add(self, amount):
        now = time.monotonic()
        with self._lock:
            self.total += amount
            if now - self._last_sample >= self.step:
                self._last_sample = now
                self._samples.append((now, self.total))
                self._trim(now)

    def reset(self):
        with self._lock:
            self.total = 0
            self._samples.clear()
            self._last_sample = 0.0

    def _trim(self, now):
        while len(self._samples) > 2 and self._samples[1][0] < now - self.window:
            self._samples.popleft()

    def value(self):
        now = time.monotonic()
        with self._lock:
            self._trim(now)
            if len(self._samples) < 2:
                return 0.0
            if now - self._samples[-1][0] > self.window:
                return 0.0
            t0, b0 = self._samples[0]
            t1, b1 = self._samples[-1]
            if t1 <= t0:
                return 0.0
            return max(0.0, (b1 - b0) / (t1 - t0))


class _FtpAbort(Exception):
    pass


class Segment:
    __slots__ = ("index", "start", "end", "pos", "finished")

    def __init__(self, index, start, end, pos, finished=False):
        self.index = index
        self.start = start
        self.end = end
        self.pos = pos
        self.finished = finished

    @property
    def total(self):
        if self.end < 0:
            return -1
        return self.end - self.start + 1

    @property
    def done(self):
        if self.end < 0:
            return self.pos - self.start
        return min(self.pos, self.end + 1) - self.start

    @property
    def is_done(self):
        if self.finished:
            return True
        if self.end < 0:
            return False
        return self.pos > self.end

    @property
    def fraction(self):
        if self.is_done:
            return 1.0
        total = self.total
        if total <= 0:
            return 0.0
        return max(0.0, min(1.0, self.done / total))


class DownloadTask:
    def __init__(self, url, manager, category=None, subdir="", filename=None,
                 referer=None, user_agent=None, cookies=None, extra_headers=None,
                 segments=None, speed_limit=0, scheduled_at=None, urls=None,
                 task_id=None):
        self.id = task_id or uuid.uuid4().hex[:12]
        self.url = url
        self._is_ftp = str(url).lower().startswith(("ftp://", "ftps://"))
        self.urls = list(urls or []) or [url]
        if url not in self.urls:
            self.urls.insert(0, url)
        self.mgr = manager
        self.settings = manager.settings
        self.category = category or "other"
        self.auto_category = category is None
        self.subdir = subdir or ""
        self.user_filename = filename
        self.filename = filename
        self.referer = referer or ""
        self.user_agent = user_agent or ""
        self.cookies = cookies or ""
        self.extra_headers = dict(extra_headers or {})
        self.segments_count = int(segments or 0)
        self.speed_limit = int(speed_limit or 0)
        self.scheduled_at = scheduled_at
        self.created_at = time.time()
        self.started_at = None
        self.finished_at = None

        self.state = QUEUED
        self.error = None
        self.dest_dir = None
        self.final_path = None
        self.part_path = None
        self.meta_path = None

        self._size = -1
        self._downloaded = 0
        self._ranges = False
        self._etag = ""
        self._final_url = url
        self._probe_name = None
        self._probed = False
        self._segments = []
        self._lock = threading.RLock()
        self._bytes_lock = threading.Lock()
        self._speed = SpeedMeter()
        self._own_limiter = None
        self._pause_evt = threading.Event()
        self._cancel_evt = threading.Event()
        self._abort_evt = threading.Event()
        self._idle_evt = threading.Event()
        self._idle_evt.set()
        self._saver_evt = threading.Event()
        self._saver_thread = None
        self._run_thread = None
        self._session = None
        self._threads = []
        self._fatal = None
        self._force_single = False
        self._mirror_index = 0
        self._delete_pending = False

    @property
    def size(self):
        return self._size

    @property
    def downloaded(self):
        with self._bytes_lock:
            return self._downloaded

    @property
    def speed(self):
        return self._speed.value()

    @property
    def segments(self):
        return list(self._segments)

    @property
    def is_active(self):
        return self.state in RUNNING_STATES

    @property
    def is_busy(self):
        if self.state in RUNNING_STATES:
            return True
        thread = self._run_thread
        return thread is not None and thread.is_alive()

    @property
    def percent(self):
        if self._size <= 0:
            return -1.0
        return max(0.0, min(100.0, self.downloaded * 100.0 / self._size))

    @property
    def eta(self):
        speed = self.speed
        if speed <= 0:
            return None
        if self._size <= 0:
            return None
        return max(0.0, (self._size - self.downloaded) / speed)

    @property
    def destination(self):
        if self.final_path:
            return str(self.final_path)
        if self.dest_dir:
            name = self.filename or self.user_filename or ""
            return str(Path(self.dest_dir) / name)
        folder = self.settings.category_folders.get(self.category, "Diğer")
        return str(Path(self.settings.download_dir) / folder / self.subdir)

    @property
    def path(self):
        if self.state == COMPLETED and self.final_path:
            return str(self.final_path)
        if self.part_path:
            return str(self.part_path)
        return self.destination

    def snapshot(self):
        seg_states = [(s.done, s.total, s.fraction) for s in self._segments]
        return {
            "id": self.id,
            "filename": self.filename or self.user_filename or self.url,
            "url": self.url,
            "category": self.category,
            "subdir": self.subdir,
            "state": self.state,
            "state_label": STATE_LABELS.get(self.state, self.state),
            "size": self._size,
            "downloaded": self.downloaded,
            "percent": self.percent,
            "speed": self.speed,
            "eta": self.eta,
            "error": self.error,
            "segments": seg_states,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "destination": self.destination,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    def set_speed_limit(self, kbps):
        self.speed_limit = int(kbps or 0)
        if self.speed_limit > 0:
            self._own_limiter = RateLimiter(self.speed_limit * 1024)
        else:
            self._own_limiter = None

    def _limiter(self):
        if self.speed_limit > 0:
            if self._own_limiter is None:
                self._own_limiter = RateLimiter(self.speed_limit * 1024)
            return self._own_limiter
        return self.mgr.limiter

    def _build_headers(self):
        st = self.settings
        headers = {"Accept": "*/*", "Accept-Encoding": "identity",
                   "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"}
        ua = self.user_agent or st.user_agent
        if ua:
            headers["User-Agent"] = ua
        referer = self.referer or st.referer
        if referer:
            headers["Referer"] = referer
        cookies = self.cookies or st.cookies
        if cookies:
            headers["Cookie"] = cookies
        headers.update(parse_header_lines(st.extra_headers))
        headers.update(self.extra_headers)
        return headers

    def _open_session(self):
        st = self.settings
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=32, pool_maxsize=32)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        proxy = (st.proxy or "").strip()
        if proxy:
            session.proxies.update({"http": proxy, "https": proxy})
        session.headers.update(self._build_headers())
        return session

    def _timeout(self):
        st = self.settings
        return (max(5, int(st.timeout_connect)), max(10, int(st.timeout_read)))

    def _urls_for_attempt(self, attempt):
        if not self.urls:
            return [self.url]
        idx = attempt % len(self.urls)
        return [self.urls[idx]] + [u for i, u in enumerate(self.urls) if i != idx]

    def _probe(self):
        if self._is_ftp:
            return self._probe_ftp()
        errors = []
        for attempt in range(2):
            for url in self._urls_for_attempt(attempt):
                if self._cancel_evt.is_set():
                    return False
                headers = dict(self._build_headers())
                headers["Range"] = "bytes=0-0"
                try:
                    response = self._session.get(url, headers=headers, stream=True,
                                                 timeout=self._timeout(),
                                                 allow_redirects=True)
                except Exception as exc:
                    errors.append(f"{url}: {exc}")
                    continue
                try:
                    if response.status_code >= 400:
                        errors.append(f"{url}: HTTP {response.status_code}")
                        continue
                    self._final_url = response.url or url
                    hdrs = response.headers
                    if response.status_code == 206:
                        match = re.search(r"/(\d+)\s*$", str(hdrs.get("Content-Range", "")))
                        if match and match.group(1) != "0":
                            self._size = int(match.group(1))
                        self._ranges = True
                    else:
                        self._ranges = False
                        length = hdrs.get("Content-Length")
                        self._size = int(length) if str(length).isdigit() else -1
                    self._etag = str(hdrs.get("ETag") or hdrs.get("Last-Modified") or "")
                    name = filename_from_headers(self._final_url, hdrs)
                    if name:
                        self._probe_name = name
                    self._probed = True
                    self.error = None
                    return True
                finally:
                    response.close()
        raise RuntimeError("Sunucuya ulaşılamadı: " + ("; ".join(errors) or self.url))

    def _ftp_connect(self, url):
        from ftplib import FTP, FTP_TLS

        parsed = urlparse(url)
        scheme = (parsed.scheme or "ftp").lower()
        host = parsed.hostname
        if not host:
            raise RuntimeError(f"Geçersiz FTP adresi: {url}")
        port = parsed.port or (990 if scheme == "ftps" else 21)
        path = unquote(parsed.path or "/")
        ftp = FTP_TLS() if scheme == "ftps" else FTP()
        ftp.connect(host, port, timeout=max(5, int(self.settings.timeout_connect)))
        user = self.settings.ftp_user or "anonymous"
        password = self.settings.ftp_password or "anonymous@"
        ftp.login(user, password)
        if isinstance(ftp, FTP_TLS):
            ftp.prot_p()
        return ftp, path

    def _ftp_probe_url(self, attempt=0):
        return self._urls_for_attempt(attempt)[0]

    def _probe_ftp(self):
        ftp = None
        try:
            ftp, path = self._ftp_connect(self._ftp_probe_url())
            self._final_url = self.url
            try:
                ftp.voidcmd("TYPE I")
            except Exception:
                pass
            try:
                size = ftp.size(path)
            except Exception:
                size = None
            if not size:
                size = self._ftp_size_from_list(ftp, path)
            self._size = int(size) if size else -1
            self._ranges = True
            self._etag = ""
            name = unquote(path.rsplit("/", 1)[-1]) if path else ""
            if name:
                self._probe_name = sanitize_filename(name)
            self._probed = True
            self.error = None
            return True
        except Exception as exc:
            raise RuntimeError(f"FTP hatası: {exc}")
        finally:
            if ftp is not None:
                try:
                    ftp.close()
                except Exception:
                    pass

    def _ftp_size_from_list(self, ftp, path):
        name = unquote(path.rsplit("/", 1)[-1])
        directory = unquote(path.rsplit("/", 1)[0]) or "/"
        try:
            for facts, filename in ftp.mlsd(directory, facts=["size"]):
                if filename == name and facts.get("size"):
                    return int(facts["size"])
        except Exception:
            pass
        return None

    def _ftp_worker(self, segment):
        from ftplib import Error as FtpError, error_perm

        limiter = self._limiter()
        attempt = 0
        while not self._should_stop():
            url = self._current_url(attempt)
            ftp = None
            try:
                ftp, path = self._ftp_connect(url)
                if segment.end >= 0 and segment.pos > segment.end:
                    segment.finished = True
                    return
                remaining = None if segment.end < 0 else segment.end - segment.pos + 1
                mode = "r+b" if self.part_path.exists() else "wb"
                done = {"finished": False, "stopped": False, "invalid": False}

                def writer(chunk):
                    nonlocal remaining
                    if self._should_stop():
                        done["stopped"] = True
                        raise _FtpAbort()
                    if remaining is not None:
                        if remaining <= 0:
                            raise _FtpAbort()
                        if len(chunk) > remaining:
                            chunk = chunk[:remaining]
                    handle.write(chunk)
                    segment.pos += len(chunk)
                    self._add_bytes(len(chunk))
                    limiter.acquire(len(chunk))
                    if remaining is not None:
                        remaining -= len(chunk)
                        if remaining <= 0:
                            done["finished"] = True
                            raise _FtpAbort()

                with open(self.part_path, mode, buffering=0) as handle:
                    if segment.end >= 0 or segment.pos > 0:
                        handle.seek(segment.pos)
                    rest = segment.pos if segment.pos > 0 else None
                    try:
                        ftp.retrbinary(f"RETR {path}", writer, blocksize=CHUNK,
                                       rest=rest)
                    except _FtpAbort:
                        pass
                    except error_perm as exc:
                        message = str(exc)
                        if rest is not None and message.startswith("550"):
                            if not self._force_single:
                                self._force_single = True
                                self._abort_evt.set()
                                self.mgr.log(
                                    f"{self.filename}: sunucu konum (REST) desteklemiyor, "
                                    "tek bağlantıya geçiliyor", "warning")
                            return
                        raise
                if done["stopped"] or self._should_stop():
                    return
                if done["finished"] or segment.end < 0:
                    if segment.end >= 0:
                        segment.pos = min(segment.pos, segment.end + 1)
                    segment.finished = True
                    return
                if segment.pos > segment.end >= 0:
                    segment.pos = segment.end + 1
                    segment.finished = True
                    return
                if segment.is_done:
                    return
                raise IOError("FTP akışı beklenmedik şekilde sonlandı")
            except Exception as exc:
                if isinstance(exc, FtpError) and "550" in str(exc) and attempt == 0:
                    if segment.pos > segment.start and self._size > 0:
                        self._fail(f"FTP dosya alınamadı: {exc}")
                        return
                attempt += 1
                if attempt > int(self.settings.retries):
                    self._fail(f"FTP parça {segment.index} başarısız: {exc}")
                    return
                self.mgr.log(f"FTP parça {segment.index} yeniden deneniyor: {exc}",
                             "warning")
                time.sleep(min(20, 2 ** min(attempt, 5)) + 0.3)
            finally:
                if ftp is not None:
                    try:
                        ftp.close()
                    except Exception:
                        pass

    def _load_meta(self):
        if not self.meta_path or not self.meta_path.exists():
            return None
        try:
            data = json.loads(self.meta_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if data.get("url") != self.url and self.url not in (data.get("urls") or []):
            return None
        if self._size > 0 and data.get("size") not in (None, -1) and data.get("size") != self._size:
            self.mgr.log(f"Boyut değiştiği için yeniden başlıyor: {self.filename}", "warning")
            try:
                self.meta_path.unlink()
            except OSError:
                pass
            return None
        meta_etag = data.get("etag") or ""
        if meta_etag and self._etag and meta_etag != self._etag:
            self.mgr.log(f"Sunucu içeriği değiştiği için yeniden başlıyor: {self.filename}", "warning")
            try:
                self.meta_path.unlink()
            except OSError:
                pass
            return None
        return data

    def _save_meta(self):
        if self.state == COMPLETED or not self.meta_path:
            return
        if self.state == CANCELED:
            return
        data = {
            "url": self.url,
            "urls": self.urls,
            "filename": self.filename,
            "dest_dir": str(self.dest_dir) if self.dest_dir else "",
            "size": self._size,
            "etag": self._etag,
            "final_url": self._final_url,
            "category": self.category,
            "subdir": self.subdir,
            "referer": self.referer,
            "user_agent": self.user_agent,
            "cookies": self.cookies,
            "extra_headers": self.extra_headers,
            "downloaded": self.downloaded,
            "segments": [{"index": s.index, "start": s.start, "end": s.end,
                          "pos": s.pos, "finished": s.finished} for s in self._segments],
        }
        try:
            tmp = Path(str(self.meta_path) + ".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, self.meta_path)
        except OSError:
            pass

    def _delete_temp(self):
        for path in (self.part_path, self.meta_path):
            if path:
                try:
                    Path(path).unlink()
                except OSError:
                    pass

    def _prepare_target(self, meta=None):
        st = self.settings
        folder = st.category_folders.get(self.category, "Diğer")
        dest = Path(st.download_dir).expanduser() / folder
        if self.subdir:
            dest = dest / self.subdir
        try:
            dest.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(f"Klasör oluşturulamadı ({dest}): {exc}")
        name = self.user_filename or (meta or {}).get("filename") or self._probe_name
        if not name:
            name = "indirilen"
        name = sanitize_filename(name)
        self.dest_dir = dest
        self.filename = name
        self.part_path = dest / (name + ".part")
        self.meta_path = dest / (name + ".part.json")
        taken = self.mgr.is_part_taken(self.part_path, self)
        if taken:
            alt = sanitize_filename(name)
            counter = 1
            while True:
                candidate = f"{alt} ({counter})"
                cand_path = dest / (candidate + ".part")
                if not self.mgr.is_part_taken(cand_path, self) and not cand_path.exists():
                    name = candidate
                    break
                counter += 1
                if counter > 200:
                    break
            self.filename = name
            self.part_path = dest / (name + ".part")
            self.meta_path = dest / (name + ".part.json")
        self.final_path = dest / name

    def _plan(self, meta=None):
        adopted = False
        if meta and meta.get("segments") and self._ranges:
            segs = []
            for item in meta["segments"]:
                segs.append(Segment(int(item["index"]), int(item["start"]), int(item["end"]),
                                    int(item["pos"]), bool(item.get("finished"))))
            if segs:
                self._segments = segs
                adopted = True
        if not adopted:
            count = self._segment_count()
            if self._size > 0 and self._ranges and count > 1:
                self._segments = self._split(self._size, count)
            elif self._size > 0:
                self._segments = [Segment(0, 0, self._size - 1, 0)]
            else:
                self._segments = [Segment(0, 0, -1, 0)]
        with self._bytes_lock:
            self._downloaded = sum(s.done for s in self._segments)
        self._speed.reset()

    def _segment_count(self):
        count = self.segments_count or int(self.settings.segments or 8)
        count = max(1, min(int(count), 32))
        if self._size > 0:
            if self._size < 512 * 1024:
                count = 1
            elif self._size < 5 * 1024 * 1024:
                count = min(count, 4)
            max_by_size = max(1, self._size // (64 * 1024))
            count = min(count, max_by_size)
        return count

    @staticmethod
    def _split(size, count):
        base = size // count
        segments = []
        start = 0
        for index in range(count):
            end = size - 1 if index == count - 1 else start + base - 1
            segments.append(Segment(index, start, end, start))
            start = end + 1
        return segments

    def _reset_to_single(self):
        if self._size > 0:
            self._segments = [Segment(0, 0, self._size - 1, 0)]
        else:
            self._segments = [Segment(0, 0, -1, 0)]
        with self._bytes_lock:
            self._downloaded = 0
        self._speed.reset()

    def _ensure_part_file(self):
        part = self.part_path
        fresh = self.downloaded <= 0
        try:
            if self._size > 0:
                current = part.stat().st_size if part.exists() else -1
                if current != self._size:
                    with open(part, "wb") as handle:
                        handle.truncate(self._size)
            elif fresh or not part.exists():
                with open(part, "wb"):
                    pass
        except OSError as exc:
            raise RuntimeError(f"Geçici dosya oluşturulamadı ({part}): {exc}")

    def _should_stop(self):
        return (self._pause_evt.is_set() or self._cancel_evt.is_set()
                or self._abort_evt.is_set())

    def _add_bytes(self, amount):
        with self._bytes_lock:
            self._downloaded += amount
        self._speed.add(amount)

    def _current_url(self, attempt):
        urls = self._urls_for_attempt(attempt)
        return urls[0]

    def _worker(self, segment):
        limiter = self._limiter()
        attempt = 0
        while not self._should_stop():
            url = self._current_url(attempt)
            headers = {}
            if segment.end >= 0:
                if segment.pos > segment.end:
                    segment.finished = True
                    return
                headers["Range"] = f"bytes={segment.pos}-{segment.end}"
            elif self._ranges and segment.pos > 0:
                headers["Range"] = f"bytes={segment.pos}-"
            try:
                response = self._session.get(url, headers=headers, stream=True,
                                             timeout=self._timeout())
            except Exception as exc:
                attempt += 1
                if attempt > int(self.settings.retries):
                    self._fail(f"Bağlantı hatası ({segment.index}. parça): {exc}")
                    return
                self.mgr.log(f"Yeniden deneniyor ({segment.index}. parça): {exc}", "warning")
                time.sleep(min(15, 1.0 * attempt) + 0.2)
                continue
            try:
                status = response.status_code
                if status == 416:
                    if segment.end >= 0:
                        segment.pos = segment.end + 1
                        segment.finished = True
                        return
                    response.close()
                    attempt += 1
                    continue
                if status in (408, 429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"HTTP {status}", response=response)
                if status >= 400:
                    self._fail(f"HTTP {status} — {url}")
                    return
                if segment.end >= 0 and segment.pos > segment.start and status == 200:
                    if not self._force_single:
                        self._force_single = True
                        self._abort_evt.set()
                        self.mgr.log("Sunucu aralık isteğini reddetti, tek bağlantıya geçiliyor",
                                     "warning")
                    return
                mode = "r+b" if self.part_path.exists() else "wb"
                written = 0
                with open(self.part_path, mode, buffering=0) as handle:
                    if segment.end >= 0 or segment.pos > 0:
                        handle.seek(segment.pos)
                    for chunk in response.iter_content(CHUNK):
                        if not chunk:
                            continue
                        if self._should_stop():
                            break
                        handle.write(chunk)
                        segment.pos += len(chunk)
                        written += len(chunk)
                        self._add_bytes(len(chunk))
                        limiter.acquire(len(chunk))
                        if segment.end >= 0 and segment.pos > segment.end:
                            break
                if segment.end >= 0 and segment.pos > segment.end:
                    segment.pos = segment.end + 1
                done_by_stream = segment.end < 0
                stopped = self._should_stop()
                if segment.end >= 0:
                    if segment.pos > segment.end:
                        segment.finished = True
                        return
                elif done_by_stream and not stopped:
                    segment.finished = True
                    return
                if stopped:
                    return
                if written == 0:
                    raise IOError("Veri akışı beklenmedik şekilde sonlandı")
            except Exception as exc:
                if isinstance(exc, requests.HTTPError) and exc.response is not None:
                    code = exc.response.status_code
                    if code in (404, 410, 403, 401, 400):
                        self._fail(f"HTTP {code} — dosya alınamadı")
                        return
                attempt += 1
                if attempt > int(self.settings.retries):
                    self._fail(f"Parça {segment.index} başarısız: {exc}")
                    return
                self.mgr.log(f"Parça {segment.index} yeniden deneniyor: {exc}", "warning")
                time.sleep(min(20, 2 ** min(attempt, 5)) + 0.3)
            finally:
                try:
                    response.close()
                except Exception:
                    pass

    def _fail(self, message):
        self._fatal = message
        self._abort_evt.set()

    def _start_saver(self):
        self._saver_evt.clear()
        self._saver_thread = threading.Thread(target=self._saver_loop, daemon=True)
        self._saver_thread.start()

    def _saver_loop(self):
        while not self._saver_evt.wait(2.0):
            self._save_meta()

    def _stop_saver(self):
        self._saver_evt.set()
        thread = self._saver_thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=3.0)
        self._saver_thread = None

    def _spawn_workers(self):
        self._threads = []
        self._abort_evt.clear()
        worker = self._ftp_worker if self._is_ftp else self._worker
        for segment in self._segments:
            if segment.is_done:
                continue
            thread = threading.Thread(target=worker, args=(segment,),
                                      daemon=True)
            self._threads.append(thread)
        for thread in self._threads:
            thread.start()
        for thread in self._threads:
            thread.join()

    def _verify_complete(self):
        if not self._segments:
            return False
        for segment in self._segments:
            if not segment.is_done:
                if segment.end < 0:
                    continue
                return False
        if self._size > 0 and self.part_path.exists():
            actual = self.part_path.stat().st_size
            if actual != self._size:
                return False
        return any(s.is_done for s in self._segments)

    def _finalize(self):
        final = unique_path(self.dest_dir / self.filename)
        os.replace(self.part_path, final)
        self.final_path = final
        self.filename = final.name
        self.dest_dir = final.parent
        try:
            if self.meta_path and self.meta_path.exists():
                self.meta_path.unlink()
        except OSError:
            pass
        self.finished_at = time.time()

    def _run(self):
        self._idle_evt.clear()
        self._fatal = None
        self._force_single = False
        session = None
        try:
            if not self._is_ftp:
                session = self._open_session()
                self._session = session
            self.state = PROBING
            self.error = None
            if self.started_at is None:
                self.started_at = time.time()
            if not self._probe():
                return
            if self._cancel_evt.is_set():
                return
            if self._pause_evt.is_set():
                self.state = PAUSED
                return
            if self.auto_category and self.filename:
                self.category = detect_category(self.filename)
            elif self.auto_category and self._probe_name:
                self.category = detect_category(self._probe_name)
            meta = self._load_meta()
            self._prepare_target(meta)
            self._plan(meta)
            self._ensure_part_file()
            self.state = DOWNLOADING
            self._start_saver()
            single_mode = len(self._segments) <= 1
            while True:
                self._spawn_workers()
                if self._cancel_evt.is_set() or self._pause_evt.is_set() or self._fatal:
                    break
                if self._force_single and not single_mode:
                    single_mode = True
                    self._force_single = False
                    self.mgr.log(f"{self.filename}: tek bağlantı moduna geçiliyor", "info")
                    self._reset_to_single()
                    continue
                break
            self._decide_state()
        except Exception as exc:
            self.error = str(exc)
            self.state = ERROR
            self.mgr.log(f"Hata ({self.filename}): {exc}", "error")
        finally:
            self._stop_saver()
            if session is not None:
                try:
                    session.close()
                except Exception:
                    pass
            self._session = None
            if self.state == CANCELED and self._delete_pending:
                self._delete_temp()
            elif self.state not in TERMINAL_STATES:
                self._save_meta()
            self._idle_evt.set()
            self.mgr.task_finished(self)

    def _decide_state(self):
        if self._cancel_evt.is_set():
            self.state = CANCELED
            return
        if self._pause_evt.is_set():
            self.state = PAUSED
            return
        if self._fatal:
            self.error = self._fatal
            self.state = ERROR
            self.mgr.log(f"Hata ({self.filename}): {self._fatal}", "error")
            return
        if self._verify_complete():
            try:
                self._finalize()
                self.state = COMPLETED
                self.error = None
            except Exception as exc:
                self.error = str(exc)
                self.state = ERROR
                self.mgr.log(f"Tamamlanamadı ({self.filename}): {exc}", "error")
            return
        self.state = PAUSED

    def _wait_idle(self, timeout=60.0):
        return self._idle_evt.wait(timeout)

    def start(self):
        with self._lock:
            if self.state in RUNNING_STATES:
                return False
            if self.state == COMPLETED:
                return False
            if self._run_thread and self._run_thread.is_alive():
                return False
            self._pause_evt.clear()
            self._cancel_evt.clear()
            self._abort_evt.clear()
            self._delete_pending = False
            self.error = None
            self.state = QUEUED
            self._run_thread = threading.Thread(target=self._run, daemon=True)
            self._run_thread.start()
            return True

    resume = start

    def pause(self):
        with self._lock:
            if self.state in (QUEUED, SCHEDULED):
                self._pause_evt.set()
                self.state = PAUSED
                self.mgr.log(f"Duraklatıldı: {self.filename or self.url}", "info")
                return True
            if self.state not in RUNNING_STATES:
                return False
            self._pause_evt.set()
            self.state = PAUSED
            self.mgr.log(f"Duraklatıldı: {self.filename}", "info")
            return True

    def cancel(self, delete_files=True):
        with self._lock:
            running = self.state in RUNNING_STATES
            self._delete_pending = bool(delete_files)
            self._cancel_evt.set()
            self._pause_evt.set()
            self._abort_evt.set()
            self.state = CANCELED
            if not running:
                if delete_files:
                    self._delete_temp()
                self.mgr.task_finished(self)
                return True
            self.mgr.log(f"İptal edildi: {self.filename}", "warning")
            return True

    def stop(self, delete_files=False):
        return self.cancel(delete_files=delete_files)

    def _hard_reset(self):
        self._probed = False
        self._size = -1
        self._ranges = False
        self._segments = []
        self._downloaded = 0
        self._speed.reset()
        self.error = None
        self.finished_at = None
        self._probe_name = None
        self._force_single = False
        self._mirror_index = 0
        self._pause_evt.clear()
        self._cancel_evt.clear()
        self._abort_evt.clear()
        self._delete_pending = False

    def restart(self):
        threading.Thread(target=self._restart_async, daemon=True).start()

    def _restart_async(self):
        if self.state in RUNNING_STATES:
            self._pause_evt.set()
            self._wait_idle(60.0)
        self._delete_temp()
        self._hard_reset()
        self.state = QUEUED
        self.mgr.log(f"Yeniden başlatılıyor: {self.url}", "info")
        self.start()

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "urls": self.urls,
            "category": None if self.auto_category else self.category,
            "subdir": self.subdir,
            "filename": self.user_filename,
            "referer": self.referer,
            "user_agent": self.user_agent,
            "cookies": self.cookies,
            "extra_headers": self.extra_headers,
            "segments": self.segments_count,
            "speed_limit": self.speed_limit,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "state": self.state,
        }

    @classmethod
    def from_dict(cls, data, manager):
        scheduled = data.get("scheduled_at")
        scheduled_at = None
        if scheduled:
            try:
                scheduled_at = datetime.fromisoformat(scheduled)
            except Exception:
                scheduled_at = None
        task = cls(
            data.get("url") or "",
            manager,
            category=data.get("category"),
            subdir=data.get("subdir") or "",
            filename=data.get("filename"),
            referer=data.get("referer"),
            user_agent=data.get("user_agent"),
            cookies=data.get("cookies"),
            extra_headers=data.get("extra_headers"),
            segments=data.get("segments"),
            speed_limit=data.get("speed_limit") or 0,
            scheduled_at=scheduled_at,
            urls=data.get("urls"),
            task_id=data.get("id"),
        )
        state = data.get("state") or QUEUED
        if state in RUNNING_STATES:
            task.state = QUEUED
        elif state in (QUEUED, SCHEDULED, PAUSED, ERROR):
            task.state = state
        return task
