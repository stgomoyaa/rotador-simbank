@echo off
chcp 65001 >nul 2>&1

echo ============================================================
echo   ACTUALIZACION PARA SERVIDOR REMOTO - v2.10.1
echo ============================================================
echo.
echo Este script copia los archivos necesarios al servidor.
echo.
echo INSTRUCCIONES:
echo.
echo 1. Copia este archivo (ACTUALIZAR_SERVIDOR.bat) al servidor
echo 2. Copia tambien estos archivos al servidor (C:\Rotador):
echo    - RotadorSimBank.py
echo    - README.md
echo    - DASHBOARD_API.md
echo.
echo 3. En el servidor, ejecuta este .bat
echo.
echo ============================================================
pause

echo.
echo [1/3] Verificando archivos...
if not exist "RotadorSimBank.py" (
    echo [ERROR] RotadorSimBank.py no encontrado
    echo Asegurate de copiar RotadorSimBank.py a esta carpeta
    pause
    exit /b 1
)

echo [ENCONTRADO] RotadorSimBank.py
echo.

echo [2/3] Verificando version...
findstr /C:"VERSION = " RotadorSimBank.py
echo.

echo [3/3] Instalando dependencias...
python -m pip install --upgrade Pillow mss
echo.

echo [4/4] Reiniciando servicio del agente...
if exist "nssm.exe" (
    .\nssm.exe restart AgenteRotadorSimBank
    echo.
    echo [OK] Servicio reiniciado
    echo.
    timeout /t 5
    .\nssm.exe status AgenteRotadorSimBank
) else (
    echo [ADVERTENCIA] nssm.exe no encontrado
    echo El servicio no se pudo reiniciar automaticamente
    echo.
    echo Reinicia manualmente con:
    echo   nssm restart AgenteRotadorSimBank
)

echo.
echo ============================================================
echo   ACTUALIZACION COMPLETADA
echo ============================================================
echo.
echo Verifica en el dashboard que la maquina aparezca con v2.10.1
echo Dashboard: https://claro-pool-dashboard.vercel.app
echo.
pause
