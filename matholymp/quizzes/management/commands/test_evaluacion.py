from django.core.management.base import BaseCommand
from django.utils import timezone
from quizzes.models import Evaluacion, Participantes
from datetime import timedelta

class Command(BaseCommand):
    help = 'Prueba el estado de las evaluaciones y participantes'

    def handle(self, *args, **options):
        self.stdout.write('=== PRUEBA DE EVALUACIONES ===')
        
        # Obtener tiempo actual
        now = timezone.localtime(timezone.now())
        self.stdout.write(f'Tiempo actual: {now}')
        
        # Obtener todas las evaluaciones
        evaluaciones = Evaluacion.objects.all()
        
        if not evaluaciones.exists():
            self.stdout.write(self.style.WARNING('No hay evaluaciones en la base de datos'))
            return
        
        for evaluacion in evaluaciones:
            self.stdout.write(f'\n--- Evaluación: {evaluacion.title} ---')
            self.stdout.write(f'Etapa: {evaluacion.get_etapa_display()}')
            self.stdout.write(f'Start time: {timezone.localtime(evaluacion.start_time)}')
            self.stdout.write(f'End time: {timezone.localtime(evaluacion.end_time)}')
            self.stdout.write(f'Duration: {evaluacion.duration_minutes} minutos')
            self.stdout.write(f'Is available: {evaluacion.is_available()}')
            self.stdout.write(f'Is finished: {evaluacion.is_finished()}')
            self.stdout.write(f'Is not started: {evaluacion.is_not_started()}')
            
            # Obtener participantes autorizados
            participantes = evaluacion.get_participantes_autorizados()
            self.stdout.write(f'Participantes autorizados: {len(participantes)}')
            
            for participante in participantes[:3]:  # Mostrar solo los primeros 3
                self.stdout.write(f'  - {participante.NombresCompletos} ({participante.cedula})')
                
                # Verificar si tiene resultado
                resultado = evaluacion.resultados.filter(participante=participante).first()
                if resultado:
                    self.stdout.write(f'    Resultado: Completada={resultado.completada}, Puntaje={resultado.puntaje}%')
                else:
                    self.stdout.write(f'    Resultado: No tiene intento previo')
        
        self.stdout.write('\n=== FIN DE PRUEBA ===')