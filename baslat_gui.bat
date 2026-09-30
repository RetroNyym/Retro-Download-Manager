@echo off
setlocal
cd /d "%~dp0"

rem ------------------------------------------------------------
rem  Retro+ Download Manager - konsolsuz baslatici
rem
rem  pythonw.exe ile baslatilir: arka planda CMD/konsol
rem  penceresi olusmaz. Tamamen sessiz acilim (pencere bile
rem  gozukmeden) icin baslat_gui.vbs dosyasini kullanin.
rem
rem  Test:  baslat_gui.bat --dry-run   (sadece bulunacak
rem         python yolunu yazar, programi acmaz)
rem ------------------------------------------------------------

set "PYW="

rem 1) PATH icindeki pythonw.exe
for /f "delims=" %%I in ('where pythonw.exe 2^>nul') do if not defined PYW set "PYW=%%~fI"

rem 2) Yaygin kurulum klasorleri (PATH'e eklenmemis kurulumlar)
if not defined PYW for %%V in (314 313 312 311 310 39 38) do (
    if not defined PYW if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python%%V\pythonw.exe"
)

rem 3) Python baslatucusu (pyw.exe): kurulu varsayilan surumu acar
if not defined PYW if exist "%WINDIR%\pyw.exe" set "PYW=%WINDIR%\pyw.exe"

if not defined PYW goto :hata

if /i "%~1"=="--dry-run" (
    echo PYW=%PYW%
    endlocal
    exit /b 0
)

rem pythonw.exe konsolsuz calisir; hicbir pencere olusmaz
start "" "%PYW%" -m download_manager
endlocal
exit /b 0

:hata
echo.
echo  [HATA] pythonw.exe bulunamadi, program baslatilamadi.
echo  Python 3 kurun:  winget install Python.Python.3.13
echo  Elle deneyin:    python -m download_manager
echo.
powershell -NoProfile -WindowStyle Hidden -Command "Add-Type -AssemblyName PresentationFramework; [void][System.Windows.MessageBox]::Show('pythonw.exe could not be found. Install Python 3: winget install Python.Python.3.13','Retro+ Download Manager','OK','Error')"
timeout /t 10 >nul
endlocal
exit /b 1
