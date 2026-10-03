# Submission Texts — English

Copy-paste texts for international portals (SourceForge, FossHub, MajorGeeks,
Softpedia, FileHippo, itch.io, UpdateStar, AlternativeTo ...).
Turkish texts: `metinler-tr.md`.

> **Contact e-mail:** currently `216476870+RetroNyym@users.noreply.github.com`
> (GitHub noreply, forwarded to the address on the account). Replace it everywhere
> in this file once a dedicated address exists.

---

## 1. Standard fields (same everywhere)

| Field | Value |
| --- | --- |
| Software name | Retro+ Download Manager |
| Version | 1.0.0 |
| License | MIT (free, open source) |
| Price | Free — ad-free, no trial period |
| Operating systems | Windows 10/11, Linux, macOS |
| Requirements | Python 3.11+ and `requests`; optional `yt-dlp` + `ffmpeg` for video/playlists |
| Category | Internet > Download Managers (fallback: System Utilities) |
| Homepage | https://retro-download-manager.netlify.app |
| Source code | https://github.com/RetroNyym/Retro-Download-Manager |
| Download (primary) | https://retro-download-manager.netlify.app/download/Retro-Download-Manager-v1.0.0.zip |
| Download (mirror) | https://github.com/RetroNyym/Retro-Download-Manager/releases/download/v1.0.0/Retro-Download-Manager-v1.0.0.zip |
| File size | 266 KB (ZIP) |
| SHA-256 | `73b50af2d18455eb4ca0d394b36138d66e5a8c83c34315b3867f80a05982366b` |
| Contact | `216476870+RetroNyym@users.noreply.github.com` |
| Screenshots | 4 PNG files in `docs/screenshots/` |
| Twitter/social | optional |
| Keywords | download manager, segmented download, resume, queue, open source |

---

## 2. Short descriptions

**≤100 characters:**

```
Fast multi-segment download manager with pause/resume, queue, scheduler and playlists
```

**≤160 characters:**

```
Retro+ Download Manager: up to 32 parallel connections, pause/resume, queue, scheduler,
auto categories, page and playlist resolution. Free, open source (MIT).
```

**≤250 characters:**

```
Retro+ Download Manager is a free (MIT), open-source download manager with up to 32
parallel segments, pause/resume from any point, a download queue and scheduler, automatic
file categories, a site grabber, web page and playlist resolution, FTP support and a
client-side speed limit. Runs on Windows, Linux and macOS. Turkish interface.
```

---

## 3. Long description (for portal listings)

```
Retro+ Download Manager is a free, open-source (MIT) download manager written in Python
with a native Tkinter interface. No installer, no ads, no trial period — the only runtime
dependency is the "requests" package.

Features:
- Segmented downloading: up to 32 parallel connections using HTTP Range, with automatic
  fallback to a single connection when the server does not support it
- Pause / resume / cancel at any point; progress is written to disk, so downloads survive
  application restarts
- Download queue with a concurrency limit and hourly/daily scheduled downloads
- Automatic categories (Video, Music, Archives, Programs, Documents) with folder routing
- Web page resolution: finds media addresses through og:video, <source> and JSON-LD tags
- Playlist support: YouTube and similar lists expand from one job to all videos; separate
  audio + video (DASH) streams are merged into a single file with yt-dlp and ffmpeg
- Quick site buttons: YouTube, Instagram, X (Twitter), Facebook, TikTok, Vimeo
- Browser bridge on 127.0.0.1:8877 plus clipboard monitoring: paste a link and it is
  queued automatically
- Site Grabber: crawl a page and queue every media link it finds
- FTP/FTPS, mirror URLs, client-side speed limit, cookie/header support, voice
  notifications
- Usable as a Python library (DownloadManager class) without the GUI

Requirements: Python 3.11 or newer on Windows 10/11, Linux or macOS. yt-dlp and ffmpeg
are optional and only needed for video/playlist downloads.

Fully tested: 165 automated checks and a clean pyflakes run. Source code is published on
GitHub for inspection.
```

---

## 4. Bullet feature list (short fields)

- Up to 32 parallel download segments (HTTP Range)
- Pause / resume / cancel from any point — survives restarts
- Download queue + hourly/daily scheduling
- Automatic categories with folder routing
- Web page and playlist link resolution (yt-dlp + ffmpeg)
- Quick site buttons: YouTube, Instagram, X, Facebook, TikTok, Vimeo
- Site Grabber: crawl a page and queue all media links
- Browser bridge + clipboard monitoring grabs links automatically
- FTP/FTPS, mirror URLs, speed limit, cookies/headers, voice notifications
- Turkish UI; MIT licensed, free, ad-free

---

## 5. System requirements (short field)

```
Python 3.11+, Windows 10/11 · Linux · macOS
Extra package: requests (~2 MB installed)
Optional: yt-dlp + ffmpeg (video and playlists)
Display: 1024x640 or higher
```

---

## 6. Screenshots

| File | Shows | Use |
| --- | --- | --- |
| `docs/screenshots/gui-downloads.png` | Main window with live parallel downloads, segment bars, categories | Main screenshot |
| `docs/screenshots/gui-add-link.png` | "Add download" dialog (segments, speed limit, scheduler) | Feature |
| `docs/screenshots/gui-grabber.png` | Site Grabber scan results | Feature |
| `docs/screenshots/gui-settings.png` | Settings dialog (concurrency, queue, bridge) | Optional |
| `docs/screenshots/gui-main.png` | Empty main window (older) | Backup |

---

## 7. Release notes v1.0.0

```
- Up to 32 parallel segments, pause/resume/cancel, queue and scheduler
- Web page resolution: og:video, source tags, JSON-LD; clear error when no media exists
- Playlists: one job expands to every video; DASH audio+video merged with ffmpeg
- Quick site buttons: YouTube, Instagram, X (Twitter), Facebook, TikTok, Vimeo
- Browser bridge + clipboard monitoring, Site Grabber, FTP, mirror URLs, speed limit,
  voice notifications
- 165 automated checks, clean pyflakes
```

---

## 8. Keywords / tags

```
download manager, download accelerator, segmented download, resume download,
download queue, video downloader, playlist downloader, open source, MIT,
free software, FTP download, Turkish download manager
```

---

## 9. FAQ — questions portals usually ask

| Question | Answer |
| --- | --- |
| Does it need installation? | Unzip the archive and run `python -m download_manager`; `baslat_gui.bat` is the Windows shortcut (no CMD window), `baslat_gui.vbs` starts it fully hidden. |
| Any malware/bundled toolbars? | No. Single dependency `requests`; MIT-licensed open source code. |
| Ads? | None, nothing is installed or modified. |
| Works offline? | The UI works offline; downloads need internet. |
| Installer (exe/msi)? | Distributed as a portable ZIP; a signed installer is planned. |
| Price? | Free, no trial, no account. |
| Support? | GitHub Issues: https://github.com/RetroNyym/Retro-Download-Manager/issues |
