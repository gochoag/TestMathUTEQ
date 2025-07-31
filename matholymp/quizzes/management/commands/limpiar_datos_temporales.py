from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quizzes.models import Evaluacion, Pregunta, Opcion, Participantes, ResultadoEvaluacion
from django.db import transaction

class Command(BaseCommand):
    help = 'Elimina los datos temporales creados por el script crear_evaluacion_etapa1.py'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmar la eliminación sin preguntar',
        )
        parser.add_argument(
            '--evaluacion-id',
            type=int,
            help='ID específico de la evaluación a eliminar (opcional)',
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        evaluacion_id = options['evaluacion_id']
        
        self.stdout.write('=== LIMPIEZA DE DATOS TEMPORALES ===')
        
        # Buscar evaluaciones de prueba
        if evaluacion_id:
            evaluaciones = Evaluacion.objects.filter(id=evaluacion_id, title__icontains='Evaluación Etapa 1 - Clasificatoria')
        else:
            evaluaciones = Evaluacion.objects.filter(title__icontains='Evaluación Etapa 1 - Clasificatoria')
        
        if not evaluaciones.exists():
            self.stdout.write(self.style.WARNING('No se encontraron evaluaciones de prueba para eliminar.'))
            return
        
        self.stdout.write(f'Se encontraron {evaluaciones.count()} evaluación(es) de prueba:')
        for eval in evaluaciones:
            self.stdout.write(f'  - ID: {eval.id}, Título: {eval.title}')
        
        # Buscar participantes de prueba (con cédulas que empiecen con 12345678)
        participantes_prueba = Participantes.objects.filter(cedula__startswith='12345678')
        self.stdout.write(f'Se encontraron {participantes_prueba.count()} participante(s) de prueba')
        
        # Buscar usuarios de prueba
        usuarios_prueba = User.objects.filter(username__startswith='12345678')
        self.stdout.write(f'Se encontraron {usuarios_prueba.count()} usuario(s) de prueba')
        
        # Mostrar resumen de lo que se eliminará
        total_preguntas = sum(eval.preguntas.count() for eval in evaluaciones)
        total_opciones = sum(eval.preguntas.count() * 4 for eval in evaluaciones)  # 4 opciones por pregunta
        total_resultados = sum(eval.resultados.count() for eval in evaluaciones)
        
        self.stdout.write('\n=== RESUMEN DE ELIMINACIÓN ===')
        self.stdout.write(f'Evaluaciones: {evaluaciones.count()}')
        self.stdout.write(f'Preguntas: {total_preguntas}')
        self.stdout.write(f'Opciones: {total_opciones}')
        self.stdout.write(f'Participantes: {participantes_prueba.count()}')
        self.stdout.write(f'Usuarios: {usuarios_prueba.count()}')
        self.stdout.write(f'Resultados: {total_resultados}')
        
        # Confirmar eliminación
        if not confirm:
            respuesta = input('\n¿Estás seguro de que quieres eliminar estos datos? (s/N): ')
            if respuesta.lower() != 's':
                self.stdout.write(self.style.WARNING('Operación cancelada.'))
                return
        
        # Eliminar datos en una transacción
        with transaction.atomic():
            self.stdout.write('\n=== ELIMINANDO DATOS ===')
            
            # 1. Eliminar resultados de evaluaciones
            resultados_eliminados = 0
            for evaluacion in evaluaciones:
                resultados = evaluacion.resultados.all()
                resultados_eliminados += resultados.count()
                resultados.delete()
                self.stdout.write(f'  ✓ Eliminados {resultados.count()} resultados de evaluación {evaluacion.id}')
            
            # 2. Eliminar opciones y preguntas
            opciones_eliminadas = 0
            preguntas_eliminadas = 0
            for evaluacion in evaluaciones:
                preguntas = evaluacion.preguntas.all()
                for pregunta in preguntas:
                    opciones = pregunta.opciones.all()
                    opciones_eliminadas += opciones.count()
                    opciones.delete()
                preguntas_eliminadas += preguntas.count()
                preguntas.delete()
                self.stdout.write(f'  ✓ Eliminadas {evaluacion.preguntas.count()} preguntas y sus opciones de evaluación {evaluacion.id}')
            
            # 3. Eliminar evaluaciones
            evaluaciones_eliminadas = evaluaciones.count()
            evaluaciones.delete()
            self.stdout.write(f'  ✓ Eliminadas {evaluaciones_eliminadas} evaluaciones')
            
            # 4. Eliminar participantes de prueba
            participantes_eliminados = participantes_prueba.count()
            participantes_prueba.delete()
            self.stdout.write(f'  ✓ Eliminados {participantes_eliminados} participantes de prueba')
            
            # 5. Eliminar usuarios de prueba
            usuarios_eliminados = usuarios_prueba.count()
            usuarios_prueba.delete()
            self.stdout.write(f'  ✓ Eliminados {usuarios_eliminados} usuarios de prueba')
        
        self.stdout.write('\n=== LIMPIEZA COMPLETADA ===')
        self.stdout.write(self.style.SUCCESS('✓ Todos los datos temporales han sido eliminados exitosamente.'))
        self.stdout.write(f'  - {evaluaciones_eliminadas} evaluaciones eliminadas')
        self.stdout.write(f'  - {preguntas_eliminadas} preguntas eliminadas')
        self.stdout.write(f'  - {opciones_eliminadas} opciones eliminadas')
        self.stdout.write(f'  - {participantes_eliminados} participantes eliminados')
        self.stdout.write(f'  - {usuarios_eliminados} usuarios eliminados')
        self.stdout.write(f'  - {resultados_eliminados} resultados eliminados') 