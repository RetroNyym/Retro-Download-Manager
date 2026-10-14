# Retro+ Tarayıcı Modülü (IDM benzeri uzantı)

Chrome/Edge uzantısı: tarayıcıda başlayan indirmeleri **iptal eder**, adresi
yerel Retro+ köprüsüne (`http://127.0.0.1:8877/add?url=...`) gönderir; dosyayı
Retro+ Download Manager'ın kendi motoru indirir, arayüzde ve klasöründe görünür.
Ek sunucu/kurulum gerekmez — programın hazır `Tarayıcı köprüsü` özelliği
kullanılır (Ayarlar → Genel → köprü açık kalmalı, port varsayılan 8877).

## Kurulum (makine başına, 1 dakika)

1. Retro+ Download Manager açık olsun (köprü çalışıyor).
2. Chrome/Edge → `chrome://extensions` (Edge: `edge://extensions`).
3. Sağ üstte **Geliştirici modu**'nu aç.
4. **Uzantıyı yükle** → bu klasörü seç (`tarayici\uzanti`).
5. Rozetten yeşil/onay görünürse hazır; kırmızı `!` ise program kapalıdır.

Uzantı portu kendisi tarar (8877–8899); Ayarlar'da köprü portunu
değiştirdiyseniz "Köprüyü yenile" ile yeniden bulur.

## Davranış

- `http/https` her indirme yakalanır; `chrome-extension://` ve uzantının
  kendi tetikledikleri hariç.
- Yakalanan URL `Retro+'a aktarıldı` olarak popup geçmişine düşer.
- Rozet: `!` köprü yok, sayı = aktif indirme, `+` köprü hazır.
- "İndirmeleri Retro+'a aktar" anahtarı ile tamamen kapatılabilir.

## Sınırlar (v1.0)

- Köprü `/add` yalnızca URL alır; site çerezleri/referer aktarılmaz
  (girişli sitelerde indirme Retro+'ın kendi oturumuyla olur).
- Yakalama anında Chrome dosyanın birkaç baytını yazmış olabilir; iptal
  edilir, dosyayı Retro+ sıfırdan indirir.

## Test

`%TEMP%\opencode\retro_test.py` uçtan uca testi: çalışan Retro+ köprüsü +
Edge (`--load-extension`) + CDP ile indirme tetikleme + sha256 doğrulama.
Not: stabil Google Chrome komut satırından `--load-extension` kaldırdı;
elle "Uzantıyı yükle" yine çalışır. Test Edge ile yapılır.
