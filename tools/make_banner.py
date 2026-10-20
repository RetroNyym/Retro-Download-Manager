"""assets/banner.png — lüks şampanya-altını banner'ı üretir.

Anthracite zemin (#0F1115→#14171d), tek vurgu: şampanya-altını (#C9A962).
Çalıştırma:  python tools/make_banner.py
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "banner.png")

W, H = 1280, 420
BG_TOP = (13, 15, 19)
BG_BOTTOM = (20, 23, 29)
GOLD = (201, 169, 98)
GOLD_LIGHT = (230, 207, 154)
INK = (15, 17, 21)
TEXT2 = (168, 174, 191)
TEXT3 = (110, 118, 137)

FONTS = r"C:\Windows\Fonts"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def vertical_gradient(size, top, bottom) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(
            int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def gradient_text(text, fnt, size, top, bottom) -> Image.Image:
    """Dikey degrade dolgulu metin (alpha mask ile)."""
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).text((0, 0), text, font=fnt, fill=255)
    grad = vertical_gradient(size, top, bottom)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


def main() -> int:
    img = vertical_gradient((W, H), BG_TOP, BG_BOTTOM).convert("RGBA")

    # Sağda yumuşak altın parıltı
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 420, -80, W + 120, 380], fill=GOLD + (34,))
    gd.ellipse([W - 260, 160, W + 40, 460], fill=GOLD_LIGHT + (22,))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)

    # Sol: logo disk (altın halka)
    cx, cy, r = 108, 196, 62
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(26, 30, 38, 255),
              outline=GOLD, width=4)
    f_logo = font("segoeuib.ttf", 40)
    d.text((cx, cy - 14), "R+", font=f_logo, fill=GOLD_LIGHT, anchor="mm")
    f_logo2 = font("seguisb.ttf", 18)
    d.text((cx, cy + 26), "RETRO", font=f_logo2, fill=TEXT2, anchor="mm")

    # Başlık — altın dikey degrade
    f_title = font("seguisb.ttf", 54)
    title = "Retro+ Download Manager"
    tb = d.textbbox((0, 0), title, font=f_title)
    timg = gradient_text(title, f_title, (tb[2] - tb[0] + 4, tb[3] - tb[1] + 8),
                         GOLD_LIGHT, GOLD)
    img.paste(timg, (196, 78 - tb[1]), timg)
    d = ImageDraw.Draw(img)

    # Alt başlık
    f_sub = font("segoeui.ttf", 21)
    d.text((198, 158),
           "IDM yeteneklerine sahip çok parçalı indirme modülü · Python / Tkinter",
           font=f_sub, fill=TEXT2)

    # Rozetler (1px altın kenarlık — cam hissi)
    f_badge = font("segoeui.ttf", 15)
    badges = ("Python 3.11+", "32 parça indirme", "HTTP · HTTPS · FTP", "MIT Lisans")
    x = 198
    by0, by1 = 208, 246
    for label in badges:
        tw = d.textlength(label, font=f_badge)
        w = int(tw + 28)
        d.rounded_rectangle([x, by0, x + w, by1], radius=19,
                            outline=GOLD + (255,), width=1)
        d.text((x + w / 2, (by0 + by1) / 2), label, font=f_badge,
               fill=GOLD_LIGHT, anchor="mm")
        x += w + 12

    # Alt künye
    f_foot = font("consola.ttf", 15)
    d.text((198, 300), "github.com/RetroNyym/Retro-Download-Manager",
           font=f_foot, fill=TEXT3)

    # Alt altın aksan şeridi
    strip = vertical_gradient((W, 5), GOLD_LIGHT, GOLD)
    img.paste(strip, (0, H - 5))

    img.convert("RGB").save(OUT, "PNG")
    print("yazildi:", OUT, img.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
