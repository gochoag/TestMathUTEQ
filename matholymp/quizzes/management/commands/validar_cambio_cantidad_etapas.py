#!/usr/bin/env python
"""
Comando para validar el cambio de la cantidad de etapas.

Este script realiza lo siguiente:
- Crea 6 representantes y 6 grupos (cada grupo con su representante)
- Crea 30 participantes y los distribuye equitativamente en los 6 grupos
- Crea una evaluación de Etapa 1 con 40 preguntas (4 opciones cada una)
- Asigna los 6 grupos a la evaluación de Etapa 1
- Crea resultados con puntajes para cada participante en dicha evaluación

Para ejecutar:
    python manage.py validar_cambio_cantidad_etapas
"""

import random
import re
import unicodedata
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from quizzes.models import (
    Participantes,
    Representante,
    GrupoParticipantes,
    Evaluacion,
    Pregunta,
    Opcion,
    ResultadoEvaluacion,
    SystemConfig,
)


class Command(BaseCommand):
    help = (
        "Crea 6 grupos con representantes, 30 participantes, una evaluación Etapa 1 con 40 preguntas, "
        "asigna los grupos a la evaluación y genera puntajes para los participantes."
    )

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando script de validación de cambio de etapas...")

        # Año activo
        anio_activo = SystemConfig.get_active_year()

        # 1) Crear 6 representantes
        representantes = [self._crear_representante() for _ in range(6)]
        self.stdout.write(f"✅ Representantes creados: {len(representantes)}")

        # 2) Crear 6 grupos (uno por representante)
        grupos = [self._crear_grupo_participantes(rep, i + 1, anio_activo) for i, rep in enumerate(representantes)]
        self.stdout.write(f"✅ Grupos creados: {len(grupos)}")

        # 3) Crear 30 participantes y distribuirlos 5 por grupo
        participantes = []
        for i in range(30):
            participante = self._crear_participante_unico(anio_activo)
            grupo = grupos[i % 6]
            grupo.participantes.add(participante)
            participantes.append(participante)
        self.stdout.write(f"✅ Participantes creados y asignados: {len(participantes)}")

        # 4) Crear evaluación Etapa 1 con 40 preguntas
        ahora = timezone.now()
        evaluacion = Evaluacion.objects.create(
            title="Evaluación Etapa 1 - Validación",
            etapa=1,
            start_time=ahora,
            end_time=ahora + timedelta(days=7),
            duration_minutes=90,
            preguntas_a_mostrar=40,
            anio=anio_activo,
        )
        evaluacion.grupos_participantes.set(grupos)
        self.stdout.write("✅ Evaluación creada y grupos asignados")

        # 5) Generar 40 preguntas simples (aritmética) con 4 opciones
        preguntas_creadas = 0
        for idx in range(40):
            texto, opciones, idx_correcta = self._generar_pregunta_aritmetica(idx + 1)
            pregunta = Pregunta.objects.create(
                evaluacion=evaluacion,
                text=texto,
                puntos=1,
            )
            for j, opcion_texto in enumerate(opciones):
                Opcion.objects.create(
                    pregunta=pregunta,
                    text=opcion_texto,
                    is_correct=(j == idx_correcta),
                )
            preguntas_creadas += 1
        self.stdout.write(f"✅ Preguntas creadas: {preguntas_creadas}")

        # 6) Crear resultados con puntajes para cada participante
        resultados_creados = 0
        for participante in participantes:
            puntos_totales = 10
            # Puntos obtenidos aleatorios entre 2.000 y 9.750 (con pasos de 0.250)
            pasos = random.randint(8, 39)  # 8*0.25=2.0, 39*0.25=9.75
            puntos_obtenidos = round(pasos * 0.25, 3)
            puntaje_porcentaje = (puntos_obtenidos / puntos_totales) * 100
            tiempo_utilizado_min = random.randint(30, 90)

            ResultadoEvaluacion.objects.update_or_create(
                evaluacion=evaluacion,
                participante=participante,
                defaults={
                    'puntaje': puntaje_porcentaje,
                    'tiempo_utilizado': tiempo_utilizado_min,
                    'completada': True,
                    'fecha_fin': timezone.now(),
                    'puntos_obtenidos': puntos_obtenidos,
                    'puntos_totales': puntos_totales,
                    'tiempo_restante': max(0, evaluacion.duration_minutes * 60 - tiempo_utilizado_min * 60),
                }
            )
            resultados_creados += 1

        self.stdout.write(f"✅ Resultados con puntajes creados: {resultados_creados}")

        # Resumen
        self.stdout.write("")
        self.stdout.write("🎉 ¡Proceso completado!")
        self.stdout.write("📊 Resumen:")
        self.stdout.write(f"   - Representantes: {len(representantes)}")
        self.stdout.write(f"   - Grupos: {len(grupos)}")
        self.stdout.write(f"   - Participantes: {len(participantes)}")
        self.stdout.write(f"   - Evaluación: {evaluacion.title}")
        self.stdout.write(f"   - Preguntas creadas: {preguntas_creadas}")
        self.stdout.write(f"   - Resultados creados: {resultados_creados}")

    # ==== Utilidades ====
    def _generar_cedula(self) -> str:
        return ''.join(str(random.randint(0, 9)) for _ in range(10))

    def _generar_telefono(self) -> str:
        return ''.join(str(random.randint(0, 9)) for _ in range(10))

    def _generar_nombres(self) -> str:
        nombres = [
            "Juan", "María", "Carlos", "Ana", "Luis", "Carmen", "Pedro", "Rosa",
            "Miguel", "Isabel", "José", "Patricia", "Fernando", "Lucía", "Roberto",
            "Elena", "Diego", "Sofia", "Andrés", "Valeria", "Ricardo", "Camila",
            "Francisco", "Daniela", "Alejandro", "Gabriela", "Manuel", "Natalia",
            "David", "Andrea", "Jorge", "Paula", "Héctor", "Mariana", "Alberto",
            "Carolina", "Eduardo", "Verónica", "Raúl", "Diana", "Santiago", "Laura"
        ]
        return random.choice(nombres)

    def _generar_apellidos(self) -> str:
        apellidos = [
            "García", "Rodríguez", "González", "Fernández", "López", "Martínez",
            "Sánchez", "Pérez", "Gómez", "Martin", "Jiménez", "Ruiz", "Hernández",
            "Díaz", "Moreno", "Muñoz", "Álvarez", "Romero", "Alonso", "Gutiérrez",
            "Navarro", "Torres", "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez",
            "Serrano", "Blanco", "Suárez", "Molina", "Morales", "Ortega", "Delgado",
            "Castro", "Ortiz", "Rubio", "Marín", "Sanz", "Iglesias", "Medina"
        ]
        return random.choice(apellidos)

    def _generar_email_unico(self, nombre: str, apellido: str, usados: set) -> str:
        dominios = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']

        def _asciiize(token: str) -> str:
            # Normaliza y elimina diacríticos, dejando solo a-z y 0-9
            normalized = unicodedata.normalize('NFKD', token)
            ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
            ascii_text = ascii_text.lower()
            ascii_text = re.sub(r'[^a-z0-9]+', '', ascii_text)
            return ascii_text

        nombre_clean = _asciiize(nombre)
        apellido_clean = _asciiize(apellido)
        if not nombre_clean:
            nombre_clean = 'user'
        if not apellido_clean:
            apellido_clean = 'x'

        while True:
            base = f"{nombre_clean}.{apellido_clean}"
            sufijo = str(random.randint(100, 999))
            correo = f"{base}{sufijo}@{random.choice(dominios)}"
            if correo not in usados:
                usados.add(correo)
                return correo

    def _crear_representante(self) -> Representante:
        nombres_colegios = [
            "Unidad Educativa San José", "Colegio Nacional Mejía", "Instituto Nacional Mejía",
            "Unidad Educativa Manuela Cañizares", "Colegio Técnico Salesiano",
            "Instituto Tecnológico Superior Central Técnico", "Colegio Militar Eloy Alfaro",
            "Unidad Educativa Bilingüe Nuevo Mundo", "Colegio Americano de Quito",
            "Unidad Educativa San Francisco de Sales",
        ]
        correo_institucional = f"info{random.randint(1000, 9999)}@{random.choice(['colegio.edu.ec', 'instituto.edu.ec', 'escuela.edu.ec'])}"
        correo_representante = f"representante{random.randint(1000, 9999)}@{random.choice(['gmail.com', 'hotmail.com'])}"

        representante = Representante.objects.create(
            NombreColegio=random.choice(nombres_colegios),
            DireccionColegio=f"Av. {random.choice(['Amazonas', '6 de Diciembre', '10 de Agosto', 'Naciones Unidas'])} #" + str(random.randint(10, 999)),
            TelefonoInstitucional=self._generar_telefono(),
            CorreoInstitucional=correo_institucional,
            NombresRepresentante=f"{self._generar_nombres()} {self._generar_apellidos()}",
            TelefonoRepresentante=self._generar_telefono(),
            CorreoRepresentante=correo_representante,
        )
        # Ajustar al año activo del sistema
        representante.anio = SystemConfig.get_active_year()
        representante.save(update_fields=["anio"])
        return representante

    def _crear_grupo_participantes(self, representante: Representante, numero_grupo: int, anio: int) -> GrupoParticipantes:
        return GrupoParticipantes.objects.create(
            name=f"Grupo {numero_grupo} - {representante.NombreColegio}",
            representante=representante,
            anio=anio,
        )

    def _crear_participante_unico(self, anio: int) -> Participantes:
        # Garantizar cédula y email únicos a nivel de aplicación antes de delegar al modelo
        while True:
            cedula = self._generar_cedula()
            if not Participantes.objects.filter(cedula=cedula).exists():
                break

        nombre = self._generar_nombres()
        apellido = self._generar_apellidos()
        nombres_completos = f"{nombre} {apellido}"

        # Control de emails únicos para evitar choques entre iteraciones
        if not hasattr(self, "_emails_usados"):
            self._emails_usados = set()
        email = self._generar_email_unico(nombre, apellido, self._emails_usados)

        telefono = self._generar_telefono()
        edad = random.randint(15, 18)

        participante, _password = Participantes.create_participant(
            cedula=cedula,
            NombresCompletos=nombres_completos,
            email=email,
            phone=telefono,
            edad=edad,
        )
        return participante

    def _generar_pregunta_aritmetica(self, numero: int):
        # Genera una pregunta de suma/resta/multiplicación/división simples
        a = random.randint(5, 50)
        b = random.randint(2, 20)
        operador = random.choice(['+', '-', '×', '÷'])
        if operador == '+':
            resultado = a + b
            texto = f"Calcule: {a} + {b} = ?"
            distractores = [resultado + 1, resultado - 1, resultado + 2]
        elif operador == '-':
            resultado = a - b
            texto = f"Calcule: {a} - {b} = ?"
            distractores = [resultado + 2, resultado - 2, resultado + 1]
        elif operador == '×':
            resultado = a * b
            texto = f"Calcule: {a} × {b} = ?"
            distractores = [resultado + a, resultado - b, resultado + b]
        else:
            # División entera segura (forzar múltiplo)
            resultado = a
            dividendo = a * b
            texto = f"Calcule: {dividendo} ÷ {b} = ?"
            distractores = [resultado + 1, resultado - 1, resultado + 2]

        opciones = [str(resultado)] + [str(x) for x in distractores]
        random.shuffle(opciones)
        idx_correcta = opciones.index(str(resultado))
        return texto, opciones, idx_correcta


