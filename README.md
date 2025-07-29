# Plataforma para Olimpiadas de Matemáticas

Este proyecto para olimpiadas de matemáticas.

## Características básicas

- Gestión de participantes y grupos.
- Creación de cuestionarios con preguntas y opciones de respuesta.
- Resolución de cuestionarios en línea.


## Requisitos

- Python 3.12
- Django 5 (u otra versión compatible)

Instale las dependencias ejecutando:

```bash
pip install -r requirements.txt
```

## Uso

Inicie un servidor de desarrollo con:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Luego acceda a `http://localhost:8000/`.
