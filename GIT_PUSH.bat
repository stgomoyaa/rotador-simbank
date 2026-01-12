@echo off
echo ============================================================
echo   SUBIR A GITHUB - Rotador SimBank v2.6.0
echo ============================================================
echo.

REM Inicializar si no existe
if not exist ".git" (
    echo [1/6] Inicializando Git...
    git init
    git branch -M main
) else (
    echo [1/6] Repositorio ya existe
)

echo.
echo [2/6] Configurando repositorio remoto...
git remote remove origin 2>nul
git remote add origin https://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@github.com/stgomoyaa/rotador-simbank.git

echo.
echo [3/6] Verificando archivos...
git status

echo.
echo [4/6] Agregando archivos...
git add .

echo.
echo [5/6] Creando commit...
git commit -m "v2.6.0: Auto-update, PostgreSQL integration, and database export"

echo.
echo [6/6] Subiendo a GitHub...
git push -u origin main --force

echo.
echo ============================================================
echo   COMPLETADO
echo ============================================================
echo.
echo Repositorio: https://github.com/stgomoyaa/rotador-simbank
echo.
pause

