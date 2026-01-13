@echo off
echo ============================================================
echo   INSTALANDO AGENTE COMO SERVICIO DE WINDOWS
echo ============================================================
echo.

:: Verificar permisos de administrador
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [ERROR] Debes ejecutar este script como Administrador
    echo Click derecho en el archivo y selecciona "Ejecutar como administrador"
    pause
    exit /b 1
)

:: Obtener la ruta actual
set "CURRENT_DIR=%CD%"
set "PYTHON_EXE=python"
set "SCRIPT_PATH=%CURRENT_DIR%\agente_control.py"

echo Directorio actual: %CURRENT_DIR%
echo Script: %SCRIPT_PATH%
echo.

:: Detener servicio si ya existe
echo [1/3] Deteniendo servicio existente (si existe)...
nssm stop AgenteRotadorSimBank >nul 2>&1
nssm remove AgenteRotadorSimBank confirm >nul 2>&1
echo.

:: Instalar servicio
echo [2/3] Instalando servicio...
nssm install AgenteRotadorSimBank "%PYTHON_EXE%" "%SCRIPT_PATH%"
nssm set AgenteRotadorSimBank AppDirectory "%CURRENT_DIR%"
nssm set AgenteRotadorSimBank DisplayName "Agente Rotador SimBank"
nssm set AgenteRotadorSimBank Description "Servicio de control remoto para RotadorSimBank"
nssm set AgenteRotadorSimBank Start SERVICE_AUTO_START
nssm set AgenteRotadorSimBank AppStdout "%CURRENT_DIR%\agente_stdout.log"
nssm set AgenteRotadorSimBank AppStderr "%CURRENT_DIR%\agente_stderr.log"
nssm set AgenteRotadorSimBank AppRotateFiles 1
nssm set AgenteRotadorSimBank AppRotateBytes 1048576
echo.

:: Iniciar servicio
echo [3/3] Iniciando servicio...
nssm start AgenteRotadorSimBank
echo.

echo ============================================================
echo   SERVICIO INSTALADO Y INICIADO
echo ============================================================
echo.
echo El agente ahora está corriendo como servicio de Windows.
echo Se iniciará automáticamente al encender el PC.
echo.
echo Comandos útiles:
echo   - Ver estado: nssm status AgenteRotadorSimBank
echo   - Detener: nssm stop AgenteRotadorSimBank
echo   - Reiniciar: nssm restart AgenteRotadorSimBank
echo   - Desinstalar: nssm remove AgenteRotadorSimBank confirm
echo.
echo Logs en:
echo   - %CURRENT_DIR%\agente_control.log
echo   - %CURRENT_DIR%\agente_stdout.log
echo   - %CURRENT_DIR%\agente_stderr.log
echo.
pause

