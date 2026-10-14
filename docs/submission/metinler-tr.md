# Başvuru Metinleri — Türkçe

Bu dosya, Türkçe yayın yapan portallara (Gezginler, Tamindir, CHIP, ShiftDelete,
Donanım Haber vb.) yapılacak başvurularda **kopyala-yapıştır** için hazırlanmıştır.
İngilizce metinler için: `metinler-en.md`.

> **İletişim e-postası:** şu an `216476870+RetroNyym@users.noreply.github.com`
> kullanılıyor (GitHub noreply — hesabınızın bağlı olduğu adrese iletilir). Kendi
> adresiniz açıldığında bu dosyadaki tabloyu ve şablonları güncelleyin. Ek kanal:
> `https://github.com/RetroNyym`

---

## 1. Temel alanlar (formlarda hep aynı)

| Alan | Değer |
| --- | --- |
| Program adı | Retro+ Download Manager |
| Sürüm | 1.2.0 |
| Lisans | MIT (ücretsiz, açık kaynak) |
| Fiyat | Ücretsiz — reklamsız, deneme süresi yok |
| İşletim sistemi | Windows 10/11 (x64); taşınabilir exe — Python gerekmez |
| Gereksinim | Exe sürümünde ek gereksinim yok (Python3.11+ yalnız kaynak için; video için isteğe bağlı `ffmpeg`) |
| Kategori | İnternet › İndirme Yöneticileri (yoksa: Sistem Araçları) |
| Ana sayfa | https://retro-download-manager.netlify.app |
| Kaynak kod | https://github.com/RetroNyym/Retro-Download-Manager |
| İndirme (ana) | https://retro-download-manager.netlify.app/download/RetroDownloadManager-v1.2.0.zip |
| İndirme (ayna) | https://github.com/RetroNyym/Retro-Download-Manager/releases/download/v1.2.0/RetroDownloadManager-v1.2.0.zip |
| Dosya boyutu | 51.5 MB (ZIP; taşınabilir exe + aria2 torrent motoru) |
| SHA-256 | `7809cacfeb47da65231e98e13a986c028b00ce076ed60651e079c757bb6598e7` |
| İletişim | `216476870+RetroNyym@users.noreply.github.com` |
| Ekran görüntüsü | `docs/screenshots/` altındaki 4 PNG |

---

## 2. Kısa açıklamalar (karakter sınırına göre)

**≤100 karakter (en kısa):**

```
Çok parçalı indirme + torrent (aria2) ve magnet: desteği — duraklat/devam, kuyruk, zamanlama
```

**≤160 karakter (arama sonucu / meta):**

```
Retro+ Download Manager: 32 parçaya kadar paralel indirme + torrent (aria2) ve magnet:
desteği; duraklat/devam, kuyruk, zamanlama. Ücretsiz, MIT.
```

**≤250 karakter (sosyal / portal özeti):**

```
Retro+ Download Manager, 32 parçaya kadar paralel indirme, her noktadan duraklat/devam,
indirme kuyruğu ve zamanlayıcı, otomatik dosya kategorileri, site grabber, web sayfası ve
playlist çözümleme, FTP ve hız sınırı sunan ücretsiz (MIT) ve açık kaynak bir Türkçe
indirme yöneticisidir. Windows, Linux ve macOS'ta çalışır.
```

---

## 3. Uzun açıklama (portallar için)

```
Retro+ Download Manager, Türkçe arayüzlü, ücretsiz ve açık kaynak (MIT lisanslı) bir
indirme yöneticisidir. Windows için taşınabilir .exe sunulur (ZIP'ten çıkarıp
çalıştırın, Python gerekmez); kaynak sürüm Python 3.11+ ile Linux/macOS'ta da çalışır.
Reklam ve deneme süresi yoktur.

Özellikler:
- 32 parçaya kadar paralel (segmentli) indirme; sunucu Range desteklemiyorsa tek parçaya
  otomatik düşer
- Torrent indirme: yerleşik aria2 motoru; magnet ve .torrent dosyaları, duraklat/devam,
  kayıtlı işlerin otomatik geri yüklenmesi
- magnet: protokolü: tarayıcınızdan magnet bağlantısına tıklayın, uygulama otomatik
  açılıp kuyruğa ekler
- Her noktadan duraklat / devam / iptal; ilerleme diske yazılır, program kapansa bile
  kaldığı yerden devam eder
- İndirme kuyruğu ve eşzamanlılık sınırı; saatlik/günlük zamanlanmış indirmeler
- Otomatik kategoriler (Video, Ses, Program, Arşiv, Belge) ve klasöre ayırma
- Web sayfası çözümleme: og:video, <source> ve JSON-LD etiketlerinden medya adresi bulma
- Playlist desteği: YouTube vb. listeler tek görevden tüm videolara genişler, ses ve
  video (DASH) yt-dlp + ffmpeg ile tek dosyada birleştirilir
- Hızlı site butonları: YouTube, Instagram, X (Twitter), Facebook, TikTok, Vimeo
- Tarayıcı köprüsü (127.0.0.1:8877) ve pano izleme: bağlantıyı yapıştırın, kuyruğa
  otomatik eklenir
- Site Grabber: bir sayfayı tarayıp tüm medya bağlantılarını topluca kuyruğa ekler
- FTP/FTPS, ayna (mirror) URL, istemci tarafı hız sınırı, çerez/başlık desteği, sesli
  bildirim
- Kütüphane olarak da kullanılabilir: GUI olmadan DownloadManager sınıfını kendi
  programınıza bağlayabilirsiniz

Sistem gereksinimleri: Windows 10/11 (64 bit) — .exe sürümünde ek gereksinim yok.
Video ve playlist için isteğe bağlı ffmpeg. Kaynak sürüm: Python 3.11+.

Tamamen test edilmiş: 165 otomatik kontrol ve pyflakes temiz. Kaynak kod GitHub'da
açıkça incelenebilir.
```

---

## 4. Madde madde özellik listesi (kısa alanlar için)

- 32 parçaya kadar paralel indirme (HTTP Range)
- Her noktadan duraklat / devam / iptal — yeniden başlatınca kaldığı yerden
- İndirme kuyruğu + saatlik/günlük zamanlama
- Otomatik kategoriler ve klasör ayırma
- Web sayfası ve playlist linki çözümleme (yt-dlp + ffmpeg)
- Hızlı site butonları: YouTube, Instagram, X, Facebook, TikTok, Vimeo
- Site Grabber: sayfa tarama ve toplu kuyruğa ekleme
- Tarayıcı köprüsü + pano izleme ile bağlantıyı otomatik yakalama
- FTP/FTPS, ayna URL, hız sınırı, çerez/başlık, sesli bildirim
- Türkçe arayüz; MIT lisansı, ücretsiz, reklamsız

---

## 5. Sistem gereksinimleri (kısa form alanı)

```
Python 3.11+, Windows 10/11 · Linux · macOS
Zorunlu ek paket: requests (2 MB disk)
Opsiyonel: yt-dlp + ffmpeg (video/playlist için)
Ekran: 1024x640 ve üzeri
```

---

## 6. Ekran görüntüsü dosyaları

Portal yüklemelerinde bu sırayla ekleyin (başvuru formu görsel isterse 1–3 numaralılar):

| Dosya | Gösteren ekran | Kullanım |
| --- | --- | --- |
| `docs/screenshots/gui-downloads.png` | Ana pencere: canlı paralel indirme, segment çubukları, kategoriler | Ana ekran görüntüsü |
| `docs/screenshots/gui-add-link.png` | "İndirme Ekle" penceresi (parça, hız sınırı, zamanlama) | Özellik ekranı |
| `docs/screenshots/gui-grabber.png` | Site Grabber tarama sonucu | Özellik ekranı |
| `docs/screenshots/gui-settings.png` | Ayarlar penceresi (eşzamanlılık, kuyruk, köprü) | Opsiyonel |
| `docs/screenshots/gui-main.png` | Boş ana pencere (eski) | Yedek |

PNG, 1280×800 altındaki tüm portallara uygundur; daha büyük isteyen portallar için
görüntüleri 1280×800'e ölçekleyin.

---

## 7. Sürüm 1.2.0 notları (TR)

```
Yeni v1.2.0'da:
- Torrent indirme: yerleşik aria2 motoru; magnet ve .torrent dosyaları
- magnet: protokolü desteği — tarayıcınızdan magnet bağlantısına tıklayın,
  uygulama otomatik açılıp kuyruğa ekler
- Taşınabilir Windows .exe (Python gerekmez) — ZIP'ten çıkarıp çalıştırın
- MSIX paketi (Microsoft Store'a hazır, WACK sertifikasyonu PASS)
- aria2 yapılandırmasını içeren geliştirilmiş ayarlar penceresi
- Hata düzeltmeleri ve performans iyileştirmeleri

Önceki (v1.0.0):
- 32 parçaya kadar paralel indirme, duraklat/devam/iptal, kuyruk ve zamanlayıcı
- Web sayfası çözümleme: og:video, kaynak etiketleri, JSON-LD
- Playlist: YouTube vb. listeler tek görevden tüm videolara genişler
- Hızlı site butonları: YouTube, Instagram, X (Twitter), Facebook, TikTok, Vimeo
- Tarayıcı köprüsü + pano izleme, Site Grabber, FTP, ayna URL, hız sınırı
- 165 test kontrolü ve pyflakes temiz
```

---

## 8. Anahtar kelimeler / etiketler

```
indirme yöneticisi, indirme hızlandırıcı, download manager, ücretsiz program,
parça indirme, duraklat devam, kuyruklu indirme, torrent, aria2, magnet,
.video indirme, playlist indirme, açık kaynak, MIT, Türkçe program,
dosya indirme programı, FTP indirme
```

---

## 9. SSS — portalların sık sorduğu sorular

| Soru | Cevap |
| --- | --- |
| Kurulum gerektiriyor mu? | Hayır. ZIP'i açın, `RetroDownloadManager.exe` dosyasını çift tıklayın — Python gerekmez. |
| Kötü yazılım içerir mi? | Hayır; MIT lisanslı açık kaynak, tek bağımlılık `requests` (kaynak sürümde). |
| Reklam/toolbar ekler mi? | Hayır, hiçbir şey kurmaz. |
| İnternetsiz çalışır mı? | İndirme için internet gerekir; arayüz ve yerel dosya işlemleri internetsiz çalışır. |
| Torrent desteği var mı? | Evet; yerleşik aria2 motoru ile magnet ve .torrent dosyaları desteklenir. |
| magnet: linkleri açılır mı? | Evet; uygulama kurulduğunda `magnet:` Windows kaydı otomatik yapılır. |
| Fiyat? | Ücretsiz, deneme süresi yok, hesap gerekmez. |
| Destek? | GitHub Issues: https://github.com/RetroNyym/Retro-Download-Manager/issues |
