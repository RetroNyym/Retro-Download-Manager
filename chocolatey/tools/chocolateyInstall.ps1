$ErrorActionPreference = 'Stop'

$packageName = 'RetroDownloadManager'
$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$url = 'https://github.com/RetroNyym/Retro-Download-Manager/releases/download/v1.1.0/RetroDownloadManager-v1.1.0.zip'
$checksum = '9e953eb3fca84a0d5667857ef322ba6ff0f97dfb0470df2d7528d111913f62cb'
$checksumType = 'SHA256'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  url           = $url
  checksum      = $checksum
  checksumType  = $checksumType
}

Install-ChocolateyZipPackage @packageArgs

# Create shim for the portable exe
$exePath = Join-Path $toolsDir 'RetroDownloadManager.exe'
if (Test-Path $exePath) {
  Install-BinFile -Name 'retro-dl' -Path $exePath
}

Write-Host "Retro+ Download Manager 1.1.0 installed." -ForegroundColor Green
Write-Host "Run 'retro-dl' or launch RetroDownloadManager.exe from $toolsDir" -ForegroundColor Yellow
