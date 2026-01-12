# 📘 GUÍA RÁPIDA - RotadorSimBank v2.6.0

## 🚀 NUEVAS FUNCIONALIDADES

### 1️⃣ Auto-Actualización desde GitHub

**¿Qué hace?**  
Verifica automáticamente si hay una nueva versión disponible en GitHub y te permite actualizarla con un clic.

**Cómo usar:**
```bash
# El script verifica automáticamente al inicio
python RotadorSimBank.py

# Saltar verificación de actualizaciones
python RotadorSimBank.py --no-update-check

# Forzar actualización inmediata
python RotadorSimBank.py --update
```

**Configurar tu repositorio:**
1. Edita `RotadorSimBank.py` línea 39:
   ```python
   REPO_URL = "https://github.com/TU_USUARIO/rotador-simbank.git"
   ```
2. Sube el script a tu repositorio de GitHub
3. ¡Listo! Ahora se actualizará automáticamente desde ahí

---

### 2️⃣ Integración con PostgreSQL

**¿Qué hace?**  
Guarda automáticamente todos los números activados en una base de datos en la nube (PostgreSQL).

**Ventajas:**
- ✅ Backup en la nube de todos tus números
- ✅ Acceso desde cualquier lugar
- ✅ Actualización inteligente (si el ICCID ya existe, actualiza el número)
- ✅ Si PostgreSQL falla, sigue guardando en archivo local

**Configuración:**
```python
DB_ENABLED = True  # Ya está activado por defecto
```

**¿Cómo funciona?**
```
Número activado → Archivo local (listadonumeros_claro.txt)
                ↓
                SIM (contacto "myphone")
                ↓
                PostgreSQL en la nube ☁️
```

**Logs que verás:**
```
✅ [COM45] Guardado en archivo: 569XXXXXXXX=8956030...
✅ [COM45] Número guardado en SIM como 'myphone'
✅ [COM45] Número 569XXXXXXXX e ICCID 8956030... guardados en DB
```

---

### 3️⃣ Exportar Base de Datos

**¿Qué hace?**  
Descarga todos los registros de PostgreSQL a tu archivo local.

**Cuándo usar:**
- Para sincronizar tu archivo local con la base de datos en la nube
- Para hacer backup de todos los números
- Para recuperar números si perdiste el archivo local

**Uso:**
```bash
python RotadorSimBank.py --export-db
```

**Resultado:**
```
📥 Exportando listado completo desde la base de datos...
✅ Exportados 1523 registros desde PostgreSQL al archivo local
```

⚠️ **Advertencia:** Esto sobrescribirá tu archivo local `listadonumeros_claro.txt`

---

### 4️⃣ Limpiar Duplicados

**¿Qué hace?**  
Elimina líneas duplicadas del archivo `listadonumeros_claro.txt`.

**Qué limpia:**
- ✅ Líneas duplicadas exactas
- ✅ Números de teléfono repetidos
- ✅ ICCIDs repetidos

**Uso:**
```bash
python RotadorSimBank.py --clean-duplicates
```

**Resultado:**
```
✅ Limpieza completa: 1850 → 1523 líneas.
```

---

## 📋 COMANDOS CLI COMPLETOS

### Modo Normal
```bash
python RotadorSimBank.py
```
- Rotación cada 30 minutos
- Verifica actualizaciones al inicio
- Guarda en archivo + SIM + PostgreSQL

### Modo Activación Masiva
```bash
python RotadorSimBank.py --activacion-masiva
```
- Procesa los 32 slots (1024 SIMs) de una vez
- Sin interrupciones
- Solo abre HeroSMS-Partners al final

### Modo Prueba (Dry Run)
```bash
python RotadorSimBank.py --dry-run
```
- Simula sin tocar hardware
- Para probar el script

### Auto-Test
```bash
python RotadorSimBank.py --self-test
```
- Verifica conectividad con SIM Banks
- Prueba comandos AT+SWIT

### Herramientas de Base de Datos
```bash
# Exportar PostgreSQL a archivo local
python RotadorSimBank.py --export-db

# Limpiar duplicados del archivo local
python RotadorSimBank.py --clean-duplicates
```

### Sistema de Actualizaciones
```bash
# Forzar actualización inmediata
python RotadorSimBank.py --update

# Saltar verificación de actualizaciones
python RotadorSimBank.py --no-update-check
```

### Otros
```bash
# Cambiar intervalo de rotación
python RotadorSimBank.py --intervalo 15  # 15 minutos

# Comenzar desde un slot específico
python RotadorSimBank.py --slot-start 10
```

---

## 🔧 CONFIGURACIÓN AVANZADA

### Desactivar PostgreSQL
Si no quieres usar PostgreSQL, edita línea 87:
```python
DB_ENABLED = False
```

### Actualización Automática sin Preguntar
Si quieres que se actualice automáticamente sin preguntar, edita línea 108:
```python
AUTO_UPDATE = True  # Por defecto es False
```

### Desactivar Verificación de Actualizaciones
Si no quieres que verifique actualizaciones al inicio, edita línea 107:
```python
CHECK_UPDATES = False  # Por defecto es True
```

---

## 📊 FLUJO DE TRABAJO RECOMENDADO

### Configuración Inicial (Una vez)

1. **Configurar GitHub** (opcional, para auto-actualización):
   ```python
   # Línea 39 de RotadorSimBank.py
   REPO_URL = "https://github.com/TU_USUARIO/rotador-simbank.git"
   ```

2. **Verificar PostgreSQL** (ya está configurado):
   ```python
   # Líneas 87-94 de RotadorSimBank.py
   DB_ENABLED = True  # ✅ Ya activado
   ```

3. **Primera ejecución**:
   ```bash
   python RotadorSimBank.py
   ```
   - El script creará automáticamente la tabla en PostgreSQL
   - Verificará si hay actualizaciones

### Uso Diario

**Opción 1: Modo Normal (Recomendado)**
```bash
python RotadorSimBank.py
```
- Rotación cada 30 minutos
- Activación automática de SIMs Claro
- Guardado en archivo + SIM + PostgreSQL

**Opción 2: Modo Activación Masiva (Setup Inicial)**
```bash
python RotadorSimBank.py --activacion-masiva
```
- Procesa todas las 1024 SIMs de una vez
- Ideal para configuración inicial o reactivación masiva

### Mantenimiento Semanal

**Limpiar duplicados:**
```bash
python RotadorSimBank.py --clean-duplicates
```

**Sincronizar con PostgreSQL:**
```bash
python RotadorSimBank.py --export-db
```

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### "No se pudo conectar a PostgreSQL"

**Solución 1:** Verifica tu conexión a internet  
**Solución 2:** Desactiva PostgreSQL temporalmente:
```python
DB_ENABLED = False
```
El script seguirá funcionando guardando solo en archivo local.

### "Error al verificar actualizaciones"

**Solución 1:** Salta la verificación:
```bash
python RotadorSimBank.py --no-update-check
```

**Solución 2:** Desactiva la verificación:
```python
CHECK_UPDATES = False
```

### "No hay ICCIDs duplicados dentro de rotación, pero PostgreSQL tiene muchos registros"

Esto es **normal**. PostgreSQL guarda **todos** los números de **todas las rotaciones** históricamente. El análisis de duplicados solo verifica que dentro de una misma rotación no haya puertos con el mismo ICCID.

---

## 📈 ESTADÍSTICAS Y MONITOREO

### Ver Total de Números en PostgreSQL

Ejecuta este script Python:
```python
import psycopg2

conn = psycopg2.connect(
    host="crossover.proxy.rlwy.net",
    database="railway",
    user="postgres",
    password="QOHmELJXXFPmWBlyFmgtjLMvZfeoFaJa",
    port=43307
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM claro_numbers")
total = cursor.fetchone()[0]
print(f"Total números en PostgreSQL: {total}")

cursor.close()
conn.close()
```

### Ver Últimas Activaciones

```python
cursor.execute("SELECT numero_telefono, fecha_activacion FROM claro_numbers ORDER BY fecha_activacion DESC LIMIT 10")
for numero, fecha in cursor.fetchall():
    print(f"{numero} - {fecha}")
```

---

## ✅ RESUMEN DE CAMBIOS v2.6.0

```
✅ Auto-actualización desde GitHub
✅ Integración con PostgreSQL (backup en la nube)
✅ Exportación de base de datos (PostgreSQL → archivo local)
✅ Limpieza de duplicados mejorada
✅ Instalación automática de psycopg2-binary
✅ Nuevos comandos CLI: --export-db, --clean-duplicates, --update, --no-update-check
✅ Logs mejorados para guardado en base de datos
✅ Manejo robusto de errores (si falla DB, continúa con archivo local)
```

---

## 🎯 PRÓXIMOS PASOS RECOMENDADOS

1. **Configurar tu repositorio GitHub** para auto-actualizaciones
2. **Ejecutar modo activación masiva** si es la primera vez: `--activacion-masiva`
3. **Dejar en modo normal** para rotaciones continuas
4. **Limpiar duplicados semanalmente**: `--clean-duplicates`
5. **Exportar base de datos mensualmente** para backup: `--export-db`

---

**¿Preguntas? ¿Problemas?**  
Revisa el `CHANGELOG_v2.6.0.md` para más detalles técnicos.

**Versión:** 2.6.0  
**Fecha:** 2026-01-12

