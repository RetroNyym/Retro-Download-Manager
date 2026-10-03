"""Yerel güncelleme kanalı: yerel klasör/UNC/HTTP kaynağından sürüm paketi indirme.

Manifest (version.json):
    {"version": "1.1.0", "file": "Retro-Download-Manager-1.1.0.zip",
     "sha256": "<64 hex>", "notes": "..."}

Kaynak (Settings.update_source):
    - klasör yolu (ör. C:\\Guncelleme veya \\\\sunucu\\paylasim)  -> <klasör>/version.json
    - http(s)://.../version.json (klasör URL'i de olur)
Boş kaynak = güncelleme kapalı.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import threading
import time
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

MANIFEST_NAME = "version.json"
STAGING_DIRNAME = ".update_staging"
BACKUP_DIRNAME = ".update_backup"
# Güncelleme sırasında korunacak kök girdileri (kullanıcı verisi / git geçmişi).
PRESERVE_ROOT = {".git", STAGING_DIRNAME, BACKUP_DIRNAME}
# Paket içinde korunacak alt klasörler (kullanıcı verisi, oturumlar, bağımlılıklar).
PRESERVE_SUBDIRS = {
    "download_manager": {"data"},
    "whatsapp_listener": {"session", "node_modules", "__pycache__"},
}
PACKAGE_INIT = Path("download_manager") / "__init__.py"


def _current_version():
    """Sürümü paketten okur (döngüsel import önlemi, çağrı anında)."""
    from . import __version__
    return __version__


def parse_version(text):
    """'1.2.3' -> (1, 2, 3); 'v2.10rc1' -> (2, 10) (yalnız sayısal önek)."""
    match = re.match(r"v?(\d+(?:\.\d+)*)", str(text or "0").strip())
    if not match:
        return (0,)
    return tuple(int(part) for part in match.group(1).split("."))


def compare_versions(a, b):
    ta, tb = parse_version(a), parse_version(b)
    length = max(len(ta), len(tb))
    ta += (0,) * (length - len(ta))
    tb += (0,) * (length - len(tb))
    return (ta > tb) - (ta < tb)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_url(url, timeout=20):
    request = Request(url, headers={"User-Agent": "Retro-Download-Manager"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def load_manifest(source):
    """Manifesti okur; hata durumunda RuntimeError fırlatır."""
    source = (source or "").strip()
    if not source:
        raise RuntimeError("güncelleme kaynağı boş")
    if source.lower().startswith(("http://", "https://")):
        base = source.rstrip("/")
        raw = _read_url(base if base.endswith(".json") else base + "/" + MANIFEST_NAME)
        data = json.loads(raw.decode("utf-8"))
    else:
        base = Path(source).expanduser()
        manifest = base if base.is_file() else base / MANIFEST_NAME
        data = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data.get("version") or not data.get("file"):
        raise RuntimeError("manifest geçersiz (version/file alanları gerekli)")
    return data


def check_for_update(source, current=None):
    """{status: up_to_date|update_available|disabled|error, ...} döndürür."""
    current = current or _current_version()
    if not (source or "").strip():
        return {"status": "disabled"}
    try:
        manifest = load_manifest(source)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    result = {"status": "up_to_date", "current": current,
              "version": str(manifest.get("version", "")),
              "notes": str(manifest.get("notes", "")),
              "file": str(manifest.get("file", "")),
              "sha256": str(manifest.get("sha256", "")).lower()}
    if compare_versions(manifest["version"], current) > 0:
        result["status"] = "update_available"
    return result


def fetch_package(source, filename, dest_dir):
    """Paketi (zip) indirir/kopyalar; dönen yol."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    source = (source or "").strip()
    if source.lower().startswith(("http://", "https://")):
        base = source.rstrip("/")
        url = base if base.lower().endswith(".zip") else f"{base}/{filename}"
        data = _read_url(url, timeout=120)
        dest.write_bytes(data)
        return dest
    src = Path(source).expanduser()
    package = src / filename if src.is_dir() else src
    if not package.is_file():
        raise RuntimeError(f"paket bulunamadı: {package}")
    if Path(package).resolve() != dest.resolve():
        shutil.copy2(package, dest)
    return dest


def _safe_extract(zip_path, staging):
    """Zip-slip korumalı çıkarma."""
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            target = Path(staging) / info.filename
            if not str(target.resolve()).startswith(str(Path(staging).resolve())):
                raise RuntimeError(f"güvensiz arşiv yolu: {info.filename}")
        archive.extractall(staging)


def _staged_version(staging):
    init = Path(staging) / PACKAGE_INIT
    if not init.is_file():
        raise RuntimeError("paket içinde download_manager/__init__.py yok")
    match = re.search(r'__version__\s*=\s*"([^"]+)"',
                      init.read_text(encoding="utf-8", errors="ignore"))
    if not match:
        raise RuntimeError("paket sürümü okunamadı")
    return match.group(1)


def apply_update(app_root, zip_path, expected_version=None, backup=True):
    """Zip'i uygular. Kullanıcı verisi korunur; hata olursa geri alır.

    Dönen değer: uygulanan sürüm (str).
    """
    app_root = Path(app_root).resolve()
    staging = app_root / STAGING_DIRNAME
    backup_dir = app_root / BACKUP_DIRNAME
    for path in (staging, backup_dir):
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
    try:
        _safe_extract(zip_path, staging)
        version = _staged_version(staging)
        if expected_version and compare_versions(version, expected_version) != 0:
            raise RuntimeError(
                f"manifest sürümü {expected_version} ama paket {version}")
        moved_to_backup = []
        replaced = []
        try:
            for item in sorted(staging.iterdir()):
                if item.name in PRESERVE_ROOT:
                    continue
                target = app_root / item.name
                keeps = PRESERVE_SUBDIRS.get(item.name, set())
                kept = []
                for keep in keeps:
                    keep_path = target / keep
                    if target.is_dir() and keep_path.exists():
                        stash = backup_dir / ("__keep_" + item.name + "_" + keep)
                        shutil.move(str(keep_path), str(stash))
                        kept.append((keep, stash))
                if target.exists():
                    if backup:
                        shutil.move(str(target), str(backup_dir / item.name))
                    else:
                        shutil.rmtree(target) if target.is_dir() else target.unlink()
                    moved_to_backup.append(item.name)
                shutil.move(str(item), str(target))
                replaced.append((item.name, kept))
        except Exception:
            # Geri alma: taşınanları eski yerine koy.
            for name, _kept in reversed(replaced):
                target = app_root / name
                if target.exists():
                    shutil.rmtree(target) if target.is_dir() else target.unlink()
            for name in reversed(moved_to_backup):
                saved = backup_dir / name
                if saved.exists():
                    shutil.move(str(saved), str(app_root / name))
            raise
        # Korunan alt klasörleri yeni pakete taşı.
        for name, kept in replaced:
            for keep, stash in kept:
                dest = app_root / name / keep
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    shutil.rmtree(dest, ignore_errors=True)
                shutil.move(str(stash), str(dest))
        # staging temiz (içindekiler taşındı).
        shutil.rmtree(staging, ignore_errors=True)
        if not backup:
            shutil.rmtree(backup_dir, ignore_errors=True)
        return version
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def prepare_restart(app_root, runner=None):
    """Yeni süreç başlatıp mevcut süreci sonlandırır (kaydetme sonrası çağrılır)."""
    app_root = Path(app_root).resolve()
    runner = runner or _default_runner
    runner(app_root)


def _default_runner(app_root):
    import subprocess
    kwargs = {"cwd": str(app_root)}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen([sys.executable, "-m", "download_manager"], **kwargs)
    os._exit(0)


def install_update(source, app_root=None, current=None, expected_version=None,
                   progress=None):
    """Kontrol → indir → SHA-256 → uygula. Uygulanırsa dict{status:'installed'}."""
    app_root = Path(app_root) if app_root else Path(__file__).resolve().parent.parent
    status = check_for_update(source, current=current)
    if status["status"] != "update_available":
        return status
    manifest = load_manifest(source)
    filename = str(manifest["file"])
    if progress:
        progress(f"Paket indiriliyor: {filename}")
    # Paket staging DIŞINDA tutulmalı: apply_update staging'i baştan temizler.
    pkg_dir = app_root / ".update_pkg"
    shutil.rmtree(pkg_dir, ignore_errors=True)
    package = fetch_package(source, filename, pkg_dir)
    expected_sha = str(manifest.get("sha256", "")).lower()
    if expected_sha:
        actual = sha256_file(package)
        if actual != expected_sha:
            shutil.rmtree(pkg_dir, ignore_errors=True)
            raise RuntimeError(f"SHA-256 uyuşmuyor: {actual[:12]}… != {expected_sha[:12]}…")
    if progress:
        progress("Paket doğrulandı, uygulanıyor…")
    version = apply_update(app_root, package,
                           expected_version=expected_version or manifest["version"])
    shutil.rmtree(pkg_dir, ignore_errors=True)
    return {"status": "installed", "version": version}


def auto_update(manager, interval=6 * 3600, app_root=None):
    """Arka plan döngüsü: kaynak boşsa çalışmaz; güncelleme varsa indirip
    uygular, müsaitse yeniden başlatır. Kuyrukta iş varsa 60 sn sonra tekrar dener."""
    app_root = Path(app_root) if app_root else Path(__file__).resolve().parent.parent
    while not manager._stop.is_set():
        source = (manager.settings.update_source or "").strip()
        enabled = bool(getattr(manager.settings, "update_enabled", True))
        if enabled and source:
            try:
                status = check_for_update(source)
                if status["status"] == "update_available":
                    busy = any(t.is_busy for t in manager.tasks)
                    if not busy:
                        manager.log(f"Güncelleme uygulanıyor: "
                                    f"{status['current']} → {status['version']}", "info")
                        result = install_update(
                            source, app_root=app_root,
                            progress=lambda msg: manager.log(msg, "info"))
                        if result.get("status") == "installed":
                            manager.log("Güncelleme tamamlandı, program yeniden "
                                        "başlatılıyor.", "success")
                            manager.settings.save()
                            manager.shutdown()
                            time.sleep(1.0)
                            prepare_restart(app_root)
                            return
                    else:
                        manager.log(f"Yeni sürüm var ({status['version']}) — "
                                    "indirmeler bitince uygulanacak.", "info")
            except Exception as exc:
                manager.log(f"Güncelleme hatası: {exc}", "warning")
        manager._stop.wait(interval)


def start_auto_update(manager, interval=6 * 3600, app_root=None):
    thread = threading.Thread(target=auto_update, args=(manager, interval, app_root),
                              daemon=True)
    thread.start()
    return thread


__all__ = [
    "MANIFEST_NAME", "parse_version", "compare_versions", "sha256_file",
    "load_manifest", "check_for_update", "fetch_package", "apply_update",
    "install_update", "prepare_restart", "auto_update", "start_auto_update",
]
