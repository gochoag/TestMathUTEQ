"""Prueba de carga del flujo real de una evaluación y su monitoreo.

Se ejecuta desde ``matholymp``. Las cuentas se leen de archivos locales no
versionados: ``load_tests/credentials.csv`` y
``load_tests/admin_credentials.csv``.
"""

import csv
import os
import random
import re
import time
from collections import defaultdict, deque
from pathlib import Path

from gevent import sleep
from gevent.lock import Semaphore
from locust import HttpUser, constant_pacing, task
from locust.exception import StopUser


EVALUACION_ID = os.getenv("LOCUST_EVALUACION_ID", "1")
DURACION_MINUTOS = int(os.getenv("LOCUST_DURATION_MINUTES", "60"))
CONCURSO_ID = os.getenv("LOCUST_CONCURSO_ID", "")
PREFIJO_USUARIOS = os.getenv("LOCUST_USER_PREFIX", "loadtest_")
MIN_FINALIZACION_SEGUNDOS = int(os.getenv("LOCUST_MIN_COMPLETION_SECONDS", "90"))
MAX_FINALIZACION_SEGUNDOS = int(os.getenv("LOCUST_MAX_COMPLETION_SECONDS", "300"))
ARCHIVO_CREDENCIALES = Path(__file__).with_name("credentials.csv")
ARCHIVO_ADMINS = Path(__file__).with_name("admin_credentials.csv")

if MIN_FINALIZACION_SEGUNDOS > MAX_FINALIZACION_SEGUNDOS:
    raise RuntimeError(
        "LOCUST_MIN_COMPLETION_SECONDS no puede ser mayor que "
        "LOCUST_MAX_COMPLETION_SECONDS."
    )


def cargar_credenciales(archivo, descripcion):
    """Carga cuentas únicas de un CSV local con columnas username,password."""
    if not archivo.exists():
        raise RuntimeError(
            f"Falta {archivo.name}. Copia su archivo .example.csv y reemplaza "
            f"los datos por cuentas de {descripcion}."
        )

    with archivo.open(newline="", encoding="utf-8") as archivo_csv:
        credenciales = deque(
            fila
            for fila in csv.DictReader(archivo_csv)
            if fila.get("username") and fila.get("password")
        )

    if not credenciales:
        raise RuntimeError(f"{archivo.name} no contiene credenciales válidas.")
    cuentas_no_prueba = [
        fila["username"]
        for fila in credenciales
        if not fila["username"].startswith(PREFIJO_USUARIOS)
    ]
    if cuentas_no_prueba:
        raise RuntimeError(
            f"{archivo.name} contiene cuentas fuera del prefijo de prueba "
            f"'{PREFIJO_USUARIOS}': {', '.join(cuentas_no_prueba)}. "
            "Locust no usará cuentas reales."
        )
    return credenciales


CREDENCIALES_ESTUDIANTES = cargar_credenciales(
    ARCHIVO_CREDENCIALES, "participantes autorizados"
)
CREDENCIALES_ADMINS = cargar_credenciales(ARCHIVO_ADMINS, "administradores")
BLOQUEO_ESTUDIANTES = Semaphore()
BLOQUEO_ADMINS = Semaphore()


def tomar_credencial(credenciales, bloqueo):
    """Asigna una cuenta a un único usuario simulado, sin reutilizar sesiones."""
    with bloqueo:
        return credenciales.popleft() if credenciales else None


def extraer_csrf(html):
    coincidencia = re.search(
        r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', html
    )
    if not coincidencia:
        raise RuntimeError("No se encontró el token CSRF en la página de inicio de sesión.")
    return coincidencia.group(1)


def iniciar_sesion(usuario, username, password):
    pagina = usuario.client.get("/login/", name="GET /login/")
    csrf = extraer_csrf(pagina.text)

    with usuario.client.post(
        "/login/",
        data={
            "username": username,
            "password": password,
            "csrfmiddlewaretoken": csrf,
        },
        headers={"Referer": f"{usuario.host}/login/"},
        allow_redirects=False,
        name="POST /login/",
        catch_response=True,
    ) as respuesta:
        if respuesta.status_code not in (302, 303):
            respuesta.failure(f"Login falló: HTTP {respuesta.status_code}")
            raise StopUser()


class EstudianteEvaluacion(HttpUser):
    """Simula un estudiante: entra, responde, guarda y entrega la evaluación."""

    wait_time = constant_pacing(5)

    def on_start(self):
        credencial = tomar_credencial(CREDENCIALES_ESTUDIANTES, BLOQUEO_ESTUDIANTES)
        if not credencial:
            raise StopUser()

        iniciar_sesion(self, credencial["username"], credencial["password"])

        with self.client.get(
            f"/quiz/{EVALUACION_ID}/",
            name="GET /quiz/[id]/",
            catch_response=True,
        ) as respuesta:
            pares = re.findall(
                r'name="(pregunta_\d+)"\s+value="(\d+)"', respuesta.text
            )
            if respuesta.status_code != 200 or not pares:
                respuesta.failure(
                    "No se cargaron preguntas. La cuenta debe estar autorizada para "
                    "la evaluación y tener al menos un intento disponible."
                )
                raise StopUser()

        self.opciones = defaultdict(list)
        for pregunta, opcion in pares:
            self.opciones[pregunta].append(opcion)

        self.respuestas = {}
        self.preguntas_pendientes = list(self.opciones)
        random.shuffle(self.preguntas_pendientes)
        self.inicio = time.monotonic()
        self.momento_finalizacion = self.inicio + random.uniform(
            MIN_FINALIZACION_SEGUNDOS, MAX_FINALIZACION_SEGUNDOS
        )
        self.ciclo = 0

    def registrar_respuestas(self, cantidad):
        """Responde algunas preguntas para que los guardados sean progresivos."""
        for _ in range(min(cantidad, len(self.preguntas_pendientes))):
            pregunta = self.preguntas_pendientes.pop()
            self.respuestas[pregunta] = random.choice(self.opciones[pregunta])

    def tiempo_restante(self):
        transcurrido = int(time.monotonic() - self.inicio)
        return max(0, DURACION_MINUTOS * 60 - transcurrido)

    def guardar_progreso(self):
        self.registrar_respuestas(random.randint(1, 2))
        csrf = self.client.cookies.get("csrftoken", "")
        self.client.post(
            f"/quiz/{EVALUACION_ID}/guardar/",
            json={"respuestas": self.respuestas},
            headers={
                "X-CSRFToken": csrf,
                "Referer": f"{self.host}/quiz/{EVALUACION_ID}/",
            },
            name="POST /quiz/[id]/guardar/",
        )

    def finalizar_evaluacion(self):
        """Entrega todas las respuestas mediante el POST normal del formulario."""
        self.registrar_respuestas(len(self.preguntas_pendientes))
        csrf = self.client.cookies.get("csrftoken", "")
        datos = {
            "csrfmiddlewaretoken": csrf,
            "tiempo_restante": str(self.tiempo_restante()),
            **self.respuestas,
        }

        with self.client.post(
            f"/quiz/{EVALUACION_ID}/",
            data=datos,
            headers={"Referer": f"{self.host}/quiz/{EVALUACION_ID}/"},
            name="POST /quiz/[id]/entregar/",
            catch_response=True,
        ) as respuesta:
            if respuesta.status_code != 200 or "Evaluación completada" not in respuesta.text:
                respuesta.failure(
                    "La entrega no produjo la página de resultado de la evaluación."
                )
                raise StopUser()

        raise StopUser()

    @task
    def actividad_de_evaluacion(self):
        """Reproduce verificaciones cada 15 s y guardados cada 30 s."""
        if time.monotonic() >= self.momento_finalizacion:
            self.finalizar_evaluacion()

        self.ciclo += 1
        if self.ciclo % 3 == 0:
            self.client.get(
                f"/quiz/{EVALUACION_ID}/verificar-estado/",
                name="GET /quiz/[id]/verificar-estado/",
            )

        if self.ciclo % 6 == 0:
            self.guardar_progreso()


class AdministradorMonitoreo(HttpUser):
    """Mantiene cada panel administrativo consultando el monitoreo cada 10 s."""

    fixed_count = len(CREDENCIALES_ADMINS)
    wait_time = constant_pacing(10)

    def on_start(self):
        credencial = tomar_credencial(CREDENCIALES_ADMINS, BLOQUEO_ADMINS)
        if not credencial:
            raise StopUser()

        iniciar_sesion(self, credencial["username"], credencial["password"])
        if CONCURSO_ID:
            self.client.get(
                f"/cambiar-contexto/?concurso_id={CONCURSO_ID}",
                allow_redirects=False,
                name="GET /cambiar-contexto/",
            )
        self.client.get(
            f"/evaluacion/{EVALUACION_ID}/monitoreo/",
            name="GET /evaluacion/[id]/monitoreo/",
        )
        # Dos personas no abren el monitor exactamente en el mismo milisegundo.
        sleep(random.uniform(0, 5))

    @task
    def consultar_monitoreo(self):
        self.client.get(
            f"/evaluacion/{EVALUACION_ID}/monitoreo/estado/",
            name="GET /evaluacion/[id]/monitoreo/estado/",
        )
