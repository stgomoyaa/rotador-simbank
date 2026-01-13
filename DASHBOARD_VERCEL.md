# 🎛️ Dashboard de Control Remoto - Vercel

Este archivo contiene el código completo para el dashboard que se desplegará en Vercel.

## 📁 Estructura del Proyecto

Crea un nuevo proyecto de Next.js y copia estos archivos:

```
dashboard-simbank/
├── pages/
│   ├── api/
│   │   └── commands.js         # API endpoint para el agente
│   └── index.js                # Dashboard principal
├── lib/
│   └── db.js                   # Conexión a base de datos (Vercel KV)
├── package.json
├── .env.local                  # Variables de entorno
└── vercel.json                 # Configuración de Vercel
```

---

## 1️⃣ package.json

```json
{
  "name": "dashboard-simbank",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.0.4",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "@vercel/kv": "^1.0.1"
  }
}
```

---

## 2️⃣ pages/api/commands.js

```javascript
import { kv } from '@vercel/kv';

// Token de autenticación (debe coincidir con el del agente)
const AUTH_TOKEN = process.env.AUTH_TOKEN || 'CAMBIAR_ESTO_POR_UN_TOKEN_SEGURO';

export default async function handler(req, res) {
  // Verificar autenticación
  const authHeader = req.headers.authorization;
  if (!authHeader || authHeader !== `Bearer ${AUTH_TOKEN}`) {
    return res.status(401).json({ error: 'No autorizado' });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método no permitido' });
  }

  const { machine_id, action, command, result, status, timestamp } = req.body;

  if (!machine_id) {
    return res.status(400).json({ error: 'machine_id requerido' });
  }

  try {
    // 1. POLL: Agente consulta si hay comandos
    if (action === 'poll') {
      const pendingCommand = await kv.get(`command:${machine_id}`);
      
      if (pendingCommand) {
        // Hay un comando pendiente
        return res.status(200).json({
          has_command: true,
          command: pendingCommand
        });
      } else {
        // No hay comandos
        return res.status(204).end();
      }
    }

    // 2. REPORT: Agente reporta resultado de comando
    if (action === 'report') {
      // Guardar resultado
      await kv.set(`result:${machine_id}:${command}`, {
        result,
        timestamp
      }, { ex: 3600 }); // Expira en 1 hora

      // Eliminar comando pendiente
      await kv.del(`command:${machine_id}`);

      // Guardar en historial
      const historyKey = `history:${machine_id}`;
      const history = (await kv.get(historyKey)) || [];
      history.unshift({
        command,
        result,
        timestamp
      });
      // Mantener solo los últimos 50 comandos
      if (history.length > 50) history.pop();
      await kv.set(historyKey, history);

      return res.status(200).json({ success: true });
    }

    // 3. HEARTBEAT: Agente envía estado periódico
    if (action === 'heartbeat') {
      // Guardar estado actual
      await kv.set(`status:${machine_id}`, {
        ...status,
        last_seen: new Date().toISOString()
      }, { ex: 120 }); // Expira en 2 minutos

      return res.status(200).json({ success: true });
    }

    // 4. SEND_COMMAND: Dashboard envía comando al agente
    if (action === 'send_command') {
      if (!command) {
        return res.status(400).json({ error: 'command requerido' });
      }

      // Guardar comando pendiente
      await kv.set(`command:${machine_id}`, command, { ex: 300 }); // Expira en 5 minutos

      return res.status(200).json({ 
        success: true,
        message: `Comando '${command}' enviado a ${machine_id}`
      });
    }

    // 5. GET_STATUS: Dashboard consulta estado
    if (action === 'get_status') {
      const status = await kv.get(`status:${machine_id}`);
      const pendingCommand = await kv.get(`command:${machine_id}`);
      const history = (await kv.get(`history:${machine_id}`)) || [];

      return res.status(200).json({
        status: status || { running: false },
        pending_command: pendingCommand,
        history: history.slice(0, 10) // Últimos 10 comandos
      });
    }

    // 6. LIST_MACHINES: Dashboard lista todas las máquinas
    if (action === 'list_machines') {
      // Obtener todas las claves de status
      const keys = await kv.keys('status:*');
      const machines = [];

      for (const key of keys) {
        const machineId = key.replace('status:', '');
        const status = await kv.get(key);
        machines.push({
          machine_id: machineId,
          ...status
        });
      }

      return res.status(200).json({ machines });
    }

    return res.status(400).json({ error: 'Acción no válida' });

  } catch (error) {
    console.error('Error en API:', error);
    return res.status(500).json({ 
      error: 'Error interno del servidor',
      details: error.message 
    });
  }
}
```

---

## 3️⃣ pages/index.js

```javascript
import { useState, useEffect } from 'react';

export default function Dashboard() {
  const [machines, setMachines] = useState([]);
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [status, setStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Cargar lista de máquinas
  useEffect(() => {
    loadMachines();
    const interval = setInterval(loadMachines, 5000); // Actualizar cada 5s
    return () => clearInterval(interval);
  }, []);

  // Cargar estado de máquina seleccionada
  useEffect(() => {
    if (selectedMachine) {
      loadStatus();
      const interval = setInterval(loadStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [selectedMachine]);

  async function loadMachines() {
    try {
      const res = await fetch('/api/commands', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.NEXT_PUBLIC_AUTH_TOKEN}`
        },
        body: JSON.stringify({ 
          machine_id: 'dashboard',
          action: 'list_machines' 
        })
      });
      const data = await res.json();
      setMachines(data.machines || []);
    } catch (error) {
      console.error('Error cargando máquinas:', error);
    }
  }

  async function loadStatus() {
    if (!selectedMachine) return;

    try {
      const res = await fetch('/api/commands', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.NEXT_PUBLIC_AUTH_TOKEN}`
        },
        body: JSON.stringify({ 
          machine_id: selectedMachine,
          action: 'get_status' 
        })
      });
      const data = await res.json();
      setStatus(data.status);
      setHistory(data.history || []);
    } catch (error) {
      console.error('Error cargando estado:', error);
    }
  }

  async function sendCommand(command) {
    if (!selectedMachine) {
      setMessage('⚠️ Selecciona una máquina primero');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const res = await fetch('/api/commands', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.NEXT_PUBLIC_AUTH_TOKEN}`
        },
        body: JSON.stringify({ 
          machine_id: selectedMachine,
          action: 'send_command',
          command 
        })
      });
      
      const data = await res.json();
      
      if (data.success) {
        setMessage(`✅ ${data.message}`);
      } else {
        setMessage(`❌ Error: ${data.error}`);
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  const isOnline = status && status.last_seen && 
    (new Date() - new Date(status.last_seen)) < 30000; // 30s

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>🎛️ Dashboard - Rotador SimBank</h1>

      {/* Lista de máquinas */}
      <div style={styles.section}>
        <h2>🖥️ Máquinas Conectadas</h2>
        <div style={styles.machineList}>
          {machines.length === 0 && <p>No hay máquinas conectadas</p>}
          {machines.map(machine => (
            <div 
              key={machine.machine_id}
              style={{
                ...styles.machineCard,
                ...(selectedMachine === machine.machine_id ? styles.machineCardSelected : {})
              }}
              onClick={() => setSelectedMachine(machine.machine_id)}
            >
              <div style={styles.machineName}>{machine.machine_id}</div>
              <div style={styles.machineStatus}>
                {(new Date() - new Date(machine.last_seen)) < 30000 ? '🟢 Online' : '🔴 Offline'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Estado de la máquina seleccionada */}
      {selectedMachine && (
        <>
          <div style={styles.section}>
            <h2>📊 Estado: {selectedMachine}</h2>
            {status ? (
              <div style={styles.statusGrid}>
                <div style={styles.statusCard}>
                  <div style={styles.statusLabel}>Estado</div>
                  <div style={styles.statusValue}>
                    {isOnline ? '🟢 Online' : '🔴 Offline'}
                  </div>
                </div>
                <div style={styles.statusCard}>
                  <div style={styles.statusLabel}>Hero-SMS</div>
                  <div style={styles.statusValue}>
                    {status.services?.herosms?.status || '❓'}
                  </div>
                </div>
                <div style={styles.statusCard}>
                  <div style={styles.statusLabel}>Rotador</div>
                  <div style={styles.statusValue}>
                    {status.services?.rotador?.status || '❓'}
                  </div>
                </div>
                <div style={styles.statusCard}>
                  <div style={styles.statusLabel}>CPU</div>
                  <div style={styles.statusValue}>
                    {status.system?.cpu_percent || 0}%
                  </div>
                </div>
                <div style={styles.statusCard}>
                  <div style={styles.statusLabel}>RAM</div>
                  <div style={styles.statusValue}>
                    {status.system?.memory_percent || 0}%
                  </div>
                </div>
                <div style={styles.statusCard}>
                  <div style={styles.statusLabel}>Uptime</div>
                  <div style={styles.statusValue}>
                    {status.system?.uptime_hours || 0}h
                  </div>
                </div>
              </div>
            ) : (
              <p>Esperando datos...</p>
            )}
          </div>

          {/* Controles */}
          <div style={styles.section}>
            <h2>🎮 Controles</h2>
            <div style={styles.buttonGrid}>
              <button 
                style={styles.button} 
                onClick={() => sendCommand('restart_pc')}
                disabled={loading}
              >
                🔄 Reiniciar PC
              </button>
              <button 
                style={styles.button} 
                onClick={() => sendCommand('restart_herosms')}
                disabled={loading}
              >
                🔄 Reiniciar Hero-SMS
              </button>
              <button 
                style={styles.button} 
                onClick={() => sendCommand('restart_rotador')}
                disabled={loading}
              >
                🔄 Reiniciar Rotador
              </button>
              <button 
                style={{...styles.button, ...styles.buttonDanger}} 
                onClick={() => sendCommand('stop_rotador')}
                disabled={loading}
              >
                🛑 Detener Rotador
              </button>
            </div>
            {message && <div style={styles.message}>{message}</div>}
          </div>

          {/* Historial */}
          <div style={styles.section}>
            <h2>📜 Historial de Comandos</h2>
            <div style={styles.history}>
              {history.length === 0 && <p>No hay historial</p>}
              {history.map((item, idx) => (
                <div key={idx} style={styles.historyItem}>
                  <span style={styles.historyTime}>
                    {new Date(item.timestamp).toLocaleString()}
                  </span>
                  <span style={styles.historyCommand}>{item.command}</span>
                  <span style={styles.historyResult}>
                    {item.result?.success ? '✅' : '❌'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: 'system-ui, -apple-system, sans-serif'
  },
  title: {
    textAlign: 'center',
    color: '#333',
    marginBottom: '30px'
  },
  section: {
    background: 'white',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  machineList: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '10px'
  },
  machineCard: {
    padding: '15px',
    border: '2px solid #e0e0e0',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s'
  },
  machineCardSelected: {
    borderColor: '#4CAF50',
    background: '#f1f8f4'
  },
  machineName: {
    fontWeight: 'bold',
    marginBottom: '5px'
  },
  machineStatus: {
    fontSize: '14px'
  },
  statusGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '15px'
  },
  statusCard: {
    padding: '15px',
    background: '#f5f5f5',
    borderRadius: '8px',
    textAlign: 'center'
  },
  statusLabel: {
    fontSize: '12px',
    color: '#666',
    marginBottom: '5px'
  },
  statusValue: {
    fontSize: '18px',
    fontWeight: 'bold'
  },
  buttonGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '10px',
    marginBottom: '15px'
  },
  button: {
    padding: '15px 20px',
    fontSize: '16px',
    border: 'none',
    borderRadius: '8px',
    background: '#4CAF50',
    color: 'white',
    cursor: 'pointer',
    transition: 'background 0.2s'
  },
  buttonDanger: {
    background: '#f44336'
  },
  message: {
    padding: '10px',
    borderRadius: '4px',
    background: '#e3f2fd',
    marginTop: '10px'
  },
  history: {
    maxHeight: '300px',
    overflowY: 'auto'
  },
  historyItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px',
    borderBottom: '1px solid #eee'
  },
  historyTime: {
    fontSize: '12px',
    color: '#666',
    flex: '0 0 160px'
  },
  historyCommand: {
    flex: 1,
    marginLeft: '10px'
  },
  historyResult: {
    flex: '0 0 30px',
    textAlign: 'right'
  }
};
```

---

## 4️⃣ .env.local

```bash
# Token de autenticación (debe coincidir con el del agente)
AUTH_TOKEN=GENERA_UN_TOKEN_SEGURO_AQUI

# Token público para el frontend
NEXT_PUBLIC_AUTH_TOKEN=GENERA_UN_TOKEN_SEGURO_AQUI

# URL de Vercel KV (se auto-configura después del deploy)
KV_URL=
KV_REST_API_URL=
KV_REST_API_TOKEN=
KV_REST_API_READ_ONLY_TOKEN=
```

---

## 5️⃣ vercel.json

```json
{
  "env": {
    "AUTH_TOKEN": "@auth_token"
  }
}
```

---

## 🚀 Instrucciones de Deploy

### 1. Crear proyecto en Vercel

```bash
# Instalar Vercel CLI
npm i -g vercel

# Crear directorio del proyecto
mkdir dashboard-simbank
cd dashboard-simbank

# Copiar los archivos de arriba en sus respectivas carpetas

# Instalar dependencias
npm install

# Deploy a Vercel
vercel
```

### 2. Configurar Vercel KV

1. Ve a tu proyecto en Vercel Dashboard
2. Ve a "Storage" → "Create Database" → "KV"
3. Crea una nueva base de datos KV
4. Copia las variables de entorno que Vercel te da automáticamente

### 3. Configurar variables de entorno

En Vercel Dashboard:
1. Ve a "Settings" → "Environment Variables"
2. Agrega `AUTH_TOKEN` con un token seguro (ej: `rotador_2024_secure_token_xyz`)
3. Agrega `NEXT_PUBLIC_AUTH_TOKEN` con el mismo valor

### 4. Obtener la URL del dashboard

Después del deploy, Vercel te dará una URL como:
```
https://dashboard-simbank-xxx.vercel.app
```

### 5. Configurar el agente local

Edita `agente_control.py` y cambia:
```python
API_URL = "https://dashboard-simbank-xxx.vercel.app/api/commands"
AUTH_TOKEN = "rotador_2024_secure_token_xyz"  # El mismo que pusiste en Vercel
```

---

## ✅ Listo!

Ahora tu dashboard estará en:
`https://dashboard-simbank-xxx.vercel.app`

Y podrás controlar todas tus máquinas desde cualquier lugar! 🎉

