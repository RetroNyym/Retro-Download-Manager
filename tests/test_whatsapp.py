import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from download_manager import DownloadManager
from download_manager.whatsapp import (
    default_output_folder,
    is_allowed,
    load_meta,
    normalize_whitelist,
)

RESULTS = []
TMP = tempfile.mkdtemp(prefix="pdm_wa_")


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition)))
    print(f"[{'OK  ' if condition else 'FAIL'}] {name} {detail}")


def put_pdf(folder, name, meta=None):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    with open(path, "wb") as handle:
        handle.write(b"%PDF-1.4 icerik " + name.encode("utf-8"))
    if meta is not None:
        with open(path + ".json", "w", encoding="utf-8") as handle:
            json.dump(meta, handle, ensure_ascii=False)
    return path


def main():
    # -- beyaz liste normalizasyonu -------------------------------------------
    norm = normalize_whitelist(["123@g.us", {"jid": "905xx@s.net", "label": "Ali"},
                                "  ", 42])
    check("normalizasyon sayisi", len(norm) == 2, str(len(norm)))
    check("normalizasyon etiket", norm[0]["label"] == "123" and
          norm[1]["label"] == "Ali", str(norm))

    # -- izin kontrolü -----------------------------------------------------------
    wl = [{"jid": "111-222@g.us", "label": "Grup"},
          {"jid": "905551112233@s.net", "label": "Musteri"}]
    check("bos liste her seyi reddeder", not is_allowed({"chat": "x@g.us"}, []))
    check("grup jid eslesme", is_allowed({"chat": "111-222@g.us"}, wl))
    check("grup jid eslesmez", not is_allowed({"chat": "999@g.us"}, wl))
    check("numara govdesi eslesme",
          is_allowed({"chat": "905551112233@s.whatsapp.net"}, wl))
    check("numara eslesmez", not is_allowed({"chat": "905550000000@s.whatsapp.net"}, wl))
    check("sender ile eslesme",
          is_allowed({"chat": "999@g.us", "sender": "905551112233@s.net"}, wl))
    check("metin jid girdisi", is_allowed({"chat": "111-222@g.us"},
                                          ["111-222@g.us"]))
    check("bos meta reddi", not is_allowed({}, wl))

    # -- ust veri -----------------------------------------------------------------
    side_pdf = put_pdf(os.path.join(TMP, "meta"), "a.pdf",
                       {"chat": "1-2@g.us", "label": "Test"})
    meta = load_meta(side_pdf)
    check("meta okundu", meta.get("chat") == "1-2@g.us", str(meta))
    check("meta yoksa bos", load_meta(os.path.join(TMP, "yok.pdf")) == {})

    check("varsayilan hedef klasor",
          default_output_folder("/tmp/dl").endswith("WhatsApp PDF"))

    # -- izleyici: saglikli teslim -------------------------------------------------
    mgr = DownloadManager(data_dir=os.path.join(TMP, "data"))
    mgr.apply_settings({"bridge_enabled": False, "auto_start": False,
                        "queue_running": False})
    watch = os.path.join(TMP, "izleme")
    out = os.path.join(TMP, "cikti")
    mgr.apply_settings({
        "wa_enabled": True,
        "wa_watch_folder": watch,
        "wa_output_folder": out,
        "wa_whitelist": [{"jid": "30-40@g.us", "label": "Fatura"}],
    })
    watcher = mgr.wa_watcher
    check("izleyici aktif", watcher._thread is not None)

    put_pdf(watch, "fatura.pdf",
            {"chat": "30-40@g.us", "label": "Fatura", "name": "fatura.pdf"})
    put_pdf(watch, "izinli_degil.pdf", {"chat": "70-80@g.us"})
    taken = watcher.scan_once()
    check("izinli pdf alindi", taken == 1, str(taken))
    check("hedef klasorde dosya",
          os.path.isfile(os.path.join(out, "fatura.pdf")))
    check("izin disi yerinde kaldi",
          os.path.isfile(os.path.join(watch, "izinli_degil.pdf")))
    check("yan dosya temizlendi",
          not os.path.exists(os.path.join(out, "fatura.pdf.json")))
    check("tekrar tarama almaz", watcher.scan_once() == 0)

    # -- bos beyaz liste hicbir seyi almaz --------------------------------------------
    mgr.apply_settings({"wa_whitelist": []})
    put_pdf(watch, "bos_liste.pdf", {"chat": "30-40@g.us"})
    taken = watcher.scan_once()
    check("bos beyaz liste sifir", taken == 0, str(taken))
    check("bos listede dosya yerinde",
          os.path.isfile(os.path.join(watch, "bos_liste.pdf")))

    # -- ust verisiz dosya alinmaz -------------------------------------------------------
    mgr.apply_settings({"wa_whitelist": [{"jid": "30-40@g.us", "label": "Fatura"}]})
    put_pdf(watch, "ust_verisiz.pdf")
    taken = watcher.scan_once()
    check("ust verisiz alinmaz", taken == 0, str(taken))

    # -- klasor kapaliyken hata yok ---------------------------------------------------------
    mgr.apply_settings({"wa_enabled": False})
    check("kapaliyken tarama sessiz", watcher.scan_once() == 0)

    mgr.shutdown()
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} whatsapp test gecti")
    shutil.rmtree(TMP, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
