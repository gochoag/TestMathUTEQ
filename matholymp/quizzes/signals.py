from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, ResultadoEvaluacion, MonitoreoEvaluacion
from django.utils import timezone


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear perfil de usuario cuando se crea un nuevo usuario"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar el perfil de usuario cuando se actualiza el usuario"""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # Si no existe el perfil, crearlo
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=ResultadoEvaluacion)
def actualizar_monitoreo_evaluacion(sender, instance, **kwargs):
    """
    Actualizar automáticamente el estado del monitoreo cuando se complete una evaluación
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Signal activado para ResultadoEvaluacion: {instance.id}, completada: {instance.completada}")
    
    if instance.completada:
        try:
            # Buscar el monitoreo correspondiente
            monitoreo = MonitoreoEvaluacion.objects.filter(
                evaluacion=instance.evaluacion,
                participante=instance.participante
            ).first()
            
            if monitoreo:
                logger.info(f"Monitoreo encontrado: {monitoreo.id}, estado actual: {monitoreo.estado}")
                
                # Actualizar el estado a finalizado
                monitoreo.estado = 'finalizado'
                monitoreo.resultado = instance
                monitoreo.fecha_ultima_actualizacion = timezone.now()
                monitoreo.save()
                
                logger.info(f"Monitoreo actualizado a 'finalizado' para {instance.participante.NombresCompletos}")
                
                # Notificar al WebSocket sobre la actualización del monitoreo
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        group_name = f'monitoreo_evaluacion_{instance.evaluacion.id}'
                        logger.info(f"Enviando notificación WebSocket al grupo: {group_name}")
                        
                        message_data = {
                            'type': 'participant_update',
                            'participant_id': instance.participante.id,
                            'participante_id': instance.participante.id,  # Para compatibilidad
                            'event_type': 'evaluation_completed',
                            'estado': 'finalizado',
                            'esta_activo': False,
                            'tiene_resultado_completado': True,
                            'puntaje': float(instance.puntaje),  # Convertir a float
                            'puntaje_numerico': str(instance.get_puntaje_numerico()),  # Convertir a string
                            'finalizado_por_admin': monitoreo.finalizado_por_admin is not None,
                            'data': {
                                'estado': 'finalizado',
                                'ultima_actividad': timezone.now().isoformat(),
                                'preguntas_respondidas': len([r for r in instance.respuestas_guardadas.values() if r]) if instance.respuestas_guardadas else 0,
                                'resultado_id': instance.id,
                                'puntaje': float(instance.puntaje),  # Convertir a float
                                'puntaje_numerico': str(instance.get_puntaje_numerico()),  # Convertir a string
                                'tiene_resultado_completado': True,
                                'finalizado_por_admin': monitoreo.finalizado_por_admin is not None
                            }
                        }
                        
                        async_to_sync(channel_layer.group_send)(group_name, message_data)
                        logger.info(f"Notificación WebSocket enviada exitosamente para {instance.participante.NombresCompletos}")
                    else:
                        logger.error("Channel layer no disponible")
                        
                except Exception as ws_error:
                    logger.error(f"Error al enviar notificación WebSocket: {str(ws_error)}")
                
                print(f"Monitoreo actualizado para {instance.participante.NombresCompletos} - Evaluación completada")
            else:
                logger.warning(f"No se encontró monitoreo para evaluación {instance.evaluacion.id} y participante {instance.participante.id}")
            
        except Exception as e:
            logger.error(f"Error al actualizar monitoreo: {str(e)}")
            print(f"Error al actualizar monitoreo: {str(e)}")


@receiver(post_save, sender=MonitoreoEvaluacion)
def notificar_cambio_monitoreo(sender, instance, created, **kwargs):
    """
    Notificar cambios en el monitoreo a través de WebSocket
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not created:  # Solo notificar actualizaciones, no creaciones
        logger.info(f"Signal de MonitoreoEvaluacion activado para: {instance.participante.NombresCompletos}, estado: {instance.estado}")
        
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                # Determinar el tipo de evento
                event_type = 'monitoring_update'
                
                # Obtener información de intentos
                intento_participante = instance.evaluacion.get_o_crear_intento_participante(instance.participante)
                
                data = {
                    'estado': instance.estado,
                    'ultima_actividad': instance.ultima_actividad.isoformat() if instance.ultima_actividad else timezone.now().isoformat(),
                    'esta_activo': instance.esta_activo(),
                    'tiene_resultado_completado': instance.resultado and instance.resultado.completada if instance.resultado else False,
                    'finalizado_por_admin': instance.finalizado_por_admin is not None,
                    'intentos_utilizados': intento_participante.intentos_utilizados,
                    'intentos_permitidos': intento_participante.intentos_permitidos,
                    'participante_nombre': instance.participante.NombresCompletos,
                    'participante_cedula': instance.participante.cedula,
                    'monitoreo_id': instance.id
                }
                
                # Si fue finalizada por admin, incluir información adicional
                if instance.finalizado_por_admin:
                    event_type = 'admin_termination'
                    data.update({
                        'motivo_finalizacion': instance.motivo_finalizacion,
                        'admin': instance.finalizado_por_admin.username if instance.finalizado_por_admin else 'Sistema'
                    })
                
                group_name = f'monitoreo_evaluacion_{instance.evaluacion.id}'
                message_data = {
                    'type': 'participant_update',
                    'participant_id': instance.participante.id,
                    'participante_id': instance.participante.id,  # Para compatibilidad
                    'event_type': event_type,
                    'data': data
                }
                
                logger.info(f"Enviando notificación de cambio en monitoreo al grupo: {group_name}")
                async_to_sync(channel_layer.group_send)(group_name, message_data)
                logger.info(f"Notificación de cambio en monitoreo enviada para {instance.participante.NombresCompletos}")
            else:
                logger.error("Channel layer no disponible para notificar cambio en monitoreo")
                
        except Exception as e:
            logger.error(f"Error al notificar cambio en monitoreo: {str(e)}")
            print(f"Error al notificar cambio en monitoreo: {str(e)}") 