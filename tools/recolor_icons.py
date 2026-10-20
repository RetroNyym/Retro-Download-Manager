"""Aksiyon ikonlarını lüks tek-ton stiline dönüştürür.

Kural:
- Şampanya-altını (#C9A962) yuvarlak chip plakası
- Anthracite (#0F1115) glyph
- site_* ikonları (marka renkleri) dokunulmaz

Kullanım:  python tools/recolor_icons.py
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

PLATE = (201, 169, 98, 255)    # #C9A962
INK = (15, 17, 21, 255)        # #0F1115
LIGHT_LUM = 170
PLATE_FRACTION = 0.55          # opak alan >= %55 tuval → chip+glyph ikonu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_DIR = os.path.join(ROOT, "assets", "icons")

ACTION_ICONS = (
    "add", "batch", "play", "pause", "stop", "retry", "delete",
    "folder", "grabber", "schedule", "settings",
)


def luminance(r: int, g: int, b: int) -> int:
    return (r * 299 + g * 587 + b * 114) // 1000


def rounded_plate(size: int) -> Image.Image:
    """22/32 px tuval üzerinde ortalanmış yuvarlak chip plakası (alpha mask)."""
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    inset = 1 if size <= 22 else 2
    radius = max(5, size // 4)
    d.rounded_rectangle([inset, inset, size - 1 - inset, size - 1 - inset],
                        radius=radius, fill=255)
    return m


def recolor(path: str) -> str:
    size_hint = 32 if "_32" in os.path.basename(path) else 22
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    assert (w, h) == (size_hint, size_hint), f"{path}: beklenmeyen boyut {im.size}"

    px = im.load()
    opaque, light = [], []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 60:
                opaque.append((x, y))
                if luminance(r, g, b) >= LIGHT_LUM:
                    light.append((x, y))

    has_plate = len(opaque) / (w * h) >= PLATE_FRACTION

    # Plaka: chip ikonlarda mevcut plaka şekli, glyph ikonlarda çizilen chip
    plate_mask = Image.new("L", (w, h), 0)
    if has_plate:
        p = plate_mask.load()
        for x, y in opaque:
            p[x, y] = 255
    else:
        plate_mask = rounded_plate(w)

    # Glyph: açık pikseller (chip ikon) veya alfa mask (glyph ikon)
    glyph_mask = Image.new("L", (w, h), 0)
    g = glyph_mask.load()
    if has_plate:
        src = im.load()
        for x, y in light:
            g[x, y] = src[x, y][3]
    else:
        src = im.load()
        for x, y in opaque:
            g[x, y] = src[x, y][3]

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    plate = Image.new("RGBA", (w, h), PLATE)
    out.paste(plate, (0, 0), plate_mask)
    ink = Image.new("RGBA", (w, h), INK)
    out.paste(ink, (0, 0), glyph_mask)
    out.save(path)
    return os.path.basename(path)


def main() -> int:
    done, missing = [], []
    for name in ACTION_ICONS:
        for suffix in ("", "_32"):
            path = os.path.join(ICONS_DIR, f"{name}{suffix}.png")
            if os.path.exists(path):
                done.append(recolor(path))
            else:
                missing.append(f"{name}{suffix}.png")
    print(f"donen ikon: {len(done)}")
    if missing:
        print("eksik:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
