#!/usr/bin/env python
"""
Script para borrar TODOS los participantes del sistema
ADVERTENCIA: Este script es DESTRUCTIVO y eliminará todos los participantes registrados
"""

import os
import sys
import django
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from quizzes.models import (
    Participantes, ResultadoEvaluacion, GrupoParticipantes,
    UserProfile
)

class Command(BaseCommand):
    help = 'Elimina TODOS los participantes del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ejecutar sin confirmación (PELIGROSO)',
        )
        parser.add_argument(
            '--keep-users',
            action='store_true',
            help='Mantener los usuarios de Django, solo eliminar los perfiles de Participantes',
        )

    def handle(self, *args, **options):
        self.stdout.write("🚨 SCRIPT DESTRUCTIVO: BORRAR TODOS LOS PARTICIPANTES")
        self.stdout.write("=" * 60)
        
        if not options['force']:
            if not self.confirmar_eliminacion():
                self.stdout.write("❌ Operación cancelada por el usuario")
                return
        
        try:
            self.borrar_participantes(keep_users=options['keep_users'])
        except Exception as e:
            self.stdout.write(f"❌ Error durante la eliminación: {e}")
            sys.exit(1)

    def confirmar_eliminacion(self):
        """Solicita confirmación múltiple antes de proceder"""
        # Contar participantes actuales
        total_participantes = Participantes.objects.count()
        
        if total_participantes == 0:
            self.stdout.write("ℹ️  No hay participantes registrados en el sistema.")
            return False
        
        self.stdout.write("⚠️  ADVERTENCIA CRÍTICA ⚠️")
        self.stdout.write("=" * 30)
        self.stdout.write(f"📊 Total de participantes a eliminar: {total_participantes}")
        self.stdout.write("")
        self.stdout.write("🔥 ESTA ACCIÓN ES IRREVERSIBLE")
        self.stdout.write("📋 Se eliminarán:")
        self.stdout.write("   ❌ Todos los registros de Participantes")
        self.stdout.write("   ❌ Todos los ResultadoEvaluacion asociados")
        self.stdout.write("   ❌ Relaciones con GrupoParticipantes")
        self.stdout.write("   ❌ Perfiles de usuario asociados")
        self.stdout.write("   ❌ Usuarios de Django asociados (por defecto)")
        self.stdout.write("")
        self.stdout.write("💡 Tip: Use --keep-users para mantener los usuarios de Django")
        self.stdout.write("")
        
        # Primera confirmación
        respuesta1 = input("¿Está ABSOLUTAMENTE seguro de que desea continuar? (escriba 'SI' en mayúsculas): ")
        if respuesta1 != 'SI':
            return False
        
        # Segunda confirmación
        self.stdout.write("")
        self.stdout.write("🔴 ÚLTIMA ADVERTENCIA")
        respuesta2 = input(f"Confirme escribiendo 'ELIMINAR {total_participantes} PARTICIPANTES': ")
        if respuesta2 != f'ELIMINAR {total_participantes} PARTICIPANTES':
            return False
        
        return True

    def borrar_participantes(self, keep_users=False):
        """Elimina todos los participantes y datos relacionados"""
        self.stdout.write("🚀 Iniciando proceso de eliminación...")
        
        with transaction.atomic():
            # 1. Contar elementos antes de la eliminación
            participantes = Participantes.objects.all()
            total_participantes = participantes.count()
            
            if total_participantes == 0:
                self.stdout.write("ℹ️  No hay participantes para eliminar.")
                return
            
            # Contar elementos relacionados
            total_resultados = ResultadoEvaluacion.objects.filter(
                participante__in=participantes
            ).count()
            
            # Contar usuarios asociados
            users_participantes = User.objects.filter(
                participantes__isnull=False
            ).distinct()
            total_users = users_participantes.count()
            
            self.stdout.write(f"📊 Estadísticas antes de la eliminación:")
            self.stdout.write(f"   👥 Participantes: {total_participantes}")
            self.stdout.write(f"   📝 Resultados de evaluación: {total_resultados}")
            self.stdout.write(f"   👤 Usuarios asociados: {total_users}")
            self.stdout.write("")
            
            # 2. Eliminar resultados de evaluación
            self.stdout.write("🗑️  Eliminando resultados de evaluación...")
            ResultadoEvaluacion.objects.filter(
                participante__in=participantes
            ).delete()
            self.stdout.write(f"   ✅ {total_resultados} resultados eliminados")
            
            # 3. Remover participantes de grupos
            self.stdout.write("🗑️  Removiendo participantes de grupos...")
            grupos_afectados = 0
            for grupo in GrupoParticipantes.objects.all():
                count_before = grupo.participantes.count()
                grupo.participantes.clear()
                if count_before > 0:
                    grupos_afectados += 1
            self.stdout.write(f"   ✅ {grupos_afectados} grupos actualizados")
            
            # 4. Eliminar perfiles de usuario asociados
            self.stdout.write("🗑️  Eliminando perfiles de usuario...")
            user_profiles_eliminados = 0
            for participante in participantes:
                try:
                    if hasattr(participante.user, 'userprofile'):
                        participante.user.userprofile.delete()
                        user_profiles_eliminados += 1
                except Exception as e:
                    self.stdout.write(f"   ⚠️  Error eliminando perfil: {e}")
            self.stdout.write(f"   ✅ {user_profiles_eliminados} perfiles de usuario eliminados")
            
            # 5. Eliminar registros de Participantes
            self.stdout.write("🗑️  Eliminando registros de Participantes...")
            participantes.delete()
            self.stdout.write(f"   ✅ {total_participantes} participantes eliminados")
            
            # 6. Eliminar usuarios de Django (opcional)
            if not keep_users:
                self.stdout.write("🗑️  Eliminando usuarios de Django asociados...")
                users_eliminados = 0
                for user in users_participantes:
                    try:
                        # Verificar que no sea superuser o staff
                        if not user.is_superuser and not user.is_staff:
                            user.delete()
                            users_eliminados += 1
                        else:
                            self.stdout.write(f"   ⚠️  Preservando usuario staff/superuser: {user.username}")
                    except Exception as e:
                        self.stdout.write(f"   ⚠️  Error eliminando usuario {user.username}: {e}")
                self.stdout.write(f"   ✅ {users_eliminados} usuarios eliminados")
            else:
                self.stdout.write("   ℹ️  Usuarios de Django preservados (--keep-users)")
            
            self.stdout.write("")
            self.stdout.write("✅ PROCESO COMPLETADO EXITOSAMENTE")
            self.stdout.write("=" * 50)
            self.stdout.write("📊 Resumen de eliminación:")
            self.stdout.write(f"   👥 Participantes eliminados: {total_participantes}")
            self.stdout.write(f"   📝 Resultados eliminados: {total_resultados}")
            self.stdout.write(f"   🏢 Grupos actualizados: {grupos_afectados}")
            self.stdout.write(f"   👤 Perfiles eliminados: {user_profiles_eliminados}")
            if not keep_users:
                self.stdout.write(f"   🔑 Usuarios eliminados: {users_eliminados}")
            self.stdout.write("")
            self.stdout.write("🎯 La base de datos ha sido limpiada de participantes.")
            
            # Verificación final
            participantes_restantes = Participantes.objects.count()
            if participantes_restantes == 0:
                self.stdout.write("✅ Verificación: No quedan participantes en la base de datos")
            else:
                self.stdout.write(f"⚠️  Advertencia: Aún quedan {participantes_restantes} participantes")
