# 🔄 Rotador Automático de SIM Bank v2.6.0

Sistema de rotación automática de slots en SIM Banks con activación de SIMs Claro.

## 📦 Instalación Rápida

1. **Instalar dependencias:**
   ```bash
   pip install pyserial rich psycopg2-binary
   ```
   O ejecutar: `INSTALAR.bat`

2. **Ejecutar:**
   ```bash
   python RotadorSimBank.py
   ```
   O ejecutar: `EJECUTAR.bat`

## 🚀 Comandos Principales

```bash
# Modo normal (rotación cada 30 minutos)
python RotadorSimBank.py

# Activación masiva (1024 SIMs de una vez)
python RotadorSimBank.py --activacion-masiva

# Modo prueba
python RotadorSimBank.py --dry-run

# Exportar base de datos PostgreSQL
python RotadorSimBank.py --export-db

# Limpiar duplicados
python RotadorSimBank.py --clean-duplicates

# Actualizar desde GitHub
python RotadorSimBank.py --update
```

## ⚙️ Configuración

Edita `RotadorSimBank.py` si necesitas cambiar:
- **Puertos COM** de SIM Banks (líneas 92-96)
- **Intervalo** de rotación (línea 45, default: 30 min)
- **PostgreSQL** (líneas 89-96, ya configurado)

## 🏗️ Arquitectura

- **4 Pools** de SIM Banks
- **8 Puertos** por pool
- **32 Slots** por pool
- **Total: 1024 SIMs**

Offsets escalonados (+0, +8, +16, +24) para evitar duplicados entre pools.

## 📊 Características v2.6.0

- ✅ Rotación automática con verificación de ICCID
- ✅ Activación automática de SIMs Claro
- ✅ Guardado triple: Archivo + SIM + PostgreSQL
- ✅ Auto-actualización desde GitHub
- ✅ Exportación de base de datos
- ✅ Limpieza de duplicados

## 📝 Archivos Generados

- `listadonumeros_claro.txt` - Números activados
- `rotador_simbank.log` - Log principal
- `rotador_state.json` - Estado actual

## 🔧 Solución Rápida de Problemas

**No detecta SIM Banks:**
```bash
python RotadorSimBank.py --self-test
```

**PostgreSQL no conecta:**
```python
# Línea 87: Deshabilitar temporalmente
DB_ENABLED = False
```

---

**Repositorio:** https://github.com/stgomoyaa/rotador-simbank  
**Versión:** 2.6.0
