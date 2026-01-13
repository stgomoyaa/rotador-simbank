# 🔄 Rotador Automático de SIM Bank v2.6.2

Sistema inteligente de rotación automática de slots en SIM Banks con activación de SIMs Claro, auto-actualización y persistencia en PostgreSQL.

---

## 📦 Instalación (Primera Vez)

### 1. Requisitos Previos
- **Python 3.7+** instalado ([descargar](https://www.python.org/downloads/))
- **Git** (opcional, para clonar desde GitHub)

### 2. Instalar Dependencias

**Opción A: Automático**
```bash
INSTALAR.bat
```

**Opción B: Manual**
```bash
pip install pyserial rich psycopg2-binary
```

### 3. Configurar el Script

Abre `RotadorSimBank.py` y edita:

**a) Puertos COM de tus SIM Banks (líneas ~119-124):**
```python
SIM_BANKS = {
    "Pool1": {"com": "COM62", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 0},
    "Pool2": {"com": "COM60", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 8},
    "Pool3": {"com": "COM61", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 16},
    "Pool4": {"com": "COM59", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 24},
}
```

**b) Base de datos PostgreSQL (líneas ~104-110, OPCIONAL):**
```python
DB_ENABLED = True  # Cambiar a False si no tienes PostgreSQL
DB_HOST = "tu_host"
DB_NAME = "tu_database"
DB_USER = "tu_usuario"
DB_PASSWORD = "tu_password"
DB_PORT = 5432
```

**c) Repositorio para auto-actualización (línea ~52, OPCIONAL):**
```python
REPO_URL = "https://github.com/TU_USUARIO/TU_REPO.git"
```

---

## 🚀 Uso

### Modo Normal (Rotación Continua)
```bash
EJECUTAR.bat
```
o
```bash
python RotadorSimBank.py
```
Rota cada 30 minutos automáticamente.

### Modo Activación Masiva (1024 SIMs)
```bash
EJECUTAR.bat --activacion-masiva
```
Procesa todos los slots (1-32) una sola vez, sin esperas. Ideal para activar todas las SIMs de golpe.

### Otros Comandos Útiles

```bash
# Probar conexión con SIM Banks
python RotadorSimBank.py --self-test

# Modo prueba (sin tocar hardware)
python RotadorSimBank.py --dry-run

# Exportar base de datos PostgreSQL a archivo
python RotadorSimBank.py --export-db

# Limpiar duplicados del archivo local
python RotadorSimBank.py --clean-duplicates

# Forzar actualización desde GitHub
python RotadorSimBank.py --update

# Comenzar desde un slot específico
python RotadorSimBank.py --slot-start 15

# Cambiar intervalo de rotación (en minutos)
python RotadorSimBank.py --intervalo 45

# Ver todas las opciones
python RotadorSimBank.py --help
```

---

## 🏗️ Arquitectura del Sistema

- **4 Pools** de SIM Banks (Pool1, Pool2, Pool3, Pool4)
- **8 Puertos lógicos** por pool (01-08)
- **32 Slots** por pool (1-32)
- **Total: 1024 SIMs** (4 pools × 8 puertos × 32 slots)

**Offsets escalonados:**
- Pool1: Slot 1 → Pool2: Slot 9 → Pool3: Slot 17 → Pool4: Slot 25
- Esto evita duplicados entre pools en la misma rotación.

---

## ✨ Características Principales

### v2.6.2 (Última Versión)
- ✅ **Rotación automática** con verificación de ICCID (detecta si realmente cambió la SIM)
- ✅ **Activación automática de SIMs Claro** (envío de USSD `*103#`, lectura de SMS, guardado de número)
- ✅ **Verificación de red (CREG/CSQ)** antes de activar (mejora tasa de éxito)
- ✅ **Guardado triple:** Archivo local + SIM (contacto "myphone") + PostgreSQL
- ✅ **Auto-actualización desde GitHub** con reinicio automático (sin errores en rutas con espacios)
- ✅ **Modo activación masiva** con confirmación automática (sin interrupciones)
- ✅ **Exportación de base de datos** PostgreSQL → archivo local
- ✅ **Limpieza de duplicados** en archivo local
- ✅ **Persistencia de estado** (recuerda el slot y continúa si se reinicia)
- ✅ **Procesamiento paralelo** con threading (rápido y eficiente)
- ✅ **Manejo de errores robusto** con reintentos y blacklist de puertos problemáticos

---

## 📝 Archivos Generados (Automáticamente)

Durante la ejecución, el script genera:

- `listadonumeros_claro.txt` - Números activados (formato: `569XXXXXXXX=ICCID`)
- `log_activacion_rotador.txt` - Log específico del proceso de activación
- `rotador_simbank_YYYY-MM-DD.log` - Log diario de operaciones
- `rotador_state.json` - Estado actual (slot e iteración)
- `rotador_metrics.json` - Métricas acumuladas
- `iccids_history.json` - Historial de ICCIDs detectados
- `snapshots/` - Carpeta con snapshots de cada rotación

**Nota:** Estos archivos son ignorados por Git (están en `.gitignore`).

---

## 🔧 Solución de Problemas

### ❌ No detecta los SIM Banks
```bash
python RotadorSimBank.py --self-test
```
Verifica que los puertos COM estén correctos en la configuración.

### ❌ Error de conexión con PostgreSQL
Edita `RotadorSimBank.py`:
```python
DB_ENABLED = False  # Línea ~104
```
El script seguirá guardando en el archivo local.

### ❌ Error "CME ERROR: 30" (sin red)
El script ya incluye verificación de red antes de activar. Si persiste:
- Verifica que las SIMs tengan cobertura
- Aumenta `MAX_INTENTOS_REGISTRO_RED` (línea ~68)

### ❌ ICCIDs duplicados
El script ahora verifica que los ICCIDs cambien después de cada rotación. Si persiste:
- Verifica conexiones físicas de los SIM Banks
- Revisa logs para identificar puertos problemáticos

### ⚠️ Ya hay una instancia ejecutándose
```bash
# Eliminar el archivo lock manualmente
del rotador.lock
```

---

## 📊 Monitoreo y Logs

- **Log principal:** `rotador_simbank_YYYY-MM-DD.log`
- **Log activación:** `log_activacion_rotador.txt`
- **Métricas:** `rotador_metrics.json`
- **Estado actual:** `rotador_state.json`

**Ver log en tiempo real:**
```bash
# En PowerShell
Get-Content rotador_simbank_2026-01-XX.log -Wait -Tail 50
```

---

## 🔐 Git y GitHub (Opcional)

Si quieres mantener tu código en GitHub:

1. **Configurar tu repositorio:**
   ```bash
   git remote set-url origin https://github.com/TU_USUARIO/TU_REPO.git
   ```

2. **Hacer commit y push:**
   ```bash
   git add .
   git commit -m "Actualización del rotador"
   git push origin main
   ```

**Nota:** El `.gitignore` está configurado para NO subir:
- Archivos con credenciales (`.bat` con tokens)
- Datos privados (`listadonumeros_claro.txt`)
- Logs y archivos de estado

---

## 📞 Soporte

- **Repositorio:** https://github.com/stgomoyaa/rotador-simbank
- **Versión:** 2.6.2

---

## 🛠️ Estructura de Archivos

```
Claro Pool/
├── RotadorSimBank.py       # Script principal (ESENCIAL)
├── EJECUTAR.bat            # Ejecutar el rotador (ESENCIAL)
├── INSTALAR.bat            # Instalar dependencias (ESENCIAL)
├── README.md               # Este archivo (DOCUMENTACIÓN)
└── .gitignore              # Configuración de Git
```

**Archivos generados** (creados automáticamente al ejecutar):
```
├── listadonumeros_claro.txt
├── log_activacion_rotador.txt
├── rotador_simbank_2026-XX-XX.log
├── rotador_state.json
├── rotador_metrics.json
├── iccids_history.json
└── snapshots/
```

---

## 📚 Ejemplos de Uso Completos

### Ejemplo 1: Primera ejecución
```bash
# 1. Instalar dependencias
INSTALAR.bat

# 2. Ejecutar en modo prueba (sin tocar hardware)
EJECUTAR.bat --dry-run

# 3. Verificar que detecta los SIM Banks
EJECUTAR.bat --self-test

# 4. Ejecutar en modo normal
EJECUTAR.bat
```

### Ejemplo 2: Activación masiva
```bash
# Activar todas las 1024 SIMs de una vez
EJECUTAR.bat --activacion-masiva
```

### Ejemplo 3: Mantenimiento
```bash
# Exportar base de datos a archivo local
EJECUTAR.bat --export-db

# Limpiar duplicados del archivo
EJECUTAR.bat --clean-duplicates

# Actualizar a la última versión desde GitHub
EJECUTAR.bat --update
```

---

**¡Listo para usar! 🎉**
