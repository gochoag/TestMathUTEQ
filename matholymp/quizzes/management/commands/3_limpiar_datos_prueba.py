#!/usr/bin/env python
"""
Script para limpiar todos los datos de prueba del sistema
Borra participantes, evaluaciones, preguntas, opciones, grupos y representantes
"""

import os
import sys
import django
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User
from quizzes.models import (
    Participantes, Evaluacion, Pregunta, Opcion, 
    GrupoParticipantes, Representante, ResultadoEvaluacion,
    AdminProfile, UserProfile
)

class Command(BaseCommand):
    help = 'Elimina todos los datos de prueba del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ejecutar sin confirmación',
        )

    def handle(self, *args, **options):
        self.stdout.write("🧹 Script de Limpieza de Datos de Prueba")
        self.stdout.write("=" * 50)
        
        if not options['force']:
            if not self.confirmar_limpieza():
                self.stdout.write("❌ Operación cancelada por el usuario")
                return
        
        try:
            self.limpiar_datos_prueba()
        except Exception as e:
            self.stdout.write(f"❌ Error general: {e}")
            sys.exit(1)

    def confirmar_limpieza(self):
        """Solicita confirmación antes de proceder con la limpieza"""
        self.stdout.write("⚠️  ADVERTENCIA: Este script eliminará TODOS los datos de prueba del sistema.")
        self.stdout.write("📋 Se eliminarán:")
        self.stdout.write("   - Todos los participantes de prueba")
        self.stdout.write("   - Todas las evaluaciones de prueba")
        self.stdout.write("   - Todas las preguntas y opciones")
        self.stdout.write("   - Todos los grupos de participantes")
        self.stdout.write("   - Todos los representantes")
        self.stdout.write("   - Todos los resultados de evaluaciones")
        self.stdout.write("   - Todos los perfiles de usuario asociados")
        self.stdout.write()
        
        respuesta = input("¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): ")
        return respuesta.upper() == 'SI'

    def limpiar_datos_prueba(self):
        """Elimina todos los datos de prueba del sistema"""
        self.stdout.write("🧹 Iniciando limpieza de datos de prueba...")
        
        # Contadores para el resumen
        contadores = {
            'resultados': 0,
            'opciones': 0,
            'preguntas': 0,
            'evaluaciones': 0,
            'participantes': 0,
            'grupos': 0,
            'representantes': 0,
            'usuarios': 0,
            'perfiles_admin': 0,
            'perfiles_usuario': 0
        }
        
        try:
            # 1. Eliminar resultados de evaluaciones
            self.stdout.write("🗑️  Eliminando resultados de evaluaciones...")
            resultados = ResultadoEvaluacion.objects.all()
            contadores['resultados'] = resultados.count()
            resultados.delete()
            self.stdout.write(f"✅ {contadores['resultados']} resultados eliminados")
            
            # 2. Eliminar opciones de preguntas
            self.stdout.write("🗑️  Eliminando opciones de preguntas...")
            opciones = Opcion.objects.all()
            contadores['opciones'] = opciones.count()
            opciones.delete()
            self.stdout.write(f"✅ {contadores['opciones']} opciones eliminadas")
            
            # 3. Eliminar preguntas
            self.stdout.write("🗑️  Eliminando preguntas...")
            preguntas = Pregunta.objects.all()
            contadores['preguntas'] = preguntas.count()
            preguntas.delete()
            self.stdout.write(f"✅ {contadores['preguntas']} preguntas eliminadas")
            
            # 4. Eliminar evaluaciones
            self.stdout.write("🗑️  Eliminando evaluaciones...")
            evaluaciones = Evaluacion.objects.all()
            contadores['evaluaciones'] = evaluaciones.count()
            evaluaciones.delete()
            self.stdout.write(f"✅ {contadores['evaluaciones']} evaluaciones eliminadas")
            
            # 5. Eliminar participantes
            self.stdout.write("🗑️  Eliminando participantes...")
            participantes = Participantes.objects.all()
            contadores['participantes'] = participantes.count()
            
            # Obtener los usuarios asociados antes de eliminar participantes
            usuarios_participantes = [p.user for p in participantes]
            participantes.delete()
            self.stdout.write(f"✅ {contadores['participantes']} participantes eliminados")
            
            # 6. Eliminar grupos de participantes
            self.stdout.write("🗑️  Eliminando grupos de participantes...")
            grupos = GrupoParticipantes.objects.all()
            contadores['grupos'] = grupos.count()
            grupos.delete()
            self.stdout.write(f"✅ {contadores['grupos']} grupos eliminados")
            
            # 7. Eliminar representantes
            self.stdout.write("🗑️  Eliminando representantes...")
            representantes = Representante.objects.all()
            contadores['representantes'] = representantes.count()
            representantes.delete()
            self.stdout.write(f"✅ {contadores['representantes']} representantes eliminados")
            
            # 8. Eliminar perfiles de administradores (no superuser)
            self.stdout.write("🗑️  Eliminando perfiles de administradores...")
            perfiles_admin = AdminProfile.objects.all()
            contadores['perfiles_admin'] = perfiles_admin.count()
            
            # Obtener los usuarios asociados antes de eliminar perfiles
            usuarios_admin = [p.user for p in perfiles_admin]
            perfiles_admin.delete()
            self.stdout.write(f"✅ {contadores['perfiles_admin']} perfiles de administradores eliminados")
            
            # 9. Eliminar perfiles de usuario
            self.stdout.write("🗑️  Eliminando perfiles de usuario...")
            perfiles_usuario = UserProfile.objects.all()
            contadores['perfiles_usuario'] = perfiles_usuario.count()
            
            # Obtener los usuarios asociados antes de eliminar perfiles
            usuarios_perfil = [p.user for p in perfiles_usuario]
            perfiles_usuario.delete()
            self.stdout.write(f"✅ {contadores['perfiles_usuario']} perfiles de usuario eliminados")
            
            # 10. Eliminar usuarios (participantes, admins y perfiles)
            self.stdout.write("🗑️  Eliminando usuarios...")
            todos_usuarios = set(usuarios_participantes + usuarios_admin + usuarios_perfil)
            
            # Filtrar usuarios que no sean superusuarios
            usuarios_a_eliminar = [u for u in todos_usuarios if not u.is_superuser]
            contadores['usuarios'] = len(usuarios_a_eliminar)
            
            for usuario in usuarios_a_eliminar:
                try:
                    usuario.delete()
                except Exception as e:
                    self.stdout.write(f"⚠️  No se pudo eliminar usuario {usuario.username}: {e}")
            
            self.stdout.write(f"✅ {contadores['usuarios']} usuarios eliminados")
            
            self.stdout.write("\n🎉 ¡Limpieza completada exitosamente!")
            
            # Mostrar resumen
            self.stdout.write("\n📊 Resumen de elementos eliminados:")
            total_elementos = sum(contadores.values())
            for elemento, cantidad in contadores.items():
                if cantidad > 0:
                    self.stdout.write(f"   - {elemento.replace('_', ' ').title()}: {cantidad}")
            
            self.stdout.write(f"\n📈 Total de elementos eliminados: {total_elementos}")
            
            # Verificar que la limpieza fue exitosa
            self.stdout.write("\n🔍 Verificando limpieza...")
            elementos_restantes = {
                'Participantes': Participantes.objects.count(),
                'Evaluaciones': Evaluacion.objects.count(),
                'Preguntas': Pregunta.objects.count(),
                'Opciones': Opcion.objects.count(),
                'Grupos': GrupoParticipantes.objects.count(),
                'Representantes': Representante.objects.count(),
                'Resultados': ResultadoEvaluacion.objects.count(),
                'Perfiles Admin': AdminProfile.objects.count(),
                'Perfiles Usuario': UserProfile.objects.count()
            }
            
            elementos_con_datos = {k: v for k, v in elementos_restantes.items() if v > 0}
            
            if elementos_con_datos:
                self.stdout.write("⚠️  Elementos que aún contienen datos:")
                for elemento, cantidad in elementos_con_datos.items():
                    self.stdout.write(f"   - {elemento}: {cantidad}")
            else:
                self.stdout.write("✅ Todos los datos de prueba han sido eliminados correctamente")
            
        except Exception as e:
            self.stdout.write(f"❌ Error durante la limpieza: {e}")
            raise 