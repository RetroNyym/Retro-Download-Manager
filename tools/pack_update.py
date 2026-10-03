"""Yerel güncelleme paketi üretir: dist/<sürüm>/ + version.json + zip.

Kullanım (repo kökünden):
    python tools\\pack_update.py
    python tools\\pack_update.py --out D:\\Guncelleme

Çıktı:
    <out>/Retro-Download-Manager-<sürüm>.zip   (SHA-256'lı)
    <out>/version.json                         (manifest)

Bu klasörü paylaşıma (yerel disk / UNC / HTTP) koyan Retro+ Update
kaynağını oraya yönlendirir; kullanıcılar linke dokunmadan güncellenir.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "session", "dist",
                ".update_staging", ".update_backup", ".update_pkg", ".wrangler",
                ".gizli"}
EXCLUDE_FILES = {"Thumbs.db", "desktop.ini"}
EXCLUDE_SUFFIXES = {".zip", ".log", ".pyc", ".part"}


def app_version():
    text = (REPO / "download_manager" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        raise SystemExit("__version__ bulunamadı")
    return match.group(1)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def should_skip(entry: Path):
    rel_parts = entry.relative_to(REPO).parts
    if any(part in EXCLUDE_DIRS for part in rel_parts):
        return True
    if entry.name in EXCLUDE_FILES:
        return True
    if entry.is_file() and entry.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    return False


def build(out_dir: Path):
    version = app_version()
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_name = f"Retro-Download-Manager-{version}.zip"
    zip_path = out_dir / zip_name
    if zip_path.exists():
        zip_path.unlink()
    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(REPO.rglob("*")):
            if item.is_dir() or should_skip(item):
                continue
            arcname = str(item.relative_to(REPO)).replace("\\", "/")
            archive.write(item, arcname)
            count += 1
    digest = sha256_file(zip_path)
    manifest = {
        "version": version,
        "file": zip_name,
        "sha256": digest,
        "notes": f"Retro+ Download Manager {version}",
    }
    manifest_path = out_dir / "version.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    size = zip_path.stat().st_size
    print(f"paket   : {zip_path}")
    print(f"dosya   : {count}")
    print(f"boyut   : {size:,} bayt")
    print(f"sha256  : {digest}")
    print(f"manifest: {manifest_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Yerel güncelleme paketi üretir")
    parser.add_argument("--out", default=str(REPO / "dist"),
                        help="Çıktı klasörü (varsayılan: dist)")
    args = parser.parse_args(argv)
    build(Path(args.out).expanduser())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
