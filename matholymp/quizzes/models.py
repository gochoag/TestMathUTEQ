from django.contrib.auth.models import User
from django.db import models
from django.utils.crypto import get_random_string
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

# Validadores personalizados
def validate_cedula(value):
    """Valida que la cédula tenga exactamente 10 dígitos numéricos"""
    if not re.match(r'^\d{10}$', value):
        raise ValidationError('La cédula debe tener exactamente 10 dígitos numéricos.')
    return value

def validate_phone(value):
    """Valida que el teléfono tenga exactamente 10 dígitos numéricos"""
    if value and not re.match(r'^\d{10}$', value):
        raise ValidationError('El teléfono debe tener exactamente 10 dígitos numéricos.')
    return value

# Nuevo modelo para representantes
class Representante(models.Model):
    NombreColegio = models.CharField(max_length=200)
    DireccionColegio = models.CharField(max_length=300)
    TelefonoInstitucional = models.CharField(max_length=10, validators=[validate_phone])
    CorreoInstitucional = models.EmailField()
    NombresRepresentante = models.CharField(max_length=200)
    TelefonoRepresentante = models.CharField(max_length=10, validators=[validate_phone])
    CorreoRepresentante = models.EmailField()

    def __str__(self):
        return f"{self.NombresRepresentante} - {self.NombreColegio}"

# Modelo para grupos de participantes
class GrupoParticipantes(models.Model):
    name = models.CharField(max_length=100)
    representante = models.ForeignKey(Representante, on_delete=models.SET_NULL, null=True, blank=True, related_name='grupos')
    participantes = models.ManyToManyField('Participantes', related_name='grupos', blank=True)

    def __str__(self):
        return self.name

# Modelo para distinguir a los administradores (no superuser)
class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_admins')  # Super admin que lo creó
    password = models.CharField(max_length=50, blank=True, help_text='Contraseña generada para el admin')
    acceso_total = models.BooleanField(default=False, help_text='Permite acceso total al sistema')

    def __str__(self):
        return self.user.get_full_name() or self.user.username

# Modelo para los participantes
class Participantes(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cedula = models.CharField(max_length=10, unique=True, validators=[validate_cedula])
    NombresCompletos = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=10, blank=True, validators=[validate_phone])
    edad = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.NombresCompletos} ({self.cedula})"

    @staticmethod
    def create_participant(cedula, NombresCompletos, email, phone=None, edad=None):
        password = get_random_string(length=6)
        user = User.objects.create_user(username=cedula, password=password, first_name=NombresCompletos, email=email)
        participante = Participantes.objects.create(user=user, cedula=cedula, NombresCompletos=NombresCompletos, email=email, phone=phone or "", edad=edad)
        # Aquí se puede agregar lógica para enviar el correo con la contraseña
        return participante, password

# Modelo Evaluacion para las evaluaciones
class Evaluacion(models.Model):
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField(help_text='Fecha y hora de inicio de la ventana de acceso')
    end_time = models.DateTimeField(help_text='Fecha y hora de finalización de la ventana de acceso')
    duration_minutes = models.PositiveIntegerField(help_text='Tiempo disponible para completar la evaluación (en minutos)')

    def __str__(self):
        return self.title
    
    def is_available(self):
        """Verifica si la evaluación está disponible para ser tomada"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
    def is_finished(self):
        """Verifica si la evaluación ya terminó"""
        now = timezone.now()
        return now > self.end_time
    
    def is_not_started(self):
        """Verifica si la evaluación aún no ha comenzado"""
        now = timezone.now()
        return now < self.start_time
    
    def get_status(self):
        """Retorna el estado actual de la evaluación"""
        if self.is_not_started():
            return 'pending'
        elif self.is_available():
            return 'active'
        else:
            return 'finished'
    
    def get_status_display(self):
        """Retorna el texto del estado de la evaluación"""
        status = self.get_status()
        if status == 'pending':
            return 'Pendiente'
        elif status == 'active':
            return 'Disponible'
        else:
            return 'Finalizada'
    
    def clean(self):
        """Validación personalizada del modelo"""
        from django.core.exceptions import ValidationError
        
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError('La fecha de inicio debe ser anterior a la fecha de finalización.')
        
        if self.duration_minutes <= 0:
            raise ValidationError('La duración debe ser mayor a 0 minutos.')
        
        if self.duration_minutes > 480:  # 8 horas máximo
            raise ValidationError('La duración no puede exceder 8 horas.')
    
    class Meta:
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'

# Modelo para las preguntas
class Pregunta(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, related_name='preguntas', on_delete=models.CASCADE)
    text = models.TextField(help_text='Use LaTeX para fórmulas')

    def __str__(self):
        return self.text[:50]

# Modelo para las opciones de respuesta
class Opcion(models.Model):
    pregunta = models.ForeignKey(Pregunta, related_name='opciones', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

