"""Elimina únicamente datos con el prefijo de pruebas de carga de una EVA."""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from quizzes.models import Evaluacion, GrupoParticipantes, Participantes, ResultadoEvaluacion


class Command(BaseCommand):
    help = "Elimina cuentas y resultados aislados de Locust para una evaluación."

    def add_arguments(self, parser):
        parser.add_argument("--evaluation", type=int, required=True, help="ID de la evaluación.")
        parser.add_argument(
            "--confirmar",
            action="store_true",
            help="Confirma la eliminación irreversible de datos de carga con prefijo loadtest_.",
        )

    def handle(self, *args, **options):
        if not options["confirmar"]:
            raise CommandError("Operación cancelada. Vuelve a ejecutar con --confirmar.")

        evaluacion = Evaluacion.objects.filter(pk=options["evaluation"]).first()
        if not evaluacion:
            raise CommandError(f"No existe la evaluación {options['evaluation']}.")

        prefix = f"loadtest_e{evaluacion.id}_"
        participant_users = User.objects.filter(username__startswith=f"{prefix}student_")
        monitor_users = User.objects.filter(username__startswith=f"{prefix}monitor_")
        participants = Participantes.objects.filter(user__in=participant_users)
        group = GrupoParticipantes.objects.filter(
            concurso=evaluacion.concurso, name=f"{prefix}grupo"
        ).first()

        with transaction.atomic():
            results_count, _ = ResultadoEvaluacion.objects.filter(
                evaluacion=evaluacion, participante__in=participants
            ).delete()
            evaluacion.participantes_individuales.remove(*participants)
            if group:
                evaluacion.grupos_participantes.remove(group)
                group.delete()
            participants.delete()
            participant_users.delete()
            monitor_users.delete()

        self.stdout.write(self.style.SUCCESS(
            f"Eliminados datos de carga de la EVA {evaluacion.id}: {results_count} resultados y "
            f"cuentas con prefijo {prefix}."
        ))
