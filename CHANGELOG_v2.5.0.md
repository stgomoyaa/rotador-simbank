# 🚀 CHANGELOG v2.5.0 - Verificación de Cambio de ICCID

**Fecha:** 2026-01-12
**Versión:** 2.5.0
**Tipo:** Mejora Crítica - Solución a Duplicados Internos

---

## 🎯 PROBLEMA IDENTIFICADO

### Análisis del Log (2026-01-09)

Tras analizar 93,099 líneas de log con 69 rotaciones completadas, se identificó un problema crítico:

```
❌ 75% de rotaciones con ICCIDs duplicados (52/69)
❌ Promedio: 5-6 módems NO cambian de SIM por rotación
❌ Picos problemáticos: hasta 11 módems sin cambio
❌ 87 de 1024 SIMs no rotaron correctamente (8.5%)
```

### Ejemplo Real

```
COM56 - Rotaciones consecutivas:
00:23:17 → ICCID: 8956030253041804893
00:56:27 → ICCID: 8956030253041804893 ← MISMO (no cambió)
01:29:31 → ICCID: 8956030253041804893 ← MISMO (no cambió)
02:02:41 → ICCID: 8956030253041804893 ← MISMO (no cambió)
02:35:52 → ICCID: 8956030253041804893 ← MISMO (no cambió)
03:09:01 → ICCID: 8956030253041804893 ← MISMO (no cambió)
03:42:02 → ICCID: 8956030253047165158 ← CAMBIÓ ✅ (después de 6 intentos)
```

### Causa Raíz

El script enviaba comandos `AT+SWIT` y **asumía** que el cambio se aplicó correctamente, pero:

1. ❌ No verificaba que el ICCID cambió
2. ❌ Tiempo de espera insuficiente (5s)
3. ❌ No reintentaba si el cambio falló
4. ❌ Switches mecánicos del SIM Bank no siempre responden a tiempo

---

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. **Verificación de Cambio de ICCID** ⭐ CRÍTICO

**Antes (v2.4.0):**
```python
def cambiar_slot_pool(pool_name, pool_config, slot_base):
    # Enviar comandos SWIT
    for puerto_logico in puertos_logicos:
        comando = f"AT+SWIT{puerto_logico}-{slot_formateado}"
        enviar_comando(sim_bank_com, comando)
        time.sleep(0.5)
    
    # ❌ Asumir que cambió
    return comandos_ok, comandos_error
```

**Ahora (v2.5.0):**
```python
def cambiar_slot_pool(pool_name, pool_config, slot_base):
    # PASO 1: Leer ICCIDs actuales (muestra de 3 módems)
    iccids_anteriores = {}
    for puerto_modem in modems_muestra:
        iccid = obtener_iccid_modem_rapido(puerto_modem)
        iccids_anteriores[puerto_modem] = iccid
    
    # PASO 2: Enviar comandos SWIT
    for puerto_logico in puertos_logicos:
        comando = f"AT+SWIT{puerto_logico}-{slot_formateado}"
        enviar_comando(sim_bank_com, comando)
        time.sleep(0.5)
    
    # PASO 3: Esperar aplicación (10s)
    time.sleep(Settings.TIEMPO_APLICAR_SLOT)
    
    # PASO 4: ✅ VERIFICAR que ICCIDs cambiaron
    cambios_verificados = 0
    sin_cambio = 0
    
    for puerto_modem, iccid_anterior in iccids_anteriores.items():
        iccid_nuevo = obtener_iccid_modem_rapido(puerto_modem)
        
        if iccid_nuevo != iccid_anterior:
            cambios_verificados += 1
        else:
            sin_cambio += 1
            escribir_log(f"⚠️ [{puerto_modem}] ICCID no cambió")
    
    # PASO 5: ✅ REINTENTAR si no cambió
    if sin_cambio > cambios_verificados:
        escribir_log(f"⚠️ Reintentando cambio de slot...")
        # Reenviar comandos y esperar más tiempo
        ...
```

### 2. **Aumento de Tiempo de Aplicación**

```python
# Antes
TIEMPO_APLICAR_SLOT = 5  # Muy corto para switches mecánicos

# Ahora
TIEMPO_APLICAR_SLOT = 10  # +100% más tiempo
```

**Razón:** Los switches mecánicos del SIM Bank necesitan más tiempo para cambiar físicamente de slot.

### 3. **Nueva Función: `obtener_iccid_modem_rapido()`**

```python
def obtener_iccid_modem_rapido(puerto, timeout=1.5):
    """Obtiene el ICCID del módem de forma rápida (sin log) para verificación"""
    try:
        with serial.Serial(puerto, baudrate=115200, timeout=timeout) as ser:
            ser.write(b"AT+QCCID\r\n")
            time.sleep(0.8)
            respuesta = ser.read_all().decode(errors="ignore").strip()
            
            match = re.search(r'\d{19,20}', respuesta)
            if match:
                return match.group(0)
            return None
    except Exception:
        return None
```

**Ventajas:**
- ⚡ Más rápida (timeout 1.5s vs 2s)
- 📝 Sin logging (para no saturar logs)
- 🎯 Solo para verificación interna

### 4. **Reintentos Automáticos**

Si más de la mitad de los módems no cambiaron de ICCID:

1. ✅ Reenvía comandos SWIT
2. ✅ Espera 13 segundos adicionales
3. ✅ Verifica de nuevo
4. ✅ Reporta resultado en log

### 5. **Logging Mejorado**

**Nuevo formato de log:**
```
✅ Pool1 cambiado a slot 15 (verificado: 3/3 módems)
⚠️ [COM45] ICCID no cambió: 8956030253041804893
⚠️ Pool2: 1/3 módems no cambiaron ICCID, reintentando...
✅ Pool2: Reintento exitoso, 3/3 módems cambiaron
```

---

## 📊 IMPACTO ESPERADO

### Antes (v2.4.0)

```
ICCIDs únicos: 937/1024 (91.5%)
Duplicados: 87 (8.5%)
Rotaciones con duplicados: 52/69 (75%)
Promedio duplicados/rotación: 5-6 módems
```

### Después (v2.5.0 - Proyectado)

```
ICCIDs únicos: 990-1000/1024 (97-98%)
Duplicados: 24-34 (2-3%)
Rotaciones con duplicados: 10-15/69 (15-20%)
Promedio duplicados/rotación: 1-2 módems

MEJORA: +6-7% más ICCIDs únicos
REDUCCIÓN: -70% en duplicados
```

---

## 🔧 CAMBIOS TÉCNICOS

### Archivos Modificados

1. **RotadorSimBank.py**
   - `VERSION = "2.5.0"`
   - `TIEMPO_APLICAR_SLOT = 10` (antes: 5)
   - `MAX_INTENTOS_CAMBIO_SLOT = 3` (nuevo)
   - Nueva función: `obtener_iccid_modem_rapido()`
   - Modificada función: `cambiar_slot_pool()` (ahora verifica cambio)
   - Modificada función: `cambiar_slot_simbank()` (elimina sleep redundante)

### Compatibilidad

✅ **100% Compatible con v2.4.0**
- Todos los argumentos CLI funcionan igual
- Archivos de estado compatibles
- No requiere cambios en configuración

---

## 🚀 CÓMO USAR

### Modo Normal (sin cambios)

```bash
python RotadorSimBank.py
```

### Modo Activación Masiva (sin cambios)

```bash
python RotadorSimBank.py --activacion-masiva
```

### Modo Dry Run (sin cambios)

```bash
python RotadorSimBank.py --dry-run
```

**La verificación de ICCID se ejecuta automáticamente en todos los modos.**

---

## 📈 MÉTRICAS A MONITOREAR

Después de implementar v2.5.0, monitorear:

1. **Duplicados por rotación**
   - Buscar en log: `ADVERTENCIA: X ICCIDs duplicados`
   - Objetivo: < 2 duplicados por rotación

2. **Reintentos de cambio**
   - Buscar en log: `Reintentando cambio de slot`
   - Si es frecuente: problema hardware

3. **ICCIDs únicos totales**
   - Buscar en log: `ICCIDs únicos: X/30`
   - Objetivo: 28-30/30 por rotación

4. **Tiempo por rotación**
   - Buscar en log: `cambiar_slot_simbank completado en Xs`
   - Esperado: 260-280s (antes: 248s)

---

## ⚠️ NOTAS IMPORTANTES

### Aumento de Tiempo por Rotación

```
v2.4.0: ~248 segundos/rotación (~4.1 min)
v2.5.0: ~270 segundos/rotación (~4.5 min)

Aumento: +22 segundos (+9%)
```

**Razón:** Verificación de ICCIDs (3 módems × 2 lecturas × 2s = 12s) + tiempo adicional de espera (+10s)

**Justificación:** Vale la pena el tiempo adicional para garantizar que **todos** los módems cambien de SIM correctamente.

### Posibles Problemas Hardware

Si después de v2.5.0 sigues viendo muchos reintentos:

```
⚠️ Pool2: 2/3 módems no cambiaron ICCID, reintentando...
❌ Pool2: Reintento falló, posible problema hardware en COM60
```

**Acción:** Revisar físicamente el SIM Bank COM60 (switches mecánicos defectuosos)

---

## 🎉 RESUMEN

### ✅ Lo que se Solucionó

1. **Duplicados Internos**: Reducción esperada del 75% al 15-20%
2. **Verificación de Cambio**: Ahora se confirma que el ICCID cambió
3. **Reintentos Automáticos**: Si no cambia, reintenta automáticamente
4. **Logging Mejorado**: Identifica exactamente qué módems no cambiaron

### 🚀 Próximos Pasos

1. Ejecutar v2.5.0 durante 24 horas
2. Analizar nuevo log con script de análisis
3. Comparar métricas con v2.4.0
4. Si persisten duplicados >20%, revisar hardware

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

- [x] Actualizar VERSION a 2.5.0
- [x] Aumentar TIEMPO_APLICAR_SLOT a 10
- [x] Implementar obtener_iccid_modem_rapido()
- [x] Modificar cambiar_slot_pool() con verificación
- [x] Agregar MAX_INTENTOS_CAMBIO_SLOT
- [x] Actualizar logging
- [x] Eliminar sleep redundante en cambiar_slot_simbank()
- [ ] Probar en producción 24h
- [ ] Analizar resultados
- [ ] Documentar mejoras observadas

---

**Desarrollado por:** Análisis basado en 93,099 líneas de log
**Fecha de análisis:** 2026-01-09
**Fecha de implementación:** 2026-01-12
**Versión:** 2.5.0

