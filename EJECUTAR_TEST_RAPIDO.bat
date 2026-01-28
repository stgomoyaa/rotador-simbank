@echo off
chcp 65001 > nul
title ⚡ Test Rápido de Capturas - Rotador SimBank

:: Navegar al directorio del script
cd /d "%~dp0"

echo.
echo ============================================
echo   ⚡ TEST RÁPIDO DE CAPTURAS DE SLOTS
echo ============================================
echo.
echo Este test optimizado:
echo   • Tiempo por slot: ~5 minutos
echo   • Tiempo total: ~2.5 horas
echo   • Verifica cambios de slot
echo   • Más rápido y eficiente
echo.
echo ============================================
echo.

:: Ejecutar el script Python de test rápido
python test_capturas_rapido.py

echo.
echo ============================================
echo   Test completado
echo ============================================
echo.
pause
