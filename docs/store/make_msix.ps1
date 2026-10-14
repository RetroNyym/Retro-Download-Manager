# Retro+ Download Manager - MSIX paket uretici
# Kullanim (repo kokunden):
#   powershell -ExecutionPolicy Bypass -File docs\store\make_msix.ps1
#   powershell ... -Publisher "CN=PartnerCenterKimligi"   # varsayilan: CN=RetroPlus
# Gereksinim: MakeAppx.exe (Windows SDK) + Python (PIL) - GONDERIM-REHBERI.md'ye bak.
param(
    [string]$Exe = "dist\RetroDownloadManager.exe",
    [string]$Publisher = "CN=RetroPlus",
    [switch]$DenemeSertifikasi
)

$ErrorActionPreference = "Stop"
$Kok = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)  # repo koku
if (-not (Test-Path (Join-Path $Kok $Exe))) {
    Write-Error "Exe bulunamadi: $Exe (once PyInstaller build gerekli)"
}

# 1) MakeAppx.exe ara
$makeappx = $null
$ad = Get-Command makeappx.exe -ErrorAction SilentlyContinue
if ($ad) { $makeappx = $ad.Source }
if (-not $makeappx) {
    $kitler = @("${env:ProgramFiles(x86)}\Windows Kits\10\bin",
                "$env:ProgramFiles\Windows Kits\10\bin")
    foreach ($k in $kitler) {
        if (Test-Path $k) {
            $bul = Get-ChildItem $k -Recurse -Filter makeappx.exe -ErrorAction SilentlyContinue |
                   Sort-Object FullName -Descending | Select-Object -First 1
            if ($bul) { $makeappx = $bul.FullName; break }
        }
    }
}
if (-not $makeappx) {
    Write-Error ("MakeAppx.exe bulunamadi. Windows SDK kurun: " +
        "Visual Studio Installer > 'Windows 11 SDK' (veya `winget install Microsoft.WindowsSDK`), " +
        "sonra tekrar deneyin. Ayrinti: docs\store\GONDERIM-REHBERI.md")
}
Write-Output "makeappx: $makeappx"

# 2) Stage hazirla
$stage = Join-Path $env:TEMP "rdm_msix_stage"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage -Force | Out-Null
Copy-Item (Join-Path $Kok $Exe) (Join-Path $stage "RetroDownloadManager.exe")
Copy-Item (Join-Path $PSScriptRoot "Package.appxmanifest") (Join-Path $stage "AppxManifest.xml")
(Get-Content (Join-Path $stage "AppxManifest.xml") -Raw) `
    -replace 'Publisher="[^"]*"', ('Publisher="' + $Publisher + '"') |
    Set-Content (Join-Path $stage "AppxManifest.xml") -Encoding UTF8

# 3) Gecici logo uret (PIL) - Store icin gercek logoyla degistirin!
$assets = Join-Path $stage "assets"
New-Item -ItemType Directory -Path $assets -Force | Out-Null
python -c @"
from PIL import Image, ImageDraw
import os
base = r'$assets'
def kutu(w, h, path, metin=True):
    img = Image.new('RGBA', (w, h), (24, 26, 32, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, w - 3, h - 3], outline=(0, 200, 120, 255), width=max(1, w // 40))
    if metin:
        t = 'R+'
        try:
            from PIL import ImageFont
            f = ImageFont.truetype('consola.ttf', min(w, h) // 2)
        except Exception:
            f = None
        bb = d.textbbox((0, 0), t, font=f)
        d.text(((w - (bb[2] - bb[0])) / 2, (h - (bb[3] - bb[1])) / 2 - bb[1]), t,
               fill=(0, 230, 140, 255), font=f)
    img.save(os.path.join(base, path))
kutu(50, 50, 'StoreLogo.png')
kutu(44, 44, 'Square44x44Logo.png')
kutu(150, 150, 'Square150x150Logo.png')
kutu(310, 150, 'Wide310x150Logo.png')
kutu(620, 300, 'SplashScreen.png', metin=False)
print('logo uretildi (gecici) - Store oncesi docs/store/logo-uyarisi.md')
"@

# 4) Paketle
$cikti = Join-Path $Kok "dist\RetroDownloadManager.msix"
& $makeappx pack /d $stage /p $cikti /o
if ($LASTEXITCODE -ne 0) { Write-Error "makeappx pack basarisiz (kod $LASTEXITCODE)" }
Write-Output "MSIX uretildi: $cikti ($([math]::Round((Get-Item $cikti).Length/1MB,1)) MB)"

# 5) Istege bagli deneme imzasi (yerel kurulum testi icin; Store imzayi kendisi atar)
if ($DenemeSertifikasi) {
    $cert = New-SelfSignedCertificate -Type Custom -Subject "CN=RetroPlus" `
        -KeyUsage DigitalSignature -FriendlyName "Retro+ MSIX Deneme" `
        -CertStoreLocation Cert:\CurrentUser\My -TextExtension @(
        "2.5.29.37={text}1.3.6.1.5.5.7.3.3,1.3.6.1.4.1.311.84.1.1",
        "2.5.29.19={text}")
    $cer = Join-Path $env:TEMP "rdm_deneme.pfx"
    Export-PfxCertificate -Cert $cert -FilePath $cer -Password (ConvertTo-SecureString -String "deneme" -Force -AsPlainText) | Out-Null
    $adaylar = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Recurse `
        -Filter signtool.exe -ErrorAction SilentlyContinue
    $signtool = $adaylar | Where-Object { $_.FullName -match '\\(x64|x86)\\' } |
        Select-Object -First 1
    if ($signtool) {
        & $signtool.FullName sign /fd SHA256 /f $cer /p "deneme" $cikti
        if ($LASTEXITCODE -ne 0) { Write-Error "signtool imza basarisiz (kod $LASTEXITCODE)" }
        Remove-Item $cer -Force -ErrorAction SilentlyContinue
        Write-Output "Deneme imzasi eklendi; yerel test: Add-AppxPackage -Path $cikti"
    } else {
        Write-Warning "signtool bulunamadi; imza eklenmedi (yerel kurulum testi icin gerekli)"
    }
}



