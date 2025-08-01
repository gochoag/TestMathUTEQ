from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from quizzes.models import Evaluacion, Pregunta, Opcion, Participantes, ResultadoEvaluacion
from django.utils.crypto import get_random_string
import random
from datetime import timedelta
from decimal import Decimal

class Command(BaseCommand):
    help = 'Crea evaluaciones de etapa 1, 2 y 3 con participantes y resultados simulados'

    def handle(self, *args, **options):
        self.stdout.write('=== CREANDO EVALUACIONES DE ETAPA 1, 2 Y 3 ===')
        
        # ===== ETAPA 1 =====
        self.stdout.write('\n=== CREANDO EVALUACIÓN DE ETAPA 1 ===')
        
        # Crear evaluación de etapa 1
        start_time_etapa1 = timezone.now() + timedelta(hours=1)
        end_time_etapa1 = start_time_etapa1 + timedelta(hours=2)
        
        evaluacion_etapa1 = Evaluacion.objects.create(
            title='Evaluación Etapa 1 - Clasificatoria',
            etapa=1,
            start_time=start_time_etapa1,
            end_time=end_time_etapa1,
            duration_minutes=60,
            preguntas_a_mostrar=20  # Mostrar 20 de las 50 preguntas
        )
        
        self.stdout.write(f'✓ Evaluación creada: {evaluacion_etapa1.title}')
        
        # Crear 50 preguntas con opciones para etapa 1
        self.stdout.write('Creando 50 preguntas para etapa 1...')
        for i in range(1, 51):
            pregunta = Pregunta.objects.create(
                evaluacion=evaluacion_etapa1,
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
        
        self.stdout.write(f'✓ 50 preguntas creadas para etapa 1')
        
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
        
        # Asignar participantes a la evaluación de etapa 1
        evaluacion_etapa1.participantes_individuales.add(*participantes)
        self.stdout.write(f'✓ 30 participantes asignados a la evaluación de etapa 1')
        
        # Simular resultados de etapa 1
        self.stdout.write('Simulando resultados de etapa 1...')
        
        # Primeros 15 participantes: nota 10/10 (todas correctas)
        for i in range(15):
            participante = participantes[i]
            tiempo_utilizado = random.randint(20, 45)  # Entre 20 y 45 minutos
            
            # Nueva lógica: 20 preguntas correctas = 20 puntos, ponderado a 10
            puntos_obtenidos = 20  # 20 correctas * 1 punto = 20
            puntaje_ponderado = (puntos_obtenidos / 20) * 10  # Ponderar a escala de 10
            percentage = (puntaje_ponderado / 10) * 100  # 100%
            
            resultado = ResultadoEvaluacion.objects.create(
                evaluacion=evaluacion_etapa1,
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
            
            # Generar puntaje aleatorio entre 6.0 y 9.5
            puntaje_ponderado = Decimal(str(random.uniform(6.0, 9.5)))
            percentage = float(puntaje_ponderado) * 10  # Convertir a porcentaje
            
            resultado = ResultadoEvaluacion.objects.create(
                evaluacion=evaluacion_etapa1,
                participante=participante,
                puntaje=percentage,
                puntos_obtenidos=puntaje_ponderado,  # Puntaje ponderado sobre 10
                puntos_totales=10,  # Siempre 10
                tiempo_utilizado=tiempo_utilizado,
                fecha_fin=timezone.now(),
                completada=True
            )
            
            self.stdout.write(f'  ✓ {participante.NombresCompletos}: {puntaje_ponderado:.3f}/10 ({percentage:.1f}%) - {tiempo_utilizado} min')
        
        # Obtener los 15 mejores de etapa 1
        mejores_etapa1 = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa1,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado')[:15]
        
        participantes_etapa2 = [r.participante for r in mejores_etapa1]
        
        # ===== ETAPA 2 =====
        self.stdout.write('\n=== CREANDO EVALUACIÓN DE ETAPA 2 ===')
        
        # Crear evaluación de etapa 2
        start_time_etapa2 = timezone.now() + timedelta(hours=4)
        end_time_etapa2 = start_time_etapa2 + timedelta(hours=2)
        
        evaluacion_etapa2 = Evaluacion.objects.create(
            title='Evaluación Etapa 2 - Semifinal',
            etapa=2,
            start_time=start_time_etapa2,
            end_time=end_time_etapa2,
            duration_minutes=60,
            preguntas_a_mostrar=10  # Mostrar 10 de las 50 preguntas
        )
        
        self.stdout.write(f'✓ Evaluación creada: {evaluacion_etapa2.title}')
        
        # Crear 50 preguntas con opciones para etapa 2
        self.stdout.write('Creando 50 preguntas para etapa 2...')
        for i in range(1, 51):
            pregunta = Pregunta.objects.create(
                evaluacion=evaluacion_etapa2,
                text=f'Pregunta Etapa 2 - {i}: ¿Cuál es el resultado de {random.randint(10, 500)} × {random.randint(2, 20)}?',
                puntos=1
            )
            
            # Crear 4 opciones, una correcta
            resultado_correcto = random.randint(20, 10000)
            opciones_incorrectas = [
                resultado_correcto + random.randint(10, 100),
                resultado_correcto - random.randint(10, 100),
                random.randint(20, 10000)
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
        
        self.stdout.write(f'✓ 50 preguntas creadas para etapa 2')
        
        # Asignar los 15 mejores de etapa 1 a etapa 2
        evaluacion_etapa2.participantes_individuales.add(*participantes_etapa2)
        self.stdout.write(f'✓ 15 participantes de etapa 1 asignados a etapa 2')
        
        # Simular resultados de etapa 2
        self.stdout.write('Simulando resultados de etapa 2...')
        
        # Primeros 5 participantes: nota 10/10
        for i in range(5):
            participante = participantes_etapa2[i]
            tiempo_utilizado = random.randint(15, 35)  # Entre 15 y 35 minutos
            
            # 10 preguntas correctas = 10 puntos, ponderado a 10
            puntos_obtenidos = 10  # 10 correctas * 1 punto = 10
            puntaje_ponderado = (puntos_obtenidos / 10) * 10  # Ponderar a escala de 10
            percentage = (puntaje_ponderado / 10) * 100  # 100%
            
            resultado = ResultadoEvaluacion.objects.create(
                evaluacion=evaluacion_etapa2,
                participante=participante,
                puntaje=percentage,  # 100%
                puntos_obtenidos=Decimal(str(puntaje_ponderado)),  # 10.000
                puntos_totales=10,  # Siempre 10
                tiempo_utilizado=tiempo_utilizado,
                fecha_fin=timezone.now(),
                completada=True
            )
            
            self.stdout.write(f'  ✓ {participante.NombresCompletos}: {puntaje_ponderado:.3f}/10 ({percentage:.1f}%) - {tiempo_utilizado} min')
        
        # Últimos 10 participantes: nota menor a 9/10
        for i in range(5, 15):
            participante = participantes_etapa2[i]
            tiempo_utilizado = random.randint(25, 55)  # Entre 25 y 55 minutos
            
            # Generar puntaje aleatorio entre 5.0 y 8.9
            puntaje_ponderado = Decimal(str(random.uniform(5.0, 8.9)))
            percentage = float(puntaje_ponderado) * 10  # Convertir a porcentaje
            
            resultado = ResultadoEvaluacion.objects.create(
                evaluacion=evaluacion_etapa2,
                participante=participante,
                puntaje=percentage,
                puntos_obtenidos=puntaje_ponderado,  # Puntaje ponderado sobre 10
                puntos_totales=10,  # Siempre 10
                tiempo_utilizado=tiempo_utilizado,
                fecha_fin=timezone.now(),
                completada=True
            )
            
            self.stdout.write(f'  ✓ {participante.NombresCompletos}: {puntaje_ponderado:.3f}/10 ({percentage:.1f}%) - {tiempo_utilizado} min')
        
        # Obtener los 5 mejores de etapa 2
        mejores_etapa2 = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa2,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado')[:5]
        
        participantes_etapa3 = [r.participante for r in mejores_etapa2]
        
        # ===== ETAPA 3 =====
        self.stdout.write('\n=== CREANDO EVALUACIÓN DE ETAPA 3 ===')
        
        # Crear evaluación de etapa 3
        start_time_etapa3 = timezone.now() + timedelta(hours=7)
        end_time_etapa3 = start_time_etapa3 + timedelta(hours=2)
        
        evaluacion_etapa3 = Evaluacion.objects.create(
            title='Evaluación Etapa 3 - Final',
            etapa=3,
            start_time=start_time_etapa3,
            end_time=end_time_etapa3,
            duration_minutes=60,
            preguntas_a_mostrar=10  # Mostrar 10 de las 50 preguntas
        )
        
        self.stdout.write(f'✓ Evaluación creada: {evaluacion_etapa3.title}')
        
        # Crear 50 preguntas con opciones para etapa 3
        self.stdout.write('Creando 50 preguntas para etapa 3...')
        for i in range(1, 51):
            pregunta = Pregunta.objects.create(
                evaluacion=evaluacion_etapa3,
                text=f'Pregunta Etapa 3 - {i}: ¿Cuál es el resultado de {random.randint(50, 1000)} ÷ {random.randint(2, 10)}?',
                puntos=1
            )
            
            # Crear 4 opciones, una correcta
            resultado_correcto = random.randint(5, 500)
            opciones_incorrectas = [
                resultado_correcto + random.randint(5, 50),
                resultado_correcto - random.randint(5, 50),
                random.randint(5, 500)
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
        
        self.stdout.write(f'✓ 50 preguntas creadas para etapa 3')
        
        # Asignar los 5 mejores de etapa 2 a etapa 3
        evaluacion_etapa3.participantes_individuales.add(*participantes_etapa3)
        self.stdout.write(f'✓ 5 participantes de etapa 2 asignados a etapa 3')
        
        # Simular resultados de etapa 3 con criterios específicos
        self.stdout.write('Simulando resultados de etapa 3...')
        
        # 1 participante: nota 10/10 (ORO)
        participante_oro = participantes_etapa3[0]
        tiempo_utilizado = random.randint(12, 30)  # Entre 12 y 30 minutos
        
        puntaje_ponderado = Decimal('10.000')
        percentage = 100.0
        
        resultado = ResultadoEvaluacion.objects.create(
            evaluacion=evaluacion_etapa3,
            participante=participante_oro,
            puntaje=percentage,
            puntos_obtenidos=puntaje_ponderado,
            puntos_totales=10,
            tiempo_utilizado=tiempo_utilizado,
            fecha_fin=timezone.now(),
            completada=True
        )
        
        self.stdout.write(f'  ✓ {participante_oro.NombresCompletos}: {puntaje_ponderado:.3f}/10 ({percentage:.1f}%) - {tiempo_utilizado} min [ORO]')
        
        # 2 participantes: notas 9/10 y 8/10 (PLATA)
        for i in range(1, 3):
            participante = participantes_etapa3[i]
            tiempo_utilizado = random.randint(18, 40)  # Entre 18 y 40 minutos
            
            puntaje_ponderado = Decimal(str(10 - i))  # 9.000 y 8.000
            percentage = float(puntaje_ponderado) * 10
            
            resultado = ResultadoEvaluacion.objects.create(
                evaluacion=evaluacion_etapa3,
                participante=participante,
                puntaje=percentage,
                puntos_obtenidos=puntaje_ponderado,
                puntos_totales=10,
                tiempo_utilizado=tiempo_utilizado,
                fecha_fin=timezone.now(),
                completada=True
            )
            
            self.stdout.write(f'  ✓ {participante.NombresCompletos}: {puntaje_ponderado:.3f}/10 ({percentage:.1f}%) - {tiempo_utilizado} min [PLATA]')
        
        # 2 participantes: notas 7/10 y 6/10 (BRONCE)
        for i in range(3, 5):
            participante = participantes_etapa3[i]
            tiempo_utilizado = random.randint(25, 50)  # Entre 25 y 50 minutos
            
            puntaje_ponderado = Decimal(str(10 - i))  # 7.000 y 6.000
            percentage = float(puntaje_ponderado) * 10
            
            resultado = ResultadoEvaluacion.objects.create(
                evaluacion=evaluacion_etapa3,
                participante=participante,
                puntaje=percentage,
                puntos_obtenidos=puntaje_ponderado,
                puntos_totales=10,
                tiempo_utilizado=tiempo_utilizado,
                fecha_fin=timezone.now(),
                completada=True
            )
            
            self.stdout.write(f'  ✓ {participante.NombresCompletos}: {puntaje_ponderado:.3f}/10 ({percentage:.1f}%) - {tiempo_utilizado} min [BRONCE]')
        
        # ===== RESUMEN FINAL =====
        self.stdout.write('\n=== RESUMEN DE EVALUACIONES CREADAS ===')
        
        # Etapa 1
        self.stdout.write(f'\n📊 ETAPA 1 - Clasificatoria:')
        self.stdout.write(f'   ID: {evaluacion_etapa1.id}')
        self.stdout.write(f'   Participantes: 30')
        self.stdout.write(f'   Preguntas: 50 (mostrar 20)')
        self.stdout.write(f'   Clasificados: 15 (10/10)')
        
        # Etapa 2
        self.stdout.write(f'\n📊 ETAPA 2 - Semifinal:')
        self.stdout.write(f'   ID: {evaluacion_etapa2.id}')
        self.stdout.write(f'   Participantes: 15 (de etapa 1)')
        self.stdout.write(f'   Preguntas: 50 (mostrar 10)')
        self.stdout.write(f'   Finalistas: 5 (10/10)')
        
        # Etapa 3
        self.stdout.write(f'\n📊 ETAPA 3 - Final:')
        self.stdout.write(f'   ID: {evaluacion_etapa3.id}')
        self.stdout.write(f'   Participantes: 5 (de etapa 2)')
        self.stdout.write(f'   Preguntas: 50 (mostrar 10)')
        self.stdout.write(f'   Medallas: 1 ORO (10/10), 2 PLATA (9/10, 8/10), 2 BRONCE (7/10, 6/10)')
        
        # Mostrar ranking final de etapa 3
        self.stdout.write(f'\n=== RANKING FINAL ETAPA 3 ===')
        ranking_final = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa3,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado')
        
        for i, resultado in enumerate(ranking_final, 1):
            if i == 1:
                medalla = "🥇 ORO"
            elif i in [2, 3]:
                medalla = "🥈 PLATA"
            elif i in [4, 5]:
                medalla = "🥉 BRONCE"
            else:
                medalla = "🏅"
            
            self.stdout.write(f'{i}. {resultado.participante.NombresCompletos}: {resultado.get_puntaje_numerico()} ({resultado.puntaje:.1f}%) - {resultado.tiempo_utilizado} min {medalla}')
        
        self.stdout.write('\n=== EVALUACIONES CREADAS EXITOSAMENTE ===')
        self.stdout.write('✅ Etapa 1: 30 participantes → 15 clasificados')
        self.stdout.write('✅ Etapa 2: 15 participantes → 5 finalistas')
        self.stdout.write('✅ Etapa 3: 5 participantes → 1 ORO, 2 PLATA, 2 BRONCE')
        self.stdout.write('\nAhora puedes verificar los procedimientos de preselección automática.') 