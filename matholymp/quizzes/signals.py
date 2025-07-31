from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear automáticamente un perfil de usuario cuando se crea un nuevo usuario"""
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