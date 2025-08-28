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
from quizzes.models import Participantes, Representante, GrupoParticipantes, SystemConfig

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
        emails_generados = set()
        
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
            
            # Generar email único
            email = self.generar_email_unico(nombre, apellido, emails_generados)
            emails_generados.add(email.lower())
            
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

    def generar_email_unico(self, nombre, apellido, emails_existentes):
        """Genera un email único basado en el nombre"""
        dominios = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
        dominio = random.choice(dominios)
        
        # Limpiar nombres de caracteres especiales y acentos
        nombre_limpio = self.limpiar_para_email(nombre)
        apellido_limpio = self.limpiar_para_email(apellido)
        
        # Diferentes formatos de email para evitar duplicados
        formatos = [
            f"{nombre_limpio}.{apellido_limpio}@{dominio}",
            f"{nombre_limpio}{apellido_limpio}@{dominio}",
            f"{nombre_limpio}_{apellido_limpio}@{dominio}",
            f"{nombre_limpio}{random.randint(100, 999)}@{dominio}",
            f"{nombre_limpio}.{apellido_limpio}{random.randint(10, 99)}@{dominio}",
        ]
        
        # Probar cada formato hasta encontrar uno único
        for formato in formatos:
            if formato.lower() not in emails_existentes:
                return formato
        
        # Si todos los formatos están ocupados, agregar un número aleatorio
        return f"{nombre_limpio}.{apellido_limpio}{random.randint(1000, 9999)}@{dominio}"

    def limpiar_para_email(self, texto):
        """Limpia texto removiendo acentos y caracteres especiales para emails"""
        # Diccionario de reemplazos para caracteres con acentos
        reemplazos = {
            'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ã': 'a',
            'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e',
            'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i',
            'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'õ': 'o',
            'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u',
            'ñ': 'n',
            'ç': 'c',
            'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A', 'Ã': 'A',
            'É': 'E', 'È': 'E', 'Ë': 'E', 'Ê': 'E',
            'Í': 'I', 'Ì': 'I', 'Ï': 'I', 'Î': 'I',
            'Ó': 'O', 'Ò': 'O', 'Ö': 'O', 'Ô': 'O', 'Õ': 'O',
            'Ú': 'U', 'Ù': 'U', 'Ü': 'U', 'Û': 'U',
            'Ñ': 'N',
            'Ç': 'C'
        }
        
        # Aplicar reemplazos
        texto_limpio = texto
        for caracter_original, caracter_reemplazo in reemplazos.items():
            texto_limpio = texto_limpio.replace(caracter_original, caracter_reemplazo)
        
        # Convertir a minúsculas y quitar espacios
        texto_limpio = texto_limpio.lower().strip()
        
        # Quitar cualquier caracter que no sea letra o número
        texto_limpio = ''.join(c for c in texto_limpio if c.isalnum())
        
        # Si el texto quedó vacío, generar un nombre genérico
        if not texto_limpio:
            texto_limpio = f"user{random.randint(100, 999)}"
        
        return texto_limpio

    def generar_nombres(self):
        """Lista de nombres ecuatorianos comunes sin caracteres especiales"""
        nombres = [
            "Juan", "Maria", "Carlos", "Ana", "Luis", "Carmen", "Pedro", "Rosa",
            "Miguel", "Isabel", "Jose", "Patricia", "Fernando", "Lucia", "Roberto",
            "Elena", "Diego", "Sofia", "Andres", "Valeria", "Ricardo", "Camila",
            "Francisco", "Daniela", "Alejandro", "Gabriela", "Manuel", "Natalia",
            "David", "Andrea", "Jorge", "Paula", "Hector", "Mariana", "Alberto",
            "Carolina", "Eduardo", "Veronica", "Raul", "Diana", "Santiago", "Laura"
        ]
        return random.choice(nombres)

    def generar_apellidos(self):
        """Lista de apellidos ecuatorianos comunes sin caracteres especiales"""
        apellidos = [
            "Garcia", "Rodriguez", "Gonzalez", "Fernandez", "Lopez", "Martinez",
            "Sanchez", "Perez", "Gomez", "Martin", "Jimenez", "Ruiz", "Hernandez",
            "Diaz", "Moreno", "Munoz", "Alvarez", "Romero", "Alonso", "Gutierrez",
            "Navarro", "Torres", "Dominguez", "Vazquez", "Ramos", "Gil", "Ramirez",
            "Serrano", "Blanco", "Suarez", "Molina", "Morales", "Ortega", "Delgado",
            "Castro", "Ortiz", "Rubio", "Marin", "Sanz", "Iglesias", "Medina"
        ]
        return random.choice(apellidos)

    def crear_representante(self):
        """Crea un representante de prueba"""
        nombres_colegios = [
            "Unidad Educativa San Jose", "Colegio Nacional Mejia", "Instituto Nacional Mejia",
            "Unidad Educativa Manuela Canizares", "Colegio Tecnico Salesiano",
            "Instituto Tecnologico Superior Central Tecnico", "Colegio Militar Eloy Alfaro",
            "Unidad Educativa Bilingue Nuevo Mundo", "Colegio Americano de Quito",
            "Unidad Educativa San Francisco de Sales"
        ]
        
        # Generar correos únicos para representantes sin caracteres especiales
        numero_aleatorio = random.randint(1000, 9999)
        correo_institucional = f"info{numero_aleatorio}@colegio.edu.ec"
        correo_representante = f"representante{numero_aleatorio}@gmail.com"
        
        # Generar nombres sin caracteres especiales para el representante
        nombres_representantes = [
            "Ana Rodriguez", "Carlos Martinez", "Maria Gonzalez", "Luis Fernandez",
            "Carmen Lopez", "Pedro Sanchez", "Rosa Perez", "Miguel Gomez",
            "Isabel Martin", "Jose Jimenez", "Patricia Ruiz", "Fernando Hernandez"
        ]
        
        representante = Representante.objects.create(
            NombreColegio=random.choice(nombres_colegios),
            DireccionColegio=f"Av. {random.choice(['Amazonas', '6 de Diciembre', '10 de Agosto', 'Naciones Unidas'])} #123",
            TelefonoInstitucional=self.generar_telefono(),
            CorreoInstitucional=correo_institucional,
            NombresRepresentante=random.choice(nombres_representantes),
            TelefonoRepresentante=self.generar_telefono(),
            CorreoRepresentante=correo_representante,
            anio=SystemConfig.get_active_year()  # Usar el año activo del sistema
        )
        return representante

    def crear_grupo_participantes(self, representante, numero_grupo):
        """Crea un grupo de participantes"""
        grupo = GrupoParticipantes.objects.create(
            name=f"Grupo {numero_grupo} - {representante.NombreColegio}",
            representante=representante,
            anio=SystemConfig.get_active_year()  # Usar el año activo del sistema
        )
        return grupo 