# Retro+ Download Manager — Dağıtım / Gönderim Paketi

Bu dosya, yazılım indirme sitelerine (SourceForge, FossHub, MajorGeeks,
Softpedia, itch.io) yapılacak başvurular için hazır metinlerdir. Sürüm
değişince yalnızca sürüm numarası ve linkleri güncelleyin.

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
| Ekran görüntüsü | docs/screenshots/gui-main.png |

## Kısa açıklama (≤100 karakter)

```
Çok parçalı, hızlı indirme yöneticisi — duraklat/devam, kuyruk, zamanlama, video linkleri
```

## Uzun açıklama (portallar için)

```
Retro+ Download Manager is a free, open-source (MIT) download manager written
in Python with a native Tkinter interface.

Features:
- Segmented downloading: up to 32 parallel connections with HTTP Range,
  automatic fallback to a single connection when the server does not support it
- Pause / resume / cancel at any point; progress is saved to disk, so downloads
  survive application restarts
- Download queue with concurrency limit, hourly/daily scheduled downloads
- Automatic categories (Video, Music, Archives, Programs, Documents) with
  custom rules
- Web page and playlist resolution: og:video/source tag scanning for page
  links, yt-dlp + ffmpeg integration for YouTube playlists and DASH streams
  (audio+video merged automatically)
- Quick site buttons: YouTube, Instagram, X (Twitter), Facebook, TikTok, Vimeo
- Browser bridge on 127.0.0.1:8877 + clipboard monitoring: paste a link and
  it is queued automatically
- Site Grabber: crawl a page and queue all media links with a depth filter
- FTP support, mirror URLs, client-side speed limit, voice notifications
- Usable as a Python library (DownloadManager class) without the GUI

Requirements: Python 3.11+ and the requests package. Optional for video and
playlists: yt-dlp and ffmpeg.

Turkish UI. Fully tested: 108 automated checks + pyflakes clean.
```

## Siteye göre başvuru notları

### 1) SourceForge (öncelikli — en çok trafik)
- https://sourceforge.net/projects/create/ → GitHub ile giriş
- Proje adı: `retro-download-manager`
- Kategori: `Internet/Networking` → `Download Managers`
- License: `MIT`
- Üretilecek dosyalar: Release ZIP + docs/screenshots/gui-main.png
- Kaynak link: GitHub reposu; ana sayfa link: Netlify adresi
- Release yükleme: Projects → Files → Add Release (`1.0.0` klasörü) → ZIP

### 2) itch.io (anında yayında)
- https://itch.io/signup → proje: `retro-download-manager`
- Type: `Downloadable` > `Tool` (oyun değil)
- Price: `No payment` / istenirse `Name your price`
- Dosya: aynı ZIP; screenshots: gui-main.png
- Açıklama: yukarıdaki kısa + uzun açıklama

### 3) FossHub (manuel onay, FOSS şartı)
- https://www.fosshub.com/ → Contact/Submit
- MIT lisans + GitHub linki şart; malware/paketsiz dağıtım
- Yükleme: Release ZIP

### 4) MajorGeeks (manuel inceleme)
- https://www.majorgeeks.com/files/submit.html
- Title: Retro+ Download Manager
- Version: 1.0.0
- Download URL: GitHub Release linki (versiyonlu, kalıcı)
- More Info URL: ana sayfa
- Category: Internet / Download Managers
- License: Freeware / Open Source (MIT)
- Ekran görüntüsü: docs/screenshots/gui-main.png
- Not: yeni sürümde "Report New Version" ile güncellenir

### 5) Softpedia (manuel inceleme)
- https://www.softpedia.com/ → Submit
- Aynı alanlar; kategori: Internet > Download Managers
- Freeware + open source olarak işaretlenir

## Sürüm güncelleme akışı (her yeni sürümde)

1. Repo'da yeni tag + GitHub Release oluşturun, ZIP'i asset olarak ekleyin
2. ZIP'i `download/` klasörüne kopyalayıp `indir.html` içindeki linki güncelleyin
3. Siteyi yeniden deploy edin (Netlify + Cloudflare + GitHub Pages)
4. SourceForge'a Files → Add Release
5. MajorGeeks'e "Report New Version"
