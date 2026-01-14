# 🔄 Rotador Automático de SIM Bank v2.10.3

Sistema inteligente de rotación automática de slots en SIM Banks con activación de SIMs Claro, agente de control remoto 24/7 y auto-detección de configuración.

---

## 🚀 Instalación Ultra-Rápida

### 1. Copiar archivos al servidor

**Solo necesitas 4 archivos:**
```
📁 Servidor/
├── RotadorSimBank.py      ⭐ Script principal
├── INSTALAR.bat           ⭐ Instalador TODO EN UNO
├── instalar_agente.ps1    🔧 Script de instalación del agente
└── EJECUTAR.bat           💡 Menú de opciones
```

### 2. Ejecutar instalación

**Click derecho en `INSTALAR.bat` → "Ejecutar como administrador"**

**¡Eso es todo!** El instalador hace:
- ✅ Verifica que Python esté instalado
- ✅ Instala todas las dependencias (pyserial, rich, psycopg2, requests, psutil, Pillow, mss)
- ✅ Instala el agente como Tarea Programada de Windows
- ✅ Configura inicio automático al iniciar sesión
- ✅ Inicia el agente inmediatamente

**Tiempo total:** ~2 minutos

---

## 🎮 Uso

### Ejecutar el rotador (modo por defecto = activación masiva)
```bash
python RotadorSimBank.py
```

### Modo continuo (rotación cada 30 minutos)
```bash
python RotadorSimBank.py --modo-continuo
```

### Detectar SIM Banks automáticamente
```bash
python RotadorSimBank.py --detectar-simbanks
```

### Ver todas las opciones
```bash
python RotadorSimBank.py --help
```

O simplemente ejecuta `EJECUTAR.bat` para un menú interactivo.

---

## 🎛️ Control Remoto desde Cualquier Lugar

### Dashboard Web
**URL:** https://claro-pool-dashboard.vercel.app

Desde el dashboard puedes:
- 📊 Ver todas las máquinas conectadas en tiempo real
- 🏥 **Health check completo** (Hero-SMS: ✅/❌, Rotador: ✅/❌)
- 🔄 Reiniciar PC / Hero-SMS / Rotador
- 🛑 Detener servicios
- 📥 Forzar actualización del script
- 📄 **Leer logs remotamente** (principal, activación, agente)
- 📈 Ver CPU, RAM, uptime, timers
- 📜 Ver historial de comandos

### El agente de control remoto:
- ✅ Se instala automáticamente con `INSTALAR.bat`
- ✅ Corre 24/7 como Tarea Programada de Windows
- ✅ Se inicia automáticamente al iniciar sesión en Windows
- ✅ Reporta estado cada 10 segundos (CPU, RAM, servicios)
- ✅ Verifica actualizaciones cada 24 horas automáticamente
- ✅ Soporte completo para capturas de pantalla remotas
- ✅ Permite forzar actualización desde el dashboard
- ✅ **Reinicia Hero-SMS cada 2 horas automáticamente** (solo si no está corriendo el rotador)
- ✅ **Health check completo** (detecta si Hero-SMS y Rotador están corriendo)
- ✅ **Lectura de logs remotos** desde el dashboard

---

## ⚙️ Configuración Automática

### Auto-detección de SIM Banks
El script detecta automáticamente la configuración de tus SIM Banks desde los logs de HeroSMS-Partners.

**Prioridad:**
1. ✅ Detecta desde `C:\Users\...\HeroSMS-Partners\app\log\simBanks.txt`
2. ✅ Si falla, carga desde `simbanks_config.json` (guardada)
3. ✅ Si falla, usa configuración por defecto en el script

**Forzar detección:**
```bash
python RotadorSimBank.py --detectar-simbanks
```

### Formatos soportados en logs:
- `'Pool #1'` → Pool1
- `'Pool 1'` → Pool1
- `'1'` → Pool1
- Cualquier variación con números

---

## 🔧 Comandos Útiles

### Gestionar la Tarea Programada del agente
```powershell
# Ver estado
Get-ScheduledTask -TaskName "AgenteRotadorSimBank"

# Iniciar
Start-ScheduledTask -TaskName "AgenteRotadorSimBank"

# Detener
Stop-ScheduledTask -TaskName "AgenteRotadorSimBank"

# Ver información detallada
Get-ScheduledTaskInfo -TaskName "AgenteRotadorSimBank"

# Desinstalar (ejecutar en PowerShell)
powershell -ExecutionPolicy Bypass -File desinstalar_agente.ps1
```

### Otros comandos
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
```

---

## 📱 Control Remoto desde Dashboard

### Comandos Disponibles (v2.10.3)

| Comando | Descripción | Nuevo |
|---------|-------------|-------|
| `restart_pc` | Reinicia la PC | |
| `start_herosms` | **Inicia HeroSMS-Partners** | ⭐ |
| `restart_herosms` | Reinicia HeroSMS-Partners | |
| `start_rotador` | **Inicia el rotador** | ⭐ |
| `restart_rotador` | Reinicia el script RotadorSimBank.py | |
| `stop_rotador` | Detiene el script RotadorSimBank.py | |
| `restart_agent` | **Reinicia la tarea del agente** | ⭐ |
| `update` | Fuerza actualización del script | |
| `get_logs` | Lee log principal | |
| `get_activation_logs` | Lee log de activación | |
| `get_agent_logs` | Lee log del agente | |
| `set_name:Nombre` | **Cambia nombre de la máquina** | ⭐ |
| `take_screenshot` | **Captura de pantalla** | ⭐ |

### Funcionalidades Nuevas v2.10.0

#### 🏷️  Nombres Personalizados
- Cambia el nombre de visualización de cada máquina en el dashboard
- El nombre se guarda localmente en `machine_config.json`
- No afecta el hostname del sistema
- Útil para identificar: "Servidor Pool 1", "Servidor Pool 2", etc.

#### 🟢 Comandos de Inicio
- `start_herosms`: Abre HeroSMS-Partners si no está corriendo
- `start_rotador`: Inicia el rotador si no está activo
- Útil después de reiniciar la PC o detener servicios manualmente

#### 📸 Capturas de Pantalla
- Captura la pantalla completa de la máquina remota
- Se redimensiona automáticamente a max 1280px de ancho
- Comprimida en JPEG (75% calidad) para transmisión rápida
- Visualiza y descarga desde el dashboard

**Dashboard:** https://claro-pool-dashboard.vercel.app

**Documentación completa:** [`DASHBOARD_API.md`](DASHBOARD_API.md)

---

## 📂 Archivos Generados

Después de ejecutar, el script crea automáticamente:

```
📁 Servidor/
├── RotadorSimBank.py
├── INSTALAR.bat
├── EJECUTAR.bat
├── DIAGNOSTICO_SERVICIO.bat          ← Diagnóstico del servicio
├── nssm.exe                          ← Auto-descargado
├── simbanks_config.json              ← Auto-detectado
├── machine_config.json               ← Nombre personalizado (v2.10.0)
├── rotador_state.json                ← Estado persistente
├── rotador_metrics.json              ← Métricas
├── rotador_simbank.log               ← Log principal
├── listadonumeros_claro.txt          ← Números activados
├── agente_stdout.log                 ← Log del agente
└── agente_stderr.log                 ← Errores del agente
```

---

## 🛠️ Solución de Problemas

### "pip no se reconoce como comando"

**Solución:** Python no está en el PATH. Durante la instalación de Python, marca:
```
☑ Add Python to PATH
```

O usa: `python -m pip install ...` en lugar de `pip install ...`

### "No se encuentra RotadorSimBank.py"

**Solución:** Ejecuta `INSTALAR.bat` desde la misma carpeta donde está `RotadorSimBank.py`

### "Error descargando NSSM"

**Solución:** `INSTALAR.bat` ya maneja este error automáticamente usando PowerShell. Si falla, descarga manualmente desde https://nssm.cc/release/nssm-2.24.zip

### El servicio está en estado PAUSED o no inicia

**Solución:**
1. **Ejecuta el script de diagnóstico:** `DIAGNOSTICO_SERVICIO.bat`
2. **Prueba manualmente:** `python RotadorSimBank.py --agente`
3. **Verifica los logs:**
   - `type agente_stdout.log` (salida estándar)
   - `type agente_stderr.log` (errores)
   - `type agente_error.log` (errores críticos)
4. **Reinstala el servicio:**
   ```bash
   nssm remove AgenteRotadorSimBank confirm
   python RotadorSimBank.py --instalar-servicio
   ```

### El agente no aparece en el dashboard

**Solución:**
1. Verifica que el servicio esté corriendo: `nssm status AgenteRotadorSimBank`
2. Verifica los logs: `type agente_stdout.log`
3. Reinicia el servicio: `nssm restart AgenteRotadorSimBank`
4. Ejecuta diagnóstico completo: `DIAGNOSTICO_SERVICIO.bat`

---

## 🚀 Despliegue en Múltiples Servidores

### Proceso para cada servidor (3 minutos):

1. **Copiar 3 archivos:**
   - `RotadorSimBank.py`
   - `INSTALAR.bat`
   - `EJECUTAR.bat`

2. **Ejecutar:**
   - Click derecho en `INSTALAR.bat` → "Ejecutar como administrador"

3. **Verificar:**
   - Abrir dashboard: https://claro-pool-dashboard.vercel.app
   - Ver que la máquina aparece 🟢

**¡Listo para el siguiente servidor!**

---

## 🎯 Características Principales

- ✅ **Auto-detección de SIM Banks** desde HeroSMS-Partners
- ✅ **Activación automática** de SIMs Claro (modo masivo por defecto)
- ✅ **Control remoto 24/7** vía dashboard web
- ✅ **Persistencia en PostgreSQL** (opcional)
- ✅ **Auto-actualización** desde GitHub
- ✅ **Instalación de 1 click** (INSTALAR.bat)
- ✅ **Servicio de Windows** con inicio automático
- ✅ **Sin configuración manual** de puertos COM

---

## 📊 Modos de Operación

### Modo Activación Masiva (Por Defecto)
- Procesa los 32 slots (1024 SIMs) en una sola pasada
- No abre/cierra HeroSMS-Partners entre slots
- Tiempo estimado: 2-3 horas
- **Comando:** `python RotadorSimBank.py`

### Modo Continuo
- Rota cada 30 minutos indefinidamente
- Abre/cierra HeroSMS-Partners en cada rotación
- Para operación 24/7
- **Comando:** `python RotadorSimBank.py --modo-continuo`

---

## 🔒 Seguridad

- ✅ Autenticación con token Bearer
- ✅ HTTPS automático (Vercel)
- ✅ Sin exposición de puertos locales
- ✅ Logs completos de todas las acciones

**Token configurado en:**
- `RotadorSimBank.py` (línea ~56): `AGENTE_AUTH_TOKEN`
- Vercel Dashboard → Environment Variables

---

## 📝 Requisitos

- **Python 3.7+** ([descargar](https://www.python.org/downloads/))
- **Windows 10/11**
- **HeroSMS-Partners** instalado y configurado
- **Permisos de Administrador** (para instalar servicio)

---

## 💾 Base de Datos PostgreSQL (Opcional)

Si tienes PostgreSQL configurado, edita en `RotadorSimBank.py` (líneas ~104-110):

```python
DB_ENABLED = True  # Cambiar a False si no tienes PostgreSQL
DB_HOST = "tu_host"
DB_NAME = "tu_database"
DB_USER = "tu_usuario"
DB_PASSWORD = "tu_password"
DB_PORT = 5432
```

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs (`rotador_simbank.log`, `agente_stdout.log`)
2. Ejecuta `python RotadorSimBank.py --self-test`
3. Verifica el dashboard web: https://claro-pool-dashboard.vercel.app

---

## 🎉 ¡Listo!

Con solo **3 archivos** y **1 click** tienes todo funcionando:
- ✅ Rotador automático
- ✅ Agente de control remoto
- ✅ Auto-detección de SIM Banks
- ✅ Dashboard web

**Versión:** 2.8.1  
**Última actualización:** 2026-01-14  
**Repositorio:** https://github.com/stgomoyaa/rotador-simbank
