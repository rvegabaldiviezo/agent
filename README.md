# Configuración inicial del proyecto

Este proyecto utiliza un **entorno virtual** para aislar las dependencias y evitar conflictos con otras instalaciones de Python en el sistema.

## 1. Crear el entorno virtual

Si aún no existe, crea el entorno virtual llamado `.venv`:

```bash
python -m venv .venv
```

## 2. Activar el entorno virtual

En **Git Bash / MINGW64** (Windows):

```bash
source .venv/Scripts/activate
```
o
```bash
. .venv/Scripts/activate
```

En **cmd** (Windows):

```cmd
.venv\Scripts\activate
```

Cuando el entorno esté activo, el prompt de la terminal mostrará algo como:
```
(.venv) qimk@DESKTOP-B9E83NI ...
```

## 3. Instalar dependencias

Con el entorno virtual activo, instala las librerías necesarias para el proyecto:

```bash
pip install --no-cache-dir -r requirements.txt
```

## 4. Levantar el Agente


```bash
adk web
```


## 5. Levantar el Agente como container

Para levantar por primera vez tenemos asegurarnos que no existan volumenes previos.
```bash
docker-compose down -v
```

Para levantar los containers.
```bash
docker-compose up --build -d
```

## 5. Desactivar el entorno virtual

Cuando termines de trabajar:

```bash
deactivate
```

---

> **Nota:** Siempre activa el entorno virtual antes de trabajar en el proyecto para asegurar que uses las dependencias correctas.
