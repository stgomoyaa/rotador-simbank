# 🎮 Dashboard API - Comandos Disponibles

## 📡 Comandos Soportados por el Agente

El agente de control remoto ahora soporta los siguientes comandos:

### 1. `restart_pc`
Reinicia la PC del servidor
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "restart_pc"
}
```

### 2. `restart_herosms`
Reinicia la aplicación HeroSMS-Partners
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "restart_herosms"
}
```

### 3. `restart_rotador`
Reinicia el script RotadorSimBank.py
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "restart_rotador"
}
```

### 4. `stop_rotador`
Detiene el script RotadorSimBank.py
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "stop_rotador"
}
```

### 5. `update` ⭐
Fuerza la actualización del script RotadorSimBank.py a la última versión
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "update"
}
```

### 6. `get_logs` ⭐ NUEVO
Obtiene las últimas 100 líneas del log principal del rotador
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "get_logs"
}
```
**Respuesta:**
```json
{
  "success": true,
  "logs": "[2026-01-14 18:30:15] ✅ Rotación completada...\n...",
  "file": "rotador_simbank.log"
}
```

### 7. `get_activation_logs` ⭐ NUEVO
Obtiene las últimas 100 líneas del log de activación de SIMs
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "get_activation_logs"
}
```
**Respuesta:**
```json
{
  "success": true,
  "logs": "[2026-01-14 18:30:15] 📞 [COM5] Activación exitosa...\n...",
  "file": "log_activacion_rotador.txt"
}
```

### 8. `get_agent_logs` ⭐ NUEVO
Obtiene las últimas 50 líneas del log del agente
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "get_agent_logs"
}
```
**Respuesta:**
```json
{
  "success": true,
  "logs": "💓 Heartbeat enviado - CPU: 15%...\n...",
  "file": "agente_stdout.log"
}
```

---

## 🔄 Tareas Automáticas del Agente

El agente ejecuta las siguientes tareas automáticamente:

### 1. Verificación de Actualizaciones (cada 24 horas)
- ✅ Verifica si hay una nueva versión en GitHub
- ✅ Descarga e instala automáticamente
- ✅ Reinicia el script con la nueva versión

### 2. Reinicio de Hero-SMS (cada 2 horas) ⭐ NUEVO
- ✅ Reinicia Hero-SMS automáticamente cada 2 horas
- ✅ **Solo si el rotador NO está en ejecución** (para no interrumpir el proceso)
- ✅ Verifica que Hero-SMS esté corriendo antes de reiniciar
- ✅ Abre Hero-SMS automáticamente después de cerrarlo

**Logs en tiempo real:**
```
⏰ Han pasado 2 horas. Reiniciando Hero-SMS automáticamente...
✅ Hero-SMS reiniciado automáticamente
```

O si el rotador está corriendo:
```
⏭️  Saltando reinicio de Hero-SMS: Rotador está en ejecución
```

**Archivos de log del agente:**
- `agente_stdout.log` - Salida estándar (incluye reinicios automáticos)
- `agente_stderr.log` - Errores

---

## 🏥 Health Check Mejorado ⭐ NUEVO

El agente ahora envía información detallada del estado de los servicios en cada heartbeat:

### Estado de Hero-SMS:
```json
{
  "herosms": {
    "status": "running",
    "display": "✅ Running",
    "count": 1,
    "pids": [12345]
  }
}
```

O si está detenido:
```json
{
  "herosms": {
    "status": "stopped",
    "display": "❌ Stopped",
    "count": 0,
    "pids": []
  }
}
```

### Estado del Rotador:
```json
{
  "rotador": {
    "status": "running",
    "display": "✅ Running"
  }
}
```

### Timers:
```json
{
  "timers": {
    "next_update_check": 23,  // horas restantes
    "next_herosms_restart": 1  // horas restantes
  }
}
```

---

## 📋 Resumen de Comandos Disponibles

| Comando | Descripción | Desde API | Nuevo |
|---------|-------------|-----------|-------|
| `restart_pc` | Reinicia la PC | ✅ | |
| `restart_herosms` | Reinicia HeroSMS | ✅ | |
| `restart_rotador` | Reinicia el rotador | ✅ | |
| `stop_rotador` | Detiene el rotador | ✅ | |
| `update` | Actualiza el script | ✅ | |
| `get_logs` | **Lee log principal** | ✅ | ⭐ |
| `get_activation_logs` | **Lee log de activación** | ✅ | ⭐ |
| `get_agent_logs` | **Lee log del agente** | ✅ | ⭐ |

---

## 🎨 Actualización del Dashboard de Vercel

Para agregar el botón de **Actualizar** en tu dashboard, agrega este código:

### En tu componente de React/Next.js:

```jsx
// Agregar el botón de actualizar
<button
  onClick={() => sendCommand(machine.id, 'update')}
  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
  title="Forzar actualización del script"
>
  📥 Actualizar
</button>
```

### Ejemplo de función sendCommand:

```javascript
const sendCommand = async (machineId, command) => {
  try {
    const response = await fetch('/api/control', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.NEXT_PUBLIC_AUTH_TOKEN}`,
      },
      body: JSON.stringify({
        machine_id: machineId,
        action: 'command',
        command: command,
      }),
    });

    const data = await response.json();
    
    if (data.success) {
      alert(`✅ ${data.message}`);
    } else {
      alert(`❌ Error: ${data.message}`);
    }
  } catch (error) {
    alert(`❌ Error: ${error.message}`);
  }
};
```

---

## 🔐 Seguridad

**IMPORTANTE:** Todos los comandos requieren autenticación con Bearer Token:

```http
Authorization: Bearer tu_token_secreto_aqui
```

El token debe coincidir con:
- `AGENTE_AUTH_TOKEN` en `RotadorSimBank.py` (línea ~56)
- Variable de entorno en Vercel: `AUTH_TOKEN`

---

## 📊 Ejemplo de Dashboard Completo

```jsx
'use client'

import { useState, useEffect } from 'react'

export default function Dashboard() {
  const [machines, setMachines] = useState([])
  const [logs, setLogs] = useState({})
  const [showLogs, setShowLogs] = useState({})

  // Función para enviar comandos
  const sendCommand = async (machineId, command) => {
    try {
      const response = await fetch('/api/control', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.NEXT_PUBLIC_AUTH_TOKEN}`,
        },
        body: JSON.stringify({
          machine_id: machineId,
          action: 'command',
          command: command,
        }),
      })

      const data = await response.json()
      
      if (data.success) {
        alert(`✅ ${data.message}`)
        
        // Si es comando de logs, mostrarlos
        if (data.logs) {
          setLogs(prev => ({ ...prev, [machineId]: data.logs }))
          setShowLogs(prev => ({ ...prev, [machineId]: true }))
        }
      } else {
        alert(`❌ Error: ${data.message}`)
      }
    } catch (error) {
      alert(`❌ Error: ${error.message}`)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">🎮 Control Remoto - SimBank</h1>
      
      {machines.map(machine => (
        <div key={machine.id} className="bg-white shadow rounded-lg p-4 mb-4">
          {/* Header */}
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">{machine.id}</h2>
            <div className="text-sm text-gray-500">
              CPU: {machine.system?.cpu_percent}% | RAM: {machine.system?.memory_percent}%
            </div>
          </div>
          
          {/* Health Check */}
          <div className="mb-4 p-3 bg-gray-50 rounded">
            <h3 className="font-semibold mb-2">🏥 Estado de Servicios:</h3>
            <div className="grid grid-cols-2 gap-2">
              <div className="flex items-center">
                <span className="mr-2">{machine.services?.herosms?.display || '❓'}</span>
                <span className="text-sm">Hero-SMS</span>
                {machine.services?.herosms?.pids?.length > 0 && (
                  <span className="text-xs text-gray-500 ml-2">
                    (PID: {machine.services.herosms.pids.join(', ')})
                  </span>
                )}
              </div>
              <div className="flex items-center">
                <span className="mr-2">{machine.services?.rotador?.display || '❓'}</span>
                <span className="text-sm">Rotador SimBank</span>
              </div>
            </div>
            
            {/* Timers */}
            {machine.timers && (
              <div className="mt-2 text-xs text-gray-600">
                <div>⏰ Próxima actualización: {machine.timers.next_update_check}h</div>
                <div>🔄 Próximo reinicio Hero-SMS: {machine.timers.next_herosms_restart}h</div>
              </div>
            )}
          </div>
          
          {/* Botones de Control */}
          <div className="mb-4 space-x-2 space-y-2">
            <button onClick={() => sendCommand(machine.id, 'restart_pc')} 
                    className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition">
              🔄 Reiniciar PC
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'restart_herosms')} 
                    className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 transition">
              🔄 Reiniciar Hero-SMS
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'restart_rotador')} 
                    className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 transition">
              🔄 Reiniciar Rotador
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'stop_rotador')} 
                    className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition">
              🛑 Detener Rotador
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'update')} 
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition">
              📥 Actualizar Script
            </button>
          </div>
          
          {/* Botones de Logs ⭐ NUEVO */}
          <div className="mb-4 space-x-2">
            <button onClick={() => sendCommand(machine.id, 'get_logs')} 
                    className="px-3 py-1 bg-purple-500 text-white text-sm rounded hover:bg-purple-600 transition">
              📄 Ver Log Principal
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'get_activation_logs')} 
                    className="px-3 py-1 bg-purple-500 text-white text-sm rounded hover:bg-purple-600 transition">
              📄 Ver Log Activación
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'get_agent_logs')} 
                    className="px-3 py-1 bg-purple-500 text-white text-sm rounded hover:bg-purple-600 transition">
              📄 Ver Log Agente
            </button>
          </div>
          
          {/* Mostrar Logs */}
          {showLogs[machine.id] && logs[machine.id] && (
            <div className="mt-4 p-3 bg-black text-green-400 rounded font-mono text-xs overflow-x-auto">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold">📋 Logs:</span>
                <button 
                  onClick={() => setShowLogs(prev => ({ ...prev, [machine.id]: false }))}
                  className="text-red-400 hover:text-red-300"
                >
                  ✕ Cerrar
                </button>
              </div>
              <pre className="whitespace-pre-wrap">{logs[machine.id]}</pre>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
```

---

## 🧪 Pruebas

### Probar el comando de actualización localmente:

1. **Desde Python:**
   ```bash
   python RotadorSimBank.py --update
   ```

2. **Desde el dashboard:**
   - Envía el comando `update` a la máquina
   - Verifica los logs en `agente_stdout.log`

3. **Verificar logs del agente:**
   ```bash
   type agente_stdout.log
   ```

---

## 📝 Notas Importantes

1. **Verificación automática:** El agente verifica actualizaciones cada 24 horas sin intervención manual.

2. **Actualización forzada:** Puedes forzar una actualización en cualquier momento desde el dashboard enviando el comando `update`.

3. **Reinicio automático:** Cuando se actualiza el script, se reinicia automáticamente con la nueva versión.

4. **Rollback:** Si hay un problema con la actualización, el script crea un backup automático: `RotadorSimBank_backup_YYYYMMDD_HHMMSS.py`

5. **Logs:** Revisa `agente_stdout.log` y `agente_stderr.log` para ver el resultado de las actualizaciones.

---

## 🎯 Versión Actual

**Versión:** 2.9.0

**Nuevas características v2.9.0:**
- ✅ **Auto-reinicio de Hero-SMS cada 2 horas** (solo si no está corriendo el rotador)
- ✅ **Health check mejorado** con detección detallada de servicios (PIDs, conteo)
- ✅ **Comandos para leer logs remotamente** (`get_logs`, `get_activation_logs`, `get_agent_logs`)
- ✅ **Timers en tiempo real** (próxima actualización, próximo reinicio Hero-SMS)
- ✅ Verificación automática de actualizaciones cada 24 horas
- ✅ Comando `update` para forzar actualización desde el dashboard
- ✅ Logs detallados del proceso de actualización

---

## 🔗 Enlaces Útiles

- **Repositorio GitHub:** https://github.com/stgomoyaa/rotador-simbank
- **Dashboard Vercel:** https://claro-pool-dashboard.vercel.app
- **Documentación completa:** README.md
