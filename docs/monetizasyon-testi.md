# Fikir Testi: "Ücretsiz v1 + Ömür Boyu $5'lik v2 Pro" (Open Core)

> **Tarih:** 01.10.2026 · **Kaynak:** canlı web araştırması (rakip fiyat sayfaları, itch.io ödeme
> dokümanı, Motrix/FDM pazar verisi) · **Kapsam:** yapı kararı (Yapı A) doğrulanması
> Satış kanalı henüz seçilmedi — bu doküman kanal seçiminden **önce** fikri sınamak için var.

---

## 1. Test edilen hipotez

> "v1'i ücretsiz/limitsiz dağıtalım, v2 çıktığında ömür boyu $5'ya satalım (ByClick gibi)
> — ama açık kaynak MIT'yi ve portal metinlerini bozmayalım (Yapı A = open core)."

---

## 2. Rakip fiyat verisi (01.10.2026, doğrudan fiyat sayfalarından)

| Ürün | Ücretsiz katman | Ödeme | Ömür boyu |
| --- | --- | --- | --- |
| **Internet Download Manager** | 30 gün deneme | $24.99 / 1 yıl | ~$25 (3 yıl güncelleme, sonra ücretli güncelleme) |
| **ByClick Downloader** | Var (kısıtlı) | ~$11,99–40 / yıl (kaynaklara göre farklı) | **$14,99–60** (kaynaklar çelişiyor) |
| **4K Video Downloader+** | Var | ~$15–24,95 / yıl | **$25–45** |
| **SnapDownloader** | Var | $19,95 / yıl | **$39,99** (1 PC) / $69,99 (aile) |
| **Leawo Video Downloader** | Var | $29,95 / yıl | — |
| **JDownloader2 (premium)** | Tam ücretsiz (reklamlı) | — | ~€12,99 (JD/premium) |

**Konum:** Piyasada ömür boyu **$15–60 bandı** hâkim. **$5, bandın alt sınırının1/3'ü** →
güçlü fiyat kancası ("herkesten ucuz") ama tek başına yetersiz (bkz. §5 Risk R3).

### Asıl rakip ücretliler değil, ücretsizler

| Ücretsiz & açık kaynak | Durum |
| --- | --- |
| **Motrix** | **22,5 milyon** Release indirmesi, **55,7k** GitHub yıldızı; aria2 tabanlı, BitTorrent/magnet, eklenti marketplace, tarayıcı eki, CLI, Docker |
| **Free Download Manager (FDM)** | Kurumsal, çok platformlu, tamamen ücretsiz |
| **JDownloader2** | Ağ/farm desteğiyle ücretsiz (reklamlı) |
| **Xtreme DM, Neat DM, DownThemAll, aria2, wget** | Hepsi ücretsiz |

→ Kullanıcı "para vermem" diyorsa **zaten** Motrix/FDM var. Ödeme havuzu: destek, sadelik,
özel özellik ve Türkiye yerelleştirmesi isteyen **dar ama niş** kitle.

---

## 3. itch.io satışının gerçek rakamları (ödeme dokümanından)

| Kalem | Değer |
| --- | --- |
| Satıcı komisyonu (itch) | varsayılan **%10** (sıfıra da çekilebilir) |
| İşlemci (PayPal/Stripe) | ~$0,30 + %2,9 |
| **$5 satıştan net** | **≈ $4,05** |
| Minimum ödeme eşiği | **$5** (altında çekilemez) |
| Ödeme yöntemi | PayPal **veya Payoneer** — Payoneer TR'de yaygın, **önce doğrulanmalı** (bkz. Risk R5) |

---

## 4. Puanlama: fikir testi sonucu ✅ **KOŞULLU GEÇER**

| Kriter | Puan | Gerekçe |
| --- | --- | --- |
| Fiyat cazibesi | ✅ | $5, rakip ömür boyu fiyatlarının (%60–90) altında |
| Portal/itibar zararı | ✅ | MIT v1.x olduğu gibi kalır — KONTROL-LISTESİ, itch.io ilanı, FossHub/MIT satırı **dokunulmaz** |
| Kanal işlevselliği | ✅ | itch.io paid ilanı sonraya ertelendi; teknik engel yok |
| Ölçek ekonomisi | 🟨 | Dönüşüm düşük → hacim şart (bkz. §6 senaryolar) |
| Korsan/delme dayanıklılığı | 🟨 | Python binary'si delinir; savunma: lisans anahtarı + **sunucu tarafı özellik** |
| "Ömür boyu" yükü | 🟨 | Sınırsız güncelleme garantisi verme — IDM modeli: **"ömür boyu lisans + N yıl güncelleme"** |
| Ücretsiz rakip duvarı | ❌/🟨 | Motrix/FDM bedava ve çok güçlü; ödeme gerekçesi **özellikte** değil fiyatda olamaz |

**Sonuç:** Fikir mantıklı; **karar verici unsur özellik ayrımı ve fiyat testi** (§7).

---

## 5. Riskler ve azaltıcılar

| # | Risk | Azaltıcı |
| --- | --- | --- |
| R1 | "v1 zaten tam ve MIT" → limitsiz sürüm dolaşımda kalır | Limit **koyma**; Pro'yu **yeni özellik** olarak sat (Yapı A) |
| R2 | Açık kaynakta limit kodu2 satırla silinir | Pro binary **kapalı** ya da savunmayı **sunucu tarafı** özelliğe taşı (uzaktan kumanda, bulut kuyruk) |
| R3 | $5 → "ucuz/kalitesiz" algısı | **Fiyat testi:** $5 / $9 / $12 varyantı (§7). Güven veren sinyaller: MIT çekirdek, açık kaynak, SHA-256, kod imzalı binary |
| R4 | "Ömür boyu güncelleme" taahhüdü | Lisans metni: *ömür boyu kullanım,2 yıl güncelleme dahil* (IDM standardı) |
| R5 | TR'den ödeme tahsilatı | **Payoneer doğrulaması yap**, PayPal'ı ikinci sıraya al; ilk satışta gerçek test |
| R6 | Portal incelemelerinde "önce bedava sonra ücret" algısı | Free katman **gerçekten tam** kalsın; Pro'yu **ekstra** olarak lanse et |
| R7 | Destek yükü ($5'lık ürüne $50'lık destek) | SLA: e-posta,48 saat, SSS/otomatik iade14 gün |

---

## 6. Gelir senaryoları (net ≈ $4,05/satış, itch varsayılan %10 ile)

| Senaryo | Aylık ziyaret | Dönüşüm | Aylık satış | Aylık net |
| --- | --- | --- | --- | --- |
| Kötü | 1.000 | %0,3 | 3 | **~$12** |
| Beklenen | 5.000 | %0,5 | 25 | **~$100** |
| İyi (TR kanalları + forum aktif) | 20.000 | %1 | 200 | **~$810** |

**Yorum:** $5 tek başına bir **iş modeli değil, ek gelir hattı**. Anlamlı gelir için hacim
(geliştirici forumları, YouTube/inceleme kanalları, TR portalları) şart. Bu yüzden fiyat
$5'te sabitlenmemeli — test edilmeli (§7 Faz0).

---

## 7. Ölçüm planı (kod yazmadan, ucuza)

### Faz0 — Fiyat/ mesaj testi (bu hafta, maliyet $0)
1. Netlify'a **tek sayfa** çıkar: `retro-download-manager.netlify.app/pro` — Pro özellik listesi
   + iki farklı buton metni varyantı (rastgele: **"Ömür boyu $5"** vs **"Ömür boyu $9"**).
2. Sayfa başlığı A/B: (A) "Ücretsiz sürüm + $5'lık Pro" (B) "Pro ile sınırsız kuyruk & uzaktan kumanda".
3. Buton → "Yakında" bekleme listesi (e-posta/itch takip).
4. **KPI:** ≥ **%3** buton tıklaması → yeşil · **%1–3** → sarı (fiyat metni/özellik gözden geçir) ·
   **< %1** → kırmızı (özellik kancası yanlış; Pro özelliklerini yenile).
5. Trafik kaynağı: yayınlanmış portallardaki **"Ana sayfa" linki + itch.io sayfasına devlog notu**.

### Faz1 — Gerçek talep ölçümü (1–2 hafta)
- itch.io'da **Pro ilanını gizli/coming soon** aç (ücretsiz ilana devlog: "Pro geliyor, takip et").
- **KPI:** ≥100 takip/e-posta → gerçek satışa geç.

### Faz2 — İlk satış (doğrulama)
- itch.io paid ilan, **ilk100 kullanıcıya %50 kod** → hedef **30 günde ≥20 satış**.
- ≥20 → kalıcı hattır, özellik yol haritasına geç · <5 → fiyat/özellik pivotu (§8).

### Karar ağacı
```
Faz0 %3+ ──► Faz1 ≥100 takip ──► Faz2 ≥20 satış ──► Pro yol haritası (v2.0)
   │                │                    │
   <%1          <%50 takip            <5 satış
   ▼                ▼                    ▼
Fiyatı/özellik    Pro'yu ertele,      Fiyatı $9'a çek
mesajını değiştir  v1.x büyüt         ya da Pro'yu iptal et
```

---

## 8. Önerilen Pro özellik listesi (Yapı A — free MIT'e dokunmadan)

**Ücretsiz (MIT, değişmez):** segmentli indirme32'ye kadar, kuyruk + zamanlayıcı, kategoriler,
site grabber, tarayıcı köprüsü, playlist, FTP, sesli bildirim — **hepsi serbest**.

**Pro (kapalı, $5 ömür boyu):**
1. **Uzaktan kumanda** — telefondan/web panelden kuyruğu yönet (sunucu tarafı, patch'lenemez)
2. **Kural motoru / otomasyon** — "şu siteden gelenleri şu klasöre, saat19'da, hız limitiyle"
3. **Sürüm kanalı + otomatik güncelleme** (masaüstü)
4. **Bulut/çoklu PC senkronu** — lisans1 PC değil,3 PC
5. **Eklenti API + toplu içe/dışa aktarma** (CSV/JSON kuyruk)
6. **Öncelikli destek** (48 saat) + **2 yıl güncelleme dahil**

---

## 9. Sonraki adım (karar bekliyor)

- [ ] Faz0 sayfasını **şimdi** çıkarayım mı? (A/B buton + bekleme listesi, ~30 dakika)
- [ ] Pro özellik listesinde kesinleştirme (hangileri v2.0'a?)
- [ ] Satış kanalı: itch.io / Lemon Squeezy / kendi mağaza (sonra)
- [ ] Payoneer/TR tahsilat doğrulaması (satıştan önce şart)
