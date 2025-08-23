#!/usr/bin/env python
"""
Script para generar 30 participantes de prueba para la Olimpiada de Matemáticas
"""

import os
import sys
import django
from django.utils.crypto import get_random_string
import random
from datetime import datetime
from django.core.management.base import BaseCommand
import unicodedata
import re

from django.contrib.auth.models import User
from quizzes.models import Participantes, Representante, GrupoParticipantes, SystemConfig

class Command(BaseCommand):
    help = 'Genera 30 participantes de prueba con datos aleatorios'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando generación de 30 participantes de prueba...")
        
        # Obtener el año activo del sistema
        anio_activo = SystemConfig.get_active_year()
        self.stdout.write(f"📅 Año activo del sistema: {anio_activo}")
        
        # Limpiar datos existentes del año actual (opcional)
        self.limpiar_datos_existentes(anio_activo)
        
        # Verificar cédulas y emails existentes en BD ANTES de crear nada
        cedulas_existentes = set(Participantes.objects.values_list('cedula', flat=True))
        emails_existentes = set(Participantes.objects.values_list('email', flat=True))
        
        # Obtener correos de representantes existentes
        correos_inst_existentes = set(Representante.objects.values_list('CorreoInstitucional', flat=True))
        correos_repr_existentes = set(Representante.objects.values_list('CorreoRepresentante', flat=True))
        
        # Convertir todos a minúsculas para comparación y filtrar valores nulos/vacíos
        emails_existentes = {email.lower().strip() for email in emails_existentes if email and email.strip()}
        correos_inst_existentes = {email.lower().strip() for email in correos_inst_existentes if email and email.strip()}
        correos_repr_existentes = {email.lower().strip() for email in correos_repr_existentes if email and email.strip()}
        
        # Combinar todos los correos existentes
        todos_correos_existentes = emails_existentes | correos_inst_existentes | correos_repr_existentes
        
        self.stdout.write(f"📧 Correos existentes encontrados: {len(todos_correos_existentes)}")
        if todos_correos_existentes:
            self.stdout.write(f"   Ejemplos: {list(todos_correos_existentes)[:3]}...")
        
        # Crear representantes
        representantes = []
        correos_institucionales_usados = set()
        correos_representante_usados = set()
        
        for i in range(3):  # 3 representantes para distribuir los participantes
            representante = self.crear_representante(anio_activo, correos_institucionales_usados, correos_representante_usados, todos_correos_existentes)
            representantes.append(representante)
            correos_institucionales_usados.add(representante.CorreoInstitucional.lower())
            correos_representante_usados.add(representante.CorreoRepresentante.lower())
            self.stdout.write(f"✅ Representante creado: {representante}")
        
        # Crear grupos
        grupos = []
        for i, representante in enumerate(representantes):
            grupo = self.crear_grupo_participantes(representante, i + 1, anio_activo)
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
                if cedula not in cedulas_generadas and cedula not in cedulas_existentes:
                    cedulas_generadas.add(cedula)
                    break
            
            nombre = self.generar_nombres()
            apellido = self.generar_apellidos()
            nombres_completos = f"{nombre} {apellido}"
            
            # Generar email único
            email = self.generar_email_unico(nombre, apellido, emails_generados, todos_correos_existentes, correos_institucionales_usados, correos_representante_usados)
            emails_generados.add(email.lower())
            
            # Debug: verificar formato del email
            if '@' not in email or '.' not in email.split('@')[1]:
                self.stdout.write(f"⚠️  Email con formato incorrecto generado: '{email}' para {nombre} {apellido}")
                continue
            
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
                
                # Asignar a un grupo de forma balanceada
                grupo = grupos[i % len(grupos)]
                grupo.participantes.add(participante)
                
                participantes_creados += 1
                self.stdout.write(f"✅ Participante {participantes_creados}/30 creado: {nombres_completos} ({cedula}) - Contraseña: {password}")
                
            except Exception as e:
                self.stdout.write(f"❌ Error al crear participante {i+1}: {e}")
                continue
        
        self.stdout.write(f"\n🎉 ¡Proceso completado!")
        self.stdout.write(f"📊 Resumen:")
        self.stdout.write(f"   - Año: {anio_activo}")
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

    def generar_email_unico(self, nombre, apellido, emails_generados, todos_correos_existentes, correos_institucionales_usados, correos_representante_usados):
        """Genera un email único basado en el nombre"""
        dominios = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
        dominio = random.choice(dominios)
        
        # Normalizar nombres para email (quitar acentos y caracteres especiales)
        nombre_limpio = self.normalizar_para_email(nombre)
        apellido_limpio = self.normalizar_para_email(apellido)
        
        # Combinar todos los emails usados (existentes + generados en esta sesión)
        todos_emails_usados = emails_generados | todos_correos_existentes | correos_institucionales_usados | correos_representante_usados
        
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
            if formato.lower() not in todos_emails_usados:
                return formato
        
        # Si todos los formatos están ocupados, agregar un número aleatorio
        return f"{nombre_limpio}.{apellido_limpio}{random.randint(1000, 9999)}@{dominio}"
    
    def normalizar_para_email(self, texto):
        """Normaliza texto para uso en email (quita acentos y caracteres especiales)"""
        # Convertir a minúsculas
        texto = texto.lower()
        
        # Quitar acentos y diacríticos
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(char for char in texto if unicodedata.category(char) != 'Mn')
        
        # Quitar caracteres no alfanuméricos (excepto letras y números)
        texto = re.sub(r'[^a-z0-9]', '', texto)
        
        # Asegurar que no esté vacío
        if not texto:
            texto = f"user{random.randint(100, 999)}"
        
        return texto

    def generar_nombres(self):
        """Lista de nombres ecuatorianos comunes"""
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
        """Lista de apellidos ecuatorianos comunes"""
        apellidos = [
            "Garcia", "Rodriguez", "Gonzalez", "Fernandez", "Lopez", "Martinez",
            "Sanchez", "Perez", "Gomez", "Martin", "Jimenez", "Ruiz", "Hernandez",
            "Diaz", "Moreno", "Munoz", "Alvarez", "Romero", "Alonso", "Gutierrez",
            "Navarro", "Torres", "Dominguez", "Vazquez", "Ramos", "Gil", "Ramirez",
            "Serrano", "Blanco", "Suarez", "Molina", "Morales", "Ortega", "Delgado",
            "Castro", "Ortiz", "Rubio", "Marin", "Sanz", "Iglesias", "Medina"
        ]
        return random.choice(apellidos)

    def limpiar_datos_existentes(self, anio):
        """Limpia datos existentes del año especificado (opcional)"""
        try:
            # Contar datos existentes
            grupos_count = GrupoParticipantes.objects.filter(anio=anio).count()
            representantes_count = Representante.objects.filter(anio=anio).count()
            
            if grupos_count > 0 or representantes_count > 0:
                self.stdout.write(f"⚠️  Datos existentes encontrados para el año {anio}:")
                self.stdout.write(f"   - Grupos: {grupos_count}")
                self.stdout.write(f"   - Representantes: {representantes_count}")
                self.stdout.write("   Los nuevos datos se agregarán sin eliminar los existentes.")
            
        except Exception as e:
            self.stdout.write(f"⚠️  Error al verificar datos existentes: {e}")

    def crear_representante(self, anio, correos_institucionales_usados, correos_representante_usados, todos_correos_existentes):
        """Crea un representante de prueba"""
        nombres_colegios = [
            "Unidad Educativa San José", "Colegio Nacional Mejía", "Instituto Nacional Mejía",
            "Unidad Educativa Manuela Cañizares", "Colegio Técnico Salesiano",
            "Instituto Tecnológico Superior Central Técnico", "Colegio Militar Eloy Alfaro",
            "Unidad Educativa Bilingüe Nuevo Mundo", "Colegio Americano de Quito",
            "Unidad Educativa San Francisco de Sales"
        ]
        
        # Generar correos únicos para representantes
        dominios_institucionales = ['colegio.edu.ec', 'instituto.edu.ec', 'escuela.edu.ec']
        dominios_personales = ['gmail.com', 'hotmail.com', 'yahoo.com']
        
        # Generar correo institucional único
        while True:
            correo_institucional = f"info{random.randint(100, 999)}@{random.choice(dominios_institucionales)}"
            if (correo_institucional.lower() not in correos_institucionales_usados and 
                correo_institucional.lower() not in todos_correos_existentes):
                break
                
        # Generar correo del representante único
        while True:
            correo_representante = f"representante{random.randint(100, 999)}@{random.choice(dominios_personales)}"
            if (correo_representante.lower() not in correos_representante_usados and 
                correo_representante.lower() not in todos_correos_existentes and
                correo_representante.lower() != correo_institucional.lower()):
                break
        
        representante = Representante.objects.create(
            NombreColegio=random.choice(nombres_colegios),
            DireccionColegio=f"Av. {random.choice(['Amazonas', '6 de Diciembre', '10 de Agosto', 'Naciones Unidas'])} #{random.randint(100, 999)}",
            TelefonoInstitucional=self.generar_telefono(),
            CorreoInstitucional=correo_institucional,
            NombresRepresentante=f"{self.generar_nombres()} {self.generar_apellidos()}",
            TelefonoRepresentante=self.generar_telefono(),
            CorreoRepresentante=correo_representante,
            anio=anio  # Agregar el año
        )
        return representante

    def crear_grupo_participantes(self, representante, numero_grupo, anio):
        """Crea un grupo de participantes"""
        grupo = GrupoParticipantes.objects.create(
            name=f"Grupo {numero_grupo} - {representante.NombreColegio}",
            representante=representante,
            anio=anio  # Agregar el año
        )
        return grupo 