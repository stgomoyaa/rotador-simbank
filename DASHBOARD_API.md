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

### 5. `update` ⭐ NUEVO
Fuerza la actualización del script RotadorSimBank.py a la última versión
```json
{
  "machine_id": "BEELINK-01",
  "action": "command",
  "command": "update"
}
```

---

## 🔄 Verificación Automática de Actualizaciones

El agente ahora verifica automáticamente cada **24 horas** si hay una nueva versión disponible en GitHub.

Si detecta una actualización:
- ✅ La descarga automáticamente
- ✅ Reinicia el script con la nueva versión
- ✅ Notifica en los logs del agente

**Archivos de log del agente:**
- `agente_stdout.log` - Salida estándar
- `agente_stderr.log` - Errores

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
export default function Dashboard() {
  const [machines, setMachines] = useState([]);

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">🎮 Control Remoto - SimBank</h1>
      
      {machines.map(machine => (
        <div key={machine.id} className="bg-white shadow rounded-lg p-4 mb-4">
          <h2 className="text-xl font-semibold">{machine.id}</h2>
          <p className="text-gray-600">CPU: {machine.cpu}% | RAM: {machine.ram}%</p>
          
          <div className="mt-4 space-x-2">
            <button onClick={() => sendCommand(machine.id, 'restart_pc')} 
                    className="px-4 py-2 bg-red-500 text-white rounded">
              🔄 Reiniciar PC
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'restart_herosms')} 
                    className="px-4 py-2 bg-orange-500 text-white rounded">
              🔄 Reiniciar Hero-SMS
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'restart_rotador')} 
                    className="px-4 py-2 bg-yellow-500 text-white rounded">
              🔄 Reiniciar Rotador
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'stop_rotador')} 
                    className="px-4 py-2 bg-gray-500 text-white rounded">
              🛑 Detener Rotador
            </button>
            
            <button onClick={() => sendCommand(machine.id, 'update')} 
                    className="px-4 py-2 bg-blue-500 text-white rounded">
              📥 Actualizar Script
            </button>
          </div>
        </div>
      ))}
    </div>
  );
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

**Versión:** 2.8.2

**Nuevas características:**
- ✅ Verificación automática de actualizaciones cada 24 horas
- ✅ Comando `update` para forzar actualización desde el dashboard
- ✅ Logs detallados del proceso de actualización

---

## 🔗 Enlaces Útiles

- **Repositorio GitHub:** https://github.com/stgomoyaa/rotador-simbank
- **Dashboard Vercel:** https://claro-pool-dashboard.vercel.app
- **Documentación completa:** README.md
