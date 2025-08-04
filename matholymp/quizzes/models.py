from django.contrib.auth.models import User
from django.db import models
from django.utils.crypto import get_random_string
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
import os
from datetime import datetime

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
    NombreColegio = models.CharField(max_length=200)
    DireccionColegio = models.CharField(max_length=300)
    TelefonoInstitucional = models.CharField(max_length=10, validators=[validate_phone])
    CorreoInstitucional = models.EmailField(unique=True, help_text='Correo institucional único')
    NombresRepresentante = models.CharField(max_length=200)
    TelefonoRepresentante = models.CharField(max_length=10, validators=[validate_phone])
    CorreoRepresentante = models.EmailField(unique=True, help_text='Correo del representante único')

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

# Modelo para grupos de participantes
class GrupoParticipantes(models.Model):
    name = models.CharField(max_length=100)
    representante = models.ForeignKey(Representante, on_delete=models.SET_NULL, null=True, blank=True, related_name='grupos')
    participantes = models.ManyToManyField('Participantes', related_name='grupos', blank=True)

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
    email = models.EmailField(unique=True, help_text='Correo electrónico único')
    phone = models.CharField(max_length=10, blank=True, validators=[validate_phone])
    edad = models.IntegerField(null=True, blank=True)
    password_temporal = models.CharField(max_length=50, blank=True, help_text='Contraseña temporal para mostrar en correos')

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

    @staticmethod
    def create_participant(cedula, NombresCompletos, email, phone=None, edad=None):
        # Validar que el correo no esté duplicado antes de crear
        email_normalized = email.lower().strip()
        
        # Verificar si ya existe un participante con este correo
        if Participantes.objects.filter(email__iexact=email_normalized).exists():
            raise ValidationError(f'Ya existe un participante con el correo "{email}".')
        
        # Verificar si el correo está siendo usado por un representante
        if Representante.objects.filter(
            models.Q(CorreoInstitucional__iexact=email_normalized) |
            models.Q(CorreoRepresentante__iexact=email_normalized)
        ).exists():
            raise ValidationError(f'El correo "{email}" ya está siendo usado por un representante.')
        
        password = get_random_string(length=6)
        user = User.objects.create_user(username=cedula, password=password, first_name=NombresCompletos, email=email_normalized)
        participante = Participantes.objects.create(
            user=user, 
            cedula=cedula, 
            NombresCompletos=NombresCompletos, 
            email=email_normalized, 
            phone=phone or "", 
            edad=edad,
            password_temporal=password  # Guardar la contraseña temporal
        )
        # Aquí se puede agregar lógica para enviar el correo con la contraseña
        return participante, password

# Modelo Evaluacion para las evaluaciones
class Evaluacion(models.Model):
    ETAPA_CHOICES = [
        (1, 'Etapa 1 - Clasificatoria'),
        (2, 'Etapa 2 - Semifinal'),
        (3, 'Etapa 3 - Final'),
    ]
    
    title = models.CharField(max_length=200)
    etapa = models.IntegerField(choices=ETAPA_CHOICES, default=1, help_text='Etapa de la olimpiada')
    start_time = models.DateTimeField(help_text='Fecha y hora de inicio de la ventana de acceso')
    end_time = models.DateTimeField(help_text='Fecha y hora de finalización de la ventana de acceso')
    duration_minutes = models.PositiveIntegerField(help_text='Tiempo disponible para completar la evaluación (en minutos)')
    
    # Nuevo campo para configurar preguntas
    preguntas_a_mostrar = models.PositiveIntegerField(
        default=10, 
        help_text='Número de preguntas que se mostrarán al estudiante (selección aleatoria)'
    )
    
    # Campos para participantes de la etapa 1
    grupos_participantes = models.ManyToManyField('GrupoParticipantes', blank=True, related_name='evaluaciones_etapa1')
    participantes_individuales = models.ManyToManyField('Participantes', blank=True, related_name='evaluaciones_individuales')

    def __str__(self):
        return f"{self.title} - Etapa {self.etapa}"
    
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
        """Obtiene los 15 mejores de la etapa 1"""
        if self.etapa != 2:
            return []
        
        # Buscar la evaluación de la etapa 1
        evaluacion_etapa1 = Evaluacion.objects.filter(etapa=1).first()
        if not evaluacion_etapa1:
            return []
        
        # Obtener los 15 mejores resultados de la etapa 1
        mejores_resultados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa1,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado')[:15]
        
        return [resultado.participante for resultado in mejores_resultados]
    
    def get_participantes_etapa3(self):
        """Obtiene los 5 mejores de la etapa 2"""
        if self.etapa != 3:
            return []
        
        # Buscar la evaluación de la etapa 2
        evaluacion_etapa2 = Evaluacion.objects.filter(etapa=2).first()
        if not evaluacion_etapa2:
            return []
        
        # Obtener los 5 mejores resultados de la etapa 2
        mejores_resultados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa2,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado')[:5]
        
        return [resultado.participante for resultado in mejores_resultados]
    
    def get_participantes_autorizados(self):
        """Obtiene los participantes autorizados según la etapa"""
        if self.etapa == 1:
            return self.get_participantes_etapa1()
        elif self.etapa == 2:
            return self.get_participantes_etapa2()
        elif self.etapa == 3:
            return self.get_participantes_etapa3()
        return []
    
    def get_preguntas_aleatorias(self):
        """Obtiene preguntas aleatorias según la configuración"""
        total_preguntas = self.preguntas.count()
        if total_preguntas == 0:
            return []
        
        # Si hay menos preguntas que las configuradas, mostrar todas
        if total_preguntas <= self.preguntas_a_mostrar:
            return list(self.preguntas.prefetch_related('opciones').all())
        
        # Obtener preguntas aleatorias
        return list(self.preguntas.prefetch_related('opciones').order_by('?')[:self.preguntas_a_mostrar])
    
    def get_preguntas_para_estudiante(self, participante_id):
        """Obtiene preguntas específicas para un estudiante (consistente)"""
        import hashlib
        
        total_preguntas = self.preguntas.count()
        if total_preguntas == 0:
            return []
        
        # Si hay menos preguntas que las configuradas, mostrar todas
        if total_preguntas <= self.preguntas_a_mostrar:
            return list(self.preguntas.prefetch_related('opciones').all())
        
        # Usar hash del participante para selección consistente pero aleatoria
        hash_participante = hashlib.md5(f"{self.id}_{participante_id}".encode()).hexdigest()
        seed = int(hash_participante[:8], 16)
        
        # Obtener todas las preguntas ordenadas por ID
        todas_preguntas = list(self.preguntas.prefetch_related('opciones').order_by('id'))
        
        # Seleccionar preguntas usando el seed
        import random
        random.seed(seed)
        preguntas_seleccionadas = random.sample(todas_preguntas, min(self.preguntas_a_mostrar, len(todas_preguntas)))
        
        return preguntas_seleccionadas
    
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
    puntos = models.PositiveIntegerField(default=1, help_text='Puntos que vale esta pregunta')

    def __str__(self):
        return self.text[:50]

# Modelo para las opciones de respuesta
class Opcion(models.Model):
    pregunta = models.ForeignKey(Pregunta, related_name='opciones', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

# Modelo para los resultados de las evaluaciones
class ResultadoEvaluacion(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='resultados')
    participante = models.ForeignKey(Participantes, on_delete=models.CASCADE, related_name='resultados')
    puntaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tiempo_utilizado = models.PositiveIntegerField(help_text='Tiempo utilizado en minutos', default=0)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    completada = models.BooleanField(default=False)
    
    # Campos para guardado automático
    respuestas_guardadas = models.JSONField(default=dict, blank=True, help_text='Respuestas guardadas automáticamente')
    tiempo_restante = models.PositiveIntegerField(help_text='Tiempo restante en segundos', default=0)
    ultima_actividad = models.DateTimeField(auto_now=True, help_text='Última actividad del estudiante')
    
    # Nuevos campos para puntaje numérico
    puntos_obtenidos = models.DecimalField(max_digits=5, decimal_places=3, default=0, help_text='Puntos obtenidos por el estudiante (ponderado sobre 10)')
    puntos_totales = models.PositiveIntegerField(default=10, help_text='Puntos totales de la evaluación (siempre 10)')
    
    class Meta:
        unique_together = ['evaluacion', 'participante']
        ordering = ['-puntaje', 'tiempo_utilizado']
    
    def get_tiempo_formateado(self):
        """Retorna el tiempo utilizado en formato legible"""
        if self.fecha_inicio and self.fecha_fin:
            # Calcular tiempo real utilizado
            tiempo_total = (self.fecha_fin - self.fecha_inicio).total_seconds()
            minutos = int(tiempo_total // 60)
            segundos = int(tiempo_total % 60)
            
            if minutos > 0:
                return f"{minutos}m {segundos}s"
            else:
                return f"{segundos}s"
        elif self.tiempo_utilizado:
            # Fallback al tiempo guardado
            horas = self.tiempo_utilizado // 60
            minutos = self.tiempo_utilizado % 60
            
            if horas > 0:
                return f"{horas}h {minutos}m"
            else:
                return f"{minutos}m"
        return "0m"
    
    def __str__(self):
        return f"{self.participante.NombresCompletos} - {self.evaluacion.title} ({self.puntaje}%)"
    
    def get_posicion_ranking(self):
        """Obtiene la posición en el ranking de la evaluación"""
        resultados = self.evaluacion.resultados.filter(completada=True).order_by('-puntos_obtenidos', 'tiempo_utilizado')
        for i, resultado in enumerate(resultados, 1):
            if resultado == self:
                return i
        return None
    
    def get_puntaje_numerico(self):
        """Retorna el puntaje ponderado en formato numérico (ej: 8.500/10)"""
        if self.puntos_totales > 0:
            # Formatear con 3 decimales para mostrar el puntaje ponderado
            return f"{self.puntos_obtenidos:.3f}/{self.puntos_totales}"
        return "0.000/0"
    
    def get_puntaje_porcentaje(self):
        """Retorna el puntaje como porcentaje"""
        if self.puntos_totales > 0:
            return (self.puntos_obtenidos / self.puntos_totales) * 100
        return 0

# Modelo para el monitoreo en tiempo real de evaluaciones
class MonitoreoEvaluacion(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado'),
        ('suspendido', 'Suspendido'),
    ]
    
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='monitoreos')
    participante = models.ForeignKey(Participantes, on_delete=models.CASCADE, related_name='monitoreos')
    resultado = models.OneToOneField(ResultadoEvaluacion, on_delete=models.CASCADE, related_name='monitoreo', null=True, blank=True)
    
    # Estado del monitoreo
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    
    # Información de actividad
    ultima_actividad = models.DateTimeField(auto_now=True)
    tiempo_activo = models.PositiveIntegerField(default=0, help_text='Tiempo activo en segundos')
    tiempo_inactivo = models.PositiveIntegerField(default=0, help_text='Tiempo inactivo en segundos')
    
    # Información de navegación
    pagina_actual = models.PositiveIntegerField(default=1, help_text='Página actual del estudiante')
    preguntas_respondidas = models.PositiveIntegerField(default=0, help_text='Número de preguntas respondidas')
    preguntas_revisadas = models.PositiveIntegerField(default=0, help_text='Número de preguntas revisadas')
    
    # Alertas y irregularidades
    alertas_detectadas = models.JSONField(default=list, blank=True, help_text='Lista de alertas detectadas')
    irregularidades = models.TextField(blank=True, help_text='Descripción de irregularidades detectadas')
    
    # Control administrativo
    finalizado_por_admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='evaluaciones_finalizadas',
        help_text='Administrador que finalizó la evaluación'
    )
    motivo_finalizacion = models.TextField(blank=True, help_text='Motivo de la finalización administrativa')
    fecha_finalizacion_admin = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    fecha_inicio_monitoreo = models.DateTimeField(auto_now_add=True)
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['evaluacion', 'participante']
        ordering = ['-fecha_ultima_actualizacion']
        verbose_name = 'Monitoreo de Evaluación'
        verbose_name_plural = 'Monitoreos de Evaluaciones'
    
    def __str__(self):
        return f"Monitoreo: {self.participante.NombresCompletos} - {self.evaluacion.title}"
    
    def get_tiempo_total_activo(self):
        """Retorna el tiempo total activo en formato legible"""
        horas = self.tiempo_activo // 3600
        minutos = (self.tiempo_activo % 3600) // 60
        segundos = self.tiempo_activo % 60
        
        if horas > 0:
            return f"{horas}h {minutos}m {segundos}s"
        elif minutos > 0:
            return f"{minutos}m {segundos}s"
        else:
            return f"{segundos}s"
    
    def get_tiempo_total_inactivo(self):
        """Retorna el tiempo total inactivo en formato legible"""
        horas = self.tiempo_inactivo // 3600
        minutos = (self.tiempo_inactivo % 3600) // 60
        segundos = self.tiempo_inactivo % 60
        
        if horas > 0:
            return f"{horas}h {minutos}m {segundos}s"
        elif minutos > 0:
            return f"{minutos}m {segundos}s"
        else:
            return f"{segundos}s"
    
    def get_porcentaje_avance(self):
        """Retorna el porcentaje de avance basado en preguntas respondidas"""
        if self.preguntas_revisadas > 0:
            return (self.preguntas_respondidas / self.preguntas_revisadas) * 100
        return 0
    
    def agregar_alerta(self, tipo_alerta, descripcion, severidad='baja'):
        """Agrega una nueva alerta al monitoreo"""
        alerta = {
            'tipo': tipo_alerta,
            'descripcion': descripcion,
            'severidad': severidad,
            'timestamp': timezone.now().isoformat()
        }
        self.alertas_detectadas.append(alerta)
        self.save()
    
    def finalizar_por_admin(self, admin_user, motivo):
        """Finaliza la evaluación por decisión administrativa"""
        self.estado = 'finalizado'
        self.finalizado_por_admin = admin_user
        self.motivo_finalizacion = motivo
        self.fecha_finalizacion_admin = timezone.now()
        
        # Obtener o crear el resultado de evaluación
        if not self.resultado:
            self.resultado, created = ResultadoEvaluacion.objects.get_or_create(
                evaluacion=self.evaluacion,
                participante=self.participante,
                defaults={
                    'puntaje': 0,
                    'puntos_obtenidos': 0,
                    'puntos_totales': 10,
                    'tiempo_utilizado': 0,
                    'completada': True,
                    'fecha_fin': timezone.now(),
                    'tiempo_restante': 0
                }
            )
        else:
            # Si ya existe un resultado, asignar nota de 0 por finalización administrativa
            self.resultado.puntaje = 0
            self.resultado.puntos_obtenidos = 0
            self.resultado.puntos_totales = 10
            self.resultado.completada = True
            self.resultado.fecha_fin = timezone.now()
            self.resultado.tiempo_restante = 0
            self.resultado.save()
        
        self.save()
    
    def esta_activo(self):
        """Verifica si el estudiante está activo (última actividad en los últimos 5 minutos)"""
        tiempo_limite = timezone.now() - timezone.timedelta(minutes=5)
        return self.ultima_actividad > tiempo_limite
    
    def get_estado_display_color(self):
        """Retorna el color CSS para el estado"""
        if self.estado == 'activo':
            return 'success' if self.esta_activo() else 'warning'
        elif self.estado == 'finalizado':
            return 'secondary'
        elif self.estado == 'suspendido':
            return 'danger'
        return 'info'

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

