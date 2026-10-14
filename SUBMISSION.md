# Retro+ Download Manager — Dağıtım / Gönderim Paketi

Bu dosya **indekstir**: yazılım indirme portallarına (global + Türkiye)
başvuru için gereken her şey aşağıda ve `docs/submission/` klasöründedir.
Sürüm değişince yalnızca sürüm numarası ve linkleri güncelleyin.

| İhtiyaç | Dosya |
| --- | --- |
| Türkçe başvuru metinleri (kısa/uzun açıklama, künye, ekran görüntüleri, SSS) | [`docs/submission/metinler-tr.md`](docs/submission/metinler-tr.md) |
| İngilizce başvuru metinleri | [`docs/submission/metinler-en.md`](docs/submission/metinler-en.md) |
| Portal/tanıtım e-postası şablonları (TR + EN) | [`docs/submission/e-posta-sablonlari.md`](docs/submission/e-posta-sablonlari.md) |
| **Başvuru durum takibi (ne, ne zaman, sonuç)** | [`docs/submission/KONTROL-LISTESI.md`](docs/submission/KONTROL-LISTESI.md) |
| PAD dosyası (UpdateStar vb.) | [`docs/pad.xml`](docs/pad.xml) → site deploy: `download/pad.xml` |
| Chocolatey paketi | [`chocolatey/RetroDownloadManager.nuspec`](chocolatey/RetroDownloadManager.nuspec) + `tools/` |
| Ekran görüntüsü üretimi | `python tools/shots.py` |

## Temel bilgiler

| Alan | Değer |
| --- | --- |
| Yazılım adı | Retro+ Download Manager |
| Sürüm | 1.1.0 |
| Lisans | MIT (ücretsiz, açık kaynak) |
| İşletim sistemleri | Windows 10/11 (x64, taşınabilir exe — Python gerekmez); kaynak: Python 3.11+ (Linux/macOS) |
| Kategori | Internet > Download Managers / System Utilities |
| Dil | Türkçe arayüz (kod İngilizce) |
| Fiyat | Ücretsiz |
| Ana sayfa | https://retro-download-manager.netlify.app |
| Kaynak kod | https://github.com/RetroNyym/Retro-Download-Manager |
| İndirme (site) | https://retro-download-manager.netlify.app/download/RetroDownloadManager-v1.1.0.zip |
| İndirme (GitHub Release) | https://github.com/RetroNyym/Retro-Download-Manager/releases/download/v1.1.0/RetroDownloadManager-v1.1.0.zip |
| Boyut | 51.5 MB (ZIP, taşınabilir exe + aria2 torrent motoru) |
| SHA-256 | `9e953eb3fca84a0d5667857ef322ba6ff0f97dfb0470df2d7528d111913f62cb` |
| Ekran görüntüsüleri | `docs/screenshots/store-1920x1080-main.png` (ana), `gui-downloads.png`, `gui-add-link.png`, `gui-grabber.png`, `gui-settings.png` |
| İletişim e-postası | `216476870+RetroNyym@users.noreply.github.com` (GitHub noreply — kendi adresiniz açılınca tüm dosyalarda güncelleyin) |

## Kısa açıklama (≤100 karakter)

```
Çok parçalı indirme + torrent (aria2) ve magnet: desteği — duraklat/devam, kuyruk, zamanlama
```

## Uzun açıklama (portallar için)

Türkçe uzun açıklama → [`docs/submission/metinler-tr.md`](docs/submission/metinler-tr.md) §3,
İngilizce uzun açıklama → [`docs/submission/metinler-en.md`](docs/submission/metinler-en.md) §3.

---

## Yayınlama sırası (önerilen)

1. **GitHub Release** (zaten hazır: `v1.1.0` — exe + ZIP, SmartScreen'süz kurulum notlu) — tüm portallar bunu referans alır
2. ✅ **itch.io** — **yayında**: https://retronym.itch.io/retro-download-manager (01.10.2026,
   hesap Retronym, ücretsiz + MIT, kapak +4 ekran görüntüsü + ZIP) ·
   🟨 **SourceForge** (en çok trafik; telefon doğrulaması `POST /p/verify_phone` →
   Cloudflare 403, destek/sonraki oturum bekliyor)
3. **MajorGeeks + Softpedia + FossHub** — manuel ama hızlı inceleme
4. **Softonic, Uptodown, AlternativeTo** — self-servis hesap (ücretsiz)
5. **UpdateStar (PAD dosyası), FileHippo (e-posta)** — doğrudan e-posta
6. **Türkiye:** CHIP + Donanım Haber (gerçek form var), Tamindir, Webtekno;
   ShiftDelete/Gezginler/Technopat'ta form yok → e-posta
7. **TR teknoloji siteleri** — inceleme/haber önerisi e-postası + forum tanıtım konusu

> **Gerçek:** Türkiye'deki indirme portallarının çoğu editöryeldir, "program yükle"
> formu yoktur. Bu yüzden TR'de açık form verenler (CHIP, Donanım Haber, Tamindir,
> Webtekno) önceliklidir, kalanlar `e-posta-sablonlari.md` ile e-posta ile gidilir.
> Doğrulanmış tüm URL'ler ve durumlar →
> [`docs/submission/KONTROL-LISTESI.md`](docs/submission/KONTROL-LISTESI.md).

---

## Sürüm güncelleme akışı (her yeni sürümde)

1. Repo'da yeni tag + GitHub Release oluşturun, ZIP'i asset olarak ekleyin
2. ZIP'i `download/` klasörüne kopyalayıp `indir.html` içindeki linki güncelleyin
3. `SHA-256`'yı yeni ZIP için üretip bu dosyadaki ve `metinler-*.md` içindeki hash'i güncelleyin
4. Siteyi yeniden deploy edin (Netlify + Cloudflare + GitHub Pages)
5. `python tools/shots.py` ile ekran görüntülerini yenileyin (arayüz değiştiyse)
6. SourceForge'a Files → Add Release; MajorGeeks'e "Report New Version"
7. `KONTROL-LISTESI.md` içindeki tarih/sürümleri güncelleyin
