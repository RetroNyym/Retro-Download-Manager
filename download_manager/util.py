"""Yardimci fonksiyonlar, kategori tanimlari ve bicimlendiriciler."""

from __future__ import annotations

import mimetypes
import re
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

CATEGORIES = ("video", "audio", "programs", "archives", "documents", "other")

CATEGORY_LABELS = {
    "video": "Video",
    "audio": "Ses",
    "programs": "Programlar",
    "archives": "Arşivler",
    "documents": "Belgeler",
    "other": "Diğer",
}

CATEGORY_EXTENSIONS = {
    "video": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mpg",
              ".mpeg", ".m4v", ".3gp", ".ts", ".vob", ".ogv"},
    "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus",
              ".mid", ".amr", ".aiff"},
    "programs": {".exe", ".msi", ".apk", ".deb", ".rpm", ".dmg", ".pkg", ".msix",
                 ".appimage", ".jar", ".bat", ".com", ".scr"},
    "archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz",
                 ".iso", ".cab", ".arj", ".lz", ".zst", ".tar.gz", ".tar.bz2"},
    "documents": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                  ".txt", ".csv", ".rtf", ".epub", ".odt", ".ods", ".odp",
                  ".md", ".xlsxm", ".xlsm"},
}

DEFAULT_CATEGORY_FOLDERS = {
    "video": "Video",
    "audio": "Ses",
    "programs": "Programlar",
    "archives": "Arşivler",
    "documents": "Belgeler",
    "other": "Diğer",
}

PAGE_EXTENSIONS = {
    ".html", ".htm", ".php", ".php3", ".phtml", ".asp", ".aspx", ".jsp",
    ".cgi", ".xhtml", ".shtml", ".css", ".js", ".mjs", ".svg", ".xml",
    ".json", ".md", ".txt",
}


def detect_category(filename):
    if not filename:
        return "other"
    ext = Path(filename).suffix.lower()
    for cat in ("video", "audio", "programs", "archives", "documents"):
        if ext in CATEGORY_EXTENSIONS[cat]:
            return cat
    return "other"


def sanitize_filename(name, fallback="indirilen"):
    if not name:
        return fallback
    name = str(name).replace("\x00", "")
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"[\r\n\t]+", " ", name)
    name = re.sub(r"\s{2,}", " ", name).strip().strip(".")
    if not name:
        return fallback
    if len(name) > 150:
        stem, dot, ext = name.rpartition(".")
        if dot and len(ext) <= 12:
            keep = max(10, 150 - len(ext) - 1)
            name = stem[:keep].rstrip() + "." + ext
        else:
            name = name[:150]
    return name


def _header_value(headers, key):
    if headers is None:
        return None
    try:
        val = headers.get(key)
        if val is not None:
            return val
    except AttributeError:
        pass
    low = key.lower()
    try:
        items = headers.items()
    except AttributeError:
        return None
    for k, v in items:
        if str(k).lower() == low:
            return v
    return None


def filename_from_headers(url, headers):
    cd = _header_value(headers, "Content-Disposition")
    if cd:
        m = re.search(r"filename\*\s*=\s*([^']*)'[^']*'([^;]*)", str(cd), re.I)
        if m:
            charset, value = m.group(1).strip(), m.group(2).strip().strip('"')
            try:
                if charset and charset.lower() != "utf-8":
                    value = unquote(value, encoding=charset, errors="replace")
                else:
                    value = unquote(value)
            except Exception:
                value = unquote(value)
            if value:
                return sanitize_filename(value)
        m = re.search(r'filename\s*=\s*"([^"]+)"', str(cd), re.I)
        if m and m.group(1).strip():
            return sanitize_filename(unquote(m.group(1).strip()))
        m = re.search(r"filename\s*=\s*([^;]+)", str(cd), re.I)
        if m and m.group(1).strip():
            return sanitize_filename(unquote(m.group(1).strip().strip('"')))
    path = urlparse(url or "").path
    name = unquote(path.rsplit("/", 1)[-1]) if path else ""
    if name:
        ctype = _header_value(headers, "Content-Type")
        if "." not in name and ctype:
            ctype = str(ctype).split(";")[0].strip().lower()
            ext = mimetypes.guess_extension(ctype)
            if ext and ext not in (".html", ".htm"):
                name += ext
        return sanitize_filename(name)
    return None


def unique_path(path):
    path = Path(path)
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    index = 1
    while True:
        cand = path.with_name(f"{stem} ({index}){suffix}")
        if not cand.exists():
            return cand
        index += 1


def parse_header_lines(text):
    out = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key:
            out[key] = value
    return out


def looks_like_url(text):
    if not text:
        return False
    text = text.strip()
    if len(text) > 2048 or "\n" in text or " " in text:
        return False
    return bool(re.match(r"^(https?|ftp)://\S+$", text, re.I))


def format_bytes(value):
    if value is None or value < 0:
        return "?"
    size = float(value)
    unit = "B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0 or unit == "TB":
            break
        size /= 1024.0
    if unit == "B":
        return f"{int(size)} B"
    return f"{size:.1f} {unit}"


def format_speed(bytes_per_second):
    if bytes_per_second is None or bytes_per_second <= 0:
        return "-"
    return format_bytes(bytes_per_second) + "/sn"


def format_eta(seconds, size=-1, speed=0):
    if seconds is None or seconds < 0:
        if size is not None and size >= 0 and speed and speed > 0:
            seconds = size / speed
        else:
            return "--:--"
    if seconds < 0:
        return "--:--"
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_clock(seconds):
    if seconds is None or seconds < 0:
        return "--:--"
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:d}:{minutes:02d}:{secs:02d}"


def format_datetime(ts):
    if not ts:
        return ""
    if isinstance(ts, (int, float)):
        ts = time.localtime(ts)
        return time.strftime("%d.%m.%Y %H:%M:%S", ts)
    try:
        return ts.strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        return str(ts)
