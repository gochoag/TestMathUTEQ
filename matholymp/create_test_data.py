#!/usr/bin/env python
"""
Script para crear datos de prueba para las evaluaciones
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olymp.settings')
django.setup()

from quizzes.models import Evaluacion, Pregunta, Opcion
from django.utils import timezone

def create_test_evaluations():
    """Crear evaluaciones de prueba"""
    
    print("🗑️ Limpiando datos existentes...")
    
    # Limpiar todos los datos existentes
    Opcion.objects.all().delete()
    Pregunta.objects.all().delete()
    Evaluacion.objects.all().delete()
    

if __name__ == '__main__':
    try:
        create_test_evaluations()
    except Exception as e:
        print(f"❌ Error al crear datos de prueba: {e}")
        sys.exit(1) 