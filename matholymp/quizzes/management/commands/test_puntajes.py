from django.core.management.base import BaseCommand
from quizzes.models import ResultadoEvaluacion, Evaluacion, Participantes

class Command(BaseCommand):
    help = 'Prueba el sistema de puntajes numéricos'

    def handle(self, *args, **options):
        self.stdout.write('=== PRUEBA DE PUNTAJES NUMÉRICOS ===')
        
        # Obtener todos los resultados
        resultados = ResultadoEvaluacion.objects.filter(completada=True)
        
        if not resultados.exists():
            self.stdout.write(self.style.WARNING('No hay resultados para probar'))
            return
        
        for resultado in resultados:
            self.stdout.write(f'\n--- Resultado: {resultado.participante.NombresCompletos} ---')
            self.stdout.write(f'Evaluación: {resultado.evaluacion.title}')
            self.stdout.write(f'Puntaje porcentual: {resultado.puntaje}%')
            self.stdout.write(f'Puntos obtenidos: {resultado.puntos_obtenidos}')
            self.stdout.write(f'Puntos totales: {resultado.puntos_totales}')
            self.stdout.write(f'Puntaje numérico: {resultado.get_puntaje_numerico()}')
            self.stdout.write(f'Porcentaje calculado: {resultado.get_puntaje_porcentaje():.1f}%')
            self.stdout.write(f'Tiempo formateado: {resultado.get_tiempo_formateado()}')
            self.stdout.write(f'Fecha inicio: {resultado.fecha_inicio}')
            self.stdout.write(f'Fecha fin: {resultado.fecha_fin}')
        
        self.stdout.write('\n=== FIN DE PRUEBA ===')