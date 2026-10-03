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
| Sürüm | 1.0.0 |
| Lisans | MIT (ücretsiz, açık kaynak) |
| Fiyat | Ücretsiz — reklamsız, deneme süresi yok |
| İşletim sistemi | Windows 10/11, Linux, macOS |
| Gereksinim | Python 3.11+ ve `requests` (video için isteğe bağlı `yt-dlp` + `ffmpeg`) |
| Kategori | İnternet › İndirme Yöneticileri (yoksa: Sistem Araçları) |
| Ana sayfa | https://retro-download-manager.netlify.app |
| Kaynak kod | https://github.com/RetroNyym/Retro-Download-Manager |
| İndirme (ana) | https://retro-download-manager.netlify.app/download/Retro-Download-Manager-v1.0.0.zip |
| İndirme (ayna) | https://github.com/RetroNyym/Retro-Download-Manager/releases/download/v1.0.0/Retro-Download-Manager-v1.0.0.zip |
| Dosya boyutu | 266 KB (ZIP) |
| SHA-256 | `73b50af2d18455eb4ca0d394b36138d66e5a8c83c34315b3867f80a05982366b` |
| İletişim | `216476870+RetroNyym@users.noreply.github.com` |
| Ekran görüntüsü | `docs/screenshots/` altındaki 4 PNG |

---

## 2. Kısa açıklamalar (karakter sınırına göre)

**≤100 karakter (en kısa):**

```
Çok parçalı, hızlı indirme yöneticisi — duraklat/devam, kuyruk, zamanlama, video linkleri
```

**≤160 karakter (arama sonucu / meta):**

```
Retro+ Download Manager: 32 parçaya kadar paralel indirme, duraklat/devam, kuyruk,
zamanlama, otomatik kategoriler ve web sayfası/playlist çözümleme. Ücretsiz, MIT.
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
Retro+ Download Manager, Python ile yazılmış, Türkçe arayüzlü, ücretsiz ve açık kaynak
(MIT lisanslı) bir indirme yöneticisidir. Kurulum gerektirmez, reklam ve deneme süresi
yoktur; tek çalışma zamanı bağımlılığı "requests" paketidir.

Özellikler:
- 32 parçaya kadar paralel (segmentli) indirme; sunucu Range desteklemiyorsa tek parçaya
  otomatik düşer
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

Sistem gereksinimleri: Python 3.11 veya üzeri (Windows 10/11, Linux, macOS). Video ve
playlist için isteğe bağlı yt-dlp ve ffmpeg.

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

## 7. Sürüm 1.0.0 notları (TR)

```
- 32 parçaya kadar paralel indirme, duraklat/devam/iptal, kuyruk ve zamanlayıcı
- Web sayfası çözümleme: og:video, kaynak etiketleri, JSON-LD; medya yoksa net hata
- Playlist: YouTube vb. listeler tek görevden tüm videolara genişler; DASH'ta ffmpeg
  ile ses+video birleştirme
- Hızlı site butonları: YouTube, Instagram, X (Twitter), Facebook, TikTok, Vimeo
- Tarayıcı köprüsü + pano izleme, Site Grabber, FTP, ayna URL, hız sınırı,
  sesli bildirim
- 165 test kontrolü ve pyflakes temiz
```

---

## 8. Anahtar kelimeler / etiketler

```
indirme yöneticisi, indirme hızlandırıcı, download manager, ücretsiz program,
parça indirme, duraklat devam, kuyruklu indirme, video indirme, playlist indirme,
açık kaynak, MIT, Türkçe program, dosya indirme programı, FTP indirme
```

---

## 9. SSS — portalların sık sorduğu sorular

| Soru | Cevap |
| --- | --- |
| Kurulum gerektiriyor mu? | ZIP'i açıp `python -m download_manager` çalıştırılır; `baslat_gui.bat` Windows kısayoludur (CMD penceresi açılmaz), `baslat_gui.vbs` ile tamamen gizli açılır. |
| Kötü yazılım içerir mi? | Hayır; tek bağımlılık `requests`, kod MIT lisanslı ve açık kaynak. |
| Reklam/toolbar ekler mi? | Hayır, hiçbir şey kurmaz. |
| İnternetsiz çalışır mı? | İndirme için internet gerekir; arayüz ve yerel dosya işlemleri internetsiz çalışır. |
| Çıkarım/kurulum (installer) var mı? | Portable ZIP olarak dağıtılır; imzalı .exe kurucusu planlanmaktadır. |
| Fiyat? | Ücretsiz, deneme süresi yok, hesap gerekmez. |
| Destek? | GitHub Issues: https://github.com/RetroNyym/Retro-Download-Manager/issues |
