"""
Tareas de Celery para el sistema de monitoreo en tiempo real
"""
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from datetime import timedelta
from .models import MonitoreoEvaluacion, Evaluacion
import logging

logger = logging.getLogger(__name__)


@shared_task
def actualizar_monitoreo_evaluaciones_activas():
    """
    Tarea periódica para actualizar el monitoreo de evaluaciones activas
    Se ejecuta cada 60 segundos para enviar actualizaciones a los administradores
    """
    try:
        # Obtener evaluaciones activas
        ahora = timezone.now()
        evaluaciones_activas = Evaluacion.objects.filter(
            start_time__lte=ahora,
            end_time__gt=ahora
        )
        
        channel_layer = get_channel_layer()
        
        for evaluacion in evaluaciones_activas:
            # Enviar actualización a cada grupo de monitoreo
            group_name = f'monitoreo_evaluacion_{evaluacion.id}'
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'monitoring_update',
                    'data': {
                        'force_update': True,
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )
        
        logger.info(f"Actualizaciones de monitoreo enviadas para {len(evaluaciones_activas)} evaluaciones activas")
        return f"Procesadas {len(evaluaciones_activas)} evaluaciones"
        
    except Exception as e:
        logger.error(f"Error en actualizar_monitoreo_evaluaciones_activas: {str(e)}")
        raise


@shared_task
def detectar_participantes_inactivos():
    """
    Tarea para detectar participantes inactivos y generar alertas automáticas
    Se ejecuta cada 2 minutos
    """
    try:
        # Definir tiempo límite de inactividad (10 minutos)
        tiempo_limite = timezone.now() - timedelta(minutes=10)
        
        # Buscar monitoreos activos con inactividad prolongada
        monitoreos_inactivos = MonitoreoEvaluacion.objects.filter(
            estado='activo',
            ultima_actividad__lt=tiempo_limite,
            evaluacion__start_time__lte=timezone.now(),
            evaluacion__end_time__gt=timezone.now()
        )
        
        alertas_generadas = 0
        
        for monitoreo in monitoreos_inactivos:
            # Verificar si ya existe una alerta de inactividad reciente
            alertas_inactividad = [
                alerta for alerta in monitoreo.alertas_detectadas 
                if alerta.get('tipo') == 'inactividad' and 
                   (timezone.now() - timezone.fromisoformat(alerta.get('timestamp', '2000-01-01T00:00:00Z'))) < timedelta(minutes=30)
            ]
            
            if not alertas_inactividad:
                # Agregar alerta de inactividad
                tiempo_inactivo = timezone.now() - monitoreo.ultima_actividad
                minutos_inactivo = int(tiempo_inactivo.total_seconds() // 60)
                
                monitoreo.agregar_alerta(
                    'inactividad',
                    f'Participante inactivo por {minutos_inactivo} minutos',
                    'media'
                )
                alertas_generadas += 1
                
                # Enviar actualización al grupo de monitoreo
                channel_layer = get_channel_layer()
                group_name = f'monitoreo_evaluacion_{monitoreo.evaluacion.id}'
                
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'participant_update',
                        'participant_id': monitoreo.participante.id,
                        'event_type': 'inactivity_alert',
                        'data': {
                            'alert_type': 'inactividad',
                            'minutes_inactive': minutos_inactivo
                        }
                    }
                )
        
        logger.info(f"Generadas {alertas_generadas} alertas de inactividad")
        return f"Generadas {alertas_generadas} alertas de inactividad"
        
    except Exception as e:
        logger.error(f"Error en detectar_participantes_inactivos: {str(e)}")
        raise


@shared_task
def limpiar_monitoreos_antiguos():
    """
    Tarea para limpiar monitoreos de evaluaciones que han finalizado hace más de 24 horas
    Se ejecuta diariamente
    """
    try:
        tiempo_limite = timezone.now() - timedelta(hours=24)
        
        # Buscar evaluaciones finalizadas hace más de 24 horas
        evaluaciones_antiguas = Evaluacion.objects.filter(
            end_time__lt=tiempo_limite
        )
        
        monitoreos_eliminados = 0
        
        for evaluacion in evaluaciones_antiguas:
            # Eliminar monitoreos asociados (mantener solo los datos del resultado)
            monitoreos = MonitoreoEvaluacion.objects.filter(evaluacion=evaluacion)
            count = monitoreos.count()
            monitoreos.delete()
            monitoreos_eliminados += count
        
        logger.info(f"Eliminados {monitoreos_eliminados} monitoreos antiguos")
        return f"Eliminados {monitoreos_eliminados} monitoreos antiguos"
        
    except Exception as e:
        logger.error(f"Error en limpiar_monitoreos_antiguos: {str(e)}")
        raise


@shared_task
def enviar_estadisticas_monitoreo(evaluacion_id):
    """
    Tarea para enviar estadísticas actualizadas de una evaluación específica
    """
    try:
        evaluacion = Evaluacion.objects.get(id=evaluacion_id)
        channel_layer = get_channel_layer()
        group_name = f'monitoreo_evaluacion_{evaluacion.id}'
        
        # Enviar actualización forzada
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'monitoring_update',
                'data': {
                    'force_update': True,
                    'timestamp': timezone.now().isoformat(),
                    'manual_trigger': True
                }
            }
        )
        
        logger.info(f"Estadísticas de monitoreo enviadas para evaluación {evaluacion_id}")
        return f"Estadísticas enviadas para evaluación {evaluacion_id}"
        
    except Evaluacion.DoesNotExist:
        logger.error(f"Evaluación {evaluacion_id} no encontrada")
        raise
    except Exception as e:
        logger.error(f"Error en enviar_estadisticas_monitoreo: {str(e)}")
        raise


@shared_task
def notificar_finalizacion_evaluacion(evaluacion_id, participante_id, razon='completada'):
    """
    Tarea para notificar la finalización de una evaluación
    """
    try:
        from .models import Participantes
        
        evaluacion = Evaluacion.objects.get(id=evaluacion_id)
        participante = Participantes.objects.get(id=participante_id)
        
        channel_layer = get_channel_layer()
        
        # Notificar al grupo de monitoreo
        monitoring_group_name = f'monitoreo_evaluacion_{evaluacion.id}'
        async_to_sync(channel_layer.group_send)(
            monitoring_group_name,
            {
                'type': 'participant_update',
                'participant_id': participante.id,
                'event_type': 'evaluation_completed',
                'data': {
                    'reason': razon,
                    'timestamp': timezone.now().isoformat()
                }
            }
        )
        
        # Notificar al participante si es terminación administrativa
        if razon == 'admin_terminated':
            participant_group_name = f'evaluacion_{evaluacion.id}_participante_{participante.id}'
            async_to_sync(channel_layer.group_send)(
                participant_group_name,
                {
                    'type': 'evaluation_terminated',
                    'data': {
                        'reason': 'Evaluación finalizada por un administrador',
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )
        
        logger.info(f"Notificación de finalización enviada para participante {participante_id} en evaluación {evaluacion_id}")
        return f"Notificación enviada para participante {participante_id}"
        
    except (Evaluacion.DoesNotExist, Participantes.DoesNotExist) as e:
        logger.error(f"Entidad no encontrada: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error en notificar_finalizacion_evaluacion: {str(e)}")
        raise
