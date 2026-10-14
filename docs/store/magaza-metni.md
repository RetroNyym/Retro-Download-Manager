# Mağaza metinleri — Microsoft Store gönderimi

Partner Center'daki alanlara buradan yapıştırın. Sürüm: **1.1.0**.

## Ürün kimliği

| Alan | Değer |
| --- | --- |
| Ürün adı | Retro+ Download Manager |
| Yayıncı görünen ad | Retro+ (hesap kimliğiyle eşleşmeli) |
| Kategori | Utilities & tools (Araçlar) |
| Alt kategori | — |
| Fiyat | Ücretsiz |
| Desteklenen mimariler | x64 |

## Kısa açıklama (Store tekrarı, ~1 karakter)

- **TR:** Hızlı, parçalı indirme yöneticisi — magnet ve .torrent desteğiyle.
- **TR (opsiyonel kısa):** Hızlı indirme yöneticisi + torrent.
- **EN:** Fast chunked download manager with magnet and .torrent support.

## Uzun açıklama

**TR:**

> Retro+ Download Manager, bağlantıları paralel parçalar hâlinde indirir,
> kuyruğu yönetir ve yarım kalan işleri kaldığı yerden sürdürür.
>
> Özellikler:
> - Hızlı, parçalı (multi-segment) HTTP/HTTPS/FTP indirmeleri
> - Kuyruk, klasöre göre otomatik sıralama, hız sınırı
> - Yarım kalan indirmeleri otomatik sürdürme
> - BitTorrent: magnet: bağlantıları ve .torrent dosyaları (aria2 motoru)
> - "Torrent" sekmesinden duraklat/devam/kaldır
> - Tarayıcı bağlantısını tek tıkla gönderme (opsiyonel eklenti)
>
> Tüm veriler yalnızca cihazınızda saklanır; hesap gerekmez, reklam/analitik
> yoktur.

**EN:**

> Retro+ Download Manager downloads links in parallel segments, manages a
> queue, and resumes interrupted downloads.
>
> Features:
> - Fast multi-segment HTTP/HTTPS/FTP downloads
> - Queue, category-based sorting, speed limit
> - Automatic resume for interrupted downloads
> - BitTorrent: magnet: links and .torrent files (aria2 engine)
> - Pause/resume/remove from the dedicated Torrent tab
> - Optional browser extension to send links in one click
>
> All data stays on your device. No account, no ads, no analytics.

## Anahtar kelimeler (en fazla 7)

1. indirme yöneticisi
2. download manager
3. torrent
4. magnet
5. hızlı indirme
6. kuyruk
7. resume

## Yaş derecelendirmesi (IARC anketi notu)

Uygulama yalnızca indirme yöneticisidir; şiddet, kumar, yetişkin içerik,
kullanıcı arası etkileşim **yoktur**. Beklenen sonuç: **3+ / ESRB EVERYONE**.
Ankette "dosya indirme/dış bağlantı" sorusuna uygulamanın yalnızca kullanıcının
kendi verdiği adresleri indirdiğini belirtin.

## Ekran görüntüleri (zorunlu, en az 1; önerilen 3+)

Mevcutlar: `docs/screenshots/`

| Dosya | Kullanım |
| --- | --- |
| `gui-main.png` | Ana ekran / indirme listesi (kapak adayı) |
| `gui-downloads.png` | Kuyruk görünümü |
| `gui-settings.png` | Ayarlar |
| `gui-add-link.png` | Bağlantı ekleme |
| `gui-grabber.png` | Yakalayıcı |
| `gui-search.png` | Arama |

Store şartı: en az **1366×768**, gerçek uygulama ekranı; kırpılmış/gerilmiş
olmamalı. Türkçe arayüz görselleri tercih edilir; gerekirse EN görsel de ekle.

## Gönderim notları (certification notes)

- Uygulama gömülü **aria2** (GPLv2+) kullanır; kaynak:
  https://github.com/aria2/aria2 (Store dışı dağıtımda lisans metni `tools/`
  içinde sunulur).
- Bağımlılık: harici servis/driver **yok**; yalnızca internet erişimi.
- Test için dikkat: magnet ekleme ilk denemede tracker yanıtı bekleyebilir;
  uygulama kilitlenmez, durum "Sırada/İndiriliyor" olarak kalır.
- Kaldırma: Windows Ayarlar > Uygulamalar > Retro+ Download Manager (MSIX
  kaldırma menüsü otomatik gelir).

## Sürüm güncelleme akışı

1. `download_manager/__init__.py` → `__version__` (örn. 1.1.1.0)
2. `docs/store/Package.appxmanifest` → `Version="1.1.1.0"`
3. PyInstaller build + `make_msix.ps1`
4. Partner Center → güncelleme yükle (aynı sürüm numarası tekrar kullanılamaz)
