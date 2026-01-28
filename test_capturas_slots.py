"""
Test de Capturas de Slots - Rotador SimBank
============================================
Script de prueba que:
1. Cierra HeroSMS
2. Rota a cada slot (1-32)
3. Abre HeroSMS
4. Espera 2 minutos
5. Captura pantalla
6. Cierra HeroSMS
7. Repite para todos los slots
"""

import time
import subprocess
import os
import serial
from datetime import datetime
from pathlib import Path

# Importar funciones del script principal
try:
    from RotadorSimBank import (
        SIM_BANKS,
        inicializar_simbanks,
        cerrar_simclient,
        abrir_simclient,
        cerrar_puertos_serial,
        escribir_log
    )
except ImportError:
    print("Error: No se pudo importar funciones de RotadorSimBank.py")
    print("Asegúrate de que RotadorSimBank.py esté en la misma carpeta")
    exit(1)

# Configuración
TOTAL_SLOTS = 32
TIEMPO_ESPERA_MINUTOS = 2
CARPETA_CAPTURAS = "capturas_test_slots"

def crear_carpeta_capturas():
    """Crea la carpeta para guardar capturas si no existe"""
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    carpeta = f"{CARPETA_CAPTURAS}_{fecha}"
    
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    
    print(f"📁 Carpeta de capturas: {carpeta}")
    return carpeta

def cambiar_slot_pool_test(pool_name: str, pool_config: dict, slot_base: int):
    """Cambia todos los puertos de un pool al slot especificado"""
    sim_bank_com = pool_config["com"]
    puertos_logicos = pool_config["puertos"]
    offset_slot = pool_config.get("offset_slot", 0)
    
    # Calcular slot real con offset
    slot_real = ((slot_base - 1 + offset_slot) % TOTAL_SLOTS) + 1
    
    print(f"  📡 {pool_name}: Cambiando a slot {slot_real:02d} (COM: {sim_bank_com})")
    
    try:
        # Abrir puerto serial del SIM Bank
        ser = serial.Serial(
            port=sim_bank_com,
            baudrate=115200,
            timeout=3,
            write_timeout=3
        )
        
        time.sleep(0.5)
        
        # Cambiar cada puerto lógico
        for puerto_logico in puertos_logicos:
            comando = f"AT+SWIT={puerto_logico},{slot_real}\r\n"
            ser.write(comando.encode())
            time.sleep(0.3)
        
        ser.close()
        print(f"  ✅ {pool_name}: Slot {slot_real:02d} aplicado")
        return True
        
    except Exception as e:
        print(f"  ❌ {pool_name}: Error - {e}")
        return False

def capturar_pantalla(carpeta: str, slot: int):
    """Captura la pantalla completa y guarda en archivo"""
    try:
        # Usar mss para captura (más rápido y funciona en servicios)
        try:
            import mss
            import mss.tools
            
            with mss.mss() as sct:
                # Capturar monitor principal
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                
                # Guardar
                filename = os.path.join(carpeta, f"slot_{slot:02d}.png")
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=filename)
                
                print(f"  📸 Captura guardada: slot_{slot:02d}.png")
                return True
                
        except ImportError:
            # Fallback a PIL si mss no está disponible
            from PIL import ImageGrab
            
            screenshot = ImageGrab.grab()
            filename = os.path.join(carpeta, f"slot_{slot:02d}.png")
            screenshot.save(filename)
            
            print(f"  📸 Captura guardada: slot_{slot:02d}.png")
            return True
            
    except Exception as e:
        print(f"  ⚠️ Error al capturar pantalla: {e}")
        return False

def procesar_slot(slot: int, carpeta_capturas: str):
    """Procesa un slot completo: cerrar, rotar, abrir, esperar, capturar, cerrar"""
    print(f"\n{'='*80}")
    print(f"🔄 PROCESANDO SLOT {slot:02d}/{TOTAL_SLOTS} ({(slot/TOTAL_SLOTS)*100:.1f}%)")
    print(f"{'='*80}")
    
    # 1. Cerrar HeroSMS
    print("1️⃣ Cerrando HeroSMS...")
    cerrar_simclient()
    cerrar_puertos_serial()
    time.sleep(2)
    
    # 2. Rotar todos los pools al slot
    print(f"2️⃣ Rotando todos los pools al slot {slot:02d}...")
    for pool_name, pool_config in SIM_BANKS.items():
        cambiar_slot_pool_test(pool_name, pool_config, slot)
    
    # Esperar a que se apliquen los cambios
    print("  ⏳ Esperando 10 segundos para aplicar cambios...")
    time.sleep(10)
    
    # 3. Abrir HeroSMS
    print("3️⃣ Abriendo HeroSMS...")
    abrir_simclient()
    
    # 4. Esperar 2 minutos
    print(f"4️⃣ Esperando {TIEMPO_ESPERA_MINUTOS} minutos para detección de módems...")
    for i in range(TIEMPO_ESPERA_MINUTOS * 60):
        if i % 15 == 0:  # Mostrar progreso cada 15 segundos
            tiempo_restante = TIEMPO_ESPERA_MINUTOS * 60 - i
            print(f"  ⏳ {tiempo_restante}s restantes...")
        time.sleep(1)
    
    # 5. Capturar pantalla
    print("5️⃣ Capturando pantalla...")
    capturar_pantalla(carpeta_capturas, slot)
    
    # 6. Cerrar HeroSMS
    print("6️⃣ Cerrando HeroSMS...")
    cerrar_simclient()
    cerrar_puertos_serial()
    
    print(f"✅ Slot {slot:02d} completado!")
    time.sleep(2)

def main():
    """Función principal del test"""
    print("\n" + "="*80)
    print("🧪 TEST DE CAPTURAS DE SLOTS - ROTADOR SIMBANK")
    print("="*80)
    print(f"📊 Total de slots a procesar: {TOTAL_SLOTS}")
    print(f"⏱️  Tiempo por slot: ~{TIEMPO_ESPERA_MINUTOS + 1} minutos")
    print(f"⏱️  Tiempo total estimado: ~{(TIEMPO_ESPERA_MINUTOS + 1) * TOTAL_SLOTS} minutos ({((TIEMPO_ESPERA_MINUTOS + 1) * TOTAL_SLOTS)/60:.1f} horas)")
    print("="*80 + "\n")
    
    # Confirmar con el usuario
    respuesta = input("¿Deseas continuar con el test? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Test cancelado")
        return
    
    # Inicializar SIM Banks
    print("\n🔍 Inicializando configuración de SIM Banks...")
    inicializar_simbanks()
    
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
    print("🚀 INICIANDO TEST DE SLOTS")
    print("="*80 + "\n")
    
    tiempo_inicio = time.time()
    
    for slot in range(1, TOTAL_SLOTS + 1):
        try:
            procesar_slot(slot, carpeta)
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
    print("✅ TEST COMPLETADO")
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
