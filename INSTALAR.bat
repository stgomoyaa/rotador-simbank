@echo off
chcp 65001 >nul 2>&1
echo ============================================================
echo   INSTALACION COMPLETA - Rotador SimBank v2.8.0
echo   Incluye: Dependencias + Agente de Control Remoto
echo ============================================================
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
python -m pip install pyserial rich psycopg2-binary requests psutil

if %errorLevel% NEQ 0 (
    echo.
    echo [ERROR] Hubo un problema instalando las dependencias
    echo.
    echo Intenta ejecutar manualmente:
    echo   python -m pip install pyserial rich psycopg2-binary requests psutil
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] Instalando Agente de Control Remoto como servicio...
echo.
python RotadorSimBank.py --instalar-servicio

if %errorLevel% NEQ 0 (
    echo.
    echo [ADVERTENCIA] Hubo un problema instalando el servicio
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
echo Servicios instalados:
echo   1. Dependencias Python (pyserial, rich, psycopg2, requests, psutil)
echo   2. Agente de Control Remoto (servicio de Windows)
echo.
echo El agente se iniciara automaticamente al encender el PC.
echo.
echo COMANDOS UTILES:
echo   - Ejecutar rotador:     python RotadorSimBank.py
echo   - Modo continuo:        python RotadorSimBank.py --modo-continuo
echo   - Detectar SIM Banks:   python RotadorSimBank.py --detectar-simbanks
echo   - Estado del servicio:  nssm status AgenteRotadorSimBank
echo.
echo Dashboard de control remoto:
echo   https://claro-pool-dashboard.vercel.app
echo.
pause
