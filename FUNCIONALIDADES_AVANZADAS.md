# 🚀 FUNCIONALIDADES AVANZADAS - Dashboard Rotador SimBank

## 📊 1. EXPORTAR DATOS A CSV/EXCEL

### Endpoint: `/api/export`

**Exporta datos de máquinas, logs y estadísticas a CSV/Excel**

```typescript
// app/api/export/route.ts

import { kv } from '@vercel/kv'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const type = searchParams.get('type') // 'machines' | 'logs' | 'stats'
  const machineId = searchParams.get('machine_id')
  const format = searchParams.get('format') || 'csv' // 'csv' | 'json'
  
  try {
    let data: any[] = []
    
    if (type === 'machines') {
      // Exportar estado de todas las máquinas
      const keys = await kv.keys('machine:*')
      const machines = await Promise.all(keys.map(key => kv.get(key)))
      
      data = machines.map(m => ({
        nombre: m.custom_name || m.machine_id,
        hostname: m.machine_id,
        estado: m.online ? 'Online' : 'Offline',
        cpu: `${m.status?.system?.cpu_percent}%`,
        ram: `${m.status?.system?.memory_percent}%`,
        uptime: `${m.status?.system?.uptime_hours}h`,
        hero_sms: m.status?.services?.herosms?.status,
        rotador: m.status?.services?.rotador?.status,
        ultima_conexion: new Date(m.last_seen).toLocaleString('es-ES')
      }))
    }
    
    else if (type === 'logs' && machineId) {
      // Exportar logs de una máquina
      const logs = await kv.lrange(`logs:${machineId}`, 0, -1)
      
      data = logs.map((log: any) => ({
        fecha: new Date(log.timestamp).toLocaleString('es-ES'),
        tipo: log.type,
        mensaje: log.message,
        nivel: log.level
      }))
    }
    
    else if (type === 'stats' && machineId) {
      // Exportar estadísticas de activación
      const stats = await kv.get(`stats:${machineId}`)
      
      data = [{
        maquina: machineId,
        sims_activadas_hoy: stats?.today || 0,
        sims_activadas_semana: stats?.week || 0,
        sims_activadas_mes: stats?.month || 0,
        tasa_exito: `${stats?.success_rate || 0}%`,
        promedio_por_dia: stats?.avg_per_day || 0
      }]
    }
    
    // Convertir a CSV
    if (format === 'csv') {
      const csv = convertToCSV(data)
      
      return new Response(csv, {
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': `attachment; filename="${type}-${Date.now()}.csv"`
        }
      })
    }
    
    // Retornar JSON
    return Response.json({ data })
    
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 })
  }
}

function convertToCSV(data: any[]): string {
  if (data.length === 0) return ''
  
  const headers = Object.keys(data[0])
  const rows = data.map(obj => 
    headers.map(header => {
      const value = obj[header]
      // Escapar comillas y comas
      return typeof value === 'string' && (value.includes(',') || value.includes('"'))
        ? `"${value.replace(/"/g, '""')}"`
        : value
    }).join(',')
  )
  
  return [headers.join(','), ...rows].join('\n')
}
```

### Frontend: Botones de Exportación

```tsx
// components/ExportButtons.tsx

'use client'

import { useState } from 'react'

export default function ExportButtons({ machineId }: { machineId?: string }) {
  const [exporting, setExporting] = useState(false)
  
  const handleExport = async (type: string) => {
    setExporting(true)
    
    try {
      const url = new URL('/api/export', window.location.origin)
      url.searchParams.set('type', type)
      url.searchParams.set('format', 'csv')
      
      if (machineId) {
        url.searchParams.set('machine_id', machineId)
      }
      
      const response = await fetch(url.toString())
      const blob = await response.blob()
      
      // Descargar archivo
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${type}-${Date.now()}.csv`
      link.click()
      
      URL.revokeObjectURL(link.href)
      
    } catch (error) {
      alert(`Error exportando: ${error.message}`)
    } finally {
      setExporting(false)
    }
  }
  
  return (
    <div className="flex gap-2">
      <button
        onClick={() => handleExport('machines')}
        disabled={exporting}
        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
      >
        {exporting ? '📥 Exportando...' : '📊 Exportar Máquinas'}
      </button>
      
      {machineId && (
        <>
          <button
            onClick={() => handleExport('logs')}
            disabled={exporting}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {exporting ? '📥 Exportando...' : '📄 Exportar Logs'}
          </button>
          
          <button
            onClick={() => handleExport('stats')}
            disabled={exporting}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
          >
            {exporting ? '📥 Exportando...' : '📈 Exportar Estadísticas'}
          </button>
        </>
      )}
    </div>
  )
}
```

---

## 🔍 2. LOGS PERSISTENTES CON BÚSQUEDA

### Endpoint: `/api/logs/save` - Guardar Logs

```typescript
// app/api/logs/save/route.ts

import { kv } from '@vercel/kv'

export async function POST(request: Request) {
  const auth = request.headers.get('authorization')
  if (!auth || !auth.includes(process.env.AUTH_TOKEN!)) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  
  const body = await request.json()
  const { machine_id, logs, log_type } = body
  
  try {
    // Parsear logs y guardarlos individualmente
    const logLines = logs.split('\n').filter((line: string) => line.trim())
    
    for (const line of logLines) {
      const logEntry = parseLogLine(line, log_type)
      
      // Guardar en lista de logs (max 10000 entradas)
      await kv.rpush(`logs:${machine_id}`, JSON.stringify(logEntry))
      
      // Mantener solo las últimas 10000 entradas
      const length = await kv.llen(`logs:${machine_id}`)
      if (length > 10000) {
        await kv.ltrim(`logs:${machine_id}`, -10000, -1)
      }
      
      // Indexar por keyword para búsqueda
      const keywords = extractKeywords(logEntry.message)
      for (const keyword of keywords) {
        await kv.sadd(`log_index:${machine_id}:${keyword.toLowerCase()}`, logEntry.timestamp)
      }
    }
    
    return Response.json({ success: true, saved: logLines.length })
    
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 })
  }
}

function parseLogLine(line: string, logType: string) {
  // Extraer timestamp, nivel y mensaje
  const timestampMatch = line.match(/\[?(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})/);
  const levelMatch = line.match(/(ERROR|WARN|INFO|DEBUG|SUCCESS|FAIL)/i);
  
  return {
    timestamp: timestampMatch ? new Date(timestampMatch[1]).getTime() : Date.now(),
    level: levelMatch ? levelMatch[1].toUpperCase() : 'INFO',
    type: logType,
    message: line,
    machine_id: body.machine_id
  }
}

function extractKeywords(text: string): string[] {
  // Extraer palabras significativas (ignorar palabras comunes)
  const stopWords = ['el', 'la', 'de', 'en', 'y', 'a', 'los', 'las', 'un', 'una']
  const words = text.toLowerCase()
    .replace(/[^\w\sáéíóúñ]/g, ' ')
    .split(/\s+/)
    .filter(word => word.length > 3 && !stopWords.includes(word))
  
  return [...new Set(words)] // Únicos
}
```

### Endpoint: `/api/logs/search` - Buscar Logs

```typescript
// app/api/logs/search/route.ts

import { kv } from '@vercel/kv'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const machineId = searchParams.get('machine_id')
  const keyword = searchParams.get('keyword')
  const level = searchParams.get('level')
  const startDate = searchParams.get('start_date')
  const endDate = searchParams.get('end_date')
  const limit = parseInt(searchParams.get('limit') || '100')
  
  if (!machineId) {
    return Response.json({ error: 'Missing machine_id' }, { status: 400 })
  }
  
  try {
    let logs = await kv.lrange(`logs:${machineId}`, -limit, -1)
    logs = logs.map((log: string) => JSON.parse(log))
    
    // Filtrar por keyword
    if (keyword) {
      const keywordLower = keyword.toLowerCase()
      logs = logs.filter((log: any) => 
        log.message.toLowerCase().includes(keywordLower)
      )
    }
    
    // Filtrar por nivel
    if (level) {
      logs = logs.filter((log: any) => log.level === level.toUpperCase())
    }
    
    // Filtrar por rango de fechas
    if (startDate) {
      const start = new Date(startDate).getTime()
      logs = logs.filter((log: any) => log.timestamp >= start)
    }
    
    if (endDate) {
      const end = new Date(endDate).getTime()
      logs = logs.filter((log: any) => log.timestamp <= end)
    }
    
    // Ordenar por fecha descendente
    logs.sort((a: any, b: any) => b.timestamp - a.timestamp)
    
    return Response.json({ 
      logs,
      total: logs.length,
      filtered: logs.length < limit
    })
    
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 })
  }
}
```

### Frontend: Buscador de Logs

```tsx
// components/LogViewer.tsx

'use client'

import { useState, useEffect } from 'react'

export default function LogViewer({ machineId }: { machineId: string }) {
  const [logs, setLogs] = useState<any[]>([])
  const [keyword, setKeyword] = useState('')
  const [level, setLevel] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [loading, setLoading] = useState(false)
  
  const searchLogs = async () => {
    setLoading(true)
    
    try {
      const url = new URL('/api/logs/search', window.location.origin)
      url.searchParams.set('machine_id', machineId)
      
      if (keyword) url.searchParams.set('keyword', keyword)
      if (level) url.searchParams.set('level', level)
      if (startDate) url.searchParams.set('start_date', startDate)
      if (endDate) url.searchParams.set('end_date', endDate)
      
      const response = await fetch(url.toString())
      const data = await response.json()
      
      setLogs(data.logs || [])
      
    } catch (error) {
      alert(`Error buscando logs: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    searchLogs()
  }, [machineId])
  
  return (
    <div className="bg-white rounded-lg shadow p-4">
      {/* Filtros */}
      <div className="mb-4 grid grid-cols-4 gap-2">
        <input
          type="text"
          placeholder="🔍 Buscar por keyword..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="px-3 py-2 border rounded"
        />
        
        <select
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          className="px-3 py-2 border rounded"
        >
          <option value="">Todos los niveles</option>
          <option value="ERROR">❌ ERROR</option>
          <option value="WARN">⚠️  WARN</option>
          <option value="INFO">ℹ️  INFO</option>
          <option value="SUCCESS">✅ SUCCESS</option>
        </select>
        
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="px-3 py-2 border rounded"
        />
        
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="px-3 py-2 border rounded"
        />
      </div>
      
      <button
        onClick={searchLogs}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 mb-4"
      >
        {loading ? '🔍 Buscando...' : '🔍 Buscar'}
      </button>
      
      {/* Resultados */}
      <div className="bg-black text-green-400 rounded p-3 font-mono text-xs max-h-96 overflow-y-auto">
        {logs.length === 0 ? (
          <p className="text-gray-500">No se encontraron logs</p>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="mb-1">
              <span className="text-gray-500">
                [{new Date(log.timestamp).toLocaleString('es-ES')}]
              </span>
              {' '}
              <span className={getLevelColor(log.level)}>
                [{log.level}]
              </span>
              {' '}
              {log.message}
            </div>
          ))
        )}
      </div>
      
      <p className="text-xs text-gray-500 mt-2">
        Mostrando {logs.length} resultados
      </p>
    </div>
  )
}

function getLevelColor(level: string): string {
  switch (level) {
    case 'ERROR': return 'text-red-500'
    case 'WARN': return 'text-yellow-500'
    case 'SUCCESS': return 'text-green-500'
    default: return 'text-blue-400'
  }
}
```

---

## 💾 3. BACKUP AUTOMÁTICO DE CONFIGURACIÓN

### Endpoint: `/api/backup/create` - Crear Backup

```typescript
// app/api/backup/create/route.ts

import { kv } from '@vercel/kv'

export async function POST(request: Request) {
  const auth = request.headers.get('authorization')
  if (!auth || !auth.includes(process.env.AUTH_TOKEN!)) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  
  const body = await request.json()
  const { machine_id, config, manual } = body
  
  try {
    const backupId = `backup_${Date.now()}`
    
    const backup = {
      backup_id: backupId,
      machine_id,
      timestamp: Date.now(),
      date: new Date().toISOString(),
      manual: manual || false,
      config: {
        sim_banks: config.sim_banks || {},
        settings: config.settings || {},
        ports: config.ports || {},
        database: config.database || {}
      },
      metadata: {
        version: config.version,
        hostname: config.hostname
      }
    }
    
    // Guardar backup
    await kv.set(`backup:${machine_id}:${backupId}`, backup)
    
    // Agregar a lista de backups
    await kv.rpush(`backup_list:${machine_id}`, backupId)
    
    // Mantener solo los últimos 30 backups
    const length = await kv.llen(`backup_list:${machine_id}`)
    if (length > 30) {
      const toDelete = await kv.lrange(`backup_list:${machine_id}`, 0, length - 31)
      
      for (const id of toDelete) {
        await kv.del(`backup:${machine_id}:${id}`)
      }
      
      await kv.ltrim(`backup_list:${machine_id}`, -30, -1)
    }
    
    return Response.json({ 
      success: true, 
      backup_id: backupId,
      message: 'Backup creado exitosamente'
    })
    
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 })
  }
}
```

### Endpoint: `/api/backup/list` - Listar Backups

```typescript
// app/api/backup/list/route.ts

import { kv } from '@vercel/kv'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const machineId = searchParams.get('machine_id')
  
  if (!machineId) {
    return Response.json({ error: 'Missing machine_id' }, { status: 400 })
  }
  
  try {
    const backupIds = await kv.lrange(`backup_list:${machineId}`, 0, -1)
    
    const backups = await Promise.all(
      backupIds.map(async (id: string) => {
        const backup = await kv.get(`backup:${machineId}:${id}`)
        
        return {
          backup_id: id,
          date: backup.date,
          manual: backup.manual,
          size_kb: JSON.stringify(backup.config).length / 1024
        }
      })
    )
    
    // Ordenar por fecha descendente
    backups.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    
    return Response.json({ backups })
    
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 })
  }
}
```

### Endpoint: `/api/backup/restore` - Restaurar Backup

```typescript
// app/api/backup/restore/route.ts

import { kv } from '@vercel/kv'

export async function POST(request: Request) {
  const auth = request.headers.get('authorization')
  if (!auth || !auth.includes(process.env.AUTH_TOKEN!)) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  
  const body = await request.json()
  const { machine_id, backup_id } = body
  
  try {
    // Obtener backup
    const backup = await kv.get(`backup:${machine_id}:${backup_id}`)
    
    if (!backup) {
      return Response.json({ error: 'Backup not found' }, { status: 404 })
    }
    
    // Crear comando para restaurar en el agente
    const commandId = crypto.randomUUID()
    
    await kv.rpush(`pending_commands:${machine_id}`, JSON.stringify({
      command_id: commandId,
      command: `restore_config:${JSON.stringify(backup.config)}`,
      timestamp: Date.now()
    }))
    
    return Response.json({ 
      success: true, 
      command_id: commandId,
      message: 'Comando de restauración enviado al agente'
    })
    
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 })
  }
}
```

### Frontend: Gestor de Backups

```tsx
// components/BackupManager.tsx

'use client'

import { useState, useEffect } from 'react'

export default function BackupManager({ machineId }: { machineId: string }) {
  const [backups, setBackups] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    loadBackups()
  }, [machineId])
  
  const loadBackups = async () => {
    try {
      const response = await fetch(`/api/backup/list?machine_id=${machineId}`)
      const data = await response.json()
      setBackups(data.backups || [])
    } catch (error) {
      console.error('Error loading backups:', error)
    }
  }
  
  const createBackup = async () => {
    setLoading(true)
    
    try {
      const response = await fetch('/api/backup/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          machine_id: machineId,
          config: {
            // Obtener configuración actual de la máquina
            // (esto debería venir del agente)
          },
          manual: true
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        alert('✅ Backup creado exitosamente')
        loadBackups()
      }
      
    } catch (error) {
      alert(`❌ Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }
  
  const restoreBackup = async (backupId: string) => {
    if (!confirm('¿Estás seguro de restaurar esta configuración? Esto reiniciará el agente.')) {
      return
    }
    
    setLoading(true)
    
    try {
      const response = await fetch('/api/backup/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          machine_id: machineId,
          backup_id: backupId
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        alert('✅ Comando de restauración enviado. El agente aplicará los cambios.')
      }
      
    } catch (error) {
      alert(`❌ Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold">💾 Backups de Configuración</h3>
        
        <button
          onClick={createBackup}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? '💾 Creando...' : '➕ Crear Backup'}
        </button>
      </div>
      
      <div className="space-y-2">
        {backups.length === 0 ? (
          <p className="text-gray-500">No hay backups disponibles</p>
        ) : (
          backups.map((backup) => (
            <div key={backup.backup_id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <div>
                <p className="font-semibold">
                  {new Date(backup.date).toLocaleString('es-ES')}
                  {backup.manual && <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Manual</span>}
                </p>
                <p className="text-xs text-gray-600">
                  Tamaño: {backup.size_kb.toFixed(2)} KB
                </p>
              </div>
              
              <button
                onClick={() => restoreBackup(backup.backup_id)}
                disabled={loading}
                className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
              >
                🔄 Restaurar
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
```

---

## 🔄 ACTUALIZACIÓN DEL AGENTE (RotadorSimBank.py)

### Comando: `restore_config` - Restaurar Configuración

```python
# Agregar en RotadorSimBank.py → execute_command()

elif command.startswith("restore_config:"):
    console.print("[yellow]🔄 Ejecutando: Restaurar Configuración[/yellow]")
    try:
        # Extraer configuración del comando
        config_json = command.split(":", 1)[1]
        config = json.loads(config_json)
        
        # Guardar en archivo
        with open("simbanks_config.json", "w", encoding="utf-8") as f:
            json.dump(config.get("sim_banks", {}), f, indent=2)
        
        with open("rotador_settings.json", "w", encoding="utf-8") as f:
            json.dump(config.get("settings", {}), f, indent=2)
        
        console.print("[green]✅ Configuración restaurada[/green]")
        
        # Reiniciar agente para aplicar cambios
        nssm_path = os.path.join(os.getcwd(), "nssm.exe")
        if os.path.exists(nssm_path):
            subprocess.Popen([nssm_path, "restart", "AgenteRotadorSimBank"])
        
        return {"success": True, "message": "Configuración restaurada. Reiniciando agente..."}
        
    except Exception as e:
        return {"success": False, "message": f"Error al restaurar: {str(e)}"}
```

### Tarea Automática: Backup Diario

```python
# Agregar en AgenteControlRemoto → run()

def crear_backup_automatico(self):
    """Crea un backup automático de la configuración"""
    try:
        # Recopilar configuración actual
        config = {
            "sim_banks": {},
            "settings": {},
            "version": Settings.VERSION
        }
        
        # Leer simbanks_config.json si existe
        if os.path.exists("simbanks_config.json"):
            with open("simbanks_config.json", "r", encoding="utf-8") as f:
                config["sim_banks"] = json.load(f)
        
        # Enviar al API para guardar
        response = requests.post(
            f"{self.api_url}/backup/create",
            json={
                "machine_id": self.machine_id,
                "config": config,
                "manual": False
            },
            headers={"Authorization": f"Bearer {self.auth_token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            console.print("[green]✅ Backup automático creado[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error creando backup: {e}[/red]")

# En el bucle principal (run()):
# Crear backup cada 24 horas
if time.time() - self.ultimo_backup > 86400:  # 24 horas
    self.crear_backup_automatico()
    self.ultimo_backup = time.time()
```

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Exportar Datos:
- [ ] Crear `/api/export/route.ts`
- [ ] Agregar botones de exportación en el dashboard
- [ ] Probar exportar máquinas a CSV
- [ ] Probar exportar logs a CSV
- [ ] Probar exportar estadísticas a CSV

### Logs Persistentes:
- [ ] Crear `/api/logs/save/route.ts`
- [ ] Crear `/api/logs/search/route.ts`
- [ ] Implementar componente `LogViewer`
- [ ] Modificar comandos `get_logs` para guardar en KV
- [ ] Agregar búsqueda por keyword
- [ ] Agregar filtros por fecha y nivel

### Backup Automático:
- [ ] Crear `/api/backup/create/route.ts`
- [ ] Crear `/api/backup/list/route.ts`
- [ ] Crear `/api/backup/restore/route.ts`
- [ ] Implementar componente `BackupManager`
- [ ] Agregar comando `restore_config` al agente
- [ ] Implementar backup automático diario

---

¿Necesitas ayuda implementando alguna de estas funcionalidades? 🚀
