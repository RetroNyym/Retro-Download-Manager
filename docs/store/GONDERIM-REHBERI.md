# Microsoft Store gönderim rehberi — Retro+ Download Manager

Hazır durum: exe (`dist\RetroDownloadManager.exe`), manifest + paketleme
scripti (`docs/store/`), gizlilik politikası, mağaza metinleri, ekran
görüntüleri (`docs/screenshots/`) mevcut. Eksik olan tek şey **senin yapman
gereken hesap/ kimlik adımları**.

## A. Geliştirici hesabı (sen yapacaksın — ~10 dk, ücretsiz)

1. <https://storedeveloper.microsoft.com> → **Get started for free**.
2. **Individual developer** seç (bireysel hesap ücretsiz; $19 ücreti 2025'ten
   beri kalktı, kredi kartı istenmez).
3. Microsoft hesabıyla giriş → **kimlik kartı + selfie** doğrulaması
   (telefonda, ışıklı ortamda; dakikalar sürer).
4. Profili tamamla → **Partner Center dashboard** açılır.

> Not: Bireysel hesap kişisel adınla yayımlanır; "Retro+" gibi kurumsal ad
> istiyorsan **Company account** (~$99, iş doğrulaması) gerekir. V1 için
> bireysel + yayıncı adı yeterli.

## B. MSIX paketi üret (makinede — benim yapabileceğim kısım hazır)

```powershell
# 1) exe'yi (yeniden) üret — kod MSIX uyumu için güncellendi
python -m PyInstaller --noconfirm --onefile --windowed --name RetroDownloadManager `
    --add-data "assets;assets" --add-data "whatsapp_listener;whatsapp_listener" `
    --add-data "tools;tools" baslat_exe.py

# 2) MSIX paketle (MakeAppx gerekir — yoksa aşağıya bak)
powershell -ExecutionPolicy Bypass -File docs\store\make_msix.ps1 `
    -Publisher "CN=PartnerCenterKimligin" -DenemeSertifikasi
```

- **MakeAppx yoksa:** Visual Studio Installer → *Workloads* → **Windows
  application development** (veya yalnız *Windows 11 SDK*) kur; makeappx.exe
  `C:\Program Files (x86)\Windows Kits\10\bin\<sürüm>\x64\` altına gelir,
  script otomatik bulur.
- Script: `dist\RetroDownloadManager.msix` üretir + geçici logoları koyar
  (gerçek logoyla değiştir — `logo-uyarisi.md` bak, Store geçici logoyu
  reddedebilir; mevcut `assets/` ikonundan türetilebilir).
- `-Publisher` **mutlaka** Partner Center'daki Publisher kimliğinle aynı olmalı
  (hesap sayfasında görünür, `CN=...` formatında).

## B2. Yerel kurulum testi (doğrulandı — 13.10.2026)

```powershell
# 1) Paket + deneme sertifikası (yukarıdaki make_msix komutu gibi)
powershell -ExecutionPolicy Bypass -File docs\store\make_msix.ps1 -DenemeSertifikasi

# 2) Test sertifikasını MACHINE store'lara ekle (admin/UAC penceresi çıkar —
#    AppX Deployment servisi LocalMachine okur; CurrentUser YETMEZ, hata 0x800B0109)
certutil -f -addstore Root %TEMP%\rddm_trust.cer
certutil -f -addstore TrustedPublisher %TEMP%\rddm_trust.cer

# 3) Kur + doğrula
Add-AppxPackage -Path dist\RetroDownloadManager.msix
Get-AppxPackage -Name RetroPlusDownloadManager   # PackageFullName görünmeli

# 4) magnet: protokol aktivasyonu — uygulama açılmalı (PID not al)
Start-Process "magnet:?xt=urn:btih:<testhash>&dn=Test"

# 5) Temizlik
Stop-Process -Name RetroDownloadManager -Force -EA SilentlyContinue
Remove-AppxPackage -Package (Get-AppxPackage RetroPlusDownloadManager).PackageFullName
```

Doğrulanan sonuçlar: kurulum ✓, `HKCU\Software\Classes\magnet` `URL Protocol`
kaydı ✓, magnet URI ile süreç başlatma ✓, kaldırma ✓.
**Dikkat:** uygulama kapanışında `durdur` aria2'yi kapatır — masaüstü
uygulamasının aynı porttaki (6800) arka plan örneği de kapanır; uygulama yeniden
açılınca kendi örneğini otomatik başlatır. `Remove-AppxPackage` sonrası test
sertifikalarını `certutil -deleteStore Root <thumbprint>` ile temizleyebilirsin.

## C. Store'a gönder (Partner Center — sen yapacaksın)

1. Dashboard → **Apps & games → + New app** → Platform **Windows**, tip **PC**.
2. **Packages** adımında `dist\RetroDownloadManager.msix` yükle.
3. **Properties**:
   - Kategori: *Utilities & tools*; fiyat: ücretsiz.
   - Gizlilik politikası URL'si: `docs/store/gizlilik-politikasi.md` metnini
     herkese açık bir yere koy (GitHub repo readme / GitHub Pages) → URL'yi gir.
     *Zorunlu:* Win32/Desktop Bridge ürünleri her zaman gizlilik politikası
     ister (Store politikası 10.5.1).
   - Destek URL'si + iletişim e-postası.
4. **Age ratings**: IARC anketini doldur (notlar:
   `docs/store/magaza-metni.md` → "Yaş derecelendirmesi"). Beklenen: 3+.
5. **Store listing**: metinler `docs/store/magaza-metni.md`'den;
   görseller `docs/screenshots/` (≥1366×768, en az 1, önerilen 3+).
6. **Notes for certification**: aria2 (GPLv2+) kaynak notu +
   magnet test ipucu (metin dosyasındaki "Gönderim notları").
7. **Submit for review** → tipik 1–3 iş günü onay; reddedilirse nedenle
   düzeltip tekrar gönder.

## D. Yayımdan sonra

- `tools\magnet_bagla.ps1` gereksiz: MSIX manifesti `magnet:` protokolünü
  kendisi bağlar (`Application > Extensions > uap:Extension[windows.protocol] >
  uap:Protocol`; uygulama çıplak `magnet:?…` argümanını da kabul eder).
- Veri klasörü Store sürümünde `%LOCALAPPDATA%\RetroDownloadManager\data`
  (WindowsApps'a yazma engeli nedeniyle otomatik).
- Sürüm atlaması: `__version__` + manifest `Version` (a.göre
  `magaza-metni.md` → "Sürüm güncelleme akışı").

## Diğer dağıtım kanalları (düşük efor → yüksek erişim)

| Kanal | Durum | Ne gerekir |
| --- | --- | --- |
| **GitHub Releases** | En hızlısı | Tag + `RetroDownloadManager.exe`/zip yükle; README'ye buton |
| **winget** (`winget-pkgs`) | Hazır altyapı | `docs/submission/KONTROL-LISTESI.md` zaten yazıldı: manifest yolu + exe şartı karşılanıyor; PR açılır (yayıncı imzası/URL yeterli) |
| **Kendi site** | Sitede indirme butonu | exe'yi siteye koy; mevcut indirme altyapısıyla doğrudan dağıtım |
| **itch.io** | Doğrudan yükleme | Hesap aç → upload exe/zip; kategori "Software" |
| **Scoop / Chocolatey** | Paket yöneticileri | scoop bucket veya choco package scripti (`install` + `checksum`) |
| **PortableApps** | Niş | PortableApps formatı (launcher + `*.paf.exe`) |
| SourceForge / Softpedia | Submission formu | Daha uzun inceleme süreçleri; mevcut engeller nedeniyle öncelik düşük |

**Önerilen sıra:** Store başvurusu (onay beklenebilir) paralelinde **GitHub
Releases + winget PR** ile bugün yayına başla; itch.io hesabın açılırsa ekle.
