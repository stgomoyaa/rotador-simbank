# 📦 INSTRUCCIONES DE INSTALACIÓN - Rotador SimBank v2.10.3

## ✅ **Nuevo Sistema:** Tarea Programada (NO NSSM)

La versión 2.10.3 **ya NO usa NSSM**. Ahora el agente se instala como una **Tarea Programada de Windows**, que es más confiable y compatible con capturas de pantalla.

---

## 📋 Archivos Necesarios

Copia estos 4 archivos al servidor:

```
📁 Servidor/
├── RotadorSimBank.py          ⭐ Script principal
├── INSTALAR.bat               ⭐ Instalador automático
├── instalar_agente.ps1        🔧 Script de instalación del agente
└── EJECUTAR.bat               💡 Menú de opciones
```

---

## 🚀 Instalación en 3 Pasos

### **Paso 1: Click Derecho en INSTALAR.bat**

1. Ubica el archivo `INSTALAR.bat`
2. **Click derecho** → **"Ejecutar como administrador"**
3. Espera 2-3 minutos

El instalador hará automáticamente:
- ✅ Verificar Python
- ✅ Instalar dependencias (pyserial, rich, psycopg2, requests, psutil, Pillow, mss)
- ✅ Crear la Tarea Programada
- ✅ Iniciar el agente

### **Paso 2: Verificar que el Agente Está Corriendo**

Abre PowerShell y ejecuta:

```powershell
Get-ScheduledTask -TaskName "AgenteRotadorSimBank"
```

**Deberías ver:**
```
TaskName                : AgenteRotadorSimBank
State                   : Running
```

### **Paso 3: Verificar en el Dashboard**

1. Abre: https://claro-pool-dashboard.vercel.app
2. Espera 10-30 segundos
3. Tu máquina debería aparecer con **nombre del PC**
4. Verás: CPU, RAM, estado de Hero-SMS y Rotador

---

## 🔧 Comandos Útiles (PowerShell)

### Ver estado de la tarea
```powershell
Get-ScheduledTask -TaskName "AgenteRotadorSimBank"
```

### Ver información detallada
```powershell
Get-ScheduledTaskInfo -TaskName "AgenteRotadorSimBank"
```

### Iniciar manualmente
```powershell
Start-ScheduledTask -TaskName "AgenteRotadorSimBank"
```

### Detener
```powershell
Stop-ScheduledTask -TaskName "AgenteRotadorSimBank"
```

### Ver logs del agente
```powershell
Get-Content "agente_stdout.log" -Tail 50
```

### Desinstalar
```powershell
powershell -ExecutionPolicy Bypass -File desinstalar_agente.ps1
```

---

## ❓ Troubleshooting

### ❌ Error: "Acceso denegado"
**Solución:** Asegúrate de ejecutar `INSTALAR.bat` como **Administrador** (click derecho → Ejecutar como administrador)

### ❌ La tarea aparece pero no el agente en el dashboard
**Verifica los logs:**
```powershell
Get-Content "agente_stdout.log" -Tail 20
Get-Content "agente_stderr.log" -Tail 20
```

**Posibles causas:**
1. Firewall bloqueando conexión a Vercel
2. Variables de entorno incorrectas en el script
3. Python no tiene permisos

**Solución rápida:**
```powershell
# Detener tarea
Stop-ScheduledTask -TaskName "AgenteRotadorSimBank"

# Probar manualmente
python RotadorSimBank.py --agente
```

Si funciona manualmente, el problema es la configuración de la tarea.

### ❌ Error: "Python no encontrado"
**Solución:** Instala Python 3.7+ desde https://www.python.org/downloads/

**IMPORTANTE:** Durante la instalación marca:
- ☑️ **Add Python to PATH**

### ❌ La máquina no aparece en el dashboard después de 1 minuto
**Verifica:**
1. Que el agente esté corriendo: `Get-ScheduledTask -TaskName "AgenteRotadorSimBank"`
2. Los logs: `Get-Content "agente_stdout.log" -Tail 30`
3. Conexión a internet: `ping vercel.app`

---

## 🆚 Diferencias vs Versión Anterior (NSSM)

| Característica | NSSM (Antiguo) | Tarea Programada (Nuevo) |
|----------------|----------------|---------------------------|
| **Capturas de pantalla** | ❌ No funciona | ✅ Funciona |
| **Instalación** | Requiere descargar NSSM | ✅ Integrado en Windows |
| **Inicio** | Al encender PC | Al iniciar sesión |
| **Sesión** | Session 0 | Tu sesión de usuario |
| **Debugging** | Difícil | ✅ Fácil (logs claros) |
| **Problemas con espacios en rutas** | ⚠️ A veces | ✅ No hay problema |

---

## 🎯 Lo Que Hace el Agente (24/7)

El agente de control remoto ejecuta estas tareas automáticamente:

### 🔄 Cada 10 segundos:
- Reporta CPU, RAM, uptime al dashboard
- Verifica si Hero-SMS está corriendo
- Verifica si el Rotador está corriendo
- Escucha comandos desde el dashboard

### 🔄 Cada 2 horas:
- **Reinicia Hero-SMS automáticamente** (solo si el Rotador NO está corriendo)

### 🔄 Cada 24 horas:
- Verifica si hay actualizaciones en GitHub
- Si hay actualización, descarga y reinicia

### 🎛️ Comandos del Dashboard:
- Reiniciar PC / Hero-SMS / Rotador
- Iniciar Hero-SMS / Rotador
- Detener Rotador
- Leer logs remotamente
- Capturar pantalla
- Forzar actualización
- Cambiar nombre de la máquina
- Reiniciar el agente

---

## 📚 Más Información

- **Dashboard API:** Ver `DASHBOARD_API.md`
- **README principal:** Ver `README.md`
- **Funcionalidades avanzadas:** Ver `FUNCIONALIDADES_AVANZADAS.md`

---

## 🆘 Soporte

Si después de seguir estas instrucciones el agente no aparece en el dashboard:

1. Ejecuta el diagnóstico:
```powershell
# Estado de la tarea
Get-ScheduledTask -TaskName "AgenteRotadorSimBank" | Format-List *

# Logs completos
Get-Content "agente_stdout.log"
Get-Content "agente_stderr.log"

# Procesos Python corriendo
Get-Process python
```

2. Comparte la salida de estos comandos para ayuda.
