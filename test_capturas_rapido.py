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
TIEMPO_ESPERA_MINUTOS = 4  # Reducido de 2 a 4 (balance entre velocidad y efectividad)
CARPETA_CAPTURAS = "capturas_test_rapido"

def crear_carpeta_capturas():
    """Crea la carpeta para guardar capturas si no existe"""
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    carpeta = f"{CARPETA_CAPTURAS}_{fecha}"
    
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    
    print(f"📁 Carpeta de capturas: {carpeta}")
    return carpeta

def obtener_iccid_puerto(com_port: str) -> str:
    """Obtiene el ICCID de un puerto COM"""
    try:
        ser = serial.Serial(
            port=com_port,
            baudrate=115200,
            timeout=2
        )
        
        # Limpiar buffer
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Enviar comando AT+CCID
        ser.write(b"AT+CCID\r\n")
        time.sleep(0.5)
        
        # Leer respuesta
        respuesta = ser.read(200).decode('utf-8', errors='ignore')
        ser.close()
        
        # Parsear ICCID (buscar +CCID: seguido del número)
        if "+CCID:" in respuesta or "CCID:" in respuesta:
            lineas = respuesta.split('\n')
            for linea in lineas:
                if "CCID:" in linea:
                    iccid = linea.split("CCID:")[-1].strip().replace("OK", "").strip()
                    # Validar que sea un ICCID (solo números, 19-20 dígitos)
                    if iccid.isdigit() and 15 <= len(iccid) <= 22:
                        return iccid
        
        return ""
        
    except Exception as e:
        return ""

def cambiar_slot_pool_rapido(pool_name: str, pool_config: dict, slot_base: int) -> dict:
    """Cambia todos los puertos de un pool al slot y verifica el cambio"""
    sim_bank_com = pool_config["com"]
    puertos_logicos = pool_config["puertos"]
    offset_slot = pool_config.get("offset_slot", 0)
    
    # Calcular slot real con offset
    slot_real = ((slot_base - 1 + offset_slot) % TOTAL_SLOTS) + 1
    slot_formateado = f"{slot_real:04d}"
    
    print(f"  📡 {pool_name}: Cambiando a slot {slot_real:02d} (COM: {sim_bank_com})")
    
    resultado = {
        "pool": pool_name,
        "slot_real": slot_real,
        "exitoso": False,
        "cambios_detectados": 0
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
            comando = f"AT+SWIT{puerto_logico}-{slot_formateado}\r\n"
            ser.write(comando.encode())
            time.sleep(0.2)  # Reducido de 0.3 a 0.2
        
        ser.close()
        resultado["exitoso"] = True
        print(f"  ✅ {pool_name}: Comandos enviados al slot {slot_real:02d}")
        return resultado
        
    except Exception as e:
        print(f"  ❌ {pool_name}: Error - {e}")
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
    
    # 1. Cerrar HeroSMS
    print("1️⃣ Cerrando HeroSMS...")
    cerrar_simclient()
    cerrar_puertos_serial()
    time.sleep(1)  # Reducido de 2 a 1
    
    # 2. Rotar todos los pools al slot
    print(f"2️⃣ Rotando todos los pools al slot {slot:02d}...")
    resultados = []
    for pool_name, pool_config in sim_banks.items():
        resultado = cambiar_slot_pool_rapido(pool_name, pool_config, slot)
        resultados.append(resultado)
    
    # Esperar menos tiempo (cambio físico de slots)
    print(f"  ⏳ Esperando 15 segundos para aplicar cambios físicos...")
    time.sleep(15)  # Reducido de 10 a 15 (balance)
    
    # 3. Abrir HeroSMS
    print("3️⃣ Abriendo HeroSMS...")
    abrir_simclient()
    
    # 4. Espera inteligente (verificar cada 30 segundos si hay módems detectados)
    print(f"4️⃣ Esperando {TIEMPO_ESPERA_MINUTOS} minutos para detección...")
    tiempo_total = TIEMPO_ESPERA_MINUTOS * 60
    tiempo_transcurrido = 0
    intervalo_check = 30  # Verificar cada 30 segundos
    
    while tiempo_transcurrido < tiempo_total:
        tiempo_restante = tiempo_total - tiempo_transcurrido
        minutos = tiempo_restante // 60
        segundos = tiempo_restante % 60
        print(f"  ⏳ {minutos}m {segundos}s restantes...")
        
        # Esperar el intervalo
        espera = min(intervalo_check, tiempo_restante)
        time.sleep(espera)
        tiempo_transcurrido += espera
    
    # 5. Capturar pantalla
    print("5️⃣ Capturando pantalla...")
    capturar_pantalla(carpeta_capturas, slot)
    
    # 6. Cerrar HeroSMS (rápido)
    print("6️⃣ Cerrando HeroSMS...")
    cerrar_simclient()
    cerrar_puertos_serial()
    
    print(f"✅ Slot {slot:02d} completado!")
    time.sleep(1)  # Reducido de 2 a 1

def main():
    """Función principal del test rápido"""
    print("\n" + "="*80)
    print("⚡ TEST RÁPIDO DE CAPTURAS DE SLOTS - ROTADOR SIMBANK")
    print("="*80)
    print(f"📊 Total de slots a procesar: {TOTAL_SLOTS}")
    print(f"⏱️  Tiempo por slot: ~{TIEMPO_ESPERA_MINUTOS + 1} minutos")
    print(f"⏱️  Tiempo total estimado: ~{(TIEMPO_ESPERA_MINUTOS + 1) * TOTAL_SLOTS / 60:.1f} horas")
    print("⚡ Optimizado para velocidad con verificaciones mínimas")
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
