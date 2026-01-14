# 🔧 Solución: Capturas de Pantalla no Funcionan

## 🔴 PROBLEMA

Al enviar el comando `take_screenshot` desde el dashboard, obtienes:

```
✅ Resultado: {'success': False, 'message': 'Error al capturar pantalla'}
```

---

## 🎯 CAUSA RAÍZ

**Los servicios de Windows corren en "Session 0"** (sin interfaz gráfica) y **NO pueden capturar la pantalla del usuario** que está en "Session 1".

```
Session 0 (Servicios)          Session 1 (Usuario)
┌────────────────────┐         ┌────────────────────┐
│  AgenteRotador     │         │  Tu escritorio     │
│  (sin pantalla)    │  ❌     │  (con pantalla)    │
└────────────────────┘         └────────────────────┘
```

Este es un **límite de seguridad de Windows** para aislar servicios de las sesiones de usuario.

---

## ✅ SOLUCIÓN 1: Actualizar a v2.10.3 (Recomendado)

He implementado **3 métodos de fallback** que intentan capturar la pantalla de diferentes formas:

### Actualizar el Servidor

```powershell
cd C:\Rotador  # Tu carpeta

# Descargar última versión
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/stgomoyaa/rotador-simbank/main/RotadorSimBank.py" -OutFile "RotadorSimBank.py"

# Instalar nueva dependencia (mss)
python -m pip install mss

# Reiniciar servicio
.\nssm restart AgenteRotadorSimBank

# Verificar versión
timeout /t 10
Get-Content agente_stdout.log -Tail 5
```

**Deberías ver:**
```
AGENTE INICIADO - v2.10.3
```

---

## ✅ SOLUCIÓN 2: Ejecutar el Agente Manualmente

Si necesitas capturas de pantalla **inmediatamente**, ejecuta el agente manualmente (en Session 1):

```powershell
# 1. Detener el servicio
.\nssm stop AgenteRotadorSimBank

# 2. Ejecutar manualmente
python RotadorSimBank.py --agente
```

**Ahora las capturas SÍ funcionarán** porque el agente corre en tu sesión de usuario.

**Desventajas:**
- ❌ El agente se cierra cuando cierres la ventana
- ❌ No se inicia automáticamente al encender la PC
- ❌ Debes tenerlo corriendo manualmente

**Para volver al modo servicio:**
```powershell
# Detener el agente manual (Ctrl+C)
# Reiniciar el servicio
.\nssm start AgenteRotadorSimBank
```

---

## ✅ SOLUCIÓN 3: Script de Captura Externo (Avanzado)

Crear un script que se ejecute en la sesión del usuario y guarde la captura en un archivo compartido.

### 1. Crear script de captura

```powershell
# Guardar como: C:\Rotador\screenshot.ps1

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)

$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$path = "C:\Rotador\screenshots\screenshot_$timestamp.png"

$bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Output $path
```

### 2. Configurar tarea programada del usuario

```powershell
# Crear tarea que corre en tu sesión de usuario
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Rotador\screenshot.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName "ScreenshotCapture" -Action $action -Trigger $trigger -Principal $principal
```

---

## 🧪 PROBAR LOS MÉTODOS DE CAPTURA

### Método 1: mss (Mejor para servicios)

```powershell
python -c "import mss; print('mss disponible:', mss is not None)"
```

**Esperado:** `mss disponible: True`

### Método 2: PIL ImageGrab

```powershell
python -c "from PIL import ImageGrab; img = ImageGrab.grab(); print('Captura exitosa:', img.size)"
```

**Esperado:** `Captura exitosa: (1920, 1080)` (tu resolución)

### Método 3: PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File C:\Rotador\screenshot.ps1
```

**Esperado:** Debe crear un archivo PNG

---

## 📊 COMPARACIÓN DE MÉTODOS

| Método | Funciona en Servicio | Calidad | Velocidad | Requiere |
|--------|----------------------|---------|-----------|----------|
| **mss** | ⚠️  A veces | Alta | Rápido | `pip install mss` |
| **PIL ImageGrab** | ❌ No | Alta | Medio | `pip install Pillow` |
| **PowerShell** | ⚠️  A veces | Alta | Lento | Windows built-in |
| **Agente Manual** | ✅ Sí | Alta | Rápido | Ejecutar manualmente |

---

## 🔍 DIAGNÓSTICO

### Ver logs detallados del intento de captura:

```powershell
# Ver últimas 50 líneas del log del agente
Get-Content C:\Rotador\agente_stdout.log -Tail 50
```

**Busca estas líneas:**
```
📸 Intentando captura con mss...
✅ Captura exitosa con mss

O

⚠️  mss falló: [error]
📸 Intentando captura con PIL ImageGrab...
✅ Captura exitosa con PIL

O

❌ Todos los métodos de captura fallaron
💡 Nota: Los servicios de Windows (Session 0) no pueden capturar...
```

---

## 🎯 SOLUCIÓN DEFINITIVA (v2.10.3)

### Lo que hace la nueva versión:

1. **Intenta mss primero** (mejor compatibilidad con servicios)
2. **Si falla, intenta PIL ImageGrab**
3. **Si falla, intenta PowerShell**
4. **Si todo falla, explica el problema claramente**

### Código implementado:

```python
def take_screenshot(self):
    # Método 1: mss
    if mss is not None:
        try:
            with mss.mss() as sct:
                screenshot_raw = sct.grab(sct.monitors[1])
                screenshot = Image.frombytes('RGB', screenshot_raw.size, screenshot_raw.rgb)
                # ... redimensionar y comprimir ...
                return img_base64
        except Exception as e:
            console.print(f"⚠️  mss falló: {e}")
    
    # Método 2: PIL ImageGrab
    try:
        screenshot = ImageGrab.grab()
        # ... procesar ...
        return img_base64
    except Exception as e:
        console.print(f"⚠️  PIL falló: {e}")
    
    # Método 3: PowerShell
    try:
        # Script PowerShell para capturar
        # ... ejecutar y procesar ...
        return img_base64
    except Exception as e:
        console.print(f"⚠️  PowerShell falló: {e}")
    
    return None  # Todos fallaron
```

---

## 📋 CHECKLIST DE ACTUALIZACIÓN

- [ ] Actualizar a v2.10.3
- [ ] Instalar `mss`: `pip install mss`
- [ ] Reiniciar servicio del agente
- [ ] Verificar versión en logs
- [ ] Probar comando `take_screenshot`
- [ ] Verificar logs del intento de captura

---

## 💡 ALTERNATIVAS SI NADA FUNCIONA

### Opción A: RDP + Captura Manual

1. Conéctate al servidor vía RDP
2. Ejecuta el agente manualmente: `python RotadorSimBank.py --agente`
3. Envía el comando de captura desde el dashboard
4. Desconéctate (el agente seguirá corriendo en tu sesión)

### Opción B: Herramienta Externa

Usa una herramienta de monitoreo visual como:
- **AnyDesk** / **TeamViewer** (acceso remoto visual)
- **OBS Studio** (streaming de pantalla)
- **Windows Remote Assistance**

### Opción C: Desactivar Capturas

Si no necesitas capturas de pantalla frecuentemente, simplemente no uses esa funcionalidad. Todas las demás funciones del dashboard seguirán funcionando perfectamente.

---

## 🚀 PRÓXIMOS PASOS

1. **Actualiza a v2.10.3** (5 minutos)
2. **Prueba las capturas** desde el dashboard
3. **Si funciona:** ¡Listo! 🎉
4. **Si no funciona:** Ejecuta el agente manualmente cuando necesites capturas

---

¿La captura funcionó después de actualizar? Comparte el resultado. 📸
