@echo off
chcp 65001 >nul 2>&1

:: Cambiar al directorio donde está el .bat
cd /d "%~dp0"

echo ============================================================
echo   DESCARGADOR DE NSSM - Rotador SimBank
echo ============================================================
echo.

:: Verificar si nssm.exe ya existe
if exist "nssm.exe" (
    echo [OK] nssm.exe ya existe en este directorio
    echo.
    echo Ubicacion: %CD%\nssm.exe
    echo.
    pause
    exit /b 0
)

echo Descargando NSSM usando PowerShell...
echo.

:: Usar PowerShell para descargar (ignora certificados SSL)
powershell -Command "& {[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}; Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip' -UserAgent 'Mozilla/5.0'}"

if %errorLevel% NEQ 0 (
    echo.
    echo [ERROR] No se pudo descargar NSSM automaticamente
    echo.
    echo Por favor, descarga manualmente:
    echo   1. Ve a: https://nssm.cc/release/nssm-2.24.zip
    echo   2. Descarga el archivo
    echo   3. Extrae "nssm-2.24\win64\nssm.exe"
    echo   4. Copia nssm.exe a: %CD%
    echo.
    pause
    exit /b 1
)

echo.
echo Extrayendo nssm.exe...
echo.

:: Extraer usando PowerShell
powershell -Command "& {Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force}"

if %errorLevel% NEQ 0 (
    echo.
    echo [ERROR] No se pudo extraer nssm.zip
    echo.
    pause
    exit /b 1
)

:: Copiar nssm.exe a la carpeta actual
copy "nssm-2.24\win64\nssm.exe" "nssm.exe"

if %errorLevel% NEQ 0 (
    echo.
    echo [ERROR] No se pudo copiar nssm.exe
    echo.
    pause
    exit /b 1
)

:: Limpiar archivos temporales
del nssm.zip
rmdir /s /q nssm-2.24

echo.
echo ============================================================
echo   DESCARGA COMPLETADA
echo ============================================================
echo.
echo nssm.exe esta listo en: %CD%\nssm.exe
echo.
echo Ahora puedes ejecutar:
echo   python RotadorSimBank.py --instalar-servicio
echo.
pause
