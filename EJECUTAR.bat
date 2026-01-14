@echo off
echo ============================================================
echo   ROTADOR SIMBANK v2.7.0
echo ============================================================
echo.
echo Seleccione el modo de ejecucion:
echo.
echo   [1] Activacion Masiva (1024 SIMs) - RECOMENDADO
echo   [2] Modo Continuo (rotacion cada 30 minutos)
echo   [3] Self-Test (probar conexiones)
echo   [4] Exportar base de datos
echo   [5] Limpiar duplicados
echo.
set /p opcion="Ingrese el numero de opcion: "

if "%opcion%"=="1" (
    echo.
    echo Ejecutando Activacion Masiva...
    python RotadorSimBank.py
) else if "%opcion%"=="2" (
    echo.
    echo Ejecutando Modo Continuo...
    python RotadorSimBank.py --modo-continuo
) else if "%opcion%"=="3" (
    echo.
    echo Ejecutando Self-Test...
    python RotadorSimBank.py --self-test
) else if "%opcion%"=="4" (
    echo.
    echo Exportando base de datos...
    python RotadorSimBank.py --export-db
) else if "%opcion%"=="5" (
    echo.
    echo Limpiando duplicados...
    python RotadorSimBank.py --clean-duplicates
) else (
    echo.
    echo Opcion invalida. Ejecutando modo por defecto (Activacion Masiva)...
    python RotadorSimBank.py
)

pause
