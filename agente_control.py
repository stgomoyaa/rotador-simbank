"""
Agente de Control Remoto - Rotador SimBank
===========================================
Servicio que corre 24/7 y escucha comandos desde el dashboard de Vercel.

Comandos soportados:
- restart_pc: Reinicia el PC
- restart_herosms: Reinicia Hero-SMS
- restart_rotador: Reinicia el RotadorSimBank
- status: Devuelve estado del sistema
- stop_rotador: Detiene el RotadorSimBank
"""

import time
import requests
import subprocess
import os
import psutil
import platform
import json
from datetime import datetime
from pathlib import Path

# ==================== CONFIGURACIÓN ====================
class Config:
    """Configuración del agente"""
    VERSION = "1.0.0"
    
    # URL de tu API en Vercel (CAMBIAR DESPUÉS DE DEPLOY)
    API_URL = "https://tu-dashboard.vercel.app/api/commands"
    
    # Token de autenticación (genera uno único para tu instalación)
    AUTH_TOKEN = "CAMBIAR_ESTO_POR_UN_TOKEN_SEGURO"
    
    # ID único de esta máquina (para identificar múltiples instalaciones)
    MACHINE_ID = platform.node()  # Nombre de la máquina
    
    # Intervalo de polling (segundos)
    POLL_INTERVAL = 5  # Consulta cada 5 segundos
    
    # Rutas
    ROTADOR_SCRIPT = "RotadorSimBank.py"
    HEROSMS_EXE = "HeroSMS-Partners.exe"
    LOG_FILE = "agente_control.log"

# ==================== UTILIDADES ====================
def log(mensaje: str):
    """Escribe en el log con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {mensaje}\n"
    
    print(mensaje)  # Consola
    
    try:
        with open(Config.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linea)
    except:
        pass

def ejecutar_comando(comando: str) -> dict:
    """Ejecuta un comando del sistema y devuelve resultado"""
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": True,
            "stdout": resultado.stdout,
            "stderr": resultado.stderr,
            "returncode": resultado.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ==================== COMANDOS ====================
def cmd_restart_pc():
    """Reinicia el PC"""
    log("🔄 Comando recibido: REINICIAR PC")
    
    # Dar tiempo para responder al servidor
    time.sleep(2)
    
    # Reiniciar (Windows)
    if platform.system() == "Windows":
        os.system("shutdown /r /t 5")
        return {"success": True, "message": "PC se reiniciará en 5 segundos"}
    else:
        return {"success": False, "message": "Sistema operativo no soportado"}

def cmd_restart_herosms():
    """Reinicia Hero-SMS Partners"""
    log("🔄 Comando recibido: REINICIAR HERO-SMS")
    
    try:
        # 1. Cerrar Hero-SMS
        subprocess.run(["taskkill", "/f", "/im", Config.HEROSMS_EXE], 
                      capture_output=True, timeout=10)
        time.sleep(3)
        
        # 2. Abrir Hero-SMS desde el acceso directo
        user = os.environ.get("USERNAME", "")
        shortcut_path = f"C:\\Users\\{user}\\Desktop\\HeroSMS-Partners.lnk"
        
        if os.path.exists(shortcut_path):
            os.startfile(shortcut_path)
            log("✅ Hero-SMS reiniciado correctamente")
            return {"success": True, "message": "Hero-SMS reiniciado"}
        else:
            log(f"❌ No se encontró Hero-SMS en: {shortcut_path}")
            return {"success": False, "message": f"No se encontró Hero-SMS en: {shortcut_path}"}
            
    except Exception as e:
        log(f"❌ Error al reiniciar Hero-SMS: {e}")
        return {"success": False, "message": str(e)}

def cmd_restart_rotador():
    """Reinicia el RotadorSimBank"""
    log("🔄 Comando recibido: REINICIAR ROTADOR")
    
    try:
        # 1. Detener el rotador actual
        cmd_stop_rotador()
        time.sleep(3)
        
        # 2. Iniciar nuevo proceso del rotador
        script_path = os.path.join(os.getcwd(), Config.ROTADOR_SCRIPT)
        
        if os.path.exists(script_path):
            # Ejecutar en segundo plano
            subprocess.Popen(
                ["python", script_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0
            )
            log("✅ RotadorSimBank reiniciado correctamente")
            return {"success": True, "message": "RotadorSimBank reiniciado"}
        else:
            log(f"❌ No se encontró RotadorSimBank.py en: {script_path}")
            return {"success": False, "message": f"No se encontró el script en: {script_path}"}
            
    except Exception as e:
        log(f"❌ Error al reiniciar RotadorSimBank: {e}")
        return {"success": False, "message": str(e)}

def cmd_stop_rotador():
    """Detiene el RotadorSimBank"""
    log("🛑 Comando recibido: DETENER ROTADOR")
    
    try:
        # Buscar procesos de Python ejecutando RotadorSimBank.py
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('RotadorSimBank' in str(arg) for arg in cmdline):
                        proc.kill()
                        log(f"✅ Proceso RotadorSimBank (PID {proc.info['pid']}) detenido")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Eliminar archivo lock si existe
        lock_file = "rotador.lock"
        if os.path.exists(lock_file):
            os.remove(lock_file)
            log("✅ Archivo lock eliminado")
        
        return {"success": True, "message": "RotadorSimBank detenido"}
        
    except Exception as e:
        log(f"❌ Error al detener RotadorSimBank: {e}")
        return {"success": False, "message": str(e)}

def cmd_status():
    """Devuelve el estado del sistema"""
    log("📊 Comando recibido: STATUS")
    
    try:
        # 1. Verificar si Hero-SMS está corriendo
        herosms_running = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and Config.HEROSMS_EXE.lower() in proc.info['name'].lower():
                herosms_running = True
                break
        
        # 2. Verificar si RotadorSimBank está corriendo
        rotador_running = False
        rotador_pid = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('RotadorSimBank' in str(arg) for arg in cmdline):
                        rotador_running = True
                        rotador_pid = proc.info['pid']
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 3. Info del sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 4. Uptime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_hours = uptime_seconds / 3600
        
        status = {
            "success": True,
            "machine_id": Config.MACHINE_ID,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "herosms": {
                    "running": herosms_running,
                    "status": "🟢 Activo" if herosms_running else "🔴 Inactivo"
                },
                "rotador": {
                    "running": rotador_running,
                    "pid": rotador_pid,
                    "status": "🟢 Activo" if rotador_running else "🔴 Inactivo"
                }
            },
            "system": {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "disk_percent": round(disk.percent, 1),
                "uptime_hours": round(uptime_hours, 2)
            }
        }
        
        log(f"✅ Status: Hero-SMS={herosms_running}, Rotador={rotador_running}")
        return status
        
    except Exception as e:
        log(f"❌ Error al obtener status: {e}")
        return {
            "success": False,
            "message": str(e)
        }

# ==================== DISPATCHER ====================
COMMANDS = {
    "restart_pc": cmd_restart_pc,
    "restart_herosms": cmd_restart_herosms,
    "restart_rotador": cmd_restart_rotador,
    "stop_rotador": cmd_stop_rotador,
    "status": cmd_status,
}

def procesar_comando(comando: str) -> dict:
    """Procesa un comando y devuelve resultado"""
    if comando in COMMANDS:
        try:
            return COMMANDS[comando]()
        except Exception as e:
            log(f"❌ Error ejecutando comando '{comando}': {e}")
            return {"success": False, "message": str(e)}
    else:
        log(f"⚠️ Comando desconocido: {comando}")
        return {"success": False, "message": f"Comando desconocido: {comando}"}

# ==================== POLLING ====================
def consultar_comandos():
    """Consulta al servidor si hay comandos pendientes"""
    try:
        headers = {
            "Authorization": f"Bearer {Config.AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "machine_id": Config.MACHINE_ID,
            "action": "poll"
        }
        
        response = requests.post(
            Config.API_URL,
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Si hay un comando pendiente
            if result.get("has_command"):
                comando = result.get("command")
                log(f"📨 Comando recibido del servidor: {comando}")
                
                # Ejecutar comando
                resultado = procesar_comando(comando)
                
                # Enviar resultado de vuelta al servidor
                enviar_resultado(comando, resultado)
                
        elif response.status_code == 204:
            # No hay comandos pendientes (esto es normal)
            pass
        else:
            log(f"⚠️ Respuesta inesperada del servidor: {response.status_code}")
            
    except requests.exceptions.Timeout:
        log("⚠️ Timeout al consultar servidor")
    except requests.exceptions.ConnectionError:
        log("⚠️ Error de conexión con el servidor")
    except Exception as e:
        log(f"❌ Error en polling: {e}")

def enviar_resultado(comando: str, resultado: dict):
    """Envía el resultado de un comando al servidor"""
    try:
        headers = {
            "Authorization": f"Bearer {Config.AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "machine_id": Config.MACHINE_ID,
            "action": "report",
            "command": comando,
            "result": resultado,
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(
            Config.API_URL,
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            log(f"✅ Resultado enviado al servidor")
        else:
            log(f"⚠️ Error al enviar resultado: {response.status_code}")
            
    except Exception as e:
        log(f"❌ Error al enviar resultado: {e}")

def enviar_heartbeat():
    """Envía heartbeat periódico al servidor"""
    try:
        status = cmd_status()
        
        headers = {
            "Authorization": f"Bearer {Config.AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "machine_id": Config.MACHINE_ID,
            "action": "heartbeat",
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(
            Config.API_URL,
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            log("💓 Heartbeat enviado")
        
    except Exception as e:
        log(f"❌ Error en heartbeat: {e}")

# ==================== MAIN LOOP ====================
def main():
    """Bucle principal del agente"""
    log("="*80)
    log(f"🚀 AGENTE DE CONTROL REMOTO v{Config.VERSION}")
    log(f"   Máquina: {Config.MACHINE_ID}")
    log(f"   API URL: {Config.API_URL}")
    log(f"   Intervalo: {Config.POLL_INTERVAL}s")
    log("="*80)
    
    # Verificar configuración
    if Config.AUTH_TOKEN == "CAMBIAR_ESTO_POR_UN_TOKEN_SEGURO":
        log("⚠️ ADVERTENCIA: Debes cambiar el AUTH_TOKEN en la configuración")
    
    if "tu-dashboard.vercel.app" in Config.API_URL:
        log("⚠️ ADVERTENCIA: Debes cambiar la API_URL después de hacer deploy en Vercel")
    
    contador_heartbeat = 0
    
    try:
        while True:
            # Polling de comandos
            consultar_comandos()
            
            # Heartbeat cada 60 segundos (12 ciclos de 5 segundos)
            contador_heartbeat += 1
            if contador_heartbeat >= 12:
                enviar_heartbeat()
                contador_heartbeat = 0
            
            # Esperar antes del próximo poll
            time.sleep(Config.POLL_INTERVAL)
            
    except KeyboardInterrupt:
        log("\n⚠️ Agente detenido por el usuario")
    except Exception as e:
        log(f"❌ Error fatal: {e}")
        raise

if __name__ == "__main__":
    main()

