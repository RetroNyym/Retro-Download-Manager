<p align="center">
  <a href="README.md">🌐 English</a> ·
  <a href="README.tr.md">🇹🇷 Türkçe</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.es.md">Español</a>
</p>

# Retro+ Download Manager — Gestionnaire de téléchargement multi-segments

Retro+ Download Manager est un gestionnaire de téléchargement Python autonome
avec téléchargements parallèles segmentés (jusqu'à 32 segments), pause/reprise
à n'importe quel point, file d'attente et planification, catégorisation
automatique des fichiers, passerelle de navigateur locale et une interface
soignée en thème sombre (accents champagne doré). Il fonctionne à la fois
comme application de bureau et comme bibliothèque Python (`DownloadManager`).

## Fonctions principales

- **Jusqu'à 32 segments parallèles** — HTTP 206 `Range`, reprise depuis le
  fichier de progression, même après redémarrage
- **File d'attente & planification** — horaires horaires/quotidiens
- **Torrent** (magnet / `.torrent`) via le moteur aria2 intégré
- **Vidéo/Playlists** via yt-dlp + ffmpeg (fusion audio+vidéo)
- **Site Grabber & passerelle navigateur** — tous les liens média d'une page
  en un clic ; bookmarklet : `http://127.0.0.1:8877`
- **FTP / FTPS**, limiteur de vitesse, support des cookies/référent
- **Mise à jour automatique locale** avec vérification SHA-256 (sans dépendance GitHub)
- 3 thèmes (Sombre / Clair / Minuit), 8 catégories de fichiers, 199 tests automatisés

## Installation & démarrage

```bash
git clone https://github.com/RetroNyym/Retro-Download-Manager.git
cd Retro-Download-Manager
python -m pip install -r requirements.txt
python -m download_manager
```

## En savoir plus

La documentation complète (fonctions, architecture, tests, passerelle du
navigateur, configuration du torrent, capture PDF WhatsApp) se trouve dans la
**[README anglaise](README.md)** ou la **[README turque](README.tr.md)**.

## Licence

[MIT](LICENSE) © RetroNyym
