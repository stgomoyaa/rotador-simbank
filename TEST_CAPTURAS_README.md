# 🧪 Script de Test - Capturas de Slots

## 📋 Descripción

Este script de prueba captura pantallas de HeroSMS para cada uno de los 32 slots, permitiendo verificar visualmente el estado de todos los módems.

## 🎯 ¿Qué hace?

Para cada slot (1-32), el script:

1. ✅ **Cierra HeroSMS** - Termina el proceso completamente
2. ✅ **Rota al slot** - Envía comandos AT+SWIT a todos los pools
3. ✅ **Abre HeroSMS** - Inicia HeroSMS-Partners
4. ✅ **Espera 2 minutos** - Tiempo para detectar módems
5. ✅ **Captura pantalla** - Guarda imagen en carpeta
6. ✅ **Cierra HeroSMS** - Prepara para siguiente slot
7. ✅ **Repite** - Hasta completar los 32 slots

## 🚀 Cómo Usar

### Opción 1: Archivo Batch (Recomendado)

```
Doble clic en: EJECUTAR_TEST_CAPTURAS.bat
```

### Opción 2: Línea de Comandos

```bash
python test_capturas_slots.py
```

## ⏱️ Tiempo Estimado

- **Por slot:** ~3 minutos (cierre + rotación + apertura + espera + captura)
- **Total:** ~96 minutos (1.6 horas) para los 32 slots

## 📂 Estructura de Capturas

Las capturas se guardan en:

```
capturas_test_slots_YYYY-MM-DD_HH-MM-SS/
├── slot_01.png
├── slot_02.png
├── slot_03.png
...
└── slot_32.png
```

## 📊 Salida del Script

Durante la ejecución verás:

```
================================================================================
🔄 PROCESANDO SLOT 01/32 (3.1%)
================================================================================
1️⃣ Cerrando HeroSMS...
  🛑 Cerrando HeroSMS-Partners...
  ✅ HeroSMS-Partners cerrado completamente

2️⃣ Rotando todos los pools al slot 01...
  📡 Pool1: Cambiando a slot 01 (COM: COM38)
  ✅ Pool1: Slot 01 aplicado
  📡 Pool2: Cambiando a slot 09 (COM: COM37)
  ✅ Pool2: Slot 09 aplicado
  📡 Pool3: Cambiando a slot 17 (COM: COM36)
  ✅ Pool3: Slot 17 aplicado
  📡 Pool4: Cambiando a slot 25 (COM: COM35)
  ✅ Pool4: Slot 25 aplicado
  ⏳ Esperando 10 segundos para aplicar cambios...

3️⃣ Abriendo HeroSMS...
  🟢 Abriendo HeroSMS-Partners...
  ✅ HeroSMS-Partners iniciado
  ✅ HeroSMS-Partners confirmado en ejecución (tras 1s)

4️⃣ Esperando 2 minutos para detección de módems...
  ⏳ 120s restantes...
  ⏳ 105s restantes...
  ⏳ 90s restantes...
  ...

5️⃣ Capturando pantalla...
  📸 Captura guardada: slot_01.png

6️⃣ Cerrando HeroSMS...
  🛑 Cerrando HeroSMS-Partners...
  ✅ HeroSMS-Partners cerrado completamente

✅ Slot 01 completado!
```

## 🛑 Cómo Detener

Para detener el test en cualquier momento:

1. **Presiona `Ctrl+C`**
2. El script cerrará HeroSMS limpiamente
3. Las capturas hasta ese momento estarán guardadas

## 📋 Requisitos

- ✅ HeroSMS-Partners instalado
- ✅ SIM Banks conectados y configurados
- ✅ Python con dependencias instaladas (`mss` o `PIL`)

## 🔧 Instalación de Dependencias

Si no tienes `mss` instalado:

```bash
pip install mss
```

O alternativamente usa `PIL` (ya incluido en el instalador):

```bash
pip install Pillow
```

## ⚙️ Configuración

Puedes modificar estas variables en `test_capturas_slots.py`:

```python
TOTAL_SLOTS = 32                    # Total de slots a procesar
TIEMPO_ESPERA_MINUTOS = 2           # Tiempo de espera por slot
CARPETA_CAPTURAS = "capturas_test_slots"  # Carpeta base
```

## 💡 Casos de Uso

### 1. Verificación Visual de Todos los Slots
```bash
python test_capturas_slots.py
```
Útil para verificar que todos los slots tienen módems funcionando

### 2. Documentación del Sistema
Las capturas sirven como documentación visual del estado del sistema

### 3. Debugging de Problemas
Si un slot tiene problemas, la captura muestra exactamente qué ve HeroSMS

### 4. Verificación Post-Configuración
Después de configurar nuevos pools, verifica que todo funciona

## 🐛 Resolución de Problemas

### Problema: "No se pudo importar funciones de RotadorSimBank.py"
**Solución:** Asegúrate de que ambos archivos estén en la misma carpeta

### Problema: "Error al capturar pantalla"
**Solución:** Instala `mss`:
```bash
pip install mss
```

### Problema: "No se detectaron SIM Banks"
**Solución:** 
1. Ejecuta primero: `python RotadorSimBank.py --detectar-simbanks`
2. Verifica que HeroSMS-Partners tenga los simbanks configurados

### Problema: HeroSMS no se abre
**Solución:** Verifica que el acceso directo exista en el escritorio:
```
C:\Users\[TU_USUARIO]\Desktop\HeroSMS-Partners.lnk
```

## 📊 Análisis de Resultados

Después del test, revisa las capturas para:

- ✅ **Verificar módems detectados** - Deben aparecer en HeroSMS
- ✅ **Identificar slots problemáticos** - Capturas sin módems o con errores
- ✅ **Confirmar offset correcto** - Cada pool debe tener slots diferentes
- ✅ **Documentar estado** - Guardar evidencia visual del sistema

## 📈 Ejemplo de Análisis

```
slot_01.png  ✅ 32 módems detectados
slot_02.png  ✅ 32 módems detectados
slot_03.png  ⚠️  28 módems detectados (4 módems sin señal)
slot_04.png  ✅ 32 módems detectados
...
slot_32.png  ✅ 32 módems detectados
```

## 🔄 Diferencias con Modo Normal

| Característica | Modo Normal | Test Capturas |
|---|---|---|
| **Objetivo** | Activar SIMs | Capturar pantallas |
| **Duración** | 2-3 horas | 1.6 horas |
| **Activación** | Sí | No |
| **Capturas** | No | Sí (32 capturas) |
| **Loop** | Opcional | No (una sola pasada) |
| **Apertura HeroSMS** | Al final | Cada slot |

## 💾 Espacio en Disco

- **Por captura:** ~1-3 MB (depende de resolución)
- **Total:** ~32-96 MB para las 32 capturas

## 🎯 Recomendaciones

1. ✅ **Ejecuta este test** después de configurar nuevos pools
2. ✅ **Guarda las capturas** como documentación del sistema
3. ✅ **Ejecuta periódicamente** para verificar estado de módems
4. ✅ **Compara capturas** de diferentes fechas para detectar degradación

## 📝 Notas

- El script usa el **offset de slots** configurado en cada pool
- Las capturas muestran **HeroSMS tal como se ve en pantalla**
- El script **no activa SIMs**, solo captura el estado
- Puedes **detener y reanudar** en cualquier momento

---

**Versión:** 1.0.0  
**Fecha:** 28 Enero 2026  
**Compatibilidad:** RotadorSimBank v2.11.0+
