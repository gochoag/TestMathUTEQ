from django.contrib.auth.models import User
from django.db import models


class ParticipantGroup(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Participant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cedula = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    groups = models.ManyToManyField(ParticipantGroup, related_name='participants', blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.cedula})"


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField(help_text='Use LaTeX for formulas')

    def __str__(self):
        return self.text[:50]


class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text
