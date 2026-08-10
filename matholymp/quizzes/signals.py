from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Participantes


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear automáticamente un perfil de usuario cuando se crea un nuevo usuario"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar el perfil de usuario cuando se actualiza el usuario"""
    try:
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
        else:
            UserProfile.objects.get_or_create(user=instance)
    except Exception:
        pass


@receiver(post_save, sender=User)
def sync_user_to_participante(sender, instance, created, **kwargs):
    """
    Sincroniza cambios de email y nombres desde User hacia Participantes de forma bidireccional.
    """
    if getattr(instance, '_syncing', False):
        return
        
    try:
        participante = Participantes.objects.filter(user=instance).first()
        if participante:
            email_normalized = (instance.email or '').lower().strip()
            full_name = instance.get_full_name() or instance.first_name
            
            needs_update = False
            if email_normalized and participante.email != email_normalized:
                participante.email = email_normalized
                needs_update = True
                
            if full_name and participante.NombresCompletos != full_name:
                participante.NombresCompletos = full_name
                needs_update = True
                
            if needs_update:
                participante._syncing = True
                participante.save()
                participante._syncing = False
    except Exception:
        pass


@receiver(post_save, sender=Participantes)
def sync_participante_to_user(sender, instance, created, **kwargs):
    """
    Sincroniza cambios de email y NombresCompletos desde Participantes hacia User.
    """
    if getattr(instance, '_syncing', False):
        return
        
    try:
        user = instance.user
        if user:
            email_normalized = (instance.email or '').lower().strip()
            full_name = (instance.NombresCompletos or '').strip()
            
            needs_update = False
            if email_normalized and user.email != email_normalized:
                user.email = email_normalized
                needs_update = True
                
            if full_name and user.first_name != full_name:
                user.first_name = full_name
                needs_update = True
                
            if needs_update:
                user._syncing = True
                user.save()
                user._syncing = False
    except Exception:
        pass


# --- DISPARADORES AUTOMÁTICOS DE AUDITORÍA DE SEGURIDAD (SIGNALS) ---

from .models import Pregunta, Evaluacion, ResultadoEvaluacion, AdminProfile, AuditLog
from olymp.middleware import get_current_user, get_current_ip

@receiver(post_save, sender=Pregunta)
def audit_pregunta_save(sender, instance, created, **kwargs):
    try:
        user = get_current_user()
        ip = get_current_ip()
        accion = 'CREACION_PREGUNTA' if created else 'EDICION_PREGUNTA'
        texto_corto = (instance.text or '')[:60]
        detalles = f"{'Creó' if created else 'Modificó'} la pregunta ID {instance.id}: '{texto_corto}...'"
        AuditLog.registrar_accion(usuario_ejecutor=user, accion=accion, detalles=detalles, ip_address=ip)
    except Exception:
        pass

@receiver(post_delete, sender=Pregunta)
def audit_pregunta_delete(sender, instance, **kwargs):
    try:
        user = get_current_user()
        ip = get_current_ip()
        texto_corto = (instance.text or '')[:60]
        detalles = f"Eliminó la pregunta ID {instance.id}: '{texto_corto}...'"
        AuditLog.registrar_accion(usuario_ejecutor=user, accion='ELIMINACION_PREGUNTA', detalles=detalles, ip_address=ip)
    except Exception:
        pass

@receiver(post_save, sender=Evaluacion)
def audit_evaluacion_save(sender, instance, created, **kwargs):
    try:
        user = get_current_user()
        ip = get_current_ip()
        accion = 'CREACION_EVALUACION' if created else 'EDICION_EVALUACION'
        detalles = f"{'Creó' if created else 'Modificó'} la evaluación '{instance.title}' (ID {instance.id}, Etapa: {instance.etapa}, Duración: {instance.duration_minutes}m)"
        AuditLog.registrar_accion(usuario_ejecutor=user, accion=accion, detalles=detalles, ip_address=ip)
    except Exception:
        pass

@receiver(post_delete, sender=Evaluacion)
def audit_evaluacion_delete(sender, instance, **kwargs):
    try:
        user = get_current_user()
        ip = get_current_ip()
        detalles = f"Eliminó la evaluación '{instance.title}' (ID {instance.id})"
        AuditLog.registrar_accion(usuario_ejecutor=user, accion='ELIMINACION_EVALUACION', detalles=detalles, ip_address=ip)
    except Exception:
        pass

@receiver(post_save, sender=ResultadoEvaluacion)
def audit_resultado_save(sender, instance, created, **kwargs):
    try:
        if not created:
            user = get_current_user()
            ip = get_current_ip()
            detalles = f"Modificó la nota/resultado del participante '{instance.participante}' en '{instance.evaluacion.title}' (Nota: {instance.puntos_obtenidos}/10)"
            AuditLog.registrar_accion(usuario_ejecutor=user, accion='MODIFICACION_PUNTAJE', detalles=detalles, ip_address=ip)
    except Exception:
        pass

@receiver(post_delete, sender=ResultadoEvaluacion)
def audit_resultado_delete(sender, instance, **kwargs):
    try:
        user = get_current_user()
        ip = get_current_ip()
        detalles = f"Eliminó el intento de examen de '{instance.participante}' en '{instance.evaluacion.title}'"
        AuditLog.registrar_accion(usuario_ejecutor=user, accion='ELIMINACION_INTENTO', detalles=detalles, ip_address=ip)
    except Exception:
        pass