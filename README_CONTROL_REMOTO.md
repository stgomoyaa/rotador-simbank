# 🎛️ Sistema de Control Remoto - Rotador SimBank

Sistema completo para controlar remotamente el Rotador SimBank desde cualquier lugar vía dashboard web en Vercel.

---

## 📋 Tabla de Contenidos

1. [Arquitectura](#arquitectura)
2. [Instalación del Agente Local](#instalación-del-agente-local)
3. [Deploy del Dashboard en Vercel](#deploy-del-dashboard-en-vercel)
4. [Uso del Dashboard](#uso-del-dashboard)
5. [Comandos Disponibles](#comandos-disponibles)
6. [Solución de Problemas](#solución-de-problemas)

---

## 🏗️ Arquitectura

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Dashboard     │         │   Vercel API     │         │  Agente Local   │
│   (Navegador)   │◄───────►│   + Vercel KV    │◄───────►│   (PC Local)    │
│                 │         │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                                                   │
                                                                   ▼
                                                          ┌──────────────────┐
                                                          │ RotadorSimBank   │
                                                          │ Hero-SMS         │
                                                          │ Windows System   │
                                                          └──────────────────┘
```

**Flujo:**
1. Abres el dashboard desde cualquier lugar (navegador)
2. Envías un comando (ej: "Reiniciar Rotador")
3. El comando se guarda en Vercel KV
4. El agente local (corriendo 24/7) consulta cada 5s si hay comandos
5. El agente ejecuta el comando y envía el resultado de vuelta
6. Ves el resultado en el dashboard

---

## 🔧 Instalación del Agente Local

### Paso 1: Instalar dependencias

```bash
INSTALAR_AGENTE.bat
```

Esto instalará:
- `requests` (para comunicación HTTP)
- `psutil` (para monitoreo del sistema)
- `NSSM` (para correr como servicio de Windows)

### Paso 2: Configurar el agente

Abre `agente_control.py` y edita las líneas 22-33:

```python
class Config:
    # URL de tu API en Vercel (cambiar después de hacer deploy)
    API_URL = "https://tu-dashboard.vercel.app/api/commands"
    
    # Token de autenticación (genera uno único)
    AUTH_TOKEN = "rotador_2024_CAMBIAR_ESTO_abc123xyz"
    
    # ID de esta máquina (opcional, se auto-detecta)
    MACHINE_ID = platform.node()  # Ej: "DESKTOP-ABC123"
```

**⚠️ Importante:**
- Genera un token seguro aleatorio (puedes usar: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- La API_URL la obtendrás después de hacer deploy en Vercel

### Paso 3: Instalar como servicio de Windows

**Ejecuta como Administrador:**

```bash
INSTALAR_SERVICIO.bat
```

Esto:
- Instala el agente como servicio de Windows
- Lo configura para iniciarse automáticamente al encender el PC
- Lo inicia inmediatamente

### Paso 4: Verificar que está corriendo

```bash
nssm status AgenteRotadorSimBank
```

Deberías ver: `SERVICE_RUNNING`

**Ver logs:**
```bash
type agente_control.log
```

---

## 🚀 Deploy del Dashboard en Vercel

### Opción 1: Deploy automático desde GitHub

1. **Crea un nuevo repositorio en GitHub**
   ```bash
   mkdir dashboard-simbank
   cd dashboard-simbank
   git init
   ```

2. **Copia todos los archivos del dashboard** (ver `DASHBOARD_VERCEL.md`)
   - `pages/api/commands.js`
   - `pages/index.js`
   - `package.json`
   - `vercel.json`

3. **Sube a GitHub**
   ```bash
   git add .
   git commit -m "Initial dashboard"
   git remote add origin https://github.com/TU_USUARIO/dashboard-simbank.git
   git push -u origin main
   ```

4. **Conecta con Vercel**
   - Ve a https://vercel.com
   - Click "New Project"
   - Importa tu repositorio de GitHub
   - Vercel detectará automáticamente que es Next.js

5. **Configura Vercel KV**
   - En tu proyecto de Vercel, ve a "Storage"
   - Click "Create Database" → "KV"
   - Vercel agregará automáticamente las variables de entorno necesarias

6. **Configura el AUTH_TOKEN**
   - Ve a "Settings" → "Environment Variables"
   - Agrega `AUTH_TOKEN` = `rotador_2024_CAMBIAR_ESTO_abc123xyz` (el mismo que pusiste en el agente)
   - Agrega `NEXT_PUBLIC_AUTH_TOKEN` = `rotador_2024_CAMBIAR_ESTO_abc123xyz`

7. **Redeploy**
   - Ve a "Deployments"
   - Click en el último deployment → "..." → "Redeploy"

### Opción 2: Deploy directo con Vercel CLI

```bash
# Instalar Vercel CLI
npm i -g vercel

# Navegar a tu directorio del dashboard
cd dashboard-simbank

# Deploy
vercel

# Seguir las instrucciones en pantalla
```

---

## 🎮 Uso del Dashboard

### 1. Acceder al dashboard

Abre tu navegador y ve a:
```
https://tu-dashboard.vercel.app
```

### 2. Seleccionar una máquina

En la sección "🖥️ Máquinas Conectadas", verás todas las máquinas que tienen el agente corriendo.

Click en una máquina para seleccionarla.

### 3. Ver estado

La sección "📊 Estado" muestra:
- **Estado general:** 🟢 Online / 🔴 Offline
- **Hero-SMS:** 🟢 Activo / 🔴 Inactivo
- **Rotador:** 🟢 Activo / 🔴 Inactivo
- **CPU:** % de uso
- **RAM:** % de uso
- **Uptime:** Horas desde el último reinicio

### 4. Enviar comandos

En la sección "🎮 Controles", tienes los botones:
- **🔄 Reiniciar PC:** Reinicia el PC completamente
- **🔄 Reiniciar Hero-SMS:** Cierra y abre Hero-SMS
- **🔄 Reiniciar Rotador:** Reinicia el script RotadorSimBank.py
- **🛑 Detener Rotador:** Detiene el script (sin reiniciar)

Click en cualquier botón para enviar el comando.

### 5. Ver historial

La sección "📜 Historial de Comandos" muestra los últimos 10 comandos ejecutados con:
- Fecha y hora
- Comando ejecutado
- ✅ Éxito / ❌ Error

---

## 📱 Comandos Disponibles

### `status`
Obtiene el estado completo del sistema.

**Respuesta:**
```json
{
  "machine_id": "DESKTOP-ABC123",
  "timestamp": "2026-01-13T10:30:00",
  "services": {
    "herosms": {
      "running": true,
      "status": "🟢 Activo"
    },
    "rotador": {
      "running": true,
      "pid": 12345,
      "status": "🟢 Activo"
    }
  },
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "disk_percent": 52.1,
    "uptime_hours": 48.5
  }
}
```

### `restart_pc`
Reinicia el PC completamente.

**⚠️ Advertencia:** El PC se reiniciará en 5 segundos después de ejecutar este comando.

### `restart_herosms`
Cierra Hero-SMS y lo abre de nuevo.

**Proceso:**
1. Ejecuta `taskkill /f /im HeroSMS-Partners.exe`
2. Espera 3 segundos
3. Abre el acceso directo desde el escritorio

### `restart_rotador`
Reinicia el script RotadorSimBank.py.

**Proceso:**
1. Detiene todos los procesos Python ejecutando RotadorSimBank.py
2. Elimina el archivo `rotador.lock` si existe
3. Inicia un nuevo proceso de RotadorSimBank.py

### `stop_rotador`
Detiene el script RotadorSimBank.py sin reiniciarlo.

**Proceso:**
1. Detiene todos los procesos Python ejecutando RotadorSimBank.py
2. Elimina el archivo `rotador.lock` si existe

---

## 🔍 Monitoreo

### Logs del agente local

```bash
# Ver log principal
type agente_control.log

# Ver stdout del servicio
type agente_stdout.log

# Ver stderr del servicio
type agente_stderr.log

# Ver en tiempo real (PowerShell)
Get-Content agente_control.log -Wait -Tail 50
```

### Estado del servicio

```bash
# Ver estado
nssm status AgenteRotadorSimBank

# Iniciar
nssm start AgenteRotadorSimBank

# Detener
nssm stop AgenteRotadorSimBank

# Reiniciar
nssm restart AgenteRotadorSimBank
```

### Dashboard de Vercel

Ve a https://vercel.com/dashboard para:
- Ver logs del API
- Monitorear requests
- Ver métricas de uso
- Revisar errores

---

## 🛠️ Solución de Problemas

### El agente no aparece en el dashboard

**Causas posibles:**
1. El agente no está corriendo
2. La API_URL está mal configurada
3. El AUTH_TOKEN no coincide
4. Hay un firewall bloqueando la conexión

**Soluciones:**
```bash
# 1. Verificar que el servicio esté corriendo
nssm status AgenteRotadorSimBank

# 2. Ver logs del agente
type agente_control.log

# 3. Verificar configuración
python
>>> from agente_control import Config
>>> print(Config.API_URL)
>>> print(Config.AUTH_TOKEN)

# 4. Probar conexión manualmente
curl -X POST https://tu-dashboard.vercel.app/api/commands ^
  -H "Authorization: Bearer TU_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"machine_id\":\"test\",\"action\":\"list_machines\"}"
```

### El comando no se ejecuta

**Causas posibles:**
1. El agente no está consultando el servidor
2. El comando expiró (TTL de 5 minutos)
3. Hay un error en la ejecución del comando

**Soluciones:**
```bash
# Ver logs del agente
type agente_control.log | findstr "Comando recibido"

# Verificar que el polling esté funcionando
type agente_control.log | findstr "Heartbeat"

# Reiniciar el servicio
nssm restart AgenteRotadorSimBank
```

### Error "No autorizado" en el dashboard

**Causa:** El `AUTH_TOKEN` no coincide entre el agente y Vercel.

**Solución:**
1. Verifica el token en `agente_control.py`
2. Verifica el token en Vercel Dashboard → Settings → Environment Variables
3. Asegúrate de que sean exactamente iguales
4. Redeploy en Vercel después de cambiar

### Hero-SMS no se reinicia

**Causa:** La ruta del acceso directo no es correcta.

**Solución:**
Edita `agente_control.py` línea ~163:
```python
# Cambiar según tu ruta real
shortcut_path = f"C:\\Users\\{user}\\Desktop\\HeroSMS-Partners.lnk"
```

### El PC no se reinicia

**Causa:** Permisos insuficientes.

**Solución:**
El servicio debe correr como Administrador:
```bash
nssm set AgenteRotadorSimBank ObjectName LocalSystem
nssm restart AgenteRotadorSimBank
```

---

## 🔒 Seguridad

### Mejores prácticas

1. **Usa un token fuerte:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Cambia el token periódicamente** (cada 3-6 meses)

3. **No compartas el token** en repositorios públicos

4. **Usa HTTPS siempre** (Vercel lo hace por defecto)

5. **Limita el acceso al dashboard** mediante autenticación adicional si lo necesitas

### Variables de entorno en Vercel

Todas las variables sensibles deben estar en Vercel Environment Variables, NO en el código:
- `AUTH_TOKEN`
- `NEXT_PUBLIC_AUTH_TOKEN`
- `KV_URL`, `KV_REST_API_TOKEN`, etc. (auto-configuradas por Vercel KV)

---

## 📊 Características Adicionales

### Múltiples máquinas

El sistema soporta múltiples máquinas automáticamente. Cada una tendrá su propio `MACHINE_ID` (nombre del PC).

En el dashboard verás una lista de todas las máquinas conectadas.

### Heartbeat automático

El agente envía un "heartbeat" cada 60 segundos con el estado completo del sistema.

Si una máquina no envía heartbeat por más de 30 segundos, se marca como 🔴 Offline.

### Historial de comandos

El sistema guarda los últimos 50 comandos ejecutados por cada máquina.

Puedes ver los últimos 10 en el dashboard.

### Expiración de comandos

Los comandos pendientes expiran después de 5 minutos si no son ejecutados.

Esto evita ejecutar comandos obsoletos.

---

## 🚀 Próximos Pasos

1. **Instala el agente** en todas tus máquinas
2. **Deploy el dashboard** en Vercel
3. **Configura los tokens** en ambos lados
4. **Prueba cada comando** para verificar que funciona
5. **¡Disfruta del control remoto!** 🎉

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs del agente local
2. Revisa los logs en Vercel Dashboard
3. Verifica la configuración de tokens
4. Asegúrate de que el firewall no bloquea la conexión

---

**¡Sistema de control remoto listo! 🎛️**

Ahora puedes controlar todas tus máquinas desde cualquier lugar del mundo con solo abrir tu navegador. 🌍

