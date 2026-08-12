"""Crea cuentas aisladas para una ejecución de Locust.

Nunca usa participantes o administradores existentes. Las cuentas creadas se
identifican por el prefijo ``loadtest_e<evaluacion>_`` y sus credenciales se
escriben sólo en archivos ignorados por Git.
"""

import csv
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.crypto import get_random_string

from quizzes.models import (
    AdminProfile,
    Evaluacion,
    GrupoParticipantes,
    IntentosParticipante,
    Participantes,
    ResultadoEvaluacion,
)


class Command(BaseCommand):
    help = (
        "Crea participantes y monitores aislados para Locust, asignados a una "
        "evaluación sin tocar cuentas reales."
    )

    def add_arguments(self, parser):
        parser.add_argument("--evaluation", type=int, required=True, help="ID de la evaluación.")
        parser.add_argument("--students", type=int, required=True, help="Cantidad de estudiantes de prueba.")
        parser.add_argument("--admins", type=int, default=2, help="Cantidad de monitores de prueba (por defecto: 2).")
        parser.add_argument("--attempts", type=int, default=1, help="Intentos por estudiante (por defecto: 1).")
        parser.add_argument(
            "--reset-results",
            action="store_true",
            help="Elimina únicamente resultados previos de estas cuentas de prueba en esta EVA.",
        )

    def handle(self, *args, **options):
        evaluation_id = options["evaluation"]
        students_count = options["students"]
        admins_count = options["admins"]
        attempts = options["attempts"]

        if students_count < 1:
            raise CommandError("--students debe ser al menos 1.")
        if admins_count < 1:
            raise CommandError("--admins debe ser al menos 1.")
        if attempts < 1:
            raise CommandError("--attempts debe ser al menos 1.")
        if evaluation_id > 999:
            raise CommandError("El ID de evaluación debe ser menor de 1000 para generar cédulas de prueba.")

        evaluacion = Evaluacion.objects.select_related("concurso", "concurso__carrera").filter(pk=evaluation_id).first()
        if not evaluacion:
            raise CommandError(f"No existe la evaluación {evaluation_id}.")

        prefix = f"loadtest_e{evaluacion.id}_"
        group_name = f"{prefix}grupo"
        password_chars = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@$%"

        existing_students = Participantes.objects.filter(
            user__username__startswith=f"{prefix}student_"
        ).count()
        existing_admins = AdminProfile.objects.filter(
            user__username__startswith=f"{prefix}monitor_"
        ).count()
        if existing_students not in (0, students_count) or existing_admins not in (0, admins_count):
            raise CommandError(
                "Ya existe una preparación de carga con una cantidad distinta de cuentas. "
                "Límpiala primero con limpiar_carga_locust --evaluation "
                f"{evaluacion.id} --confirmar."
            )

        with transaction.atomic():
            grupo, _ = GrupoParticipantes.objects.get_or_create(
                concurso=evaluacion.concurso,
                name=group_name,
                defaults={"anio": evaluacion.anio},
            )
            evaluacion.grupos_participantes.add(grupo)

            students = []
            student_credentials = []
            for number in range(1, students_count + 1):
                username = f"{prefix}student_{number:03d}"
                password = get_random_string(18, allowed_chars=password_chars)
                email = f"{username}@example.test"
                cedula = f"9{evaluacion.id:03d}{number:06d}"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": email,
                        "first_name": f"Carga {number:03d}",
                    },
                )
                self._validar_usuario_prueba(user, username, Participantes)
                user.email = email
                user.first_name = f"Carga {number:03d}"
                user.set_password(password)
                user.save(update_fields=["email", "first_name", "password"])

                participante, participant_created = Participantes.objects.get_or_create(
                    user=user,
                    defaults={
                        "concurso": evaluacion.concurso,
                        "carrera": evaluacion.concurso.carrera,
                        "cedula": cedula,
                        "NombresCompletos": f"Estudiante de carga {number:03d}",
                        "email": email,
                        "phone": "0990000000",
                        "edad": 18,
                        "intentos_maximos_default": attempts,
                    },
                )
                if not participant_created and (
                    participante.concurso_id != evaluacion.concurso_id
                    or participante.carrera_id != evaluacion.concurso.carrera_id
                    or participante.cedula != cedula
                ):
                    raise CommandError(
                        f"La cuenta de prueba {username} no coincide con la EVA solicitada. "
                        "Ejecuta la limpieza específica antes de reutilizarla."
                    )

                participante.NombresCompletos = f"Estudiante de carga {number:03d}"
                participante.email = email
                participante.phone = "0990000000"
                participante.edad = 18
                participante.intentos_maximos_default = attempts
                participante.save()
                students.append(participante)
                student_credentials.append({"username": username, "password": password})

            grupo.participantes.add(*students)
            if evaluacion.etapa != 1:
                evaluacion.participantes_individuales.add(*students)

            if options["reset_results"]:
                ResultadoEvaluacion.objects.filter(
                    evaluacion=evaluacion, participante__in=students
                ).delete()
            elif ResultadoEvaluacion.objects.filter(
                evaluacion=evaluacion, participante__in=students
            ).exists():
                raise CommandError(
                    "Las cuentas de prueba ya tienen resultados en esta EVA. "
                    "Vuelve a ejecutar con --reset-results para borrar sólo esos resultados de prueba."
                )

            for participante in students:
                IntentosParticipante.objects.update_or_create(
                    participante=participante,
                    evaluacion=evaluacion,
                    defaults={
                        "intentos_maximos": attempts,
                        "motivo": "Cuenta aislada creada para prueba de carga con Locust.",
                    },
                )

            admin_credentials = []
            for number in range(1, admins_count + 1):
                username = f"{prefix}monitor_{number:02d}"
                password = get_random_string(18, allowed_chars=password_chars)
                email = f"{username}@example.test"
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={"email": email, "first_name": f"Monitor carga {number:02d}"},
                )
                self._validar_usuario_prueba(user, username, AdminProfile)
                user.email = email
                user.first_name = f"Monitor carga {number:02d}"
                user.set_password(password)
                user.save(update_fields=["email", "first_name", "password"])
                AdminProfile.objects.update_or_create(
                    user=user,
                    defaults={"carrera": evaluacion.concurso.carrera, "acceso_total": False},
                )
                admin_credentials.append({"username": username, "password": password})

            self._escribir_csv("credentials.csv", student_credentials)
            self._escribir_csv("admin_credentials.csv", admin_credentials)

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {students_count} estudiantes y {admins_count} monitores de prueba "
            f"asignados a la EVA {evaluacion.id}."
        ))
        self.stdout.write(
            "Credenciales locales actualizadas en load_tests/credentials.csv y "
            "load_tests/admin_credentials.csv."
        )
        self.stdout.write(
            f"Ejecuta Locust con LOCUST_CONCURSO_ID={evaluacion.concurso_id} y "
            f"-u {students_count + admins_count}."
        )

    @staticmethod
    def _validar_usuario_prueba(user, username, expected_profile):
        if expected_profile.objects.filter(user=user).exists():
            return
        if username.startswith("loadtest_") and not (
            Participantes.objects.filter(user=user).exists()
            or AdminProfile.objects.filter(user=user).exists()
        ):
            return
        raise CommandError(
            f"El usuario existente {username} no es una cuenta de carga compatible; no se modificó."
        )

    @staticmethod
    def _escribir_csv(filename, credentials):
        destination = Path(settings.BASE_DIR) / "load_tests" / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["username", "password"])
            writer.writeheader()
            writer.writerows(credentials)
