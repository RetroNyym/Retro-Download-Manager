<p align="center">
  <a href="README.md">🌐 English</a> ·
  <a href="README.tr.md">🇹🇷 Türkçe</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.es.md">Español</a>
</p>

# Retro+ Download Manager — Gestor de descargas multi-segmento

Retro+ Download Manager es un gestor de descargas Python independiente con
descargas paralelas por segmentos (hasta 32 segmentos), pausa/continuación en
cualquier punto, cola y programación, categorización automática de archivos,
un puente local de navegador y una interfaz cuidada con tema oscuro (acento
dorado champán). Funciona como aplicación de escritorio y como biblioteca
Python (`DownloadManager`).

## Funciones principales

- **Hasta 32 segmentos paralelos** — HTTP 206 `Range`, reanudación desde el
  archivo de progreso, incluso tras reiniciar
- **Cola y programación** — planes horarios y diarios
- **Torrent** (magnet / `.torrent`) mediante el motor aria2 integrado
- **Vídeo/Playlists** vía yt-dlp + ffmpeg (unificación de audio+vídeo)
- **Site Grabber y puente de navegador** — todos los enlaces multimedia de
  una página en un clic; bookmarklet: `http://127.0.0.1:8877`
- **FTP / FTPS**, limitador de velocidad, soporte de cookies/referer
- **Autoactualización local** con verificación SHA-256 (sin dependencia de GitHub)
- 3 temas (Oscuro / Claro / Medianoche), 8 categorías de archivos, 199 pruebas automatizadas

## Instalación y arranque

```bash
git clone https://github.com/RetroNyym/Retro-Download-Manager.git
cd Retro-Download-Manager
python -m pip install -r requirements.txt
python -m download_manager
```

## Saber más

La documentación completa (funciones, arquitectura, pruebas, puente del
navegador, configuración de torrent, captura de PDF de WhatsApp) está en la
**[README en inglés](README.md)** o en la **[README en turco](README.tr.md)**.

## Licencia

[MIT](LICENSE) © RetroNyym
