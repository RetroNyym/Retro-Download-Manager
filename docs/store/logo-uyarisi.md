# Logo uyarısı (Store gönderiminden önce)

`make_msix.ps1` pakete **geçici** logolar basar (koyu zemin + "R+" yazısı).
Bunlar yerel test için yeterli, **mağaza incelemesinde kaba görünebilir**.

Gerçek logoyla değiştir:

- Kaynak: repo `assets/` klasöründeki uygulama ikonu (`icon.ico` vb.).
- Gereken boyutlar (docs/store/Package.appxmanifest'teki yollar):

| Dosya | Boyut |
| --- | --- |
| `StoreLogo.png` | 50×50 |
| `Square44x44Logo.png` | 44×44 (veya 256×256'ya ölçekle) |
| `Square150x150Logo.png` | 150×150 |
| `Wide310x150Logo.png` | 310×150 |
| `SplashScreen.png` | 620×300 |

Python ile üretme örneği:

```python
from PIL import Image
img = Image.open("assets/icon.ico")  # veya .png
img.resize((150, 150), Image.LANCZOS).save("docs/store/assets/Square150x150Logo.png")
```

Stage klasörü her çalıştırmada yeniden oluşur (`%TEMP%\rdm_msix_stage`) —
gerçek logoları üretimden önce `docs/store/assets/` altına koyup scriptin
oradan kopyalamasını bekleyebilir veya pack sonrası stage'e elle bırakabilirsin.
