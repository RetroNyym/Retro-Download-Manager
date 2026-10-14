$ErrorActionPreference = 'Stop'

$packageName = 'RetroDownloadManager'
$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Remove shim
Uninstall-BinFile -Name 'retro-dl'

Write-Host "Retro+ Download Manager uninstalled." -ForegroundColor Green
