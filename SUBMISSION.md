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
| Ekran görüntüsü üretimi | `python tools/shots.py` |

## Temel bilgiler

| Alan | Değer |
| --- | --- |
| Yazılım adı | Retro+ Download Manager |
| Sürüm | 1.0.0 |
| Lisans | MIT (ücretsiz, açık kaynak) |
| İşletim sistemleri | Windows 10/11, Linux, macOS (Python 3.11+) |
| Kategori | Internet > Download Managers / System Utilities |
| Dil | Türkçe arayüz (kod İngilizce) |
| Fiyat | Ücretsiz |
| Ana sayfa | https://retro-download-manager.netlify.app |
| Kaynak kod | https://github.com/RetroNyym/Retro-Download-Manager |
| İndirme (site) | https://retro-download-manager.netlify.app/download/Retro-Download-Manager-v1.0.0.zip |
| İndirme (GitHub Release) | https://github.com/RetroNyym/Retro-Download-Manager/releases/download/v1.0.0/Retro-Download-Manager-v1.0.0.zip |
| Boyut | 266 KB (ZIP, kaynak kod) |
| SHA-256 | `73b50af2d18455eb4ca0d394b36138d66e5a8c83c34315b3867f80a05982366b` |
| Ekran görüntüsüleri | `docs/screenshots/gui-downloads.png` (ana), `gui-add-link.png`, `gui-grabber.png`, `gui-settings.png` |
| İletişim e-postası | `216476870+RetroNyym@users.noreply.github.com` (GitHub noreply — kendi adresiniz açılınca tüm dosyalarda güncelleyin) |

## Kısa açıklama (≤100 karakter)

```
Çok parçalı, hızlı indirme yöneticisi — duraklat/devam, kuyruk, zamanlama, video linkleri
```

## Uzun açıklama (portallar için)

Türkçe uzun açıklama → [`docs/submission/metinler-tr.md`](docs/submission/metinler-tr.md) §3,
İngilizce uzun açıklama → [`docs/submission/metinler-en.md`](docs/submission/metinler-en.md) §3.

---

## Yayınlama sırası (önerilen)

1. **GitHub Release** (zaten hazır: `v1.0.0`) — tüm portallar bunu referans alır
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
