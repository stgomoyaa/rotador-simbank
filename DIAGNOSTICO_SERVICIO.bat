@echo off
chcp 65001 >nul 2>&1

:: Cambiar al directorio donde está el .bat
cd /d "%~dp0"

echo ============================================================
echo   DIAGNÓSTICO DEL SERVICIO - Agente Rotador SimBank
echo ============================================================
echo.

echo [1/5] Verificando ubicación...
echo Directorio actual: %CD%
echo.

echo [2/5] Verificando archivos...
if exist "RotadorSimBank.py" (
    echo ✅ RotadorSimBank.py encontrado
) else (
    echo ❌ RotadorSimBank.py NO encontrado
)

if exist "nssm.exe" (
    echo ✅ nssm.exe encontrado
) else (
    echo ❌ nssm.exe NO encontrado
)
echo.

echo [3/5] Verificando estado del servicio...
if exist "nssm.exe" (
    nssm status AgenteRotadorSimBank
) else (
    echo ⚠️  No se puede verificar: nssm.exe no encontrado
)
echo.

echo [4/5] Verificando logs...
if exist "agente_stdout.log" (
    echo ✅ agente_stdout.log encontrado
    echo.
    echo Últimas 20 líneas:
    echo ----------------------------------------
    powershell -Command "Get-Content 'agente_stdout.log' -Tail 20 -ErrorAction SilentlyContinue"
    echo ----------------------------------------
) else (
    echo ⚠️  agente_stdout.log NO encontrado (el servicio no se ha iniciado correctamente)
)
echo.

if exist "agente_stderr.log" (
    echo ✅ agente_stderr.log encontrado
    echo.
    echo Contenido de errores:
    echo ----------------------------------------
    type agente_stderr.log
    echo ----------------------------------------
) else (
    echo ℹ️  agente_stderr.log NO encontrado (sin errores registrados)
)
echo.

if exist "agente_error.log" (
    echo ⚠️  agente_error.log encontrado - ERRORES CRÍTICOS DETECTADOS
    echo.
    echo Contenido:
    echo ----------------------------------------
    type agente_error.log
    echo ----------------------------------------
) else (
    echo ℹ️  agente_error.log NO encontrado (sin errores críticos)
)
echo.

echo [5/5] Verificando Python...
python --version
echo.

echo ============================================================
echo   SUGERENCIAS DE SOLUCIÓN
echo ============================================================
echo.
echo Si el servicio está en estado PAUSED o no funciona:
echo.
echo 1. Prueba ejecutar el agente manualmente:
echo    python RotadorSimBank.py --agente
echo.
echo 2. Si funciona manualmente pero no como servicio:
echo    nssm restart AgenteRotadorSimBank
echo.
echo 3. Si sigue sin funcionar, reinstala el servicio:
echo    nssm remove AgenteRotadorSimBank confirm
echo    python RotadorSimBank.py --instalar-servicio
echo.
echo 4. Verifica que todas las dependencias estén instaladas:
echo    pip install pyserial rich psycopg2-binary requests psutil
echo.
echo ============================================================
echo   COMANDOS ÚTILES
echo ============================================================
echo.
echo - Ver estado:      nssm status AgenteRotadorSimBank
echo - Detener:         nssm stop AgenteRotadorSimBank
echo - Iniciar:         nssm start AgenteRotadorSimBank
echo - Reiniciar:       nssm restart AgenteRotadorSimBank
echo - Desinstalar:     nssm remove AgenteRotadorSimBank confirm
echo - Ver logs:        type agente_stdout.log
echo - Ejecutar manual: python RotadorSimBank.py --agente
echo.
pause
