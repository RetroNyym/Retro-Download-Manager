<p align="center">
  <img src="assets/banner.png" alt="Retro+ Download Manager" width="100%">
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white">
  <img alt="Lisans" src="https://img.shields.io/badge/Lisans-MIT-yellow.svg">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey">
  <img alt="Parça" src="https://img.shields.io/badge/indirme-32%20par%C3%A7a-brightgreen">
  <img alt="Test" src="https://img.shields.io/badge/test-82%20kontrol-blue">
</p>

**Retro+ Download Manager**, Internet Download Manager'ın indirme becerilerini bağımsız bir Python
modülüne taşıyan bir araçtır: çok parçalı (segmentli) indirme, duraklat/devam, kuyruk, zamanlama,
otomatik dosya kategorileri, bağlantı grabber'ı, tarayıcı köprüsü ve Türkçe Tkinter arayüzü.

Modül hem **masaüstü uygulaması** hem de **Python kütüphanesi** olarak kullanılabilir — GUI olmadan
`DownloadManager` sınıfını doğrudan kendi programınıza bağlayabilirsiniz.

> Depo adı `Retro-Download-Manager` (GitHub boşluk ve `+` karakterini depo adında kabul etmez),
> ürün adı **Retro+ Download Manager**'dır.

---

## IDM ile Karşılaştırma

| IDM yeteneği | Retro+ | Not |
| --- | :---: | --- |
| Çok parçalı indirme (paralel segment) | ✅ | Varsayılan 8, en fazla 32 parça |
| Duraklat / devam (her noktadan) | ✅ | 206 Range ile ilerleme dosyasına yazılır |
| Bilinmeyen boyutlu / `Range` desteklemeyen sunucu | ✅ | Tek parça + hazır olan kadar parçalı kademelenme |
| Çelişkili/eksik `Content-Length` çözümü | ✅ | `HEAD` + `Range` teyidi, uzunluk uyuşmazlığında parça sadeleştirilir |
| Zamanlanmış / tekrarlayan indirme | ✅ | Kuyruk + saatlik/günlük planlayıcı |
| Duraklatma sırasında bitiş eşiği ve hız sınırı | ✅ | KB/sn sınırı, isteğe bağlı kota |
| Kategori kuralı (video/müzik/arşiv...) | ✅ | Uzantı + anahtar kelime, eşleşene göre klasöre ayırır |
| Tarayıcı bağlantı grabber'ı | ✅ | Pano izleme + yerel HTTP köprüsü (`/links`, `/add`) |
| Site şifresi / çerez desteği | ⚠️ | Başlıklar ve tanımlar üzerinden (`headers`/`cookies`) |
| MMS/RTSP, FTPS'te özel tunnel | ❌ | HTTP(S), HTTP range, FTP/FTPS desteklenir |
| Site entegrasyonu (site yöneticisi) | ❌ | Yerel köprü ve pano ile ikame edildi |

---

## Kurulum

```bash
git clone https://github.com/RetroNyym/Retro-Download-Manager.git
cd Retro-Download-Manager
python -m pip install -r requirements.txt
```

Tek çalışma zamanı bağımlılığı `requests`'tir; `tkinterdnd2` kuruluysa sürükle-bırak eklenir.

## Çalıştırma

```bash
python -m download_manager        # GUI
baslat_idm.bat                    # Windows kısayolu
```

## Kütüphane olarak kullanma

```python
from download_manager import DownloadManager

mgr = DownloadManager(max_tasks=4)          # ayarlar veri klasörüne yazılır
mgr.add(["https://ornek.com/dosya.zip", "https://ornek.com/bolum-01.mkv"],
        segments=16,                        # parça sayısı (1..32)
        speed_limit=2048)                   # KB/sn, None = sınırsız
mgr.start()                                 # kuyruk çalışır
```

Durum, ilerleme ve sonuçlar `mgr.tasks` üzerinden okunabilir; uygulama yeniden başlatıldığında
yarım kalan indirmeler `download_manager/data/state.json` üzerinden kaldığı yerden devam eder.

## Tarayıcı köprüsü

Adres çubuğuna yazılan linkleri arayüze taşımak için yerel köprü sunucusu kullanılır
(`http://127.0.0.1:8877`, yalnızca makinenize bağlıdır):

| Uç | Ne yapar |
| --- | --- |
| `GET /links` | pano/grabber'da toplanan linkleri JSON olarak verir |
| `GET /add?url=...` | linki kuyruğa ekler |
| `GET /status` | kuyruk özeti |

Tarayıcıya ekleyebileceğiniz imleç (bookmarklet):

```javascript
javascript:(function(){fetch('http://127.0.0.1:8877/add?url='+encodeURIComponent(location.href))})()
```

## Mimari

| Dosya | Görev |
| --- | --- |
| `download_manager/engine.py` | çok parçalı indirme motoru (HTTP/FTP, duraklat/devam, yeniden deneme, ayna URL) |
| `download_manager/manager.py` | kuyruk, zamanlayıcı, kategoriler, grabber, köprü, geçmiş, ayarlar |
| `download_manager/gui.py` | Tkinter arayüz (indirme listesi, segment görünürlüğü, diyaloglar) |
| `download_manager/util.py` | kategori tespiti, biçimlendirme, dosya yardımcıları |
| `download_manager/notify.py` | tamamlanma / hata sesli bildirimi |
| `tests/` | 82 kontrol (motor, FTP, köprü, yeniden başlatma, GUI) |

## Testler

| Dosya | Kapsam | Kontrol |
| --- | --- | ---: |
| `tests/test_download_manager.py` | çok parçalı, `Range` yok, bilinmeyen boyut, duraklat/devam, iptal, kuyruk, grabber, kalıcılık | 37 |
| `tests/test_restart_resume.py` | kapanınca duraklat → açılınca devam + gerçek internet indirmesi | 8 |
| `tests/test_ftp.py` | FTP parça/duraklat/iptal (`pip install pyftpdlib`) | 10 |
| `tests/test_bridge.py` | köprü uçları (`/add`, `/links`, `/status`) | 7 |
| `tests/test_gui.py` | diyaloglar ve arayüz (ekran/`tkinter` gerektirir) | 20 |

```bash
python tests/test_download_manager.py
python tests/test_restart_resume.py
python tests/test_bridge.py
python tests/test_ftp.py        # pip install pyftpdlib
python tests/test_gui.py        # grafik oturum gerekir
```

Lint: `python -m pyflakes download_manager`.

## Sınırlamalar

- Tarayıcı entegrasyonu eklenti yerine **yerel köprü + pano izleme** ile sağlanır.
- Sunucu `Range` desteklemiyorsa paralel segment kullanılmaz (tümü doğrudan tamamlanır).
- `FTP over explicit TLS` (FTPS) deneme amaçlıdır; bazı sunucularda `MLSD` yerine `NLST`'ye düşer.
- Saloon / çoklu parça her zaman sunucunun izin verdiği kadar hızlanır; hız sınırı istemci tarafıdır.

## Lisans

[MIT](LICENSE) © RetroNyym
