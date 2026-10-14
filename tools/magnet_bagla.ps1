# magnet: baglantilarini Retro+ Download Manager ile acar (HKCU, yonetici gerekmez)
# Kullanim:
#   powershell -ExecutionPolicy Bypass -File tools\magnet_bagla.ps1
#   powershell -ExecutionPolicy Bypass -File tools\magnet_bagla.ps1 -Exe "C:\Yol\RetroOps.exe"
#   powershell -ExecutionPolicy Bypass -File tools\magnet_bagla.ps1 -Kaldir   # geri al

param(
    [string]$Exe = "",
    [switch]$Kaldir
)

$Anahtar = "HKCU:\Software\Classes\magnet"

if ($Kaldir) {
    if (Test-Path $Anahtar) {
        Remove-Item -Path $Anahtar -Recurse -Force
        Write-Output "magnet: baglantisi geri alindi (HKCU temizlendi)."
    } else {
        Write-Output "Kayitli magnet: baglantisi yok."
    }
    exit 0
}

if (-not $Exe) {
    # Varsayilan adaylar: bu betigin ust dizinindeki paket exe'leri
    $Adaylar = @(
        (Join-Path $PSScriptRoot "..\RetroDownloadManager.exe"),
        (Join-Path $PSScriptRoot "..\retro_download_manager.exe"),
        (Join-Path $PSScriptRoot "..\RetroOps.exe"),
        (Join-Path $PSScriptRoot "..\retro_ops.exe")
    )
    $Bulunan = $Adaylar | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($Bulunan) {
        $Exe = (Resolve-Path $Bulunan).Path
    } else {
        # kaynak kurulum: python -m download_manager
        $Exe = "pythonw.exe -m download_manager"
        Write-Warning "Paket exe bulunamadi; pythonw -m download_manager olarak baglandi."
    }
}

New-Item -Path $Anahtar -Force | Out-Null
Set-ItemProperty -Path $Anahtar -Name "(default)" -Value "URL:magnet Protocol"
New-Item -Path "$Anahtar\shell" -Force | Out-Null
New-Item -Path "$Anahtar\shell\open" -Force | Out-Null
New-Item -Path "$Anahtar\shell\open\command" -Force | Out-Null
$Komut = "`"$Exe`" --magnet `"%1`""
if ($Exe -like "*pythonw*") { $Komut = "$Exe -m download_manager --magnet `"%1`"" }
Set-ItemProperty -Path "$Anahtar\shell\open\command" -Name "(default)" -Value $Komut
Set-ItemProperty -Path $Anahtar -Name "URL Protocol" -Value ""

Write-Output "magnet: baglantisi Retro+ icin kaydedildi (HKCU)."
Write-Output "Komut: $Komut"
