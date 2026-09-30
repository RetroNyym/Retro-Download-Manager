"""Web sayfalarindan indirilebilir medya cikarma.

Bir baglanti sunucudan HTML olarak dondugunde (video sitesi, playlist,
indirme sayfasi) motor buraya duser:

1. Sayfa metnindeki dogrudan medya baglantilari aranir (og:video, <source>).
2. yt-dlp kuruluysa site cozumleyicisi olarak kullanilir (YouTube dahil
   binlerce site, playlist girisleri dahil).
   - Tek dosyada ses+video varsa dogrudan URL verilir: indirme motorumuz
     cok parcali olarak indirir.
   - Ses/video ayrilysa (DASH/HLS) indirme yt-dlp'ye devredilir; birlestirme
     icin ffmpeg kullanilir.
3. Bulunamazsa indirme acik bir hata ile durur; indirilmis bir HTML dosyasi
   "video tamamlandi" diye gosterilmez.
"""

from __future__ import annotations

import glob
import os
import re
import shutil
from pathlib import Path
from urllib.parse import urljoin, urlparse

MEDIA_EXTENSIONS = (
    ".mp4", ".m4v", ".mkv", ".webm", ".mov", ".flv", ".avi", ".ogv",
    ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac",
)
STREAM_EXTENSIONS = (".m3u8", ".mpd")

SUPPORTED_SITES = (
    ("YouTube", "youtube.com", "youtu.be"),
    ("Instagram", "instagram.com", "cdninstagram.com"),
    ("X (Twitter)", "twitter.com", "x.com", "t.co"),
    ("Facebook", "facebook.com", "fb.watch", "fb.com"),
    ("TikTok", "tiktok.com"),
    ("Vimeo", "vimeo.com"),
)


def site_name(url):
    """URL'in ait oldugu bilinen site adini dondurur (bilinmiyorsa None)."""
    host = (urlparse(str(url or "")).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    for name, *domains in SUPPORTED_SITES:
        for domain in domains:
            if host == domain or host.endswith("." + domain):
                return name
    return None

_OG_VIDEO = re.compile(
    r"<meta[^>]+(?:property|name)\s*=\s*[\"'](?:og:video(?::secure_url|:url)?|"
    r"twitter:player:stream)[\"'][^>]+content\s*=\s*[\"']([^\"']+)[\"']", re.I)
_OG_VIDEO_FLIP = re.compile(
    r"<meta[^>]+content\s*=\s*[\"']([^\"']+)[\"'][^>]+(?:property|name)\s*=\s*"
    r"[\"'](?:og:video(?::secure_url|:url)?|twitter:player:stream)[\"']", re.I)
_MEDIA_SRC = re.compile(
    r"<(?:video|audio|source|embed|iframe)[^>]+(?:src|data-src)\s*=\s*[\"']([^\"']+)[\"']",
    re.I)
_JSON_URL = re.compile(
    r"[\"'](?:contentUrl|file|src|url|playUrl)[\"']\s*:\s*[\"']([^\"']+)[\"']", re.I)
_DIRECT_MEDIA = re.compile(
    r"https?://[^\s\"'<>\\)]+?\.(?:mp4|m4v|mkv|webm|mov|flv|avi|ogv|mp3|m4a|aac|ogg|"
    r"opus|wav|flac)(?:\?[^\s\"'<>\\)]*)?", re.I)

_ytdlp_state = {"checked": False, "available": False}
_ffmpeg_state = {"checked": False, "path": None}


def ytdlp_available():
    if not _ytdlp_state["checked"]:
        _ytdlp_state["checked"] = True
        try:
            __import__("yt_dlp")
            _ytdlp_state["available"] = True
        except Exception:
            _ytdlp_state["available"] = False
    return _ytdlp_state["available"]


def find_ffmpeg():
    """ffmpeg yolunu bulur (sistem PATH, WinGet kurulumu veya ./tools)."""
    if _ffmpeg_state["checked"]:
        return _ffmpeg_state["path"]
    _ffmpeg_state["checked"] = True
    candidates = []
    which = shutil.which("ffmpeg")
    if which:
        candidates.append(which)
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        candidates.extend(glob.glob(os.path.join(
            local, "Microsoft", "WinGet", "Links", "ffmpeg.exe")))
        candidates.extend(glob.glob(os.path.join(
            local, "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*",
            "ffmpeg-*", "bin", "ffmpeg.exe")))
    here = Path(__file__).resolve().parent.parent
    candidates.extend(str(p) for p in (here / "tools").glob("ffmpeg*.exe"))
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            _ffmpeg_state["path"] = candidate
            return candidate
    return None


def has_ffmpeg():
    return find_ffmpeg() is not None


def is_local_url(url):
    host = (urlparse(url or "").hostname or "").lower()
    return host in ("localhost", "127.0.0.1", "::1", "0.0.0.0") or host.endswith(".local")


def is_stream_url(url):
    path = urlparse(url or "").path.lower()
    return path.endswith(STREAM_EXTENSIONS)


def sniff_media(html, base_url=""):
    """Sayfa metnindeki dogrudan medya baglantilarini toplar (ilk tercih once)."""
    found = []
    if not html:
        return found
    for pattern in (_OG_VIDEO, _OG_VIDEO_FLIP, _MEDIA_SRC, _JSON_URL, _DIRECT_MEDIA):
        for match in pattern.finditer(html):
            raw = match.group(1) if match.lastindex else match.group(0)
            candidate = (raw or "").strip()
            if not candidate or candidate.startswith(("data:", "javascript:")):
                continue
            absolute = urljoin(base_url, candidate)
            if not absolute.startswith(("http://", "https://")):
                continue
            if is_stream_url(absolute):
                continue
            if absolute not in found:
                found.append(absolute)
        if found:
            break
    return found


def _ydl_options(settings, playlist=True, headers=None):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "skip_download": True,
        "retries": 1,
        "fragment_retries": 2,
        "socket_timeout": 25,
        "playlistend": 200,
        "noplaylist": not playlist,
        "cachedir": False,
    }
    http_headers = dict(headers or {})
    ua = str(getattr(settings, "user_agent", "") or "")
    if ua and "User-Agent" not in http_headers:
        http_headers["User-Agent"] = ua
    if http_headers:
        opts["http_headers"] = http_headers
    proxy = str(getattr(settings, "proxy", "") or "").strip()
    if proxy:
        opts["proxy"] = proxy
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        opts["ffmpeg_location"] = os.path.dirname(ffmpeg)
    return opts


def _filename_of(info):
    title = str(info.get("title") or "").strip()
    ext = str(info.get("ext") or "").strip() or "mp4"
    if not title:
        return None
    return f"{title}.{ext}"


def _headers_of(info):
    return dict(info.get("http_headers") or {})


def _pick_progressive(info):
    """Ses+video iceren tek dosyali (ileri/DASH olmayan) formati secer."""
    best = None
    for fmt in info.get("formats") or []:
        if fmt.get("vcodec") in (None, "none"):
            continue
        if fmt.get("acodec") in (None, "none"):
            continue
        if not fmt.get("url") or is_stream_url(fmt.get("url")):
            continue
        protocol = str(fmt.get("protocol") or "")
        if protocol.startswith(("m3u8", "http_dash")):
            continue
        score = (fmt.get("height") or 0) * 1000 + (fmt.get("tbr") or 0)
        if best is None or score > best[0]:
            best = (score, fmt)
    return best[1] if best else None


def _task_from_info(info, fallback_url):
    progressive = _pick_progressive(info)
    if progressive:
        filename = _filename_of(info)
        if filename and info.get("ext"):
            filename = f"{Path(filename).stem}.{progressive.get('ext') or info['ext']}"
        return {"kind": "media", "url": progressive["url"], "filename": filename,
                "headers": dict(progressive.get("http_headers") or _headers_of(info))}
    single = info.get("url")
    if single and not info.get("requested_formats") and not is_stream_url(single):
        return {"kind": "media", "url": single, "filename": _filename_of(info),
                "headers": _headers_of(info)}
    page = info.get("webpage_url") or info.get("original_url") or fallback_url
    return {"kind": "external", "url": page, "filename": _filename_of(info),
            "headers": {}, "needs_ffmpeg": not has_ffmpeg()}


def ytdlp_extract(url, settings, playlist=True):
    """yt-dlp ile sayfayi cozer; tek medya veya playlist girisleri dondurur."""
    if is_local_url(url) or not ytdlp_available():
        return None
    try:
        import yt_dlp
    except Exception:
        return None
    try:
        with yt_dlp.YoutubeDL(_ydl_options(settings, playlist=playlist)) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        return None
    if not info:
        return None
    entries = list(info.get("entries") or [])
    if entries:
        tasks = []
        for entry in entries:
            if not entry:
                continue
            page = (entry.get("webpage_url") or entry.get("original_url")
                    or entry.get("url"))
            if not page or not str(page).startswith(("http://", "https://")):
                continue
            resolved = _task_from_info(entry, page)
            item = {
                "url": resolved.get("url") or page,
                "filename": resolved.get("filename") or _filename_of(entry),
                "headers": resolved.get("headers") or {},
            }
            if resolved["kind"] == "external":
                item["external"] = True
            tasks.append(item)
        if tasks:
            return {"kind": "playlist", "entries": tasks}
        return None
    return _task_from_info(info, url)


def resolve_page(url, html="", settings=None):
    """HTML sayfasi icin indirilebilir medya bilgisi uretir.

    Once sayfa metni taranir (hizli, yerel sunucularda da calisir), bulunamazsa
    yt-dlp site cozumleyicisi devreye girer.

    Donus degeri:
      {"kind": "media",    -> motor dogrudan cok parcali indirir
      {"kind": "external", -> indirme yt-dlp'ye devredilir (birlestirme icin ffmpeg)
      {"kind": "playlist", "entries": [...]}
      None -> medya bulunamadi
    """
    for candidate in sniff_media(html, url):
        return {"kind": "media", "url": candidate, "filename": None, "headers": {}}
    return ytdlp_extract(url, settings)


def _final_from_outtmpl(outtmpl, fallback=None):
    """outtmpl sablonundan birlestirilmis nihai dosyayi bulur."""
    base = outtmpl.split("%(")[0]
    parent = Path(base).parent
    prefix = Path(base).name
    if not parent.is_dir():
        return fallback
    best = None
    for entry in parent.iterdir():
        name = entry.name
        if not entry.is_file() or not name.startswith(prefix):
            continue
        if name.endswith((".part", ".ytdl", ".json")):
            continue
        if re.search(r"\.f\d+\.", name):
            continue
        if best is None or entry.stat().st_mtime > best.stat().st_mtime:
            best = entry
    if best:
        return str(best)
    if fallback and Path(fallback).exists():
        return fallback
    return None


def external_download(url, outtmpl, settings=None, hook=None, headers=None):
    """yt-dlp ile indirme yapar, biten dosyanin yolunu dondurur (bulunamazsa None)."""
    if not ytdlp_available():
        raise RuntimeError("yt-dlp kurulu değil: pip install yt-dlp")
    import yt_dlp

    opts = _ydl_options(settings, playlist=False, headers=headers)
    opts.update({
        "noplaylist": True,
        "skip_download": False,
        "outtmpl": {"default": outtmpl},
        "continuedl": True,
        "retries": max(5, int(getattr(settings, "retries", 3) or 3)),
        "extractor_retries": 3,
        "fragment_retries": 5,
    })
    final = {"path": None}

    def _wrapper(data):
        if data.get("status") == "finished" and data.get("filename"):
            final["path"] = data["filename"]
        if hook:
            hook(data)

    opts["progress_hooks"] = [_wrapper]
    if not has_ffmpeg():
        opts["format"] = "best[acodec!=none]/best"
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    return _final_from_outtmpl(outtmpl, final["path"])


def unavailable_reason():
    if not ytdlp_available():
        return ("Web sayfası algılandı ama medya bulunamadı. yt-dlp kurulu değil: "
                "\"pip install yt-dlp\" ile binlerce site desteği ekleyebilirsiniz.")
    return ("Web sayfası algılandı ancak indirilebilir medya bulunamadı. "
            "Bağlantıyı tarayıcıda açıp gerçek medya adresini (Site Grabber) kullanın.")
