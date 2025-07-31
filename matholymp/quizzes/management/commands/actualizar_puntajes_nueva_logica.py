from django.core.management.base import BaseCommand
from quizzes.models import ResultadoEvaluacion
from decimal import Decimal

class Command(BaseCommand):
    help = 'Actualiza los puntajes existentes con la nueva lógica de ponderación (escala de 10 puntos)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmar la actualización sin preguntar',
        )
        parser.add_argument(
            '--evaluacion-id',
            type=int,
            help='ID específico de la evaluación a actualizar (opcional)',
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        evaluacion_id = options['evaluacion_id']
        
        self.stdout.write('=== ACTUALIZANDO PUNTAJES CON NUEVA LÓGICA ===')
        
        # Obtener resultados a actualizar
        if evaluacion_id:
            resultados = ResultadoEvaluacion.objects.filter(
                evaluacion_id=evaluacion_id,
                completada=True
            )
        else:
            resultados = ResultadoEvaluacion.objects.filter(completada=True)
        
        if not resultados.exists():
            self.stdout.write(self.style.WARNING('No hay resultados para actualizar'))
            return
        
        self.stdout.write(f'Se encontraron {resultados.count()} resultados para actualizar')
        
        # Mostrar ejemplos de lo que se va a actualizar
        self.stdout.write('\n=== EJEMPLOS DE ACTUALIZACIÓN ===')
        self.stdout.write('Formato anterior: X/Y (ej: 20/20)')
        self.stdout.write('Formato nuevo: X.XXX/10 (ej: 10.000/10)')
        self.stdout.write('Lógica: puntaje ponderado sobre 10 puntos')
        
        # Confirmar actualización
        if not confirm:
            respuesta = input('\n¿Estás seguro de que quieres actualizar estos puntajes? (s/N): ')
            if respuesta.lower() != 's':
                self.stdout.write(self.style.WARNING('Operación cancelada.'))
                return
        
        actualizados = 0
        
        for resultado in resultados:
            # Obtener preguntas de la evaluación
            preguntas = resultado.evaluacion.get_preguntas_para_estudiante(resultado.participante.id)
            
            if preguntas:
                total_questions = len(preguntas)
                
                # Si el resultado ya tiene el formato nuevo (puntos_totales = 10), saltarlo
                if resultado.puntos_totales == 10:
                    self.stdout.write(f'  ⏭️  Saltado: {resultado.participante.NombresCompletos} - Ya tiene formato nuevo')
                    continue
                
                # Calcular puntaje con nueva lógica basado en el puntaje porcentual existente
                # Asumimos que el puntaje porcentual es correcto y lo convertimos a la nueva escala
                puntaje_ponderado = (resultado.puntaje / 100) * 10
                
                # Actualizar el resultado
                resultado.puntos_obtenidos = Decimal(str(puntaje_ponderado))
                resultado.puntos_totales = 10
                resultado.save()
                
                actualizados += 1
                self.stdout.write(f'  ✓ Actualizado: {resultado.participante.NombresCompletos} - {resultado.get_puntaje_numerico()}')
            else:
                self.stdout.write(f'  ⚠️  Sin preguntas: {resultado.participante.NombresCompletos}')
        
        self.stdout.write('\n=== ACTUALIZACIÓN COMPLETADA ===')
        self.stdout.write(self.style.SUCCESS(f'Se actualizaron {actualizados} resultados'))
        self.stdout.write('Los puntajes ahora se muestran en formato X.XXX/10')
        
        # Mostrar algunos ejemplos de los resultados actualizados
        if actualizados > 0:
            self.stdout.write('\n=== EJEMPLOS DE RESULTADOS ACTUALIZADOS ===')
            ejemplos = resultados.filter(puntos_totales=10)[:5]
            for resultado in ejemplos:
                self.stdout.write(f'  {resultado.participante.NombresCompletos}: {resultado.get_puntaje_numerico()} ({resultado.puntaje:.1f}%)') 