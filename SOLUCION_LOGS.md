# 🔧 SOLUCIÓN: Problema con los Logs no se Muestran

## 🔴 PROBLEMA DETECTADO

Cuando haces clic en **"Ver Log Principal"**, **"Ver Log Activación"** o **"Ver Log Agente"**, los logs **NO se muestran**.

### ¿Por qué pasa esto?

El flujo debería ser:

```
1. Usuario click "Ver Log" 
   ↓
2. Dashboard envía comando "get_logs" al API
   ↓
3. API guarda comando en cola
   ↓
4. Agente hace polling y obtiene el comando
   ↓
5. Agente ejecuta el comando y obtiene los logs
   ↓
6. Agente envía los logs de vuelta al API
   ↓
7. Dashboard hace polling del resultado
   ↓
8. Dashboard muestra los logs ✅
```

**El problema está en el paso 7:** El dashboard **NO está haciendo polling** para obtener el resultado.

---

## ✅ SOLUCIÓN COMPLETA

### 1. Verificar que el API Guarda Respuestas

Asegúrate de tener este endpoint:

```typescript
// app/api/command-result/route.ts

import { kv } from '@vercel/kv'

// POST: Guardar resultado del comando (desde el agente)
export async function POST(request: Request) {
  const auth = request.headers.get('authorization')
  if (!auth || !auth.includes(process.env.AUTH_TOKEN!)) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  
  const body = await request.json()
  const { machine_id, command_id, result } = body
  
  console.log('💾 Guardando resultado de comando:', { machine_id, command_id, result })
  
  // Guardar resultado (expira en 1 hora)
  await kv.set(`command_result:${machine_id}:${command_id}`, result, { ex: 3600 })
  
  return Response.json({ success: true })
}

// GET: Obtener resultado del comando (desde el dashboard)
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const machineId = searchParams.get('machine_id')
  const commandId = searchParams.get('command_id')
  
  if (!machineId || !commandId) {
    return Response.json({ error: 'Missing parameters' }, { status: 400 })
  }
  
  const result = await kv.get(`command_result:${machineId}:${commandId}`)
  
  console.log('📥 Consultando resultado:', { machineId, commandId, found: !!result })
  
  if (result) {
    return Response.json({ success: true, data: result })
  }
  
  return Response.json({ success: false, data: null })
}
```

---

### 2. Actualizar el Agente para Enviar Respuestas

El agente debe enviar la respuesta de vuelta al API:

```python
# En RotadorSimBank.py → poll_commands()

def poll_commands(self):
    """Consulta comandos pendientes desde el API"""
    try:
        response = requests.get(
            f"{self.api_url}/commands",
            params={"machine_id": self.machine_id},
            headers={"Authorization": f"Bearer {self.auth_token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("command"):
                cmd_data = data["command"]
                command_id = cmd_data.get("command_id")
                command = cmd_data.get("command")
                
                console.print(f"[cyan]📥 Comando recibido: {command}[/cyan]")
                
                # Ejecutar comando
                result = self.execute_command({"command": command})
                
                # ✅ CRÍTICO: Enviar respuesta de vuelta al API
                self.send_command_result(command_id, result)
                
    except Exception as e:
        console.print(f"[red]❌ Error polling commands: {e}[/red]")

def send_command_result(self, command_id: str, result: dict):
    """Envía el resultado de un comando de vuelta al API"""
    try:
        response = requests.post(
            f"{self.api_url}/command-result",
            json={
                "machine_id": self.machine_id,
                "command_id": command_id,
                "result": result
            },
            headers={"Authorization": f"Bearer {self.auth_token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            console.print(f"[green]✅ Resultado enviado: {command_id}[/green]")
        else:
            console.print(f"[red]❌ Error enviando resultado: {response.status_code}[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error enviando resultado: {e}[/red]")
```

---

### 3. Actualizar el Frontend para Hacer Polling

Este es el código **CRÍTICO** que falta en tu dashboard:

```typescript
// app/page.tsx o components/Dashboard.tsx

'use client'

import { useState } from 'react'

export default function Dashboard() {
  const [logs, setLogs] = useState<Record<string, string>>({})
  const [showLogs, setShowLogs] = useState<Record<string, boolean>>({})
  const [pendingCommands, setPendingCommands] = useState<Record<string, boolean>>({})
  
  // Función para enviar comandos CON POLLING
  const sendCommand = async (machineId: string, command: string) => {
    try {
      // 1. Enviar comando al API
      const response = await fetch('/api/commands', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.NEXT_PUBLIC_AUTH_TOKEN}`
        },
        body: JSON.stringify({
          machine_id: machineId,
          action: 'command',
          command: command
        })
      })
      
      const { command_id } = await response.json()
      
      console.log('📤 Comando enviado:', { command_id, command })
      
      // 2. Marcar como pendiente
      setPendingCommands(prev => ({ ...prev, [command_id]: true }))
      
      // 3. ✅ CRÍTICO: Iniciar polling del resultado
      pollCommandResult(machineId, command_id, command)
      
    } catch (error) {
      alert(`❌ Error: ${error.message}`)
    }
  }
  
  // ✅ FUNCIÓN CRÍTICA: Polling del resultado
  const pollCommandResult = async (
    machineId: string,
    commandId: string,
    commandType: string
  ) => {
    let attempts = 0
    const maxAttempts = 30 // 30 segundos
    
    console.log('🔄 Iniciando polling para:', { commandId, commandType })
    
    const interval = setInterval(async () => {
      attempts++
      
      try {
        // Consultar resultado
        const response = await fetch(
          `/api/command-result?machine_id=${machineId}&command_id=${commandId}`
        )
        const result = await response.json()
        
        console.log(`🔍 Polling intento ${attempts}:`, result)
        
        if (result.success && result.data) {
          // ✅ Resultado recibido!
          console.log('✅ Resultado recibido:', result.data)
          
          clearInterval(interval)
          setPendingCommands(prev => {
            const newState = { ...prev }
            delete newState[commandId]
            return newState
          })
          
          // Mostrar resultado según el tipo de comando
          handleCommandResult(machineId, commandType, result.data)
        }
        
        if (attempts >= maxAttempts) {
          // Timeout
          clearInterval(interval)
          console.error('⏱️ Timeout: El comando no respondió')
          alert('⏱️ Timeout: El comando no respondió en 30 segundos')
          setPendingCommands(prev => {
            const newState = { ...prev }
            delete newState[commandId]
            return newState
          })
        }
      } catch (error) {
        console.error('❌ Error polling:', error)
      }
    }, 1000) // Poll cada 1 segundo
  }
  
  // Manejar el resultado según el tipo de comando
  const handleCommandResult = (
    machineId: string,
    commandType: string,
    data: any
  ) => {
    if (commandType === 'get_logs' || 
        commandType === 'get_activation_logs' || 
        commandType === 'get_agent_logs') {
      
      // Mostrar logs
      console.log('📄 Mostrando logs:', data.logs?.substring(0, 100))
      
      setLogs(prev => ({ ...prev, [machineId]: data.logs || 'No hay logs disponibles' }))
      setShowLogs(prev => ({ ...prev, [machineId]: true }))
      
    } else if (commandType === 'take_screenshot') {
      
      // Mostrar screenshot
      // (implementar según necesites)
      
    } else {
      
      // Mostrar mensaje de éxito
      alert(`✅ ${data.message}`)
      
    }
  }
  
  return (
    <div className="p-6">
      {/* Indicador de comandos pendientes */}
      {Object.keys(pendingCommands).length > 0 && (
        <div className="fixed top-4 right-4 bg-yellow-100 border-l-4 border-yellow-500 p-4 rounded shadow-lg z-50">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-700 mr-2"></div>
            <p className="text-yellow-700 font-medium">
              Esperando respuesta de {Object.keys(pendingCommands).length} comando(s)...
            </p>
          </div>
        </div>
      )}
      
      {/* Tus máquinas y botones */}
      {machines.map(machine => (
        <div key={machine.machine_id} className="bg-white shadow rounded-lg p-4 mb-4">
          {/* ... resto del código ... */}
          
          {/* Botones de logs */}
          <div className="mb-4 flex gap-2">
            <button 
              onClick={() => sendCommand(machine.machine_id, 'get_logs')}
              className="px-3 py-1 bg-purple-500 text-white text-sm rounded hover:bg-purple-600"
            >
              📄 Ver Log Principal
            </button>
            
            <button 
              onClick={() => sendCommand(machine.machine_id, 'get_activation_logs')}
              className="px-3 py-1 bg-purple-500 text-white text-sm rounded hover:bg-purple-600"
            >
              📄 Ver Log Activación
            </button>
            
            <button 
              onClick={() => sendCommand(machine.machine_id, 'get_agent_logs')}
              className="px-3 py-1 bg-purple-500 text-white text-sm rounded hover:bg-purple-600"
            >
              📄 Ver Log Agente
            </button>
          </div>
          
          {/* Mostrar logs */}
          {showLogs[machine.machine_id] && logs[machine.machine_id] && (
            <div className="mt-4 p-3 bg-black text-green-400 rounded font-mono text-xs overflow-x-auto max-h-96">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold">📋 Logs:</span>
                <button 
                  onClick={() => setShowLogs(prev => ({ ...prev, [machine.machine_id]: false }))}
                  className="text-red-400 hover:text-red-300"
                >
                  ✕ Cerrar
                </button>
              </div>
              <pre className="whitespace-pre-wrap">{logs[machine.machine_id]}</pre>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
```

---

## 🧪 CÓMO PROBAR

### Paso 1: Verificar que el Agente Envía Respuestas

En el servidor (`C:\Rotador`), ejecuta el agente manualmente para ver los logs:

```powershell
# Detener el servicio temporalmente
.\nssm stop AgenteRotadorSimBank

# Ejecutar manualmente para ver logs
python RotadorSimBank.py --agente
```

Deberías ver algo como:

```
💓 Heartbeat [PC-1] - CPU: 15%...
📥 Comando recibido: get_logs
✅ Resultado enviado: abc-123-def
```

### Paso 2: Verificar en el Dashboard

1. Abre las **DevTools** del navegador (F12)
2. Ve a la pestaña **Console**
3. Haz clic en **"Ver Log Principal"**
4. Deberías ver:

```javascript
📤 Comando enviado: { command_id: "abc-123-def", command: "get_logs" }
🔄 Iniciando polling para: { commandId: "abc-123-def", commandType: "get_logs" }
🔍 Polling intento 1: { success: false, data: null }
🔍 Polling intento 2: { success: false, data: null }
🔍 Polling intento 3: { success: true, data: { logs: "..." } }
✅ Resultado recibido: { logs: "..." }
📄 Mostrando logs: [2026-01-14 19:30:15] ✅...
```

### Paso 3: Verificar en Vercel KV

Puedes verificar que los resultados se están guardando:

```bash
# En Vercel CLI o desde el dashboard de Vercel KV
GET command_result:DESKTOP-06LGQS1:abc-123-def
```

Debería retornar:

```json
{
  "success": true,
  "logs": "[2026-01-14 19:30:15] ✅...",
  "file": "rotador_simbank.log"
}
```

---

## 🚨 PROBLEMAS COMUNES Y SOLUCIONES

### Problema 1: "Timeout: El comando no respondió"

**Causa:** El agente NO está enviando la respuesta de vuelta al API.

**Solución:**
1. Verifica que `send_command_result()` esté implementado en el agente
2. Verifica que el agente tenga acceso al URL del API
3. Verifica los logs del agente: `type agente_stdout.log`

---

### Problema 2: Los logs se muestran vacíos

**Causa:** El comando `get_logs` retorna un string vacío.

**Solución:**
1. Verifica que el archivo de log exista: `type rotador_simbank.log`
2. Verifica la implementación del comando en el agente:

```python
elif command == "get_logs":
    try:
        log_content = self.read_log_file(Settings.LOG_FILE, lines=100)
        return {"success": True, "logs": log_content, "file": Settings.LOG_FILE}
    except Exception as e:
        return {"success": False, "message": f"Error leyendo log: {str(e)}"}
```

---

### Problema 3: El polling nunca encuentra el resultado

**Causa:** El `command_id` no coincide entre el comando enviado y la respuesta guardada.

**Solución:**
1. Agrega logs de debug en el API:

```typescript
// En /api/commands/route.ts (POST)
console.log('📤 Comando creado:', { command_id, command })

// En /api/command-result/route.ts (POST)
console.log('💾 Resultado guardado:', { machine_id, command_id, result })

// En /api/command-result/route.ts (GET)
console.log('📥 Consultando resultado:', { machine_id, command_id, found: !!result })
```

2. Verifica en los logs de Vercel (Vercel Dashboard → Logs) que todos los IDs coincidan.

---

## 📋 CHECKLIST DE VERIFICACIÓN

- [ ] El agente tiene la función `send_command_result()` implementada
- [ ] El agente llama a `send_command_result()` después de ejecutar cada comando
- [ ] El endpoint `/api/command-result` existe y funciona (POST y GET)
- [ ] El frontend tiene la función `pollCommandResult()` implementada
- [ ] El frontend llama a `pollCommandResult()` después de enviar un comando
- [ ] Los logs de la consola del navegador muestran el flujo completo
- [ ] Los logs del agente muestran "✅ Resultado enviado"
- [ ] Vercel KV contiene los resultados guardados

---

## 🎯 RESULTADO ESPERADO

Cuando hagas clic en **"Ver Log Principal"**:

1. ✅ Aparece un indicador amarillo: "Esperando respuesta de 1 comando(s)..."
2. ✅ En 1-3 segundos, el indicador desaparece
3. ✅ Se muestra un panel negro con los logs en texto verde
4. ✅ Puedes hacer scroll para ver todo el contenido
5. ✅ Hay un botón "✕ Cerrar" para ocultar los logs

---

¿Los logs ya están funcionando? Si no, comparte los logs de la consola del navegador y del agente para ayudarte más. 🚀
