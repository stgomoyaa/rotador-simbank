"""
Rotador Automático de SIM Bank - Claro Pool
============================================
Cambia automáticamente los slots de todas las SIM banks cada 30 minutos
para evitar repetición de números de teléfono en SimClient.

Slots: 1-32 (luego vuelve al 1)
Puertos lógicos: 01-08
Total SIMs: 1024 (4 pools × 8 puertos × 32 slots)

Modos de operación:
1. Modo Normal: Rotación continua cada 30 minutos
2. Modo Activación Masiva: Procesa los 32 slots una sola vez sin interrupciones
"""

import time
import serial
import serial.tools.list_ports
import subprocess
import os
import threading
import getpass
import json
import argparse
import re
import sys
import ssl
import urllib.request
import shutil
import platform
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

# Instalación automática de dependencias si no están disponibles
try:
    import psycopg2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

try:
    import requests
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "psutil"])
    import requests
    import psutil

try:
    from PIL import ImageGrab, Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import ImageGrab, Image

try:
    import mss
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mss"])
        import mss
    except:
        mss = None

import base64
from io import BytesIO

console = Console()

# ==================== CONFIGURACIÓN ====================
class Settings:
    """Configuración centralizada del rotador"""
    # Version
    VERSION = "2.10.5"  # Mejoras: detección SIM Banks + taskkill robusto (previene abrir HeroSMS dos veces)
    REPO_URL = "https://github.com/stgomoyaa/rotador-simbank.git"
    
    # Agente de Control Remoto
    AGENTE_API_URL = "https://claro-pool-dashboard.vercel.app/api/commands"
    AGENTE_AUTH_TOKEN = "0l7TnHmWwOg3J4YBPhqZt9z1CDiMfLAk"
    AGENTE_POLL_INTERVAL = 10  # Segundos entre consultas
    
    # Slots
    SLOT_MIN = 1
    SLOT_MAX = 32
    
    # Tiempos (en minutos o segundos según contexto)
    INTERVALO_MINUTOS = 30
    TIEMPO_APLICAR_SLOT = 10  # Aumentado de 5 a 10 (switches mecánicos necesitan más tiempo)
    TIEMPO_ESTABILIZACION_FINAL = 15  # Aumentado de 8 a 15 (más tiempo para registro en red)
    TIEMPO_ANTES_SIMCLIENT = 3
    TIEMPO_SIMCLIENT_DETECTAR = 8
    
    # Reintentos y timeouts
    MAX_INTENTOS_SIM = 15
    MAX_INTENTOS_COMANDO_AT = 3
    MAX_INTENTOS_REGISTRO_RED = 15  # Nuevo: intentos para verificar registro en red
    MAX_INTENTOS_CAMBIO_SLOT = 3  # Nuevo: intentos para verificar cambio de ICCID
    TIMEOUT_SERIAL = 3
    BAUDRATE = 115200
    
    # Delays mejorados (fix para CME ERROR: 14)
    DELAY_ACCESO_SIM = 1.5  # Aumentado de 1 a 1.5 (reduce CME ERROR: 14)
    DELAY_ENTRE_COMANDOS_AT = 0.5  # Delay entre comandos AT consecutivos
    
    # Umbrales de alerta
    UMBRAL_ALERTA_SIMS = 0.70  # 70% de SIMs OK mínimo
    UMBRAL_PUERTO_INESTABLE = 3  # Fallos consecutivos antes de marcar puerto
    
    # Blacklist permanente de puertos defectuosos (fix para timeouts recurrentes)
    PUERTOS_BLACKLIST = []  # Puertos con fallas constantes (88% y 83% timeout)
    
    # Archivos
    LOG_FILE = "rotador_simbank.log"
    STATE_FILE = "rotador_state.json"
    METRICS_FILE = "rotador_metrics.json"
    LOCK_FILE = "rotador.lock"
    ICCIDS_HISTORY_FILE = "iccids_history.json"
    
    # Flags
    MODO_DRY_RUN = False  # Cambiar a True para probar sin hardware
    LOG_DIARIO = True  # Crear log por día
    ACTIVAR_SIMS_CLARO = True  # Activar SIMs Claro automáticamente después de cambiar slot
    MODO_ACTIVACION_MASIVA = True  # Modo por defecto: activar todas las 1024 SIMs sin abrir/cerrar programa
    
    # Activación de SIMs
    INTENTOS_ACTIVACION = 5  # Aumentado de 3 a 5 (más oportunidades)
    ESPERA_ENTRE_INTENTOS = 15  # Aumentado de 10 a 15 (más tiempo para SMS)
    ESPERA_DESPUES_ACTIVACION = 20  # Nuevo: tiempo de espera después de enviar USSD
    LOG_ACTIVACION = "log_activacion_rotador.txt"  # Log específico de activaciones
    
    # Base de datos PostgreSQL
    DB_ENABLED = True  # Habilitar integración con PostgreSQL
    DB_HOST = "crossover.proxy.rlwy.net"
    DB_NAME = "railway"
    DB_USER = "postgres"
    DB_PASSWORD = "QOHmELJXXFPmWBlyFmgtjLMvZfeoFaJa"
    DB_PORT = 43307
    DB_TABLE = "claro_numbers"
    
    # Auto-actualización
    CHECK_UPDATES = True  # Verificar actualizaciones al inicio
    AUTO_UPDATE = False  # Actualizar automáticamente (False = preguntar al usuario)

# Configuración de SIM Banks (auto-detectada o manual)
# IMPORTANTE: Los puertos lógicos de cada SIM Bank son siempre 01-08
# NOTA: Esta configuración se detecta automáticamente desde HeroSMS-Partners
# Si la auto-detección falla, se usa esta configuración por defecto
SIM_BANKS_DEFAULT = {
    "Pool1": {"com": "COM38", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 0},
    "Pool2": {"com": "COM37", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 8},
    "Pool3": {"com": "COM36", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 16},
    "Pool4": {"com": "COM35", "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"], "offset_slot": 24},
}

# Variable global que contendrá la configuración actual
SIM_BANKS = {}

# Variables globales
puertos_mapeados = {}
_mapeo_cargado = False
puertos_inestables = {}  # {puerto: {"fallos": N, "ultima_vez": datetime}}
contador_fallos_pool = {}  # {pool_name: contador}

# ==================== AUTO-DETECCIÓN DE SIM BANKS ====================
def detectar_simbanks_desde_log() -> dict:
    """
    Detecta automáticamente la configuración de SIM Banks desde el log de HeroSMS-Partners.
    
    MEJORAS v2.10.4:
    - Lee solo las últimas 300 líneas (configuración más reciente)
    - Sobrescribe duplicados (usa la última aparición)
    - Parsea timestamps para filtrar por fecha
    - Valida que los COM detectados existan
    - Mejor manejo de formatos: 'Pool #1', 'Pool 1', 'Pool1', '1', etc.
    
    Returns:
        dict: Diccionario con la configuración de SIM Banks detectada
              Formato: {"Pool1": {"com": "COM38", "puertos": [...], "offset_slot": 0}, ...}
              Retorna {} si no se pudo detectar
    """
    try:
        # Buscar archivo simBanks.txt en HeroSMS-Partners
        usuario = getpass.getuser()
        log_path = rf"C:\Users\{usuario}\AppData\Local\HeroSMS-Partners\app\log\simBanks.txt"
        
        if not os.path.exists(log_path):
            escribir_log(f"⚠️ No se encontró archivo de log: {log_path}")
            return {}
        
        escribir_log(f"📂 Detectando SIM Banks desde: {log_path}")
        
        # Leer las últimas 300 líneas del archivo (configuración más reciente)
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            todas_las_lineas = f.readlines()
        
        # Tomar solo las últimas 300 líneas
        ultimas_lineas = todas_las_lineas[-300:] if len(todas_las_lineas) > 300 else todas_las_lineas
        
        escribir_log(f"📊 Analizando últimas {len(ultimas_lineas)} líneas del log...")
        
        # Diccionario temporal para almacenar pools con timestamp
        pools_con_timestamp = {}
        
        # Parsear líneas
        for linea in ultimas_lineas:
            # Buscar líneas que contengan "Успешно добавлен" (Successfully added)
            if "Успешно добавлен" in linea:
                # Formato: "DD.MM.YY HH:MM:SS.mmm|COMXX 'Pool #1' : Успешно добавлен"
                
                # Extraer timestamp (si existe)
                timestamp_str = None
                match_timestamp = re.match(r'^(\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\.\d+\|', linea)
                if match_timestamp:
                    timestamp_str = match_timestamp.group(1)
                
                # Extraer COM port
                match_com = re.search(r'COM(\d+)', linea)
                if not match_com:
                    continue
                
                com_port = f"COM{match_com.group(1)}"
                
                # Extraer nombre del pool (entre comillas)
                match_pool = re.search(r"'([^']+)'", linea)
                if not match_pool:
                    continue
                
                pool_name_raw = match_pool.group(1)
                
                # Normalizar nombre del pool
                # Soportar: "Pool #1", "Pool 1", "Pool1", "1", etc.
                match_number = re.search(r'(\d+)', pool_name_raw)
                if not match_number:
                    continue
                
                pool_number = int(match_number.group(1))
                pool_name = f"Pool{pool_number}"
                
                # Guardar/actualizar pool (sobrescribe si ya existe = usa la última aparición)
                pools_con_timestamp[pool_name] = {
                    "com": com_port,
                    "puertos": ["01", "02", "03", "04", "05", "06", "07", "08"],
                    "offset_slot": (pool_number - 1) * 8,  # Offset automático: 0, 8, 16, 24
                    "numero": pool_number,
                    "timestamp": timestamp_str,
                    "pool_name_original": pool_name_raw
                }
                
                escribir_log(f"   🔍 Detectado: {pool_name} ({pool_name_raw}) -> {com_port} @ {timestamp_str or 'sin timestamp'}")
        
        if not pools_con_timestamp:
            escribir_log("⚠️ No se detectaron SIM Banks en las últimas líneas del log")
            escribir_log("   💡 Asegúrate de que HeroSMS-Partners tenga simbanks agregados recientemente")
            return {}
        
        # Validar que los COM ports existan en el sistema
        puertos_disponibles = listar_puertos_disponibles()
        escribir_log(f"🔌 Puertos COM disponibles en el sistema: {', '.join(puertos_disponibles)}")
        
        pools_validados = {}
        for pool_name, pool_data in pools_con_timestamp.items():
            com_port = pool_data["com"]
            
            if com_port in puertos_disponibles:
                # Remover campos temporales antes de guardar
                pools_validados[pool_name] = {
                    "com": pool_data["com"],
                    "puertos": pool_data["puertos"],
                    "offset_slot": pool_data["offset_slot"],
                    "numero": pool_data["numero"]
                }
                escribir_log(f"   ✅ {pool_name}: {com_port} validado (existe en sistema)")
            else:
                escribir_log(f"   ⚠️ {pool_name}: {com_port} NO encontrado en sistema (será ignorado)")
        
        if not pools_validados:
            escribir_log("❌ Ninguno de los COM detectados existe en el sistema")
            escribir_log("   💡 Verifica las conexiones USB de los simbanks")
            return {}
        
        # Ordenar por número de pool
        pools_ordenados = dict(sorted(pools_validados.items(), key=lambda x: x[1]['numero']))
        
        # Remover campo 'numero' que solo usamos para ordenar
        for pool_config in pools_ordenados.values():
            del pool_config['numero']
        
        # Mostrar configuración final detectada
        escribir_log(f"✅ SIM Banks detectados y validados: {len(pools_ordenados)}")
        for pool_name, config in pools_ordenados.items():
            escribir_log(f"   {pool_name}: {config['com']} (offset={config['offset_slot']})")
        
        return pools_ordenados
        
    except Exception as e:
        escribir_log(f"❌ Error al detectar SIM Banks: {e}")
        import traceback
        escribir_log(f"   Detalles: {traceback.format_exc()}")
        return {}

def guardar_simbanks_config(config: dict):
    """Guarda la configuración de SIM Banks detectada en un archivo JSON"""
    try:
        config_file = "simbanks_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        escribir_log(f"💾 Configuración de SIM Banks guardada en: {config_file}")
    except Exception as e:
        escribir_log(f"⚠️ Error al guardar configuración: {e}")

def cargar_simbanks_config() -> dict:
    """Carga la configuración de SIM Banks desde el archivo JSON si existe"""
    try:
        config_file = "simbanks_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            escribir_log(f"📂 Configuración de SIM Banks cargada desde: {config_file}")
            return config
    except Exception as e:
        escribir_log(f"⚠️ Error al cargar configuración guardada: {e}")
    return {}

def inicializar_simbanks():
    """
    Inicializa la configuración de SIM Banks usando auto-detección o configuración por defecto.
    
    Prioridad:
    1. Intentar detectar desde el log de HeroSMS-Partners
    2. Si falla, cargar desde archivo guardado (simbanks_config.json)
    3. Si falla, usar configuración por defecto (SIM_BANKS_DEFAULT)
    """
    global SIM_BANKS
    
    console.print("[cyan]🔍 Inicializando configuración de SIM Banks...[/cyan]")
    
    # 1. Intentar auto-detección desde log
    config_detectada = detectar_simbanks_desde_log()
    
    if config_detectada:
        SIM_BANKS = config_detectada
        guardar_simbanks_config(config_detectada)
        console.print("[green]✅ SIM Banks detectados automáticamente desde HeroSMS-Partners[/green]")
        return
    
    # 2. Intentar cargar desde archivo guardado
    config_guardada = cargar_simbanks_config()
    if config_guardada:
        SIM_BANKS = config_guardada
        console.print("[yellow]⚠️ Usando configuración guardada (no se pudo auto-detectar)[/yellow]")
        return
    
    # 3. Usar configuración por defecto
    SIM_BANKS = SIM_BANKS_DEFAULT
    console.print("[yellow]⚠️ Usando configuración por defecto (no se pudo auto-detectar ni cargar)[/yellow]")
    console.print("[yellow]   Si los COM ports son incorrectos, edita SIM_BANKS_DEFAULT en el script[/yellow]")

# ==================== DECORADORES Y UTILIDADES ====================
def medir_tiempo(func):
    """Decorador para medir tiempo de ejecución de funciones"""
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fin = time.time()
        duracion = fin - inicio
        escribir_log(f"⏱️ {func.__name__} completado en {duracion:.2f}s")
        return resultado
    return wrapper

def guardar_snapshot(slot: int, iteracion: int, datos: dict):
    """Guarda snapshot completo de una rotación"""
    try:
        # Crear directorio de snapshots si no existe
        snapshot_dir = "snapshots"
        if not os.path.exists(snapshot_dir):
            os.makedirs(snapshot_dir)
        
        # Crear subdirectorio por fecha
        fecha = datetime.now().strftime("%Y-%m-%d")
        fecha_dir = os.path.join(snapshot_dir, fecha)
        if not os.path.exists(fecha_dir):
            os.makedirs(fecha_dir)
        
        # Nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%H-%M-%S")
        filename = f"snapshot_slot{slot:02d}_iter{iteracion}_{timestamp}.json"
        filepath = os.path.join(fecha_dir, filename)
        
        # Agregar metadatos
        datos["metadata"] = {
            "slot": slot,
            "iteracion": iteracion,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": Settings.VERSION
        }
        
        # Guardar
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        
        escribir_log(f"📸 Snapshot guardado: {filename}")
        
    except Exception as e:
        escribir_log(f"⚠️ Error al guardar snapshot: {e}")

# ==================== FUNCIONES DE LOCK (ANTI-DOBLE INSTANCIA) ====================
def crear_lock():
    """Crea archivo lock para evitar múltiples instancias"""
    if os.path.exists(Settings.LOCK_FILE):
        console.print("[red]❌ Ya hay una instancia del rotador ejecutándose[/red]")
        console.print(f"[red]   Si estás seguro de que no hay otra instancia, elimina: {Settings.LOCK_FILE}[/red]")
        raise SystemExit(1)
    try:
        with open(Settings.LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        console.print(f"[red]❌ Error al crear lock file: {e}[/red]")
        raise SystemExit(1)

def borrar_lock():
    """Elimina el archivo lock"""
    try:
        if os.path.exists(Settings.LOCK_FILE):
            os.remove(Settings.LOCK_FILE)
    except Exception as e:
        console.print(f"[yellow]⚠️ Error al borrar lock: {e}[/yellow]")

# ==================== FUNCIONES DE LOG Y ESTADO ====================
def escribir_log(mensaje):
    """Escribe en el archivo de log con timestamp (principal + diario)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {mensaje}\n"
    
    # Log principal
    try:
        with open(Settings.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception as e:
        pass  # No bloquear ejecución por error de log
    
    # Log diario (si está activado)
    if Settings.LOG_DIARIO:
        try:
            fecha = datetime.now().strftime("%Y-%m-%d")
            log_diario = f"rotador_simbank_{fecha}.log"
            with open(log_diario, "a", encoding="utf-8") as f:
                f.write(linea)
        except Exception as e:
            pass
    
    console.print(mensaje)

def cargar_estado():
    """Carga el estado persistido (slot actual e iteración)"""
    try:
        if os.path.exists(Settings.STATE_FILE):
            with open(Settings.STATE_FILE, "r", encoding="utf-8") as f:
                estado = json.load(f)
                return estado.get("slot_actual", Settings.SLOT_MIN), estado.get("iteracion", 1)
        else:
            return Settings.SLOT_MIN, 1
    except Exception as e:
        escribir_log(f"⚠️ Error al cargar estado: {e}. Iniciando desde slot 1")
        return Settings.SLOT_MIN, 1

def validar_simbanks():
    """Valida que los COM de los SIM Banks existan antes de iniciar"""
    puertos_disponibles = listar_puertos_disponibles()
    coms_simbank = {config["com"] for config in SIM_BANKS.values()}
    
    faltantes = [c for c in coms_simbank if c not in puertos_disponibles]
    
    if faltantes:
        console.print("[red]❌ Error: No se detectan estos COM de SIM Bank:[/red]")
        for c in faltantes:
            console.print(f"[red]   - {c}[/red]")
        escribir_log(f"❌ COM de SIM Bank no detectados: {faltantes}")
        console.print("[yellow]⚠️ El script continuará, pero es probable que falle.[/yellow]")
        console.print("[yellow]   Verifica las conexiones y configuración en SIM_BANKS[/yellow]")
        return False
    else:
        escribir_log("✅ Todos los COM de SIM Bank fueron detectados correctamente")
        console.print("[green]✅ Todos los COM de SIM Bank detectados[/green]")
        return True

def guardar_estado(slot_actual, iteracion):
    """Guarda el estado actual en archivo JSON"""
    try:
        estado = {
            "slot_actual": slot_actual,
            "iteracion": iteracion,
            "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": Settings.VERSION
        }
        with open(Settings.STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
    except Exception as e:
        escribir_log(f"⚠️ Error al guardar estado: {e}")

def actualizar_metricas(slot: int, iteracion: int, sims_listas: int, total_modems: int, iccids_unicos: int, comandos_ok: int, comandos_error: int):
    """Actualiza métricas acumuladas en JSON"""
    try:
        # Cargar métricas existentes
        data = {
            "total_rotaciones": 0,
            "total_sims_ok": 0,
            "total_modems_contados": 0,
            "total_iccids_unicos": 0,
            "total_comandos_ok": 0,
            "total_comandos_error": 0,
            "ultima_rotacion": None,
            "version": Settings.VERSION
        }
        
        if os.path.exists(Settings.METRICS_FILE):
            try:
                with open(Settings.METRICS_FILE, "r", encoding="utf-8") as f:
                    data.update(json.load(f))
            except:
                pass
        
        # Actualizar métricas
        data["total_rotaciones"] += 1
        data["total_sims_ok"] += sims_listas
        data["total_modems_contados"] += total_modems
        data["total_iccids_unicos"] += iccids_unicos
        data["total_comandos_ok"] += comandos_ok
        data["total_comandos_error"] += comandos_error
        data["ultima_rotacion"] = {
            "slot": slot,
            "iteracion": iteracion,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sims_listas": sims_listas,
            "total_modems": total_modems,
            "iccids_unicos": iccids_unicos
        }
        
        # Guardar
        with open(Settings.METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        escribir_log(f"⚠️ Error al actualizar métricas: {e}")

def guardar_historial_iccids(slot: int, iteracion: int, iccids_verificados: dict):
    """Guarda historial de ICCIDs detectados por rotación"""
    try:
        # Cargar historial existente
        historial = {}
        if os.path.exists(Settings.ICCIDS_HISTORY_FILE):
            try:
                with open(Settings.ICCIDS_HISTORY_FILE, "r", encoding="utf-8") as f:
                    historial = json.load(f)
            except:
                pass
        
        # Agregar entrada actual
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clave_rotacion = f"slot_{slot:02d}_iter_{iteracion}"
        
        historial[clave_rotacion] = {
            "timestamp": timestamp,
            "slot": slot,
            "iteracion": iteracion,
            "iccids_por_puerto": iccids_verificados,
            "total_unicos": len(set(iccids_verificados.values()))
        }
        
        # Mantener solo las últimas 100 rotaciones
        if len(historial) > 100:
            claves_ordenadas = sorted(historial.keys())
            for clave in claves_ordenadas[:-100]:
                del historial[clave]
        
        # Guardar
        with open(Settings.ICCIDS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        escribir_log(f"⚠️ Error al guardar historial ICCIDs: {e}")

# ==================== FUNCIONES DE AUTO-ACTUALIZACIÓN ====================
def obtener_version_remota() -> tuple:
    """Obtiene la versión remota del script desde GitHub.
    Retorna (exito, version, url_descarga).
    """
    try:
        # Extraer usuario y repo de REPO_URL
        # Formato: https://github.com/USUARIO/REPO.git
        import re
        match = re.search(r'github\.com/([^/]+)/([^/]+)\.git', Settings.REPO_URL)
        if not match:
            return False, Settings.VERSION, ""
        
        usuario, repo = match.groups()
        
        # URL de la API de GitHub
        api_url = f"https://api.github.com/repos/{usuario}/{repo}/contents/RotadorSimBank.py"
        
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'RotadorSimBank-Updater')
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            data = json.loads(response.read().decode())
            download_url = data.get('download_url')
            
            if not download_url:
                return False, Settings.VERSION, ""
            
            # Descargar el contenido del script
            with urllib.request.urlopen(download_url, timeout=10, context=ctx) as file_response:
                contenido = file_response.read().decode('utf-8')
                
                # Buscar la versión en el contenido
                match = re.search(r'VERSION = "([^"]+)"', contenido)
                
                if match:
                    version_remota = match.group(1)
                    return True, version_remota, download_url
                    
        return False, Settings.VERSION, ""
        
    except Exception as e:
        escribir_log(f"⚠️ Error al verificar actualizaciones: {e}")
        return False, Settings.VERSION, ""

def comparar_versiones(v1: str, v2: str) -> int:
    """Compara dos versiones en formato X.Y.Z.
    Retorna: 1 si v1 > v2, -1 si v1 < v2, 0 si son iguales.
    """
    try:
        partes1 = [int(x) for x in v1.split('.')]
        partes2 = [int(x) for x in v2.split('.')]
        
        for p1, p2 in zip(partes1, partes2):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        
        return 0
    except:
        return 0

def verificar_actualizacion() -> tuple:
    """Verifica si hay una actualización disponible.
    Retorna (hay_actualizacion, version_remota).
    """
    try:
        console.print("[cyan]🔍 Verificando actualizaciones...[/cyan]")
        
        exito, version_remota, _ = obtener_version_remota()
        
        if not exito:
            console.print("[yellow]⚠️ No se pudo verificar actualizaciones.[/yellow]")
            return False, Settings.VERSION
        
        # Comparar versiones
        if comparar_versiones(version_remota, Settings.VERSION) > 0:
            console.print(f"[green]🆕 ¡Nueva versión disponible: v{version_remota} (actual: v{Settings.VERSION})![/green]")
            return True, version_remota
        else:
            console.print(f"[green]✅ Estás usando la versión más reciente (v{Settings.VERSION})[/green]")
            return False, Settings.VERSION
            
    except Exception as e:
        console.print(f"[yellow]⚠️ Error al verificar actualizaciones: {e}[/yellow]")
        return False, Settings.VERSION

def descargar_actualizacion(url: str) -> bool:
    """Descarga la nueva versión del script.
    Retorna True si se descargó correctamente.
    """
    try:
        script_actual = os.path.abspath(__file__)
        script_backup = f"{script_actual}.backup"
        script_temp = f"{script_actual}.new"
        
        # Hacer backup del script actual
        console.print("[cyan]💾 Creando respaldo...[/cyan]")
        shutil.copy2(script_actual, script_backup)
        
        # Descargar nueva versión
        console.print("[cyan]📥 Descargando actualización...[/cyan]")
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'RotadorSimBank-Updater')
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            contenido = response.read()
            
            # Guardar en archivo temporal
            with open(script_temp, 'wb') as f:
                f.write(contenido)
        
        # Reemplazar el script actual
        console.print("[cyan]🔄 Aplicando actualización...[/cyan]")
        shutil.move(script_temp, script_actual)
        
        console.print("[green]✅ Script actualizado exitosamente![/green]")
        console.print("[yellow]🔄 Reiniciando con la nueva versión...[/yellow]\n")
        
        # Reiniciar el script (maneja rutas con espacios correctamente)
        time.sleep(2)
        
        # Si estamos corriendo como agente (servicio), reiniciar el servicio NSSM
        if "--agente" in sys.argv:
            try:
                console.print("[cyan]📦 Detectado modo agente - Reiniciando servicio NSSM...[/cyan]")
                nssm_path = os.path.join(os.getcwd(), "nssm.exe")
                if os.path.exists(nssm_path):
                    # Reiniciar el servicio NSSM
                    subprocess.Popen([nssm_path, "restart", "AgenteRotadorSimBank"])
                    time.sleep(2)
                    sys.exit(0)
                else:
                    console.print("[yellow]⚠️  NSSM no encontrado - Reiniciando proceso Python directamente[/yellow]")
            except Exception as e:
                console.print(f"[yellow]⚠️  Error reiniciando servicio: {e}[/yellow]")
        
        # Fallback: reiniciar proceso Python directamente
        import subprocess
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error al descargar actualización: {e}[/red]")
        
        # Restaurar backup si existe
        if os.path.exists(script_backup):
            console.print("[yellow]🔙 Restaurando versión anterior...[/yellow]")
            try:
                shutil.copy2(script_backup, script_actual)
                console.print("[green]✅ Versión anterior restaurada.[/green]")
            except:
                pass
        
        return False
    finally:
        # Limpiar archivos temporales
        for temp_file in [script_backup, script_temp]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

def actualizar_script() -> bool:
    """Actualiza el script a la última versión disponible.
    Retorna True si se actualizó correctamente.
    """
    try:
        exito, version_remota, url = obtener_version_remota()
        
        if not exito or not url:
            console.print("[red]❌ No se pudo obtener la información de actualización.[/red]")
            return False
        
        return descargar_actualizacion(url)
        
    except Exception as e:
        console.print(f"[red]❌ Error al actualizar: {e}[/red]")
        return False

def verificar_y_actualizar():
    """Función principal que verifica y actualiza el script si es necesario."""
    if not Settings.CHECK_UPDATES:
        return
    
    try:
        hay_actualizacion, version_remota = verificar_actualizacion()
        
        if hay_actualizacion:
            if Settings.AUTO_UPDATE:
                console.print(f"[yellow]🔄 Actualizando automáticamente a v{version_remota}...[/yellow]")
                actualizar_script()
            else:
                console.print(f"\n[bold yellow]¿Deseas actualizar a v{version_remota}? (s/n):[/bold yellow] ", end="")
                respuesta = input().strip().lower()
                if respuesta == 's':
                    actualizar_script()
                else:
                    console.print("[yellow]Actualización omitida. Continuando con v{Settings.VERSION}...[/yellow]\n")
        
        time.sleep(1)
            
    except Exception as e:
        console.print(f"[yellow]⚠️ Error en el sistema de actualización: {e}[/yellow]")
        console.print("[yellow]Continuando con la ejecución normal...[/yellow]\n")
        time.sleep(1)

# ==================== FUNCIONES DE BASE DE DATOS ====================
def conectar_db():
    """Establece conexión con la base de datos PostgreSQL."""
    if not Settings.DB_ENABLED:
        return None
    
    try:
        conn = psycopg2.connect(
            host=Settings.DB_HOST,
            database=Settings.DB_NAME,
            user=Settings.DB_USER,
            password=Settings.DB_PASSWORD,
            port=Settings.DB_PORT
        )
        return conn
    except Exception as e:
        escribir_log(f"❌ Error al conectar con la base de datos: {e}")
        return None

def crear_tabla_db():
    """Crea la tabla en PostgreSQL si no existe."""
    if not Settings.DB_ENABLED:
        return
    
    try:
        conn = conectar_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {Settings.DB_TABLE} (
                id SERIAL PRIMARY KEY,
                iccid VARCHAR(20) UNIQUE NOT NULL,
                numero_telefono VARCHAR(15) NOT NULL,
                fecha_activacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        escribir_log(f"✅ Tabla {Settings.DB_TABLE} verificada/creada en PostgreSQL")
        
    except Exception as e:
        escribir_log(f"⚠️ Error al crear tabla en base de datos: {e}")

def guardar_numero_db(iccid: str, numero: str, puerto: str) -> bool:
    """Guarda o actualiza un número en la base de datos PostgreSQL.
    Retorna True si se guardó correctamente.
    """
    if not Settings.DB_ENABLED:
        return False
    
    try:
        conn = conectar_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Verificar si el ICCID ya existe
        cursor.execute(f"SELECT numero_telefono FROM {Settings.DB_TABLE} WHERE iccid = %s", (iccid,))
        registro_existente = cursor.fetchone()
        
        if registro_existente:
            # Si existe, actualizar con el nuevo número
            numero_anterior = registro_existente[0]
            cursor.execute(
                f"UPDATE {Settings.DB_TABLE} SET numero_telefono = %s WHERE iccid = %s",
                (numero, iccid)
            )
            log_activacion(f"🔄 [{puerto}] ICCID {iccid} actualizado en DB: {numero_anterior} → {numero}")
        else:
            # Si no existe, insertar como nuevo registro
            cursor.execute(
                f"INSERT INTO {Settings.DB_TABLE} (iccid, numero_telefono, fecha_activacion) VALUES (%s, %s, %s)",
                (iccid, numero, fecha_actual)
            )
            log_activacion(f"✅ [{puerto}] Número {numero} e ICCID {iccid} guardados en DB")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        log_activacion(f"❌ [{puerto}] Error al guardar en base de datos: {e}")
        return False

def exportar_base_datos_completa() -> bool:
    """Exporta toda la base de datos PostgreSQL al archivo local."""
    if not Settings.DB_ENABLED:
        console.print("[yellow]⚠️ Base de datos deshabilitada en configuración[/yellow]")
        return False
    
    try:
        console.print("[cyan]📥 Exportando listado completo desde la base de datos...[/cyan]")
        escribir_log("📥 Exportando base de datos a archivo local...")
        
        conn = conectar_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Obtener todos los registros
        cursor.execute(f"SELECT numero_telefono, iccid, fecha_activacion FROM {Settings.DB_TABLE} ORDER BY fecha_activacion")
        registros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Escribir al archivo (sobrescribir)
        with open("listadonumeros_claro.txt", "w", encoding="utf-8") as archivo:
            for numero, iccid, fecha in registros:
                archivo.write(f"{numero}={iccid}\n")
        
        console.print(f"[green]✅ Exportados {len(registros)} registros desde PostgreSQL al archivo local[/green]")
        escribir_log(f"✅ Exportados {len(registros)} registros desde base de datos")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error al exportar base de datos: {e}[/red]")
        escribir_log(f"❌ Error al exportar base de datos: {e}")
        return False

def limpiar_listado(path: str = "listadonumeros_claro.txt") -> bool:
    """Elimina duplicados exactos y duplicados por número o ICCID.
    Conserva la primera aparición.
    """
    archivo = Path(path)
    if not archivo.exists():
        console.print(f"[yellow]⚠️ No existe {archivo}; nada que limpiar.[/yellow]")
        return False

    try:
        # Leer todas las líneas
        with archivo.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        # Eliminar duplicados exactos
        unique_lines = list(dict.fromkeys(lines))

        seen_numbers, seen_iccids = set(), set()
        cleaned = []

        for raw in unique_lines:
            line = raw.strip()
            if not line or "=" not in line:
                continue
            
            parts = line.split("=", 1)
            if len(parts) != 2:
                continue
            
            number, iccid = parts

            # ¿Ya vimos el mismo número o ICCID?
            if number in seen_numbers or iccid in seen_iccids:
                continue

            seen_numbers.add(number)
            seen_iccids.add(iccid)
            cleaned.append(f"{number}={iccid}")

        # Escribir el archivo limpio
        with archivo.open("w", encoding="utf-8") as f:
            for ln in cleaned:
                f.write(ln + "\n")

        console.print(f"[green]✅ Limpieza completa: {len(lines)} → {len(cleaned)} líneas.[/green]")
        escribir_log(f"✅ Archivo limpiado: {len(lines)} → {len(cleaned)} líneas")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error al limpiar archivo: {e}[/red]")
        return False

# ==================== FUNCIONES DE MAPEO DE PUERTOS ====================
def cargar_mapeo_puertos():
    """Lee 'ports.txt' desde SimClient y retorna dict {COMx: numero_logico}."""
    global _mapeo_cargado, puertos_mapeados
    usuario = getpass.getuser()
    path = rf"C:\Users\{usuario}\AppData\Local\HeroSMS-Partners\app\ports.txt"
    port_map = {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "-" in line:
                    left, right = line.strip().split("-")
                    port_map[f"COM{right}"] = left
        
        if not _mapeo_cargado:
            escribir_log(f"✅ Mapeo de puertos cargado: {len(port_map)} puertos configurados")
            _mapeo_cargado = True
            
    except FileNotFoundError:
        if not _mapeo_cargado:
            escribir_log(f"⚠️ Archivo ports.txt no encontrado. Se usará mapeo directo.")
            _mapeo_cargado = True
    except Exception as e:
        if not _mapeo_cargado:
            escribir_log(f"⚠️ Error al cargar mapeo: {e}")
            _mapeo_cargado = True
    
    puertos_mapeados = port_map
    return port_map

def listar_puertos_disponibles():
    """Lista todos los puertos COM disponibles"""
    puertos = serial.tools.list_ports.comports()
    lista_puertos = [puerto.device for puerto in puertos]
    escribir_log(f"🔍 Puertos detectados: {lista_puertos}")
    return lista_puertos

def obtener_puerto_numerado(puerto_real):
    """Obtiene el número lógico de un puerto COM"""
    return (
        f"#{puertos_mapeados[puerto_real]}"
        if puerto_real in puertos_mapeados
        else puerto_real
    )

# ==================== FUNCIONES DE ACTIVACIÓN DE SIMS ====================
def obtener_operador(iccid: str) -> str:
    """Detecta el operador según el ICCID"""
    if not iccid:
        return "Desconocido"
    if iccid.startswith("895603"):
        return "Claro"
    return "Desconocido"

def log_activacion(mensaje: str):
    """Log específico para proceso de activación"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {mensaje}\n"
    try:
        with open(Settings.LOG_ACTIVACION, "a", encoding="utf-8") as f:
            f.write(linea)
    except:
        pass
    escribir_log(mensaje)

def borrar_mensajes_modem(puerto: str) -> bool:
    """Borra todos los SMS del módem (memoria del módem y SIM)"""
    if Settings.MODO_DRY_RUN:
        log_activacion(f"[DRY RUN] [{puerto}] Mensajes borrados")
        return True
    
    try:
        # Borrar todos los mensajes (flag 4 = todos los mensajes)
        respuesta = enviar_comando(puerto, "AT+CMGD=1,4", espera=2)
        if "OK" in respuesta or respuesta:
            log_activacion(f"🗑️ [{puerto}] Mensajes borrados del módem")
            return True
        else:
            log_activacion(f"⚠️ [{puerto}] No se pudieron borrar mensajes")
            return False
    except Exception as e:
        log_activacion(f"❌ [{puerto}] Error al borrar mensajes: {e}")
        return False

def leer_contacto_myphone(puerto: str) -> str:
    """Lee el contacto 'myphone' guardado en la SIM para verificar si ya está activada"""
    if Settings.MODO_DRY_RUN:
        return None
    
    try:
        # Delay antes de acceder a SIM (fix para CME ERROR: 14 - SIM busy)
        time.sleep(Settings.DELAY_ACCESO_SIM)
        
        # Seleccionar memoria de la SIM
        enviar_comando(puerto, 'AT+CPBS="SM"', espera=0.5)
        
        # Leer el contacto en posición 1 (donde guardamos 'myphone')
        respuesta = enviar_comando(puerto, 'AT+CPBR=1', espera=1)
        
        if not respuesta:
            return None
        
        # Buscar el número en la respuesta
        # Formato: +CPBR: 1,"56999123456",129,"myphone"
        match = re.search(r'\+CPBR:\s*1,"(\+?569\d{8})"', respuesta)
        if match:
            numero = match.group(1)
            # Asegurar formato 569XXXXXXXX
            if numero.startswith('+'):
                numero = numero[1:]
            log_activacion(f"📱 [{puerto}] Ya tiene número guardado: {numero}")
            return numero
        
        return None
        
    except Exception as e:
        log_activacion(f"❌ [{puerto}] Error leyendo contacto myphone: {e}")
        return None

def activar_sim_claro(puerto: str, iccid: str) -> bool:
    """Activa una SIM Claro enviando USSD *103# con retry para error de red"""
    if Settings.MODO_DRY_RUN:
        log_activacion(f"[DRY RUN] [{puerto}] Activación Claro simulada")
        return True
    
    operador = obtener_operador(iccid)
    if operador != "Claro":
        log_activacion(f"⏭️  [{puerto}] No es Claro, saltando activación")
        return True
    
    try:
        log_activacion(f"📞 [{puerto}] Enviando *103# para activación Claro")
        
        # Retry para CME ERROR: 30 (No network service)
        for intento_red in range(3):
            respuesta = enviar_comando_resiliente(puerto, 'AT+CUSD=1,"*103#",15', intentos=2)
            
            # Si hay error de red, esperar y reintentar
            if "+CME ERROR: 30" in respuesta:
                if intento_red < 2:
                    log_activacion(f"⚠️ [{puerto}] Sin servicio de red, reintentando en 5s... ({intento_red + 1}/3)")
                    time.sleep(5)
                    continue
                else:
                    log_activacion(f"❌ [{puerto}] Sin servicio de red tras 3 intentos")
                    return False
            
            # Esperar respuesta USSD
            time.sleep(3)
            
            if "OK" in respuesta or respuesta:
                log_activacion(f"✅ [{puerto}] Comando de activación enviado")
                return True
            else:
                log_activacion(f"⚠️ [{puerto}] Respuesta inesperada: {respuesta[:50]}")
                return False
            
    except Exception as e:
        log_activacion(f"❌ [{puerto}] Error en activación: {e}")
        return False

def leer_numero_sms(puerto: str, iccid: str) -> str:
    """Lee SMS para obtener el número de teléfono"""
    if Settings.MODO_DRY_RUN:
        return "569XXXXXXXX"
    
    operador = obtener_operador(iccid)
    if operador != "Claro":
        return None
    
    try:
        # Configurar modo texto
        enviar_comando(puerto, "AT+CMGF=1", espera=0.5)
        
        # Patrones para detectar números
        patrones_numeros = [
            r"Tu numero es (\d+)",
            r"\b(\d{9})\b",
            r"\+569 ?(\d{4} ?\d{4})",
            r"569 ?(\d{4} ?\d{4})",
            r"\+569(\d{8})",
            r"569(\d{8})",
            r"\b(?:tu\s*n[uú]mero\s*es)\s*([\d\s]+)",
        ]
        
        # Leer SMS de diferentes memorias
        memorias = ["SM", "ME"]
        numero = None
        
        for memoria in memorias:
            enviar_comando(puerto, f'AT+CPMS="{memoria}"', espera=0.5)
            respuesta = enviar_comando(puerto, 'AT+CMGL="ALL"', espera=2)
            
            if not respuesta:
                continue
            
            # Buscar número en SMS
            for patron in patrones_numeros:
                match = re.search(patron, respuesta, re.IGNORECASE)
                if match:
                    numero_extraido = match.group(1).replace(" ", "")
                    numero = f"569{numero_extraido[-8:]}"
                    log_activacion(f"📱 [{puerto}] Número encontrado: {numero}")
                    return numero
            
            # Buscar en URL de Claro
            match_url = re.search(r"https://fif\.clarovtrcloud\.com/aod/form\?t=(\d+)", respuesta)
            if match_url:
                numero = f"569{match_url.group(1)[-8:]}"
                log_activacion(f"📱 [{puerto}] Número encontrado en URL: {numero}")
                return numero
        
        return None
        
    except Exception as e:
        log_activacion(f"❌ [{puerto}] Error leyendo SMS: {e}")
        return None

def guardar_numero_en_sim(puerto: str, numero: str, iccid: str) -> bool:
    """Guarda el número en la SIM, en archivo local y en base de datos PostgreSQL"""
    if Settings.MODO_DRY_RUN:
        log_activacion(f"[DRY RUN] [{puerto}] Número {numero} guardado")
        return True
    
    try:
        # 1. Guardar en archivo local
        with open("listadonumeros_claro.txt", "a", encoding="utf-8") as f:
            f.write(f"{numero}={iccid}\n")
        log_activacion(f"💾 [{puerto}] Guardado en archivo: {numero}={iccid}")
        
        # 2. Guardar en la SIM como "myphone"
        log_activacion(f"📲 [{puerto}] Guardando {numero} en la SIM...")
        enviar_comando(puerto, 'AT+CPBS="SM"', espera=0.5)
        comando_guardar = f'AT+CPBW=1,"{numero}",129,"myphone"'
        respuesta = enviar_comando(puerto, comando_guardar, espera=1)
        
        sim_ok = False
        if "OK" in respuesta or respuesta:
            log_activacion(f"✅ [{puerto}] Número guardado en SIM como 'myphone'")
            sim_ok = True
        else:
            log_activacion(f"⚠️ [{puerto}] Error al guardar en SIM")
        
        # 3. Guardar en base de datos PostgreSQL
        if Settings.DB_ENABLED:
            db_ok = guardar_numero_db(iccid, numero, puerto)
            if not db_ok:
                log_activacion(f"⚠️ [{puerto}] No se pudo guardar en base de datos, pero está en archivo local")
        
        return sim_ok
            
    except Exception as e:
        log_activacion(f"❌ [{puerto}] Error guardando número: {e}")
        return False

@medir_tiempo
def procesar_activacion_sim(puerto: str) -> dict:
    """Proceso completo de activación de una SIM"""
    resultado = {
        "puerto": puerto,
        "iccid": None,
        "numero": None,
        "activado": False,
        "intentos": 0
    }
    
    try:
        # 1. Obtener ICCID (verifica que SIM responde - fix para CMS ERROR: 500)
        iccid = obtener_iccid_modem(puerto)
        if not iccid:
            log_activacion(f"❌ [{puerto}] No se pudo obtener ICCID")
            return resultado
        
        resultado["iccid"] = iccid
        operador = obtener_operador(iccid)
        
        if operador != "Claro":
            log_activacion(f"⏭️  [{puerto}] {operador} - No requiere activación")
            resultado["activado"] = True
            return resultado
        
        # 2. VERIFICAR SI YA TIENE NÚMERO GUARDADO EN "myphone"
        numero_existente = leer_contacto_myphone(puerto)
        if numero_existente:
            log_activacion(f"✅ [{puerto}] SIM ya activada con número: {numero_existente}")
            resultado["numero"] = numero_existente
            resultado["activado"] = True
            resultado["intentos"] = 0  # No necesitó intentos, ya estaba activada
            return resultado
        
        # 3. BORRAR MENSAJES DEL MÓDEM (ahora que SIM está confirmada como lista)
        # Esto previene leer SMS de la SIM anterior
        borrar_mensajes_modem(puerto)
        
        # 4. VERIFICAR REGISTRO EN RED (CRÍTICO para activación exitosa)
        log_activacion(f"🔍 [{puerto}] Esperando registro en red antes de activar...")
        if not esperar_registro_red(puerto, max_intentos=15):
            log_activacion(f"❌ [{puerto}] No se pudo registrar en red - Saltando activación")
            resultado["intentos"] = 0
            return resultado
        
        # 5. VERIFICAR SEÑAL (opcional, para diagnóstico)
        verificar_intensidad_senal(puerto)
        
        # 6. Intentar activación
        for intento in range(Settings.INTENTOS_ACTIVACION):
            resultado["intentos"] = intento + 1
            log_activacion(f"🔄 [{puerto}] Intento {intento + 1}/{Settings.INTENTOS_ACTIVACION}")
            
            # Activar SIM
            if not activar_sim_claro(puerto, iccid):
                time.sleep(Settings.ESPERA_ENTRE_INTENTOS)
                continue
            
            # Esperar a que llegue SMS (aumentado para dar más tiempo)
            log_activacion(f"⏳ [{puerto}] Esperando {Settings.ESPERA_DESPUES_ACTIVACION}s para recibir SMS...")
            time.sleep(Settings.ESPERA_DESPUES_ACTIVACION)
            
            # Leer número
            numero = leer_numero_sms(puerto, iccid)
            if numero:
                resultado["numero"] = numero
                resultado["activado"] = True
                
                # Guardar número
                guardar_numero_en_sim(puerto, numero, iccid)
                log_activacion(f"🎉 [{puerto}] Activación exitosa: {numero}")
                return resultado
            
            # Si no se obtuvo número, reintentar
            if intento < Settings.INTENTOS_ACTIVACION - 1:
                log_activacion(f"⏳ [{puerto}] Esperando {Settings.ESPERA_ENTRE_INTENTOS}s antes de reintentar...")
                time.sleep(Settings.ESPERA_ENTRE_INTENTOS)
        
        log_activacion(f"❌ [{puerto}] No se obtuvo número tras {Settings.INTENTOS_ACTIVACION} intentos")
        return resultado
        
    except Exception as e:
        log_activacion(f"❌ [{puerto}] Error en proceso de activación: {e}")
        return resultado

# ==================== FUNCIONES DE PUERTO SERIAL ====================
def cerrar_puertos_serial():
    """Cierra todos los puertos serial abiertos usando hilos"""
    console.print("[yellow]🔒 Cerrando todos los puertos serial...[/yellow]")
    
    def cerrar_puerto(puerto):
        try:
            ser = serial.Serial(puerto)
            if ser.is_open:
                ser.close()
                escribir_log(f"✅ Puerto cerrado: {puerto}")
        except:
            pass
    
    hilos = []
    for p in serial.tools.list_ports.comports():
        hilo = threading.Thread(target=cerrar_puerto, args=(p.device,))
        hilo.start()
        hilos.append(hilo)
    
    for h in hilos:
        h.join()
    
    console.print("[green]✅ Puertos cerrados[/green]")
    time.sleep(2)

def enviar_comando(puerto: str, comando: str, espera: float = 1) -> str:
    """Envía un comando AT al puerto especificado y devuelve la respuesta cruda."""
    if Settings.MODO_DRY_RUN:
        escribir_log(f"[DRY RUN] {puerto} ← {comando}")
        return "OK"
    
    try:
        with serial.Serial(puerto, baudrate=Settings.BAUDRATE, timeout=Settings.TIMEOUT_SERIAL) as ser:
            # Limpiar buffer antes de enviar
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # Enviar comando
            ser.write((comando + "\r\n").encode())
            time.sleep(espera)
            
            # Leer respuesta
            respuesta = ser.read_all().decode(errors="ignore").strip()
            
            # Log más informativo
            if respuesta:
                if "OK" in respuesta:
                    escribir_log(f"✅ [{puerto}] {comando} → OK")
                elif "ERROR" in respuesta:
                    escribir_log(f"⚠️ [{puerto}] {comando} → ERROR: {respuesta[:80]}")
                else:
                    escribir_log(f"📝 [{puerto}] {comando} → {respuesta[:80]}")
            else:
                escribir_log(f"⚠️ [{puerto}] {comando} → Sin respuesta")
            
            return respuesta
    except Exception as e:
        escribir_log(f"❌ [{puerto}] Error en {comando}: {e}")
        return ""

def enviar_comando_resiliente(puerto: str, comando: str, intentos: int = None) -> str:
    """Envía comando AT con reintentos automáticos (backoff exponencial)"""
    if intentos is None:
        intentos = Settings.MAX_INTENTOS_COMANDO_AT
    
    for i in range(intentos):
        respuesta = enviar_comando(puerto, comando)
        if respuesta and ("OK" in respuesta or respuesta):  # Considera válida cualquier respuesta
            return respuesta
        if i < intentos - 1:  # No esperar en el último intento
            espera = 1.5 * (i + 1)  # Backoff exponencial
            escribir_log(f"🔄 [{puerto}] Reintento {i+2}/{intentos} en {espera:.1f}s...")
            time.sleep(espera)
    
    escribir_log(f"❌ [{puerto}] Comando falló tras {intentos} intentos: {comando}")
    return respuesta if 'respuesta' in locals() else ""

def revisar_puerto(puerto):
    """Verifica si un puerto responde al comando AT y lo reinicia"""
    try:
        with serial.Serial(puerto, baudrate=115200, timeout=2) as ser:
            ser.write(b"AT\r\n")
            time.sleep(1)
            respuesta = ser.read_all().decode(errors="ignore").strip()
            
            if "OK" in respuesta:
                escribir_log(f"✅ [{puerto}] Módem responde OK")
                # Reiniciar módem
                ser.write(b"AT+CFUN=1,1\r\n")
                escribir_log(f"🔄 [{puerto}] Módem reiniciado")
                return True
            else:
                escribir_log(f"⚠️ [{puerto}] No respondió al comando AT")
                return False
    except Exception as e:
        escribir_log(f"❌ [{puerto}] Error al validar: {e}")
        return False

def esperar_sim_lista(puerto, max_intentos=15):
    """Espera hasta que la SIM esté lista y detectada correctamente"""
    escribir_log(f"⏳ [{puerto}] Esperando detección de SIM...")
    
    for intento in range(max_intentos):
        try:
            with serial.Serial(puerto, baudrate=115200, timeout=2) as ser:
                # Verificar estado de SIM
                ser.write(b"AT+CPIN?\r\n")
                time.sleep(0.8)
                respuesta = ser.read_all().decode(errors="ignore").strip()
                
                if "+CPIN: READY" in respuesta:
                    escribir_log(f"✅ [{puerto}] SIM lista (intento {intento + 1})")
                    return True
                elif "+CPIN:" in respuesta:
                    escribir_log(f"⏳ [{puerto}] SIM detectada pero no lista: {respuesta[:50]}")
                else:
                    # Solo loguear cada 3 intentos para no saturar el log
                    if intento % 3 == 0:
                        escribir_log(f"⏳ [{puerto}] Esperando SIM... (intento {intento + 1}/{max_intentos})")
                
                time.sleep(1.5)
        except Exception as e:
            escribir_log(f"⚠️ [{puerto}] Error al verificar SIM: {e}")
            time.sleep(1.5)
    
    escribir_log(f"❌ [{puerto}] Timeout esperando SIM después de {max_intentos} intentos")
    return False

def obtener_iccid_modem(puerto):
    """Obtiene el ICCID del módem para verificar que cambió"""
    try:
        with serial.Serial(puerto, baudrate=115200, timeout=2) as ser:
            ser.write(b"AT+QCCID\r\n")
            time.sleep(1)
            respuesta = ser.read_all().decode(errors="ignore").strip()
            
            # Buscar el ICCID en la respuesta (19-20 dígitos)
            import re
            match = re.search(r'\d{19,20}', respuesta)
            if match:
                iccid = match.group(0)
                escribir_log(f"📱 [{puerto}] ICCID detectado: {iccid}")
                return iccid
            else:
                escribir_log(f"⚠️ [{puerto}] No se pudo extraer ICCID: {respuesta[:50]}")
                return None
    except Exception as e:
        escribir_log(f"❌ [{puerto}] Error al obtener ICCID: {e}")
        return None

def obtener_iccid_modem_rapido(puerto, timeout=1.5):
    """Obtiene el ICCID del módem de forma rápida (sin log) para verificación"""
    try:
        with serial.Serial(puerto, baudrate=115200, timeout=timeout) as ser:
            ser.write(b"AT+QCCID\r\n")
            time.sleep(0.8)
            respuesta = ser.read_all().decode(errors="ignore").strip()
            
            # Buscar el ICCID en la respuesta (19-20 dígitos)
            match = re.search(r'\d{19,20}', respuesta)
            if match:
                return match.group(0)
            return None
    except Exception:
        return None

def esperar_registro_red(puerto: str, max_intentos: int = 15) -> bool:
    """Espera hasta que el módem esté registrado en red antes de enviar USSD"""
    if Settings.MODO_DRY_RUN:
        return True
    
    log_activacion(f"📡 [{puerto}] Verificando registro en red...")
    
    for intento in range(max_intentos):
        try:
            respuesta = enviar_comando(puerto, "AT+CREG?", espera=0.5)
            
            # Parsear respuesta: +CREG: n,stat
            # stat: 0=no registrado, 1=registrado (home), 2=buscando, 3=denegado, 5=registrado (roaming)
            if "+CREG:" in respuesta:
                # Buscar el segundo número (estado de registro)
                match = re.search(r'\+CREG:\s*\d+,(\d+)', respuesta)
                if match:
                    estado = match.group(1)
                    if estado == "1":
                        log_activacion(f"✅ [{puerto}] Registrado en red local (intento {intento + 1})")
                        return True
                    elif estado == "5":
                        log_activacion(f"✅ [{puerto}] Registrado en roaming (intento {intento + 1})")
                        return True
                    elif estado == "2":
                        if intento % 3 == 0:  # Log cada 3 intentos
                            log_activacion(f"🔍 [{puerto}] Buscando red... (intento {intento + 1}/{max_intentos})")
                    elif estado == "3":
                        log_activacion(f"❌ [{puerto}] Registro denegado por la red")
                        return False
                    else:
                        if intento % 3 == 0:
                            log_activacion(f"⏳ [{puerto}] No registrado (estado={estado}, intento {intento + 1}/{max_intentos})")
            
            time.sleep(2)  # Esperar 2 segundos entre intentos
            
        except Exception as e:
            log_activacion(f"⚠️ [{puerto}] Error verificando registro: {e}")
            time.sleep(2)
    
    log_activacion(f"❌ [{puerto}] Timeout esperando registro en red ({max_intentos * 2}s)")
    return False

def verificar_intensidad_senal(puerto: str) -> int:
    """Verifica la intensidad de señal del módem (0-31, 99=desconocido)"""
    if Settings.MODO_DRY_RUN:
        return 20
    
    try:
        respuesta = enviar_comando(puerto, "AT+CSQ", espera=0.5)
        
        # Parsear: +CSQ: rssi,ber
        # rssi: 0-31 (0=-113dBm o menos, 31=-51dBm o mayor, 99=desconocido)
        match = re.search(r'\+CSQ:\s*(\d+),', respuesta)
        if match:
            rssi = int(match.group(1))
            if rssi == 99:
                log_activacion(f"📶 [{puerto}] Señal desconocida")
            elif rssi >= 20:
                log_activacion(f"📶 [{puerto}] Señal excelente ({rssi}/31)")
            elif rssi >= 15:
                log_activacion(f"📶 [{puerto}] Señal buena ({rssi}/31)")
            elif rssi >= 10:
                log_activacion(f"📶 [{puerto}] Señal regular ({rssi}/31)")
            else:
                log_activacion(f"📶 [{puerto}] Señal débil ({rssi}/31)")
            return rssi
        return 0
    except Exception as e:
        log_activacion(f"⚠️ [{puerto}] Error verificando señal: {e}")
        return 0

# ==================== FUNCIONES DE SIMCLIENT ====================
def cerrar_simclient():
    """Cierra HeroSMS-Partners usando taskkill y verifica que se haya cerrado completamente"""
    try:
        console.print("[yellow]🛑 Cerrando HeroSMS-Partners...[/yellow]")
        
        # Primer intento: taskkill normal
        result = subprocess.run(
            ["taskkill", "/f", "/im", "HeroSMS-Partners.exe"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            escribir_log("✅ HeroSMS-Partners: Comando taskkill enviado")
            
            # Verificar que realmente se cerró (esperar hasta 5 segundos)
            for intento in range(5):
                time.sleep(1)
                check = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq HeroSMS-Partners.exe"],
                    capture_output=True,
                    text=True
                )
                if "HeroSMS-Partners.exe" not in check.stdout:
                    escribir_log("✅ HeroSMS-Partners cerrado completamente")
                    time.sleep(1)  # Espera adicional para liberar puertos
                    return True
            
            # Si después de 5 segundos sigue abierto, forzar cierre adicional
            escribir_log("⚠️ HeroSMS-Partners no se cerró completamente, forzando cierre...")
            subprocess.run(
                ["taskkill", "/f", "/t", "/im", "HeroSMS-Partners.exe"],
                capture_output=True,
                text=True
            )
            time.sleep(2)
            return True
        else:
            escribir_log("⚠️ HeroSMS-Partners no estaba ejecutándose")
            return True
            
    except Exception as e:
        escribir_log(f"❌ Error al cerrar HeroSMS-Partners: {e}")
        return False

def abrir_simclient():
    """Abre HeroSMS-Partners desde el acceso directo en el escritorio (verifica que no esté ya abierto)"""
    try:
        # Verificar si HeroSMS-Partners ya está ejecutándose
        check = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq HeroSMS-Partners.exe"],
            capture_output=True,
            text=True
        )
        
        if "HeroSMS-Partners.exe" in check.stdout:
            escribir_log("⚠️ HeroSMS-Partners ya está en ejecución (no se abrirá de nuevo)")
            console.print("[yellow]⚠️ HeroSMS-Partners ya está abierto[/yellow]")
            return True
        
        # Si no está abierto, proceder a abrirlo
        user = os.environ["USERNAME"]
        simclient_path = f"C:\\Users\\{user}\\Desktop\\HeroSMS-Partners.lnk"
        
        if os.path.exists(simclient_path):
            console.print("[green]🟢 Abriendo HeroSMS-Partners...[/green]")
            os.startfile(simclient_path)
            escribir_log("✅ HeroSMS-Partners iniciado")
            
            # Verificar que se haya abierto correctamente (esperar hasta 10 segundos)
            for intento in range(10):
                time.sleep(1)
                check_abierto = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq HeroSMS-Partners.exe"],
                    capture_output=True,
                    text=True
                )
                if "HeroSMS-Partners.exe" in check_abierto.stdout:
                    escribir_log(f"✅ HeroSMS-Partners confirmado en ejecución (tras {intento + 1}s)")
                    time.sleep(4)  # Espera adicional para que cargue completamente
                    return True
            
            escribir_log("⚠️ No se pudo confirmar que HeroSMS-Partners se haya abierto")
            return True  # Retornar True igual para no bloquear el flujo
        else:
            escribir_log(f"❌ No se encontró HeroSMS-Partners en: {simclient_path}")
            return False
            
    except Exception as e:
        escribir_log(f"❌ Error al abrir HeroSMS-Partners: {e}")
        return False

# ==================== FUNCIÓN PRINCIPAL DE ROTACIÓN ====================
def cambiar_slot_pool(pool_name: str, pool_config: dict, slot_base: int):
    """Cambia todos los puertos lógicos de un pool al slot especificado con offset
    
    v2.5.0: Ahora verifica que el ICCID cambió después del comando SWIT
    """
    sim_bank_com = pool_config["com"]
    puertos_logicos = pool_config["puertos"]
    offset_slot = pool_config.get("offset_slot", 0)
    
    # Calcular el slot real para este pool (con offset circular)
    slot_real = ((slot_base - 1 + offset_slot) % Settings.SLOT_MAX) + 1
    slot_formateado = f"{slot_real:04d}"
    
    console.print(f"[blue]  🔄 {pool_name}: Slot {slot_real:02d} (base {slot_base:02d} + offset {offset_slot}) en {sim_bank_com}[/blue]")
    
    # PASO 1: Obtener ICCIDs actuales de algunos módems del pool (para verificar cambio)
    # Nota: puertos_mapeados solo tiene el número lógico, no sabemos qué pool es cada uno
    # Usamos todos los puertos mapeados que no estén en blacklist
    modems_pool = [puerto for puerto in puertos_mapeados.keys() if puerto not in Settings.PUERTOS_BLACKLIST]
    
    # Tomar muestra de 3 módems para verificar (no todos para ser más rápido)
    modems_muestra = modems_pool[:3] if len(modems_pool) >= 3 else modems_pool
    iccids_anteriores = {}
    
    if modems_muestra and not Settings.MODO_DRY_RUN:
        for puerto_modem in modems_muestra:
            iccid = obtener_iccid_modem_rapido(puerto_modem, timeout=1.5)
            if iccid:
                iccids_anteriores[puerto_modem] = iccid
    
    # PASO 2: Enviar comandos SWIT
    comandos_ok = 0
    comandos_error = 0
    
    for puerto_logico in puertos_logicos:
        comando = f"AT+SWIT{puerto_logico}-{slot_formateado}"
        respuesta = enviar_comando(sim_bank_com, comando, espera=1.0)
        
        # Verificar si el comando fue exitoso
        if "OK" in respuesta or not respuesta:  # Algunos SIM Banks no responden con OK
            comandos_ok += 1
        elif "ERROR" in respuesta:
            comandos_error += 1
        
        time.sleep(0.5)
    
    # PASO 3: Esperar a que se apliquen los cambios mecánicos
    time.sleep(Settings.TIEMPO_APLICAR_SLOT)
    
    # PASO 4: Verificar que los ICCIDs cambiaron
    cambios_verificados = 0
    sin_cambio = 0
    
    if iccids_anteriores and not Settings.MODO_DRY_RUN:
        for puerto_modem, iccid_anterior in iccids_anteriores.items():
            iccid_nuevo = obtener_iccid_modem_rapido(puerto_modem, timeout=1.5)
            
            if iccid_nuevo:
                if iccid_nuevo != iccid_anterior:
                    cambios_verificados += 1
                else:
                    sin_cambio += 1
                    escribir_log(f"⚠️ [{puerto_modem}] ICCID no cambió: {iccid_anterior}")
    
    # PASO 5: Reintentar si muchos módems no cambiaron
    if sin_cambio > 0 and sin_cambio >= cambios_verificados:
        escribir_log(f"⚠️ {pool_name}: {sin_cambio}/{len(iccids_anteriores)} módems no cambiaron ICCID, reintentando...")
        
        # Reenviar comandos SWIT
        for puerto_logico in puertos_logicos:
            comando = f"AT+SWIT{puerto_logico}-{slot_formateado}"
            enviar_comando(sim_bank_com, comando, espera=1.0)
            time.sleep(0.5)
        
        # Esperar más tiempo
        time.sleep(Settings.TIEMPO_APLICAR_SLOT + 3)
        
        # Verificar de nuevo
        cambios_verificados_2 = 0
        for puerto_modem, iccid_anterior in iccids_anteriores.items():
            iccid_nuevo = obtener_iccid_modem_rapido(puerto_modem, timeout=1.5)
            if iccid_nuevo and iccid_nuevo != iccid_anterior:
                cambios_verificados_2 += 1
        
        if cambios_verificados_2 > cambios_verificados:
            escribir_log(f"✅ {pool_name}: Reintento exitoso, {cambios_verificados_2}/{len(iccids_anteriores)} módems cambiaron")
        else:
            escribir_log(f"❌ {pool_name}: Reintento falló, posible problema hardware en {sim_bank_com}")
    
    # Log final
    if comandos_error > 0:
        escribir_log(f"⚠️ {pool_name}: {comandos_ok} OK, {comandos_error} ERROR")
    else:
        if cambios_verificados > 0:
            escribir_log(f"✅ {pool_name} cambiado a slot {slot_real:02d} (verificado: {cambios_verificados}/{len(iccids_anteriores)} módems)")
        else:
            escribir_log(f"✅ {pool_name} cambiado a slot {slot_real:02d} (base {slot_base:02d})")
    
    return comandos_ok, comandos_error

def marcar_puerto_inestable(puerto: str):
    """Marca un puerto como inestable por fallos consecutivos"""
    if puerto not in puertos_inestables:
        puertos_inestables[puerto] = {"fallos": 0, "ultima_vez": datetime.now()}
    
    puertos_inestables[puerto]["fallos"] += 1
    puertos_inestables[puerto]["ultima_vez"] = datetime.now()
    
    if puertos_inestables[puerto]["fallos"] >= Settings.UMBRAL_PUERTO_INESTABLE:
        escribir_log(f"⚠️ Puerto {puerto} marcado como INESTABLE ({puertos_inestables[puerto]['fallos']} fallos)")
        return True
    return False

def es_puerto_inestable(puerto: str) -> bool:
    """Verifica si un puerto está actualmente marcado como inestable"""
    if puerto not in puertos_inestables:
        return False
    
    # Si ya pasó 1 hora, rehabilitar el puerto
    delta = datetime.now() - puertos_inestables[puerto]["ultima_vez"]
    if delta.total_seconds() > 3600:  # 1 hora
        escribir_log(f"✅ Puerto {puerto} rehabilitado (pasó 1 hora)")
        del puertos_inestables[puerto]
        return False
    
    return puertos_inestables[puerto]["fallos"] >= Settings.UMBRAL_PUERTO_INESTABLE

def limpiar_puerto_inestable(puerto: str):
    """Limpia el marcador de puerto inestable (cuando funciona OK)"""
    if puerto in puertos_inestables:
        del puertos_inestables[puerto]

def obtener_modems_activos():
    """Obtiene lista de puertos COM disponibles (excluyendo blacklist e inestables)"""
    puertos_disponibles = listar_puertos_disponibles()
    
    # Si hay mapeo, usar solo los puertos mapeados
    if puertos_mapeados:
        modems_activos = [p for p in puertos_disponibles if p in puertos_mapeados]
        escribir_log(f"📱 Usando {len(modems_activos)} puertos del mapeo")
    else:
        # Si no hay mapeo, usar todos los puertos excepto los controladores de SIM Bank
        controladores = [config["com"] for config in SIM_BANKS.values()]
        modems_activos = [p for p in puertos_disponibles if p not in controladores]
        escribir_log(f"⚠️ Sin mapeo - Usando todos los puertos ({len(modems_activos)}) excepto controladores")
    
    # Filtrar blacklist permanente
    modems_activos = [p for p in modems_activos if p not in Settings.PUERTOS_BLACKLIST]
    blacklist_count = len([p for p in puertos_disponibles if p in Settings.PUERTOS_BLACKLIST])
    if blacklist_count > 0:
        escribir_log(f"🚫 {blacklist_count} puertos excluidos por blacklist: {', '.join(Settings.PUERTOS_BLACKLIST)}")
    
    # Filtrar puertos inestables
    modems_activos = [p for p in modems_activos if not es_puerto_inestable(p)]
    
    inestables_count = len([p for p in puertos_disponibles if es_puerto_inestable(p)])
    if inestables_count > 0:
        escribir_log(f"⚠️ {inestables_count} puertos excluidos por inestabilidad")
    
    return modems_activos

def registrar_fallo_pool(pool_name: str):
    """Registra un fallo en un pool y toma acción si supera umbral"""
    global contador_fallos_pool
    
    if pool_name not in contador_fallos_pool:
        contador_fallos_pool[pool_name] = 0
    
    contador_fallos_pool[pool_name] += 1
    
    if contador_fallos_pool[pool_name] >= 3:
        escribir_log(f"🚨 {pool_name} con {contador_fallos_pool[pool_name]} fallos consecutivos")
        console.print(f"[red]🚨 ALERTA: {pool_name} presenta fallos recurrentes[/red]")
        
        # Intentar reset del SIM Bank
        try:
            sim_bank_com = SIM_BANKS[pool_name]["com"]
            escribir_log(f"🔄 Intentando reset de {pool_name} ({sim_bank_com})")
            enviar_comando_resiliente(sim_bank_com, "AT+CFUN=1,1", intentos=2)
            time.sleep(3)
        except Exception as e:
            escribir_log(f"❌ Error al resetear {pool_name}: {e}")
        
        # Resetear contador después del intento
        contador_fallos_pool[pool_name] = 0

def limpiar_fallos_pool(pool_name: str):
    """Limpia el contador de fallos de un pool (cuando funciona OK)"""
    if pool_name in contador_fallos_pool:
        contador_fallos_pool[pool_name] = 0

@medir_tiempo
def cambiar_slot_simbank(slot: int, iteracion: int, abrir_programa_al_final: bool = True):
    """Cambia todos los SIM Banks al slot especificado (con offset por pool)
    
    Args:
        slot: Número de slot a activar (1-32)
        iteracion: Número de iteración actual
        abrir_programa_al_final: Si True, abre HeroSMS-Partners al final (default)
                                Si False, no abre programa (para modo masivo)
    """
    # Calcular porcentaje de progreso
    porcentaje = (slot / Settings.SLOT_MAX) * 100
    
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold cyan]🔄 ROTACIÓN - SLOT {slot:02d}/{Settings.SLOT_MAX} | ITERACIÓN #{iteracion} | {porcentaje:.1f}% COMPLETADO[/bold cyan]")
    
    # Mostrar slots reales por pool
    slots_info = []
    for pool_name, config in SIM_BANKS.items():
        offset = config.get("offset_slot", 0)
        slot_real = ((slot - 1 + offset) % Settings.SLOT_MAX) + 1
        slots_info.append(f"{pool_name}=slot{slot_real:02d}")
    
    console.print(f"[bold cyan]   {' | '.join(slots_info)}[/bold cyan]")
    
    # Barra de progreso visual
    barra_longitud = 40
    bloques_llenos = int((slot / Settings.SLOT_MAX) * barra_longitud)
    barra = "█" * bloques_llenos + "░" * (barra_longitud - bloques_llenos)
    console.print(f"[cyan]   [{barra}] {porcentaje:.1f}%[/cyan]")
    
    console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")
    
    escribir_log(f"\n{'='*80}")
    escribir_log(f"INICIO ROTACIÓN - Slot {slot:02d}/{Settings.SLOT_MAX} ({porcentaje:.1f}%) - Iteración #{iteracion}")
    escribir_log(f"Slots: {' | '.join(slots_info)}")
    escribir_log(f"{'='*80}")
    
    # 1. Cerrar SimClient (solo si no estamos en modo masivo o es el primer slot)
    if not Settings.MODO_ACTIVACION_MASIVA or slot == Settings.SLOT_MIN:
        cerrar_simclient()
    
    # 2. Cerrar puertos serial
    cerrar_puertos_serial()
    
    # 3. Cargar mapeo de puertos desde SimClient
    console.print("[cyan]📂 Cargando configuración de puertos...[/cyan]")
    cargar_mapeo_puertos()
    
    # 4. Enviar comandos de cambio de slot a todos los SIM Banks en paralelo
    console.print(f"[bold blue]📡 Enviando comandos de cambio a slot {slot:02d} en todos los pools...[/bold blue]")
    
    hilos_cambio = []
    for pool_name, pool_config in SIM_BANKS.items():
        hilo = threading.Thread(
            target=cambiar_slot_pool,
            args=(pool_name, pool_config, slot)
        )
        hilo.start()
        hilos_cambio.append(hilo)
    
    # Esperar a que todos los cambios se completen
    for hilo in hilos_cambio:
        hilo.join()
    
    console.print("[green]✅ Comandos enviados y verificados en todos los pools[/green]")
    
    # 5. Los cambios ya se aplicaron y verificaron dentro de cambiar_slot_pool()
    # No necesitamos esperar adicional aquí
    
    # 6. Obtener módems activos del mapeo
    modems_activos = obtener_modems_activos()
    console.print(f"[cyan]📱 Módems detectados: {len(modems_activos)}[/cyan]")
    
    if len(modems_activos) == 0:
        console.print("[yellow]⚠️ No se detectaron módems para verificar[/yellow]")
        console.print("[yellow]   Posibles causas:[/yellow]")
        console.print("[yellow]   1. El archivo ports.txt no existe o está vacío[/yellow]")
        console.print("[yellow]   2. Todos los puertos son controladores SIM Bank[/yellow]")
        console.print("[yellow]   Se continuará solo con cambio de slots...[/yellow]")
        escribir_log("⚠️ No hay módems para verificar - Continuando sin verificación")
    
    # 7. Revisar y reiniciar todos los módems en paralelo
    console.print("[bold blue]🔍 Paso 1/3: Verificando y reiniciando módems...[/bold blue]")
    
    modems_ok = 0
    modems_lock = threading.Lock()
    
    def revisar_y_contar(puerto):
        nonlocal modems_ok
        if revisar_puerto(puerto):
            with modems_lock:
                modems_ok += 1
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Reiniciando módems...", total=len(modems_activos))
        
        hilos_revision = []
        for puerto_modem in modems_activos:
            hilo = threading.Thread(target=revisar_y_contar, args=(puerto_modem,))
            hilo.start()
            hilos_revision.append(hilo)
        
        for hilo in hilos_revision:
            hilo.join()
            progress.update(task, advance=1)
    
    console.print(f"[green]✅ Módems reiniciados: {modems_ok}/{len(modems_activos)}[/green]")
    
    # 8. Esperar a que los módems detecten las nuevas SIM
    console.print("[bold blue]🔍 Paso 2/3: Esperando detección de SIM en todos los módems...[/bold blue]")
    console.print("[yellow]⏳ Esto puede tomar 20-40 segundos (modo prueba)...[/yellow]")
    
    sims_listas = 0
    iccids_verificados = {}
    
    def esperar_sim_y_verificar(puerto):
        nonlocal sims_listas
        # Esperar a que la SIM esté lista (modo prueba: 15 intentos)
        if esperar_sim_lista(puerto, max_intentos=15):
            # Obtener ICCID para confirmar cambio
            iccid = obtener_iccid_modem(puerto)
            if iccid:
                iccids_verificados[puerto] = iccid
                with modems_lock:
                    sims_listas += 1
                return True
        return False
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Verificando SIMs...", total=len(modems_activos))
        
        hilos_sim = []
        for puerto_modem in modems_activos:
            hilo = threading.Thread(target=esperar_sim_y_verificar, args=(puerto_modem,))
            hilo.start()
            hilos_sim.append(hilo)
        
        for hilo in hilos_sim:
            hilo.join()
            progress.update(task, advance=1)
    
    console.print(f"[green]✅ SIMs listas y verificadas: {sims_listas}/{len(modems_activos)}[/green]")
    
    # Mostrar algunos ICCIDs como confirmación
    if iccids_verificados:
        console.print("[dim]📋 Muestra de ICCIDs detectados:[/dim]")
        for i, (puerto, iccid) in enumerate(list(iccids_verificados.items())[:5]):
            console.print(f"[dim]   {puerto}: {iccid}[/dim]")
        if len(iccids_verificados) > 5:
            console.print(f"[dim]   ... y {len(iccids_verificados) - 5} más[/dim]")
    
    # 9. ACTIVACIÓN DE SIMS CLARO (si está habilitada)
    if Settings.ACTIVAR_SIMS_CLARO and iccids_verificados:
        console.print("\n[bold magenta]{'='*80}[/bold magenta]")
        console.print("[bold magenta]📞 ACTIVACIÓN DE SIMS CLARO[/bold magenta]")
        console.print("[bold magenta]{'='*80}[/bold magenta]\n")
        
        log_activacion(f"\n{'='*80}")
        log_activacion(f"🔄 INICIANDO ACTIVACIÓN - SLOT {slot:02d} - ITERACIÓN #{iteracion}")
        log_activacion(f"{'='*80}")
        
        activaciones_exitosas = 0
        activaciones_fallidas = 0
        sims_claro = 0
        numeros_obtenidos = []
        
        # Procesar activación en paralelo
        resultados_activacion = []
        
        def activar_y_guardar(puerto):
            resultado = procesar_activacion_sim(puerto)
            resultados_activacion.append(resultado)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[magenta]Activando SIMs Claro...", total=len(iccids_verificados))
            
            hilos_activacion = []
            for puerto_modem in iccids_verificados.keys():
                hilo = threading.Thread(target=activar_y_guardar, args=(puerto_modem,))
                hilo.start()
                hilos_activacion.append(hilo)
            
            for hilo in hilos_activacion:
                hilo.join()
                progress.update(task, advance=1)
        
        # Procesar resultados
        for resultado in resultados_activacion:
            if obtener_operador(resultado.get("iccid", "")) == "Claro":
                sims_claro += 1
                if resultado["activado"] and resultado["numero"]:
                    activaciones_exitosas += 1
                    numeros_obtenidos.append(resultado["numero"])
                else:
                    activaciones_fallidas += 1
        
        # Mostrar resumen
        console.print(f"\n[bold magenta]📊 RESUMEN DE ACTIVACIÓN:[/bold magenta]")
        console.print(f"[magenta]  • SIMs Claro detectadas: {sims_claro}[/magenta]")
        console.print(f"[green]  • Activaciones exitosas: {activaciones_exitosas}[/green]")
        console.print(f"[red]  • Activaciones fallidas: {activaciones_fallidas}[/red]")
        
        if numeros_obtenidos:
            console.print(f"\n[dim]📱 Muestra de números obtenidos:[/dim]")
            for i, num in enumerate(numeros_obtenidos[:5]):
                console.print(f"[dim]   {num}[/dim]")
            if len(numeros_obtenidos) > 5:
                console.print(f"[dim]   ... y {len(numeros_obtenidos) - 5} más[/dim]")
        
        log_activacion(f"\n📊 RESUMEN FINAL:")
        log_activacion(f"  • SIMs Claro: {sims_claro}")
        log_activacion(f"  • Exitosas: {activaciones_exitosas}")
        log_activacion(f"  • Fallidas: {activaciones_fallidas}")
        log_activacion(f"{'='*80}\n")
        
        console.print(f"[bold magenta]{'='*80}[/bold magenta]\n")
    
    # 10. Esperar tiempo adicional para estabilización completa (registro en red)
    console.print("[bold blue]🔍 Paso 3/4: Estabilización final y registro en red...[/bold blue]")
    console.print(f"[yellow]⏳ Esperando {Settings.TIEMPO_ESTABILIZACION_FINAL} segundos para registro completo en red...[/yellow]")
    time.sleep(Settings.TIEMPO_ESTABILIZACION_FINAL)
    
    # 11. Cerrar puertos serial nuevamente antes de abrir programa (solo si no es modo masivo)
    if not Settings.MODO_ACTIVACION_MASIVA:
        cerrar_puertos_serial()
    
    # 12. Abrir programa solo si NO estamos en modo masivo O si se especifica explícitamente
    if abrir_programa_al_final and not Settings.MODO_ACTIVACION_MASIVA:
        # 12.1 Esperar antes de abrir
        console.print("[yellow]⏳ Esperando 3 segundos antes de abrir HeroSMS-Partners...[/yellow]")
        time.sleep(3)
        
        # 12.2 Abrir SimClient
        abrir_simclient()
        
        # 12.3 Dar tiempo a SimClient para detectar todos los módems
        console.print("[yellow]⏳ Dando 8 segundos a HeroSMS-Partners para detectar módems...[/yellow]")
        time.sleep(8)
    elif Settings.MODO_ACTIVACION_MASIVA:
        console.print("[green]✅ Modo Activación Masiva: Programa NO será abierto (se abrirá al final)[/green]")
    
    # Mostrar resumen de slots actuales
    slots_actuales = []
    for pool_name, config in SIM_BANKS.items():
        offset = config.get("offset_slot", 0)
        slot_real = ((slot - 1 + offset) % Settings.SLOT_MAX) + 1
        slots_actuales.append(f"{pool_name}=slot{slot_real:02d}")
    
    # Estadísticas finales
    iccids_unicos = len(set(iccids_verificados.values())) if iccids_verificados else 0
    porcentaje_final = (slot / Settings.SLOT_MAX) * 100
    comandos_ok_total = sum(1 for v in iccids_verificados.values() if v)  # Aproximado
    comandos_error_total = len(modems_activos) - comandos_ok_total if modems_activos else 0
    
    # Actualizar métricas acumuladas
    actualizar_metricas(slot, iteracion, sims_listas, len(modems_activos), 
                       iccids_unicos, comandos_ok_total, comandos_error_total)
    
    # Guardar historial de ICCIDs
    if iccids_verificados:
        guardar_historial_iccids(slot, iteracion, iccids_verificados)
    
    # Guardar snapshot completo de la rotación
    snapshot_data = {
        "slot": slot,
        "iteracion": iteracion,
        "modems_reiniciados": modems_ok,
        "total_modems": len(modems_activos),
        "sims_listas": sims_listas,
        "iccids_unicos": iccids_unicos,
        "iccids_verificados": iccids_verificados,
        "slots_activos": {pool: f"slot{((slot-1+config.get('offset_slot',0))%Settings.SLOT_MAX)+1:02d}" 
                         for pool, config in SIM_BANKS.items()},
        "puertos_inestables": list(puertos_inestables.keys()),
        "fallos_por_pool": dict(contador_fallos_pool)
    }
    guardar_snapshot(slot, iteracion, snapshot_data)
    
    escribir_log(f"✅ ROTACIÓN COMPLETADA - Slot {slot:02d}/{Settings.SLOT_MAX} ({porcentaje_final:.1f}%) - Iteración #{iteracion}")
    escribir_log(f"   Módems reiniciados: {modems_ok}/{len(modems_activos)}")
    escribir_log(f"   SIMs verificadas: {sims_listas}/{len(modems_activos)}")
    escribir_log(f"   ICCIDs únicos: {iccids_unicos}/{len(modems_activos)}")
    escribir_log(f"   Slots activos: {' | '.join(slots_actuales)}")
    
    console.print(f"\n[bold green]{'='*80}[/bold green]")
    console.print(f"[bold green]✅ ROTACIÓN COMPLETADA - SLOT {slot:02d}/{Settings.SLOT_MAX} | ITERACIÓN #{iteracion} | {porcentaje_final:.1f}%[/bold green]")
    console.print(f"[bold green]{'='*80}[/bold green]")
    
    if len(modems_activos) > 0:
        console.print(f"[cyan]📊 Estadísticas:[/cyan]")
        console.print(f"   • Módems reiniciados: {modems_ok}/{len(modems_activos)}")
        console.print(f"   • SIMs verificadas: {sims_listas}/{len(modems_activos)}")
        console.print(f"   • ICCIDs únicos detectados: {iccids_unicos}/{len(modems_activos)}")
        
        # 🚨 UMBRAL DE ALERTA: Verificar si hay problemas graves
        if len(modems_activos) > 0:
            ratio_sims_ok = sims_listas / len(modems_activos)
            if ratio_sims_ok < Settings.UMBRAL_ALERTA_SIMS:
                console.print(f"[red]🚨 ALERTA CRÍTICA: Solo {ratio_sims_ok:.1%} de SIMs quedaron listas[/red]")
                console.print(f"[red]   (Umbral mínimo: {Settings.UMBRAL_ALERTA_SIMS:.1%})[/red]")
                escribir_log(f"🚨 ALERTA: Ratio SIMs listas {ratio_sims_ok:.1%} < umbral {Settings.UMBRAL_ALERTA_SIMS:.1%}")
        
        # Advertencia si hay ICCIDs duplicados
        if iccids_unicos < len(modems_activos):
            console.print(f"[yellow]⚠️  ATENCIÓN: Se detectaron {len(modems_activos) - iccids_unicos} ICCIDs duplicados[/yellow]")
            escribir_log(f"⚠️ ADVERTENCIA: {len(modems_activos) - iccids_unicos} ICCIDs duplicados detectados")
    
    console.print(f"[green]🎯 Slots activos: {' | '.join(slots_actuales)}[/green]")
    console.print(f"[bold green]{'='*80}[/bold green]\n")

# ==================== PARÁMETROS CLI ====================
def parse_args():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description=f"Rotador Automático de SIM Bank v{Settings.VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python RotadorSimBank.py                          # Modo por defecto: Activación masiva (1024 SIMs)
  python RotadorSimBank.py --modo-continuo          # Modo rotación continua cada 30 minutos
  python RotadorSimBank.py --intervalo 15           # Cambiar intervalo (solo con --modo-continuo)
  python RotadorSimBank.py --dry-run                # Modo prueba sin hardware
  python RotadorSimBank.py --slot-start 10          # Comenzar desde slot 10
  python RotadorSimBank.py --self-test              # Probar COM ports y salir
  python RotadorSimBank.py --export-db              # Exportar PostgreSQL a archivo local
  python RotadorSimBank.py --clean-duplicates       # Limpiar duplicados del archivo
  python RotadorSimBank.py --update                 # Forzar actualización desde GitHub
  python RotadorSimBank.py --no-update-check        # Saltar verificación de actualizaciones
        """
    )
    
    parser.add_argument(
        "--intervalo",
        type=int,
        default=Settings.INTERVALO_MINUTOS,
        help=f"Minutos entre rotaciones (default: {Settings.INTERVALO_MINUTOS})"
    )
    
    parser.add_argument(
        "--slot-start",
        type=int,
        help="Forzar inicio en un slot específico (1-32)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Modo prueba: simula sin tocar hardware"
    )
    
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Probar COM ports de SIM Banks y salir"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Modo verboso: logs más detallados"
    )
    
    parser.add_argument(
        "--modo-continuo",
        action="store_true",
        help="Modo rotación continua: Rota cada 30 minutos indefinidamente (desactiva modo masivo por defecto)"
    )
    
    parser.add_argument(
        "--export-db",
        action="store_true",
        help="Exportar base de datos PostgreSQL a archivo local y salir"
    )
    
    parser.add_argument(
        "--clean-duplicates",
        action="store_true",
        help="Limpiar duplicados del archivo local y salir"
    )
    
    parser.add_argument(
        "--update",
        action="store_true",
        help="Forzar actualización del script desde GitHub"
    )
    
    parser.add_argument(
        "--no-update-check",
        action="store_true",
        help="Saltar verificación de actualizaciones al inicio"
    )
    
    parser.add_argument(
        "--agente",
        action="store_true",
        help="Ejecutar en modo agente de control remoto (servicio 24/7)"
    )
    
    parser.add_argument(
        "--instalar-servicio",
        action="store_true",
        help="Instalar el agente como servicio de Windows"
    )
    
    parser.add_argument(
        "--detectar-simbanks",
        action="store_true",
        help="Forzar detección de SIM Banks desde HeroSMS-Partners y salir"
    )
    
    return parser.parse_args()

# ==================== SELF TEST ====================
def self_test():
    """Prueba rápida de conectividad con SIM Banks"""
    console.print("\n[bold cyan]🧪 AUTO-TEST DE SIM BANKS[/bold cyan]")
    console.print("="*70)
    
    puertos_disponibles = listar_puertos_disponibles()
    
    for pool_name, config in SIM_BANKS.items():
        puerto = config["com"]
        console.print(f"\n[bold]{pool_name} ({puerto}):[/bold]")
        
        if puerto not in puertos_disponibles:
            console.print(f"  [red]❌ Puerto no detectado[/red]")
            continue
        
        # Test 1: AT básico
        try:
            respuesta = enviar_comando(puerto, "AT", espera=0.5)
            if "OK" in respuesta:
                console.print(f"  [green]✅ Responde a AT[/green]")
            else:
                console.print(f"  [yellow]⚠️ Respuesta inesperada: {respuesta[:50]}[/yellow]")
        except Exception as e:
            console.print(f"  [red]❌ Error: {e}[/red]")
            continue
        
        # Test 2: Comando SWIT de prueba
        try:
            comando_test = f"AT+SWIT01-0001"
            respuesta = enviar_comando(puerto, comando_test, espera=0.5)
            if "OK" in respuesta or not respuesta:
                console.print(f"  [green]✅ Comando AT+SWIT funcional[/green]")
            else:
                console.print(f"  [yellow]⚠️ Respuesta a SWIT: {respuesta[:50]}[/yellow]")
        except Exception as e:
            console.print(f"  [red]❌ Error en SWIT: {e}[/red]")
    
    console.print("\n" + "="*70)
    console.print("[bold green]✅ Auto-test completado[/bold green]\n")

# ==================== MODO ACTIVACIÓN MASIVA ====================
@medir_tiempo
def activacion_masiva_todas_las_sims():
    """Modo especial: Activa todas las 1024 SIMs (32 slots × 32 SIMs) sin interrupciones
    
    Este modo:
    - Cierra HeroSMS-Partners al inicio
    - Procesa todos los slots 1-32 en secuencia
    - Activa todas las SIMs y guarda myphone
    - Solo abre HeroSMS-Partners al final
    - NO espera 30 minutos entre slots
    """
    console.print("\n[bold magenta]" + "="*80 + "[/bold magenta]")
    console.print("[bold magenta]🚀 MODO ACTIVACIÓN MASIVA - 1024 SIMS TOTALES[/bold magenta]")
    console.print("[bold magenta]" + "="*80 + "[/bold magenta]\n")
    
    escribir_log("="*80)
    escribir_log("🚀 INICIANDO MODO ACTIVACIÓN MASIVA")
    escribir_log("   Total SIMs a procesar: 1024 (32 slots × 32 SIMs)")
    escribir_log("   Pools: 4 (Pool1-4)")
    escribir_log("   Sin interrupciones entre slots")
    escribir_log("="*80)
    
    # 1. Cerrar HeroSMS-Partners al inicio (solo una vez)
    console.print("[yellow]📌 Paso 1/4: Cerrando HeroSMS-Partners...[/yellow]")
    cerrar_simclient()
    cerrar_puertos_serial()
    
    # 2. Cargar mapeo de puertos
    console.print("[yellow]📌 Paso 2/4: Cargando configuración de puertos...[/yellow]")
    cargar_mapeo_puertos()
    
    # 3. Procesar todos los slots (1-32)
    console.print("\n[bold yellow]📌 Paso 3/4: Procesando todos los slots (1-32)...[/bold yellow]")
    console.print("[yellow]   Esto tomará aproximadamente 2-3 horas (sin esperas entre slots)[/yellow]\n")
    
    total_activaciones = 0
    total_sims_procesadas = 0
    slots_info_completa = []
    
    tiempo_inicio = time.time()
    
    for slot in range(Settings.SLOT_MIN, Settings.SLOT_MAX + 1):
        console.print(f"\n[bold cyan]{'─'*80}[/bold cyan]")
        console.print(f"[bold cyan]📍 PROCESANDO SLOT {slot:02d}/32 ({(slot/32)*100:.1f}% completado)[/bold cyan]")
        console.print(f"[bold cyan]{'─'*80}[/bold cyan]")
        
        # Cambiar slot (sin abrir programa)
        cambiar_slot_simbank(slot, iteracion=1, abrir_programa_al_final=False)
        
        # Contar activaciones de este slot (aproximado)
        # Nota: Las métricas reales se guardarán en los archivos JSON
        
        # Pequeña pausa entre slots para estabilidad
        if slot < Settings.SLOT_MAX:
            console.print("[dim]⏳ Pausa de 5 segundos antes del siguiente slot...[/dim]")
            time.sleep(5)
    
    tiempo_fin = time.time()
    duracion_total = tiempo_fin - tiempo_inicio
    
    # 4. Abrir HeroSMS-Partners al finalizar todo
    console.print("\n[bold green]📌 Paso 4/4: Abriendo HeroSMS-Partners (finalizando proceso)...[/bold green]")
    cerrar_puertos_serial()
    time.sleep(3)
    abrir_simclient()
    time.sleep(8)
    
    # Resumen final
    console.print("\n[bold green]" + "="*80 + "[/bold green]")
    console.print("[bold green]✅ ACTIVACIÓN MASIVA COMPLETADA[/bold green]")
    console.print("[bold green]" + "="*80 + "[/bold green]")
    console.print(f"[green]⏱️  Tiempo total: {duracion_total/60:.1f} minutos ({duracion_total/3600:.2f} horas)[/green]")
    console.print(f"[green]📊 Slots procesados: 32/32[/green]")
    console.print(f"[green]🎯 Total SIMs procesadas: ~1024 (verificar logs detallados)[/green]")
    console.print(f"[green]💾 Revisa los archivos:[/green]")
    console.print(f"[green]   • {Settings.LOG_ACTIVACION}[/green]")
    console.print(f"[green]   • {Settings.METRICS_FILE}[/green]")
    console.print(f"[green]   • {Settings.ICCIDS_HISTORY_FILE}[/green]")
    console.print(f"[green]   • listadonumeros_claro.txt[/green]")
    console.print("[bold green]" + "="*80 + "[/bold green]\n")
    
    escribir_log("="*80)
    escribir_log("✅ ACTIVACIÓN MASIVA COMPLETADA")
    escribir_log(f"   Tiempo total: {duracion_total/60:.1f} minutos")
    escribir_log(f"   Slots procesados: 32/32")
    escribir_log("="*80)

# ==================== BUCLE PRINCIPAL ====================
def mostrar_configuracion():
    """Muestra la configuración inicial en una tabla"""
    console.print("\n[bold green]" + "="*80 + "[/bold green]")
    console.print("[bold green]      🔄 ROTADOR AUTOMÁTICO DE SIM BANK - CLARO POOL[/bold green]")
    console.print("[bold green]         (Con Escalonamiento para Evitar Duplicados)[/bold green]")
    console.print("[bold green]" + "="*80 + "[/bold green]\n")
    
    # Advertencia si está en modo prueba
    if Settings.INTERVALO_MINUTOS < 10:
        console.print("[bold yellow]⚠️  MODO PRUEBA ACTIVADO ⚠️[/bold yellow]")
        console.print(f"[yellow]Rotación cada {Settings.INTERVALO_MINUTOS} minutos (recuerda cambiar a 30 en producción)[/yellow]")
        console.print("[yellow]" + "="*80 + "[/yellow]\n")
    
    # Tabla de configuración de pools
    table = Table(title="📋 Configuración de SIM Banks", show_header=True, header_style="bold cyan")
    table.add_column("Pool", style="cyan", width=10)
    table.add_column("Puerto COM", style="yellow", width=12)
    table.add_column("Offset Slot", style="magenta", width=12)
    table.add_column("Puertos Lógicos", style="green", width=30)
    
    for pool_name, config in SIM_BANKS.items():
        puertos_str = ", ".join(config["puertos"])
        offset = config.get("offset_slot", 0)
        table.add_row(pool_name, config["com"], f"+{offset}", puertos_str)
    
    console.print(table)
    console.print()
    
    console.print(f"[cyan]⚙️  Parámetros:[/cyan]")
    console.print(f"   • Slots: {Settings.SLOT_MIN}-{Settings.SLOT_MAX} (progreso 0% → 100%)")
    console.print(f"   • Intervalo: {Settings.INTERVALO_MINUTOS} minutos por rotación")
    
    # Mostrar estado de activación automática
    if Settings.ACTIVAR_SIMS_CLARO:
        console.print(f"\n[magenta]📞 Activación Automática de SIMs Claro: HABILITADA[/magenta]")
        console.print(f"[magenta]   • Intentos por SIM: {Settings.INTENTOS_ACTIVACION}[/magenta]")
        console.print(f"[magenta]   • Espera entre intentos: {Settings.ESPERA_ENTRE_INTENTOS}s[/magenta]")
        console.print(f"[magenta]   • Log: {Settings.LOG_ACTIVACION}[/magenta]")
    else:
        console.print(f"\n[dim]📞 Activación Automática: DESHABILITADA[/dim]")
    console.print(f"   • Tiempo total por ciclo: {Settings.SLOT_MAX * Settings.INTERVALO_MINUTOS} minutos ({(Settings.SLOT_MAX * Settings.INTERVALO_MINUTOS)/60:.1f} horas)")
    console.print(f"   • Total pools: {len(SIM_BANKS)}")
    console.print(f"   • Total puertos por pool: 8")
    console.print(f"   • Log: {Settings.LOG_FILE}")
    console.print(f"   • Estado persistente: {Settings.STATE_FILE}")
    console.print()
    console.print(f"[yellow]💡 Escalonamiento:[/yellow]")
    console.print(f"   Pool1 comenzará en slot 1, Pool2 en slot 9, Pool3 en slot 17, Pool4 en slot 25")
    console.print(f"   Esto asegura que no haya duplicados entre pools.")
    console.print()
    console.print(f"[green]💾 Memoria Persistente:[/green]")
    console.print(f"   El script recuerda en qué slot quedó y continúa desde ahí si se reinicia.")
    console.print(f"   Al completar los 32 slots (100%), inicia nueva iteración desde slot 1.\n")

def main():
    """Bucle principal del rotador con persistencia de estado"""
    # 0. Parsear argumentos CLI
    args = parse_args()
    
    # Verificar actualización forzada
    if args.update:
        console.print("[yellow]🔄 Actualizando script...[/yellow]")
        actualizar_script()
        return
    
    # Si se especifica modo continuo, desactivar activación masiva
    if args.modo_continuo:
        Settings.MODO_ACTIVACION_MASIVA = False
        console.print(f"[yellow]🔄 Modo ROTACIÓN CONTINUA activado[/yellow]")
    else:
        # Modo masivo por defecto, activar auto-update para no pedir confirmación
        Settings.AUTO_UPDATE = True
        console.print(f"[yellow]🚀 Modo ACTIVACIÓN MASIVA activado (por defecto)[/yellow]")
    
    # Verificar actualizaciones al inicio (si no se desactiva)
    if not args.no_update_check and Settings.CHECK_UPDATES:
        verificar_y_actualizar()
    
    # Crear tabla de base de datos si no existe
    if Settings.DB_ENABLED:
        crear_tabla_db()
    
    # Detectar SIM Banks y salir
    if args.detectar_simbanks:
        console.print("\n[bold cyan]🔍 DETECCIÓN DE SIM BANKS[/bold cyan]")
        console.print("=" * 70 + "\n")
        config = detectar_simbanks_desde_log()
        if config:
            guardar_simbanks_config(config)
            console.print("\n[bold green]✅ Configuración detectada y guardada exitosamente[/bold green]")
            console.print("\nConfiguración detectada:\n")
            for pool_name, pool_config in config.items():
                console.print(f"  [cyan]{pool_name}:[/cyan]")
                console.print(f"    COM: {pool_config['com']}")
                console.print(f"    Offset: {pool_config['offset_slot']}")
                console.print(f"    Puertos: {', '.join(pool_config['puertos'])}\n")
        else:
            console.print("\n[bold red]❌ No se pudo detectar la configuración[/bold red]")
            console.print("[yellow]Asegúrate de que HeroSMS-Partners esté instalado y haya logs disponibles[/yellow]")
        return
    
    # Exportar base de datos y salir
    if args.export_db:
        exportar_base_datos_completa()
        return
    
    # Limpiar duplicados y salir
    if args.clean_duplicates:
        limpiar_listado()
        return
    
    # Aplicar overrides de CLI
    if args.intervalo:
        Settings.INTERVALO_MINUTOS = args.intervalo
        console.print(f"[yellow]⚙️  Override: Intervalo = {args.intervalo} minutos[/yellow]")
    
    if args.dry_run:
        Settings.MODO_DRY_RUN = True
        console.print(f"[yellow]🧪 Modo DRY RUN activado[/yellow]")
    
    # Si es self-test, ejecutar y salir
    if args.self_test:
        self_test()
        return
    
    # Si es activación masiva (modo por defecto), ejecutar y salir
    if Settings.MODO_ACTIVACION_MASIVA:
        console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
        console.print(f"[bold cyan]🚀 MODO ACTIVACIÓN MASIVA[/bold cyan]")
        console.print(f"[bold cyan]{'='*80}[/bold cyan]")
        console.print(f"[cyan]   Se procesarán los 32 slots (1024 SIMs) sin interrupciones[/cyan]")
        console.print(f"[cyan]   Tiempo estimado: 2-3 horas[/cyan]")
        console.print(f"[cyan]   El programa se abrirá solo al final[/cyan]")
        console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")
        
        activacion_masiva_todas_las_sims()
        return
    
    # 1. Crear lock file (anti-doble instancia)
    crear_lock()
    
    try:
        # 2. Inicializar configuración de SIM Banks (auto-detección)
        inicializar_simbanks()
        
        # 3. Mostrar configuración
        mostrar_configuracion()
        
        # 4. Validar que los COM de SIM Banks existan
        validar_simbanks()
        
        # 5. Cargar estado anterior (slot e iteración)
        slot_actual, iteracion = cargar_estado()
        
        # Override de slot si se especificó en CLI
        if args.slot_start:
            if Settings.SLOT_MIN <= args.slot_start <= Settings.SLOT_MAX:
                slot_actual = args.slot_start
                console.print(f"[yellow]⚙️  Override: Comenzando desde slot {slot_actual}[/yellow]")
            else:
                console.print(f"[red]❌ Slot inválido: {args.slot_start}. Usando slot guardado: {slot_actual}[/red]")
        
        console.print(f"[bold yellow]📂 Estado: Slot {slot_actual}/{Settings.SLOT_MAX} - Iteración #{iteracion}[/bold yellow]")
        escribir_log("="*80)
        escribir_log(f"ROTADOR SIMBANK v{Settings.VERSION} INICIADO")
        escribir_log(f"Slot {slot_actual}/{Settings.SLOT_MAX} - Iteración #{iteracion}")
        escribir_log(f"Intervalo: {Settings.INTERVALO_MINUTOS} minutos")
        escribir_log(f"Modo Dry Run: {Settings.MODO_DRY_RUN}")
        escribir_log("="*80)
    
        while True:
            # Ejecutar rotación
            cambiar_slot_simbank(slot_actual, iteracion)
            
            # Avanzar al siguiente slot
            slot_actual += 1
            
            # Si completamos el ciclo, reiniciar y aumentar iteración
            if slot_actual > Settings.SLOT_MAX:
                slot_actual = Settings.SLOT_MIN
                iteracion += 1
                
                # Mensaje de ciclo completo
                console.print(f"\n[bold green]{'='*80}[/bold green]")
                console.print(f"[bold green]🎉 CICLO COMPLETO - 100% COMPLETADO[/bold green]")
                console.print(f"[bold green]{'='*80}[/bold green]")
                console.print(f"[bold yellow]🔄 Iniciando Iteración #{iteracion}[/bold yellow]")
                console.print(f"[bold yellow]   Volviendo al Slot 1...[/bold yellow]")
                console.print(f"[bold green]{'='*80}[/bold green]\n")
                
                escribir_log(f"\n{'='*80}")
                escribir_log(f"🎉 CICLO COMPLETO - 100% COMPLETADO")
                escribir_log(f"🔄 Iniciando Iteración #{iteracion}")
                escribir_log(f"{'='*80}\n")
            
            # Guardar estado después de cada rotación
            guardar_estado(slot_actual, iteracion)
            escribir_log(f"💾 Estado guardado: Slot {slot_actual}/{Settings.SLOT_MAX} - Iteración #{iteracion}")
            
            # Esperar el intervalo configurado
            console.print(f"[dim]💤 Esperando {Settings.INTERVALO_MINUTOS} minutos hasta la próxima rotación...[/dim]")
            console.print(f"[dim]   Próximo slot: {slot_actual}/{Settings.SLOT_MAX} ({(slot_actual/Settings.SLOT_MAX)*100:.1f}%)[/dim]\n")
            time.sleep(Settings.INTERVALO_MINUTOS * 60)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Rotador detenido por el usuario[/yellow]")
        console.print(f"[yellow]💾 Estado guardado: Slot {slot_actual}/{Settings.SLOT_MAX} - Iteración #{iteracion}[/yellow]")
        guardar_estado(slot_actual, iteracion)
        escribir_log(f"⚠️ ROTADOR DETENIDO POR EL USUARIO - Estado guardado: Slot {slot_actual} - Iteración #{iteracion}")
    except Exception as e:
        console.print(f"\n[red]❌ Error fatal: {e}[/red]")
        guardar_estado(slot_actual, iteracion)
        escribir_log(f"❌ ERROR FATAL: {e} - Estado guardado: Slot {slot_actual} - Iteración #{iteracion}")
        import traceback
        escribir_log(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        borrar_lock()

# ==================== AGENTE DE CONTROL REMOTO ====================
class AgenteControlRemoto:
    """Agente que escucha comandos remotos desde el dashboard de Vercel"""
    
    def __init__(self):
        # Configurar encoding UTF-8 para evitar errores con emojis en servicios de Windows
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
        except:
            pass
        
        self.api_url = Settings.AGENTE_API_URL
        self.auth_token = Settings.AGENTE_AUTH_TOKEN
        self.machine_id = platform.node()
        self.poll_interval = Settings.AGENTE_POLL_INTERVAL
        self.rotador_script = os.path.abspath(__file__)
        self.ultima_verificacion_actualizacion = time.time()
        self.ultimo_reinicio_herosms = time.time()  # Timer para reinicio automático cada 2h
        self.machine_config_file = "machine_config.json"
        self.custom_name = self.load_custom_name()
        
    def load_custom_name(self):
        """Carga el nombre personalizado de la máquina desde archivo"""
        try:
            if os.path.exists(self.machine_config_file):
                with open(self.machine_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("custom_name", self.machine_id)
        except:
            pass
        return self.machine_id
    
    def save_custom_name(self, name: str):
        """Guarda el nombre personalizado de la máquina"""
        try:
            config = {"custom_name": name, "original_hostname": self.machine_id}
            with open(self.machine_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.custom_name = name
            return True
        except Exception as e:
            console.print(f"[red]❌ Error guardando nombre: {e}[/red]")
            return False
    
    def take_screenshot(self):
        """Toma una captura de pantalla y la retorna en base64
        
        Intenta múltiples métodos en orden:
        1. mss (funciona mejor con servicios de Windows)
        2. PIL/ImageGrab
        3. PowerShell (fallback para servicios)
        """
        # Método 1: Usar mss (funciona en Session 0)
        if mss is not None:
            try:
                console.print("[cyan]📸 Intentando captura con mss...[/cyan]")
                
                with mss.mss() as sct:
                    # Capturar el monitor principal
                    monitor = sct.monitors[1]
                    screenshot_raw = sct.grab(monitor)
                    
                    # Convertir a PIL Image
                    screenshot = Image.frombytes('RGB', screenshot_raw.size, screenshot_raw.rgb)
                    
                    # Redimensionar para reducir tamaño
                    max_width = 1280
                    if screenshot.width > max_width:
                        ratio = max_width / screenshot.width
                        new_size = (max_width, int(screenshot.height * ratio))
                        screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # Convertir a JPEG y comprimir
                    buffer = BytesIO()
                    screenshot.save(buffer, format='JPEG', quality=75, optimize=True)
                    buffer.seek(0)
                    
                    # Codificar en base64
                    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    
                    console.print("[green]✅ Captura exitosa con mss[/green]")
                    return img_base64
                    
            except Exception as e:
                console.print(f"[yellow]⚠️  mss falló: {e}[/yellow]")
        
        # Método 2: Usar PIL ImageGrab
        try:
            console.print("[cyan]📸 Intentando captura con PIL ImageGrab...[/cyan]")
            
            screenshot = ImageGrab.grab()
            
            # Redimensionar para reducir tamaño
            max_width = 1280
            if screenshot.width > max_width:
                ratio = max_width / screenshot.width
                new_size = (max_width, int(screenshot.height * ratio))
                screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convertir a JPEG y comprimir
            buffer = BytesIO()
            screenshot.save(buffer, format='JPEG', quality=75, optimize=True)
            buffer.seek(0)
            
            # Codificar en base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            console.print("[green]✅ Captura exitosa con PIL[/green]")
            return img_base64
            
        except Exception as e:
            console.print(f"[yellow]⚠️  PIL falló: {e}[/yellow]")
        
        # Método 3: Usar PowerShell (fallback para servicios)
        try:
            console.print("[cyan]📸 Intentando captura con PowerShell...[/cyan]")
            
            import tempfile
            screenshot_path = os.path.join(tempfile.gettempdir(), f"screenshot_{int(time.time())}.png")
            
            # Script PowerShell para capturar pantalla
            ps_script = f"""
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
            $bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
            $bitmap.Save('{screenshot_path}', [System.Drawing.Imaging.ImageFormat]::Png)
            $graphics.Dispose()
            $bitmap.Dispose()
            """
            
            # Ejecutar PowerShell
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and os.path.exists(screenshot_path):
                # Leer y procesar la imagen
                screenshot = Image.open(screenshot_path)
                
                # Redimensionar
                max_width = 1280
                if screenshot.width > max_width:
                    ratio = max_width / screenshot.width
                    new_size = (max_width, int(screenshot.height * ratio))
                    screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
                
                # Convertir a JPEG
                buffer = BytesIO()
                screenshot.save(buffer, format='JPEG', quality=75, optimize=True)
                buffer.seek(0)
                
                # Limpiar archivo temporal
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
                # Codificar en base64
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                console.print("[green]✅ Captura exitosa con PowerShell[/green]")
                return img_base64
            else:
                console.print(f"[yellow]⚠️  PowerShell falló: {result.stderr.decode() if result.stderr else 'Unknown error'}[/yellow]")
                
        except Exception as e:
            console.print(f"[yellow]⚠️  PowerShell falló: {e}[/yellow]")
        
        # Si todos los métodos fallaron
        console.print("[red]❌ Todos los métodos de captura fallaron[/red]")
        console.print("[yellow]💡 Nota: Los servicios de Windows (Session 0) no pueden capturar la pantalla del usuario.[/yellow]")
        console.print("[yellow]💡 Para usar capturas de pantalla, ejecuta el agente manualmente: python RotadorSimBank.py --agente[/yellow]")
        
        return None
    
    def get_system_status(self):
        """Obtiene el estado del sistema"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "uptime_hours": int((time.time() - psutil.boot_time()) / 3600)
        }
    
    def check_service_status(self, service_name):
        """Verifica si un servicio está corriendo y devuelve información detallada"""
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {service_name}"],
                capture_output=True,
                text=True
            )
            
            is_running = service_name in result.stdout
            
            # Obtener información adicional si está corriendo
            if is_running:
                # Contar procesos
                count = result.stdout.count(service_name)
                
                # Obtener PID si es posible
                lines = result.stdout.split('\n')
                pids = []
                for line in lines:
                    if service_name in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                pids.append(int(parts[1]))
                            except:
                                pass
                
                return {
                    "status": "running",
                    "display": "✅ Running",
                    "count": count,
                    "pids": pids
                }
            else:
                return {
                    "status": "stopped",
                    "display": "❌ Stopped",
                    "count": 0,
                    "pids": []
                }
        except Exception as e:
            return {
                "status": "unknown",
                "display": "❓ Unknown",
                "error": str(e),
                "count": 0,
                "pids": []
            }
    
    def execute_command(self, command):
        """Ejecuta un comando según el tipo"""
        try:
            if command == "restart_pc":
                console.print("[yellow]🔄 Ejecutando: Reiniciar PC[/yellow]")
                subprocess.Popen(["shutdown", "/r", "/t", "10"])
                return {"success": True, "message": "PC reiniciándose en 10s"}
            
            elif command == "start_herosms":
                console.print("[yellow]🟢 Ejecutando: Iniciar Hero-SMS[/yellow]")
                # Verificar si ya está corriendo
                herosms_status = self.check_service_status("HeroSMS-Partners.exe")
                if herosms_status["status"] == "running":
                    return {"success": False, "message": "Hero-SMS ya está corriendo"}
                
                # Iniciar Hero-SMS
                user = os.environ.get("USERNAME", "")
                shortcut_path = f"C:\\Users\\{user}\\Desktop\\HeroSMS-Partners.lnk"
                if os.path.exists(shortcut_path):
                    os.startfile(shortcut_path)
                    return {"success": True, "message": "Hero-SMS iniciado"}
                else:
                    return {"success": False, "message": f"No se encontró Hero-SMS en: {shortcut_path}"}
            
            elif command == "restart_herosms":
                console.print("[yellow]🔄 Ejecutando: Reiniciar Hero-SMS[/yellow]")
                subprocess.run(["taskkill", "/F", "/IM", "HeroSMS-Partners.exe"], 
                             capture_output=True, timeout=10)
                time.sleep(2)
                user = os.environ.get("USERNAME", "")
                shortcut_path = f"C:\\Users\\{user}\\Desktop\\HeroSMS-Partners.lnk"
                if os.path.exists(shortcut_path):
                    os.startfile(shortcut_path)
                    return {"success": True, "message": "Hero-SMS reiniciado"}
                else:
                    return {"success": False, "message": f"No se encontró Hero-SMS en: {shortcut_path}"}
            
            elif command == "start_rotador":
                console.print("[yellow]🟢 Ejecutando: Iniciar Rotador[/yellow]")
                # Verificar si ya está corriendo
                if self.is_rotador_running():
                    return {"success": False, "message": "RotadorSimBank ya está corriendo"}
                
                # Iniciar nuevo proceso
                subprocess.Popen(
                    [sys.executable, self.rotador_script],
                    creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0
                )
                return {"success": True, "message": "RotadorSimBank iniciado"}
            
            elif command == "restart_rotador":
                console.print("[yellow]🔄 Ejecutando: Reiniciar Rotador[/yellow]")
                # Detener el rotador actual
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and 'python' in proc.info['name'].lower():
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline and any('RotadorSimBank' in str(arg) for arg in cmdline):
                                proc.kill()
                                console.print(f"[green]✅ Proceso RotadorSimBank (PID {proc.info['pid']}) detenido[/green]")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                time.sleep(3)
                
                # Iniciar nuevo proceso
                subprocess.Popen(
                    [sys.executable, self.rotador_script],
                    creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0
                )
                return {"success": True, "message": "RotadorSimBank reiniciado"}
            
            elif command == "restart_agent":
                console.print("[yellow]🔄 Ejecutando: Reiniciar Agente[/yellow]")
                try:
                    nssm_path = os.path.join(os.getcwd(), "nssm.exe")
                    if os.path.exists(nssm_path):
                        subprocess.run([nssm_path, "restart", "AgenteRotadorSimBank"], 
                                     capture_output=True, timeout=10)
                        return {"success": True, "message": "Agente reiniciándose..."}
                    else:
                        return {"success": False, "message": "NSSM no encontrado"}
                except Exception as e:
                    return {"success": False, "message": f"Error al reiniciar agente: {str(e)}"}
            
            elif command == "stop_rotador":
                console.print("[yellow]🛑 Ejecutando: Detener Rotador[/yellow]")
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and 'python' in proc.info['name'].lower():
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline and any('RotadorSimBank' in str(arg) for arg in cmdline):
                                proc.kill()
                                console.print(f"[green]✅ Proceso RotadorSimBank (PID {proc.info['pid']}) detenido[/green]")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Eliminar archivo lock
                if os.path.exists(Settings.LOCK_FILE):
                    os.remove(Settings.LOCK_FILE)
                
                return {"success": True, "message": "RotadorSimBank detenido"}
            
            elif command == "update":
                console.print("[yellow]📥 Ejecutando: Actualizar Script[/yellow]")
                try:
                    hay_actualizacion, version_remota = verificar_actualizacion()
                    if hay_actualizacion:
                        console.print(f"[green]🆕 Actualizando a v{version_remota}...[/green]")
                        if actualizar_script():
                            return {"success": True, "message": f"Actualizado a v{version_remota}. Reiniciando..."}
                        else:
                            return {"success": False, "message": "Error al descargar la actualización"}
                    else:
                        return {"success": True, "message": f"Ya estás en la última versión (v{Settings.VERSION})"}
                except Exception as e:
                    return {"success": False, "message": f"Error al actualizar: {str(e)}"}
            
            elif command == "get_logs":
                console.print("[yellow]📄 Ejecutando: Obtener Logs[/yellow]")
                try:
                    # Leer últimas 100 líneas del log principal
                    log_content = self.read_log_file(Settings.LOG_FILE, lines=100)
                    return {"success": True, "logs": log_content, "file": Settings.LOG_FILE}
                except Exception as e:
                    return {"success": False, "message": f"Error leyendo logs: {str(e)}"}
            
            elif command == "get_activation_logs":
                console.print("[yellow]📄 Ejecutando: Obtener Logs de Activación[/yellow]")
                try:
                    # Leer últimas 100 líneas del log de activación
                    log_content = self.read_log_file(Settings.LOG_ACTIVACION, lines=100)
                    return {"success": True, "logs": log_content, "file": Settings.LOG_ACTIVACION}
                except Exception as e:
                    return {"success": False, "message": f"Error leyendo logs: {str(e)}"}
            
            elif command == "get_agent_logs":
                console.print("[yellow]📄 Ejecutando: Obtener Logs del Agente[/yellow]")
                try:
                    # Leer últimas 50 líneas del log del agente
                    log_content = self.read_log_file("agente_stdout.log", lines=50)
                    return {"success": True, "logs": log_content, "file": "agente_stdout.log"}
                except Exception as e:
                    return {"success": False, "message": f"Error leyendo logs: {str(e)}"}
            
            elif command.startswith("set_name:"):
                console.print("[yellow]✏️  Ejecutando: Cambiar Nombre de Máquina[/yellow]")
                try:
                    # Extraer el nombre del comando (formato: "set_name:Nuevo Nombre")
                    new_name = command.split(":", 1)[1].strip()
                    if not new_name:
                        return {"success": False, "message": "El nombre no puede estar vacío"}
                    
                    if self.save_custom_name(new_name):
                        console.print(f"[green]✅ Nombre cambiado a: {new_name}[/green]")
                        return {"success": True, "message": f"Nombre cambiado a: {new_name}"}
                    else:
                        return {"success": False, "message": "Error al guardar el nombre"}
                except Exception as e:
                    return {"success": False, "message": f"Error al cambiar nombre: {str(e)}"}
            
            elif command == "take_screenshot":
                console.print("[yellow]📸 Ejecutando: Captura de Pantalla[/yellow]")
                try:
                    screenshot_base64 = self.take_screenshot()
                    if screenshot_base64:
                        console.print(f"[green]✅ Captura realizada ({len(screenshot_base64)} bytes)[/green]")
                        return {
                            "success": True, 
                            "message": "Captura de pantalla realizada",
                            "screenshot": screenshot_base64,
                            "format": "jpeg"
                        }
                    else:
                        return {"success": False, "message": "Error al capturar pantalla"}
                except Exception as e:
                    return {"success": False, "message": f"Error al capturar: {str(e)}"}
            
            else:
                return {"success": False, "message": f"Comando desconocido: {command}"}
        
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def read_log_file(self, filename: str, lines: int = 100) -> str:
        """Lee las últimas N líneas de un archivo de log"""
        try:
            if not os.path.exists(filename):
                return f"[Archivo {filename} no encontrado]"
            
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(last_lines)
        except Exception as e:
            return f"[Error leyendo {filename}: {str(e)}]"
    
    def is_rotador_running(self) -> bool:
        """Verifica si el RotadorSimBank está corriendo actualmente"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and any('RotadorSimBank' in str(arg) for arg in cmdline):
                            # Verificar que no sea el agente mismo
                            if not any('--agente' in str(arg) for arg in cmdline):
                                return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return False
        except:
            return False
    
    def auto_restart_herosms_periodicamente(self):
        """Reinicia Hero-SMS cada 2 horas automáticamente (solo si no está corriendo el rotador)"""
        tiempo_transcurrido = time.time() - self.ultimo_reinicio_herosms
        horas_transcurridas = tiempo_transcurrido / 3600
        
        if horas_transcurridas >= 2:
            # Verificar si el rotador está corriendo
            if self.is_rotador_running():
                console.print(f"[dim]⏭️  Saltando reinicio de Hero-SMS: Rotador está en ejecución[/dim]")
                self.ultimo_reinicio_herosms = time.time()  # Reset timer
                return
            
            # Verificar si Hero-SMS está corriendo
            herosms_status = self.check_service_status("HeroSMS-Partners.exe")
            
            if herosms_status["status"] == "running":
                console.print(f"\n[cyan]⏰ Han pasado 2 horas. Reiniciando Hero-SMS automáticamente...[/cyan]")
                try:
                    # Cerrar Hero-SMS
                    subprocess.run(["taskkill", "/F", "/IM", "HeroSMS-Partners.exe"], 
                                 capture_output=True, timeout=10)
                    time.sleep(2)
                    
                    # Abrir Hero-SMS
                    user = os.environ.get("USERNAME", "")
                    shortcut_path = f"C:\\Users\\{user}\\Desktop\\HeroSMS-Partners.lnk"
                    if os.path.exists(shortcut_path):
                        os.startfile(shortcut_path)
                        console.print(f"[green]✅ Hero-SMS reiniciado automáticamente[/green]")
                    else:
                        console.print(f"[yellow]⚠️ No se encontró acceso directo de Hero-SMS[/yellow]")
                except Exception as e:
                    console.print(f"[red]❌ Error reiniciando Hero-SMS: {e}[/red]")
            else:
                console.print(f"[dim]💤 Hero-SMS no está corriendo, saltando reinicio automático[/dim]")
            
            self.ultimo_reinicio_herosms = time.time()
    
    def verificar_actualizaciones_periodicas(self):
        """Verifica actualizaciones cada 24 horas automáticamente"""
        tiempo_transcurrido = time.time() - self.ultima_verificacion_actualizacion
        horas_transcurridas = tiempo_transcurrido / 3600
        
        if horas_transcurridas >= 24:
            console.print(f"\n[cyan]🔍 Han pasado {int(horas_transcurridas)} horas. Verificando actualizaciones...[/cyan]")
            try:
                hay_actualizacion, version_remota = verificar_actualizacion()
                if hay_actualizacion:
                    console.print(f"[bold green]🆕 ¡Nueva versión disponible: v{version_remota}![/bold green]")
                    console.print(f"[yellow]📥 Actualizando automáticamente...[/yellow]")
                    if actualizar_script():
                        console.print(f"[green]✅ Actualizado exitosamente a v{version_remota}[/green]")
                        # El script se reiniciará automáticamente por actualizar_script()
                    else:
                        console.print(f"[red]❌ Error al descargar la actualización[/red]")
                else:
                    console.print(f"[green]✅ Ya estás usando la última versión (v{Settings.VERSION})[/green]")
                
                self.ultima_verificacion_actualizacion = time.time()
            except Exception as e:
                console.print(f"[red]❌ Error verificando actualizaciones: {e}[/red]")
                self.ultima_verificacion_actualizacion = time.time()
    
    def send_heartbeat(self):
        """Envía el estado del sistema al dashboard"""
        herosms_status = self.check_service_status("HeroSMS-Partners.exe")
        rotador_running = self.is_rotador_running()
        
        status = {
            "system": self.get_system_status(),
            "services": {
                "herosms": herosms_status,
                "rotador": {
                    "status": "running" if rotador_running else "stopped",
                    "display": "✅ Running" if rotador_running else "❌ Stopped"
                }
            },
            "timers": {
                "next_update_check": int(24 - ((time.time() - self.ultima_verificacion_actualizacion) / 3600)),
                "next_herosms_restart": int(2 - ((time.time() - self.ultimo_reinicio_herosms) / 3600))
            },
            "machine_info": {
                "custom_name": self.custom_name,
                "original_hostname": self.machine_id
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "machine_id": self.machine_id,
                    "action": "heartbeat",
                    "status": status,
                    "custom_name": self.custom_name  # Enviar también en el nivel superior
                },
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=10
            )
            if response.status_code == 200:
                herosms_display = herosms_status.get("display", "❓ Unknown")
                rotador_display = "✅ Running" if rotador_running else "❌ Stopped"
                console.print(f"[dim]💓 Heartbeat [{self.custom_name}] - CPU: {status['system']['cpu_percent']}% | Hero-SMS: {herosms_display} | Rotador: {rotador_display}[/dim]")
        except Exception as e:
            console.print(f"[red]❌ Error enviando heartbeat: {e}[/red]")
    
    def poll_commands(self):
        """Consulta si hay comandos pendientes"""
        try:
            response = requests.post(
                self.api_url,
                json={
                    "machine_id": self.machine_id,
                    "action": "poll"
                },
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("has_command"):
                    command = data["command"]
                    console.print(f"\n[bold cyan]📥 Comando recibido: {command}[/bold cyan]")
                    
                    # Ejecutar comando
                    result = self.execute_command(command)
                    console.print(f"[green]✅ Resultado: {result}[/green]")
                    
                    # Reportar resultado
                    report_response = requests.post(
                        self.api_url,
                        json={
                            "machine_id": self.machine_id,
                            "action": "report",
                            "command": command,
                            "result": result,
                            "timestamp": datetime.now().isoformat()
                        },
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                        timeout=10
                    )
                    
                    if report_response.status_code == 200:
                        console.print("[dim]📤 Resultado reportado al dashboard[/dim]\n")
        
        except Exception as e:
            console.print(f"[red]❌ Error consultando comandos: {e}[/red]")
    
    def run(self):
        """Bucle principal del agente"""
        try:
            # Log inicial (incluso si rich console falla)
            try:
                console.print("=" * 60)
                console.print(f"[bold cyan]🤖 AGENTE DE CONTROL REMOTO - SIMBANK v{Settings.VERSION}[/bold cyan]")
                console.print("=" * 60)
                console.print(f"[cyan]📍 Máquina: {self.machine_id}[/cyan]")
                console.print(f"[cyan]📡 API: {self.api_url}[/cyan]")
                console.print(f"[cyan]⏱️  Intervalo: {self.poll_interval}s[/cyan]")
                console.print("=" * 60)
                console.print("\n[green]✅ Agente iniciado. Presiona Ctrl+C para detener.[/green]\n")
            except Exception as e:
                # Fallback si rich console falla
                print(f"AGENTE INICIADO - v{Settings.VERSION}")
                print(f"Error en rich console: {e}")
            
            while True:
                try:
                    # Verificar actualizaciones cada 24 horas
                    self.verificar_actualizaciones_periodicas()
                    
                    # Reiniciar Hero-SMS cada 2 horas (solo si no está corriendo el rotador)
                    self.auto_restart_herosms_periodicamente()
                    
                    # Enviar estado
                    self.send_heartbeat()
                    
                    # Consultar comandos
                    self.poll_commands()
                    
                    # Esperar antes de la siguiente iteración
                    time.sleep(self.poll_interval)
                
                except KeyboardInterrupt:
                    try:
                        console.print("\n\n[yellow]👋 Agente detenido por el usuario[/yellow]")
                    except:
                        print("\nAgente detenido por el usuario")
                    break
                except Exception as e:
                    try:
                        console.print(f"[red]❌ Error inesperado: {e}[/red]")
                    except:
                        print(f"Error inesperado: {e}")
                    time.sleep(self.poll_interval)
        except Exception as e:
            # Error crítico en la inicialización
            try:
                with open("agente_error.log", "a", encoding="utf-8") as f:
                    f.write(f"\n[{datetime.now()}] ERROR CRÍTICO AL INICIAR AGENTE:\n")
                    f.write(f"{str(e)}\n")
                    import traceback
                    f.write(traceback.format_exc())
            except:
                pass
            raise

def instalar_servicio_windows():
    """Instala el agente como servicio de Windows usando NSSM"""
    console.print("\n[bold cyan]🔧 INSTALANDO AGENTE COMO SERVICIO DE WINDOWS[/bold cyan]")
    console.print("=" * 70 + "\n")
    
    # Verificar permisos de administrador
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            console.print("[red]❌ Este script debe ejecutarse como Administrador[/red]")
            console.print("[yellow]Click derecho en el .bat y selecciona 'Ejecutar como administrador'[/yellow]")
            return False
    except:
        pass
    
    # Descargar NSSM si no existe
    nssm_path = os.path.join(os.getcwd(), "nssm.exe")
    if not os.path.exists(nssm_path):
        console.print("[cyan]📥 Descargando NSSM...[/cyan]")
        try:
            # Intentar descarga con certificados deshabilitados (fix para Python 3.11+)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(
                "https://nssm.cc/release/nssm-2.24.zip",
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                with open("nssm.zip", 'wb') as out_file:
                    out_file.write(response.read())
            
            import zipfile
            with zipfile.ZipFile("nssm.zip", 'r') as zip_ref:
                zip_ref.extractall(".")
            
            shutil.copy("nssm-2.24/win64/nssm.exe", "nssm.exe")
            os.remove("nssm.zip")
            shutil.rmtree("nssm-2.24")
            
            console.print("[green]✅ NSSM descargado[/green]")
        except Exception as e:
            console.print(f"[red]❌ Error descargando NSSM: {e}[/red]")
            console.print("\n[yellow]📥 Descarga manual de NSSM:[/yellow]")
            console.print("[yellow]1. Ve a: https://nssm.cc/release/nssm-2.24.zip[/yellow]")
            console.print("[yellow]2. Descarga el archivo[/yellow]")
            console.print("[yellow]3. Extrae 'nssm-2.24\\win64\\nssm.exe'[/yellow]")
            console.print(f"[yellow]4. Copia nssm.exe a: {os.getcwd()}[/yellow]")
            console.print("[yellow]5. Ejecuta este comando de nuevo[/yellow]\n")
            return False
    
    # Detener servicio si ya existe
    console.print("[cyan]🛑 Deteniendo servicio existente (si existe)...[/cyan]")
    subprocess.run([nssm_path, "stop", "AgenteRotadorSimBank"], capture_output=True)
    subprocess.run([nssm_path, "remove", "AgenteRotadorSimBank", "confirm"], capture_output=True)
    
    # Instalar servicio
    console.print("[cyan]📦 Instalando servicio...[/cyan]")
    current_dir = os.getcwd()
    script_path = os.path.abspath(__file__)
    python_exe = sys.executable
    
    # Comando que ejecutará el servicio
    cmd = [python_exe, script_path, "--agente"]
    
    result = subprocess.run(
        [nssm_path, "install", "AgenteRotadorSimBank", python_exe, script_path, "--agente"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        console.print(f"[red]❌ Error instalando servicio: {result.stderr}[/red]")
        return False
    
    # Configurar servicio
    subprocess.run([nssm_path, "set", "AgenteRotadorSimBank", "AppDirectory", current_dir])
    subprocess.run([nssm_path, "set", "AgenteRotadorSimBank", "DisplayName", "Agente Rotador SimBank"])
    subprocess.run([nssm_path, "set", "AgenteRotadorSimBank", "Description", "Servicio de control remoto para RotadorSimBank"])
    subprocess.run([nssm_path, "set", "AgenteRotadorSimBank", "Start", "SERVICE_AUTO_START"])
    subprocess.run([nssm_path, "set", "AgenteRotadorSimBank", "AppStdout", os.path.join(current_dir, "agente_stdout.log")])
    subprocess.run([nssm_path, "set", "AgenteRotadorSimBank", "AppStderr", os.path.join(current_dir, "agente_stderr.log")])
    subprocess.run([nssm_path, "set", "AgenteRotadorSimBank", "AppRotateFiles", "1"])
    subprocess.run([nssm_path, "set", "AgenteRotadorSimBank", "AppRotateBytes", "1048576"])
    
    # Iniciar servicio
    console.print("[cyan]▶️  Iniciando servicio...[/cyan]")
    result = subprocess.run([nssm_path, "start", "AgenteRotadorSimBank"], capture_output=True, text=True)
    
    if result.returncode == 0:
        # Esperar un momento y verificar el estado
        time.sleep(3)
        status_result = subprocess.run([nssm_path, "status", "AgenteRotadorSimBank"], capture_output=True, text=True)
        
        if "SERVICE_RUNNING" in status_result.stdout:
            console.print("\n[bold green]✅ SERVICIO INSTALADO Y INICIADO EXITOSAMENTE[/bold green]\n")
            console.print("[green]El agente ahora está corriendo como servicio de Windows.[/green]")
            console.print("[green]Se iniciará automáticamente al encender el PC.[/green]\n")
            console.print("[cyan]Comandos útiles:[/cyan]")
            console.print(f"[dim]  - Ver estado: {nssm_path} status AgenteRotadorSimBank[/dim]")
            console.print(f"[dim]  - Detener: {nssm_path} stop AgenteRotadorSimBank[/dim]")
            console.print(f"[dim]  - Reiniciar: {nssm_path} restart AgenteRotadorSimBank[/dim]")
            console.print(f"[dim]  - Desinstalar: {nssm_path} remove AgenteRotadorSimBank confirm[/dim]")
            console.print(f"[dim]  - Ver logs: type agente_stdout.log[/dim]\n")
            return True
        elif "SERVICE_PAUSED" in status_result.stdout:
            console.print(f"[yellow]⚠️ El servicio está en estado PAUSED[/yellow]")
            console.print(f"[yellow]Esto suele significar que el script falló al iniciar.[/yellow]\n")
            console.print(f"[cyan]Diagnóstico:[/cyan]")
            console.print(f"[dim]1. Verifica los logs: type agente_stdout.log[/dim]")
            console.print(f"[dim]2. Verifica errores: type agente_stderr.log[/dim]")
            console.print(f"[dim]3. Prueba manualmente: python RotadorSimBank.py --agente[/dim]")
            console.print(f"[dim]4. Reinicia el servicio: {nssm_path} restart AgenteRotadorSimBank[/dim]\n")
            return False
        else:
            console.print(f"[yellow]⚠️ Estado del servicio: {status_result.stdout}[/yellow]")
            console.print(f"[yellow]El servicio no está en ejecución normal.[/yellow]\n")
            return False
    else:
        console.print(f"[red]❌ Error iniciando servicio: {result.stderr}[/red]")
        console.print(f"\n[cyan]Intenta:[/cyan]")
        console.print(f"[dim]1. Ejecutar como Administrador[/dim]")
        console.print(f"[dim]2. Probar manualmente: python RotadorSimBank.py --agente[/dim]")
        console.print(f"[dim]3. Verificar que todas las dependencias estén instaladas[/dim]\n")
        return False

if __name__ == "__main__":
    # Si se ejecuta con --agente, iniciar el agente de control remoto
    if len(sys.argv) > 1 and sys.argv[1] == "--agente":
        agente = AgenteControlRemoto()
        agente.run()
    # Si se ejecuta con --instalar-servicio, instalar como servicio de Windows
    elif len(sys.argv) > 1 and sys.argv[1] == "--instalar-servicio":
        instalar_servicio_windows()
    # Si no, ejecutar el rotador normal
    else:
        main()

