from django.contrib.auth.models import User
from django.db import models, transaction, IntegrityError
from django.utils.crypto import get_random_string
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
import os
from datetime import datetime




# Modelo para Facultades de la Institución
class Facultad(models.Model):
    nombre = models.CharField(max_length=150, unique=True, help_text='Nombre de la Facultad (ej: Facultad de Ciencias de la Ingeniería)')
    siglas = models.CharField(max_length=20, blank=True, help_text='Ej: FCI')
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Facultad'
        verbose_name_plural = 'Facultades'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.siglas})" if self.siglas else self.nombre


# Modelo para Carreras Universitarias
class Carrera(models.Model):
    facultad = models.ForeignKey(Facultad, related_name='carreras', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150, help_text='Nombre de la Carrera (ej: Ingeniería de Software, Mecánica)')
    codigo = models.CharField(max_length=20, blank=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
        unique_together = ('facultad', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.facultad.nombre}"


# Modelo para Concursos / Olimpiadas (Evento con fechas, fases y participantes específicos)
class Concurso(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador / Registro'),
        ('EN_CURSO', 'En Curso'),
        ('FINALIZADO', 'Finalizado'),
        ('ARCHIVADO', 'Archivado'),
    ]
    carrera = models.ForeignKey(Carrera, related_name='concursos', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200, help_text='Nombre del Concurso (ej: I Olimpiada de Física FIC - Febrero 2026)')
    anio = models.IntegerField(default=datetime.now().year)
    num_etapas = models.PositiveSmallIntegerField(default=2, choices=[(2, '2 Etapas'), (3, '3 Etapas')])
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BORRADOR')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Concurso / Olimpiada'
        verbose_name_plural = 'Concursos / Olimpiadas'
        ordering = ['-fecha_creacion']

    def clean(self):
        super().clean()
        f_inicio = self.fecha_inicio
        f_fin = self.fecha_fin
        if isinstance(f_inicio, str) and f_inicio:
            try:
                f_inicio = datetime.strptime(f_inicio, '%Y-%m-%d').date()
            except ValueError:
                pass
        if isinstance(f_fin, str) and f_fin:
            try:
                f_fin = datetime.strptime(f_fin, '%Y-%m-%d').date()
            except ValueError:
                pass

        if f_inicio and f_fin and f_fin < f_inicio:
            raise ValidationError({'fecha_fin': 'La fecha de fin no puede ser anterior a la fecha de inicio.'})

        if self.pk:
            old_instance = Concurso.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.carrera_id != self.carrera_id:
                has_records = (
                    self.participantes.exists() or
                    self.representantes.exists() or
                    self.grupos.exists() or
                    self.evaluaciones.exists()
                )
                if has_records:
                    raise ValidationError({'carrera': 'No se puede cambiar la Carrera de este concurso porque ya posee participantes, representantes, grupos o evaluaciones registradas.'})

    def save(self, *args, **kwargs):
        if self.fecha_inicio:
            if isinstance(self.fecha_inicio, str):
                try:
                    self.anio = datetime.strptime(self.fecha_inicio, '%Y-%m-%d').year
                except ValueError:
                    self.anio = int(self.fecha_inicio[:4])
            elif hasattr(self.fecha_inicio, 'year'):
                self.anio = self.fecha_inicio.year
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.carrera.nombre})"

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

def validate_unique_email(value, model_class, instance=None):
    """Valida que el correo electrónico sea único en el modelo especificado"""
    # Normalizar el correo (convertir a minúsculas)
    email_normalized = value.lower().strip()
    
    # Buscar si ya existe un registro con este correo
    queryset = model_class.objects.filter(email__iexact=email_normalized)
    
    # Si estamos editando un registro existente, excluirlo de la búsqueda
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    
    if queryset.exists():
        raise ValidationError(f'Ya existe un registro con el correo electrónico "{value}".')
    
    return email_normalized

def validate_unique_correo_institucional(value, model_class, instance=None):
    """Valida que el correo institucional sea único"""
    email_normalized = value.lower().strip()
    
    queryset = model_class.objects.filter(CorreoInstitucional__iexact=email_normalized)
    
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    
    if queryset.exists():
        raise ValidationError(f'Ya existe un representante con el correo institucional "{value}".')
    
    return email_normalized

def validate_unique_correo_representante(value, model_class, instance=None):
    """Valida que el correo del representante sea único"""
    email_normalized = value.lower().strip()
    
    queryset = model_class.objects.filter(CorreoRepresentante__iexact=email_normalized)
    
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    
    if queryset.exists():
        raise ValidationError(f'Ya existe un representante con el correo "{value}".')
    
    return email_normalized

def validate_email_across_all_models(value, exclude_user_id=None, exclude_participante_id=None, exclude_representante_id=None):
    """
    Valida que el correo sea único en todos los modelos (User, Participantes, Representante)
    
    Args:
        value: El correo a validar
        exclude_user_id: ID del usuario a excluir de la validación
        exclude_participante_id: ID del participante a excluir de la validación
        exclude_representante_id: ID del representante a excluir de la validación
    
    Returns:
        str: El correo normalizado si es válido
    
    Raises:
        ValidationError: Si el correo ya existe en algún modelo
    """
    email_normalized = value.lower().strip()
    
    # Verificar en User
    user_queryset = User.objects.filter(email__iexact=email_normalized)
    if exclude_user_id:
        user_queryset = user_queryset.exclude(id=exclude_user_id)
    if user_queryset.exists():
        raise ValidationError(f'El correo "{value}" ya está registrado por otro usuario.')
    
    # Verificar en Participantes
    participante_queryset = Participantes.objects.filter(email__iexact=email_normalized)
    if exclude_participante_id:
        participante_queryset = participante_queryset.exclude(id=exclude_participante_id)
    if participante_queryset.exists():
        raise ValidationError(f'El correo "{value}" ya está registrado por un participante.')
    
    # Verificar en Representante
    representante_queryset = Representante.objects.filter(
        models.Q(CorreoInstitucional__iexact=email_normalized) | 
        models.Q(CorreoRepresentante__iexact=email_normalized)
    )
    if exclude_representante_id:
        representante_queryset = representante_queryset.exclude(id=exclude_representante_id)
    if representante_queryset.exists():
        raise ValidationError(f'El correo "{value}" ya está siendo usado por un representante.')
    
    return email_normalized

def upload_to_avatar(instance, filename):
    """
    Genera un nombre único para las imágenes de avatar basado en el username del usuario
    y la fecha/hora de subida para evitar conflictos
    """
    # Obtener la extensión del archivo original
    ext = filename.split('.')[-1]
    
    # Obtener el username del usuario
    username = instance.user.username if instance.user else 'usuario'
    
    # Generar timestamp único
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Crear nombre único: username_timestamp.ext
    new_filename = f"{username}_{timestamp}.{ext}"
    
    # Retornar la ruta completa
    return os.path.join('fotos', 'perfil', new_filename)

# Nuevo modelo para representantes
class Representante(models.Model):
    concurso = models.ForeignKey('Concurso', related_name='representantes', on_delete=models.CASCADE, help_text='Concurso específico al que pertenece')
    NombreColegio = models.CharField(max_length=200)
    DireccionColegio = models.CharField(max_length=300)
    TelefonoInstitucional = models.CharField(max_length=10, validators=[validate_phone])
    CorreoInstitucional = models.EmailField(help_text='Correo institucional (único por año)')
    NombresRepresentante = models.CharField(max_length=200)
    TelefonoRepresentante = models.CharField(max_length=10, validators=[validate_phone])
    CorreoRepresentante = models.EmailField(help_text='Correo del representante (único por año)')
    anio = models.IntegerField(default=datetime.now().year, help_text='Año del concurso al que pertenece')

    def clean(self):
        """Validación personalizada para evitar correos duplicados"""
        super().clean()
        
        if self.CorreoInstitucional:
            self.CorreoInstitucional = validate_unique_correo_institucional(
                self.CorreoInstitucional,
                Representante,
                self
            )
        
        if self.CorreoRepresentante:
            self.CorreoRepresentante = validate_unique_correo_representante(
                self.CorreoRepresentante,
                Representante,
                self
            )
        
        # Validar que los correos institucional y del representante no sean iguales
        if (self.CorreoInstitucional and self.CorreoRepresentante and 
            self.CorreoInstitucional.lower().strip() == self.CorreoRepresentante.lower().strip()):
            raise ValidationError('El correo institucional y el correo del representante no pueden ser iguales.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.NombresRepresentante} - {self.NombreColegio}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['CorreoInstitucional', 'anio'], name='unique_correo_institucional_por_anio'),
            models.UniqueConstraint(fields=['CorreoRepresentante', 'anio'], name='unique_correo_representante_por_anio'),
        ]

# Modelo para grupos de participantes
class GrupoParticipantes(models.Model):
    concurso = models.ForeignKey('Concurso', related_name='grupos', on_delete=models.CASCADE, help_text='Concurso específico al que pertenece')
    name = models.CharField(max_length=100)
    representante = models.ForeignKey(Representante, on_delete=models.SET_NULL, null=True, blank=True, related_name='grupos')
    participantes = models.ManyToManyField('Participantes', related_name='grupos', blank=True)
    anio = models.IntegerField(default=datetime.now().year, help_text='Año del concurso al que pertenece')

    def __str__(self):
        return self.name

# Modelo para el perfil de usuario
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to=upload_to_avatar, null=True, blank=True, help_text='Foto de perfil del usuario')
    phone = models.CharField(max_length=10, blank=True, validators=[validate_phone], help_text='Teléfono del usuario')
    bio = models.TextField(max_length=500, blank=True, help_text='Biografía o descripción del usuario')
    fecha_actualizacion = models.DateTimeField(auto_now=True, help_text='Fecha de última actualización del perfil')

    def __str__(self):
        return f"Perfil de {self.user.get_full_name() or self.user.username}"

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

# Modelo para distinguir a los administradores (no superuser)
class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    carrera = models.ForeignKey('Carrera', related_name='administradores', on_delete=models.SET_NULL, null=True, blank=True, help_text='Carrera asignada al administrador')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_admins')  # Super admin que lo creó
    acceso_total = models.BooleanField(default=False, help_text='Permite acceso total a la gestión dentro de su carrera asignada')

    def clean(self):
        super().clean()
        if self.user_id and not self.user.is_superuser and not self.carrera_id:
            raise ValidationError({'carrera': 'Todo administrador secundario debe tener asignada una carrera obligatoriamente.'})

    def save(self, *args, **kwargs):
        if self.user_id and not self.user.is_superuser:
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

# Modelo para configurar intentos específicos por participante y evaluación
class IntentosParticipante(models.Model):
    """
    Modelo para configurar intentos específicos por participante en evaluaciones
    Permite sobrescribir el número de intentos por defecto
    """
    participante = models.ForeignKey('Participantes', on_delete=models.CASCADE, related_name='configuraciones_intentos')
    evaluacion = models.ForeignKey('Evaluacion', on_delete=models.CASCADE, related_name='configuraciones_intentos')
    intentos_maximos = models.PositiveIntegerField(help_text='Intentos máximos para este participante en esta evaluación')
    
    # Campos de auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text='Admin que asignó los intentos')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField(blank=True, help_text='Motivo por el cual se asignaron intentos adicionales')
    
    class Meta:
        unique_together = ['participante', 'evaluacion']
        verbose_name = 'Configuración de Intentos'
        verbose_name_plural = 'Configuraciones de Intentos'
    
    def __str__(self):
        return f"{self.participante.NombresCompletos} - {self.evaluacion.title} ({self.intentos_maximos} intentos)"

# Modelo para los participantes
class Participantes(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    concurso = models.ForeignKey('Concurso', related_name='participantes', on_delete=models.CASCADE, help_text='Concurso al que pertenece')
    carrera = models.ForeignKey('Carrera', related_name='participantes', on_delete=models.CASCADE, help_text='Carrera a la que pertenece')
    cedula = models.CharField(max_length=10, unique=True, validators=[validate_cedula])
    NombresCompletos = models.CharField(max_length=200)
    email = models.EmailField(unique=True, help_text='Correo electrónico único')
    phone = models.CharField(max_length=10, blank=True, validators=[validate_phone])
    edad = models.IntegerField(null=True, blank=True)
    
    intentos_maximos_default = models.PositiveIntegerField(default=1, help_text='Intentos máximos por defecto para evaluaciones')

    def clean(self):
        """Validación personalizada para evitar correos duplicados"""
        super().clean()
        
        if self.email:
            self.email = validate_unique_email(self.email, Participantes, self)
        
        # Validar que el correo no esté siendo usado por un representante
        if self.email:
            email_normalized = self.email.lower().strip()
            if Representante.objects.filter(
                models.Q(CorreoInstitucional__iexact=email_normalized) |
                models.Q(CorreoRepresentante__iexact=email_normalized)
            ).exists():
                raise ValidationError(f'El correo "{self.email}" ya está siendo usado por un representante.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.NombresCompletos} ({self.cedula})"
    
    def get_intentos_disponibles(self, evaluacion):
        """Calcula intentos disponibles para una evaluación específica"""
        # Buscar configuración específica para esta evaluación
        intento_config = IntentosParticipante.objects.filter(
            participante=self,
            evaluacion=evaluacion
        ).first()
        
        if intento_config:
            max_intentos = intento_config.intentos_maximos
        else:
            max_intentos = self.intentos_maximos_default
        
        # Contar intentos usados (resultados completados)
        intentos_usados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=self,
            completada=True
        ).count()
        
        return max(0, max_intentos - intentos_usados)
    
    def get_intentos_usados(self, evaluacion):
        """Calcula intentos usados para una evaluación específica"""
        return ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=self,
            completada=True
        ).count()
    
    def puede_iniciar_evaluacion(self, evaluacion):
        """Verifica si el participante puede iniciar una evaluación"""
        return self.get_intentos_disponibles(evaluacion) > 0

    @staticmethod
    def create_participant(cedula, NombresCompletos, email, phone=None, edad=None, concurso=None, carrera=None):
        # Normalizar y validar datos antes de crear nada en BD
        cedula = str(cedula).strip()
        NombresCompletos = (NombresCompletos or '').strip()
        email_normalized = (email or '').lower().strip()

        # Validar correo único en participantes
        if Participantes.objects.filter(email__iexact=email_normalized).exists():
            raise ValidationError(f'Ya existe un participante con el correo "{email}".')

        # Validar correo contra representantes
        if Representante.objects.filter(
            models.Q(CorreoInstitucional__iexact=email_normalized) |
            models.Q(CorreoRepresentante__iexact=email_normalized)
        ).exists():
            raise ValidationError(f'El correo "{email}" ya está siendo usado por un representante.')

        # Validar que no exista ya un participante con esa cédula
        if Participantes.objects.filter(cedula=cedula).exists():
            raise ValidationError(f'La cédula {cedula} ya está registrada por otro participante.')

        # Crear de forma atómica para evitar registros parciales
        try:
            with transaction.atomic():
                password = get_random_string(length=6)

                # Reutilizar usuario huérfano si existe (username=cedula) o crear uno nuevo
                existing_user = User.objects.filter(username=cedula).first()
                if existing_user:
                    existing_user.first_name = NombresCompletos
                    existing_user.email = email_normalized
                    existing_user.set_password(password)
                    existing_user.save()
                    user = existing_user
                else:
                    user = User.objects.create_user(
                        username=cedula,
                        password=password,
                        first_name=NombresCompletos,
                        email=email_normalized,
                    )

                participante = Participantes.objects.create(
                    user=user,
                    cedula=cedula,
                    NombresCompletos=NombresCompletos,
                    email=email_normalized,
                    phone=phone or "",
                    edad=edad,
                    concurso=concurso,
                    carrera=carrera,
                )

                return participante, password
        except IntegrityError as exc:
            # Traducir errores de integridad a mensajes claros
            raise ValidationError(f'No se pudo crear el participante: {str(exc)}')

# Modelo Evaluacion para las evaluaciones
class Evaluacion(models.Model):
    ETAPA_CHOICES = [
        (1, 'Etapa 1 - Clasificatoria'),
        (2, 'Etapa 2 - Semifinal'),
        (3, 'Etapa 3 - Final'),
    ]
    
    concurso = models.ForeignKey('Concurso', related_name='evaluaciones', on_delete=models.CASCADE, help_text='Concurso al que pertenece esta evaluación')
    title = models.CharField(max_length=200)
    etapa = models.IntegerField(choices=ETAPA_CHOICES, default=1, help_text='Etapa de la olimpiada')
    start_time = models.DateTimeField(help_text='Fecha y hora de inicio de la ventana de acceso')
    end_time = models.DateTimeField(help_text='Fecha y hora de finalización de la ventana de acceso')
    duration_minutes = models.PositiveIntegerField(help_text='Tiempo disponible para completar la evaluación (en minutos)')
    anio = models.IntegerField(default=datetime.now().year, help_text='Año del concurso al que pertenece esta evaluación')
    
    # Campo total auto-calculado como suma de cuotas de Unidades Temáticas (Null hasta configurar preguntas)
    preguntas_a_mostrar = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None, 
        help_text='Número total de preguntas que se mostrarán al estudiante (calculado automáticamente al configurar cuotas)'
    )
    
    # Campos para participantes de la etapa 1
    grupos_participantes = models.ManyToManyField('GrupoParticipantes', blank=True, related_name='evaluaciones_etapa1')
    participantes_individuales = models.ManyToManyField('Participantes', blank=True, related_name='evaluaciones_individuales')

    def __str__(self):
        return f"{self.title} - Etapa {self.etapa}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalcular el total si existen cuotas de unidades asociadas
        if self.pk:
            total_cuotas = sum(c.cantidad_preguntas for c in self.cuotas_unidades.all())
            nuevo_total = total_cuotas if total_cuotas > 0 else None
            if self.preguntas_a_mostrar != nuevo_total:
                self.preguntas_a_mostrar = nuevo_total
                super().save(update_fields=['preguntas_a_mostrar'])

    def is_available(self):
        """Verifica si la evaluación está disponible para ser tomada"""
        now = timezone.localtime(timezone.now())
        start_time = timezone.localtime(self.start_time)
        end_time = timezone.localtime(self.end_time)
        return start_time <= now <= end_time
    
    def is_finished(self):
        """Verifica si la evaluación ya terminó"""
        now = timezone.localtime(timezone.now())
        end_time = timezone.localtime(self.end_time)
        return now > end_time
    
    def is_not_started(self):
        """Verifica si la evaluación aún no ha comenzado"""
        now = timezone.localtime(timezone.now())
        start_time = timezone.localtime(self.start_time)
        return now < start_time
    
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
    
    def get_etapa_display(self):
        """Retorna el nombre de la etapa"""
        return dict(self.ETAPA_CHOICES)[self.etapa]
    
    def get_participantes_etapa1(self):
        """Obtiene todos los participantes de la etapa 1 (grupos + individuales)"""
        participantes = set()
        
        # Agregar participantes de grupos
        for grupo in self.grupos_participantes.all():
            participantes.update(grupo.participantes.all())
        
        # Agregar participantes individuales
        participantes.update(self.participantes_individuales.all())
        
        return list(participantes)
    
    def get_participantes_etapa2(self):
        """Obtiene los mejores de la etapa 1 según configuración (15 si hay 3 etapas, 5 si hay 2)."""
        if self.etapa != 2:
            return []
        
        # Buscar la evaluación de la etapa 1
        evaluacion_etapa1 = Evaluacion.objects.filter(etapa=1, anio=self.anio).first()
        if not evaluacion_etapa1:
            return []
        
        # Determinar cuántos pasan desde etapa 1
        num_etapas = self.concurso.num_etapas if self.concurso else 3
        top_n = 15 if num_etapas == 3 else 5

        # Obtener los mejores resultados ordenados por nota (descendente) y tiempo en segundos (ascendente)
        resultados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa1,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado').select_related('participante')
        
        participantes = []
        vistos = set()
        for r in resultados:
            if r.participante_id not in vistos:
                vistos.add(r.participante_id)
                participantes.append(r.participante)
                if len(participantes) == top_n:
                    break
        
        return participantes
    
    def has_students_taking_exam(self):
        """Verifica si hay estudiantes que están actualmente rindiendo la evaluación"""
        if not self.pk:
            return False
            
        from django.utils import timezone
        now = timezone.now()
        
        resultados_activos = self.resultados.filter(
            completada=False,
            fecha_inicio__isnull=False,
            ultima_actividad__gte=now - timezone.timedelta(hours=1)
        )
        
        return resultados_activos.exists()
    
    def can_modify_questions(self):
        """
        Verifica si se pueden modificar las preguntas del banco de la evaluación.
        """
        if self.is_available():
            return False
        
        if self.has_students_taking_exam():
            return False
        
        return True
    
    def get_question_modification_restriction_message(self):
        """
        Retorna el mensaje de restricción apropiado para modificar preguntas
        """
        if self.is_available():
            return "No se pueden modificar las preguntas mientras la evaluación esté disponible."
        
        if self.has_students_taking_exam():
            return "No se pueden modificar las preguntas mientras hay estudiantes rindiendo la evaluación."
        
        return ""

    def get_participantes_etapa3(self):
        """Obtiene los 5 mejores de la etapa 2 (flujo actual) o directamente de etapa 1 si hay solo 2 etapas."""
        if self.etapa != 3:
            return []
        
        num_etapas = self.concurso.num_etapas if self.concurso else 3
        
        if num_etapas == 3:
            evaluacion_etapa = Evaluacion.objects.filter(etapa=2, anio=self.anio).first()
        else:
            evaluacion_etapa = Evaluacion.objects.filter(etapa=1, anio=self.anio).first()
            
        if not evaluacion_etapa:
            return []
        
        resultados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado').select_related('participante')
        
        participantes = []
        vistos = set()
        for r in resultados:
            if r.participante_id not in vistos:
                vistos.add(r.participante_id)
                participantes.append(r.participante)
                if len(participantes) == 5:
                    break
        
        return participantes
    
    def get_participantes_autorizados(self):
        """Obtiene los participantes autorizados según la etapa"""
        if self.etapa == 1:
            return self.get_participantes_etapa1()
        elif self.etapa == 2:
            if self.participantes_individuales.exists():
                return list(self.participantes_individuales.all())
            else:
                return self.get_participantes_etapa2()
        elif self.etapa == 3:
            if self.participantes_individuales.exists():
                return list(self.participantes_individuales.all())
            else:
                return self.get_participantes_etapa3()
        return []
    
    def get_preguntas_aleatorias(self):
        """Obtiene preguntas aleatorias segmentadas por Unidades Temáticas"""
        return self.get_preguntas_para_estudiante(participante_id=0, numero_intento=1)
    
    def get_preguntas_para_estudiante(self, participante_id, numero_intento=1):
        """Obtiene preguntas segmentadas por Unidades Temáticas con fallback de seguridad para un estudiante e intento específico"""
        import hashlib, random
        
        total_preguntas = self.preguntas.count()
        if total_preguntas == 0:
            return []
            
        cuotas = list(self.cuotas_unidades.select_related('unidad').all())
        total_requerido = sum(c.cantidad_preguntas for c in cuotas)
        if total_requerido <= 0:
            total_requerido = self.preguntas_a_mostrar or 10
            
        if total_preguntas <= total_requerido:
            return list(self.preguntas.prefetch_related('opciones', 'categoria').order_by('id'))
            
        hash_base = f"{self.id}_{participante_id}_{numero_intento}"
        hash_participante = hashlib.md5(hash_base.encode()).hexdigest()
        seed = int(hash_participante[:8], 16)
        random.seed(seed)
        
        seleccionadas = []
        ids_seleccionados = set()
        
        # 1. Muestreo determinístico por cada cuota de Unidad Temática configurada
        for cuota in cuotas:
            if cuota.cantidad_preguntas <= 0:
                continue
            pool = list(
                self.preguntas.filter(categoria__unidad=cuota.unidad)
                .exclude(id__in=ids_seleccionados)
                .prefetch_related('opciones', 'categoria')
                .order_by('id')
            )
            n = min(cuota.cantidad_preguntas, len(pool))
            if n > 0:
                elegidas = random.sample(pool, n)
                seleccionadas.extend(elegidas)
                ids_seleccionados.update(p.id for p in elegidas)
                
        # 2. Fallback de Seguridad: Si alguna unidad no tenía suficiente stock, completar con preguntas restantes
        if len(seleccionadas) < total_requerido:
            faltantes = total_requerido - len(seleccionadas)
            pool_restante = list(
                self.preguntas.exclude(id__in=ids_seleccionados)
                .prefetch_related('opciones', 'categoria')
                .order_by('id')
            )
            if pool_restante:
                n_extra = min(faltantes, len(pool_restante))
                extra = random.sample(pool_restante, n_extra)
                seleccionadas.extend(extra)
                
        random.shuffle(seleccionadas)
        return seleccionadas
    
    def clean(self):
        """Validación personalizada del modelo"""
        from django.core.exceptions import ValidationError
        
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError('La fecha de inicio debe ser anterior a la fecha de finalización.')
        
        if self.duration_minutes <= 0:
            raise ValidationError('La duración debe ser mayor a 0 minutos.')
        
        if self.duration_minutes > 480:
            raise ValidationError('La duración no puede exceder 8 horas.')
    
    class Meta:
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'


# Modelo para Unidades Temáticas
class UnidadTematica(models.Model):
    carrera = models.ForeignKey(
        'Carrera',
        related_name='unidades_tematicas',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        help_text='Carrera a la que pertenece esta unidad temática'
    )
    numero = models.PositiveSmallIntegerField(help_text='Número de la unidad (ej: 1, 2, 3...)')
    nombre = models.CharField(max_length=150, help_text='Nombre de la unidad temática')
    descripcion = models.TextField(blank=True, help_text='Descripción opcional de la unidad')

    class Meta:
        verbose_name = 'Unidad Temática'
        verbose_name_plural = 'Unidades Temáticas'
        ordering = ['carrera', 'numero']
        unique_together = ('carrera', 'numero')

    def __str__(self):
        carrera_name = f" [{self.carrera.siglas|default:self.carrera.nombre}]" if self.carrera else ""
        return f"Unidad {self.numero}: {self.nombre}{carrera_name}"


# Modelo intermedio para asignar cuotas dinámicas de Unidades Temáticas a cada Evaluación
class EvaluacionCuotaUnidad(models.Model):
    evaluacion = models.ForeignKey(
        Evaluacion,
        related_name='cuotas_unidades',
        on_delete=models.CASCADE
    )
    unidad = models.ForeignKey(
        UnidadTematica,
        related_name='cuotas_evaluaciones',
        on_delete=models.CASCADE
    )
    cantidad_preguntas = models.PositiveIntegerField(
        default=2,
        help_text='Cantidad de preguntas a seleccionar de esta unidad temática'
    )

    class Meta:
        verbose_name = 'Cuota de Unidad Temática'
        verbose_name_plural = 'Cuotas de Unidades Temáticas'
        unique_together = ('evaluacion', 'unidad')

    def __str__(self):
        return f"{self.evaluacion.title} - Unidad {self.unidad.numero}: {self.cantidad_preguntas} preguntas"


# Modelo para Temas (anteriormente Categorías)
class Tema(models.Model):
    unidad = models.ForeignKey(
        UnidadTematica,
        related_name='temas',
        on_delete=models.CASCADE,
        help_text='Unidad temática a la que pertenece el tema'
    )
    nombre = models.CharField(max_length=150, help_text='Nombre del tema (ej: Vectores, Leyes de Newton)')
    descripcion = models.TextField(blank=True, help_text='Descripción opcional del tema')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True, help_text='Si el tema está activo para su uso')

    class Meta:
        verbose_name = 'Tema'
        verbose_name_plural = 'Temas'
        ordering = ['unidad', 'nombre']
        unique_together = ('unidad', 'nombre')

    def __str__(self):
        if self.unidad:
            return f"U{self.unidad.numero} - {self.nombre}"
        return self.nombre

# Alias de compatibilidad hacia atrás
Categoria = Tema

# Modelo para las preguntas
class Pregunta(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, related_name='preguntas', on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, related_name='preguntas', on_delete=models.CASCADE, help_text='Categoría temática de la pregunta')
    text = models.TextField(help_text='Use LaTeX para fórmulas')
    puntos = models.PositiveIntegerField(default=1, help_text='Puntos que vale esta pregunta')

    def __str__(self):
        return self.text[:50]

# Modelo para las opciones de respuesta
class Opcion(models.Model):
    pregunta = models.ForeignKey(Pregunta, related_name='opciones', on_delete=models.CASCADE)
    text = models.TextField(help_text='Use LaTeX para fórmulas')
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

# Modelo para los resultados de las evaluaciones
class ResultadoEvaluacion(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='resultados')
    participante = models.ForeignKey(Participantes, on_delete=models.CASCADE, related_name='resultados')
    tiempo_utilizado = models.PositiveIntegerField(help_text='Tiempo utilizado en segundos', default=0)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    completada = models.BooleanField(default=False)
    
    # Campos para guardado automático
    respuestas_guardadas = models.JSONField(default=dict, blank=True, help_text='Respuestas guardadas automáticamente')
    tiempo_restante = models.PositiveIntegerField(help_text='Tiempo restante en segundos', default=0)
    ultima_actividad = models.DateTimeField(auto_now=True, help_text='Última actividad del estudiante')
    
    # Campos para puntaje numérico
    puntos_obtenidos = models.DecimalField(max_digits=5, decimal_places=3, default=0, help_text='Puntos obtenidos por el estudiante (ponderado sobre 10)')
    puntos_totales = models.PositiveIntegerField(default=10, help_text='Puntos totales de la evaluación (siempre 10)')
    
    # Campo para múltiples intentos
    numero_intento = models.PositiveIntegerField(default=1, help_text='Número del intento del participante')
    
    # Campo para control de cambios de pestaña y alertas anti-fraude
    cambios_pestana = models.PositiveIntegerField(default=0, help_text='Número de cambios de pestaña durante la evaluación')
    alertas_detectadas = models.JSONField(default=list, blank=True, help_text='Lista de alertas detectadas durante la prueba')
    
    # Control administrativo
    finalizado_por_admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='evaluaciones_finalizadas_admin',
        help_text='Administrador que finalizó la evaluación'
    )
    motivo_finalizacion = models.TextField(blank=True, help_text='Motivo de la finalización administrativa')
    fecha_finalizacion_admin = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['evaluacion', 'participante', 'numero_intento']
        ordering = ['-puntos_obtenidos', 'tiempo_utilizado']
    
    def get_tiempo_formateado(self):
        """Retorna el tiempo utilizado en formato legible"""
        total_sec = self.tiempo_utilizado
        if not total_sec and self.fecha_inicio and self.fecha_fin:
            total_sec = int((self.fecha_fin - self.fecha_inicio).total_seconds())
            
        total_sec = max(0, int(total_sec or 0))
        minutos, segundos = divmod(total_sec, 60)
        horas, minutos = divmod(minutos, 60)
        
        if horas > 0:
            return f"{horas}h {minutos}m {segundos}s"
        elif minutos > 0:
            return f"{minutos}m {segundos}s"
        return f"{segundos}s"
    
    def __str__(self):
        return f"{self.participante.NombresCompletos} - {self.evaluacion.title} ({self.puntos_obtenidos:.3f}/{self.puntos_totales})"
    
    def get_posicion_ranking(self):
        """Obtiene la posición en el ranking de la evaluación"""
        resultados = self.evaluacion.resultados.filter(completada=True).order_by('-puntos_obtenidos', 'tiempo_utilizado')
        for i, resultado in enumerate(resultados, 1):
            if resultado == self:
                return i
        return None
    
    def get_puntaje_numerico(self):
        """Retorna el puntaje ponderado en formato numérico (ej: 8.500/10)"""
        return f"{self.puntos_obtenidos:.3f}/{self.puntos_totales}"
    
    @classmethod
    def get_mejor_resultado(cls, evaluacion, participante):
        """Obtiene el mejor resultado de un participante en una evaluación específica"""
        return cls.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado').first()
    
    @classmethod
    def get_siguiente_numero_intento(cls, evaluacion, participante):
        """Obtiene el siguiente número de intento para un participante en una evaluación"""
        ultimo_resultado = cls.objects.filter(
            evaluacion=evaluacion,
            participante=participante
        ).order_by('-numero_intento').first()
        
        return (ultimo_resultado.numero_intento + 1) if ultimo_resultado else 1

    def get_snapshot_respuestas(self):
        """Retorna la lista de preguntas congeladas si el examen está completado y tiene snapshot"""
        if self.completada and isinstance(self.respuestas_guardadas, dict):
            return self.respuestas_guardadas.get('preguntas_snapshot')
        return None

    def agregar_alerta(self, tipo_alerta, descripcion, severidad='baja'):
        """Agrega una nueva alerta de auditoría al resultado del examen"""
        alerta = {
            'tipo': tipo_alerta,
            'descripcion': descripcion,
            'severidad': severidad,
            'timestamp': timezone.now().isoformat()
        }
        if self.alertas_detectadas is None:
            self.alertas_detectadas = []
        self.alertas_detectadas.append(alerta)
        # Una acción administrativa no representa actividad del estudiante.
        self.save(update_fields=['alertas_detectadas'])

    def finalizar_por_admin(self, admin_user, motivo):
        """Finaliza la evaluación por decisión administrativa"""
        with transaction.atomic():
            self.puntos_obtenidos = 0
            self.puntos_totales = 10
            self.completada = True
            self.fecha_fin = timezone.now()
            self.tiempo_restante = 0
            self.finalizado_por_admin = admin_user
            self.motivo_finalizacion = motivo
            self.fecha_finalizacion_admin = timezone.now()
            self.agregar_alerta(
                'finalizado_por_admin',
                f'Evaluación finalizada administrativamente por {admin_user.username}. Motivo: {motivo}',
                severidad='alta'
            )
            self.save()

    def esta_activo(self):
        """Verifica si el estudiante ha registrado actividad reciente (últimos 5 minutos)"""
        if self.completada:
            return False
        if not self.ultima_actividad:
            return False
        return (timezone.now() - self.ultima_actividad).total_seconds() < 300

    def get_estado_display_color(self):
        """Retorna la clase de color CSS para el estado"""
        if self.completada:
            return 'secondary'
        elif self.esta_activo():
            return 'success'
        return 'warning'

class SolicitudClaveTemporal(models.Model):
    """
    Modelo para rastrear las solicitudes de clave temporal
    Permite validar que un usuario no envíe más de 3 solicitudes por semana
    """
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('participante', 'Participante'),
    ]
    
    # Información del usuario que solicita
    username = models.CharField(max_length=150, help_text='Nombre de usuario o cédula del solicitante')
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, help_text='Tipo de usuario que solicita')
    email = models.EmailField(help_text='Correo electrónico del usuario')
    
    # Información de la solicitud
    fecha_solicitud = models.DateTimeField(auto_now_add=True, help_text='Fecha y hora de la solicitud')
    
    # Estado de la solicitud
    procesada = models.BooleanField(default=False, help_text='Indica si la solicitud fue procesada exitosamente')
    mensaje_error = models.TextField(blank=True, help_text='Mensaje de error si la solicitud falló')
    
    class Meta:
        verbose_name = 'Solicitud de Clave Temporal'
        verbose_name_plural = 'Solicitudes de Clave Temporal'
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['username', 'fecha_solicitud']),
            models.Index(fields=['tipo_usuario', 'fecha_solicitud']),
        ]
    
    def __str__(self):
        return f"Solicitud de {self.username} ({self.tipo_usuario}) - {self.fecha_solicitud.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def contar_solicitudes_semana(cls, username, tipo_usuario):
        """
        Cuenta las solicitudes de un usuario en la última semana
        """
        una_semana_atras = timezone.now() - timezone.timedelta(days=7)
        return cls.objects.filter(
            username=username,
            tipo_usuario=tipo_usuario,
            fecha_solicitud__gte=una_semana_atras
        ).count()
    
    @classmethod
    def puede_solicitar(cls, username, tipo_usuario):
        """
        Verifica si un usuario puede solicitar una nueva clave temporal
        (máximo 3 solicitudes por semana)
        """
        return cls.contar_solicitudes_semana(username, tipo_usuario) < 3


# Modelo de Auditoría para registro de acciones administrativas e imborrables
class AuditLog(models.Model):
    usuario_ejecutor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acciones_auditoria')
    accion = models.CharField(max_length=100, help_text='Tipo de acción realizada (ej. ELIMINACION_ADMINISTRADOR)')
    detalles = models.TextField(help_text='Detalles completos de la acción y la entidad afectada')
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text='Dirección IP del cliente')
    fecha_hora = models.DateTimeField(auto_now_add=True, help_text='Fecha y hora del registro')

    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'

    def __str__(self):
        ejecutor = self.usuario_ejecutor.username if self.usuario_ejecutor else 'Sistema'
        return f"[{self.fecha_hora.strftime('%Y-%m-%d %H:%M:%S')}] {ejecutor} - {self.accion}"

    @classmethod
    def registrar_accion(cls, usuario_ejecutor, accion, detalles, request=None):
        """Registra de forma segura una acción en la bitácora de auditoría."""
        ip = None
        if request:
            ip = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip:
                ip = ip.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
        return cls.objects.create(
            usuario_ejecutor=usuario_ejecutor,
            accion=accion,
            detalles=detalles,
            ip_address=ip
        )


