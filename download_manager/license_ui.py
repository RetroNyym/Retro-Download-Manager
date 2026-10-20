"""Retro+ — Ortak Lisans Diyaloğu (tüm Retro+ programları için).

Kullanım:
    from .license_ui import show_license_dialog
    show_license_dialog(parent_window, product_code=1)

İçerik:
  • Fiyat tablosu (products.json'dan)
  • Satın alma butonu (web sitesi + e-posta)
  • İletişim bilgileri (contact.json'dan)
  • Lisans anahtarı girişi + aktivasyon
  • Pro özellik listesi
"""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import webbrowser
import urllib.parse

from .license import (
    get_license_manager, parse_key, load_products,
    KIND_LABELS_TR, TRIAL_DOWNLOADS, PRO_FEATURES,
)
from .theme import titlebar_dark

# ─── Renk paleti (koyu tema — anthracite + şampanya-altını) ─────────────────
_DEFAULT_COLORS = {
    "bg": "#0f1115", "surface": "#15181e", "surface2": "#1a1e26",
    "surface3": "#21252e", "line": "#232833",
    "text": "#e8ebf0", "text2": "#a8aebf", "text3": "#6e7689",
    "primary": "#c9a962", "accent": "#e6cf9a", "success": "#2ecc96",
    "danger": "#e5484d", "warn": "#f0b429",
}

# Web sitesi kök URL
SITE_URL = "https://retro-download-manager.netlify.app"


def _load_contact() -> dict:
    """contact.json'dan iletişim bilgilerini yükler."""
    for base in (
        Path(__file__).resolve().parent.parent / "sales",
        Path(__file__).resolve().parent,  # EXE yanında
        Path.cwd() / "sales",
        Path.cwd(),
    ):
        path = base / "contact.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {}


def _center(win, parent=None):
    win.update_idletasks()
    if parent:
        x = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - win.winfo_height()) // 2
    else:
        x = (win.winfo_screenwidth() - win.winfo_width()) // 2
        y = (win.winfo_screenheight() - win.winfo_height()) // 2
    win.geometry(f"+{max(x, 0)}+{max(y, 0)}")


def show_license_dialog(parent=None, product_code: int = 1,
                        colors: dict | None = None) -> str | None:
    """Lisans diyaloğunu açar. Dönüş: 'activated' | 'deactivated' | None."""
    c = colors or _DEFAULT_COLORS
    dlg = tk.Toplevel(parent) if parent else tk.Tk()
    dlg.title("Lisans & Satın Alma — Retro+")
    dlg.configure(bg=c["bg"])
    dlg.transient(parent) if parent else None
    dlg.resizable(False, False)
    titlebar_dark(dlg, (c.get("name") or "dark") != "light")

    lic = get_license_manager()
    products = load_products()
    product = products.get(product_code, {})
    product_name = product.get("name", "Retro+")
    prices = product.get("prices", {})
    contact = _load_contact()

    body = tk.Frame(dlg, bg=c["bg"], padx=20, pady=16)
    body.pack(fill="both", expand=True)

    # ─── Başlık ─────────────────────────────────────────────────────────
    status_text = "PRO AKTİF" if lic.is_pro else "ÜCRETSİZ SÜRÜM"
    status_color = c["success"] if lic.is_pro else c["text3"]
    tk.Label(body, text=f"{product_name}", bg=c["bg"], fg=c["text"],
             font=("Segoe UI Semibold", 15)).pack(anchor="w")
    tk.Label(body, text=status_text, bg=c["bg"], fg=status_color,
             font=("Segoe UI", 10, "bold")).pack(anchor="w")

    if lic.is_pro:
        info = lic.info or {}
        kind_tr = KIND_LABELS_TR.get(info.get("kind", ""), info.get("kind", ""))
        expires = info.get("expires_at", "")
        expire_txt = f" · Bitiş: {expires[:10]}" if expires else ""
        left = lic.downloads_left
        left_txt = f" · Kalan hak: {left}" if left is not None else ""
        tk.Label(body, text=f" Tür: {kind_tr} · Cihaz: {lic.seats}{expire_txt}{left_txt}",
                 bg=c["bg"], fg=c["text2"], font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 8))

        # Pro özellik listesi
        feat = tk.Frame(body, bg=c["surface"], padx=12, pady=8)
        feat.pack(fill="x", pady=(0, 10))
        for key, desc in PRO_FEATURES:
            tk.Label(feat, text=f"✓  {desc}", bg=c["surface"], fg=c["success"],
                     font=("Segoe UI", 9)).pack(anchor="w", pady=1)
    else:
        tk.Label(body, text="Pro özelliklerin kilidini açmak için lisans satın alın.",
                 bg=c["bg"], fg=c["text2"], font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 8))

        # ─── Fiyat Tablosu ──────────────────────────────────────────────
        price_frame = tk.Frame(body, bg=c["surface"], padx=12, pady=10)
        price_frame.pack(fill="x", pady=(0, 10))
        tk.Label(price_frame, text="💰 Fiyatlar", bg=c["surface"], fg=c["accent"],
                 font=("Segoe UI Semibold", 11)).pack(anchor="w", pady=(0, 6))

        # Tablo başlıkları
        header = tk.Frame(price_frame, bg=c["surface"])
        header.pack(fill="x")
        for text, w in (("Tür", 120), ("Süre/Hak", 140), ("Fiyat", 80)):
            tk.Label(header, text=text, bg=c["surface"], fg=c["text3"],
                     font=("Segoe UI", 8, "bold"), width=w // 10, anchor="w").pack(
                side="left", padx=(0, 4))

        durations = {
            "trial": f"{TRIAL_DOWNLOADS} indirme",
            "halfyear": "183 gün",
            "year": "365 gün",
            "lifetime": "Süresiz",
        }
        for kind in ("trial", "halfyear", "year", "lifetime"):
            row = tk.Frame(price_frame, bg=c["surface"])
            row.pack(fill="x", pady=1)
            label = KIND_LABELS_TR.get(kind, kind)
            price = prices.get(kind, "—")
            color = c["success"] if kind == "lifetime" else c["text"]
            tk.Label(row, text=label, bg=c["surface"], fg=color,
                     font=("Segoe UI", 9, "bold" if kind == "lifetime" else "normal"),
                     width=12, anchor="w").pack(side="left")
            tk.Label(row, text=durations.get(kind, ""), bg=c["surface"], fg=c["text2"],
                     font=("Segoe UI", 9), width=14, anchor="w").pack(side="left")
            tk.Label(row, text=price, bg=c["surface"], fg=color,
                     font=("Segoe UI", 10, "bold"), width=8, anchor="w").pack(side="left")

        # ─── Satın Alma Butonları ───────────────────────────────────────
        buy_frame = tk.Frame(body, bg=c["bg"])
        buy_frame.pack(fill="x", pady=(0, 8))

        tk.Button(buy_frame, text="🛒  Satın Al (Web Sitesi)",
                  command=lambda: webbrowser.open(f"{SITE_URL}/satinal.html"),
                  bg=c["success"], fg="#fff", activebackground="#35c070",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=6, cursor="hand2").pack(fill="x", pady=(0, 4))

        if contact.get("email"):
            email = contact["email"]
            subject = f"{product_name} Lisans Siparişi"
            body_text = (f"Merhaba,\n\n{product_name} lisans satın almak istiyorum.\n\n"
                         "Ad Soyad: \n"
                         "Tür (6 Aylık / Yıllık / Ömür Boyu): \n"
                         "Ödeme yöntemi: \n"
                         "Dekont: eklendi\n")
            mailto = (f"mailto:{email}?subject={urllib.parse.quote(subject)}"
                      f"&body={urllib.parse.quote(body_text)}")
            tk.Button(buy_frame, text=f"📧  Sipariş E-postası Gönder ({email})",
                      command=lambda: webbrowser.open(mailto),
                      bg=c["surface3"], fg=c["text"], relief="flat",
                      font=("Segoe UI", 9), padx=12, pady=5, cursor="hand2").pack(
                fill="x", pady=(0, 4))

        if contact.get("whatsapp"):
            wa = contact["whatsapp"].replace(" ", "").replace("+", "")
            tk.Button(buy_frame, text=f"💬  WhatsApp ({contact['whatsapp']})",
                      command=lambda: webbrowser.open(f"https://wa.me/{wa}"),
                      bg=c["surface3"], fg=c["text"], relief="flat",
                      font=("Segoe UI", 9), padx=12, pady=5, cursor="hand2").pack(
                fill="x", pady=(0, 4))

        # ─── İletişim Bilgileri ─────────────────────────────────────────
        if any(contact.get(k) for k in ("iban", "bank", "holder", "papara")):
            info_frame = tk.Frame(body, bg=c["surface2"], padx=10, pady=8)
            info_frame.pack(fill="x", pady=(0, 8))
            tk.Label(info_frame, text="Ödeme Bilgileri", bg=c["surface2"],
                     fg=c["accent"], font=("Segoe UI", 9, "bold")).pack(anchor="w")
            for label, key in (("Alıcı", "holder"), ("IBAN", "iban"),
                               ("Banka", "bank"), ("Papara", "papara")):
                val = contact.get(key, "")
                if val:
                    row = tk.Frame(info_frame, bg=c["surface2"])
                    row.pack(fill="x")
                    tk.Label(row, text=f"{label}:", bg=c["surface2"], fg=c["text3"],
                             font=("Segoe UI", 8), width=8, anchor="w").pack(side="left")
                    tk.Label(row, text=val, bg=c["surface2"], fg=c["text"],
                             font=("Consolas", 8), anchor="w").pack(side="left")
                    tk.Button(row, text="📋", command=lambda v=val: _copy(dlg, v),
                              bg=c["surface3"], fg=c["text2"], relief="flat",
                              font=("Segoe UI", 7), padx=2, cursor="hand2").pack(side="right")

        # ─── Lisans Anahtarı Girişi ─────────────────────────────────────
        tk.Label(body, text="Lisans anahtarınız varsa girin:", bg=c["bg"],
                 fg=c["text2"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 2))
        var_key = tk.StringVar()
        entry = tk.Entry(body, textvariable=var_key, width=36,
                         bg=c["surface2"], fg=c["text"], insertbackground=c["text"],
                         relief="flat", font=("Consolas", 11))
        entry.pack(fill="x", ipady=5)
        entry.focus_set()

    # ─── Butonlar ───────────────────────────────────────────────────────
    btns = tk.Frame(body, bg=c["bg"])
    btns.pack(fill="x", pady=(10, 0))
    if lic.is_pro:
        ttk.Button(btns, text="Lisansı Kaldır",
                   command=lambda: _deactivate(dlg, lic)).pack(side="left", padx=4)
    else:
        ttk.Button(btns, text="✅  Aktive Et", style="Primary.TButton",
                   command=lambda: _activate(dlg, lic, var_key.get())).pack(
            side="left", padx=4)
    ttk.Button(btns, text="Kapat", command=dlg.destroy).pack(side="right", padx=4)

    dlg.bind("<Escape>", lambda _e: dlg.destroy())
    dlg.bind("<Return>", lambda _e: _activate(dlg, lic, var_key.get())
             if not lic.is_pro else None)
    _center(dlg, parent)
    dlg.mainloop()
    return None


def _copy(parent, text):
    parent.clipboard_clear()
    parent.clipboard_append(text)


def _activate(dlg, lic, key: str):
    key = key.strip()
    if not key:
        messagebox.showwarning("Eksik", "Lisans anahtarı girin.", parent=dlg)
        return
    parsed = parse_key(key)
    if not parsed:
        messagebox.showerror("Geçersiz",
                             "Lisans anahtarı geçersiz.\nKontrol edip tekrar deneyin.",
                             parent=dlg)
        return
    if lic.activate(key):
        messagebox.showinfo("Aktive Edildi",
                            "Pro özellikleri kullanıma açıldı!", parent=dlg)
        dlg.destroy()
    else:
        messagebox.showerror("Hata", "Lisans kaydedilemedi.", parent=dlg)


def _deactivate(dlg, lic):
    if messagebox.askyesno("Lisans", "Lisans kaldırılsın mı?", parent=dlg):
        lic.deactivate()
        dlg.destroy()
