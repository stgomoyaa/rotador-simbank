@echo off
REM ============================================
REM Rotador SimBank - Modo Mantenimiento Continuo
REM ============================================
REM Este script ejecuta el rotador en modo mantenimiento:
REM - Loop infinito (nunca se detiene)
REM - Activación masiva cada 24 horas
REM - Reinicio HeroSMS cada 1 hora
REM ============================================

title Rotador SimBank - Modo Mantenimiento Continuo
color 0A

echo.
echo ============================================
echo   ROTADOR SIMBANK - MODO MANTENIMIENTO
echo ============================================
echo.
echo Este modo:
echo   * Ejecuta activacion masiva cada 24 horas
echo   * Reinicia HeroSMS cada 1 hora
echo   * Loop infinito (nunca se detiene)
echo.
echo Presiona Ctrl+C para detener en cualquier momento
echo ============================================
echo.

REM Ejecutar en modo mantenimiento
python RotadorSimBank.py --modo-mantenimiento

echo.
echo ============================================
echo   Modo mantenimiento detenido
echo ============================================
echo.
pause
