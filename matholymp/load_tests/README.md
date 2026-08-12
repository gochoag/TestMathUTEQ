# Pruebas de carga con Locust

Ejecuta los comandos desde `matholymp/`; el proyecto usa `uv`, así que no debes activar el entorno virtual.

Esta herramienta **no usa ni modifica cuentas reales**. Primero se crean cuentas aisladas con el prefijo `loadtest_`; luego Locust sólo acepta credenciales con ese mismo prefijo. Si por error se coloca una cuenta real en un CSV, Locust se detiene antes de enviar solicitudes.

## 1. Preparar cuentas de prueba

El comando crea, para la EVA indicada:

- un grupo exclusivo de carga en el mismo concurso y carrera;
- los estudiantes de prueba dentro de ese grupo y autorizados para la EVA;
- dos administradores de prueba, limitados a la carrera de la EVA;
- los archivos locales `credentials.csv` y `admin_credentials.csv`.

Los dos CSV están ignorados por Git. No necesitas editarlos ni copiar los archivos `.example.csv` cuando usas este comando.

```powershell
uv run python manage.py preparar_carga_locust --evaluation 1 --students 50 --admins 2
```

El comando crea usuarios similares a `loadtest_e1_student_001` y `loadtest_e1_monitor_01`; no altera participantes ni administradores que ya existían. Cada estudiante recibe un intento específico para esa EVA.

Para repetir la prueba con las mismas cuentas, elimina sólo sus resultados anteriores de esa EVA de forma explícita:

```powershell
uv run python manage.py preparar_carga_locust --evaluation 1 --students 50 --admins 2 --reset-results
```

## 2. Ejecutar Django y Locust

En una terminal:

```powershell
uv run python manage.py runserver
```

En otra:

```powershell
$env:LOCUST_EVALUACION_ID = "1"
$env:LOCUST_CONCURSO_ID = "1"
$env:LOCUST_DURATION_MINUTES = "60"
$env:LOCUST_MIN_COMPLETION_SECONDS = "90"
$env:LOCUST_MAX_COMPLETION_SECONDS = "300"
New-Item -ItemType Directory -Force load_tests/reports | Out-Null
uv run locust -f load_tests/locustfile.py --host http://127.0.0.1:8000 --headless -u 52 -r 2 -t 6m --html load_tests/reports/eva-1-50-estudiantes.html
```

`-u 52` representa 50 estudiantes y 2 monitores. Cada estudiante abre la EVA, responde y guarda progreso gradualmente, consulta su estado y entrega una vez entre 90 y 300 segundos. Los dos monitores cargan el panel y consultan su estado cada 10 segundos; usan el mismo concurso de la EVA mediante `LOCUST_CONCURSO_ID`.

La nota es aleatoria: «terminar exitosamente» significa que los 50 formularios se entregan y generan resultados, no que todos obtienen una calificación aprobatoria.

## 3. Limpieza al finalizar

Cuando termines, elimina exclusivamente datos cuyo nombre inicia con `loadtest_e1_`:

```powershell
uv run python manage.py limpiar_carga_locust --evaluation 1 --confirmar
```

La confirmación es obligatoria. El comando elimina los resultados, el grupo, participantes y administradores de prueba de esa EVA; no toca cuentas que no tengan el prefijo de carga.

Locust mide tráfico HTTP y comportamiento del servidor. No ejecuta JavaScript del navegador, por lo que pantalla completa, eventos de visibilidad y modales se validan aparte con pruebas manuales.
