<p align="center">
  <a href="README.md">🌐 English</a> ·
  <a href="README.tr.md">🇹🇷 Türkçe</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.es.md">Español</a>
</p>

# Retro+ Download Manager — Mehrfach segmentierter Download-Manager

Retro+ Download Manager ist ein eigenständiger Python-Download-Manager mit
parallel segmentierten Downloads (bis zu 32 Segmente), Pausieren/Fortsetzen an
beliebiger Stelle, Warteschlange und Zeitplanung, automatischer Datei-
kategorisierung, einer lokalen Browser-Brücke sowie einer eleganter
Dunkelthema-Oberfläche (Champagner-Gold-Akzent). Er kann als Desktop-Anwendung
oder als Python-Bibliothek (`DownloadManager`) verwendet werden.

## Kernfunktionen

- **Bis zu 32 parallele Segmente** — HTTP 206 `Range`, Fortsetzen aus der
  Fortschrittsdatei, auch nach Neustart
- **Warteschlange & Zeitplanung** — stündliche/tägliche Pläne
- **Torrent** (magnet / `.torrent`) über eingebettete aria2-Engine
- **Video/Playlist** über yt-dlp + ffmpeg (Audio+Video-Zusammenführung)
- **Site Grabber & Browser-Brücke** — alle Medienlinks einer Seite auf einen
  Klick; Bookmarklet: `http://127.0.0.1:8877`
- **FTP / FTPS**, Geschwindigkeitsbegrenzung, Coookie/Referer-Unterstützung
- **Lokale Selbstaktualisierung** mit SHA-256-Prüfung (keine GitHub-Abhängigkeit)
- 3 Themes (Dunkel / Hell / Mitternacht), 8 Dateikategorien, 199 automatisierte Tests

## Installation & Start

```bash
git clone https://github.com/RetroNyym/Retro-Download-Manager.git
cd Retro-Download-Manager
python -m pip install -r requirements.txt
python -m download_manager
```

## Mehr erfahren

Die vollständige Dokumentation (Features, Architektur, Tests, Browser-Brücke,
Torrent-Einrichtung, WhatsApp-PDF-Erfassung) finden Sie in der
**[englischen README](README.md)** bzw. der **[türkischen README](README.tr.md)**.

## Lizenz

[MIT](LICENSE) © RetroNyym
