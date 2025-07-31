from django.core.management.base import BaseCommand
from quizzes.models import Evaluacion, ResultadoEvaluacion
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Verifica que la selección automática de los 15 mejores participantes funciona correctamente'

    def handle(self, *args, **options):
        self.stdout.write('=== VERIFICANDO SELECCIÓN AUTOMÁTICA ===')
        
        # Buscar evaluación de etapa 1
        evaluacion_etapa1 = Evaluacion.objects.filter(etapa=1).first()
        if not evaluacion_etapa1:
            self.stdout.write(self.style.ERROR('❌ No se encontró evaluación de etapa 1'))
            return
        
        self.stdout.write(f'✓ Evaluación etapa 1 encontrada: {evaluacion_etapa1.title}')
        
        # Verificar que hay resultados completados
        resultados_completados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa1,
            completada=True
        ).count()
        
        self.stdout.write(f'✓ Resultados completados: {resultados_completados}')
        
        if resultados_completados == 0:
            self.stdout.write(self.style.ERROR('❌ No hay resultados completados en la etapa 1'))
            return
        
        # Obtener los 15 mejores resultados
        mejores_resultados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa1,
            completada=True
        ).order_by('-puntaje', 'tiempo_utilizado')[:15]
        
        self.stdout.write(f'\n=== RANKING DE LOS 15 MEJORES ===')
        for i, resultado in enumerate(mejores_resultados, 1):
            self.stdout.write(f'{i:2d}. {resultado.participante.NombresCompletos}: {resultado.puntaje}% ({resultado.tiempo_utilizado} min)')
        
        # Verificar que los 15 mejores son los que tienen 100%
        participantes_100 = [r.participante for r in mejores_resultados if r.puntaje == 100]
        self.stdout.write(f'\n✓ Los {len(participantes_100)} participantes con 100% están en los 15 mejores')
        
        # Crear una evaluación de etapa 2 para probar la selección automática
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        evaluacion_etapa2 = Evaluacion.objects.create(
            title='Evaluación Etapa 2 - Semifinal (Prueba)',
            etapa=2,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=60,
            preguntas_a_mostrar=15
        )
        
        self.stdout.write(f'\n✓ Evaluación etapa 2 creada: {evaluacion_etapa2.title}')
        
        # Obtener participantes automáticos de la etapa 2
        participantes_automaticos = evaluacion_etapa2.get_participantes_etapa2()
        
        self.stdout.write(f'\n=== PARTICIPANTES AUTOMÁTICOS ETAPA 2 ===')
        self.stdout.write(f'Participantes automáticos encontrados: {len(participantes_automaticos)}')
        
        for i, participante in enumerate(participantes_automaticos, 1):
            # Buscar el resultado de este participante en la etapa 1
            resultado = ResultadoEvaluacion.objects.filter(
                evaluacion=evaluacion_etapa1,
                participante=participante,
                completada=True
            ).first()
            
            if resultado:
                self.stdout.write(f'{i:2d}. {participante.NombresCompletos}: {resultado.puntaje}% ({resultado.tiempo_utilizado} min)')
            else:
                self.stdout.write(f'{i:2d}. {participante.NombresCompletos}: Sin resultado')
        
        # Verificar que los participantes automáticos coinciden con los 15 mejores
        participantes_automaticos_ids = set(p.id for p in participantes_automaticos)
        mejores_15_ids = set(r.participante.id for r in mejores_resultados)
        
        if participantes_automaticos_ids == mejores_15_ids:
            self.stdout.write(self.style.SUCCESS('\n✅ VERIFICACIÓN EXITOSA'))
            self.stdout.write('Los participantes automáticos de la etapa 2 coinciden exactamente con los 15 mejores de la etapa 1')
        else:
            self.stdout.write(self.style.ERROR('\n❌ ERROR EN LA VERIFICACIÓN'))
            self.stdout.write('Los participantes automáticos NO coinciden con los 15 mejores')
            
            # Mostrar diferencias
            solo_automaticos = participantes_automaticos_ids - mejores_15_ids
            solo_mejores = mejores_15_ids - participantes_automaticos_ids
            
            if solo_automaticos:
                self.stdout.write(f'Participantes solo en automáticos: {solo_automaticos}')
            if solo_mejores:
                self.stdout.write(f'Participantes solo en mejores 15: {solo_mejores}')
        
        # Verificar que la evaluación de etapa 2 no tiene participantes asignados en BD
        participantes_asignados_bd = evaluacion_etapa2.participantes_individuales.count()
        self.stdout.write(f'\nParticipantes asignados en BD para etapa 2: {participantes_asignados_bd}')
        
        if participantes_asignados_bd == 0:
            self.stdout.write('✓ La evaluación de etapa 2 no tiene participantes asignados en BD (correcto)')
        else:
            self.stdout.write('⚠ La evaluación de etapa 2 tiene participantes asignados en BD')
        
        # Limpiar evaluación de prueba
        evaluacion_etapa2.delete()
        self.stdout.write('\n✓ Evaluación de prueba eliminada')
        
        self.stdout.write('\n=== RESUMEN ===')
        self.stdout.write(f'• Evaluación etapa 1: {evaluacion_etapa1.title}')
        self.stdout.write(f'• Resultados completados: {resultados_completados}')
        self.stdout.write(f'• Participantes con 100%: {len(participantes_100)}')
        self.stdout.write(f'• Participantes automáticos etapa 2: {len(participantes_automaticos)}')
        
        if participantes_automaticos_ids == mejores_15_ids:
            self.stdout.write(self.style.SUCCESS('✅ La selección automática funciona correctamente'))
        else:
            self.stdout.write(self.style.ERROR('❌ Hay un problema en la selección automática')) 