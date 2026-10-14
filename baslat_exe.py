r"""PyInstaller giriş noktası (portable exe üretimi için).

    python -m PyInstaller --noconfirm --onefile --windowed ^
        --name RetroDownloadManager --add-data "assets;assets" ^
        --add-data "whatsapp_listener;whatsapp_listener" ^
        --add-data "tools;tools" --manifest docs\store\app.manifest baslat_exe.py

tools altındaki aria2/aria2c.exe torrent motorudur; paket içinde
MEIPASS\\tools\\aria2\\ olarak çıkar (torrent.py oradan bulur).
app.manifest: PerMonitorV2 DPI bildirimi (WACK DPIAwareness testi için).
"""

from download_manager.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
