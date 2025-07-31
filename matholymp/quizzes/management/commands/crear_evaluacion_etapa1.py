from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from quizzes.models import Evaluacion, Pregunta, Opcion, Participantes, ResultadoEvaluacion
from django.utils.crypto import get_random_string
import random
from datetime import timedelta
from decimal import Decimal

class Command(BaseCommand):
    help = 'Crea una evaluación de etapa 1 con 50 preguntas y 30 participantes de prueba'

    def handle(self, *args, **options):
        self.stdout.write('=== CREANDO EVALUACIÓN DE ETAPA 1 ===')
        
        # Crear evaluación de etapa 1
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        evaluacion = Evaluacion.objects.create(
            title='Evaluación Etapa 1 - Clasificatoria',
            etapa=1,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=60,
            preguntas_a_mostrar=20  # Mostrar 20 de las 50 preguntas
        )
        
        self.stdout.write(f'✓ Evaluación creada: {evaluacion.title}')
        
        # Crear 50 preguntas con opciones
        self.stdout.write('Creando 50 preguntas...')
        for i in range(1, 51):
            pregunta = Pregunta.objects.create(
                evaluacion=evaluacion,
                text=f'Pregunta {i}: ¿Cuál es el resultado de {random.randint(1, 100)} + {random.randint(1, 100)}?',
                puntos=1
            )
            
            # Crear 4 opciones, una correcta
            resultado_correcto = random.randint(1, 200)
            opciones_incorrectas = [
                resultado_correcto + random.randint(1, 10),
                resultado_correcto - random.randint(1, 10),
                random.randint(1, 200)
            ]
            
            # Opción correcta
            Opcion.objects.create(
                pregunta=pregunta,
                text=str(resultado_correcto),
                is_correct=True
            )
            
            # Opciones incorrectas
            for opcion_incorrecta in opciones_incorrectas:
                Opcion.objects.create(
                    pregunta=pregunta,
                    text=str(opcion_incorrecta),
                    is_correct=False
                )
        
        self.stdout.write(f'✓ 50 preguntas creadas')
        
        # Crear 30 participantes de prueba
        self.stdout.write('Creando 30 participantes de prueba...')
        participantes = []
        for i in range(1, 31):
            cedula = f'12345678{str(i).zfill(2)}'
            nombres = f'Participante {i}'
            email = f'participante{i}@test.com'
            
            # Crear usuario
            username = cedula
            password = get_random_string(length=6)
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=nombres,
                email=email
            )
            
            # Crear participante
            participante = Participantes.objects.create(
                user=user,
                cedula=cedula,
                NombresCompletos=nombres,
                email=email,
                password_temporal=password
            )
            
            participantes.append(participante)
            self.stdout.write(f'  ✓ Participante {i}: {nombres} ({cedula})')
        
        # Asignar participantes a la evaluación
        evaluacion.participantes_individuales.add(*participantes)
        self.stdout.write(f'✓ 30 participantes asignados a la evaluación')
        
        # Simular resultados con NUEVA lógica de puntuación
        self.stdout.write('Simulando resultados con nueva lógica de puntuación...')
        
        # Primeros 15 participantes: nota 10/10 (todas correctas)
        for i in range(15):
            participante = participantes[i]
            tiempo_utilizado = random.randint(20, 45)  # Entre 20 y 45 minutos
            
            # Nueva lógica: 20 preguntas correctas = 20 puntos, ponderado a 10
            puntos_obtenidos = 20  # 20 correctas * 1 punto = 20
            puntaje_ponderado = (puntos_obtenidos / 20) * 10  # Ponderar a escala de 10
            percentage = (puntaje_ponderado / 10) * 100  # 100%
            
            resultado = ResultadoEvaluacion.objects.create(
                evaluacion=evaluacion,
                participante=participante,
                puntaje=percentage,  # 100%
                puntos_obtenidos=Decimal(str(puntaje_ponderado)),  # 10.000
                puntos_totales=10,  # Siempre 10
                tiempo_utilizado=tiempo_utilizado,
                fecha_fin=timezone.now(),
                completada=True
            )
            
            self.stdout.write(f'  ✓ {participante.NombresCompletos}: {puntaje_ponderado:.3f}/10 ({percentage:.1f}%) - {tiempo_utilizado} min')
        
        # Últimos 15 participantes: nota menor a 10/10 (simular respuestas mixtas)
        for i in range(15, 30):
            participante = participantes[i]
            tiempo_utilizado = random.randint(30, 60)  # Entre 30 y 60 minutos
            
            # Simular respuestas mixtas: algunas correctas, algunas incorrectas, algunas sin responder
            # Ejemplo: 17 correctas, 2 incorrectas, 1 sin responder = 17 - (2*0.25) = 16.5 puntos
            # Ponderado: (16.5/20)*10 = 8.25/10
            
            # Generar puntaje aleatorio entre 6.0 y 9.5
            puntaje_ponderado = Decimal(str(random.uniform(6.0, 9.5)))
            percentage = float(puntaje_ponderado) * 10  # Convertir a porcentaje
            
            resultado = ResultadoEvaluacion.objects.create(
                evaluacion=evaluacion,
                participante=participante,
                puntaje=percentage,
                puntos_obtenidos=puntaje_ponderado,  # Puntaje ponderado sobre 10
                puntos_totales=10,  # Siempre 10
                tiempo_utilizado=tiempo_utilizado,
                fecha_fin=timezone.now(),
                completada=True
            )
            
            self.stdout.write(f'  ✓ {participante.NombresCompletos}: {puntaje_ponderado:.3f}/10 ({percentage:.1f}%) - {tiempo_utilizado} min')
        
        # Mostrar ranking de los 15 mejores
        self.stdout.write('\n=== RANKING DE LOS 15 MEJORES ===')
        mejores_resultados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado')[:15]
        
        for i, resultado in enumerate(mejores_resultados, 1):
            self.stdout.write(f'{i:2d}. {resultado.participante.NombresCompletos}: {resultado.get_puntaje_numerico()} ({resultado.puntaje:.1f}%) - {resultado.tiempo_utilizado} min')
        
        # Verificar que los 15 mejores son los que tienen 10/10
        participantes_10 = [r.participante for r in mejores_resultados if r.puntos_obtenidos == Decimal('10.000')]
        self.stdout.write(f'\n✓ Los {len(participantes_10)} participantes con 10.000/10 están en los 15 mejores')
        
        # Mostrar información de la evaluación
        self.stdout.write(f'\n=== INFORMACIÓN DE LA EVALUACIÓN ===')
        self.stdout.write(f'ID de la evaluación: {evaluacion.id}')
        self.stdout.write(f'Título: {evaluacion.title}')
        self.stdout.write(f'Etapa: {evaluacion.get_etapa_display()}')
        self.stdout.write(f'Preguntas totales: {evaluacion.preguntas.count()}')
        self.stdout.write(f'Preguntas a mostrar: {evaluacion.preguntas_a_mostrar}')
        self.stdout.write(f'Participantes asignados: {evaluacion.participantes_individuales.count()}')
        self.stdout.write(f'Resultados completados: {evaluacion.resultados.filter(completada=True).count()}')
        
        # Mostrar ejemplos de puntuación
        self.stdout.write(f'\n=== EJEMPLOS DE PUNTUACIÓN ===')
        self.stdout.write(f'Preguntas mostradas: 20')
        self.stdout.write(f'Puntuación máxima: 20 correctas = 20 puntos = 10.000/10')
        self.stdout.write(f'Puntuación ejemplo: 17 correctas, 2 incorrectas, 1 sin responder')
        self.stdout.write(f'  Cálculo: 17 - (2 × 0.25) = 16.5 puntos')
        self.stdout.write(f'  Ponderado: (16.5/20) × 10 = 8.250/10')
        
        self.stdout.write('\n=== EVALUACIÓN CREADA EXITOSAMENTE ===')
        self.stdout.write('Ahora puedes crear una evaluación de etapa 2 y verificar que los 15 mejores')
        self.stdout.write('participantes aparezcan automáticamente seleccionados.') 