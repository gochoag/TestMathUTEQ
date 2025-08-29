#!/usr/bin/env python
"""
Comando para verificar y corregir la consistencia de la preselección automática
Este comando:
1. Verifica que la preselección automática coincida con el ranking
2. Muestra diferencias si las hay
3. Opcionalmente corrige las diferencias encontradas
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max
from quizzes.models import Evaluacion, ResultadoEvaluacion, SystemConfig, Participantes
import sys

class Command(BaseCommand):
    help = 'Verifica y corrige la consistencia de la preselección automática con el ranking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--corregir',
            action='store_true',
            help='Corrige automáticamente las diferencias encontradas'
        )
        
        parser.add_argument(
            '--anio',
            type=int,
            help='Año específico a verificar (por defecto el año activo)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== VERIFICACIÓN DE PRESELECCIÓN AUTOMÁTICA ==='))
        
        # Determinar el año a verificar
        anio = options.get('anio') or SystemConfig.get_active_year()
        self.stdout.write(f'Verificando año: {anio}')
        
        # Obtener configuración del sistema
        num_etapas = SystemConfig.get_num_etapas()
        self.stdout.write(f'Configuración: {num_etapas} etapas')
        
        # Obtener evaluaciones del año
        evaluaciones = Evaluacion.objects.filter(anio=anio).order_by('etapa')
        
        problemas_encontrados = []
        
        for evaluacion in evaluaciones:
            self.stdout.write(f'\n--- Verificando {evaluacion.title} (Etapa {evaluacion.etapa}) ---')
            
            if evaluacion.etapa == 1:
                self.stdout.write('  Etapa 1: No requiere preselección automática')
                continue
            
            # Obtener participantes preseleccionados automáticamente
            if evaluacion.etapa == 2 and num_etapas == 3:
                participantes_esperados = evaluacion.get_participantes_etapa2()
                top_n = 15
            elif evaluacion.etapa == 3:
                participantes_esperados = evaluacion.get_participantes_etapa3()
                top_n = 5
            else:
                self.stdout.write('  No aplica para esta configuración')
                continue
            
            # Obtener participantes asignados manualmente
            participantes_asignados = list(evaluacion.participantes_individuales.all())
            
            self.stdout.write(f'  Participantes esperados (automáticos): {len(participantes_esperados)}')
            self.stdout.write(f'  Participantes asignados (manuales): {len(participantes_asignados)}')
            
            if not participantes_asignados:
                self.stdout.write('  ✓ No hay asignación manual, se usará preselección automática')
                # Mostrar los preseleccionados
                self.stdout.write(f'  Preseleccionados automáticamente:')
                for i, participante in enumerate(participantes_esperados, 1):
                    self.stdout.write(f'    {i:2d}. {participante.NombresCompletos} ({participante.cedula})')
            else:
                # Comparar asignación manual con preselección automática
                ids_esperados = set(p.id for p in participantes_esperados)
                ids_asignados = set(p.id for p in participantes_asignados)
                
                if ids_esperados == ids_asignados:
                    self.stdout.write('  ✓ La asignación manual coincide con la preselección automática')
                else:
                    self.stdout.write('  ⚠️  DIFERENCIA ENCONTRADA')
                    problemas_encontrados.append({
                        'evaluacion': evaluacion,
                        'esperados': participantes_esperados,
                        'asignados': participantes_asignados
                    })
                    
                    # Mostrar diferencias
                    solo_esperados = ids_esperados - ids_asignados
                    solo_asignados = ids_asignados - ids_esperados
                    
                    if solo_esperados:
                        self.stdout.write('    Participantes que deberían estar (según ranking):')
                        for p_id in solo_esperados:
                            p = next(p for p in participantes_esperados if p.id == p_id)
                            self.stdout.write(f'      - {p.NombresCompletos} ({p.cedula})')
                    
                    if solo_asignados:
                        self.stdout.write('    Participantes asignados manualmente (no en ranking):')
                        for p_id in solo_asignados:
                            p = next(p for p in participantes_asignados if p.id == p_id)
                            self.stdout.write(f'      - {p.NombresCompletos} ({p.cedula})')
        
        # Mostrar resumen
        self.stdout.write(f'\n=== RESUMEN ===')
        if problemas_encontrados:
            self.stdout.write(self.style.WARNING(f'Se encontraron {len(problemas_encontrados)} evaluaciones con diferencias'))
            
            if options.get('corregir'):
                self.stdout.write('\nCorrigiendo diferencias...')
                for problema in problemas_encontrados:
                    evaluacion = problema['evaluacion']
                    participantes_esperados = problema['esperados']
                    
                    # Limpiar asignación manual
                    evaluacion.participantes_individuales.clear()
                    
                    # Asignar participantes según preselección automática
                    evaluacion.participantes_individuales.add(*participantes_esperados)
                    
                    self.stdout.write(f'  ✓ Corregido: {evaluacion.title}')
                
                self.stdout.write(self.style.SUCCESS('Todas las diferencias han sido corregidas'))
            else:
                self.stdout.write('\nPara corregir automáticamente, ejecuta:')
                self.stdout.write(f'  python manage.py verificar_preseleccion --corregir --anio {anio}')
        else:
            self.stdout.write(self.style.SUCCESS('✓ Todas las evaluaciones tienen preselección consistente con el ranking'))
        
        self.stdout.write('\n=== VERIFICACIÓN COMPLETADA ===')

    def obtener_ranking_real(self, evaluacion):
        """
        Obtiene el ranking real de una evaluación usando la misma lógica que la vista
        """
        from django.db.models import Max
        
        # Obtener el mejor puntaje por participante
        mejores_puntajes = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            completada=True
        ).values('participante').annotate(
            mejor_puntaje=Max('puntos_obtenidos')
        )
        
        # Crear una lista de participantes con sus mejores puntajes
        participantes_con_mejor_puntaje = []
        for item in mejores_puntajes:
            participante_id = item['participante']
            mejor_puntaje = item['mejor_puntaje']
            
            # Obtener el resultado con el mejor puntaje (si hay empate, el más rápido)
            mejor_resultado = ResultadoEvaluacion.objects.filter(
                evaluacion=evaluacion,
                participante_id=participante_id,
                completada=True,
                puntos_obtenidos=mejor_puntaje
            ).order_by('tiempo_utilizado').first()
            
            if mejor_resultado:
                participantes_con_mejor_puntaje.append(mejor_resultado)
        
        # Ordenar por puntaje descendente y tiempo ascendente
        resultados_ordenados = sorted(
            participantes_con_mejor_puntaje, 
            key=lambda x: (-x.puntos_obtenidos, x.tiempo_utilizado)
        )
        
        return resultados_ordenados
