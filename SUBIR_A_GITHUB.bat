@echo off
echo ============================================================
echo   SUBIR A GITHUB - Rotador SimBank v2.6.1
echo ============================================================
echo.

REM Verificar si Git esta instalado
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git no esta instalado
    pause
    exit /b 1
)

echo [1/5] Verificando estado...
git status

echo.
echo [2/5] Agregando archivos...
git add .

echo.
echo [3/5] Creando commit...
git commit -m "v2.6.1: Fixed PostgreSQL fecha_actualizacion column error"

echo.
echo [4/5] Subiendo a GitHub...
git push

if errorlevel 1 (
    echo.
    echo [!] Si es la primera vez, intenta:
    git push -u origin main
)

echo.
echo [5/5] Verificando...
git log --oneline -n 3

echo.
echo ============================================================
echo   COMPLETADO
echo ============================================================
echo.
echo Repositorio: https://github.com/stgomoyaa/rotador-simbank
echo.
pause

