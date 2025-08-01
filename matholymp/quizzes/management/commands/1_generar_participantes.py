#!/usr/bin/env python
"""
Script para generar 30 participantes de prueba para la Olimpiada de Matemáticas
"""

import os
import sys
import django
from django.utils.crypto import get_random_string
import random
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User
from quizzes.models import Participantes, Representante, GrupoParticipantes

class Command(BaseCommand):
    help = 'Genera 30 participantes de prueba con datos aleatorios'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando generación de 30 participantes de prueba...")
        
        # Crear representantes
        representantes = []
        for i in range(3):  # 3 representantes para distribuir los participantes
            representante = self.crear_representante()
            representantes.append(representante)
            self.stdout.write(f"✅ Representante creado: {representante}")
        
        # Crear grupos
        grupos = []
        for i, representante in enumerate(representantes):
            grupo = self.crear_grupo_participantes(representante, i + 1)
            grupos.append(grupo)
            self.stdout.write(f"✅ Grupo creado: {grupo}")
        
        # Generar participantes
        participantes_creados = 0
        cedulas_generadas = set()
        
        for i in range(30):
            # Generar datos únicos
            while True:
                cedula = self.generar_cedula()
                if cedula not in cedulas_generadas:
                    cedulas_generadas.add(cedula)
                    break
            
            nombre = self.generar_nombres()
            apellido = self.generar_apellidos()
            nombres_completos = f"{nombre} {apellido}"
            email = self.generar_email(nombre, apellido)
            telefono = self.generar_telefono()
            edad = random.randint(15, 18)  # Edad típica para olimpiadas de matemáticas
            
            try:
                # Crear participante usando el método estático
                participante, password = Participantes.create_participant(
                    cedula=cedula,
                    NombresCompletos=nombres_completos,
                    email=email,
                    phone=telefono,
                    edad=edad
                )
                
                # Asignar a un grupo
                grupo = grupos[i % len(grupos)]
                grupo.participantes.add(participante)
                
                participantes_creados += 1
                self.stdout.write(f"✅ Participante {participantes_creados}/30 creado: {nombres_completos} ({cedula}) - Contraseña: {password}")
                
            except Exception as e:
                self.stdout.write(f"❌ Error al crear participante {i+1}: {e}")
                continue
        
        self.stdout.write(f"\n🎉 ¡Proceso completado!")
        self.stdout.write(f"📊 Resumen:")
        self.stdout.write(f"   - Participantes creados: {participantes_creados}")
        self.stdout.write(f"   - Representantes creados: {len(representantes)}")
        self.stdout.write(f"   - Grupos creados: {len(grupos)}")
        
        # Mostrar información de los grupos
        self.stdout.write(f"\n📋 Distribución por grupos:")
        for grupo in grupos:
            count = grupo.participantes.count()
            self.stdout.write(f"   - {grupo.name}: {count} participantes")

    def generar_cedula(self):
        """Genera una cédula ecuatoriana válida de 10 dígitos"""
        return ''.join([str(random.randint(0, 9)) for _ in range(10)])

    def generar_telefono(self):
        """Genera un número de teléfono ecuatoriano válido"""
        return ''.join([str(random.randint(0, 9)) for _ in range(10)])

    def generar_email(self, nombre, apellido):
        """Genera un email basado en el nombre"""
        dominios = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
        dominio = random.choice(dominios)
        return f"{nombre.lower()}.{apellido.lower()}@{dominio}"

    def generar_nombres(self):
        """Lista de nombres ecuatorianos comunes"""
        nombres = [
            "Juan", "María", "Carlos", "Ana", "Luis", "Carmen", "Pedro", "Rosa",
            "Miguel", "Isabel", "José", "Patricia", "Fernando", "Lucía", "Roberto",
            "Elena", "Diego", "Sofia", "Andrés", "Valeria", "Ricardo", "Camila",
            "Francisco", "Daniela", "Alejandro", "Gabriela", "Manuel", "Natalia",
            "David", "Andrea", "Jorge", "Paula", "Héctor", "Mariana", "Alberto",
            "Carolina", "Eduardo", "Verónica", "Raúl", "Diana", "Santiago", "Laura"
        ]
        return random.choice(nombres)

    def generar_apellidos(self):
        """Lista de apellidos ecuatorianos comunes"""
        apellidos = [
            "García", "Rodríguez", "González", "Fernández", "López", "Martínez",
            "Sánchez", "Pérez", "Gómez", "Martin", "Jiménez", "Ruiz", "Hernández",
            "Díaz", "Moreno", "Muñoz", "Álvarez", "Romero", "Alonso", "Gutiérrez",
            "Navarro", "Torres", "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez",
            "Serrano", "Blanco", "Suárez", "Molina", "Morales", "Ortega", "Delgado",
            "Castro", "Ortiz", "Rubio", "Marín", "Sanz", "Iglesias", "Medina"
        ]
        return random.choice(apellidos)

    def crear_representante(self):
        """Crea un representante de prueba"""
        nombres_colegios = [
            "Unidad Educativa San José", "Colegio Nacional Mejía", "Instituto Nacional Mejía",
            "Unidad Educativa Manuela Cañizares", "Colegio Técnico Salesiano",
            "Instituto Tecnológico Superior Central Técnico", "Colegio Militar Eloy Alfaro",
            "Unidad Educativa Bilingüe Nuevo Mundo", "Colegio Americano de Quito",
            "Unidad Educativa San Francisco de Sales"
        ]
        
        representante = Representante.objects.create(
            NombreColegio=random.choice(nombres_colegios),
            DireccionColegio=f"Av. {random.choice(['Amazonas', '6 de Diciembre', '10 de Agosto', 'Naciones Unidas'])} #123",
            TelefonoInstitucional=self.generar_telefono(),
            CorreoInstitucional=f"info@{random.choice(['colegio.edu.ec', 'instituto.edu.ec', 'escuela.edu.ec'])}",
            NombresRepresentante=f"{self.generar_nombres()} {self.generar_apellidos()}",
            TelefonoRepresentante=self.generar_telefono(),
            CorreoRepresentante=f"representante@{random.choice(['gmail.com', 'hotmail.com'])}"
        )
        return representante

    def crear_grupo_participantes(self, representante, numero_grupo):
        """Crea un grupo de participantes"""
        grupo = GrupoParticipantes.objects.create(
            name=f"Grupo {numero_grupo} - {representante.NombreColegio}",
            representante=representante
        )
        return grupo 