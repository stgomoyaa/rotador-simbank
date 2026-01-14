# 🔄 Rotador Automático de SIM Bank v2.7.0

**Sistema inteligente de rotación automática de slots en SIM Banks con:**
- ✅ Activación automática de SIMs Claro
- ✅ Auto-actualización desde GitHub
- ✅ Persistencia en PostgreSQL
- ✅ **🆕 Agente de Control Remoto 24/7** (integrado)
- ✅ Dashboard web en Vercel

---

## 📦 Instalación Ultra-Rápida (Una Sola Máquina)

### 1. Requisitos Previos
- **Python 3.7+** instalado ([descargar](https://www.python.org/downloads/))
- **Windows 10/11** con permisos de Administrador

### 2. Instalación Automática (TODO EN UNO)

**Ejecutar como Administrador:**
```bash
INSTALAR.bat
```

Esto instala:
1. ✅ Todas las dependencias Python (pyserial, rich, psycopg2, requests, psutil)
2. ✅ Crea tabla en PostgreSQL (si está configurada)
3. ✅ Instala el **Agente de Control Remoto** como servicio de Windows
4. ✅ Configura inicio automático al encender el PC

**¡Listo! Ya no necesitas hacer nada más.**

---

## 🎮 Uso

### Modo Normal (Rotación Continua)
```bash
python RotadorSimBank.py
```
Rota cada 30 minutos automáticamente.

### Modo Activación Masiva (1024 SIMs)
```bash
python RotadorSimBank.py --activacion-masiva
```
Procesa todos los slots (1-32) una sola vez. Ideal para activar todas las SIMs.

### Otros Comandos

```bash
# Probar conexión con SIM Banks
python RotadorSimBank.py --self-test

# Modo prueba (sin tocar hardware)
python RotadorSimBank.py --dry-run

# Exportar base de datos PostgreSQL
python RotadorSimBank.py --export-db

# Limpiar duplicados
python RotadorSimBank.py --clean-duplicates

# Actualizar desde GitHub
python RotadorSimBank.py --update

# Ver todas las opciones
python RotadorSimBank.py --help
```

---

## 🎛️ Control Remoto desde Cualquier Lugar

### ¿Qué es el Agente de Control Remoto?

Es un **servicio de Windows** que corre 24/7 en cada PC con SIM Banks. Te permite:

- 🔄 **Reiniciar el PC** remotamente
- 🔄 **Reiniciar Hero-SMS** cuando se cuelga
- 🔄 **Reiniciar el Rotador** si algo falla
- 🛑 **Detener el Rotador** cuando quieras
- 📊 **Ver estado en tiempo real** (CPU, RAM, uptime, servicios)

### ¿Cómo funciona?

```
Dashboard Web (Vercel)  <──>  Agente (PC)  <──>  RotadorSimBank + Hero-SMS
    ^                            ^
    │                            │
    └─ Controlas desde celular/laptop desde cualquier lugar
```

### Acceso al Dashboard

**URL:** https://claro-pool-dashboard.vercel.app

Desde ahí puedes:
- Ver todas tus máquinas conectadas
- Enviar comandos (reiniciar, detener, etc.)
- Ver estado en tiempo real
- Ver historial de comandos

### Instalación del Agente (AUTOMÁTICA)

El agente se instala automáticamente cuando ejecutas `INSTALAR.bat` como Administrador.

Si ya instalaste el rotador antes y quieres solo el agente:
```bash
python RotadorSimBank.py --instalar-servicio
```

### Gestionar el Servicio

```bash
# Ver estado del agente
nssm status AgenteRotadorSimBank

# Reiniciar agente
nssm restart AgenteRotadorSimBank

# Detener agente
nssm stop AgenteRotadorSimBank

# Desinstalar agente
nssm remove AgenteRotadorSimBank confirm
```

### Logs del Agente

- `agente_stdout.log` - Salida estándar del agente
- `agente_stderr.log` - Errores del agente

---

## ⚙️ Configuración (Primera Vez)

### 1. Configurar Puertos COM de SIM Banks

Abre `RotadorSimBank.py` y edita (líneas ~119-124):

```python
SIM_BANKS = {
    "Pool1": {"com": "COM38", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 0},
    "Pool2": {"com": "COM37", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 8},
    "Pool3": {"com": "COM36", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 16},
    "Pool4": {"com": "COM35", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 24},
}
```

### 2. Configurar PostgreSQL (OPCIONAL)

Edita (líneas ~104-110):

```python
DB_ENABLED = True  # Cambiar a False si no tienes PostgreSQL
DB_HOST = "crossover.proxy.rlwy.net"
DB_NAME = "railway"
DB_USER = "postgres"
DB_PASSWORD = "tu_password"
DB_PORT = 43307
DB_TABLE = "claro_numbers"
```

### 3. Configurar Auto-Actualización (OPCIONAL)

Edita (línea ~52):

```python
REPO_URL = "https://github.com/stgomoyaa/rotador-simbank.git"
```

### 4. Configurar Agente de Control Remoto

Edita (líneas ~54-56) **SOLO si vas a cambiar el dashboard**:

```python
AGENTE_API_URL = "https://claro-pool-dashboard.vercel.app/api/commands"
AGENTE_AUTH_TOKEN = "0l7TnHmWwOg3J4YBPhqZt9z1CDiMfLAk"  # Token de autenticación
AGENTE_POLL_INTERVAL = 10  # Segundos entre consultas
```

**⚠️ IMPORTANTE:** El `AGENTE_AUTH_TOKEN` debe coincidir con el token configurado en el dashboard de Vercel.

---

## 📂 Archivos del Proyecto

### Archivos Esenciales (NO BORRAR)
- `RotadorSimBank.py` - **Script principal** (incluye rotador + agente integrado)
- `INSTALAR.bat` - Instalador automático de todo
- `EJECUTAR.bat` - Menú de ejecución rápida
- `README.md` - Esta documentación

### Archivos Generados (Auto-creados)
- `rotador_simbank.log` - Log principal
- `rotador_state.json` - Estado persistente
- `rotador_metrics.json` - Métricas acumuladas
- `iccids_history.json` - Historial de ICCIDs
- `listadonumeros_claro.txt` - Números activados
- `log_activacion_rotador.txt` - Log de activaciones
- `agente_stdout.log` - Log del agente
- `agente_stderr.log` - Errores del agente
- `nssm.exe` - Utilidad para servicios de Windows

---

## 🚀 Despliegue en Múltiples Máquinas

### Paso 1: Preparar el Script

En la **primera máquina**, configura `RotadorSimBank.py` con los puertos COM correctos.

### Paso 2: Copiar a Otras Máquinas

Copia **SOLO estos 3 archivos** a cada máquina:
1. `RotadorSimBank.py`
2. `INSTALAR.bat`
3. `EJECUTAR.bat` (opcional, para menú)

### Paso 3: Ejecutar Instalación

En cada máquina:
1. Click derecho en `INSTALAR.bat`
2. "Ejecutar como administrador"
3. Esperar a que termine (instala todo automáticamente)

**¡Listo!** Cada máquina ahora tiene:
- ✅ Rotador instalado
- ✅ Agente de control remoto corriendo como servicio
- ✅ Auto-inicio al encender el PC
- ✅ Visible en el dashboard web

---

## 🎯 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                  DASHBOARD WEB (Vercel)                     │
│        https://claro-pool-dashboard.vercel.app              │
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │ PC1 🟢   │ PC2 🟢   │ PC3 🟢   │ PC4 🔴   │             │
│  └──────────┴──────────┴──────────┴──────────┘             │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              AGENTE (Servicio Windows 24/7)                 │
│  Polling cada 10s → Ejecuta comandos → Reporta estado       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  ROTADOR + HERO-SMS                         │
│  32 slots × 32 SIMs = 1024 SIMs rotando automáticamente     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### El agente no aparece en el dashboard

```bash
# 1. Verificar que el servicio está corriendo
nssm status AgenteRotadorSimBank

# 2. Ver logs del agente
type agente_stdout.log

# 3. Reiniciar el servicio
nssm restart AgenteRotadorSimBank
```

### El rotador no arranca

```bash
# 1. Ver el log
type rotador_simbank.log

# 2. Verificar COM ports
python RotadorSimBank.py --self-test

# 3. Eliminar lock file si existe
del rotador.lock
```

### Error "Ya hay una instancia ejecutándose"

```bash
# Eliminar el archivo lock
del rotador.lock
```

### Comandos remotos no se ejecutan

1. Verificar que `AGENTE_AUTH_TOKEN` coincide con el del dashboard
2. Verificar firewall (debe permitir salida HTTPS)
3. Ver logs: `type agente_stdout.log`

---

## 📊 Comandos Disponibles desde el Dashboard

| Comando | Descripción | Tiempo |
|---------|-------------|--------|
| `restart_pc` | Reinicia el PC completamente | 10s |
| `restart_herosms` | Cierra y abre Hero-SMS | 5s |
| `restart_rotador` | Reinicia RotadorSimBank.py | 5s |
| `stop_rotador` | Detiene RotadorSimBank.py | Instantáneo |
| `status` | Obtiene estado completo | Automático (cada 10s) |

---

## 🔒 Seguridad

- ✅ Autenticación con token Bearer
- ✅ HTTPS automático (Vercel)
- ✅ Sin exposición de puertos locales
- ✅ Tokens expiran después de 5 minutos
- ✅ Logs completos de todas las acciones

**⚠️ IMPORTANTE:** El `AGENTE_AUTH_TOKEN` es tu llave de acceso. No lo compartas públicamente.

---

## 📝 Changelog

### v2.7.0 (2026-01-14)
- 🆕 **Agente de Control Remoto integrado** en el script principal
- 🆕 Instalación automática como servicio de Windows
- 🆕 Dashboard web para control desde cualquier lugar
- 🆕 Auto-actualización del agente
- 🆕 `INSTALAR.bat` ahora instala TODO en un solo paso
- 🆕 No requiere archivos separados ni configuración manual de paths
- ✅ Simplificado a **3 archivos esenciales** para despliegue

### v2.6.3 (2026-01-13)
- 🐛 Fixed AttributeError in `cambiar_slot_pool`
- ✅ Improved ICCID verification logic

### v2.6.0 (2026-01-10)
- 🆕 PostgreSQL integration
- 🆕 Auto-update from GitHub
- 🆕 Database export functionality

### v2.5.0 (2026-01-08)
- 🆕 ICCID change verification
- 🆕 Network registration check (AT+CREG?)
- 🆕 Signal quality check (AT+CSQ)

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs (`rotador_simbank.log`, `agente_stdout.log`)
2. Ejecuta `python RotadorSimBank.py --self-test`
3. Verifica la configuración de COM ports
4. Revisa el dashboard web para ver el estado

---

## 🎉 ¡Listo para Producción!

Ahora solo necesitas:
1. Ejecutar `INSTALAR.bat` (como Admin)
2. Esperar 2 minutos
3. Todo funcionará automáticamente

**Dashboard:** https://claro-pool-dashboard.vercel.app
**Repositorio:** https://github.com/stgomoyaa/rotador-simbank

---

**Versión:** 2.7.0  
**Última actualización:** 2026-01-14  
**Autor:** Sistema Claro Pool  
**Licencia:** Privado
