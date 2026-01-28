@echo off
chcp 65001 >nul 2>&1

:: Cambiar al directorio donde está el .bat (IMPORTANTE para ejecución como Admin)
cd /d "%~dp0"

echo ============================================================
echo   INSTALACION COMPLETA - Rotador SimBank v2.10.3
echo   Incluye: Dependencias + Agente (Tarea Programada)
echo ============================================================
echo.
echo Directorio de trabajo: %CD%
echo.

:: Verificar permisos de administrador
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [ERROR] Debes ejecutar este script como Administrador
    echo Click derecho en el archivo y selecciona "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

:: Verificar que Python este instalado
echo [Verificando Python...]
python --version >nul 2>&1
if %errorLevel% NEQ 0 (
    echo.
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo.
    echo Por favor instala Python 3.7+ desde:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Durante la instalacion, marca la opcion:
    echo   [X] Add Python to PATH
    echo.
    pause
    exit /b 1
)

python --version
echo.

echo [1/2] Instalando dependencias de Python...
echo.

:: Usar python -m pip en lugar de pip directamente (mas compatible)
python -m pip install --upgrade pip
python -m pip install pyserial rich psycopg2-binary requests psutil Pillow mss

if %errorLevel% NEQ 0 (
    echo.
    echo [ERROR] Hubo un problema instalando las dependencias
    echo.
    echo Intenta ejecutar manualmente:
    echo   python -m pip install pyserial rich psycopg2-binary requests psutil Pillow
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] Instalando Agente de Control Remoto como tarea programada...
echo.

:: Verificar que RotadorSimBank.py existe
if not exist "RotadorSimBank.py" (
    echo.
    echo [ERROR] No se encuentra RotadorSimBank.py en este directorio
    echo Directorio actual: %CD%
    echo.
    echo Asegurate de ejecutar este script desde la carpeta donde esta RotadorSimBank.py
    echo.
    pause
    exit /b 1
)

:: Verificar que el script PowerShell existe
if not exist "instalar_agente.ps1" (
    echo.
    echo [ERROR] No se encuentra instalar_agente.ps1
    echo.
    echo Este archivo es necesario para la instalacion.
    echo.
    pause
    exit /b 1
)

:: Ejecutar el script PowerShell para crear la tarea programada
powershell -ExecutionPolicy Bypass -File "%~dp0instalar_agente.ps1"

if %errorLevel% NEQ 0 (
    echo.
    echo [ADVERTENCIA] Hubo un problema instalando la tarea programada
    echo.
    echo Puedes ejecutar el agente manualmente con:
    echo   python RotadorSimBank.py --agente
    echo.
)

echo.
echo ============================================================
echo   INSTALACION COMPLETADA
echo ============================================================
echo.
echo Componentes instalados:
echo   1. Dependencias Python (pyserial, rich, psycopg2, requests, psutil, Pillow, mss)
echo   2. Agente de Control Remoto (Tarea Programada de Windows)
echo.
echo El agente se iniciara automaticamente al iniciar sesion en Windows.
echo.
echo COMANDOS UTILES:
echo   - Ejecutar rotador:         python RotadorSimBank.py
echo   - Modo continuo:            python RotadorSimBank.py --modo-continuo
echo   - Detectar SIM Banks:       python RotadorSimBank.py --detectar-simbanks
echo   - Ver estado de la tarea:   Get-ScheduledTask -TaskName "AgenteRotadorSimBank"
echo   - Iniciar tarea:            Start-ScheduledTask -TaskName "AgenteRotadorSimBank"
echo   - Detener tarea:            Stop-ScheduledTask -TaskName "AgenteRotadorSimBank"
echo.
echo Dashboard de control remoto:
echo   https://claro-pool-dashboard.vercel.app
echo.
pause
