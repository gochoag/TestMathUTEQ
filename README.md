# Plataforma para Olimpiadas de Matemáticas

Este proyecto para olimpiadas de matemáticas.

## Características básicas

- Gestión de participantes y grupos.
- Creación de cuestionarios con preguntas y opciones de respuesta.
- Resolución de cuestionarios en línea.

## Requisitos

- Python 3.12
- [uv](https://docs.astral.sh/uv/) — gestor de dependencias ultrarrápido

## Instalación (desarrollo local)

```bash
# 1. Instalar uv (si no lo tienes)
#    Windows (PowerShell):  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
#    Linux/macOS:           curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clonar e instalar dependencias
git clone <url-del-repo>
cd TestMathUTEQ
uv sync
```

## Uso (desarrollo local)

```bash
uv run python matholymp/manage.py migrate
uv run python matholymp/manage.py createsuperuser
uv run python matholymp/manage.py runserver
```

Luego acceda a `http://localhost:8000/`.

> Todos los comandos Django se ejecutan con `uv run python ...`, lo que activa
> automáticamente el entorno virtual `.venv` sin necesidad de hacer `activate`.

## Despliegue (Docker)

El proyecto incluye `Dockerfile` y `docker-compose.yml` listos para producción.

```bash
docker compose up -d --build
```

Las dependencias se gestionan con `uv` dentro del contenedor y las versiones
exactas quedan fijadas por `uv.lock` (notablemente más rápido que `pip install`).

## Variables de entorno

Copia `.env.example` a `.env` y configura los valores. Las variables que usa
Django son: `SECRET_KEY`, `DB_*`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`.

## Stack

- Django 5
- MySQL
- uv (gestor de dependencias)
- nginx (reverse proxy con SSL)
