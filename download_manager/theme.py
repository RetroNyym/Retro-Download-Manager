"""Retro+ Download Manager — lüks tasarım sistemi (token tabanlı).

Lüks ilkeleri:
- Anthracite koyu tema (#0F1115) + tek şampanya-altını vurgu rengi (#C9A962)
- 1px kenarlıklar, subtle katmanlar (gölge yerine yüzey tonları)
- Inter tarzı tipografi hiyerarşisi (hero/title/heading/body/caption)
- Cömert boşluk (SPACING), yumuşak köşe (RADIUS)
- 150-300 ms mikro animasyonlar (MOTION + fade_in)
- Tema kişiselleştirme: dark / light / midnight (kaydedilir)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# ─── Semantic token paletleri ───────────────────────────────────────────────
# Her tema aynı token adlarını paylaşır; bileşenler token okur, hex bilmez.

DARK = {
    "name": "dark",
    # Yüzeyler (katman → daha açık nötr ton)
    "bg":            "#0f1115",
    "surface":       "#15181e",
    "surface2":      "#1a1e26",
    "surface3":      "#21252e",
    "surface4":      "#2a2f3b",
    # Kenarlıklar (1px, subtle)
    "border":        "#232833",
    "border_focus":  "#c9a962",
    # Marka / tek vurgu: şampanya-altını
    "primary":       "#c9a962",
    "primary_hover": "#d8bc7c",
    "primary_dim":   "#a88b4e",
    "primary_soft":  "#2b2517",
    "accent":        "#e6cf9a",
    # Semantik
    "success":       "#2ecc96",
    "warning":       "#f0b429",
    "danger":        "#e5484d",
    # Metin (off-white — saf beyaz yok)
    "text":          "#e8ebf0",
    "text2":         "#a8aebf",
    "text3":         "#6e7689",
    "on_primary":    "#0f1115",
    # Kontrol yüzeyleri
    "btn_bg":        "#21252e",
    "btn_hover":     "#2a2f3b",
    "entry_bg":      "#161a21",
    "select_bg":     "#463c26",
    "select_fg":     "#f6efdf",
    "heading_bg":    "#1a1e26",
    "row_alt":       "#171a21",
    "scroll_track":  "#15181e",
    "scroll_thumb":  "#2a2f3b",
    "scroll_hover":  "#363c4b",
    # Aksan çubukları
    "header_bg":     "#101318",
    "header_accent": "#c9a962",
    "status_bg":     "#101318",
}

LIGHT = {
    "name": "light",
    "bg":            "#f6f5f2",
    "surface":       "#ffffff",
    "surface2":      "#fbfaf8",
    "surface3":      "#f0eee9",
    "surface4":      "#e7e4dc",
    "border":        "#e0dcd3",
    "border_focus":  "#8f7434",
    "primary":       "#8f7434",
    "primary_hover": "#7c6430",
    "primary_dim":   "#6d5729",
    "primary_soft":  "#f3ecdd",
    "accent":        "#7a6236",
    "success":       "#10a86e",
    "warning":       "#d97706",
    "danger":        "#dc2626",
    "text":          "#1c1a16",
    "text2":         "#55514a",
    "text3":         "#8b8579",
    "on_primary":    "#ffffff",
    "btn_bg":        "#ffffff",
    "btn_hover":     "#f0eee9",
    "entry_bg":      "#ffffff",
    "select_bg":     "#e9e0cb",
    "select_fg":     "#1c1a16",
    "heading_bg":    "#f6f5f2",
    "row_alt":       "#fbfaf8",
    "scroll_track":  "#f0eee9",
    "scroll_thumb":  "#cfc9bd",
    "scroll_hover":  "#b5ae9f",
    "header_bg":     "#ffffff",
    "header_accent": "#8f7434",
    "status_bg":     "#ffffff",
}

MIDNIGHT = {
    "name": "midnight",
    "bg":            "#0a0e1a",
    "surface":       "#101524",
    "surface2":      "#151b2e",
    "surface3":      "#1d2440",
    "surface4":      "#262e4e",
    "border":        "#232b48",
    "border_focus":  "#c9a962",
    "primary":       "#c9a962",
    "primary_hover": "#d8bc7c",
    "primary_dim":   "#a88b4e",
    "primary_soft":  "#24243a",
    "accent":        "#e6cf9a",
    "success":       "#34d399",
    "warning":       "#fbbf24",
    "danger":        "#f87171",
    "text":          "#e6e9f5",
    "text2":         "#9aa3bd",
    "text3":         "#667089",
    "on_primary":    "#0a0e1a",
    "btn_bg":        "#1d2440",
    "btn_hover":     "#262e4e",
    "entry_bg":      "#12172a",
    "select_bg":     "#3a3524",
    "select_fg":     "#f2ecdc",
    "heading_bg":    "#151b2e",
    "row_alt":       "#12172a",
    "scroll_track":  "#101524",
    "scroll_thumb":  "#262e4e",
    "scroll_hover":  "#333d66",
    "header_bg":     "#0b1020",
    "header_accent": "#c9a962",
    "status_bg":     "#0b1020",
}

THEMES = {"dark": DARK, "light": LIGHT, "midnight": MIDNIGHT}
DEFAULT_THEME = "dark"
THEME_ORDER = ("dark", "light", "midnight")
THEME_LABELS = {"dark": "Koyu", "light": "Açık", "midnight": "Gece"}

# ─── Tipografi hiyerarşisi ──────────────────────────────────────────────────
FONTS = {
    "hero":    ("Segoe UI Semibold", 22),
    "title":   ("Segoe UI Semibold", 15),
    "heading": ("Segoe UI Semibold", 12),
    "body":    ("Segoe UI", 10),
    "caption": ("Segoe UI", 9),
    "mono":    ("Consolas", 10),
}

# ─── Cömert boşluk / köşe / hareket ────────────────────────────────────────
SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 14, "xl": 20, "xxl": 28}
RADIUS = {"sm": 4, "md": 7, "lg": 12, "pill": 999}
MOTION = {"fade_ms": 200, "hover_ms": 150, "tooltip_ms": 350, "steps": 10}


def next_theme(current: str) -> str:
    """Sıradaki tema adını döndürür (dark → light → midnight → dark)."""
    if current not in THEME_ORDER:
        return DEFAULT_THEME
    return THEME_ORDER[(THEME_ORDER.index(current) + 1) % len(THEME_ORDER)]


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


def fade_in(window: tk.Misc, duration: int | None = None) -> None:
    """Pencereyi MOTION['fade_ms'] (150-300 ms) içinde 0→1 alfa ile açar."""
    duration = duration or MOTION["fade_ms"]
    try:
        window.wm_attributes("-alpha", 0.0)
    except tk.TclError:
        return
    steps = max(6, min(MOTION["steps"] * 2, duration // 25))
    delay = max(10, duration // steps)
    state = {"i": 0}

    def tick():
        try:
            if not window.winfo_exists():
                return
            state["i"] += 1
            window.wm_attributes("-alpha", min(1.0, state["i"] / steps))
            if state["i"] < steps:
                window.after(delay, tick)
        except tk.TclError:
            return

    window.after(delay, tick)


def bind_hover(widget: tk.Misc, enter, leave) -> None:
    """150 ms mikro-hover bağlar (bind tekrarları güvenli)."""
    widget.bind("<Enter>", lambda _e: enter(), add="+")
    widget.bind("<Leave>", lambda _e: leave(), add="+")


def titlebar_dark(window: tk.Misc, dark: bool) -> None:
    """Pencere başlık çubuğunu temaya göre koyu/açık yapar (DWM).

    Win10 1809+ attribute 13, Win11 attribute 20; ikisi de denenir.
    """
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        user32.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
        user32.GetAncestor.restype = wintypes.HWND
        hwnd = user32.GetAncestor(int(window.winfo_id()), 2)  # GA_ROOT
        value = ctypes.c_int(1 if dark else 0)
        dwmapi = ctypes.windll.dwmapi
        dwmapi.DwmSetWindowAttribute.argtypes = (
            wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD)
        for attr in (13, 20):
            try:
                dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(value),
                                             ctypes.sizeof(value))
            except Exception:
                pass
    except Exception:
        pass


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
    def label(self) -> str:
        """Türkçe tema etiketi (Koyu / Açık / Gece)."""
        return THEME_LABELS.get(self._name, self._name or "")

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

    def cycle(self):
        """Sıradaki temaya geç (dark → light → midnight → dark)."""
        self.apply(next_theme(self._name))

    def toggle(self):
        """Geriye dönük uyum: döngüsel tema değişimi."""
        self.cycle()

    # ── ttk styles ──────────────────────────────────────────────────────────
    def _apply_styles(self):
        c = self._palette
        s = self._style
        f = FONTS

        s.configure(".", background=c["bg"], foreground=c["text"],
                    fieldbackground=c["entry_bg"], bordercolor=c["border"],
                    lightcolor=c["border"], darkcolor=c["border"],
                    troughcolor=c["surface3"], selectbackground=c["select_bg"],
                    selectforeground=c["select_fg"],
                    font=f["body"])
        s.configure("TFrame", background=c["bg"])
        s.configure("Surface.TFrame", background=c["surface"])
        s.configure("Header.TFrame", background=c["header_bg"])
        s.configure("Status.TFrame", background=c["status_bg"])
        s.configure("TLabel", background=c["bg"], foreground=c["text"])
        s.configure("Surface.TLabel", background=c["surface"], foreground=c["text"])
        s.configure("Muted.TLabel", background=c["bg"], foreground=c["text2"])
        s.configure("Header.TLabel", background=c["header_bg"], foreground=c["text"])
        s.configure("Status.TLabel", background=c["status_bg"], foreground=c["text2"])
        s.configure("Title.TLabel", background=c["bg"], foreground=c["text"],
                    font=f["title"])
        s.configure("Heading.TLabel", background=c["bg"], foreground=c["primary"],
                    font=f["heading"])

        # Buton — cömert padding, 1px kenarlık
        s.configure("TButton", background=c["btn_bg"], foreground=c["text"],
                    bordercolor=c["border"], focuscolor=c["primary"],
                    padding=(14, 7), font=f["body"])
        s.map("TButton",
              background=[("active", c["btn_hover"]), ("pressed", c["primary_soft"])],
              foreground=[("disabled", c["text3"]), ("pressed", c["primary"])],
              bordercolor=[("focus", c["border_focus"])])
        s.configure("Primary.TButton", background=c["primary"],
                    foreground=c["on_primary"], bordercolor=c["primary"],
                    padding=(16, 7), font=(f["heading"][0], f["heading"][1], "bold"))
        s.map("Primary.TButton",
              background=[("active", c["primary_hover"]), ("pressed", c["primary_dim"])],
              bordercolor=[("active", c["primary_hover"])])
        s.configure("Ghost.TButton", background=c["header_bg"], foreground=c["text2"],
                    bordercolor=c["header_bg"], padding=(10, 5))
        s.map("Ghost.TButton",
              background=[("active", c["surface3"]), ("pressed", c["surface4"])],
              foreground=[("active", c["text"])])

        s.configure("TEntry", fieldbackground=c["entry_bg"], foreground=c["text"],
                    insertcolor=c["text"], bordercolor=c["border"],
                    lightcolor=c["border"], darkcolor=c["border"], padding=(6, 5))
        s.map("TEntry",
              bordercolor=[("focus", c["border_focus"])],
              lightcolor=[("focus", c["border_focus"])],
              darkcolor=[("focus", c["border_focus"])],
              fieldbackground=[("focus", c["entry_bg"])])
        s.configure("TCombobox", fieldbackground=c["entry_bg"], foreground=c["text"],
                    background=c["btn_bg"], arrowcolor=c["text2"],
                    bordercolor=c["border"], selectbackground=c["entry_bg"],
                    selectforeground=c["text"], padding=(6, 5))
        s.map("TCombobox",
              fieldbackground=[("readonly", c["entry_bg"])],
              foreground=[("readonly", c["text"])],
              selectbackground=[("readonly", c["surface4"])],
              selectforeground=[("readonly", c["text"])],
              arrowcolor=[("active", c["text"])],
              bordercolor=[("focus", c["border_focus"])])
        s.configure("TSpinbox", fieldbackground=c["entry_bg"], foreground=c["text"],
                    arrowcolor=c["text2"], bordercolor=c["border"],
                    background=c["btn_bg"], padding=(6, 5))
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
                    padding=(16, 8), borderwidth=0, font=f["body"])
        s.map("TNotebook.Tab",
              background=[("selected", c["surface3"]), ("active", c["surface4"])],
              foreground=[("selected", c["primary"]), ("active", c["text"])],
              expand=[("selected", (0, 0, 0, 2))])

        s.configure("Treeview", background=c["surface"], foreground=c["text"],
                    fieldbackground=c["surface"], bordercolor=c["border"],
                    rowheight=32, font=f["body"])
        s.configure("Treeview.Heading", background=c["heading_bg"],
                    foreground=c["text2"], relief="flat", padding=(10, 8),
                    font=(f["caption"][0], f["caption"][1], "bold"))
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
                    font=f["caption"])
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
