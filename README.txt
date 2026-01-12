╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        ROTADOR SIMBANK v2.4.0 - Claro Pool (1024 SIMs)         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝


█ ARCHIVOS EN ESTE DIRECTORIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. RotadorSimBank.py             ← Script principal
  2. INSTALAR.bat                  ← Instalar dependencias (ejecutar 1 vez)
  3. EJECUTAR.bat                  ← Menú para ejecutar el rotador
  4. INICIO_RAPIDO.txt             ← Guía completa de uso
  5. listadonumeros_claro.txt      ← Números activados (se crea automático)
  6. rotador_simbank_YYYY-MM-DD.log ← Logs (se crean automáticos)


█ PASOS PARA IMPLEMENTAR (3 pasos, 10 minutos)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌────────────────────────────────────────────────────────────────┐
  │ PASO 1: INSTALAR DEPENDENCIAS (1 vez, 2 minutos)              │
  └────────────────────────────────────────────────────────────────┘

    Doble clic en: INSTALAR.bat

    Esto instalará:
    • pyserial (comunicación con puertos COM)
    • rich (interfaz bonita en consola)


  ┌────────────────────────────────────────────────────────────────┐
  │ PASO 2: CONFIGURAR COM PORTS (1 vez, 5 minutos)               │
  └────────────────────────────────────────────────────────────────┘

    1. Abrir RotadorSimBank.py con editor de texto
    2. Ir a línea 83 (buscar: SIM_BANKS = {)
    3. Cambiar los COM según tu hardware:

       SIM_BANKS = {
           "Pool1": {"com": "COM62", "offset_slot": 0},
           "Pool2": {"com": "COM60", "offset_slot": 8},
           "Pool3": {"com": "COM61", "offset_slot": 16},
           "Pool4": {"com": "COM59", "offset_slot": 24},
       }

    4. Guardar y cerrar


  ┌────────────────────────────────────────────────────────────────┐
  │ PASO 3: EJECUTAR (10 segundos)                                │
  └────────────────────────────────────────────────────────────────┘

    Doble clic en: EJECUTAR.bat

    Selecciona modo:
    • Opción 1: Rotación continua (normal 24/7)
    • Opción 2: Activación masiva (1024 SIMs de una vez)
    • Opción 4: Probar COM ports (recomendado la primera vez)


█ MODOS DE OPERACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌────────────────────────────────────────────────────────────────┐
  │ MODO 1: ROTACIÓN CONTINUA (Normal)                            │
  └────────────────────────────────────────────────────────────────┘

    • Rota cada 30 minutos automáticamente
    • Abre/cierra HeroSMS-Partners en cada rotación
    • Corre 24/7 hasta que lo detengas
    • Ideal para operación diaria
    • ~144-240 números/día


  ┌────────────────────────────────────────────────────────────────┐
  │ MODO 2: ACTIVACIÓN MASIVA (Setup inicial)                     │
  └────────────────────────────────────────────────────────────────┘

    • Procesa los 32 slots sin parar
    • Cierra programa al inicio, abre solo al final
    • Toma 2-3 horas
    • Ideal para:
      - Primera vez (activar todas las SIMs)
      - Refresh mensual
    • ~120-200 números en una sesión


█ COMANDOS RÁPIDOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  # Verificar COM ports
  python RotadorSimBank.py --self-test

  # Modo normal
  python RotadorSimBank.py

  # Activación masiva
  python RotadorSimBank.py --activacion-masiva

  # Prueba sin hardware
  python RotadorSimBank.py --dry-run


█ ARCHIVOS QUE SE CREAN AUTOMÁTICAMENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ listadonumeros_claro.txt       → Todos los números activados
  ✓ log_activacion_rotador.txt     → Log detallado de activaciones
  ✓ rotador_simbank_YYYY-MM-DD.log → Log diario
  ✓ rotador_state.json              → Estado actual (continúa si se reinicia)
  ✓ rotador_metrics.json            → Estadísticas acumuladas
  ✓ iccids_history.json             → Historial de ICCIDs
  ✓ snapshots/                      → Carpeta con snapshots de cada slot


█ PROBLEMAS COMUNES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ❌ "Ya hay una instancia ejecutándose"
     → Borrar archivo: rotador.lock

  ❌ "No se detectan COM de SIM Bank"
     → Verificar configuración (Paso 2)
     → Ejecutar: python RotadorSimBank.py --self-test

  ❌ "ModuleNotFoundError"
     → Ejecutar: INSTALAR.bat

  ❌ "No se encontró SimClient"
     → Verificar que esté instalado en:
       C:\Users\TU_USUARIO\Desktop\SimClient.lnk


█ CARACTERÍSTICAS v2.4.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ Verificación de registro en red (AT+CREG?)
  ✓ Verificación de señal (AT+CSQ)
  ✓ Activación automática de SIMs Claro
  ✓ Guardado automático en SIM (myphone)
  ✓ Blacklist de puertos problemáticos
  ✓ Estado persistente (continúa si se reinicia)
  ✓ Logs detallados y métricas
  ✓ Modo activación masiva (1024 SIMs)
  ✓ Offsets escalonados (sin duplicados)


█ SOPORTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Lee INICIO_RAPIDO.txt (guía completa)
  2. Revisa los logs en rotador_simbank_YYYY-MM-DD.log
  3. Ejecuta --self-test para diagnosticar


╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  ¡TODO LISTO! Ejecuta INSTALAR.bat y luego EJECUTAR.bat        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

