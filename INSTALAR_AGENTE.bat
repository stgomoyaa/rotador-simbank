@echo off
echo ============================================================
echo   INSTALANDO AGENTE DE CONTROL REMOTO
echo ============================================================
echo.

echo [1/2] Instalando dependencias de Python...
pip install requests psutil

echo.
echo [2/2] Instalando NSSM (servicio de Windows)...
echo Descargando desde GitHub...

powershell -Command "& {Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'}"
powershell -Command "& {Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force}"
copy nssm-2.24\win64\nssm.exe nssm.exe
del nssm.zip
rmdir /s /q nssm-2.24

echo.
echo ============================================================
echo   DEPENDENCIAS INSTALADAS
echo ============================================================
echo.
echo Siguiente paso: Edita agente_control.py y configura:
echo   - API_URL (despues de hacer deploy en Vercel)
echo   - AUTH_TOKEN (genera un token seguro)
echo.
echo Luego ejecuta: INSTALAR_SERVICIO.bat
echo.
pause

