@echo off
REM ============================================
REM Test de Capturas de Slots - Rotador SimBank
REM ============================================
REM Este script hace capturas de pantalla de
REM HeroSMS en todos los slots (1-32) para
REM verificación visual
REM ============================================

title Test Capturas Slots - Rotador SimBank
color 0E

echo.
echo ============================================
echo   TEST DE CAPTURAS DE SLOTS
echo ============================================
echo.
echo Este test hara lo siguiente para cada slot:
echo   1. Cerrar HeroSMS
echo   2. Rotar al slot
echo   3. Abrir HeroSMS
echo   4. Esperar 2 minutos
echo   5. Capturar pantalla
echo   6. Cerrar HeroSMS
echo   7. Repetir hasta slot 32
echo.
echo Tiempo estimado: ~1.5 horas
echo ============================================
echo.

REM Ejecutar script de test
python test_capturas_slots.py

echo.
echo ============================================
echo   Test completado
echo ============================================
echo.
pause
