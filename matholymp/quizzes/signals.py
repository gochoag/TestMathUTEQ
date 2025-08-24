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
    if instance.completada:
        try:
            # Buscar el monitoreo correspondiente
            monitoreo = MonitoreoEvaluacion.objects.filter(
                evaluacion=instance.evaluacion,
                participante=instance.participante
            ).first()
            
            if monitoreo:
                # Actualizar el estado a finalizado
                monitoreo.estado = 'finalizado'
                monitoreo.resultado = instance
                monitoreo.fecha_ultima_actualizacion = timezone.now()
                monitoreo.save()
                
                print(f"Monitoreo actualizado para {instance.participante.NombresCompletos} - Evaluación completada")
            
        except Exception as e:
            print(f"Error al actualizar monitoreo: {str(e)}") 