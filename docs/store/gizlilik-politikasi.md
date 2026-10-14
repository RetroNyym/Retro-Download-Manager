# Gizlilik Politikası — Retro+ Download Manager

**Son güncelleme:** 13 Ekim 2026

Retro+ Download Manager ("uygulama"), indirme işlemlerinizi yerel cihazınızda
yöneten bir masaüstü uygulamasıdır. Bu politika, uygulamanın veri
davranışlarını açıklar.

## Topladığımız kişisel veri

**Yok.** Uygulama:

- Hesap oluşturmaz, giriş istemez.
- Kişisel veri (ad, e-posta, cihaz tanımlayıcısı vb.) toplamaz, iletmez,
  saklamaz.
- Analitik/reklam izleme kodu içermez.
- Hiçbir üçüncü tarafa telemetri göndermez.

## Yerel olarak saklanan veriler

Aşağıdaki veriler yalnızca **sizin cihazınızda** tutulur ve uygulama
kaldırıldığında silinir:

| Veri | Konum | Amaç |
| --- | --- | --- |
| Ayarlar | `data\settings.json` | Tercihleriniz (indirme klasörü, hız sınırı vb.) |
| İndirme kuyruğu | `data\queue.json` | Yarım kalan indirmeleri sürdürmek |
| Geçmiş/loglar | `data\indirme.log` | Yerel hata ayıklama |
| Torrent kayıtları | `data\torrents.json` | Yarım kalan torrentleri yeniden eklemek |

MSIX (Microsoft Store) sürümünde bu klasör
`%LOCALAPPDATA%\RetroDownloadManager\data` altında bulunur.

## Ağ erişimi

Uygulama yalnızca indirme amacıyla bağlanır:

- **HTTP/HTTPS/FTP indirmeleri:** belirttiğiniz adreslere istek atar.
- **BitTorrent (magnet/.torrent):** aria2 motoru (gömülü, ayrı süreç)
  eş/tohumlarla peer bağlantısı kurar; indirilen içeriğin kaynağı olan
  torrent izleyicilerine (tracker) anahtar/IP bilgisi gönderilebilir.
- **Güncelleme kontrolü:** yalnızca güncelleme kaynağı yapılandırılmışsa
  sürüm sorgusu yapar.

## Tarayıcı eklentisi (opsiyonel)

Retro+ tarayıcı eklentisini kurarsanız, eklenti yalnızca indirme bağlantılarını
yerel uygulamaya aktarır; gezinme geçmişinizi toplamaz veya saklamaz.

## Çocuklar

Uygulama 13 yaş altı çocuklardan bilerek veri toplamaz.

## İletişim

Gizlilikle ilgili sorular için: [Geliştirici iletişim adresi — gönderim öncesi
doldurun]

## Değişiklikler

Bu politika özellik eklendikçe güncellenir; sürümle birlikte yeniden yayımlanır.
