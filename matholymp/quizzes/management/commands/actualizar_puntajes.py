from django.core.management.base import BaseCommand
from quizzes.models import ResultadoEvaluacion

class Command(BaseCommand):
    help = 'Actualiza los puntajes existentes con los nuevos campos de puntos'

    def handle(self, *args, **options):
        self.stdout.write('=== ACTUALIZANDO PUNTAJES ===')
        
        # Obtener todos los resultados
        resultados = ResultadoEvaluacion.objects.filter(completada=True)
        
        if not resultados.exists():
            self.stdout.write(self.style.WARNING('No hay resultados para actualizar'))
            return
        
        actualizados = 0
        
        for resultado in resultados:
            # Calcular puntos basados en el puntaje porcentual
            if resultado.puntaje > 0:
                # Obtener preguntas de la evaluación
                preguntas = resultado.evaluacion.get_preguntas_para_estudiante(resultado.participante.id)
                
                if preguntas:
                    # Calcular puntos totales de las preguntas mostradas
                    puntos_totales = sum(pregunta.puntos for pregunta in preguntas)
                    
                    # Calcular puntos obtenidos basados en el porcentaje
                    puntos_obtenidos = int((resultado.puntaje / 100) * puntos_totales)
                    
                    # Actualizar el resultado
                    resultado.puntos_obtenidos = puntos_obtenidos
                    resultado.puntos_totales = puntos_totales
                    resultado.save()
                    
                    actualizados += 1
                    self.stdout.write(f'Actualizado: {resultado.participante.NombresCompletos} - {resultado.get_puntaje_numerico()}')
        
        self.stdout.write(self.style.SUCCESS(f'Se actualizaron {actualizados} resultados'))
        self.stdout.write('=== FIN DE ACTUALIZACIÓN ===')