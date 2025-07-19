from django.contrib.auth.models import User
from django.db import models
from django.utils.crypto import get_random_string


class ParticipantGroup(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Modelo para distinguir a los administradores (no superuser)
class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_admins')  # Super admin que lo creó
    password = models.CharField(max_length=50, blank=True, help_text='Contraseña generada para el admin')

    def __str__(self):
        return self.user.get_full_name() or self.user.username




# Modelo para los participantes
class Participant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cedula = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    groups = models.ManyToManyField(ParticipantGroup, related_name='participants', blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.cedula})"

    @staticmethod
    def create_participant(cedula, nombres, apellidos, email, phone=None):
        password = get_random_string(length=6)
        user = User.objects.create_user(username=cedula, password=password, first_name=nombres, last_name=apellidos, email=email)
        participant = Participant.objects.create(user=user, cedula=cedula, nombres=nombres, apellidos=apellidos, email=email, phone=phone or "")
        # Aquí se puede agregar lógica para enviar el correo con la contraseña
        return participant, password

# Modelo Quiz para las evaluaciones

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()

    def __str__(self):
        return self.title

# Modelo para las preguntas
class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField(help_text='Use LaTeX para fórmulas')

    def __str__(self):
        return self.text[:50]

# Modelo para las opciones de respuesta
class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

