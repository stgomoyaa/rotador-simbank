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

### 2. `start_herosms` ⭐ NUEVO
Inicia HeroSMS-Partners (si no está corriendo)
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "start_herosms"
}
```

### 3. `restart_herosms`
Reinicia la aplicación HeroSMS-Partners
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "restart_herosms"
}
```

### 4. `start_rotador` ⭐ NUEVO
Inicia el script RotadorSimBank.py (si no está corriendo)
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "start_rotador"
}
```

### 5. `restart_rotador`
Reinicia el script RotadorSimBank.py
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "restart_rotador"
}
```

### 6. `stop_rotador`
Detiene el script RotadorSimBank.py
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "stop_rotador"
}
```

### 7. `restart_agent` ⭐ NUEVO
Reinicia el servicio del agente de control remoto
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "restart_agent"
}
```
**Nota:** Útil si el agente necesita reiniciarse después de una actualización o si no responde correctamente.

### 8. `update`
Fuerza la actualización del script RotadorSimBank.py a la última versión
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "update"
}
```

### 9. `get_logs`
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

### 10. `get_activation_logs`
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

### 11. `get_agent_logs`
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

### 12. `set_name:Nombre`
Cambia el nombre personalizado de la máquina (solo para el dashboard, no en el sistema)
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "set_name:Servidor Pool 1"
}
```
**Respuesta:**
```json
{
  "success": true,
  "message": "Nombre cambiado a: Servidor Pool 1"
}
```

**Nota:** El formato del comando es `set_name:` seguido del nombre deseado. El nombre se guardará en `machine_config.json` y se enviará en cada heartbeat.

### 13. `take_screenshot`
Captura la pantalla de la máquina y la retorna en base64
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "take_screenshot"
}
```
**Respuesta:**
```json
{
  "success": true,
  "message": "Captura de pantalla realizada",
  "screenshot": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "format": "jpeg"
}
```

**Notas sobre capturas:**
- La imagen se redimensiona automáticamente a max 1280px de ancho
- Se comprime en JPEG con calidad 75% para reducir tamaño
- Se codifica en base64 para transmisión
- Tamaño aproximado: 100-300 KB por captura

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

| Comando | Descripción | Desde API | Nuevo v2.10.0 |
|---------|-------------|-----------|---------------|
| `restart_pc` | Reinicia la PC | ✅ | |
| `start_herosms` | **Inicia HeroSMS** | ✅ | ⭐ |
| `restart_herosms` | Reinicia HeroSMS | ✅ | |
| `start_rotador` | **Inicia el rotador** | ✅ | ⭐ |
| `restart_rotador` | Reinicia el rotador | ✅ | |
| `stop_rotador` | Detiene el rotador | ✅ | |
| `restart_agent` | **Reinicia el agente** | ✅ | ⭐ |
| `update` | Actualiza el script | ✅ | |
| `get_logs` | Lee log principal | ✅ | |
| `get_activation_logs` | Lee log de activación | ✅ | |
| `get_agent_logs` | Lee log del agente | ✅ | |
| `set_name:Nombre` | **Cambia nombre de máquina** | ✅ | ⭐ |
| `take_screenshot` | **Captura de pantalla** | ✅ | ⭐ |

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
  const [screenshots, setScreenshots] = useState({})
  const [showScreenshot, setShowScreenshot] = useState({})
  const [renamingMachine, setRenamingMachine] = useState(null)
  const [newName, setNewName] = useState("")

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
        // Si es captura de pantalla, mostrarla
        if (data.screenshot) {
          const img = `data:image/${data.format};base64,${data.screenshot}`
          setScreenshots(prev => ({ ...prev, [machineId]: img }))
          setShowScreenshot(prev => ({ ...prev, [machineId]: true }))
        }
        // Si es comando de logs, mostrarlos
        else if (data.logs) {
          setLogs(prev => ({ ...prev, [machineId]: data.logs }))
          setShowLogs(prev => ({ ...prev, [machineId]: true }))
        }
        // Otros comandos
        else {
          alert(`✅ ${data.message}`)
        }
      } else {
        alert(`❌ Error: ${data.message}`)
      }
    } catch (error) {
      alert(`❌ Error: ${error.message}`)
    }
  }
  
  // Función para cambiar nombre
  const handleRename = async (machineId) => {
    if (!newName.trim()) {
      alert("El nombre no puede estar vacío")
      return
    }
    await sendCommand(machineId, `set_name:${newName}`)
    setRenamingMachine(null)
    setNewName("")
    // Refrescar lista de máquinas
    // fetchMachines()
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">🎮 Control Remoto - SimBank</h1>
      
      {machines.map(machine => (
        <div key={machine.id} className="bg-white shadow rounded-lg p-4 mb-4">
          {/* Header */}
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-semibold">
                {machine.machine_info?.custom_name || machine.id}
                {machine.machine_info?.custom_name !== machine.id && (
                  <span className="text-xs text-gray-500 ml-2">({machine.id})</span>
                )}
              </h2>
              {renamingMachine === machine.id ? (
                <div className="mt-2 flex gap-2">
                  <input 
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="Nuevo nombre"
                    className="px-2 py-1 border rounded text-sm"
                  />
                  <button 
                    onClick={() => handleRename(machine.id)}
                    className="px-3 py-1 bg-green-500 text-white text-sm rounded"
                  >
                    ✓ Guardar
                  </button>
                  <button 
                    onClick={() => setRenamingMachine(null)}
                    className="px-3 py-1 bg-gray-400 text-white text-sm rounded"
                  >
                    ✕ Cancelar
                  </button>
                </div>
              ) : (
                <button 
                  onClick={() => {
                    setRenamingMachine(machine.id)
                    setNewName(machine.machine_info?.custom_name || machine.id)
                  }}
                  className="mt-1 text-xs text-blue-500 hover:text-blue-700"
                >
                  ✏️  Cambiar nombre
                </button>
              )}
            </div>
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
          <div className="mb-4 flex flex-wrap gap-2">
            <button onClick={() => sendCommand(machine.id, 'restart_pc')} 
                    className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition">
              🔄 Reiniciar PC
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'start_herosms')} 
                    className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition">
              🟢 Iniciar Hero-SMS
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'restart_herosms')} 
                    className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 transition">
              🔄 Reiniciar Hero-SMS
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'start_rotador')} 
                    className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition">
              🟢 Iniciar Rotador
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
            
            <button onClick={() => sendCommand(machine.id, 'take_screenshot')} 
                    className="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600 transition">
              📸 Captura de Pantalla
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
            <div className="mt-4 p-3 bg-black text-green-400 rounded font-mono text-xs overflow-x-auto max-h-96">
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
          
          {/* Mostrar Captura de Pantalla ⭐ NUEVO */}
          {showScreenshot[machine.id] && screenshots[machine.id] && (
            <div className="mt-4 p-3 bg-gray-100 rounded">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold">📸 Captura de Pantalla:</span>
                <div className="flex gap-2">
                  <a 
                    href={screenshots[machine.id]} 
                    download={`screenshot-${machine.id}-${Date.now()}.jpg`}
                    className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
                  >
                    💾 Descargar
                  </a>
                  <button 
                    onClick={() => setShowScreenshot(prev => ({ ...prev, [machine.id]: false }))}
                    className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
                  >
                    ✕ Cerrar
                  </button>
                </div>
              </div>
              <img 
                src={screenshots[machine.id]} 
                alt="Screenshot" 
                className="w-full rounded shadow-lg cursor-pointer"
                onClick={() => window.open(screenshots[machine.id], '_blank')}
              />
              <p className="text-xs text-gray-500 mt-2">
                Click en la imagen para verla en tamaño completo
              </p>
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

---

## 🏗️ ARQUITECTURA DEL SISTEMA COMPLETO

### Flujo de Comunicación:

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Dashboard     │  HTTP   │  Vercel API      │  HTTP   │ Agente Local    │
│   (Frontend)    │ ◄────► │  (Backend KV)    │ ◄────► │ (Servidor)      │
└─────────────────┘         └──────────────────┘         └─────────────────┘
      │                              │                            │
      │                              │                            │
   Usuario                      Redis/KV Storage            RotadorSimBank.py
   Envía Cmd                    • Commands Queue            • Poll cada 10s
   Ve Status                    • Machines State            • Ejecuta comandos
                                • Command Results           • Envía heartbeat
```

---

## ⚠️ PROBLEMAS DETECTADOS EN TU DASHBOARD

### 🔴 **Problema 1: Backend No Almacena Respuestas de Comandos**

**Síntoma:** Los logs no se muestran aunque el comando se envió correctamente.

**Causa:** Tu API de Vercel NO está guardando las respuestas del agente en Vercel KV.

**Solución requerida:**

```typescript
// app/api/commands/route.ts (DEBE IMPLEMENTARSE)

import { kv } from '@vercel/kv'

export async function POST(request: Request) {
  const body = await request.json()
  const { machine_id, action, status, result } = body
  
  if (action === 'response') {
    // ✅ CRÍTICO: Guardar respuesta del agente
    const commandId = result.command_id
    
    await kv.set(`command_result:${machine_id}:${commandId}`, {
      success: result.success,
      message: result.message,
      logs: result.logs,          // Para comandos get_logs
      screenshot: result.screenshot, // Para take_screenshot
      timestamp: Date.now()
    }, { ex: 3600 }) // Expira en 1 hora
    
    return Response.json({ success: true })
  }
  
  if (action === 'command') {
    // Guardar comando pendiente
    await kv.rpush(`commands:${machine_id}`, body.command)
    return Response.json({ success: true, command_id: crypto.randomUUID() })
  }
  
  return Response.json({ error: 'Invalid action' }, { status: 400 })
}
```

---

### 🔴 **Problema 2: Frontend No Hace Polling de Resultados**

**Síntoma:** El dashboard dice "Comando enviado" pero nunca muestra la respuesta.

**Causa:** El frontend envía el comando pero NO espera/busca la respuesta.

**Solución requerida:**

```typescript
// components/Dashboard.tsx

const [commandResults, setCommandResults] = useState({})
const [pendingCommands, setPendingCommands] = useState({})

const sendCommand = async (machineId, command) => {
  try {
    // 1. Enviar comando
    const response = await fetch('/api/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        machine_id: machineId,
        action: 'command',
        command: command
      })
    })
    
    const { command_id } = await response.json()
    
    // 2. ✅ CRÍTICO: Hacer polling del resultado
    setPendingCommands(prev => ({ ...prev, [command_id]: true }))
    
    pollCommandResult(machineId, command_id, command)
    
  } catch (error) {
    alert(`❌ Error: ${error.message}`)
  }
}

const pollCommandResult = async (machineId, commandId, commandType) => {
  let attempts = 0
  const maxAttempts = 30 // 30 segundos
  
  const interval = setInterval(async () => {
    attempts++
    
    try {
      const response = await fetch(`/api/command-result?machine_id=${machineId}&command_id=${commandId}`)
      const result = await response.json()
      
      if (result.success && result.data) {
        clearInterval(interval)
        setPendingCommands(prev => {
          const newState = { ...prev }
          delete newState[commandId]
          return newState
        })
        
        // Mostrar resultado según el tipo de comando
        if (commandType === 'get_logs' || commandType === 'get_activation_logs' || commandType === 'get_agent_logs') {
          setLogs(prev => ({ ...prev, [machineId]: result.data.logs }))
          setShowLogs(prev => ({ ...prev, [machineId]: true }))
        } else if (commandType === 'take_screenshot') {
          setScreenshots(prev => ({ ...prev, [machineId]: result.data.screenshot }))
          setShowScreenshot(prev => ({ ...prev, [machineId]: true }))
        } else {
          alert(`✅ ${result.data.message}`)
        }
      }
      
      if (attempts >= maxAttempts) {
        clearInterval(interval)
        alert('⏱️ Timeout: El comando no respondió en 30 segundos')
      }
    } catch (error) {
      console.error('Error polling result:', error)
    }
  }, 1000) // Poll cada segundo
}
```

---

### 🔴 **Problema 3: El Agente No Reporta Resultados al Backend**

**Síntoma:** El agente ejecuta el comando pero Vercel no recibe la respuesta.

**Causa:** El agente LOCAL no tiene forma de enviar la respuesta de vuelta a Vercel.

**Solución:** Ya está implementado en v2.10.2, pero necesitas actualizar el servidor:

```python
# En RotadorSimBank.py (YA IMPLEMENTADO)

def execute_command(self, command_data):
    """Ejecuta un comando y RETORNA el resultado al API"""
    command = command_data.get("command", "")
    command_id = command_data.get("command_id", "")
    
    result = self.process_command(command)
    
    # ✅ Enviar resultado de vuelta al API
    try:
        response = requests.post(
            f"{self.api_url}/response",
            json={
                "machine_id": self.machine_id,
                "action": "response",
                "command_id": command_id,
                "result": result
            },
            headers={"Authorization": f"Bearer {self.auth_token}"},
            timeout=10
        )
    except Exception as e:
        console.print(f"[red]❌ Error enviando resultado: {e}[/red]")
```

---

## 🛠️ BACKEND REQUERIDO PARA VERCEL

Tu dashboard necesita estos **3 endpoints de API**:

### 1️⃣ `/api/commands` - Recibir Comandos desde Frontend

```typescript
// app/api/commands/route.ts

import { kv } from '@vercel/kv'

export async function POST(request: Request) {
  const auth = request.headers.get('authorization')
  if (!auth || !auth.includes(process.env.AUTH_TOKEN)) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  
  const body = await request.json()
  const { machine_id, command } = body
  
  const commandId = crypto.randomUUID()
  
  // Guardar comando pendiente para que el agente lo consuma
  await kv.rpush(`pending_commands:${machine_id}`, {
    command_id: commandId,
    command: command,
    timestamp: Date.now()
  })
  
  return Response.json({ success: true, command_id: commandId })
}

// GET: Obtener comandos pendientes (para el agente)
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const machineId = searchParams.get('machine_id')
  
  if (!machineId) {
    return Response.json({ error: 'Missing machine_id' }, { status: 400 })
  }
  
  // Obtener y eliminar el primer comando pendiente
  const command = await kv.lpop(`pending_commands:${machineId}`)
  
  if (command) {
    return Response.json({ command })
  }
  
  return Response.json({ command: null })
}
```

---

### 2️⃣ `/api/command-result` - Obtener Resultado de Comando

```typescript
// app/api/command-result/route.ts

import { kv } from '@vercel/kv'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const machineId = searchParams.get('machine_id')
  const commandId = searchParams.get('command_id')
  
  if (!machineId || !commandId) {
    return Response.json({ error: 'Missing parameters' }, { status: 400 })
  }
  
  // Buscar resultado del comando
  const result = await kv.get(`command_result:${machineId}:${commandId}`)
  
  if (result) {
    return Response.json({ success: true, data: result })
  }
  
  return Response.json({ success: false, data: null })
}
```

---

### 3️⃣ `/api/heartbeat` - Recibir Heartbeats del Agente

```typescript
// app/api/heartbeat/route.ts

import { kv } from '@vercel/kv'

export async function POST(request: Request) {
  const auth = request.headers.get('authorization')
  if (!auth || !auth.includes(process.env.AUTH_TOKEN)) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  
  const body = await request.json()
  const { machine_id, custom_name, status } = body
  
  // Guardar estado de la máquina (expira en 60 segundos)
  await kv.set(`machine:${machine_id}`, {
    machine_id,
    custom_name: custom_name || machine_id,
    last_seen: Date.now(),
    status,
    online: true
  }, { ex: 60 })
  
  return Response.json({ success: true })
}

// GET: Obtener todas las máquinas conectadas
export async function GET() {
  const keys = await kv.keys('machine:*')
  const machines = await Promise.all(
    keys.map(key => kv.get(key))
  )
  
  // Filtrar máquinas offline (last_seen > 60 segundos)
  const now = Date.now()
  const onlineMachines = machines.filter(m => 
    m && (now - m.last_seen) < 60000
  )
  
  return Response.json({ machines: onlineMachines })
}
```

---

## 📦 DEPENDENCIAS REQUERIDAS

### package.json (Vercel):

```json
{
  "dependencies": {
    "@vercel/kv": "^1.0.0",
    "next": "^14.0.0",
    "react": "^18.0.0"
  }
}
```

### Variables de Entorno (Vercel):

```bash
# .env.local
AUTH_TOKEN=tu_token_secreto_12345
KV_REST_API_URL=https://xxx.upstash.io
KV_REST_API_TOKEN=tu_token_upstash
```

---

## 🎯 FUNCIONALIDADES ADICIONALES RECOMENDADAS

### 1️⃣ **Alertas y Notificaciones** 🔔

```typescript
// Detectar cuando un servicio se cae
if (machine.services?.herosms?.status === 'stopped') {
  // Enviar notificación (email, Telegram, Discord)
  await sendAlert(`⚠️ Hero-SMS detenido en ${machine.custom_name}`)
}
```

### 2️⃣ **Historial de Uptime** 📊

```typescript
// Guardar métricas cada minuto
await kv.zadd(`uptime:${machine_id}`, {
  score: Date.now(),
  member: JSON.stringify({
    herosms: machine.services.herosms.status,
    rotador: machine.services.rotador.status,
    cpu: machine.system.cpu_percent
  })
})
```

### 3️⃣ **Gráficas de CPU/RAM** 📈

```typescript
// Mostrar gráfica de CPU de las últimas 24h
const metrics = await kv.zrange(`uptime:${machine_id}`, 
  Date.now() - 86400000, // Últimas 24h
  Date.now(),
  { byScore: true }
)
```

### 4️⃣ **Programar Comandos (Cron)** ⏰

```typescript
// Ejecutar comando a una hora específica
await kv.set(`scheduled_cmd:${machine_id}:${Date.now()}`, {
  command: 'restart_herosms',
  scheduled_for: '2026-01-15T03:00:00Z'
})
```

### 5️⃣ **Múltiples Usuarios con Roles** 👥

```typescript
// Admin: puede todo
// Viewer: solo ve estado
// Operator: puede reiniciar servicios pero no PC

const userRole = await kv.get(`user:${userId}:role`)

if (command === 'restart_pc' && userRole !== 'admin') {
  return Response.json({ error: 'Unauthorized' }, { status: 403 })
}
```

### 6️⃣ **Backup Automático de Configuración** 💾

```typescript
// Guardar configuración cada día
await kv.set(`backup:${machine_id}:${Date.now()}`, {
  sim_banks: machine.config.sim_banks,
  settings: machine.config.settings
})
```

### 7️⃣ **Estadísticas de Activación de SIMs** 📱

```typescript
// Mostrar cuántas SIMs se activaron hoy/semana/mes
const stats = {
  today: await kv.get(`stats:${machine_id}:${today}`),
  week: await kv.get(`stats:${machine_id}:${week}`),
  month: await kv.get(`stats:${machine_id}:${month}`)
}
```

### 8️⃣ **Logs Persistentes con Búsqueda** 🔍

```typescript
// Guardar logs en Vercel KV con índice por fecha
await kv.rpush(`logs:${machine_id}:${date}`, logEntry)

// Buscar logs por keyword
const results = await searchLogs(machine_id, 'ERROR')
```

### 9️⃣ **Comparación entre Servidores** ⚖️

```jsx
<div className="grid grid-cols-3 gap-4">
  {machines.map(machine => (
    <div>
      <h3>{machine.custom_name}</h3>
      <p>CPU: {machine.system.cpu_percent}%</p>
      <p>Activaciones hoy: {machine.stats.today}</p>
    </div>
  ))}
</div>
```

### 🔟 **Exportar Datos a Excel/CSV** 📊

```typescript
const exportData = () => {
  const csv = machines.map(m => 
    `${m.custom_name},${m.system.cpu_percent},${m.services.herosms.status}`
  ).join('\n')
  
  downloadCSV(csv, 'machines-report.csv')
}
```

---

## 🔗 Enlaces Útiles

- **Repositorio GitHub:** https://github.com/stgomoyaa/rotador-simbank
- **Dashboard Vercel:** https://claro-pool-dashboard.vercel.app
- **Documentación completa:** README.md
- **Vercel KV Docs:** https://vercel.com/docs/storage/vercel-kv