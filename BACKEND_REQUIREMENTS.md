# 🏗️ REQUISITOS DEL BACKEND - Dashboard Vercel

## ⚠️ PROBLEMAS ACTUALES DETECTADOS

### 🔴 **Problema 1: No hay máquinas conectadas**

**Causa:** Tu backend NO está recibiendo o almacenando los heartbeats del agente.

**Síntomas:**
- Dashboard muestra "No hay máquinas conectadas"
- El agente está corriendo (`SERVICE_RUNNING`) pero no aparece

**Solución:**
1. Implementar endpoint `/api/heartbeat` en Vercel
2. Configurar Vercel KV para almacenar el estado
3. Actualizar el agente en el servidor a v2.10.2

---

### 🔴 **Problema 2: Los logs no se muestran**

**Causa:** El backend NO está guardando las respuestas de comandos.

**Síntomas:**
- Envías `get_logs` → dice "Comando enviado" ✅
- Pero nunca muestra los logs
- No hay polling de resultados

**Solución:**
1. Implementar endpoint `/api/command-result`
2. Hacer polling desde el frontend
3. Guardar respuestas en Vercel KV

---

## 🏗️ ARQUITECTURA DEL SISTEMA

```
┌──────────────────┐         ┌───────────────────┐         ┌──────────────────┐
│   Dashboard      │  HTTP   │   Vercel API      │  HTTP   │  Agente Local    │
│   (Frontend)     │ ◄─────► │   (Backend KV)    │ ◄─────► │  (Servidor)      │
└──────────────────┘         └───────────────────┘         └──────────────────┘
      │                               │                              │
      │                               │                              │
   Usuario                       Vercel KV                    RotadorSimBank.py
   • Ve estado                   • Commands queue             • Poll cada 10s
   • Envía comandos              • Machines state             • Ejecuta comandos
   • Ve logs                     • Command results            • Envía heartbeat
```

---

## 📋 ENDPOINTS REQUERIDOS

### 1️⃣ `/api/heartbeat` - Recibir Estado del Agente

**Método:** `POST`

**Body:**
```json
{
  "machine_id": "DESKTOP-06LGQS1",
  "custom_name": "Servidor Pool 1",
  "action": "heartbeat",
  "status": {
    "system": {
      "cpu_percent": 15.3,
      "memory_percent": 45.2,
      "uptime_hours": 24
    },
    "services": {
      "herosms": {
        "status": "running",
        "display": "✅ Running",
        "count": 1,
        "pids": [12345]
      },
      "rotador": {
        "status": "stopped",
        "display": "❌ Stopped"
      }
    },
    "timers": {
      "next_update_check": 23,
      "next_herosms_restart": 1
    },
    "machine_info": {
      "custom_name": "Servidor Pool 1",
      "original_hostname": "DESKTOP-06LGQS1"
    }
  }
}
```

**Implementación:**
```typescript
// app/api/heartbeat/route.ts

import { kv } from '@vercel/kv'

export async function POST(request: Request) {
  // Validar token
  const auth = request.headers.get('authorization')
  if (!auth || !auth.includes(process.env.AUTH_TOKEN!)) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  
  const body = await request.json()
  const { machine_id, custom_name, status } = body
  
  // Guardar estado (expira en 60 segundos)
  await kv.set(`machine:${machine_id}`, {
    machine_id,
    custom_name: custom_name || machine_id,
    last_seen: Date.now(),
    status,
    online: true,
    version: status.machine_info?.version || 'unknown'
  }, { ex: 60 })
  
  return Response.json({ success: true })
}

// GET: Listar máquinas conectadas
export async function GET() {
  const keys = await kv.keys('machine:*')
  const machines = await Promise.all(
    keys.map(async (key) => await kv.get(key))
  )
  
  // Filtrar máquinas online (last_seen < 60s)
  const now = Date.now()
  const onlineMachines = machines.filter(m => 
    m && (now - m.last_seen) < 60000
  )
  
  return Response.json({ machines: onlineMachines })
}
```

---

### 2️⃣ `/api/commands` - Enviar Comandos al Agente

**Método:** `POST` (desde frontend)

**Body:**
```json
{
  "machine_id": "DESKTOP-06LGQS1",
  "action": "command",
  "command": "get_logs"
}
```

**Método:** `GET` (desde agente - polling)

**Query:** `?machine_id=DESKTOP-06LGQS1`

**Response:**
```json
{
  "command": {
    "command_id": "uuid-123",
    "command": "get_logs",
    "timestamp": 1705260000000
  }
}
```

**Implementación:**
```typescript
// app/api/commands/route.ts

import { kv } from '@vercel/kv'
import { randomUUID } from 'crypto'

// POST: Crear comando (desde frontend)
export async function POST(request: Request) {
  const auth = request.headers.get('authorization')
  if (!auth || !auth.includes(process.env.AUTH_TOKEN!)) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  
  const body = await request.json()
  const { machine_id, command } = body
  
  const commandId = randomUUID()
  
  // Guardar comando pendiente
  await kv.rpush(`pending_commands:${machine_id}`, JSON.stringify({
    command_id: commandId,
    command: command,
    timestamp: Date.now()
  }))
  
  // Guardar en historial
  await kv.rpush(`command_history:${machine_id}`, JSON.stringify({
    command_id: commandId,
    command: command,
    timestamp: Date.now(),
    status: 'pending'
  }))
  
  return Response.json({ 
    success: true, 
    command_id: commandId 
  })
}

// GET: Obtener comandos pendientes (desde agente)
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const machineId = searchParams.get('machine_id')
  
  if (!machineId) {
    return Response.json({ error: 'Missing machine_id' }, { status: 400 })
  }
  
  // Obtener y eliminar el primer comando pendiente (FIFO)
  const commandStr = await kv.lpop(`pending_commands:${machineId}`)
  
  if (commandStr) {
    const command = JSON.parse(commandStr as string)
    return Response.json({ command })
  }
  
  return Response.json({ command: null })
}
```

---

### 3️⃣ `/api/command-result` - Guardar/Obtener Resultado de Comando

**Método:** `POST` (desde agente)

**Body:**
```json
{
  "machine_id": "DESKTOP-06LGQS1",
  "action": "response",
  "command_id": "uuid-123",
  "result": {
    "success": true,
    "logs": "Log content here...",
    "message": "Command executed successfully"
  }
}
```

**Método:** `GET` (desde frontend)

**Query:** `?machine_id=DESKTOP-06LGQS1&command_id=uuid-123`

**Response:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "logs": "Log content...",
    "message": "Command executed"
  }
}
```

**Implementación:**
```typescript
// app/api/command-result/route.ts

import { kv } from '@vercel/kv'

// POST: Guardar resultado (desde agente)
export async function POST(request: Request) {
  const auth = request.headers.get('authorization')
  if (!auth || !auth.includes(process.env.AUTH_TOKEN!)) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  
  const body = await request.json()
  const { machine_id, command_id, result } = body
  
  // Guardar resultado (expira en 1 hora)
  await kv.set(`command_result:${machine_id}:${command_id}`, result, { ex: 3600 })
  
  // Actualizar historial
  const history = await kv.lrange(`command_history:${machine_id}`, 0, -1)
  const updated = history.map((item: string) => {
    const cmd = JSON.parse(item)
    if (cmd.command_id === command_id) {
      cmd.status = 'completed'
      cmd.completed_at = Date.now()
    }
    return JSON.stringify(cmd)
  })
  
  await kv.del(`command_history:${machine_id}`)
  for (const item of updated) {
    await kv.rpush(`command_history:${machine_id}`, item)
  }
  
  return Response.json({ success: true })
}

// GET: Obtener resultado (desde frontend)
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const machineId = searchParams.get('machine_id')
  const commandId = searchParams.get('command_id')
  
  if (!machineId || !commandId) {
    return Response.json({ error: 'Missing parameters' }, { status: 400 })
  }
  
  const result = await kv.get(`command_result:${machineId}:${commandId}`)
  
  if (result) {
    return Response.json({ success: true, data: result })
  }
  
  return Response.json({ success: false, data: null })
}
```

---

### 4️⃣ `/api/command-history` - Historial de Comandos

**Método:** `GET`

**Query:** `?machine_id=DESKTOP-06LGQS1&limit=50`

**Implementación:**
```typescript
// app/api/command-history/route.ts

import { kv } from '@vercel/kv'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const machineId = searchParams.get('machine_id')
  const limit = parseInt(searchParams.get('limit') || '50')
  
  if (!machineId) {
    return Response.json({ error: 'Missing machine_id' }, { status: 400 })
  }
  
  const history = await kv.lrange(`command_history:${machineId}`, -limit, -1)
  const commands = history.map((item: string) => JSON.parse(item)).reverse()
  
  return Response.json({ commands })
}
```

---

## 🔧 ACTUALIZACIÓN DEL FRONTEND

### 1. Agregar Polling de Resultados

```typescript
// components/Dashboard.tsx

const [commandResults, setCommandResults] = useState<Record<string, any>>({})
const [pendingCommands, setPendingCommands] = useState<Record<string, boolean>>({})

const sendCommand = async (machineId: string, command: string) => {
  try {
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
    
    // Marcar como pendiente
    setPendingCommands(prev => ({ ...prev, [command_id]: true }))
    
    // Iniciar polling del resultado
    pollCommandResult(machineId, command_id, command)
    
  } catch (error) {
    alert(`❌ Error: ${error.message}`)
  }
}

const pollCommandResult = async (
  machineId: string, 
  commandId: string, 
  commandType: string
) => {
  let attempts = 0
  const maxAttempts = 30 // 30 segundos
  
  const interval = setInterval(async () => {
    attempts++
    
    try {
      const response = await fetch(
        `/api/command-result?machine_id=${machineId}&command_id=${commandId}`
      )
      const result = await response.json()
      
      if (result.success && result.data) {
        // ✅ Resultado recibido
        clearInterval(interval)
        setPendingCommands(prev => {
          const newState = { ...prev }
          delete newState[commandId]
          return newState
        })
        
        // Mostrar resultado según el tipo
        handleCommandResult(machineId, commandType, result.data)
      }
      
      if (attempts >= maxAttempts) {
        clearInterval(interval)
        alert('⏱️ Timeout: El comando no respondió')
        setPendingCommands(prev => {
          const newState = { ...prev }
          delete newState[commandId]
          return newState
        })
      }
    } catch (error) {
      console.error('Error polling:', error)
    }
  }, 1000)
}

const handleCommandResult = (
  machineId: string, 
  commandType: string, 
  data: any
) => {
  if (commandType.includes('get_logs') || commandType.includes('get_agent_logs')) {
    // Mostrar logs
    setLogs(prev => ({ ...prev, [machineId]: data.logs }))
    setShowLogs(prev => ({ ...prev, [machineId]: true }))
  } else if (commandType === 'take_screenshot') {
    // Mostrar screenshot
    setScreenshots(prev => ({ 
      ...prev, 
      [machineId]: `data:image/jpeg;base64,${data.screenshot}` 
    }))
    setShowScreenshot(prev => ({ ...prev, [machineId]: true }))
  } else {
    // Mostrar mensaje
    alert(`✅ ${data.message}`)
  }
}
```

### 2. Indicador de Comandos Pendientes

```jsx
{Object.keys(pendingCommands).length > 0 && (
  <div className="fixed top-4 right-4 bg-yellow-100 border-l-4 border-yellow-500 p-4">
    <div className="flex items-center">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-700 mr-2"></div>
      <p className="text-yellow-700">
        Esperando respuesta de {Object.keys(pendingCommands).length} comando(s)...
      </p>
    </div>
  </div>
)}
```

---

## 📦 DEPENDENCIAS REQUERIDAS

### package.json

```json
{
  "dependencies": {
    "@vercel/kv": "^1.0.1",
    "next": "^14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}
```

### Variables de Entorno (Vercel)

```bash
# Dashboard de Vercel → Settings → Environment Variables

AUTH_TOKEN=tu_token_secreto_12345
KV_REST_API_URL=https://your-kv-url.upstash.io
KV_REST_API_TOKEN=your_upstash_token
NEXT_PUBLIC_AUTH_TOKEN=tu_token_secreto_12345
```

---

## 🎯 FUNCIONALIDADES ADICIONALES RECOMENDADAS

### 1. Alertas Automáticas 🔔

```typescript
// Detectar cuando un servicio se cae
if (machine.services?.herosms?.status === 'stopped') {
  await sendTelegramAlert(`⚠️ Hero-SMS detenido en ${machine.custom_name}`)
}
```

### 2. Métricas y Gráficas 📊

```typescript
// Guardar histórico de CPU/RAM cada minuto
await kv.zadd(`metrics:${machine_id}`, {
  score: Date.now(),
  member: JSON.stringify({
    cpu: machine.system.cpu_percent,
    ram: machine.system.memory_percent
  })
})

// Mostrar gráfica de las últimas 24h
const metrics = await kv.zrange(
  `metrics:${machine_id}`,
  Date.now() - 86400000,
  Date.now(),
  { byScore: true }
)
```

### 3. Programar Comandos (Cron) ⏰

```typescript
// Ejecutar comando todos los días a las 3 AM
await kv.set(`scheduled:${machine_id}:daily_restart`, {
  command: 'restart_herosms',
  cron: '0 3 * * *',
  enabled: true
})
```

### 4. Backup Automático 💾

```typescript
// Guardar snapshot de configuración diariamente
await kv.set(`backup:${machine_id}:${today}`, {
  config: machine.config,
  stats: machine.stats,
  timestamp: Date.now()
})
```

### 5. Comparación Multi-Servidor ⚖️

```jsx
<div className="grid grid-cols-4 gap-4">
  {machines.map(m => (
    <div key={m.machine_id} className="bg-white p-4 rounded shadow">
      <h3 className="font-bold">{m.custom_name}</h3>
      <p>CPU: {m.status.system.cpu_percent}%</p>
      <p>Hero-SMS: {m.status.services.herosms.display}</p>
    </div>
  ))}
</div>
```

### 6. Exportar Datos 📊

```typescript
const exportToCSV = () => {
  const csv = machines.map(m => 
    `${m.custom_name},${m.status.system.cpu_percent},${m.status.services.herosms.status}`
  ).join('\n')
  
  downloadFile(csv, 'machines-report.csv')
}
```

---

## 🚀 PASOS SIGUIENTES

1. **Implementar los 4 endpoints** en `/app/api/`
2. **Configurar Vercel KV** (Storage)
3. **Actualizar el frontend** con polling
4. **Actualizar el agente** en el servidor a v2.10.2
5. **Probar el flujo completo**

---

## 📝 CHECKLIST DE IMPLEMENTACIÓN

- [ ] Crear `/app/api/heartbeat/route.ts`
- [ ] Crear `/app/api/commands/route.ts`
- [ ] Crear `/app/api/command-result/route.ts`
- [ ] Crear `/app/api/command-history/route.ts`
- [ ] Configurar Vercel KV
- [ ] Agregar variables de entorno
- [ ] Actualizar frontend con polling
- [ ] Agregar indicador de comandos pendientes
- [ ] Probar `get_logs`
- [ ] Probar `take_screenshot`
- [ ] Probar `set_name`
- [ ] Actualizar agente en servidor a v2.10.2

---

¿Necesitas ayuda implementando alguno de estos endpoints? 🚀
