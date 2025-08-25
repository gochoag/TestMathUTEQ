from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from quizzes.models import Evaluacion, Pregunta, Opcion, Participantes, ResultadoEvaluacion, Representante, GrupoParticipantes
from django.utils.crypto import get_random_string
import random
from datetime import timedelta
from decimal import Decimal

class Command(BaseCommand):
    help = 'Crea evaluaciones de etapa 1, 2 y 3 con grupos, representantes y participantes individuales'

    def handle(self, *args, **options):
        self.stdout.write('=== CREANDO EVALUACIONES DE ETAPA 1, 2 Y 3 ===')
        
        # Verificar y limpiar datos existentes
        self.stdout.write('\n=== VERIFICANDO Y LIMPIANDO DATOS EXISTENTES ===')
        
        # Eliminar evaluaciones de prueba anteriores si existen
        evaluaciones_existentes = Evaluacion.objects.filter(
            title__in=[
                'Evaluación Etapa 1 - Clasificatoria',
                'Evaluación Etapa 2 - Semifinal', 
                'Evaluación Etapa 3 - Final'
            ]
        )
        
        if evaluaciones_existentes.exists():
            self.stdout.write(f'Eliminando {evaluaciones_existentes.count()} evaluaciones de prueba anteriores...')
            evaluaciones_existentes.delete()
        
        # Eliminar participantes de prueba anteriores
        participantes_prueba = Participantes.objects.filter(
            cedula__startswith='123456'
        )
        if participantes_prueba.exists():
            self.stdout.write(f'Eliminando {participantes_prueba.count()} participantes de prueba anteriores...')
            # Eliminar usuarios asociados
            users_prueba = User.objects.filter(username__startswith='123456')
            users_prueba.delete()
            participantes_prueba.delete()
        
        # Eliminar representantes de prueba anteriores
        representantes_prueba = Representante.objects.filter(
            NombreColegio__in=['Colegio San Francisco', 'Instituto Tecnológico']
        )
        if representantes_prueba.exists():
            self.stdout.write(f'Eliminando {representantes_prueba.count()} representantes de prueba anteriores...')
            representantes_prueba.delete()
        
        self.stdout.write('✅ Datos anteriores limpiados correctamente')
        
        # ===== CREAR REPRESENTANTES =====
        self.stdout.write('\n=== CREANDO REPRESENTANTES ===')
        
        # Representante para Grupo A
        representante_a = Representante.objects.create(
            NombreColegio='Colegio San Francisco',
            DireccionColegio='Av. Principal 123, Quito',
            TelefonoInstitucional='0223456781',
            CorreoInstitucional='colegio.sanfrancisco@edu.ec',
            NombresRepresentante='María González',
            TelefonoRepresentante='0987654321',
            CorreoRepresentante='maria.gonzalez@colegio.edu.ec'
        )
        self.stdout.write(f'✓ Representante A creado: {representante_a.NombresRepresentante} - {representante_a.NombreColegio}')
        
        # Representante para Grupo B
        representante_b = Representante.objects.create(
            NombreColegio='Instituto Tecnológico',
            DireccionColegio='Calle Secundaria 456, Guayaquil',
            TelefonoInstitucional='0423456782',
            CorreoInstitucional='instituto.tecnologico@edu.ec',
            NombresRepresentante='Carlos Rodríguez',
            TelefonoRepresentante='0987654322',
            CorreoRepresentante='carlos.rodriguez@instituto.edu.ec'
        )
        self.stdout.write(f'✓ Representante B creado: {representante_b.NombresRepresentante} - {representante_b.NombreColegio}')
        
        # ===== CREAR GRUPOS =====
        self.stdout.write('\n=== CREANDO GRUPOS ===')
        
        grupo_a = GrupoParticipantes.objects.create(
            name='Grupo A - San Francisco',
            representante=representante_a
        )
        self.stdout.write(f'✓ Grupo A creado: {grupo_a.name}')
        
        grupo_b = GrupoParticipantes.objects.create(
            name='Grupo B - Tecnológico',
            representante=representante_b
        )
        self.stdout.write(f'✓ Grupo B creado: {grupo_b.name}')
        
        # ===== CREAR PARTICIPANTES =====
        self.stdout.write('\n=== CREANDO PARTICIPANTES ===')
        
        participantes_grupo_a = []
        participantes_grupo_b = []
        participantes_individuales = []
        
        # Crear 12 participantes para Grupo A
        self.stdout.write('Creando 12 participantes para Grupo A...')
        for i in range(1, 13):
            cedula = f'12345678{str(i).zfill(2)}'
            nombres = f'Estudiante A{i}'
            email = f'estudiante.a{i}@sanfrancisco.edu.ec'
            
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
            
            participantes_grupo_a.append(participante)
            self.stdout.write(f'  ✓ {nombres} ({cedula})')
        
        # Crear 12 participantes para Grupo B
        self.stdout.write('Creando 12 participantes para Grupo B...')
        for i in range(13, 25):
            cedula = f'12345678{str(i).zfill(2)}'
            nombres = f'Estudiante B{i-12}'
            email = f'estudiante.b{i-12}@tecnologico.edu.ec'
            
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
            
            participantes_grupo_b.append(participante)
            self.stdout.write(f'  ✓ {nombres} ({cedula})')
        
        # Crear 6 participantes individuales
        self.stdout.write('Creando 6 participantes individuales...')
        for i in range(25, 31):
            cedula = f'12345678{str(i).zfill(2)}'
            nombres = f'Estudiante Ind{i-24}'
            email = f'estudiante.ind{i-24}@individual.edu.ec'
            
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
            
            participantes_individuales.append(participante)
            self.stdout.write(f'  ✓ {nombres} ({cedula})')
        
        # Asignar participantes a sus grupos
        grupo_a.participantes.add(*participantes_grupo_a)
        grupo_b.participantes.add(*participantes_grupo_b)
        
        self.stdout.write(f'✓ 12 participantes asignados a Grupo A')
        self.stdout.write(f'✓ 12 participantes asignados a Grupo B')
        self.stdout.write(f'✓ 6 participantes individuales creados')
        
        # Lista completa de participantes para etapa 1
        todos_participantes = participantes_grupo_a + participantes_grupo_b + participantes_individuales
        
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
        
        # Asignar grupos y participantes individuales a la evaluación de etapa 1
        evaluacion_etapa1.grupos_participantes.add(grupo_a, grupo_b)
        evaluacion_etapa1.participantes_individuales.add(*participantes_individuales)
        self.stdout.write(f'✓ 2 grupos y 6 participantes individuales asignados a la evaluación de etapa 1')
        
        # Simular resultados de etapa 1
        self.stdout.write('Simulando resultados de etapa 1...')
        
        # Primeros 15 participantes: nota 10/10 (todas correctas)
        for i in range(15):
            participante = todos_participantes[i]
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
                completada=True,
                numero_intento=1  # Asegurar que el número de intento esté establecido
            )
            
            self.stdout.write(f'  ✓ {participante.NombresCompletos}: {puntaje_ponderado:.3f}/10 ({percentage:.1f}%) - {tiempo_utilizado} min')
        
        # Últimos 15 participantes: nota menor a 10/10 (simular respuestas mixtas)
        for i in range(15, 30):
            participante = todos_participantes[i]
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
                completada=True,
                numero_intento=1  # Asegurar que el número de intento esté establecido
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
                completada=True,
                numero_intento=1  # Asegurar que el número de intento esté establecido
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
                completada=True,
                numero_intento=1  # Asegurar que el número de intento esté establecido
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
            completada=True,
            numero_intento=1  # Asegurar que el número de intento esté establecido
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
                completada=True,
                numero_intento=1  # Asegurar que el número de intento esté establecido
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
                completada=True,
                numero_intento=1  # Asegurar que el número de intento esté establecido
            )
            
            self.stdout.write(f'  ✓ {participante.NombresCompletos}: {puntaje_ponderado:.3f}/10 ({percentage:.1f}%) - {tiempo_utilizado} min [BRONCE]')
        
        # ===== RESUMEN FINAL =====
        self.stdout.write('\n=== RESUMEN DE EVALUACIONES CREADAS ===')
        
        # Etapa 1
        self.stdout.write(f'\n📊 ETAPA 1 - Clasificatoria:')
        self.stdout.write(f'   ID: {evaluacion_etapa1.id}')
        self.stdout.write(f'   Grupos: 2 (A y B)')
        self.stdout.write(f'   Participantes por grupo: 12 cada uno')
        self.stdout.write(f'   Participantes individuales: 6')
        self.stdout.write(f'   Total participantes: 30')
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
        self.stdout.write('✅ 2 Grupos creados con sus representantes')
        self.stdout.write('✅ 30 Participantes totales (12+12+6)')
        self.stdout.write('✅ Etapa 1: 30 participantes → 15 clasificados')
        self.stdout.write('✅ Etapa 2: 15 participantes → 5 finalistas')
        self.stdout.write('✅ Etapa 3: 5 participantes → 1 ORO, 2 PLATA, 2 BRONCE')
        self.stdout.write(f'\n📋 INFORMACIÓN PARA ACCESO:')
        self.stdout.write(f'   - Todos los usuarios tienen contraseña temporal de 6 caracteres')
        self.stdout.write(f'   - El username de cada participante es su número de cédula')
        self.stdout.write(f'   - Los resultados incluyen el campo numero_intento = 1')
        self.stdout.write('\n🎯 PRÓXIMOS PASOS:')
        self.stdout.write('   1. Verificar que las evaluaciones aparezcan en el admin')
        self.stdout.write('   2. Probar el procedimiento de preselección automática')
        self.stdout.write('   3. Validar que los rankings funcionen correctamente')
        self.stdout.write(f'\n⚡ El script se ejecutó exitosamente sin errores')
        self.stdout.write('Ahora puedes verificar los procedimientos de preselección automática.') 