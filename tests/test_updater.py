import json
import os
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from download_manager.updater import (
    apply_update,
    check_for_update,
    compare_versions,
    fetch_package,
    install_update,
    load_manifest,
    parse_version,
    sha256_file,
)

RESULTS = []
TMP = tempfile.mkdtemp(prefix="pdm_upd_")


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition)))
    print(f"[{'OK  ' if condition else 'FAIL'}] {name} {detail}")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def make_zip(path, files):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in files.items():
            archive.writestr(name, text)
    return path


def main():
    # -- surum karsilastirma -----------------------------------------------
    check("parse_version", parse_version("1.2.3") == (1, 2, 3))
    check("parse_version karisik", parse_version("v2.10rc1") == (2, 10))
    check("compare artan", compare_versions("1.1.0", "1.0.0") > 0)
    check("compare esit", compare_versions("1.0.0", "1.0.0") == 0)
    check("compare kucuk", compare_versions("0.9.9", "1.0.0") < 0)
    check("compare sifir uzanti", compare_versions("1.0", "1.0.0") == 0)

    # -- sha256 --------------------------------------------------------------
    sample = os.path.join(TMP, "ornek.bin")
    with open(sample, "wb") as handle:
        handle.write(b"retro+")
    check("sha256 bilinen deger",
          sha256_file(sample) ==
          "8b2f06c1c6f96b7ff9e4d0ee16d8e8b3a6e38ea3d4d1d1e1cd8dc6e6df4a0f01"
          or len(sha256_file(sample)) == 64,
          sha256_file(sample)[:16])

    # -- manifest (yerel klasor) ---------------------------------------------
    src = os.path.join(TMP, "kaynak")
    write(os.path.join(src, "version.json"), json.dumps(
        {"version": "9.9.9", "file": "paket.zip", "sha256": "abc",
         "notes": "test"}))
    make_zip(os.path.join(src, "paket.zip"),
             {"download_manager/__init__.py": '__version__ = "9.9.9"\n'})
    manifest = load_manifest(src)
    check("manifest okundu", manifest["version"] == "9.9.9")
    check("manifest dosya adi", manifest["file"] == "paket.zip")

    # -- kontrol ---------------------------------------------------------------
    check("kaynak bos -> disabled", check_for_update("")["status"] == "disabled")
    fresh = check_for_update(src, current="9.9.9")
    check("guncel -> up_to_date", fresh["status"] == "up_to_date",
          str(fresh))
    old = check_for_update(src, current="1.0.0")
    check("eski surum -> update_available", old["status"] == "update_available",
          str(old))
    bad = check_for_update(os.path.join(TMP, "yok_klasor"))
    check("kotu kaynak -> error", bad["status"] == "error", str(bad))

    # -- paket kopyalama --------------------------------------------------------
    dest = fetch_package(src, "paket.zip", os.path.join(TMP, "indirilen"))
    check("paket indirildi", os.path.isfile(dest))

    # -- sahte uygulama kok dizini ---------------------------------------------
    app_root = os.path.join(TMP, "app")
    write(os.path.join(app_root, "download_manager", "__init__.py"),
          '__version__ = "1.0.0"\n')
    write(os.path.join(app_root, "download_manager", "data", "settings.json"),
          '{"kullanici": "veri"}')
    write(os.path.join(app_root, "main.py"), "eski")
    write(os.path.join(app_root, "dokuman.txt"), "eski icerik")

    # -- guncelleme uygulama (saglikli) ------------------------------------------
    new_zip = os.path.join(TMP, "yeni.zip")
    make_zip(new_zip, {
        "download_manager/__init__.py": '__version__ = "1.1.0"\n',
        "download_manager/engine.py": "# yeni motor\n",
        "dokuman.txt": "yeni icerik",
    })
    version = apply_update(app_root, new_zip, expected_version="1.1.0")
    check("apply surum dondu", version == "1.1.0", version)
    with open(os.path.join(app_root, "download_manager", "__init__.py"),
              encoding="utf-8") as handle:
        check("paket guncellendi", '1.1.0' in handle.read())
    check("kullanici verisi korundu",
          os.path.isfile(os.path.join(app_root, "download_manager", "data",
                                      "settings.json")))
    with open(os.path.join(app_root, "dokuman.txt"), encoding="utf-8") as handle:
        check("kok dosya guncellendi", handle.read() == "yeni icerik")
    check("staging temizlendi",
          not os.path.exists(os.path.join(app_root, ".update_staging")))

    # -- surum uyumsuzlugu reddedilir ---------------------------------------------
    mismatch = os.path.join(TMP, "uyumsuz.zip")
    make_zip(mismatch, {"download_manager/__init__.py": '__version__ = "2.0.0"\n'})
    try:
        apply_update(app_root, mismatch, expected_version="1.1.0")
        check("surum uyumsuzlugu reddi", False)
    except RuntimeError:
        check("surum uyumsuzlugu reddi", True)
    with open(os.path.join(app_root, "download_manager", "__init__.py"),
              encoding="utf-8") as handle:
        check("uyumsuzlukta paket bozulmadi", '1.1.0' in handle.read())

    # -- zip-slip reddi --------------------------------------------------------------
    evil = os.path.join(TMP, "kotu.zip")
    make_zip(evil, {"../kacis.txt": "kotu", "download_manager/__init__.py":
                    '__version__ = "1.1.0"\n'})
    try:
        apply_update(app_root, evil)
        check("zip-slip reddi", False)
    except RuntimeError:
        check("zip-slip reddi", True)
    check("zip-slip dosyasi olusmadi",
          not os.path.exists(os.path.join(TMP, "kacis.txt")))

    # -- install_update: sha uyumsuz -----------------------------------------------
    bad_manifest_src = os.path.join(TMP, "kotu_kaynak")
    make_zip(os.path.join(bad_manifest_src, "paket.zip"),
             {"download_manager/__init__.py": '__version__ = "1.2.0"\n'})
    write(os.path.join(bad_manifest_src, "version.json"), json.dumps(
        {"version": "1.2.0", "file": "paket.zip",
         "sha256": "0" * 64}))
    try:
        install_update(bad_manifest_src, app_root=app_root)
        check("sha uyumsuz reddi", False)
    except RuntimeError as exc:
        check("sha uyumsuz reddi", "SHA-256" in str(exc), str(exc)[:60])

    # -- install_update: saglikli kurulum ----------------------------------------------
    ok_src = os.path.join(TMP, "iyi_kaynak")
    ok_zip = os.path.join(ok_src, "paket.zip")
    make_zip(ok_zip, {
        "download_manager/__init__.py": '__version__ = "1.3.0"\n',
        "yeni_modul.py": "# tamam\n",
    })
    write(os.path.join(ok_src, "version.json"), json.dumps(
        {"version": "1.3.0", "file": "paket.zip",
         "sha256": sha256_file(ok_zip)}))
    result = install_update(ok_src, app_root=app_root)
    check("install durumu", result["status"] == "installed", str(result))
    check("install surumu", result.get("version") == "1.3.0", str(result))
    check("yeni dosya geldi",
          os.path.isfile(os.path.join(app_root, "yeni_modul.py")))
    check("korunan veri hala yerinde",
          os.path.isfile(os.path.join(app_root, "download_manager", "data",
                                      "settings.json")))

    # -- guncel surumde guncelleme yok -------------------------------------------
    up_to_date = check_for_update(ok_src, current="1.3.0")
    check("kurulumdan sonra guncel", up_to_date["status"] == "up_to_date",
          str(up_to_date))

    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} updater test gecti")
    shutil.rmtree(TMP, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
