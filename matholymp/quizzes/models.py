from django.contrib.auth.models import User
from django.db import models, transaction, IntegrityError
from django.utils.crypto import get_random_string
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
import os
from datetime import datetime

# Configuración global del sistema
class SystemConfig(models.Model):
    NUM_ETAPAS_CHOICES = [
        (2, 'Dos etapas'),
        (3, 'Tres etapas'),
    ]
    num_etapas = models.IntegerField(choices=NUM_ETAPAS_CHOICES, default=3, help_text='Cantidad de etapas del concurso')
    active_year = models.IntegerField(default=datetime.now().year, help_text='Año activo del concurso')

    class Meta:
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuración del Sistema'

    def __str__(self):
        return f"Config: {self.num_etapas} etapas, año {self.active_year}"

    @classmethod
    def get_num_etapas(cls) -> int:
        try:
            obj = cls.objects.first()
            return obj.num_etapas if obj else 3
        except Exception:
            # Si la tabla aún no existe o hay cualquier problema, usar 3 por defecto
            return 3

    @classmethod
    def get_active_year(cls) -> int:
        try:
            obj = cls.objects.first()
            return obj.active_year if obj else datetime.now().year
        except Exception:
            return datetime.now().year

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
                    password_temporal=password,
                )

                # Aquí se puede agregar lógica para enviar el correo con la contraseña
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
    
    title = models.CharField(max_length=200)
    etapa = models.IntegerField(choices=ETAPA_CHOICES, default=1, help_text='Etapa de la olimpiada')
    start_time = models.DateTimeField(help_text='Fecha y hora de inicio de la ventana de acceso')
    end_time = models.DateTimeField(help_text='Fecha y hora de finalización de la ventana de acceso')
    duration_minutes = models.PositiveIntegerField(help_text='Tiempo disponible para completar la evaluación (en minutos)')
    anio = models.IntegerField(default=datetime.now().year, help_text='Año del concurso al que pertenece esta evaluación')
    
    # Nuevo campo para configurar preguntas
    preguntas_a_mostrar = models.PositiveIntegerField(
        default=10, 
        help_text='Número de preguntas que se mostrarán al estudiante (selección aleatoria)'
    )
    
    # Campo para configurar intentos permitidos por defecto
    intentos_permitidos_default = models.PositiveIntegerField(
        default=1,
        help_text='Número de intentos permitidos por defecto para todos los participantes'
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
        """Obtiene los mejores de la etapa 1 según configuración (15 si hay 3 etapas, 5 si hay 2)."""
        if self.etapa != 2:
            return []
        
        # Buscar la evaluación de la etapa 1
        evaluacion_etapa1 = Evaluacion.objects.filter(etapa=1, anio=self.anio).first()
        if not evaluacion_etapa1:
            return []
        
        # Determinar cuántos pasan desde etapa 1
        from .models import SystemConfig
        num_etapas = SystemConfig.get_num_etapas()
        top_n = 15 if num_etapas == 3 else 5

        # Obtener los mejores resultados de la etapa 1
        mejores_resultados = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa1,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado')[:top_n]
        
        return [resultado.participante for resultado in mejores_resultados]
    
    def get_participantes_etapa3(self):
        """Obtiene los 5 mejores de la etapa 2 (flujo actual) o directamente de etapa 1 si hay solo 2 etapas."""
        if self.etapa != 3:
            return []
        
        from .models import SystemConfig
        num_etapas = SystemConfig.get_num_etapas()
        
        if num_etapas == 3:
            # Flujo actual: top 5 desde etapa 2
            evaluacion_etapa2 = Evaluacion.objects.filter(etapa=2, anio=self.anio).first()
            if not evaluacion_etapa2:
                return []
            mejores_resultados = ResultadoEvaluacion.objects.filter(
                evaluacion=evaluacion_etapa2,
                completada=True
            ).order_by('-puntos_obtenidos', 'tiempo_utilizado')[:5]
        else:
            # Flujo de 2 etapas: tomar top 5 directamente desde etapa 1 (saltando etapa 2)
            evaluacion_etapa1 = Evaluacion.objects.filter(etapa=1, anio=self.anio).first()
            if not evaluacion_etapa1:
                return []
            mejores_resultados = ResultadoEvaluacion.objects.filter(
                evaluacion=evaluacion_etapa1,
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
    
    def get_o_crear_intento_participante(self, participante, usuario_modificador=None):
        """Obtiene o crea el registro de intentos para un participante específico"""
        intento, created = IntentoEvaluacion.objects.get_or_create(
            evaluacion=self,
            participante=participante,
            defaults={
                'intentos_permitidos': self.intentos_permitidos_default,
                'modificado_por': usuario_modificador
            }
        )
        return intento
    
    def puede_participante_realizar_intento(self, participante):
        """Verifica si un participante puede realizar otro intento en esta evaluación"""
        intento = self.get_o_crear_intento_participante(participante)
        return intento.puede_realizar_intento()
    
    def incrementar_intentos_participante(self, participante, nuevos_intentos, usuario_modificador):
        """Incrementa los intentos permitidos para un participante específico"""
        intento = self.get_o_crear_intento_participante(participante, usuario_modificador)
        intento.intentos_permitidos = nuevos_intentos
        intento.modificado_por = usuario_modificador
        intento.save()
        return intento
    
    def obtener_siguiente_numero_intento(self, participante):
        """Obtiene el siguiente número de intento para un participante"""
        ultimo_intento = ResultadoEvaluacion.objects.filter(
            evaluacion=self,
            participante=participante
        ).order_by('-numero_intento').first()
        
        if ultimo_intento:
            return ultimo_intento.numero_intento + 1
        return 1
    
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
    text = models.TextField(help_text='Use LaTeX para fórmulas')
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

# Modelo para manejar los intentos específicos de cada participante en cada evaluación
class IntentoEvaluacion(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='intentos_participantes')
    participante = models.ForeignKey(Participantes, on_delete=models.CASCADE, related_name='intentos_evaluacion')
    intentos_permitidos = models.PositiveIntegerField(
        default=1,
        help_text='Número de intentos permitidos para este participante en esta evaluación específica'
    )
    intentos_utilizados = models.PositiveIntegerField(
        default=0,
        help_text='Número de intentos que ha realizado el participante'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Usuario que modificó los intentos de este participante'
    )
    
    class Meta:
        unique_together = ['evaluacion', 'participante']
        verbose_name = 'Intento de Evaluación'
        verbose_name_plural = 'Intentos de Evaluaciones'
    
    def __str__(self):
        return f"{self.participante.NombresCompletos} - {self.evaluacion.title} ({self.intentos_utilizados}/{self.intentos_permitidos})"
    
    def puede_realizar_intento(self):
        """Verifica si el participante puede realizar otro intento"""
        return self.intentos_utilizados < self.intentos_permitidos
    
    def registrar_nuevo_intento(self):
        """Incrementa el contador de intentos utilizados"""
        if self.puede_realizar_intento():
            self.intentos_utilizados += 1
            self.save()
            return True
        return False

# Modelo para los resultados de las evaluaciones
class ResultadoEvaluacion(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='resultados')
    participante = models.ForeignKey(Participantes, on_delete=models.CASCADE, related_name='resultados')
    numero_intento = models.PositiveIntegerField(default=1, help_text='Número del intento (1, 2, 3, etc.)')
    puntaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tiempo_utilizado = models.PositiveIntegerField(help_text='Tiempo utilizado en minutos', default=0)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    completada = models.BooleanField(default=False)
    es_mejor_intento = models.BooleanField(default=True, help_text='Indica si este es el mejor intento del participante')
    
    # Campos para guardado automático
    respuestas_guardadas = models.JSONField(default=dict, blank=True, help_text='Respuestas guardadas automáticamente')
    tiempo_restante = models.PositiveIntegerField(help_text='Tiempo restante en segundos', default=0)
    ultima_actividad = models.DateTimeField(auto_now=True, help_text='Última actividad del estudiante')
    
    # Nuevos campos para puntaje numérico
    puntos_obtenidos = models.DecimalField(max_digits=5, decimal_places=3, default=0, help_text='Puntos obtenidos por el estudiante (ponderado sobre 10)')
    puntos_totales = models.PositiveIntegerField(default=10, help_text='Puntos totales de la evaluación (siempre 10)')
    
    class Meta:
        unique_together = ['evaluacion', 'participante', 'numero_intento']
        ordering = ['-puntos_obtenidos', 'tiempo_utilizado']
    
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
    
    def actualizar_mejor_intento(self):
        """Actualiza qué resultado es el mejor intento para este participante en esta evaluación"""
        # Obtener todos los intentos completados de este participante en esta evaluación
        intentos = ResultadoEvaluacion.objects.filter(
            evaluacion=self.evaluacion,
            participante=self.participante,
            completada=True
        ).order_by('-puntos_obtenidos', 'tiempo_utilizado')
        
        # Marcar todos como no mejor intento
        ResultadoEvaluacion.objects.filter(
            evaluacion=self.evaluacion,
            participante=self.participante
        ).update(es_mejor_intento=False)
        
        # Marcar el mejor como mejor intento
        if intentos.exists():
            mejor_intento = intentos.first()
            mejor_intento.es_mejor_intento = True
            mejor_intento.save()  # Ahora es seguro porque ya está completada
    
    @classmethod
    def get_mejor_resultado_participante(cls, evaluacion, participante):
        """Obtiene el mejor resultado de un participante en una evaluación específica"""
        return cls.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            completada=True,
            es_mejor_intento=True
        ).first()
    
    def save(self, *args, **kwargs):
        # Obtener el estado anterior para comparar
        es_nuevo = self.pk is None
        completada_antes = False
        
        if not es_nuevo:
            try:
                estado_anterior = ResultadoEvaluacion.objects.get(pk=self.pk)
                completada_antes = estado_anterior.completada
            except ResultadoEvaluacion.DoesNotExist:
                completada_antes = False
        
        # Guardar el objeto
        super().save(*args, **kwargs)
        
        # Solo actualizar mejor intento si se acaba de completar (no estaba completada antes)
        if self.completada and not completada_antes:
            self.actualizar_mejor_intento()

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
        """Retorna el porcentaje de avance basado en preguntas respondidas del total de preguntas mostradas al participante"""
        try:
            # Obtener las preguntas que se muestran específicamente a este participante
            preguntas_mostradas = self.evaluacion.get_preguntas_para_estudiante(self.participante.id)
            total_preguntas_mostradas = len(preguntas_mostradas) if preguntas_mostradas else 0
            
            if total_preguntas_mostradas > 0:
                return round((self.preguntas_respondidas / total_preguntas_mostradas) * 100, 1)
            return 0
        except Exception:
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
        with transaction.atomic():
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

