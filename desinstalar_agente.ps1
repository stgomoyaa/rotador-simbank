# Script para desinstalar el Agente de Control Remoto
# Rotador SimBank v2.10.3

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  DESINSTALANDO AGENTE DE CONTROL REMOTO" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Verificar si la tarea existe
$task = Get-ScheduledTask -TaskName "AgenteRotadorSimBank" -ErrorAction SilentlyContinue

if (-not $task) {
    Write-Host "⚠️  La tarea 'AgenteRotadorSimBank' no está instalada." -ForegroundColor Yellow
    Write-Host "`nNo hay nada que desinstalar.`n" -ForegroundColor White
    exit 0
}

Write-Host "📋 Tarea encontrada:" -ForegroundColor Cyan
Write-Host "   Nombre:  $($task.TaskName)" -ForegroundColor White
Write-Host "   Estado:  $($task.State)" -ForegroundColor White
Write-Host ""

# Detener la tarea si está corriendo
if ($task.State -eq "Running") {
    Write-Host "[1/2] Deteniendo tarea..." -ForegroundColor Yellow
    try {
        Stop-ScheduledTask -TaskName "AgenteRotadorSimBank" -ErrorAction Stop
        Write-Host "✅ Tarea detenida" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  No se pudo detener la tarea: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "[1/2] La tarea no está corriendo" -ForegroundColor Gray
}

# Eliminar la tarea
Write-Host "[2/2] Eliminando tarea..." -ForegroundColor Yellow
try {
    Unregister-ScheduledTask -TaskName "AgenteRotadorSimBank" -Confirm:$false -ErrorAction Stop
    Write-Host "✅ Tarea eliminada exitosamente" -ForegroundColor Green
    
    # Verificar que se eliminó
    $taskCheck = Get-ScheduledTask -TaskName "AgenteRotadorSimBank" -ErrorAction SilentlyContinue
    if (-not $taskCheck) {
        Write-Host "`n✅ Desinstalación completada!" -ForegroundColor Green
        Write-Host "   El agente ya no se ejecutará automáticamente.`n" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️  La tarea aún aparece en el sistema" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Error al eliminar la tarea:" -ForegroundColor Red
    Write-Host "   $_" -ForegroundColor Red
    exit 1
}
