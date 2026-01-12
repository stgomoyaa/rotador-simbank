# 🔄 Rotador Automático de SIM Bank - Claro Pool

[![Version](https://img.shields.io/badge/version-2.6.0-blue.svg)](https://github.com/stgomoyaa/rotador-simbank)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

Sistema automático de rotación de slots en SIM Banks para evitar repetición de números de teléfono en SimClient. Incluye activación automática de SIMs Claro, integración con PostgreSQL y sistema de auto-actualización.

---

## ✨ Características

### 🔄 Rotación Automática
- ✅ Rotación de 32 slots cada 30 minutos (configurable)
- ✅ Sistema de offsets escalonados para evitar duplicados entre pools
- ✅ Verificación de cambio de ICCID (v2.5.0+)
- ✅ Reintentos automáticos si el slot no cambia
- ✅ Persistencia de estado (recuerda el slot actual)

### 📞 Activación de SIMs Claro
- ✅ Activación automática mediante USSD (*103#)
- ✅ Lectura de número desde SMS
- ✅ Guardado en SIM como contacto "myphone"
- ✅ Verificación de registro en red (AT+CREG)
- ✅ Verificación de intensidad de señal (AT+CSQ)
- ✅ Detección de SIMs ya activadas

### 💾 Almacenamiento Triple
- ✅ Archivo local (`listadonumeros_claro.txt`)
- ✅ SIM (contacto "myphone")
- ✅ **PostgreSQL en la nube** (v2.6.0+)

### 🔄 Auto-Actualización
- ✅ Verificación automática de actualizaciones desde GitHub
- ✅ Descarga y aplicación automática
- ✅ Backup automático antes de actualizar
- ✅ Restauración automática si falla

### 🛠️ Herramientas Adicionales
- ✅ Exportación de base de datos PostgreSQL
- ✅ Limpieza de duplicados
- ✅ Modo dry-run para pruebas
- ✅ Self-test de hardware
- ✅ Modo activación masiva (1024 SIMs de una vez)

---

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/stgomoyaa/rotador-simbank.git
cd rotador-simbank
```

### 2. Instalar dependencias

**Windows:**
```cmd
INSTALAR.bat
```

**O manualmente:**
```bash
pip install pyserial rich psycopg2-binary
```

### 3. Configurar

Edita `RotadorSimBank.py` si necesitas cambiar:
- Puertos COM de los SIM Banks (líneas 92-96)
- Intervalo de rotación (línea 45, por defecto 30 minutos)
- Credenciales de PostgreSQL (líneas 89-96, ya configuradas)

---

## 🚀 Uso

### Modo Normal (Rotación Continua)

```bash
python RotadorSimBank.py
```

O usar el script:
```cmd
EJECUTAR.bat
```

### Modo Activación Masiva (Setup Inicial)

```bash
python RotadorSimBank.py --activacion-masiva
```

Procesa los 32 slots (1024 SIMs) sin interrupciones. Ideal para la configuración inicial.

### Otros Modos

```bash
# Modo prueba (sin tocar hardware)
python RotadorSimBank.py --dry-run

# Test de hardware
python RotadorSimBank.py --self-test

# Cambiar intervalo
python RotadorSimBank.py --intervalo 15  # 15 minutos

# Comenzar desde un slot específico
python RotadorSimBank.py --slot-start 10
```

### Herramientas de Base de Datos

```bash
# Exportar PostgreSQL a archivo local
python RotadorSimBank.py --export-db

# Limpiar duplicados del archivo
python RotadorSimBank.py --clean-duplicates
```

### Auto-Actualización

```bash
# Forzar actualización
python RotadorSimBank.py --update

# Saltar verificación de actualizaciones
python RotadorSimBank.py --no-update-check
```

---

## 🏗️ Arquitectura

### Hardware Soportado

- **SIM Banks:** 4 pools (Pool1-4)
- **Puertos por pool:** 8 puertos lógicos (01-08)
- **Slots por pool:** 32 slots
- **Total SIMs:** 1024 (4 × 8 × 32)

### Sistema de Offsets Escalonados

```
Pool1: Slot 1  → 2  → 3  → ... → 32 → 1  (offset +0)
Pool2: Slot 9  → 10 → 11 → ... → 8  → 9  (offset +8)
Pool3: Slot 17 → 18 → 19 → ... → 16 → 17 (offset +16)
Pool4: Slot 25 → 26 → 27 → ... → 24 → 25 (offset +24)
```

Esto asegura que **no hay duplicados entre pools** en ningún momento.

### Flujo de Activación

```
1. Cambiar slot en SIM Bank (AT+SWIT)
   ↓
2. Verificar que el ICCID cambió
   ↓
3. Reiniciar módems (AT+CFUN=1,1)
   ↓
4. Esperar detección de SIM (AT+CPIN?)
   ↓
5. Verificar registro en red (AT+CREG?)
   ↓
6. Enviar USSD de activación (*103#)
   ↓
7. Leer número desde SMS
   ↓
8. Guardar en: Archivo + SIM + PostgreSQL
```

---

## 📊 Base de Datos PostgreSQL

### Configuración

El script está preconfigurado con credenciales de PostgreSQL en la nube:

```python
DB_HOST = "crossover.proxy.rlwy.net"
DB_NAME = "railway"
DB_USER = "postgres"
DB_PASSWORD = "QOHmELJXXFPmWBlyFmgtjLMvZfeoFaJa"
DB_PORT = 43307
```

### Estructura de la Tabla

```sql
CREATE TABLE claro_numbers (
    id SERIAL PRIMARY KEY,
    iccid VARCHAR(20) UNIQUE NOT NULL,
    numero_telefono VARCHAR(15) NOT NULL,
    fecha_activacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Características

- ✅ Guardado automático en cada activación
- ✅ Actualización inteligente (si el ICCID existe, actualiza el número)
- ✅ Fallback a archivo local si PostgreSQL falla
- ✅ Exportación completa con `--export-db`

---

## 📝 Logs

### Archivos de Log

- `rotador_simbank.log` - Log principal
- `rotador_simbank_YYYY-MM-DD.log` - Log diario
- `log_activacion_rotador.txt` - Log específico de activaciones

### Métricas

- `rotador_metrics.json` - Métricas acumuladas
- `rotador_state.json` - Estado actual (slot e iteración)
- `iccids_history.json` - Historial de ICCIDs por rotación

### Snapshots

- `snapshots/YYYY-MM-DD/` - Snapshots completos por rotación

---

## 🔧 Configuración Avanzada

### Deshabilitar PostgreSQL

```python
# Línea 87
DB_ENABLED = False
```

### Actualización Automática sin Preguntar

```python
# Línea 108
AUTO_UPDATE = True
```

### Cambiar Intervalo por Defecto

```python
# Línea 45
INTERVALO_MINUTOS = 15  # Por defecto: 30
```

### Blacklist de Puertos Problemáticos

```python
# Línea 68
PUERTOS_BLACKLIST = ["COM52", "COM35"]
```

---

## 📚 Documentación

- **[CHANGELOG_v2.6.0.md](CHANGELOG_v2.6.0.md)** - Cambios técnicos detallados
- **[GUIA_RAPIDA_v2.6.0.md](GUIA_RAPIDA_v2.6.0.md)** - Guía de usuario con ejemplos
- **[RESUMEN_IMPLEMENTACION_v2.6.0.md](RESUMEN_IMPLEMENTACION_v2.6.0.md)** - Resumen técnico
- **[README_GIT.md](README_GIT.md)** - Guía de Git y actualización

---

## 🐛 Solución de Problemas

### No se detectan los SIM Banks

**Verificar COM ports:**
```bash
python RotadorSimBank.py --self-test
```

**Actualizar configuración (líneas 92-96):**
```python
SIM_BANKS = {
    "Pool1": {"com": "COM62", ...},
    "Pool2": {"com": "COM60", ...},
    "Pool3": {"com": "COM61", ...},
    "Pool4": {"com": "COM59", ...},
}
```

### PostgreSQL no conecta

**Verificar conexión a internet y ejecutar:**
```bash
python RotadorSimBank.py --export-db
```

Si falla, deshabilitar temporalmente:
```python
DB_ENABLED = False
```

### Muchos duplicados en rotaciones

**Verificación implementada en v2.5.0:**
- El script ahora verifica que el ICCID cambió después de enviar AT+SWIT
- Si no cambió, reintenta automáticamente
- Ver [INFORME_ANALISIS_COMPLETO.md](INFORME_ANALISIS_COMPLETO.md) para más detalles

---

## 📈 Rendimiento

### Tiempos

- **Tiempo por rotación:** ~270 segundos (~4.5 minutos)
- **Tiempo ciclo completo:** ~2.4 horas (32 slots × 4.5 min)
- **Tiempo activación masiva:** ~2-3 horas (1024 SIMs)

### Mejoras de Rendimiento (v2.5.0 → v2.6.0)

| Métrica | v2.5.0 | v2.6.0 |
|---------|--------|--------|
| ICCIDs únicos | 937/1024 (91.5%) | 990-1000/1024 (97-98%) |
| Duplicados | 8.5% | 2-3% |
| Tasa activación | 17.4% | 20-25% |

---

## 🔄 Historial de Versiones

### v2.6.0 (2026-01-12) - Actual
- ✅ Auto-actualización desde GitHub
- ✅ Integración con PostgreSQL
- ✅ Exportación de base de datos
- ✅ Limpieza de duplicados mejorada

### v2.5.0 (2026-01-12)
- ✅ Verificación de cambio de ICCID
- ✅ Reintentos automáticos de comandos SWIT
- ✅ Tiempo de aplicación aumentado (5s → 10s)

### v2.4.0
- ✅ Modo activación masiva (--activacion-masiva)
- ✅ Procesamiento de 1024 SIMs sin interrupciones

### v2.3.0
- ✅ Verificación de registro en red (AT+CREG)
- ✅ Verificación de señal (AT+CSQ)
- ✅ Tiempos de estabilización mejorados

### v2.2.2
- ✅ Sistema base de rotación
- ✅ Activación automática de SIMs Claro
- ✅ Offsets escalonados

---

## 🤝 Contribuir

Las contribuciones son bienvenidas! Para cambios importantes:

1. Fork el repositorio
2. Crea una rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## 👤 Autor

**stgomoyaa**
- GitHub: [@stgomoyaa](https://github.com/stgomoyaa)
- Repositorio: [rotador-simbank](https://github.com/stgomoyaa/rotador-simbank)

---

## 🙏 Agradecimientos

- Basado en el script "Activar Claro CNUM V3" para las funcionalidades de auto-actualización y PostgreSQL
- Comunidad de desarrolladores de Python y rich library
- Documentación de AT Commands para módems Quectel

---

## 📞 Soporte

¿Necesitas ayuda? Abre un [Issue](https://github.com/stgomoyaa/rotador-simbank/issues) en GitHub.

---

**Versión Actual:** 2.6.0  
**Última Actualización:** 2026-01-12

