$ErrorActionPreference = 'Stop'

$packageName = 'RetroDownloadManager'
$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$url = 'https://github.com/RetroNyym/Retro-Download-Manager/releases/download/v1.2.0/RetroDownloadManager-v1.2.0.zip'
$checksum = '7809cacfeb47da65231e98e13a986c028b00ce076ed60651e079c757bb6598e7'
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

Write-Host "Retro+ Download Manager 1.2.0 installed." -ForegroundColor Green
Write-Host "Run 'retro-dl' or launch RetroDownloadManager.exe from $toolsDir" -ForegroundColor Yellow
