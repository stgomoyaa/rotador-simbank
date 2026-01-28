# 🔄 Modo Mantenimiento Continuo - Rotador SimBank v2.11.0

## 📊 Resumen de Análisis de Logs

### ✅ Estado de los Rotadores

#### **Rotador 1:** ✅ FUNCIONA CORRECTAMENTE
- HeroSMS se abrió exitosamente: `[2026-01-28 01:53:04] ✅ HeroSMS-Partners iniciado`
- Las mejoras de taskkill funcionaron perfectamente

#### **Rotador 3 y 4:** ✅ FUNCIONAN CORRECTAMENTE
- Ambos abrieron HeroSMS correctamente
- **Problema "rojo":** El programa terminó su ejecución después de completar los 32 slots
- **Solución:** Ahora hay modo mantenimiento continuo (loop infinito)

#### **Números Duplicados en Rotador 3:**
Se detectaron **múltiples números duplicados** con diferentes ICCIDs:
- `56950414382` aparece 7 veces (diferentes ICCIDs)
- `56950421722` aparece 5 veces
- `56979372115` aparece 4 veces

**Causa:** Problema de activación de SIMs o respuesta de la operadora Claro
**Impacto:** Las SIMs físicas son diferentes, pero reportan el mismo número

---

## 🚀 Nueva Funcionalidad: Modo Mantenimiento Continuo

### ¿Qué hace?

El **Modo Mantenimiento Continuo** es un nuevo modo de operación que mantiene el sistema funcionando 24/7:

1. ✅ **Loop infinito** - El script nunca se detiene
2. ✅ **Activación masiva cada 24 horas** - Procesa las 1024 SIMs automáticamente
3. ✅ **Reinicio HeroSMS cada 1 hora** - Mantiene HeroSMS fresco y sin problemas
4. ✅ **Monitoreo continuo** - Chequea el estado cada 5 minutos

### Ventajas

- ✅ **Cero intervención manual** - Se ejecuta indefinidamente
- ✅ **HeroSMS siempre fresco** - Reinicio cada hora previene cuelgues
- ✅ **Activación automática** - Todas las SIMs se activan cada día
- ✅ **No más "rojito"** - El programa nunca termina, siempre está activo

---

## 🎯 Cómo Usar

### Opción 1: Archivo Batch (Recomendado)

**Doble clic en:**
```
EJECUTAR_MODO_MANTENIMIENTO.bat
```

### Opción 2: Línea de Comandos

```bash
python RotadorSimBank.py --modo-mantenimiento
```

---

## ⚙️ Configuración del Modo

### Intervalos de Tiempo

```python
INTERVALO_ACTIVACION_MASIVA = 24 horas    # Activación completa cada día
INTERVALO_REINICIO_HEROSMS = 1 hora       # Reinicio HeroSMS cada hora
CHEQUEO_ESTADO = 5 minutos                # Verifica estado cada 5 min
```

### Flujo de Trabajo

```
┌─────────────────────────────────────────────────┐
│  1. Ejecutar activación masiva (32 slots)      │
│     ↓ (2-3 horas)                               │
│  2. Esperar hasta completar ciclo              │
│     ↓                                           │
│  3. Cada 1 hora:                                │
│     - Cerrar HeroSMS                            │
│     - Cerrar puertos seriales                   │
│     - Abrir HeroSMS                             │
│     ↓                                           │
│  4. Cada 24 horas:                              │
│     - Ejecutar nueva activación masiva          │
│     - Reiniciar contador de HeroSMS             │
│     ↓                                           │
│  5. Cada 5 minutos:                             │
│     - Mostrar estado del sistema                │
│     - Verificar tiempos                         │
│     ↓                                           │
│  6. Volver al paso 3 (loop infinito)           │
└─────────────────────────────────────────────────┘
```

---

## 📋 Información del Estado

Durante la ejecución, verás:

```
────────────────────────────────────────────────────────────────────────────────
📊 ESTADO DEL SISTEMA - Iteración #5
────────────────────────────────────────────────────────────────────────────────
⏱️  Tiempo desde última activación masiva: 12.5h
⏱️  Próxima activación masiva en: 11.5h
⏱️  Tiempo desde último reinicio HeroSMS: 45.0min
⏱️  Próximo reinicio HeroSMS en: 15.0min
────────────────────────────────────────────────────────────────────────────────

💤 Esperando 5 minutos para próxima verificación...
   (Presiona Ctrl+C para detener)
```

---

## 🛑 Cómo Detener

Para detener el modo mantenimiento:

1. **Presiona `Ctrl+C` en la ventana**
2. El script se detendrá de forma segura
3. Se guardarán todos los logs

---

## 📂 Archivos Generados

El modo mantenimiento genera los siguientes archivos:

```
rotador_simbank.log              - Log principal con timestamps
rotador_simbank_YYYY-MM-DD.log  - Log diario
log_activacion_rotador.txt      - Log específico de activaciones
rotador_metrics.json            - Métricas acumuladas
rotador_state.json              - Estado del sistema
iccids_history.json             - Historial de ICCIDs
listadonumeros_claro.txt        - Números activados
snapshots/                      - Snapshots por fecha
```

---

## 🆚 Comparación de Modos

| Característica | Modo Masivo (Default) | Modo Continuo | Modo Mantenimiento |
|---|---|---|---|
| **Ejecución** | Una vez y termina | Loop infinito | Loop infinito |
| **Activación** | 32 slots (1 vez) | Slot por slot | 32 slots cada 24h |
| **Reinicio HeroSMS** | Al inicio y al final | Cada rotación | Cada 1 hora |
| **Intervalo** | N/A | 30 minutos | 24 horas |
| **Mejor para** | Activación inicial | Testing | Producción 24/7 |

---

## 🔧 Comandos Disponibles

```bash
# Modo mantenimiento (nuevo)
python RotadorSimBank.py --modo-mantenimiento

# Modo masivo (default)
python RotadorSimBank.py

# Modo continuo (cada 30 min)
python RotadorSimBank.py --modo-continuo

# Detectar SIM Banks
python RotadorSimBank.py --detectar-simbanks

# Actualizar script
python RotadorSimBank.py --update

# Self test
python RotadorSimBank.py --self-test
```

---

## 🐛 Resolución de Problemas

### Problema: "HeroSMS no se abre"
**Solución:** Las mejoras v2.10.5 y v2.11.0 solucionaron este problema con verificación robusta

### Problema: "Se queda rojo después de terminar"
**Solución:** Usa `--modo-mantenimiento` para loop infinito

### Problema: "Números duplicados"
**Causa:** Problema de activación de SIMs Claro o respuesta de operadora
**Mitigación:** El script detecta y reporta duplicados en los logs

### Problema: "HeroSMS se congela después de varias horas"
**Solución:** El modo mantenimiento reinicia HeroSMS cada 1 hora automáticamente

---

## 📈 Métricas y Monitoreo

El sistema registra automáticamente:

- ✅ Total de rotaciones completadas
- ✅ SIMs verificadas por ciclo
- ✅ ICCIDs únicos detectados
- ✅ Comandos AT exitosos/fallidos
- ✅ Tiempo de ejecución por slot
- ✅ Estado de HeroSMS (abierto/cerrado)
- ✅ Último reinicio de HeroSMS
- ✅ Última activación masiva

---

## 🎉 Changelog v2.11.0

### Nuevo
- ✅ Modo mantenimiento continuo con loop infinito
- ✅ Activación masiva automática cada 24 horas
- ✅ Reinicio automático de HeroSMS cada 1 hora
- ✅ Archivo batch `EJECUTAR_MODO_MANTENIMIENTO.bat`
- ✅ Monitoreo de estado cada 5 minutos

### Mejorado
- ✅ Detección de SIM Banks más robusta (v2.10.4)
- ✅ Taskkill mejorado para prevenir duplicados (v2.10.5)
- ✅ Verificación de cierre completo de HeroSMS
- ✅ Verificación de apertura exitosa de HeroSMS

### Solucionado
- ✅ HeroSMS no se abría en algunos casos
- ✅ Programa terminaba después de completar ciclo
- ✅ HeroSMS se abría dos veces en casos raros
- ✅ Detección de SIM Banks usaba configuración antigua

---

## 📞 Soporte

Para problemas o preguntas:
1. Revisa los logs en `rotador_simbank.log`
2. Verifica que HeroSMS-Partners esté instalado
3. Asegúrate de que los COM ports estén conectados
4. Ejecuta `--detectar-simbanks` para validar configuración

---

## 🚀 Recomendación de Uso

**Para Producción 24/7:**
```bash
EJECUTAR_MODO_MANTENIMIENTO.bat
```

Este comando:
- ✅ Nunca se detiene
- ✅ Mantiene todo funcionando automáticamente
- ✅ Previene problemas de HeroSMS
- ✅ Activa todas las SIMs diariamente

---

**Versión:** 2.11.0  
**Fecha:** 28 Enero 2026  
**Autor:** Sistema de Rotación Automática Claro Pool
