# 🔧 Solución: "pip no se reconoce como comando"

## ❌ Problema

Al ejecutar `INSTALAR.bat` aparece:
```
"pip" no se reconoce como un comando interno o externo,
programa o archivo por lotes ejecutable.
```

---

## 🎯 Causa

Python no está instalado o no está en el PATH de Windows.

---

## ✅ Soluciones

### Solución 1: Reinstalar Python correctamente

1. **Descargar Python:**
   - Ve a: https://www.python.org/downloads/
   - Descarga Python 3.11 o superior

2. **Instalar Python:**
   - **MUY IMPORTANTE:** Marca la casilla:
     ```
     ☑ Add Python to PATH
     ```
   - Click en "Install Now"

3. **Verificar instalación:**
   ```bash
   python --version
   ```
   Debe mostrar: `Python 3.x.x`

4. **Ejecutar de nuevo:**
   ```bash
   INSTALAR.bat
   ```

---

### Solución 2: Agregar Python al PATH manualmente

Si ya tienes Python instalado pero no está en el PATH:

1. **Buscar donde está Python:**
   - Ubicaciones comunes:
     - `C:\Python311\`
     - `C:\Users\TuUsuario\AppData\Local\Programs\Python\Python311\`
     - `C:\Program Files\Python311\`

2. **Agregar al PATH:**
   - Click derecho en "Este equipo" → Propiedades
   - "Configuración avanzada del sistema"
   - "Variables de entorno"
   - En "Variables del sistema", buscar "Path"
   - Click "Editar"
   - Click "Nuevo"
   - Agregar la ruta de Python (ej: `C:\Python311\`)
   - Agregar también: `C:\Python311\Scripts\`
   - Click "Aceptar" en todo

3. **Reiniciar el CMD y probar:**
   ```bash
   python --version
   pip --version
   ```

---

### Solución 3: Usar INSTALAR_SIMPLE.bat

Usa la versión simplificada que hemos creado:

```bash
INSTALAR_SIMPLE.bat
```

Este script:
- Verifica que Python esté instalado
- Usa `python -m pip` (más compatible)
- Da mensajes claros de error

---

### Solución 4: Instalación manual

Si todo lo anterior falla, instala manualmente:

```bash
# Abrir PowerShell o CMD
python -m pip install --upgrade pip
python -m pip install pyserial rich psycopg2-binary requests psutil
```

---

## 🧪 Verificar que Python está correctamente instalado

```bash
# Debe mostrar la versión de Python
python --version

# Debe mostrar la versión de pip
python -m pip --version

# Si ambos funcionan, estás listo!
```

---

## 📋 Checklist de Instalación de Python

```
☐ Descargar Python desde python.org
☐ Durante instalación, marcar "Add Python to PATH"
☐ Completar instalación
☐ Abrir nuevo CMD/PowerShell
☐ Ejecutar: python --version
☐ Ejecutar: python -m pip --version
☐ Si ambos funcionan → Ejecutar INSTALAR.bat
```

---

## 🆘 Si nada funciona

**Opción 1: Desinstalar y reinstalar Python completamente**

1. Panel de Control → Desinstalar programas
2. Desinstalar todas las versiones de Python
3. Reiniciar el PC
4. Instalar Python de nuevo (marcando "Add to PATH")

**Opción 2: Usar Python desde Microsoft Store**

1. Abrir Microsoft Store
2. Buscar "Python 3.11"
3. Instalar
4. Automáticamente se agrega al PATH
5. Probar con `python --version`

---

## ✅ Después de solucionar

Una vez que `python --version` funcione correctamente:

```bash
# Ejecutar instalación completa
INSTALAR.bat

# O instalación simple
INSTALAR_SIMPLE.bat
```

---

## 💡 Tip

Si usas Python desde Microsoft Store, puede que aparezca como `python3` en lugar de `python`:

```bash
# Probar ambos
python --version
python3 --version

# Si python3 funciona, crear un alias o usar python3 en los comandos
```
