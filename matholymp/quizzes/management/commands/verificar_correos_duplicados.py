#!/usr/bin/env python
"""
Comando para verificar correos duplicados en la base de datos
"""

import os
import sys
import django
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db import transaction
from quizzes.models import Participantes, Representante
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Verifica correos duplicados en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Intenta corregir automáticamente los correos duplicados',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula las correcciones sin aplicarlas realmente',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando correos duplicados en la base de datos...")
        
        # Verificar duplicados dentro de Participantes
        self.stdout.write("\n📋 Verificando duplicados en Participantes:")
        participantes_duplicados = self.verificar_duplicados_participantes()
        
        # Verificar duplicados dentro de Representante
        self.stdout.write("\n📋 Verificando duplicados en Representantes:")
        representantes_duplicados = self.verificar_duplicados_representantes()
        
        # Verificar conflictos entre Participantes y Representantes
        self.stdout.write("\n📋 Verificando conflictos entre Participantes y Representantes:")
        conflictos = self.verificar_conflictos_cruzados()
        
        # Verificar conflictos con User
        self.stdout.write("\n📋 Verificando conflictos con usuarios del sistema:")
        conflictos_user = self.verificar_conflictos_con_user()
        
        # Resumen
        total_duplicados = (len(participantes_duplicados) + len(representantes_duplicados) + 
                           len(conflictos) + len(conflictos_user))
        
        if total_duplicados == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ ¡No se encontraron correos duplicados!"))
        else:
            self.stdout.write(self.style.WARNING(f"\n⚠️  Se encontraron {total_duplicados} problemas con correos duplicados"))
            
            if options['fix']:
                self.stdout.write("\n🔧 Intentando corregir automáticamente...")
                if options['dry_run']:
                    self.stdout.write("🔍 Modo DRY-RUN: No se aplicarán cambios reales")
                self.corregir_duplicados(
                    participantes_duplicados, 
                    representantes_duplicados, 
                    conflictos, 
                    conflictos_user,
                    dry_run=options['dry_run']
                )

    def verificar_duplicados_participantes(self):
        """Verifica correos duplicados dentro de Participantes"""
        duplicados = []
        
        # Obtener todos los correos de participantes
        participantes = Participantes.objects.all()
        emails = {}
        
        for participante in participantes:
            email = participante.email.lower().strip()
            if email in emails:
                emails[email].append(participante)
            else:
                emails[email] = [participante]
        
        # Encontrar duplicados
        for email, lista_participantes in emails.items():
            if len(lista_participantes) > 1:
                duplicados.append({
                    'email': email,
                    'participantes': lista_participantes,
                    'tipo': 'participantes'
                })
                self.stdout.write(f"  ❌ Correo duplicado: {email} ({len(lista_participantes)} participantes)")
                for p in lista_participantes:
                    self.stdout.write(f"    - {p.NombresCompletos} (ID: {p.id})")
        
        return duplicados

    def verificar_duplicados_representantes(self):
        """Verifica correos duplicados dentro de Representante"""
        duplicados = []
        
        # Verificar correos institucionales duplicados
        representantes = Representante.objects.all()
        emails_institucionales = {}
        emails_representantes = {}
        
        for representante in representantes:
            # Correo institucional
            email_inst = representante.CorreoInstitucional.lower().strip()
            if email_inst in emails_institucionales:
                emails_institucionales[email_inst].append(representante)
            else:
                emails_institucionales[email_inst] = [representante]
            
            # Correo del representante
            email_rep = representante.CorreoRepresentante.lower().strip()
            if email_rep in emails_representantes:
                emails_representantes[email_rep].append(representante)
            else:
                emails_representantes[email_rep] = [representante]
        
        # Encontrar duplicados institucionales
        for email, lista_representantes in emails_institucionales.items():
            if len(lista_representantes) > 1:
                duplicados.append({
                    'email': email,
                    'representantes': lista_representantes,
                    'tipo': 'institucional'
                })
                self.stdout.write(f"  ❌ Correo institucional duplicado: {email} ({len(lista_representantes)} representantes)")
                for r in lista_representantes:
                    self.stdout.write(f"    - {r.NombresRepresentante} - {r.NombreColegio} (ID: {r.id})")
        
        # Encontrar duplicados de representantes
        for email, lista_representantes in emails_representantes.items():
            if len(lista_representantes) > 1:
                duplicados.append({
                    'email': email,
                    'representantes': lista_representantes,
                    'tipo': 'representante'
                })
                self.stdout.write(f"  ❌ Correo de representante duplicado: {email} ({len(lista_representantes)} representantes)")
                for r in lista_representantes:
                    self.stdout.write(f"    - {r.NombresRepresentante} - {r.NombreColegio} (ID: {r.id})")
        
        return duplicados

    def verificar_conflictos_cruzados(self):
        """Verifica conflictos entre Participantes y Representantes"""
        conflictos = []
        
        # Obtener todos los correos de participantes
        emails_participantes = set()
        for participante in Participantes.objects.all():
            emails_participantes.add(participante.email.lower().strip())
        
        # Verificar conflictos con representantes
        for representante in Representante.objects.all():
            email_inst = representante.CorreoInstitucional.lower().strip()
            email_rep = representante.CorreoRepresentante.lower().strip()
            
            if email_inst in emails_participantes:
                participante_conflicto = Participantes.objects.filter(email__iexact=email_inst).first()
                conflictos.append({
                    'email': email_inst,
                    'tipo': 'institucional_participante',
                    'representante': representante,
                    'participante': participante_conflicto
                })
                self.stdout.write(f"  ❌ Conflicto: Correo institucional {email_inst} usado por participante {participante_conflicto.NombresCompletos}")
            
            if email_rep in emails_participantes:
                participante_conflicto = Participantes.objects.filter(email__iexact=email_rep).first()
                conflictos.append({
                    'email': email_rep,
                    'tipo': 'representante_participante',
                    'representante': representante,
                    'participante': participante_conflicto
                })
                self.stdout.write(f"  ❌ Conflicto: Correo de representante {email_rep} usado por participante {participante_conflicto.NombresCompletos}")
        
        return conflictos

    def verificar_conflictos_con_user(self):
        """Verifica conflictos con usuarios del sistema"""
        conflictos = []
        
        # Verificar conflictos entre User y Participantes
        for user in User.objects.all():
            if user.email:
                email_user = user.email.lower().strip()
                
                # Verificar con participantes
                participante_conflicto = Participantes.objects.filter(email__iexact=email_user).first()
                if participante_conflicto:
                    conflictos.append({
                        'email': email_user,
                        'tipo': 'user_participante',
                        'user': user,
                        'participante': participante_conflicto
                    })
                    self.stdout.write(f"  ❌ Conflicto: Correo de usuario {email_user} usado por participante {participante_conflicto.NombresCompletos}")
                
                # Verificar con representantes
                representante_conflicto = Representante.objects.filter(
                    Q(CorreoInstitucional__iexact=email_user) | Q(CorreoRepresentante__iexact=email_user)
                ).first()
                if representante_conflicto:
                    conflictos.append({
                        'email': email_user,
                        'tipo': 'user_representante',
                        'user': user,
                        'representante': representante_conflicto
                    })
                    self.stdout.write(f"  ❌ Conflicto: Correo de usuario {email_user} usado por representante {representante_conflicto.NombresRepresentante}")
        
        return conflictos

    def corregir_duplicados(self, participantes_duplicados, representantes_duplicados, conflictos, conflictos_user, dry_run=False):
        """Intenta corregir automáticamente los duplicados"""
        
        if dry_run:
            self.stdout.write("🔍 MODO DRY-RUN: Simulando correcciones...")
        
        # Corregir duplicados de participantes
        for duplicado in participantes_duplicados:
            self.corregir_duplicados_participantes(duplicado, dry_run)
        
        # Corregir duplicados de representantes
        for duplicado in representantes_duplicados:
            self.corregir_duplicados_representantes(duplicado, dry_run)
        
        # Corregir conflictos cruzados
        for conflicto in conflictos:
            self.corregir_conflicto_cruzado(conflicto, dry_run)
        
        # Corregir conflictos con User
        for conflicto in conflictos_user:
            self.corregir_conflicto_user(conflicto, dry_run)
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS("✅ Correcciones aplicadas. Ejecute el comando nuevamente para verificar."))
        else:
            self.stdout.write(self.style.WARNING("🔍 Simulación completada. Ejecute sin --dry-run para aplicar cambios reales."))

    def corregir_duplicados_participantes(self, duplicado, dry_run=False):
        """Corrige duplicados de participantes"""
        participantes = duplicado['participantes']
        email_base = duplicado['email']
        
        # Mantener el primer participante y modificar los demás
        for i, participante in enumerate(participantes[1:], 1):
            nuevo_email = f"{email_base.split('@')[0]}+{i}@{email_base.split('@')[1]}"
            
            if dry_run:
                self.stdout.write(f"  🔍 Simular: Cambiar correo de {participante.NombresCompletos} de {participante.email} a {nuevo_email}")
            else:
                try:
                    with transaction.atomic():
                        participante.email = nuevo_email
                        participante.user.email = nuevo_email
                        participante.full_clean()
                        participante.save()
                        participante.user.save()
                    self.stdout.write(f"  ✅ Corregido: {participante.NombresCompletos} -> {nuevo_email}")
                except Exception as e:
                    self.stdout.write(f"  ❌ Error corrigiendo {participante.NombresCompletos}: {e}")

    def corregir_duplicados_representantes(self, duplicado, dry_run=False):
        """Corrige duplicados de representantes"""
        representantes = duplicado['representantes']
        email_base = duplicado['email']
        tipo = duplicado['tipo']
        
        # Mantener el primer representante y modificar los demás
        for i, representante in enumerate(representantes[1:], 1):
            nuevo_email = f"{email_base.split('@')[0]}+{i}@{email_base.split('@')[1]}"
            
            if dry_run:
                self.stdout.write(f"  🔍 Simular: Cambiar correo {tipo} de {representante.NombresRepresentante} de {getattr(representante, f'Correo{tipo.capitalize()}')} a {nuevo_email}")
            else:
                try:
                    with transaction.atomic():
                        if tipo == 'institucional':
                            representante.CorreoInstitucional = nuevo_email
                        else:
                            representante.CorreoRepresentante = nuevo_email
                        representante.full_clean()
                        representante.save()
                    self.stdout.write(f"  ✅ Corregido: {representante.NombresRepresentante} -> {nuevo_email}")
                except Exception as e:
                    self.stdout.write(f"  ❌ Error corrigiendo {representante.NombresRepresentante}: {e}")

    def corregir_conflicto_cruzado(self, conflicto, dry_run=False):
        """Corrige conflictos cruzados entre participantes y representantes"""
        email = conflicto['email']
        tipo = conflicto['tipo']
        
        if tipo == 'institucional_participante':
            representante = conflicto['representante']
            participante = conflicto['participante']
            
            # Modificar el correo del representante
            nuevo_email = f"{email.split('@')[0]}+inst@{email.split('@')[1]}"
            
            if dry_run:
                self.stdout.write(f"  🔍 Simular: Cambiar correo institucional de {representante.NombresRepresentante} de {email} a {nuevo_email}")
            else:
                try:
                    with transaction.atomic():
                        representante.CorreoInstitucional = nuevo_email
                        representante.full_clean()
                        representante.save()
                    self.stdout.write(f"  ✅ Corregido: {representante.NombresRepresentante} -> {nuevo_email}")
                except Exception as e:
                    self.stdout.write(f"  ❌ Error corrigiendo {representante.NombresRepresentante}: {e}")
        
        elif tipo == 'representante_participante':
            representante = conflicto['representante']
            participante = conflicto['participante']
            
            # Modificar el correo del representante
            nuevo_email = f"{email.split('@')[0]}+rep@{email.split('@')[1]}"
            
            if dry_run:
                self.stdout.write(f"  🔍 Simular: Cambiar correo de representante de {representante.NombresRepresentante} de {email} a {nuevo_email}")
            else:
                try:
                    with transaction.atomic():
                        representante.CorreoRepresentante = nuevo_email
                        representante.full_clean()
                        representante.save()
                    self.stdout.write(f"  ✅ Corregido: {representante.NombresRepresentante} -> {nuevo_email}")
                except Exception as e:
                    self.stdout.write(f"  ❌ Error corrigiendo {representante.NombresRepresentante}: {e}")

    def corregir_conflicto_user(self, conflicto, dry_run=False):
        """Corrige conflictos con usuarios del sistema"""
        email = conflicto['email']
        tipo = conflicto['tipo']
        user = conflicto['user']
        
        if tipo == 'user_participante':
            participante = conflicto['participante']
            
            # Modificar el correo del participante
            nuevo_email = f"{email.split('@')[0]}+part@{email.split('@')[1]}"
            
            if dry_run:
                self.stdout.write(f"  🔍 Simular: Cambiar correo de participante {participante.NombresCompletos} de {email} a {nuevo_email}")
            else:
                try:
                    with transaction.atomic():
                        participante.email = nuevo_email
                        participante.user.email = nuevo_email
                        participante.full_clean()
                        participante.save()
                        participante.user.save()
                    self.stdout.write(f"  ✅ Corregido: {participante.NombresCompletos} -> {nuevo_email}")
                except Exception as e:
                    self.stdout.write(f"  ❌ Error corrigiendo {participante.NombresCompletos}: {e}")
        
        elif tipo == 'user_representante':
            representante = conflicto['representante']
            
            # Determinar qué correo del representante está en conflicto
            if representante.CorreoInstitucional.lower().strip() == email:
                nuevo_email = f"{email.split('@')[0]}+inst@{email.split('@')[1]}"
                campo = 'CorreoInstitucional'
            else:
                nuevo_email = f"{email.split('@')[0]}+rep@{email.split('@')[1]}"
                campo = 'CorreoRepresentante'
            
            if dry_run:
                self.stdout.write(f"  🔍 Simular: Cambiar {campo} de {representante.NombresRepresentante} de {email} a {nuevo_email}")
            else:
                try:
                    with transaction.atomic():
                        setattr(representante, campo, nuevo_email)
                        representante.full_clean()
                        representante.save()
                    self.stdout.write(f"  ✅ Corregido: {representante.NombresRepresentante} -> {nuevo_email}")
                except Exception as e:
                    self.stdout.write(f"  ❌ Error corrigiendo {representante.NombresRepresentante}: {e}") 