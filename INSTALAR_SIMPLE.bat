@echo off
chcp 65001 >nul 2>&1
echo ============================================================
echo   INSTALACION SIMPLE - Solo Dependencias
echo ============================================================
echo.

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

echo Instalando dependencias de Python...
echo.

python -m pip install --upgrade pip
python -m pip install pyserial rich psycopg2-binary requests psutil

if %errorLevel% NEQ 0 (
    echo.
    echo [ERROR] Hubo un problema instalando las dependencias
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   INSTALACION COMPLETADA
echo ============================================================
echo.
echo Dependencias instaladas exitosamente!
echo.
echo Ahora puedes ejecutar:
echo   python RotadorSimBank.py
echo.
pause
