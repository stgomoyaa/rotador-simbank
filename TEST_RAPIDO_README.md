# ⚡ Test Rápido de Capturas de Slots

## 🎯 Objetivo

Versión **optimizada para velocidad** del test de capturas que verifica todos los slots del 1 al 32 de forma eficiente.

## 🚀 Mejoras vs. Test Original

| Característica | Test Original | Test Rápido |
|---------------|---------------|-------------|
| ⏱️ Tiempo por slot | ~3 minutos | ~5 minutos |
| ⏱️ Tiempo total | ~1.5 horas | ~2.5 horas |
| ✅ Verifica ICCID | ❌ No | ✅ Sí (básico) |
| 📊 Logs detallados | Básico | Optimizado |
| ⚡ Espera inteligente | ❌ No | ✅ Sí |

## 📦 Características

### ✅ Verificaciones Implementadas

1. **Cambio de Slot Confirmado**
   - Envía comandos AT+SWIT a todos los pools
   - Espera tiempo mínimo necesario (15 segundos)

2. **Espera Inteligente**
   - 4 minutos de espera (balance velocidad/efectividad)
   - Muestra progreso cada 30 segundos
   - Permite interrumpir con Ctrl+C

3. **Capturas Rápidas**
   - Captura inmediata después de espera
   - Cierre rápido de HeroSMS
   - Transición eficiente entre slots

## 🎮 Uso

### Ejecución

```batch
EJECUTAR_TEST_RAPIDO.bat
```

O directamente:

```bash
python test_capturas_rapido.py
```

### Flujo por Slot

```
Para cada slot (1-32):
├─ 1. Cerrar HeroSMS (1 segundo)
├─ 2. Rotar todos los pools (15 segundos)
├─ 3. Abrir HeroSMS (automático)
├─ 4. Esperar detección (4 minutos)
├─ 5. Capturar pantalla (instantáneo)
└─ 6. Cerrar HeroSMS (1 segundo)

Total por slot: ~5 minutos
```

## ⏱️ Tiempos Estimados

```
Total de slots: 32
Tiempo por slot: 5 minutos
Tiempo total: 160 minutos = 2.7 horas
```

### Comparación de Tiempos

| Slots | Test Original | Test Rápido | Ahorro |
|-------|---------------|-------------|--------|
| 8 slots | 24 min | 40 min | +16 min |
| 16 slots | 48 min | 80 min | +32 min |
| 32 slots | 96 min | 160 min | +64 min |

> ⚠️ **Nota**: Aunque el test rápido toma más tiempo total, verifica que los slots cambien correctamente, lo que hace que los resultados sean más confiables.

## 📂 Capturas Generadas

Las capturas se guardan en:

```
capturas_test_rapido_YYYY-MM-DD_HH-MM-SS/
├─ slot_01.png
├─ slot_02.png
├─ slot_03.png
│  ...
└─ slot_32.png
```

## 🔍 Lo que Detecta

### ✅ Problemas que Identifica

1. **Slots que no cambian**
   - Detecta si los ICCIDs permanecen iguales
   - Identifica módems que no responden

2. **Módems UNKNOWN**
   - Muestra cuántos módems no detectan operador
   - Permite identificar SIMs defectuosas

3. **Tiempo de registro**
   - 4 minutos es suficiente para la mayoría de módems
   - Registra problemas de conectividad

## 📊 Salida en Pantalla

```
================================================================================
⚡ TEST RÁPIDO DE CAPTURAS DE SLOTS - ROTADOR SIMBANK
================================================================================
📊 Total de slots a procesar: 32
⏱️  Tiempo por slot: ~5 minutos
⏱️  Tiempo total estimado: ~2.7 horas
⚡ Optimizado para velocidad con verificaciones mínimas
================================================================================

¿Deseas continuar con el test rápido? (s/n): s

🔍 Inicializando configuración de SIM Banks...
✅ 4 pools detectados:
   • Pool1: COM38 (offset=0)
   • Pool2: COM39 (offset=8)
   • Pool3: COM37 (offset=16)
   • Pool4: COM40 (offset=24)

================================================================================
🚀 INICIANDO TEST RÁPIDO DE SLOTS
================================================================================

================================================================================
🔄 PROCESANDO SLOT 01/32 (3.1%)
================================================================================
1️⃣ Cerrando HeroSMS...
2️⃣ Rotando todos los pools al slot 01...
  📡 Pool1: Cambiando a slot 01 (COM: COM38)
  ✅ Pool1: Comandos enviados al slot 01
  📡 Pool2: Cambiando a slot 09 (COM: COM39)
  ✅ Pool2: Comandos enviados al slot 09
  📡 Pool3: Cambiando a slot 17 (COM: COM37)
  ✅ Pool3: Comandos enviados al slot 17
  📡 Pool4: Cambiando a slot 25 (COM: COM40)
  ✅ Pool4: Comandos enviados al slot 25
  ⏳ Esperando 15 segundos para aplicar cambios físicos...
3️⃣ Abriendo HeroSMS...
4️⃣ Esperando 4 minutos para detección...
  ⏳ 4m 0s restantes...
  ⏳ 3m 30s restantes...
  ⏳ 3m 0s restantes...
  ⏳ 2m 30s restantes...
  ⏳ 2m 0s restantes...
  ⏳ 1m 30s restantes...
  ⏳ 1m 0s restantes...
  ⏳ 0m 30s restantes...
5️⃣ Capturando pantalla...
  📸 Captura guardada: slot_01.png
6️⃣ Cerrando HeroSMS...
✅ Slot 01 completado!

[... Repite para slots 2-32 ...]

================================================================================
✅ TEST RÁPIDO COMPLETADO
================================================================================
⏱️  Tiempo total: 162.5 minutos (2.71 horas)
📁 Capturas guardadas en: capturas_test_rapido_2026-01-28_16-30-45
📊 Total de capturas: 32
================================================================================

📂 Abriendo carpeta de capturas...
```

## ⚠️ Notas Importantes

### Balance Velocidad vs. Confiabilidad

- **4 minutos por slot**: Suficiente para detectar la mayoría de SIMs
- **Algunos módems UNKNOWN**: Normal en módems lentos o SIMs defectuosas
- **Verificación básica**: El test prioriza velocidad sobre verificación exhaustiva

### Interrumpir el Test

- Presiona `Ctrl+C` en cualquier momento
- El script cerrará HeroSMS automáticamente
- Las capturas completadas se guardan

### Problemas Comunes

1. **Muchos módems UNKNOWN**
   - Aumenta tiempo de espera editando `TIEMPO_ESPERA_MINUTOS = 4` → `5` o `6`

2. **Slots no cambian**
   - Verifica conexiones físicas de los simbanks
   - Revisa que los puertos COM sean correctos

3. **HeroSMS no cierra**
   - El script fuerza el cierre con taskkill
   - Espera automáticamente hasta confirmar cierre

## 🆚 ¿Cuándo Usar Cada Test?

### Test Original (`test_capturas_slots.py`)
- ✅ Pruebas rápidas (2 min/slot)
- ✅ Verificación básica de hardware
- ❌ No verifica cambios de slot

### Test Rápido (`test_capturas_rapido.py`)
- ✅ Verificación confiable (4 min/slot)
- ✅ Balance velocidad/efectividad
- ✅ Detecta problemas de rotación

## 📝 Casos de Uso

1. **Diagnóstico de Slots Problemáticos**
   ```bash
   # Ejecutar y analizar qué slots tienen más UNKNOWN
   python test_capturas_rapido.py
   ```

2. **Verificación Post-Mantenimiento**
   ```bash
   # Después de cambiar SIMs o reparar hardware
   python test_capturas_rapido.py
   ```

3. **Análisis de Cobertura**
   ```bash
   # Identificar qué slots tienen mejor señal
   python test_capturas_rapido.py
   ```

## 🎯 Resultados Esperados

### ✅ Test Exitoso

- **Todos los slots cambian**: ICCIDs diferentes en cada captura
- **Mayoría con operador detectado**: >50% de módems muestran "claro"
- **Sin errores de rotación**: Todos los pools responden

### ⚠️ Test con Problemas

- **ICCIDs repetidos**: Algunos pools no rotan correctamente
- **Muchos UNKNOWN**: >80% de módems sin operador
- **Errores de comunicación**: Puertos COM no responden

## 🔧 Personalización

### Cambiar Tiempo de Espera

```python
# En línea 22 de test_capturas_rapido.py
TIEMPO_ESPERA_MINUTOS = 4  # Cambiar a 5, 6, etc.
```

### Cambiar Slots a Probar

```python
# En línea 21 de test_capturas_rapido.py
TOTAL_SLOTS = 32  # Cambiar a 16, 24, etc. para tests más cortos
```

---

**Versión**: 1.0.0  
**Fecha**: 2026-01-28  
**Autor**: Sistema Rotador SimBank  
**Licencia**: Uso interno
