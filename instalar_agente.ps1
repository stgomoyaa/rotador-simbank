# encoding: utf-8
# Script para instalar el Agente de Control Remoto como Tarea Programada
# Rotador SimBank v2.10.3

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  INSTALANDO AGENTE DE CONTROL REMOTO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Obtener rutas
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
$scriptPath = Join-Path $PSScriptRoot "RotadorSimBank.py"
$workDir = $PSScriptRoot

if (-not $pythonPath) {
    Write-Host "ERROR: No se encontro Python en el PATH" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: No se encontro RotadorSimBank.py en $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "Python:   $pythonPath" -ForegroundColor Green
Write-Host "Script:   $scriptPath" -ForegroundColor Green
Write-Host "WorkDir:  $workDir" -ForegroundColor Green
Write-Host ""

# Eliminar tarea si ya existe
Write-Host "[1/5] Eliminando tarea anterior (si existe)..." -ForegroundColor Yellow
Unregister-ScheduledTask -TaskName "AgenteRotadorSimBank" -Confirm:$false -ErrorAction SilentlyContinue

# Crear la accion (ejecutar el script)
Write-Host "[2/5] Creando accion de ejecucion..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`" --agente" -WorkingDirectory $workDir

# Crear el trigger (iniciar al login del usuario actual)
Write-Host "[3/5] Configurando inicio automatico..." -ForegroundColor Yellow
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Configurar principal (usuario actual, con privilegios elevados)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

# Configuraciones adicionales (reinicio automatico, etc.)
Write-Host "[4/5] Configurando opciones avanzadas..." -ForegroundColor Yellow
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

# Registrar la tarea
Write-Host "[5/5] Registrando tarea programada..." -ForegroundColor Yellow
try {
    Register-ScheduledTask -TaskName "AgenteRotadorSimBank" -Description "Agente de control remoto para Rotador SimBank - Se ejecuta automaticamente al iniciar sesion" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -ErrorAction Stop | Out-Null
    
    Write-Host ""
    Write-Host "Tarea programada creada exitosamente!" -ForegroundColor Green
    
    # Iniciar la tarea inmediatamente
    Write-Host ""
    Write-Host "Iniciando el agente..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName "AgenteRotadorSimBank" -ErrorAction Stop
    
    # Esperar un poco y verificar
    Start-Sleep -Seconds 3
    
    $task = Get-ScheduledTask -TaskName "AgenteRotadorSimBank"
    Write-Host ""
    Write-Host "Estado de la tarea:" -ForegroundColor Cyan
    Write-Host "   Nombre:         $($task.TaskName)" -ForegroundColor White
    Write-Host "   Estado:         $($task.State)" -ForegroundColor White
    Write-Host "   Ultima ejecucion: $(if ($task.LastRunTime) { $task.LastRunTime } else { 'Nunca' })" -ForegroundColor White
    
    # Verificar proceso Python
    Start-Sleep -Seconds 2
    $pythonProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*$pythonPath*" }
    if ($pythonProcess) {
        Write-Host ""
        Write-Host "El agente esta ejecutandose (PID: $($pythonProcess.Id))" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "El agente se inicio pero no se detecta el proceso" -ForegroundColor Yellow
        Write-Host "   Esto es normal si se esta inicializando. Espera 30 segundos y verifica:" -ForegroundColor Yellow
        Write-Host "   Get-Content `"$workDir\agente_stdout.log`" -Tail 20" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "Instalacion completada!" -ForegroundColor Green
    Write-Host "   La tarea se ejecutara automaticamente al iniciar sesion." -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "Error al registrar la tarea:" -ForegroundColor Red
    Write-Host "   $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
