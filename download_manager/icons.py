"""Retro+ Download Manager — Özel İkon Seti.

Tek nokta stratejisiyle çizilmiş, Segoe UI'da güvenli glifler.
Emoji yok: cross-platform render tutarlılığı için unicode semboller.
"""

from __future__ import annotations


class Icon:
    """Tutarlı ikon seti — uygulama kromu (header, menü, diyalog, durum)."""

    # İndirme / kuyruk
    DOWNLOAD      = "↓"
    BATCH         = "⇈"
    QUEUE         = "≡"
    SCHEDULE      = "⏱"
    PROGRESS      = "◐"
    SPEED         = "⚡"

    # Kontroller
    ADD           = "+"
    PLAY          = "▸"
    PAUSE         = "‖"
    STOP          = "■"
    RETRY         = "↻"
    DELETE        = "⌫"
    FOLDER        = "☐"
    GRABBER       = "⌕"
    SETTINGS      = "⚙"

    # Durum
    CHECK         = "✓"
    CLOSE         = "✕"
    DOT           = "•"
    INFO          = "ⓘ"
    WARNING       = "⚠"
    ERROR         = "✕"
    ARROW_R       = "→"
    ARROW_D       = "↓"
    CHEVRON_D     = "⌄"

    # Lisans
    KEY           = "⚿"
    PRO           = "★"
    FREE          = "○"
    TRIAL         = "☆"

    # Tema (kişiselleştirme)
    DARK          = "◐"
    LIGHT         = "◑"
    MIDNIGHT      = "◒"

    # Krom
    LOGO          = "◈"

    THEME_GLYPHS = {"dark": DARK, "light": LIGHT, "midnight": MIDNIGHT}

    @classmethod
    def theme_glyph(cls, name: str) -> str:
        """Tema adına göre glyph (dark→◐, light→◑, midnight→◒)."""
        return cls.THEME_GLYPHS.get(name, cls.DARK)

    @staticmethod
    def with_count(icon: str, count: int) -> str:
        """Sayaçlı ikon: ↓ 3"""
        return f"{icon} {count}" if count else icon
