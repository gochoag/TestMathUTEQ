#!/usr/bin/env python
"""
Script para crear una evaluación de prueba para la Etapa 1 con 60 preguntas de matemáticas
"""

import os
import sys
import django
from django.utils import timezone
from datetime import timedelta
import random
from django.core.management.base import BaseCommand

from quizzes.models import Evaluacion, Pregunta, Opcion, GrupoParticipantes, Participantes, ResultadoEvaluacion, SystemConfig

class Command(BaseCommand):
    help = 'Crea una evaluación completa para la Etapa 1 con 60 preguntas de matemáticas'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando creación de evaluación para Etapa 1...")
        
        # Obtener el año activo del sistema
        anio_activo = SystemConfig.get_active_year()
        self.stdout.write(f"📅 Año activo del sistema: {anio_activo}")
        
        # Verificar si ya existe una evaluación de etapa 1 para este año
        evaluacion_existente = Evaluacion.objects.filter(etapa=1, anio=anio_activo).first()
        if evaluacion_existente:
            self.stdout.write(f"⚠️  Ya existe una evaluación de Etapa 1 para el año {anio_activo}: {evaluacion_existente.title}")
            self.stdout.write("   Creando una nueva evaluación...")
        
        # Configurar fechas para la evaluación
        ahora = timezone.now()
        inicio = ahora - timedelta(hours=2)  # Inició hace 2 horas (para simular evaluación activa)
        fin = ahora + timedelta(days=7)      # Termina en 7 días
        
        # Crear la evaluación
        evaluacion = Evaluacion.objects.create(
            title=f"Evaluación Etapa 1 - Olimpiada de Matemáticas {anio_activo}",
            etapa=1,
            start_time=inicio,
            end_time=fin,
            duration_minutes=120,  # 2 horas
            preguntas_a_mostrar=30,  # Mostrar 30 preguntas aleatorias de las 60
            anio=anio_activo
        )
        
        self.stdout.write(f"✅ Evaluación creada: {evaluacion.title}")
        self.stdout.write(f"   - Inicio: {inicio.strftime('%d/%m/%Y %H:%M')}")
        self.stdout.write(f"   - Fin: {fin.strftime('%d/%m/%Y %H:%M')}")
        self.stdout.write(f"   - Duración: {evaluacion.duration_minutes} minutos")
        self.stdout.write(f"   - Preguntas a mostrar: {evaluacion.preguntas_a_mostrar}")
        
        # Obtener todos los grupos del año activo para asignar a la evaluación
        grupos = GrupoParticipantes.objects.filter(anio=anio_activo)
        if grupos.exists():
            evaluacion.grupos_participantes.set(grupos)
            self.stdout.write(f"✅ Asignados {grupos.count()} grupos a la evaluación")
        else:
            self.stdout.write("⚠️  No se encontraron grupos para asignar. Ejecuta primero el script 1_generar_participantes.py")
        
        # Generar todas las preguntas
        todas_preguntas = []
        todas_preguntas.extend(self.generar_preguntas_algebra())
        todas_preguntas.extend(self.generar_preguntas_geometria())
        todas_preguntas.extend(self.generar_preguntas_aritmetica())
        todas_preguntas.extend(self.generar_preguntas_probabilidad())
        todas_preguntas.extend(self.generar_preguntas_trigonometria())
        todas_preguntas.extend(self.generar_preguntas_calculo())
        
        # Mezclar las preguntas para mayor variedad
        random.shuffle(todas_preguntas)
        
        # Crear las preguntas en la base de datos
        preguntas_creadas = 0
        for i, pregunta_data in enumerate(todas_preguntas[:60]):  # Tomar solo 60 preguntas
            try:
                pregunta = Pregunta.objects.create(
                    evaluacion=evaluacion,
                    text=pregunta_data["text"],
                    puntos=1
                )
                
                # Crear las opciones
                for j, opcion_texto in enumerate(pregunta_data["opciones"]):
                    Opcion.objects.create(
                        pregunta=pregunta,
                        text=opcion_texto,
                        is_correct=(j == pregunta_data["correcta"])
                    )
                
                preguntas_creadas += 1
                self.stdout.write(f"✅ Pregunta {preguntas_creadas}/60 creada: {pregunta.text[:50]}...")
                
            except Exception as e:
                self.stdout.write(f"❌ Error al crear pregunta {i+1}: {e}")
                continue
        
        # Generar puntajes para los participantes
        self.stdout.write(f"\n🎯 Generando puntajes para los participantes...")
        puntajes_generados = self.generar_puntajes_participantes(evaluacion)
        
        self.stdout.write(f"\n🎉 ¡Evaluación completada!")
        self.stdout.write(f"📊 Resumen:")
        self.stdout.write(f"   - Evaluación: {evaluacion.title}")
        self.stdout.write(f"   - Preguntas creadas: {preguntas_creadas}")
        self.stdout.write(f"   - Opciones por pregunta: 4")
        self.stdout.write(f"   - Total de opciones: {preguntas_creadas * 4}")
        self.stdout.write(f"   - Grupos asignados: {evaluacion.grupos_participantes.count()}")
        self.stdout.write(f"   - Participantes con puntajes: {puntajes_generados}")
        
        # Mostrar distribución por categorías
        self.stdout.write(f"\n📋 Distribución de preguntas:")
        categorias = {
            "Álgebra": len(self.generar_preguntas_algebra()),
            "Geometría": len(self.generar_preguntas_geometria()),
            "Aritmética": len(self.generar_preguntas_aritmetica()),
            "Probabilidad": len(self.generar_preguntas_probabilidad()),
            "Trigonometría": len(self.generar_preguntas_trigonometria()),
            "Cálculo": len(self.generar_preguntas_calculo())
        }
        
        for categoria, cantidad in categorias.items():
            self.stdout.write(f"   - {categoria}: {cantidad} preguntas")
        
        # Mostrar ranking de mejores puntajes
        mejores_resultados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado')[:5]
        
        if mejores_resultados:
            self.stdout.write(f"\n🏆 Top 5 mejores puntajes:")
            for i, resultado in enumerate(mejores_resultados, 1):
                self.stdout.write(f"   {i}. {resultado.participante.NombresCompletos}: {resultado.get_puntaje_numerico()} pts ({resultado.get_tiempo_formateado()})")

    def generar_preguntas_algebra(self):
        """Genera preguntas de álgebra"""
        preguntas = [
            {
                "text": "Resuelve la ecuación: $2x + 5 = 13$",
                "opciones": ["x = 4", "x = 3", "x = 5", "x = 6"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el valor de $x$ en la ecuación $3x - 7 = 8$?",
                "opciones": ["x = 3", "x = 5", "x = 4", "x = 6"],
                "correcta": 1
            },
            {
                "text": "Resuelve: $\\frac{x}{2} + 3 = 7$",
                "opciones": ["x = 6", "x = 8", "x = 4", "x = 10"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es la solución de $2(x + 3) = 10$?",
                "opciones": ["x = 1", "x = 2", "x = 3", "x = 4"],
                "correcta": 1
            },
            {
                "text": "Resuelve la ecuación cuadrática: $x^2 - 5x + 6 = 0$",
                "opciones": ["x = 2, x = 3", "x = 1, x = 6", "x = -2, x = -3", "x = 2, x = -3"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el valor de $y$ si $2y + 4 = 3y - 1$?",
                "opciones": ["y = 3", "y = 5", "y = 4", "y = 6"],
                "correcta": 1
            },
            {
                "text": "Resuelve: $\\frac{2x + 1}{3} = 5$",
                "opciones": ["x = 6", "x = 7", "x = 8", "x = 9"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es la solución de $x^2 + 6x + 9 = 0$?",
                "opciones": ["x = -3", "x = 3", "x = -3 (doble)", "x = 3 (doble)"],
                "correcta": 2
            },
            {
                "text": "Resuelve: $|x - 3| = 5$",
                "opciones": ["x = 8", "x = -2", "x = 8 o x = -2", "x = 3"],
                "correcta": 2
            },
            {
                "text": "¿Cuál es el valor de $a$ si $3a + 2 = 4a - 1$?",
                "opciones": ["a = 1", "a = 2", "a = 3", "a = 4"],
                "correcta": 2
            }
        ]
        return preguntas

    def generar_preguntas_geometria(self):
        """Genera preguntas de geometría"""
        preguntas = [
            {
                "text": "¿Cuál es el área de un cuadrado de lado 6 cm?",
                "opciones": ["24 cm²", "30 cm²", "36 cm²", "42 cm²"],
                "correcta": 2
            },
            {
                "text": "¿Cuál es el perímetro de un rectángulo de 8 cm de largo y 5 cm de ancho?",
                "opciones": ["26 cm", "40 cm", "13 cm", "20 cm"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el área de un triángulo con base 10 cm y altura 6 cm?",
                "opciones": ["30 cm²", "60 cm²", "15 cm²", "45 cm²"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es la longitud de la hipotenusa de un triángulo rectángulo con catetos de 3 cm y 4 cm?",
                "opciones": ["5 cm", "7 cm", "6 cm", "8 cm"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el área de un círculo con radio 5 cm? (π ≈ 3.14)",
                "opciones": ["78.5 cm²", "31.4 cm²", "15.7 cm²", "25 cm²"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el volumen de un cubo de arista 4 cm?",
                "opciones": ["16 cm³", "64 cm³", "32 cm³", "48 cm³"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el área lateral de un cilindro con radio 3 cm y altura 8 cm? (π ≈ 3.14)",
                "opciones": ["150.72 cm²", "75.36 cm²", "113.04 cm²", "226.08 cm²"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es la medida de cada ángulo interior de un hexágono regular?",
                "opciones": ["60°", "90°", "120°", "180°"],
                "correcta": 2
            },
            {
                "text": "¿Cuál es el área de un trapecio con bases 6 cm y 10 cm, y altura 4 cm?",
                "opciones": ["32 cm²", "24 cm²", "40 cm²", "28 cm²"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es la longitud de la diagonal de un cuadrado de lado 8 cm?",
                "opciones": ["8√2 cm", "16 cm", "8 cm", "4√2 cm"],
                "correcta": 0
            }
        ]
        return preguntas

    def generar_preguntas_aritmetica(self):
        """Genera preguntas de aritmética"""
        preguntas = [
            {
                "text": "¿Cuál es el resultado de $\\frac{3}{4} + \\frac{1}{2}$?",
                "opciones": ["$\\frac{5}{4}$", "$\\frac{4}{6}$", "$\\frac{1}{4}$", "$\\frac{5}{6}$"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el 25% de 80?",
                "opciones": ["15", "20", "25", "30"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el resultado de $2^3 \\times 3^2$?",
                "opciones": ["72", "36", "54", "108"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el MCD de 24 y 36?",
                "opciones": ["6", "12", "8", "18"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el mcm de 8 y 12?",
                "opciones": ["16", "24", "32", "48"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el resultado de $\\frac{5}{6} \\div \\frac{2}{3}$?",
                "opciones": ["$\\frac{5}{4}$", "$\\frac{10}{18}$", "$\\frac{15}{12}$", "$\\frac{5}{9}$"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el valor de $\\sqrt{144}$?",
                "opciones": ["10", "12", "14", "16"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el resultado de $(-3)^2$?",
                "opciones": ["-9", "9", "-6", "6"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el 15% de 200?",
                "opciones": ["25", "30", "35", "40"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el resultado de $\\frac{7}{8} - \\frac{3}{4}$?",
                "opciones": ["$\\frac{1}{8}$", "$\\frac{4}{4}$", "$\\frac{1}{4}$", "$\\frac{3}{8}$"],
                "correcta": 0
            }
        ]
        return preguntas

    def generar_preguntas_probabilidad(self):
        """Genera preguntas de probabilidad y estadística"""
        preguntas = [
            {
                "text": "¿Cuál es la probabilidad de obtener cara al lanzar una moneda?",
                "opciones": ["$\\frac{1}{4}$", "$\\frac{1}{2}$", "$\\frac{1}{3}$", "$\\frac{2}{3}$"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es la probabilidad de obtener un número par al lanzar un dado?",
                "opciones": ["$\\frac{1}{6}$", "$\\frac{1}{3}$", "$\\frac{1}{2}$", "$\\frac{2}{3}$"],
                "correcta": 2
            },
            {
                "text": "¿Cuál es la media de los números 2, 4, 6, 8, 10?",
                "opciones": ["5", "6", "7", "8"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es la mediana de los números 1, 3, 5, 7, 9?",
                "opciones": ["3", "5", "7", "9"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es la moda de los números 2, 3, 3, 4, 5, 3, 6?",
                "opciones": ["2", "3", "4", "5"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es la probabilidad de obtener un as de una baraja de 52 cartas?",
                "opciones": ["$\\frac{1}{52}$", "$\\frac{1}{13}$", "$\\frac{4}{52}$", "$\\frac{1}{4}$"],
                "correcta": 2
            },
            {
                "text": "¿Cuál es la probabilidad de obtener un número mayor a 4 al lanzar un dado?",
                "opciones": ["$\\frac{1}{6}$", "$\\frac{1}{3}$", "$\\frac{1}{2}$", "$\\frac{2}{3}$"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es la varianza de los números 2, 4, 6, 8?",
                "opciones": ["5", "6", "7", "8"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es la probabilidad de obtener dos caras al lanzar dos monedas?",
                "opciones": ["$\\frac{1}{4}$", "$\\frac{1}{2}$", "$\\frac{1}{3}$", "$\\frac{3}{4}$"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es la desviación estándar de los números 1, 3, 5, 7, 9?",
                "opciones": ["2", "$\\sqrt{8}$", "3", "$\\sqrt{10}$"],
                "correcta": 1
            }
        ]
        return preguntas

    def generar_preguntas_trigonometria(self):
        """Genera preguntas de trigonometría"""
        preguntas = [
            {
                "text": "¿Cuál es el valor de $\\sin(30°)$?",
                "opciones": ["$\\frac{1}{2}$", "$\\frac{\\sqrt{3}}{2}$", "$\\frac{1}{\\sqrt{2}}$", "$\\frac{\\sqrt{2}}{2}$"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el valor de $\\cos(60°)$?",
                "opciones": ["$\\frac{1}{2}$", "$\\frac{\\sqrt{3}}{2}$", "$\\frac{1}{\\sqrt{2}}$", "$\\frac{\\sqrt{2}}{2}$"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el valor de $\\tan(45°)$?",
                "opciones": ["0", "1", "$\\frac{1}{\\sqrt{2}}$", "$\\sqrt{3}$"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el valor de $\\sin(90°)$?",
                "opciones": ["0", "1", "-1", "$\\frac{1}{2}$"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el valor de $\\cos(0°)$?",
                "opciones": ["0", "1", "-1", "$\\frac{1}{2}$"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el valor de $\\sin^2(30°) + \\cos^2(30°)$?",
                "opciones": ["0", "1", "$\\frac{1}{2}$", "$\\frac{3}{4}$"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el valor de $\\tan(30°)$?",
                "opciones": ["$\\frac{1}{\\sqrt{3}}$", "$\\sqrt{3}$", "$\\frac{1}{2}$", "$\\frac{\\sqrt{3}}{2}$"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es el valor de $\\csc(30°)$?",
                "opciones": ["1", "2", "$\\frac{1}{2}$", "$\\sqrt{2}$"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el valor de $\\sec(60°)$?",
                "opciones": ["1", "2", "$\\frac{1}{2}$", "$\\sqrt{2}$"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el valor de $\\cot(45°)$?",
                "opciones": ["0", "1", "$\\frac{1}{\\sqrt{2}}$", "$\\sqrt{3}$"],
                "correcta": 1
            }
        ]
        return preguntas

    def generar_preguntas_calculo(self):
        """Genera preguntas de cálculo básico"""
        preguntas = [
            {
                "text": "¿Cuál es la derivada de $x^2$?",
                "opciones": ["x", "2x", "2x²", "x²"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es la derivada de $3x^3$?",
                "opciones": ["3x²", "9x²", "6x²", "x²"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es la integral de $2x$?",
                "opciones": ["x²", "x² + C", "2x²", "2x² + C"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el límite de $\\frac{x^2 - 1}{x - 1}$ cuando $x$ tiende a 1?",
                "opciones": ["0", "1", "2", "No existe"],
                "correcta": 2
            },
            {
                "text": "¿Cuál es la derivada de $\\sin(x)$?",
                "opciones": ["cos(x)", "-cos(x)", "sin(x)", "-sin(x)"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es la derivada de $e^x$?",
                "opciones": ["e^x", "xe^x", "e^(x-1)", "ln(x)"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es la integral de $\\cos(x)$?",
                "opciones": ["sin(x)", "sin(x) + C", "-sin(x)", "-sin(x) + C"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el límite de $\\frac{1}{x}$ cuando $x$ tiende a infinito?",
                "opciones": ["0", "1", "infinito", "No existe"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es la derivada de $\\ln(x)$?",
                "opciones": ["1/x", "x", "e^x", "1"],
                "correcta": 0
            },
            {
                "text": "¿Cuál es la integral de $x^2$?",
                "opciones": ["x³/3", "x³/3 + C", "2x", "2x + C"],
                "correcta": 1
            }
        ]
        return preguntas

    def generar_puntajes_participantes(self, evaluacion):
        """Genera puntajes aleatorios para todos los participantes de la evaluación"""
        participantes_autorizados = evaluacion.get_participantes_etapa1()
        puntajes_generados = 0
        
        if not participantes_autorizados:
            self.stdout.write("⚠️  No hay participantes autorizados para esta evaluación")
            return 0
        
        self.stdout.write(f"📋 Encontrados {len(participantes_autorizados)} participantes autorizados")
        
        for participante in participantes_autorizados:
            try:
                # Verificar si ya tiene un resultado para esta evaluación
                resultado_existente = ResultadoEvaluacion.objects.filter(
                    evaluacion=evaluacion,
                    participante=participante
                ).first()
                
                if resultado_existente:
                    self.stdout.write(f"⏭️  {participante.NombresCompletos} ya tiene puntaje asignado")
                    continue
                
                # Generar puntaje aleatorio (simulando diferentes niveles de rendimiento)
                # 20% excelente (8-10), 30% bueno (6-8), 30% regular (4-6), 20% bajo (0-4)
                rand = random.random()
                if rand < 0.2:  # 20% excelente
                    puntos_obtenidos = round(random.uniform(8.0, 10.0), 3)
                elif rand < 0.5:  # 30% bueno
                    puntos_obtenidos = round(random.uniform(6.0, 8.0), 3)
                elif rand < 0.8:  # 30% regular
                    puntos_obtenidos = round(random.uniform(4.0, 6.0), 3)
                else:  # 20% bajo
                    puntos_obtenidos = round(random.uniform(0.0, 4.0), 3)
                
                # Calcular porcentaje
                puntaje_porcentaje = (puntos_obtenidos / 10.0) * 100
                
                # Generar tiempo utilizado aleatorio (entre 60 y 120 minutos)
                tiempo_utilizado = random.randint(60, 120)
                
                # Crear fechas simuladas
                fecha_inicio_simulada = evaluacion.start_time + timedelta(minutes=random.randint(0, 60))
                fecha_fin_simulada = fecha_inicio_simulada + timedelta(minutes=tiempo_utilizado)
                
                # Crear el resultado
                resultado = ResultadoEvaluacion.objects.create(
                    evaluacion=evaluacion,
                    participante=participante,
                    numero_intento=1,
                    puntaje=round(puntaje_porcentaje, 2),
                    puntos_obtenidos=puntos_obtenidos,
                    puntos_totales=10,
                    tiempo_utilizado=tiempo_utilizado,
                    fecha_inicio=fecha_inicio_simulada,
                    fecha_fin=fecha_fin_simulada,
                    completada=True,
                    es_mejor_intento=True,
                    tiempo_restante=0
                )
                
                puntajes_generados += 1
                self.stdout.write(f"✅ Puntaje asignado a {participante.NombresCompletos}: {resultado.get_puntaje_numerico()} pts")
                
            except Exception as e:
                self.stdout.write(f"❌ Error al asignar puntaje a {participante.NombresCompletos}: {e}")
                continue
        
        return puntajes_generados 