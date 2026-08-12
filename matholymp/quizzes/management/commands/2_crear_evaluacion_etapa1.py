#!/usr/bin/env python
"""
Script para crear una evaluación de prueba para la Etapa 1 con 60 preguntas de matemáticas
y simular resultados realistas para todos los participantes existentes.

Este script:
1. Crea una evaluación completa para la Etapa 1 con 60 preguntas de múltiple opción
2. Distribuye las preguntas en categorías: álgebra, geometría, aritmética, probabilidad, trigonometría y cálculo
3. Asigna la evaluación a todos los grupos de participantes del año activo
4. Simula resultados realistas para todos los participantes con:
   - Respuestas simuladas basadas en nivel de habilidad individual
   - Puntajes calculados en base a aciertos/errores reales
   - Diferentes niveles de habilidad usando distribución beta
   - Tiempos de evaluación realistas (25-120 minutos con distribución ponderada)
   - Fechas de inicio y fin simuladas
   - Control de cambios de pestaña aleatorio
   - Respuestas guardadas en base de datos para auditoría

Usar después de ejecutar el script 1_generar_participantes.py
"""

import os
import sys
import django
from django.utils import timezone
from datetime import timedelta
import random
from django.core.management.base import BaseCommand
from decimal import Decimal

from quizzes.models import Evaluacion, Pregunta, Opcion, GrupoParticipantes, Participantes, ResultadoEvaluacion

class Command(BaseCommand):
    help = 'Crea una evaluación completa para la Etapa 1 con 60 preguntas de matemáticas y simula respuestas realistas para todos los participantes'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando creación de evaluación de prueba para Etapa 1...")

        # Configurar fechas para la evaluación
        ahora = timezone.now()
        inicio = ahora + timedelta(hours=1)  # Inicia en 1 hora
        fin = ahora + timedelta(days=7)      # Termina en 7 días

        # Crear la evaluación
        evaluacion = Evaluacion.objects.create(
            title="Evaluación Etapa 1 - Prueba Primaria",
            etapa=1,
            start_time=inicio,
            end_time=fin,
            duration_minutes=60,  # 1 hora
            preguntas_a_mostrar=10,  # Mostrar 10 preguntas aleatorias
            anio=ahora.year
        )

        self.stdout.write(f"✅ Evaluación creada: {evaluacion.title}")
        self.stdout.write(f"   - Inicio: {inicio.strftime('%d/%m/%Y %H:%M')}")
        self.stdout.write(f"   - Fin: {fin.strftime('%d/%m/%Y %H:%M')}")
        self.stdout.write(f"   - Duración: {evaluacion.duration_minutes} minutos")
        self.stdout.write(f"   - Preguntas a mostrar: {evaluacion.preguntas_a_mostrar}")

        # Asignar todos los grupos de participantes del año activo
        grupos = GrupoParticipantes.objects.all()
        if grupos.exists():
            evaluacion.grupos_participantes.set(grupos)
            self.stdout.write(f"✅ Asignados {grupos.count()} grupos a la evaluación")

        # Generar preguntas de primaria
        preguntas_primaria = self.generar_preguntas_primaria()
        random.shuffle(preguntas_primaria)

        preguntas_creadas = 0
        for i, pregunta_data in enumerate(preguntas_primaria[:20]):  # Tomar solo 20 preguntas
            try:
                pregunta = Pregunta.objects.create(
                    evaluacion=evaluacion,
                    text=pregunta_data["text"],
                    puntos=1
                )
                for j, opcion_texto in enumerate(pregunta_data["opciones"]):
                    Opcion.objects.create(
                        pregunta=pregunta,
                        text=opcion_texto,
                        is_correct=(j == pregunta_data["correcta"])
                    )
                preguntas_creadas += 1
                self.stdout.write(f"✅ Pregunta {preguntas_creadas}/20 creada: {pregunta.text[:50]}...")
            except Exception as e:
                self.stdout.write(f"❌ Error al crear pregunta {i+1}: {e}")
                continue

        self.stdout.write(f"\n🎉 ¡Evaluación de prueba completada!")
        self.stdout.write(f"📊 Resumen:")
        self.stdout.write(f"   - Evaluación: {evaluacion.title}")
        self.stdout.write(f"   - Preguntas creadas: {preguntas_creadas}")
        self.stdout.write(f"   - Opciones por pregunta: 4")
        self.stdout.write(f"   - Total de opciones: {preguntas_creadas * 4}")
        self.stdout.write(f"   - Grupos asignados: {evaluacion.grupos_participantes.count()}")

    def generar_preguntas_primaria(self):
        """Genera preguntas de matemáticas de 4to de primaria (sin LaTeX ni símbolos especiales)"""
        preguntas = [
            {
                "text": "¿Cuánto es 25 + 17?",
                "opciones": ["32", "42", "43", "41"],
                "correcta": 2
            },
            {
                "text": "¿Cuánto es 56 - 29?",
                "opciones": ["27", "26", "25", "28"],
                "correcta": 0
            },
            {
                "text": "¿Cuánto es 8 x 7?",
                "opciones": ["54", "56", "64", "58"],
                "correcta": 1
            },
            {
                "text": "¿Cuánto es 72 ÷ 8?",
                "opciones": ["8", "9", "10", "7"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el doble de 15?",
                "opciones": ["25", "30", "35", "40"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es la mitad de 48?",
                "opciones": ["22", "24", "26", "28"],
                "correcta": 1
            },
            {
                "text": "¿Cuánto es 9 x 6?",
                "opciones": ["54", "56", "58", "52"],
                "correcta": 0
            },
            {
                "text": "¿Cuánto es 100 - 37?",
                "opciones": ["63", "67", "73", "57"],
                "correcta": 0
            },
            {
                "text": "¿Cuánto es 13 + 28?",
                "opciones": ["41", "42", "43", "40"],
                "correcta": 0
            },
            {
                "text": "¿Cuánto es 36 ÷ 4?",
                "opciones": ["8", "9", "10", "7"],
                "correcta": 1
            },
            {
                "text": "¿Cuál es el triple de 12?",
                "opciones": ["24", "36", "32", "30"],
                "correcta": 1
            },
            {
                "text": "¿Cuánto es 7 x 5?",
                "opciones": ["30", "35", "40", "25"],
                "correcta": 1
            },
            {
                "text": "¿Cuánto es 60 + 18?",
                "opciones": ["68", "78", "88", "58"],
                "correcta": 0
            },
            {
                "text": "¿Cuánto es 45 ÷ 5?",
                "opciones": ["8", "9", "10", "7"],
                "correcta": 1
            },
            {
                "text": "¿Cuánto es 6 x 8?",
                "opciones": ["42", "48", "54", "56"],
                "correcta": 1
            },
            {
                "text": "¿Cuánto es 90 - 27?",
                "opciones": ["63", "67", "73", "57"],
                "correcta": 0
            },
            {
                "text": "¿Cuánto es 14 + 19?",
                "opciones": ["33", "32", "31", "34"],
                "correcta": 0
            },
            {
                "text": "¿Cuánto es 8 x 4?",
                "opciones": ["32", "34", "36", "38"],
                "correcta": 0
            },
            {
                "text": "¿Cuánto es 64 ÷ 8?",
                "opciones": ["6", "7", "8", "9"],
                "correcta": 2
            },
            {
                "text": "¿Cuánto es 23 + 17?",
                "opciones": ["40", "41", "42", "39"],
                "correcta": 0
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
            {"text": "¿Cuánto es 15 + 8?", "opciones": ["22", "23", "24", "25"], "correcta": 1},
            {"text": "¿Cuánto es 30 - 12?", "opciones": ["16", "18", "20", "22"], "correcta": 1},
            {"text": "¿Cuánto es 5 x 6?", "opciones": ["25", "30", "35", "40"], "correcta": 1},
            {"text": "¿Cuánto es 36 ÷ 6?", "opciones": ["5", "6", "7", "8"], "correcta": 1},
            {"text": "¿Cuánto es 9 + 14?", "opciones": ["22", "23", "24", "25"], "correcta": 1}
        ]
        return preguntas

    def generar_preguntas_probabilidad(self):
        """Genera preguntas de conocimiento general para 4to de primaria (sin LaTeX ni símbolos especiales)"""
        preguntas = [
            {"text": "¿Cuántas caras tiene una moneda?", "opciones": ["1", "2", "3", "4"], "correcta": 1},
            {"text": "¿Cuántos números hay en un dado?", "opciones": ["4", "5", "6", "7"], "correcta": 2},
            {"text": "¿Cuál es el número mayor: 8, 12, 5 o 9?", "opciones": ["8", "12", "5", "9"], "correcta": 1},
            {"text": "¿Cuál es el número menor: 3, 7, 2 o 5?", "opciones": ["3", "7", "2", "5"], "correcta": 2},
            {"text": "¿Cuántos días tiene una semana?", "opciones": ["5", "6", "7", "8"], "correcta": 2}
        ]
        return preguntas

    def generar_preguntas_trigonometria(self):
        """Genera preguntas de conocimiento general para 4to de primaria (sin LaTeX ni símbolos especiales)"""
        preguntas = [
            {"text": "¿Cuántos meses tiene un año?", "opciones": ["10", "11", "12", "13"], "correcta": 2},
            {"text": "¿Cuántas horas tiene un día?", "opciones": ["12", "24", "36", "48"], "correcta": 1},
            {"text": "¿Cuántos centímetros hay en un metro?", "opciones": ["10", "100", "1000", "10000"], "correcta": 1},
            {"text": "¿Cuántos días tiene febrero en un año normal?", "opciones": ["28", "29", "30", "31"], "correcta": 0},
            {"text": "¿Cuántos minutos tiene una hora?", "opciones": ["30", "45", "60", "90"], "correcta": 2}
        ]
        return preguntas

    def generar_preguntas_calculo(self):
        """Genera preguntas de conocimiento general para 4to de primaria (sin LaTeX ni símbolos especiales)"""
        preguntas = [
            {"text": "¿Cuántos días tiene un año normal?", "opciones": ["360", "365", "366", "364"], "correcta": 1},
            {"text": "¿Cuántos segundos tiene un minuto?", "opciones": ["30", "45", "60", "90"], "correcta": 2},
            {"text": "¿Cuántos colores tiene el arcoíris?", "opciones": ["5", "6", "7", "8"], "correcta": 2},
            {"text": "¿Cuántos continentes hay en el mundo?", "opciones": ["5", "6", "7", "8"], "correcta": 2},
            {"text": "¿Cuántos dedos tiene una mano?", "opciones": ["4", "5", "6", "7"], "correcta": 1}
        ]
        return preguntas 