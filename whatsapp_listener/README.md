# Retro+ WhatsApp PDF dinleyici

Yalnızca beyaz listedeki grup/kişilerden gelen PDF'leri indirir ve
`config.json` → `watchFolder` klasörüne bırakır; Retro+ Download Manager
oradan alıp hedef klasöre taşır.

## Kurulum (bir kez)

```powershell
cd whatsapp_listener
npm install
```

Node.js 18+ gerekir: https://nodejs.org (LTS)

## Kullanım

1. Retro+ → Ayarlar → **WhatsApp** sekmesi → izleme/hedef klasör + beyaz liste
2. **Dinleyiciyi başlat** → **QR'ı göster** → telefondan WhatsApp →
   Bağlı cihazlar → Cihaz bağla ile `qr.png` karekodunu okutun
3. Bağlantı kurulunca **Sohbetleri yükle** ile grup/kişileri beyaz listeye ekleyin

Dinleyici `session/` içinde oturumu saklar — bir daha QR gerekmez.
Beyaz listede olmayan hiçbir sohbetten dosya INDIRILMAZ (hem dinleyici hem
Python tarafında çift kontrol).

## Dosyalar

| Dosya | Görev |
| --- | --- |
| `config.json` | İzleme klasörü + beyaz liste (Ayarlar paneli yazar) |
| `chats.json` | Bağlantıdan sonra otomatik üretilen sohbet listesi |
| `status.json` | `starting / waiting_qr / connected / error` |
| `qr.png` | Karekod (üretilir, okutulunca silinir) |
| `session/` | WhatsApp oturumu (sakla, git'e ekleme) |
