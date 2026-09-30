# Başvuru Kontrol Listesi

Bu dosya **durum takibi**dir: hangi portaala ne zaman başvuruldu, sonuç ne oldu.
Metinler `metinler-tr.md` / `metinler-en.md`, e-posta şablonları
`e-posta-sablonlari.md` içinde. URL'ler 30.09.2026'da doğrulandı.

Durum işaretleri: `⬜` başlanmadı · `🟨` başvuru yapıldı · `✅` yayında · `❌` reddedildi/atlandı

---

## A. Global portallar

| # | Portal | Başvuru yolu (doğrulanmış) | Hesap | Onay | Durum | Tarih | Not |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **SourceForge** | https://sourceforge.net/p/add_project (eski `projects/create` → `create/`'ye yönlendiriyor) | Evet | Otomatik + güvenlik taraması | 🟨 | 2026-09-30 | ⚠️ Giriş + e-posta doğrulaması **tamam**, form doldu (`Retro+ Download Manager` / `retro-download-manager`, Git+Downloads+Tickets, Terms ✔). Ancak **telefon doğrulaması zorunlu** ve `POST /p/verify_phone` **Cloudflare 403** döndürüyor (kontrol edilen iki tarayıcıda da) → SMS gönderilemiyor. Engeli destek bildirimi/sonraki oturum bekliyor; sonra Create + ZIP yükleme. GitHub OAuth içe aktarıcı da bu ağdan erişilemez (`ERR_TUNNEL_CONNECTION_FAILED`) |
| 2 | **MajorGeeks** | https://www.majorgeeks.com/files/submit.html | Hayır | Manuel editör | ⬜ | | Download URL: **GitHub Release** (versiyonlu, kalıcı); yeni sürümde "Report New Version" |
| 3 | **Softpedia** | https://www.softpedia.com/ → Submit formu | Hayır | Manuel editör | ⬜ | | Internet › Download Managers; Freeware + open source; PAD de kabul edilir |
| 4 | **FossHub** | https://www.fosshub.com/ → Contact/Submit | Evet | Manuel (FOSS şartı) | ⬜ | | MIT + GitHub linki zorunlu; malware taraması |
| 5 | **itch.io** | https://itch.io/signup → yeni proje → Upload file | Evet | **Anında yayında** | ✅ | 2026-10-01 | 🟢 **Yayında: https://retronym.itch.io/retro-download-manager** (hesap **Retronym**). Type: Downloadable, Pricing: **No payments** (bağış yok, doğrudan indirme). Kapak görseli + **4 ekran görüntüsü** + **ZIP yüklendi** (260 KB, `Retro+ Download Manager v1.0.0`, p_win/mac/linux ✔, tür: Executable). Açıklama (EN,1787 karakter, kurulum/özellik/kaynak/SHA-256) + **10 etiket** + Visibility **Public** → kaydedildi (POST /game/edit/5079471 →200) |
| 6 | **Softonic** | https://publishing-center.softonic.com/home (Publishing Center) | Evet | Self-servis, **ücretsiz yayın** | ⬜ | | Eski `developer.softonic.com/register` ölü; giriş yap → ad/açıklama/sürüm/ekran görüntüsü |
| 7 | **AlternativeTo** | https://alternativeto.net/add/ | Evet | Manuel editör (1 gün – 1 hafta) | ⬜ | | ⚠️ Uygulamanın **İngilizce** listelenmesi şart; `metinler-en.md` kullanılır |
| 8 | **Uptodown** | https://en.uptodown.com/developers-console | Evet | Self-servis, **ücretsiz** | ⬜ | | Windows/Mac/Android; Türkçe arayüz var ama gönderim konsolu EN; TR'de çok kullanılır |
| 9 | **UpdateStar** | PAD dosyası linki → **support@updatestar.com** (konu: `PAD file update`) | Hayır | Manuel | ⬜ | | Bilgi sayfası: https://client.updatestar.com/en/pad · Ücretsiz, hesap yok · PAD XML gerekli (bkz. §H) |
| 10 | **FileHippo** | Form **yok** → https://filehippo.com/info/contact/ → **contact@filehippo.com** | Hayır | Manuel editöryel | ⬜ | | Tek yol e-posta; reklam alanı ücretli, listeleme ücretsiz |
| 11 | **Archive.org** | https://archive.org/create/ → koleksiyon: Software | Evet | IA incelemesi | ⬜ | | Öncelikle tarihsel yazılım arşivi; modern uygulama için düşük öncelik |
| 12 | **PyPI** (kanal) | https://pypi.org/account/register/ → `twine upload dist/*` | Evet | Otomatik | ⬜ | | ⚠️ `download-manager` **alınmış**; **`retro-download-manager` boşta** — `pip install` kanalı olarak |

### Paket yöneticileri (form yok, hesap/PR gerektirir)

| # | Kanal | Ne yapılacak | Durum | Not |
| --- | --- | --- | --- | --- |
| 13 | **WinGet** | `microsoft/winget-pkgs` PR (`wingetcreate new`) | ⬜ | ⚠️ ZIP içinde `.py`/`.bat` var, çalıştırılabilir `.exe` yok → **önce PyInstaller ile portable exe** gerekir. Hazır: manifest yolu `manifests/r/RetroNyym/RetroDownloadManager/1.0.0/` |
| 14 | **Chocolatey** | `choco push` + https://community.chocolatey.org/ API key | ⬜ | nuspec: ProjectUrl/LicenseUrl zorunlu, **SHA-256 zorunlu**, indirme linki **GitHub Release** olmalı (SourceForge/FossHub linkleri yasak), her sürümde insan incelemesi |
| 15 | **Flathub / Snap** | flatpak manifest / snapcraft.yaml | ⬜ | Tkinter+Python için yapılabilir; Linux kullanıcıları için |

---

## B. Türkiye portalları

TR portallarının çoğu **editöryeldir**: açık "program yükle" formu yoktur →
e-posta/iletişim formu kullanılır. Hazır metin: `e-posta-sablonlari.md`.

| # | Portal | Başvuru yolu (doğrulanmış) | Onay | Durum | Tarih | Not |
| --- | --- | --- | --- | --- | --- | --- |
| 16 | **CHIP Online TR** | **Gerçek form:** https://www.chip.com.tr/iletisim → konu: **"Sitede yayınlanan içerik hakkında – Editöryal"** (Ad Soyad, e-posta, konu, 1000 kr. mesaj + reCAPTCHA) | Manuel editör | 🟨 | 2026-09-30 | Form dolduruldu (konu: "Sitede yayınlanan içerik hakkında", e-posta, başlık, 890 kr. metin) → **Ad Soyad + reCAPTCHA + Gönder** bekliyor. ⚠️ `chip.com.tr/indir` artık **404** → indirme portalı değil, **haber/inceleme** kanalı |
| 17 | **Donanım Haber** | **Form:** https://www.donanimhaber.com/iletisim · içerik bildir: https://www.donanimhaber.com/icerik-bildir · tanıtım: https://www.donanimhaber.com/tanitim | Manuel | 🟨 |2026-09-30 | "İçerik Bildir" formu dolduruldu (e-posta, bağlantı,768 kr. metin) → **Ad + reCAPTCHA + Bildir** bekliyor. Ayrıca **en hızlı organik görünürlük:** forum konusu → https://forum.donanimhaber.com/ (Diğer Yazılım) |
| 18 | **Tamindir** | Footer **"UYGULAMA/OYUN EKLE VE TANIT"** → gerçek form: **https://www.tamindir.com/sayfa/iletisim/** (`kurumsal.tamindir.com/iletisim/` buna yönlendiriyor) | Manuel editör | 🟨 |2026-09-30 | Form dolduruldu (e-posta, konu,866 kr. metin) → **Ad + (Telefon) + reCAPTCHA + Gönder** bekliyor; sürüm+link mesajda yazılı |
| 19 | **Webtekno** | https://www.webtekno.com/iletisim (departman: **İçerik Departmanı**) | Manuel editör | 🟨 |2026-09-30 | Form dolduruldu (e-posta, başlık,840 kr. metin) → **Ad + reCAPTCHA + Gönder** bekliyor; "Uygulama/Yazılım" kategorisi |
| 20 | **indir.com** | Program formu **yok** → https://www.imza.com/tr/iletisim/ | Manuel | ⬜ | | Form aslında SEO ajansının iletişim formu |
| 21 | **Gezginler** | Program ekleme formu **yok** → https://www.gezginler.net/iletisim/ (form, yalnız kendi içeriği hakkında yanıt veriyor) | Editör listelemesi | ⬜ | | ⚠️ Dünyanın en bilinen TR indirme sitesi ama **self-servis yok**; hedef kategori: https://www.gezginler.net/indir/internet/indirme-yoneticileri/ |
| 22 | **ShiftDelete.Net** | Form **yok** → **info@shiftdelete.net** · kategori: https://shiftdelete.net/yazilim | Manuel editör | ⬜ | | Haber/inceleme e-postası (`e-posta-sablonlari.md` §3) |
| 23 | **Technopat** | Form **yok** → https://www.technopat.net/yazilim/ (içerik) + forum | Editöryel | ⬜ | | Düşük öncelik |

### TR için önerilen diğer yollar

| # | Kanal | Yol | Durum | Not |
| --- | --- | --- | --- | --- |
| 24 | **DonanımHaber forum tanıtım konusu** | https://forum.donanimhaber.com/ → Diğer Yazılım | ⬜ | Ücretsiz, üyelik gerektirir; TR'de en hızlı organik görünürlük |
| 25 | **TR teknoloji editörleri** | `e-posta-sablonlari.md` §3 | ⬜ | Webtekno, ShiftDelete, Technopat, bültenler |
| 26 | **Microsoft Store (TR)** | https://partner.microsoft.com/tr-tr/microsoftstore/register | ❌ | **$19** tek seferlik + MSIX gerekir → Python/Tkinter için pratik değil; sadece not |

---

## C. Öncelik sırası (önerilen)

1. **itch.io** (anında yayında) + **SourceForge** (trafik)
2. **MajorGeeks, Softpedia, FossHub** (manuel ama hızlı)
3. **Softonic, Uptodown, AlternativeTo** (self-servis hesap)
4. **UpdateStar (PAD), FileHippo (e-posta)**
5. **TR: CHIP → DonanımHaber (form + forum) → Tamindir → Webtekno → ShiftDelete (e-posta)**
6. **Gezginler**: form yok — mevcut **kaynak kod + ana sayfa + GitHub** bilgisiyle editöre üstü kapalı hatırlatma (`e-posta-sablonlari.md` §1/§4)

---

## D. Başvuru öncesi zorunlu adımlar

- [x] **İletişim e-postası** belirlendi: `216476870+RetroNyym@users.noreply.github.com` (GitHub noreply — yeni adres açılınca `metinler-*.md`, `e-posta-sablonlari.md` ve bu dosyadaki alanları güncelleyin)
- [ ] `SHA-256` doğrulandı: `73b50af2d18455eb4ca0d394b36138d66e5a8c83c34315b3867f80a05982366b`
- [ ] GitHub Release `v1.0.0` linki çalışıyor (200) ✅
- [ ] Ana site linki çalışıyor (https://retro-download-manager.netlify.app → 200) ✅
- [ ] 4 ekran görüntüsü hazır ✅ (`docs/screenshots/`)
- [ ] 1280×800 isteyen portallar için ölçeklenmiş kopya üretildi
- [ ] Her portaala başvurudan önce şablondaki `[PORTAL ADI]` değiştirildi

## E. Her formda doldurulacak alan şablonu

Kaynak: `metinler-tr.md` §1 / `metinler-en.md` §1

```
Program adı : Retro+ Download Manager
Sürüm       : 1.0.0
Lisans      : MIT (ücretsiz)
Kategori    : Internet > Download Managers
İşletim sistemi: Windows 10/11, Linux, macOS (Python 3.11+)
Ana sayfa   : https://retro-download-manager.netlify.app
Kaynak kod  : https://github.com/RetroNyym/Retro-Download-Manager
İndirme     : https://retro-download-manager.netlify.app/download/Retro-Download-Manager-v1.0.0.zip
Ayna        : https://github.com/RetroNyym/Retro-Download-Manager/releases/download/v1.0.0/Retro-Download-Manager-v1.0.0.zip
Boyut       : 266 KB
SHA-256     : 73b50af2d18455eb4ca0d394b36138d66e5a8c83c34315b3867f80a05982366b
Ekran görüntüsü: docs/screenshots/ (4 PNG)
İletişim    : 216476870+RetroNyym@users.noreply.github.com
```

## F. Takip

- [ ] Başvurusu yapılan portallar **7–10 gün** sonra kontrol edildi; yanıt yoksa **bir kez** takip (`e-posta-sablonlari.md` §4)
- [ ] Yayınlanan her portala konan linkler aynı mı? (ZIP + ana sayfa + GitHub)
- [ ] İndirme sayıları GitHub Releases sayfasından aylık not edildi

## G. Yeni sürüm çıktığında

- [ ] GitHub tag + Release + ZIP
- [ ] `download/` klasörü + `indir.html` linki
- [ ] SHA-256 güncelle (`SUBMISSION.md` + `metinler-*.md`)
- [ ] Site deploy (Netlify + Cloudflare + GitHub Pages)
- [ ] `python tools/shots.py` (arayüz değiştiyse)
- [ ] SourceForge → Add Release; MajorGeeks → Report New Version; UpdateStar → yeni PAD
- [ ] Yayınlanan portallara kısa "yeni sürüm" e-postası (`e-posta-sablonlari.md` §5)

## H. UpdateStar için PAD dosyası

UpdateStar **yalnızca PAD (Portable Application Description) XML** kabul ediyor:
dosyayı bir web adresinde barındırıp linkini `support@updatestar.com` adresine
yolluyorsunuz (konu: `PAD file update`; ürüne ait ad, yayıncı adı ve UpdateStar
URL'sini de ekleyin).

- [ ] PAD dosyası oluşturuldu — resmî şema (PAD 4.00) kapandığı için iki yol var:
  1. UpdateStar'ın önerdiği editörle doldurun: https://xml-notepad.updatestar.com/
     (`metinler-tr.md` §1–§5 alanları doldurmaya yeter)
  2. Ya da doğrudan `metinler-en.md` özetini e-postaya yapıştırıp "PAD dosyam yok,
     ekteki bilgilerle listelemenizi rica ediyorum" deyin
- [ ] PAD dosyası siteye yüklendi (`docs/pad.xml` → örn. `…/docs/pad.xml`) ve linki e-postaya kondu
