"""Retro+ Download Manager — çift temalı tasarım sistemi (token tabanlı).

2026 trendleri: calm density, adaptive theming, layered elevation
(gölge yerine yüzey tonları), WCAG AA kontrast, saf siyah/beyaz yok.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# ─── Semantic token paletleri ───────────────────────────────────────────────
# Her tema aynı token adlarını paylaşır; bileşenler token okur, hex bilmez.

DARK = {
    "name": "dark",
    # Yüzeyler (elevation → daha açık gri)
    "bg":            "#0f1115",
    "surface":       "#161920",
    "surface2":      "#1c2028",
    "surface3":      "#232833",
    "surface4":      "#2b3140",
    # Kenarlıklar
    "border":        "#2a3040",
    "border_focus":  "#5b6cff",
    # Marka / vurgu
    "primary":       "#6c7bff",
    "primary_hover": "#8b96ff",
    "primary_dim":   "#3d4bcc",
    "primary_soft":  "#1e2440",
    "accent":        "#3ec6e0",
    # Semantik
    "success":       "#2ecc96",
    "warning":       "#f0b429",
    "danger":        "#e5484d",
    # Metin (off-white — saf beyaz yok)
    "text":          "#e8ebf0",
    "text2":         "#a8aebf",
    "text3":         "#6e7689",
    "on_primary":    "#ffffff",
    # Kontrol yüzeyleri
    "btn_bg":        "#232833",
    "btn_hover":     "#2b3140",
    "entry_bg":      "#1c2028",
    "select_bg":     "#2e3a6e",
    "select_fg":     "#ffffff",
    "heading_bg":    "#1c2028",
    "row_alt":       "#191d26",
    "scroll_track":  "#161920",
    "scroll_thumb":  "#2b3140",
    "scroll_hover":  "#3a4152",
    # Aksan çubukları
    "header_bg":     "#12151c",
    "header_accent": "#6c7bff",
    "status_bg":     "#12151c",
}

LIGHT = {
    "name": "light",
    "bg":            "#f4f6fa",
    "surface":       "#ffffff",
    "surface2":      "#f9fafb",
    "surface3":      "#eef1f6",
    "surface4":      "#e4e8f0",
    "border":        "#d8dde8",
    "border_focus":  "#4f5dff",
    "primary":       "#4f5dff",
    "primary_hover": "#3d4bff",
    "primary_dim":   "#3a46d6",
    "primary_soft":  "#e8ebff",
    "accent":        "#0ea5c6",
    "success":       "#10a86e",
    "warning":       "#d97706",
    "danger":        "#dc2626",
    "text":          "#1a1f2e",
    "text2":         "#4b5568",
    "text3":         "#8b93a5",
    "on_primary":    "#ffffff",
    "btn_bg":        "#ffffff",
    "btn_hover":     "#eef1f6",
    "entry_bg":      "#ffffff",
    "select_bg":     "#e0e5ff",
    "select_fg":     "#1a1f2e",
    "heading_bg":    "#f4f6fa",
    "row_alt":       "#f9fafb",
    "scroll_track":  "#eef1f6",
    "scroll_thumb":  "#c4cad8",
    "scroll_hover":  "#a8b0c4",
    "header_bg":     "#ffffff",
    "header_accent": "#4f5dff",
    "status_bg":     "#ffffff",
}

THEMES = {"dark": DARK, "light": LIGHT}
DEFAULT_THEME = "dark"


def detect_system_theme() -> str:
    """Windows'ta sistem temasını algılar (koyu/açık)."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if int(value) else "dark"
    except Exception:
        return DEFAULT_THEME


class ThemeManager:
    """Aktif temayı tutar, ttk stillerini ve tk widget renklerini uygular."""

    def __init__(self, root, name: str | None = None):
        self.root = root
        self._name = None
        self._palette = {}
        self._style = ttk.Style(root)
        try:
            self._style.theme_use("clam")
        except Exception:
            pass
        self._listeners = []
        initial = name if name in THEMES else detect_system_theme()
        self.apply(initial, notify=False)

    # ── properties ──────────────────────────────────────────────────────────
    @property
    def name(self) -> str:
        return self._name

    @property
    def c(self) -> dict:
        """Aktif palet (token adları → hex)."""
        return self._palette

    def on_change(self, callback):
        self._listeners.append(callback)

    # ── theme switching ─────────────────────────────────────────────────────
    def apply(self, name: str, notify: bool = True):
        if name not in THEMES:
            name = DEFAULT_THEME
        if name == self._name:
            return
        self._name = name
        self._palette = dict(THEMES[name])
        self._apply_styles()
        if notify:
            for cb in self._listeners:
                try:
                    cb(name)
                except Exception:
                    pass

    def toggle(self):
        self.apply("light" if self._name == "dark" else "dark")

    # ── ttk styles ──────────────────────────────────────────────────────────
    def _apply_styles(self):
        c = self._palette
        s = self._style

        s.configure(".", background=c["bg"], foreground=c["text"],
                    fieldbackground=c["entry_bg"], bordercolor=c["border"],
                    lightcolor=c["border"], darkcolor=c["border"],
                    troughcolor=c["surface3"], selectbackground=c["select_bg"],
                    selectforeground=c["select_fg"],
                    font=("Segoe UI", 10))
        s.configure("TFrame", background=c["bg"])
        s.configure("Surface.TFrame", background=c["surface"])
        s.configure("Header.TFrame", background=c["header_bg"])
        s.configure("Status.TFrame", background=c["status_bg"])
        s.configure("TLabel", background=c["bg"], foreground=c["text"])
        s.configure("Surface.TLabel", background=c["surface"], foreground=c["text"])
        s.configure("Muted.TLabel", background=c["bg"], foreground=c["text2"])
        s.configure("Header.TLabel", background=c["header_bg"], foreground=c["text"])
        s.configure("Status.TLabel", background=c["status_bg"], foreground=c["text2"])

        s.configure("TButton", background=c["btn_bg"], foreground=c["text"],
                    bordercolor=c["border"], focuscolor=c["primary"],
                    padding=(12, 6))
        s.map("TButton",
              background=[("active", c["btn_hover"]), ("pressed", c["primary_soft"])],
              foreground=[("disabled", c["text3"]), ("pressed", c["primary"])],
              bordercolor=[("focus", c["border_focus"])])
        s.configure("Primary.TButton", background=c["primary"],
                    foreground=c["on_primary"], bordercolor=c["primary"],
                    font=("Segoe UI", 10, "bold"))
        s.map("Primary.TButton",
              background=[("active", c["primary_hover"]), ("pressed", c["primary_dim"])],
              bordercolor=[("active", c["primary_hover"])])
        s.configure("Ghost.TButton", background=c["header_bg"], foreground=c["text2"],
                    bordercolor=c["header_bg"], padding=(8, 5))
        s.map("Ghost.TButton",
              background=[("active", c["surface3"]), ("pressed", c["surface4"])],
              foreground=[("active", c["text"])])

        s.configure("TEntry", fieldbackground=c["entry_bg"], foreground=c["text"],
                    insertcolor=c["text"], bordercolor=c["border"],
                    lightcolor=c["border"], darkcolor=c["border"])
        s.map("TEntry",
              bordercolor=[("focus", c["border_focus"])],
              lightcolor=[("focus", c["border_focus"])],
              darkcolor=[("focus", c["border_focus"])],
              fieldbackground=[("focus", c["entry_bg"])])
        s.configure("TCombobox", fieldbackground=c["entry_bg"], foreground=c["text"],
                    background=c["btn_bg"], arrowcolor=c["text2"],
                    bordercolor=c["border"], selectbackground=c["entry_bg"],
                    selectforeground=c["text"])
        s.map("TCombobox",
              fieldbackground=[("readonly", c["entry_bg"])],
              foreground=[("readonly", c["text"])],
              selectbackground=[("readonly", c["surface4"])],
              selectforeground=[("readonly", c["text"])],
              arrowcolor=[("active", c["text"])],
              bordercolor=[("focus", c["border_focus"])])
        s.configure("TSpinbox", fieldbackground=c["entry_bg"], foreground=c["text"],
                    arrowcolor=c["text2"], bordercolor=c["border"],
                    background=c["btn_bg"])
        s.map("TSpinbox", bordercolor=[("focus", c["border_focus"])])
        s.configure("TCheckbutton", background=c["bg"], foreground=c["text"],
                    focuscolor=c["bg"])
        s.map("TCheckbutton", background=[("active", c["bg"])],
              foreground=[("active", c["primary"])])
        s.configure("TCheckbutton", indicatorbackground=c["surface3"],
                    indicatorcolor=c["text2"], indicatorrelief="flat")
        s.map("TCheckbutton",
              indicatorbackground=[("selected", c["primary"]), ("active", c["surface4"])],
              indicatorcolor=[("selected", c["on_primary"]), ("active", c["text"])])
        s.configure("TRadiobutton", background=c["bg"], foreground=c["text"],
                    focuscolor=c["bg"])
        s.map("TRadiobutton", background=[("active", c["bg"])],
              foreground=[("active", c["primary"])])
        s.configure("TRadiobutton", indicatorbackground=c["surface3"],
                    indicatorcolor=c["text2"], indicatorrelief="flat")
        s.map("TRadiobutton",
              indicatorbackground=[("selected", c["primary"]), ("active", c["surface4"])],
              indicatorcolor=[("selected", c["on_primary"]), ("active", c["text"])])

        s.configure("TNotebook", background=c["bg"], borderwidth=0)
        s.configure("TNotebook.Tab", background=c["surface2"], foreground=c["text2"],
                    padding=(14, 7), borderwidth=0, font=("Segoe UI", 10))
        s.map("TNotebook.Tab",
              background=[("selected", c["surface3"]), ("active", c["surface4"])],
              foreground=[("selected", c["primary"]), ("active", c["text"])],
              expand=[("selected", (0, 0, 0, 2))])

        s.configure("Treeview", background=c["surface"], foreground=c["text"],
                    fieldbackground=c["surface"], bordercolor=c["border"],
                    rowheight=30, font=("Segoe UI", 10))
        s.configure("Treeview.Heading", background=c["heading_bg"],
                    foreground=c["text2"], relief="flat", padding=(8, 7),
                    font=("Segoe UI", 9, "bold"))
        s.map("Treeview.Heading", background=[("active", c["surface3"])])
        s.map("Treeview",
              background=[("selected", c["select_bg"])],
              foreground=[("selected", c["select_fg"])])

        for orient in ("Vertical", "Horizontal"):
            s.configure(f"{orient}.TScrollbar",
                        background=c["scroll_thumb"], troughcolor=c["scroll_track"],
                        bordercolor=c["scroll_track"], arrowcolor=c["text3"],
                        relief="flat", borderwidth=0)
            s.map(f"{orient}.TScrollbar",
                  background=[("active", c["scroll_hover"]), ("pressed", c["primary"])],
                  arrowcolor=[("active", c["text"])])

        s.configure("TPanedwindow", background=c["border"], sashwidth=4,
                    sashrelief="flat")
        s.configure("TPanedwindow.Pane", background=c["bg"])
        s.configure("TLabelframe", background=c["bg"], foreground=c["text2"],
                    bordercolor=c["border"])
        s.configure("TLabelframe.Label", background=c["bg"], foreground=c["text2"],
                    font=("Segoe UI", 9, "bold"))
        s.configure("Horizontal.TProgressbar", background=c["primary"],
                    troughcolor=c["surface3"], bordercolor=c["bg"],
                    lightcolor=c["primary"], darkcolor=c["primary"])
        s.configure("TScale", background=c["bg"], troughcolor=c["surface3"],
                    bordercolor=c["bg"], slidercolor=c["primary"])
        s.configure("TSeparator", background=c["border"])
        s.configure("TMenubar", background=c["surface"], foreground=c["text"],
                    bordercolor=c["surface"])
        s.map("TMenubar", background=[("active", c["surface3"])],
              foreground=[("active", c["primary"])])

        try:
            self.root.configure(background=c["bg"])
        except Exception:
            pass

    # ── yardımcılar ─────────────────────────────────────────────────────────
    def menu_config(self, menu: tk.Menu):
        c = self._palette
        menu.configure(background=c["surface"], foreground=c["text"],
                       activebackground=c["surface3"], activeforeground=c["primary"],
                       borderwidth=0, relief="flat", tearoff=0,
                       font=("Segoe UI", 10))
        try:
            menu.tk_popup  # noqa: B018 — varlığını doğrula
        except Exception:
            pass

    def apply_menu(self, menu: tk.Menu):
        """Menüye ve alt menülerine aktif temayı uygular."""
        c = self._palette
        try:
            menu.configure(background=c["surface"], foreground=c["text"],
                           activebackground=c["surface3"],
                           activeforeground=c["primary"])
            count = menu.index("end")
            if count is None:
                return
            for i in range(count + 1):
                try:
                    menu.entryconfig(i, background=c["surface"], foreground=c["text"],
                                     activebackground=c["surface3"],
                                     activeforeground=c["primary"])
                except Exception:
                    pass
        except Exception:
            pass
