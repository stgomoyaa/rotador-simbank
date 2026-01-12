# 📝 GUÍA DE GIT - Rotador SimBank

## 🚀 CONFIGURACIÓN INICIAL

### Opción 1: Script Automático (Recomendado)

1. **Ejecutar configuración inicial:**
   ```cmd
   git_setup.bat
   ```
   - Te pedirá tu nombre y email
   - Configurará el repositorio remoto automáticamente

2. **Hacer push:**
   ```cmd
   git_push.bat
   ```
   - Agregará todos los archivos
   - Creará el commit
   - Hará push a GitHub

### Opción 2: Comandos Manuales

Si prefieres hacerlo manualmente:

```bash
# 1. Inicializar repositorio (si no existe)
git init

# 2. Configurar usuario
git config user.name "Tu Nombre"
git config user.email "tu@email.com"

# 3. Agregar repositorio remoto
git remote add origin https://github.com/stgomoyaa/rotador-simbank.git

# 4. Agregar archivos
git add .

# 5. Hacer commit
git commit -m "v2.6.0: Added auto-update, PostgreSQL integration, and database export"

# 6. Hacer push
git push -u origin main
```

⚠️ **Nota:** Si tu rama principal se llama `master` en lugar de `main`, usa:
```bash
git push -u origin master
```

---

## 🔐 AUTENTICACIÓN DE GITHUB

### Si te pide usuario y contraseña:

GitHub ya no acepta contraseñas. Necesitas usar **Personal Access Token (PAT)**.

#### Crear un Token:

1. Ve a GitHub: https://github.com/settings/tokens
2. Click en "Generate new token" → "Generate new token (classic)"
3. Dale un nombre: `rotador-simbank-token`
4. Marca el checkbox: `repo` (full control)
5. Click en "Generate token"
6. **COPIA EL TOKEN** (solo se muestra una vez)

#### Usar el Token:

Cuando Git te pida la contraseña, **pega el token** en lugar de tu contraseña:
```
Username: stgomoyaa
Password: ghp_XXXXXXXXXXXXXXXXXXXXXX  ← (tu token)
```

### Guardar Credenciales (opcional)

Para no tener que ingresar el token cada vez:

```bash
# Windows
git config --global credential.helper wincred

# O usar URL con token
git remote set-url origin https://stgomoyaa:TU_TOKEN@github.com/stgomoyaa/rotador-simbank.git
```

---

## 📁 ESTRUCTURA DEL REPOSITORIO

Tu repositorio debería tener estos archivos:

```
rotador-simbank/
├── RotadorSimBank.py          ← Script principal
├── CHANGELOG_v2.6.0.md        ← Documentación de cambios
├── GUIA_RAPIDA_v2.6.0.md      ← Guía de usuario
├── RESUMEN_IMPLEMENTACION_v2.6.0.md
├── INFORME_ANALISIS_COMPLETO.md
├── EJECUTAR.bat               ← Script para ejecutar
├── INSTALAR.bat               ← Script para instalar dependencias
├── README.txt                 ← README básico
├── git_setup.bat              ← Este archivo (setup)
├── git_push.bat               ← Este archivo (push)
└── README_GIT.md              ← Esta guía
```

**Archivos que NO deberías subir:**
- `listadonumeros_claro.txt` (datos privados)
- `rotador_simbank.log` (logs locales)
- `rotador_state.json` (estado local)
- `*.backup` (archivos de backup)

Para ignorarlos, crea un archivo `.gitignore`:

```
# Ignorar datos privados y archivos temporales
listadonumeros_claro.txt
*.log
rotador_state.json
rotador_metrics.json
iccids_history.json
*.backup
*.new
rotador.lock
snapshots/
log_activacion_rotador.txt
```

---

## 🔄 FLUJO DE TRABAJO

### Primera vez (Setup):
```bash
git_setup.bat     # Configurar repositorio
git_push.bat      # Subir archivos a GitHub
```

### Cada vez que hagas cambios:
```bash
git_push.bat      # Commit y push automático
```

O manualmente:
```bash
git add .
git commit -m "Descripción de cambios"
git push
```

---

## ✅ VERIFICAR QUE FUNCIONA

Después de hacer push, verifica:

1. **En GitHub:**
   - Ve a: https://github.com/stgomoyaa/rotador-simbank
   - Deberías ver `RotadorSimBank.py` y los demás archivos

2. **Probar auto-actualización:**
   ```bash
   python RotadorSimBank.py --update
   ```
   Debería decir:
   ```
   🔍 Verificando actualizaciones...
   ✅ Estás usando la versión más reciente (v2.6.0)
   ```

3. **Simular actualización:**
   - Cambia la versión en línea 38 a `2.5.9`
   - Ejecuta: `python RotadorSimBank.py`
   - Debería detectar que hay una versión más nueva (2.6.0) en GitHub

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Error: "Git is not recognized"

**Solución:** Instalar Git
1. Descarga: https://git-scm.com/download/win
2. Instala con opciones por defecto
3. Reinicia la terminal

### Error: "Permission denied (publickey)"

**Solución:** Usar HTTPS en lugar de SSH
```bash
git remote set-url origin https://github.com/stgomoyaa/rotador-simbank.git
```

### Error: "Authentication failed"

**Solución:** Usar Personal Access Token (ver arriba)

### Error: "Failed to push some refs"

**Solución:** Hacer pull primero
```bash
git pull origin main --rebase
git push origin main
```

### Error: "Repository not found"

**Solución:** Verificar que el repositorio existe en GitHub
- Ve a: https://github.com/stgomoyaa/rotador-simbank
- Si no existe, créalo en: https://github.com/new

---

## 📚 COMANDOS ÚTILES

```bash
# Ver estado
git status

# Ver historial
git log --oneline -n 10

# Ver ramas
git branch

# Crear nueva rama
git checkout -b feature/nueva-funcionalidad

# Cambiar de rama
git checkout main

# Ver cambios
git diff

# Deshacer cambios (peligroso)
git reset --hard HEAD

# Ver repositorio remoto
git remote -v
```

---

## 🎯 PRÓXIMOS PASOS

1. ✅ Ejecutar `git_setup.bat` (una sola vez)
2. ✅ Ejecutar `git_push.bat` (cada vez que hagas cambios)
3. ✅ Verificar en GitHub que los archivos se subieron
4. ✅ Probar `python RotadorSimBank.py --update`
5. ✅ Crear archivo `.gitignore` para ignorar archivos privados

---

**¿Necesitas ayuda?**
- GitHub Docs: https://docs.github.com/es
- Git Tutorial: https://git-scm.com/book/es/v2

**Versión:** 2.6.0  
**Fecha:** 2026-01-12

