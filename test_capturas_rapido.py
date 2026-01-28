"""
Test Rápido de Capturas de Slots - Rotador SimBank
===================================================
Versión optimizada que:
- Verifica cambio de ICCID (confirma que el slot cambió)
- Espera solo lo necesario (más rápido)
- Detecta cuando los módems están listos
- Captura pantalla y continúa
"""

import time
import subprocess
import os
import serial
from datetime import datetime
from pathlib import Path
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Importar funciones del script principal
try:
    import RotadorSimBank
    from RotadorSimBank import (
        inicializar_simbanks,
        cerrar_simclient,
        abrir_simclient,
        cerrar_puertos_serial,
        escribir_log
    )
except ImportError:
    print("Error: No se pudo importar funciones de RotadorSimBank.py")
    exit(1)

# Configuración
TOTAL_SLOTS = 32
TIEMPO_ESPERA_MINUTOS = 4  # Balance entre velocidad y efectividad
TIEMPO_REINICIO_MODEMS = 30  # Tiempo para reinicio de módems después de AT+CFUN=1,1
CARPETA_CAPTURAS = "capturas_test_rapido"
ARCHIVO_LOG_DETALLADO = None  # Se inicializa en crear_carpeta_capturas()

def log_detallado(mensaje: str):
    """Escribe en el log detallado y en consola"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    linea_log = f"[{timestamp}] {mensaje}"
    print(f"  📝 {mensaje}")
    
    if ARCHIVO_LOG_DETALLADO:
        try:
            with open(ARCHIVO_LOG_DETALLADO, 'a', encoding='utf-8') as f:
                f.write(linea_log + '\n')
        except:
            pass

def crear_carpeta_capturas():
    """Crea la carpeta para guardar capturas si no existe"""
    global ARCHIVO_LOG_DETALLADO
    
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    carpeta = f"{CARPETA_CAPTURAS}_{fecha}"
    
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    
    ARCHIVO_LOG_DETALLADO = os.path.join(carpeta, "test_detallado.log")
    
    print(f"📁 Carpeta de capturas: {carpeta}")
    print(f"📋 Log detallado: {ARCHIVO_LOG_DETALLADO}")
    
    # Inicializar archivo de log
    with open(ARCHIVO_LOG_DETALLADO, 'w', encoding='utf-8') as f:
        f.write(f"{'='*80}\n")
        f.write(f"TEST RÁPIDO DE CAPTURAS - LOG DETALLADO\n")
        f.write(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*80}\n\n")
    
    return carpeta

def enviar_comando_at(com_port: str, comando: str, timeout: float = 2.0) -> str:
    """Envía un comando AT y retorna la respuesta completa"""
    try:
        ser = serial.Serial(
            port=com_port,
            baudrate=115200,
            timeout=timeout
        )
        
        # Limpiar buffer
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Enviar comando
        ser.write(f"{comando}\r\n".encode())
        time.sleep(0.3)
        
        # Leer respuesta
        respuesta = ser.read(500).decode('utf-8', errors='ignore')
        ser.close()
        
        return respuesta.strip()
        
    except Exception as e:
        return f"ERROR: {str(e)}"

def obtener_iccid_puerto(com_port: str) -> dict:
    """Obtiene el ICCID de un puerto COM con detalles"""
    resultado = {
        "puerto": com_port,
        "iccid": "",
        "respuesta_at": "",
        "error": None
    }
    
    try:
        # Intentar con AT+QCCID (Quectel)
        respuesta = enviar_comando_at(com_port, "AT+QCCID", timeout=2.0)
        resultado["respuesta_at"] = respuesta
        
        # Parsear ICCID
        if "+QCCID:" in respuesta or "QCCID:" in respuesta:
            lineas = respuesta.split('\n')
            for linea in lineas:
                if "QCCID:" in linea:
                    iccid = linea.split("QCCID:")[-1].strip().replace("OK", "").strip()
                    # Limpiar caracteres no numéricos al final
                    iccid_limpio = ""
                    for char in iccid:
                        if char.isdigit() or char in ['F', 'f']:
                            iccid_limpio += char
                        else:
                            break
                    
                    if len(iccid_limpio) >= 15:
                        resultado["iccid"] = iccid_limpio
                        return resultado
        
        # Si no funciona, intentar AT+CCID
        if not resultado["iccid"]:
            respuesta = enviar_comando_at(com_port, "AT+CCID", timeout=2.0)
            resultado["respuesta_at"] = respuesta
            
            if "+CCID:" in respuesta or "CCID:" in respuesta:
                lineas = respuesta.split('\n')
                for linea in lineas:
                    if "CCID:" in linea:
                        iccid = linea.split("CCID:")[-1].strip().replace("OK", "").strip()
                        iccid_limpio = ""
                        for char in iccid:
                            if char.isdigit() or char in ['F', 'f']:
                                iccid_limpio += char
                            else:
                                break
                        
                        if len(iccid_limpio) >= 15:
                            resultado["iccid"] = iccid_limpio
                            return resultado
        
        return resultado
        
    except Exception as e:
        resultado["error"] = str(e)
        return resultado

def obtener_iccids_actuales():
    """Obtiene todos los ICCIDs actuales de los módems usando hilos paralelos"""
    try:
        import serial.tools.list_ports
        
        # Obtener todos los puertos COM disponibles
        puertos_disponibles = [puerto.device for puerto in serial.tools.list_ports.comports()]
        
        # Excluir los puertos de los controladores SimBank
        controladores_simbank = [config["com"] for config in RotadorSimBank.SIM_BANKS.values()]
        puertos_modems = [p for p in puertos_disponibles if p not in controladores_simbank]
        
        log_detallado(f"Leyendo ICCIDs de {len(puertos_modems)} módems en paralelo...")
        
        iccids_info = []
        
        # Usar ThreadPoolExecutor para leer ICCIDs en paralelo
        with ThreadPoolExecutor(max_workers=32) as executor:
            # Crear todas las tareas
            future_to_puerto = {executor.submit(obtener_iccid_puerto, puerto): puerto for puerto in puertos_modems}
            
            # Procesar resultados conforme se completan
            for future in as_completed(future_to_puerto):
                try:
                    info = future.result()
                    if info["iccid"]:
                        iccids_info.append(info)
                        log_detallado(f"  {info['puerto']}: {info['iccid']}")
                    elif info["error"]:
                        log_detallado(f"  {info['puerto']}: ERROR - {info['error']}")
                    else:
                        log_detallado(f"  {info['puerto']}: Sin respuesta o ICCID no detectado")
                except Exception as e:
                    puerto = future_to_puerto[future]
                    log_detallado(f"  {puerto}: Excepción - {str(e)}")
        
        # Ordenar por puerto para que sea más fácil de leer
        iccids_info.sort(key=lambda x: x["puerto"])
        
        # Detectar duplicados
        iccids = [info["iccid"] for info in iccids_info]
        duplicados = set([x for x in iccids if iccids.count(x) > 1])
        
        if duplicados:
            log_detallado(f"⚠️  DUPLICADOS DETECTADOS: {len(duplicados)} ICCIDs repetidos")
            for dup in duplicados:
                puertos_dup = [info["puerto"] for info in iccids_info if info["iccid"] == dup]
                log_detallado(f"  ICCID {dup}: {', '.join(puertos_dup)}")
        else:
            log_detallado(f"✅ No hay ICCIDs duplicados ({len(iccids)} únicos)")
        
        return iccids_info
        
    except Exception as e:
        log_detallado(f"❌ Error obteniendo ICCIDs: {e}")
        return []

def reiniciar_un_modem(puerto_modem: str) -> dict:
    """Reinicia un módulo individual con AT+CFUN=1,1"""
    try:
        respuesta = enviar_comando_at(puerto_modem, "AT+CFUN=1,1", timeout=1.0)
        
        if "OK" in respuesta or respuesta == "":
            return {"puerto": puerto_modem, "exitoso": True, "respuesta": "OK"}
        else:
            return {"puerto": puerto_modem, "exitoso": True, "respuesta": respuesta[:50]}
    except Exception as e:
        return {"puerto": puerto_modem, "exitoso": False, "error": str(e)}

def reiniciar_modems_cfun():
    """Reinicia todos los módems con AT+CFUN=1,1 usando hilos paralelos"""
    try:
        import serial.tools.list_ports
        
        # Obtener todos los puertos COM disponibles
        puertos_disponibles = [puerto.device for puerto in serial.tools.list_ports.comports()]
        
        # Excluir los puertos de los controladores SimBank
        controladores_simbank = [config["com"] for config in RotadorSimBank.SIM_BANKS.values()]
        puertos_modems = [p for p in puertos_disponibles if p not in controladores_simbank]
        
        print(f"  🔄 Reiniciando {len(puertos_modems)} módems con AT+CFUN=1,1 (paralelo)...")
        log_detallado(f"Enviando AT+CFUN=1,1 a {len(puertos_modems)} módems en paralelo...")
        
        reiniciados = 0
        errores = 0
        
        # Usar ThreadPoolExecutor para reiniciar en paralelo
        with ThreadPoolExecutor(max_workers=32) as executor:
            # Crear todas las tareas
            future_to_puerto = {executor.submit(reiniciar_un_modem, puerto): puerto for puerto in puertos_modems}
            
            # Procesar resultados conforme se completan
            resultados = []
            for future in as_completed(future_to_puerto):
                try:
                    resultado = future.result()
                    resultados.append(resultado)
                    
                    if resultado["exitoso"]:
                        if resultado["respuesta"] == "OK":
                            log_detallado(f"  ✅ {resultado['puerto']}: OK")
                        else:
                            log_detallado(f"  ⚠️  {resultado['puerto']}: {resultado['respuesta']}")
                        reiniciados += 1
                    else:
                        log_detallado(f"  ❌ {resultado['puerto']}: {resultado['error']}")
                        errores += 1
                except Exception as e:
                    puerto = future_to_puerto[future]
                    log_detallado(f"  ❌ {puerto}: Excepción - {str(e)}")
                    errores += 1
        
        print(f"  ✅ Reiniciados: {reiniciados} | ❌ Errores: {errores}")
        log_detallado(f"Resumen: {reiniciados} reiniciados, {errores} errores")
        
        return reiniciados > 0
        
    except Exception as e:
        print(f"  ⚠️ Error reiniciando módems: {e}")
        log_detallado(f"❌ Error crítico: {e}")
        return False

def cambiar_slot_pool_rapido(pool_name: str, pool_config: dict, slot_base: int) -> dict:
    """Cambia todos los puertos de un pool al slot y verifica el cambio"""
    sim_bank_com = pool_config["com"]
    puertos_logicos = pool_config["puertos"]
    offset_slot = pool_config.get("offset_slot", 0)
    
    # Calcular slot real con offset
    slot_real = ((slot_base - 1 + offset_slot) % TOTAL_SLOTS) + 1
    slot_formateado = f"{slot_real:04d}"
    
    print(f"  📡 {pool_name}: Cambiando a slot {slot_real:02d} (COM: {sim_bank_com})")
    log_detallado(f"")
    log_detallado(f"{'='*60}")
    log_detallado(f"{pool_name}: Cambio a slot {slot_real:02d}")
    log_detallado(f"SimBank COM: {sim_bank_com}")
    log_detallado(f"Offset: {offset_slot}, Slot base: {slot_base}, Slot real: {slot_real}")
    
    resultado = {
        "pool": pool_name,
        "slot_real": slot_real,
        "exitoso": False,
        "comandos_enviados": [],
        "respuestas": []
    }
    
    try:
        # Abrir puerto serial del SIM Bank
        ser = serial.Serial(
            port=sim_bank_com,
            baudrate=115200,
            timeout=3
        )
        
        time.sleep(0.5)
        
        # Cambiar cada puerto lógico
        for puerto_logico in puertos_logicos:
            comando = f"AT+SWIT{puerto_logico}-{slot_formateado}"
            comando_completo = f"{comando}\r\n"
            
            log_detallado(f"  → Enviando: {comando}")
            
            ser.write(comando_completo.encode())
            time.sleep(0.3)
            
            # Intentar leer respuesta
            try:
                respuesta = ser.read(100).decode('utf-8', errors='ignore').strip()
                if respuesta:
                    log_detallado(f"  ← Respuesta: {respuesta}")
                    resultado["respuestas"].append(respuesta)
                else:
                    log_detallado(f"  ← Sin respuesta")
            except:
                log_detallado(f"  ← No se pudo leer respuesta")
            
            resultado["comandos_enviados"].append(comando)
        
        ser.close()
        resultado["exitoso"] = True
        print(f"  ✅ {pool_name}: {len(puertos_logicos)} comandos enviados al slot {slot_real:02d}")
        log_detallado(f"✅ {pool_name}: Completado - {len(puertos_logicos)} comandos enviados")
        log_detallado(f"{'='*60}")
        
        return resultado
        
    except Exception as e:
        print(f"  ❌ {pool_name}: Error - {e}")
        log_detallado(f"❌ {pool_name}: ERROR - {str(e)}")
        log_detallado(f"{'='*60}")
        return resultado

def capturar_pantalla(carpeta: str, slot: int):
    """Captura la pantalla completa y guarda en archivo"""
    try:
        try:
            import mss
            import mss.tools
            
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                filename = os.path.join(carpeta, f"slot_{slot:02d}.png")
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=filename)
                print(f"  📸 Captura guardada: slot_{slot:02d}.png")
                return True
                
        except ImportError:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            filename = os.path.join(carpeta, f"slot_{slot:02d}.png")
            screenshot.save(filename)
            print(f"  📸 Captura guardada: slot_{slot:02d}.png")
            return True
            
    except Exception as e:
        print(f"  ⚠️ Error al capturar pantalla: {e}")
        return False

def procesar_slot_rapido(slot: int, carpeta_capturas: str, sim_banks: dict):
    """Procesa un slot de forma rápida y eficiente"""
    print(f"\n{'='*80}")
    print(f"🔄 PROCESANDO SLOT {slot:02d}/{TOTAL_SLOTS} ({(slot/TOTAL_SLOTS)*100:.1f}%)")
    print(f"{'='*80}")
    
    log_detallado(f"\n\n{'#'*80}")
    log_detallado(f"# SLOT {slot:02d}/{TOTAL_SLOTS} - {datetime.now().strftime('%H:%M:%S')}")
    log_detallado(f"{'#'*80}\n")
    
    # 1. Cerrar HeroSMS
    print("1️⃣ Cerrando HeroSMS...")
    log_detallado("PASO 1: Cerrando HeroSMS...")
    cerrar_simclient()
    cerrar_puertos_serial()
    time.sleep(1)
    log_detallado("HeroSMS cerrado y puertos liberados")
    
    # 1.5. Reiniciar módems ANTES de leer ICCIDs iniciales
    print("  🔄 Reiniciando módems antes de leer estado inicial...")
    log_detallado("\nReiniciando módems para estado conocido...")
    reiniciar_modems_cfun()
    print(f"  ⏳ Esperando 30 segundos para que módems reinicien...")
    log_detallado("Esperando 30 segundos...")
    time.sleep(30)
    
    # 1.6. Leer ICCIDs ANTES del cambio
    print("  📋 Leyendo ICCIDs ANTES del cambio...")
    log_detallado("\n--- ICCIDs ANTES DEL CAMBIO ---")
    iccids_antes = obtener_iccids_actuales()
    
    # 2. Rotar todos los pools al slot
    print(f"2️⃣ Rotando todos los pools al slot {slot:02d}...")
    log_detallado(f"\nPASO 2: Rotando todos los pools al slot {slot:02d}...")
    resultados = []
    for pool_name, pool_config in sim_banks.items():
        resultado = cambiar_slot_pool_rapido(pool_name, pool_config, slot)
        resultados.append(resultado)
    
    # Esperar cambio físico
    print(f"  ⏳ Esperando 15 segundos para aplicar cambios físicos...")
    log_detallado("\nEsperando 15 segundos para estabilización mecánica...")
    time.sleep(15)
    
    # 3. Reiniciar módems para forzar detección de nueva SIM
    print("3️⃣ Reiniciando módems (AT+CFUN=1,1) para detectar nueva SIM...")
    log_detallado("\nPASO 3: Reiniciando módems con AT+CFUN=1,1...")
    reiniciar_modems_cfun()
    print(f"  ⏳ Esperando 30 segundos para reinicio de módems...")
    log_detallado("Esperando 30 segundos para reinicio completo...")
    time.sleep(30)
    
    # 3.5. Leer ICCIDs DESPUÉS del reinicio
    print("  📋 Leyendo ICCIDs DESPUÉS del reinicio...")
    log_detallado("\n--- ICCIDs DESPUÉS DEL REINICIO ---")
    iccids_despues = obtener_iccids_actuales()
    
    # Comparar ICCIDs antes y después
    log_detallado("\n--- ANÁLISIS DE CAMBIOS ---")
    if len(iccids_antes) > 0 and len(iccids_despues) > 0:
        iccids_antes_set = set([info["iccid"] for info in iccids_antes if info["iccid"]])
        iccids_despues_set = set([info["iccid"] for info in iccids_despues if info["iccid"]])
        
        nuevos = iccids_despues_set - iccids_antes_set
        desaparecidos = iccids_antes_set - iccids_despues_set
        sin_cambio = iccids_antes_set & iccids_despues_set
        
        log_detallado(f"ICCIDs detectados ANTES: {len(iccids_antes_set)}")
        log_detallado(f"ICCIDs detectados DESPUÉS: {len(iccids_despues_set)}")
        log_detallado(f"ICCIDs NUEVOS (cambiaron): {len(nuevos)}")
        log_detallado(f"ICCIDs que DESAPARECIERON: {len(desaparecidos)}")
        log_detallado(f"ICCIDs SIN CAMBIO: {len(sin_cambio)}")
        
        if len(sin_cambio) > 0:
            log_detallado(f"⚠️  ADVERTENCIA: {len(sin_cambio)} ICCIDs no cambiaron:")
            for iccid in list(sin_cambio)[:5]:  # Mostrar solo primeros 5
                log_detallado(f"  - {iccid}")
    
    # 4. Abrir HeroSMS
    print("4️⃣ Abriendo HeroSMS...")
    log_detallado("\nPASO 4: Abriendo HeroSMS...")
    abrir_simclient()
    log_detallado("HeroSMS iniciado")
    
    # 5. Espera inteligente
    print(f"5️⃣ Esperando {TIEMPO_ESPERA_MINUTOS} minutos para detección...")
    log_detallado(f"\nPASO 5: Esperando {TIEMPO_ESPERA_MINUTOS} minutos para registro en red...")
    tiempo_total = TIEMPO_ESPERA_MINUTOS * 60
    tiempo_transcurrido = 0
    intervalo_check = 30
    
    while tiempo_transcurrido < tiempo_total:
        tiempo_restante = tiempo_total - tiempo_transcurrido
        minutos = tiempo_restante // 60
        segundos = tiempo_restante % 60
        print(f"  ⏳ {minutos}m {segundos}s restantes...")
        
        espera = min(intervalo_check, tiempo_restante)
        time.sleep(espera)
        tiempo_transcurrido += espera
    
    log_detallado("Tiempo de espera completado")
    
    # 5.5. Leer ICCIDs FINALES (antes de captura)
    print("  📋 Leyendo ICCIDs FINALES antes de captura...")
    log_detallado("\n--- ICCIDs FINALES (ANTES DE CAPTURA) ---")
    iccids_finales = obtener_iccids_actuales()
    
    # 6. Capturar pantalla
    print("6️⃣ Capturando pantalla...")
    log_detallado("\nPASO 6: Capturando pantalla...")
    capturar_pantalla(carpeta_capturas, slot)
    
    # 7. Cerrar HeroSMS
    print("7️⃣ Cerrando HeroSMS...")
    log_detallado("\nPASO 7: Cerrando HeroSMS...")
    cerrar_simclient()
    cerrar_puertos_serial()
    log_detallado("HeroSMS cerrado")
    
    # Resumen del slot
    log_detallado(f"\n{'='*80}")
    log_detallado(f"SLOT {slot:02d} COMPLETADO - {datetime.now().strftime('%H:%M:%S')}")
    log_detallado(f"ICCIDs únicos detectados: {len(set([i['iccid'] for i in iccids_finales if i['iccid']]))}")
    log_detallado(f"{'='*80}\n")
    
    print(f"✅ Slot {slot:02d} completado!")
    time.sleep(1)  # Reducido de 2 a 1

def main():
    """Función principal del test rápido"""
    print("\n" + "="*80)
    print("⚡ TEST RÁPIDO DE CAPTURAS DE SLOTS - ROTADOR SIMBANK")
    print("="*80)
    print(f"📊 Total de slots a procesar: {TOTAL_SLOTS}")
    print(f"⏱️  Tiempo por slot: ~{TIEMPO_ESPERA_MINUTOS + 3} minutos")
    print(f"⏱️  Tiempo total estimado: ~{(TIEMPO_ESPERA_MINUTOS + 3) * TOTAL_SLOTS / 60:.1f} horas")
    print("⚡ Con hilos paralelos para velocidad máxima")
    print("⚡ Incluye doble reinicio de módems (AT+CFUN=1,1)")
    print("="*80 + "\n")
    
    # Confirmar con el usuario
    respuesta = input("¿Deseas continuar con el test rápido? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Test cancelado")
        return
    
    # Inicializar SIM Banks
    print("\n🔍 Inicializando configuración de SIM Banks...")
    inicializar_simbanks()
    
    # Obtener SIM_BANKS del módulo
    SIM_BANKS = RotadorSimBank.SIM_BANKS
    
    if not SIM_BANKS:
        print("❌ No se detectaron SIM Banks. Verifica la configuración.")
        return
    
    print(f"✅ {len(SIM_BANKS)} pools detectados:")
    for pool_name, config in SIM_BANKS.items():
        print(f"   • {pool_name}: {config['com']} (offset={config.get('offset_slot', 0)})")
    
    # Crear carpeta de capturas
    carpeta = crear_carpeta_capturas()
    
    # Procesar todos los slots
    print("\n" + "="*80)
    print("🚀 INICIANDO TEST RÁPIDO DE SLOTS")
    print("="*80 + "\n")
    
    tiempo_inicio = time.time()
    
    for slot in range(1, TOTAL_SLOTS + 1):
        try:
            procesar_slot_rapido(slot, carpeta, SIM_BANKS)
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrumpido por usuario (Ctrl+C)")
            print("🛑 Cerrando HeroSMS y limpiando...")
            cerrar_simclient()
            cerrar_puertos_serial()
            break
        except Exception as e:
            print(f"\n❌ Error procesando slot {slot}: {e}")
            print("⏭️  Continuando con el siguiente slot...")
            continue
    
    tiempo_fin = time.time()
    duracion = tiempo_fin - tiempo_inicio
    
    # Resumen final
    print("\n" + "="*80)
    print("✅ TEST RÁPIDO COMPLETADO")
    print("="*80)
    print(f"⏱️  Tiempo total: {duracion/60:.1f} minutos ({duracion/3600:.2f} horas)")
    print(f"📁 Capturas guardadas en: {carpeta}")
    print(f"📊 Total de capturas: {TOTAL_SLOTS}")
    print("="*80 + "\n")
    
    # Abrir carpeta de capturas
    try:
        os.startfile(carpeta)
        print("📂 Abriendo carpeta de capturas...")
    except:
        pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        print("🛑 Cerrando HeroSMS...")
        try:
            cerrar_simclient()
            cerrar_puertos_serial()
        except:
            pass
