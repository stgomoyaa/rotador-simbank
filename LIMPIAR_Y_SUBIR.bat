@echo off
echo ============================================================
echo   LIMPIANDO HISTORIAL Y SUBIENDO - Rotador SimBank v2.6.1
echo ============================================================
echo.
echo Este script limpiara el historial de Git para eliminar el token
echo y subira una version limpia a GitHub.
echo.
pause

echo.
echo [1/6] Eliminando commits con el token...
git reset --soft HEAD~2

echo.
echo [2/6] Eliminando archivos del staging...
git reset

echo.
echo [3/6] Agregando archivos (sin .bat gracias a .gitignore)...
git add .

echo.
echo [4/6] Verificando que archivos se van a subir...
git status

echo.
echo [5/6] Creando commit limpio (SIN TOKEN)...
git commit -m "v2.6.1: PostgreSQL integration with auto-update (cleaned history)"

echo.
echo [6/6] Subiendo a GitHub con force...
git push -u origin main --force

echo.
echo ============================================================
echo   COMPLETADO
echo ============================================================
echo.
echo El historial ha sido limpiado y el codigo esta en GitHub
echo sin ningun token expuesto.
echo.
pause

