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
    cedula = models.CharField(max_length=10, unique=True, validators=[validate_cedula])
    NombresCompletos = models.CharField(max_length=200)
    email = models.EmailField(unique=True, help_text='Correo electrónico único')
    phone = models.CharField(max_length=10, blank=True, validators=[validate_phone])
    edad = models.IntegerField(null=True, blank=True)
    password_temporal = models.CharField(max_length=50, blank=True, help_text='Contraseña temporal para mostrar en correos')
    
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

        # Usar la misma lógica que el ranking: obtener el mejor puntaje por participante
        from django.db.models import Max
        
        # Primero, obtener el mejor puntaje por participante
        mejores_puntajes = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion_etapa1,
            completada=True
        ).values('participante').annotate(
            mejor_puntaje=Max('puntos_obtenidos')
        )
        
        # Crear una lista de participantes con sus mejores puntajes
        participantes_con_mejor_puntaje = []
        for item in mejores_puntajes:
            participante_id = item['participante']
            mejor_puntaje = item['mejor_puntaje']
            
            # Obtener todos los intentos con el mejor puntaje para este participante
            intentos_con_mejor_puntaje = ResultadoEvaluacion.objects.filter(
                evaluacion=evaluacion_etapa1,
                participante_id=participante_id,
                completada=True,
                puntos_obtenidos=mejor_puntaje,
                fecha_inicio__isnull=False,
                fecha_fin__isnull=False
            )
            
            # De los intentos con el mejor puntaje, seleccionar el más rápido (menor tiempo real)
            mejor_resultado = None
            menor_tiempo = float('inf')
            
            for intento in intentos_con_mejor_puntaje:
                tiempo_real = (intento.fecha_fin - intento.fecha_inicio).total_seconds()
                if tiempo_real < menor_tiempo:
                    menor_tiempo = tiempo_real
                    mejor_resultado = intento
            
            if mejor_resultado:
                participantes_con_mejor_puntaje.append(mejor_resultado)
        
        # Ordenar por puntaje descendente y tiempo real ascendente (igual que el ranking)
        def get_tiempo_real(resultado):
            if resultado.fecha_inicio and resultado.fecha_fin:
                return (resultado.fecha_fin - resultado.fecha_inicio).total_seconds()
            return float('inf')  # Si no tiene fechas, lo colocamos al final
        
        resultados_ordenados = sorted(participantes_con_mejor_puntaje, key=lambda x: (-x.puntos_obtenidos, get_tiempo_real(x)))
        
        # Tomar solo los mejores según la configuración
        mejores_resultados = resultados_ordenados[:top_n]
        
        return [resultado.participante for resultado in mejores_resultados]
    
    def has_students_taking_exam(self):
        """Verifica si hay estudiantes que están actualmente rindiendo la evaluación"""
        # Si la evaluación no está guardada en la BD, no puede tener estudiantes rindiendo
        if not self.pk:
            return False
            
        # Un estudiante está rindiendo si tiene un ResultadoEvaluacion no completado y activo
        from django.utils import timezone
        now = timezone.now()
        
        # Verificar si hay resultados activos (no completados) donde la última actividad
        # fue hace menos de 1 hora (consideramos que aún está activo)
        resultados_activos = self.resultados.filter(
            completada=False,
            fecha_inicio__isnull=False,
            ultima_actividad__gte=now - timezone.timedelta(hours=1)
        )
        
        return resultados_activos.exists()
    
    def can_modify_questions(self):
        """
        Verifica si se pueden modificar las preguntas del banco de la evaluación.
        No se puede modificar si:
        1. La evaluación está en estado "Disponible" (activa)
        2. Hay estudiantes rindiendo actualmente
        """
        # Si la evaluación está disponible (activa)
        if self.is_available():
            return False
        
        # Si hay estudiantes rindiendo
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
        
        from .models import SystemConfig
        num_etapas = SystemConfig.get_num_etapas()
        
        if num_etapas == 3:
            # Flujo actual: top 5 desde etapa 2
            evaluacion_etapa2 = Evaluacion.objects.filter(etapa=2, anio=self.anio).first()
            if not evaluacion_etapa2:
                return []
            
            # Usar la misma lógica que el ranking: obtener el mejor puntaje por participante
            from django.db.models import Max
            
            # Primero, obtener el mejor puntaje por participante
            mejores_puntajes = ResultadoEvaluacion.objects.filter(
                evaluacion=evaluacion_etapa2,
                completada=True
            ).values('participante').annotate(
                mejor_puntaje=Max('puntos_obtenidos')
            )
            
            # Crear una lista de participantes con sus mejores puntajes
            participantes_con_mejor_puntaje = []
            for item in mejores_puntajes:
                participante_id = item['participante']
                mejor_puntaje = item['mejor_puntaje']
                
                # Obtener todos los intentos con el mejor puntaje para este participante
                intentos_con_mejor_puntaje = ResultadoEvaluacion.objects.filter(
                    evaluacion=evaluacion_etapa2,
                    participante_id=participante_id,
                    completada=True,
                    puntos_obtenidos=mejor_puntaje,
                    fecha_inicio__isnull=False,
                    fecha_fin__isnull=False
                )
                
                # De los intentos con el mejor puntaje, seleccionar el más rápido (menor tiempo real)
                mejor_resultado = None
                menor_tiempo = float('inf')
                
                for intento in intentos_con_mejor_puntaje:
                    tiempo_real = (intento.fecha_fin - intento.fecha_inicio).total_seconds()
                    if tiempo_real < menor_tiempo:
                        menor_tiempo = tiempo_real
                        mejor_resultado = intento
                
                if mejor_resultado:
                    participantes_con_mejor_puntaje.append(mejor_resultado)
            
            # Ordenar por puntaje descendente y tiempo real ascendente (igual que el ranking)
            def get_tiempo_real(resultado):
                if resultado.fecha_inicio and resultado.fecha_fin:
                    return (resultado.fecha_fin - resultado.fecha_inicio).total_seconds()
                return float('inf')  # Si no tiene fechas, lo colocamos al final
            
            resultados_ordenados = sorted(participantes_con_mejor_puntaje, key=lambda x: (-x.puntos_obtenidos, get_tiempo_real(x)))
            
            # Tomar solo los mejores 5
            mejores_resultados = resultados_ordenados[:5]
            
        else:
            # Flujo de 2 etapas: tomar top 5 directamente desde etapa 1 (saltando etapa 2)
            evaluacion_etapa1 = Evaluacion.objects.filter(etapa=1, anio=self.anio).first()
            if not evaluacion_etapa1:
                return []
            
            # Usar la misma lógica que el ranking: obtener el mejor puntaje por participante
            from django.db.models import Max
            
            # Primero, obtener el mejor puntaje por participante
            mejores_puntajes = ResultadoEvaluacion.objects.filter(
                evaluacion=evaluacion_etapa1,
                completada=True
            ).values('participante').annotate(
                mejor_puntaje=Max('puntos_obtenidos')
            )
            
            # Crear una lista de participantes con sus mejores puntajes
            participantes_con_mejor_puntaje = []
            for item in mejores_puntajes:
                participante_id = item['participante']
                mejor_puntaje = item['mejor_puntaje']
                
                # Obtener todos los intentos con el mejor puntaje para este participante
                intentos_con_mejor_puntaje = ResultadoEvaluacion.objects.filter(
                    evaluacion=evaluacion_etapa1,
                    participante_id=participante_id,
                    completada=True,
                    puntos_obtenidos=mejor_puntaje,
                    fecha_inicio__isnull=False,
                    fecha_fin__isnull=False
                )
                
                # De los intentos con el mejor puntaje, seleccionar el más rápido (menor tiempo real)
                mejor_resultado = None
                menor_tiempo = float('inf')
                
                for intento in intentos_con_mejor_puntaje:
                    tiempo_real = (intento.fecha_fin - intento.fecha_inicio).total_seconds()
                    if tiempo_real < menor_tiempo:
                        menor_tiempo = tiempo_real
                        mejor_resultado = intento
                
                if mejor_resultado:
                    participantes_con_mejor_puntaje.append(mejor_resultado)
            
            # Ordenar por puntaje descendente y tiempo real ascendente (igual que el ranking)
            def get_tiempo_real(resultado):
                if resultado.fecha_inicio and resultado.fecha_fin:
                    return (resultado.fecha_fin - resultado.fecha_inicio).total_seconds()
                return float('inf')  # Si no tiene fechas, lo colocamos al final
            
            resultados_ordenados = sorted(participantes_con_mejor_puntaje, key=lambda x: (-x.puntos_obtenidos, get_tiempo_real(x)))
            
            # Tomar solo los mejores 5
            mejores_resultados = resultados_ordenados[:5]
        
        return [resultado.participante for resultado in mejores_resultados]
    
    def get_participantes_autorizados(self):
        """Obtiene los participantes autorizados según la etapa"""
        if self.etapa == 1:
            return self.get_participantes_etapa1()
        elif self.etapa == 2:
            # Para etapa 2: si hay participantes asignados manualmente, usar solo esos
            # Si no hay manuales, usar automáticos (preseleccionados)
            if self.participantes_individuales.exists():
                return list(self.participantes_individuales.all())
            else:
                return self.get_participantes_etapa2()  # Automáticos
        elif self.etapa == 3:
            # Para etapa 3: si hay participantes asignados manualmente, usar solo esos
            # Si no hay manuales, usar automáticos (preseleccionados)
            if self.participantes_individuales.exists():
                return list(self.participantes_individuales.all())
            else:
                return self.get_participantes_etapa3()  # Automáticos
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
    
    def get_preguntas_para_estudiante(self, participante_id, numero_intento=1):
        """Obtiene preguntas específicas para un estudiante para un intento específico"""
        import hashlib
        
        total_preguntas = self.preguntas.count()
        if total_preguntas == 0:
            return []
        
        # Si hay menos preguntas que las configuradas, mostrar todas
        if total_preguntas <= self.preguntas_a_mostrar:
            return list(self.preguntas.prefetch_related('opciones').all())
        
        # Usar hash del participante + número de intento para selección aleatoria por intento
        hash_base = f"{self.id}_{participante_id}_{numero_intento}"
        hash_participante = hashlib.md5(hash_base.encode()).hexdigest()
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

# Modelo para categorías de preguntas
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text='Nombre de la categoría (ej: Álgebra, Geometría Analítica)')
    descripcion = models.TextField(blank=True, help_text='Descripción opcional de la categoría')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True, help_text='Si la categoría está activa para su uso')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

# Modelo para las preguntas
class Pregunta(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, related_name='preguntas', on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, related_name='preguntas', on_delete=models.SET_NULL, null=True, blank=True, help_text='Categoría temática de la pregunta')
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
    
    # Campo para múltiples intentos
    numero_intento = models.PositiveIntegerField(default=1, help_text='Número del intento del participante')
    
    # Campo para control de cambios de pestaña
    cambios_pestana = models.PositiveIntegerField(default=0, help_text='Número de cambios de pestaña durante la evaluación')
    
    class Meta:
        unique_together = ['evaluacion', 'participante', 'numero_intento']
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
       
    def get_puntaje_porcentaje(self):
        """Retorna el puntaje como porcentaje"""
        if self.puntos_totales > 0:
            return (self.puntos_obtenidos / self.puntos_totales) * 100
        return 0

# Modelo para el monitoreo en tiempo real de evaluaciones
class MonitoreoEvaluacion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('finalizado', 'Finalizado'),
        ('suspendido', 'Suspendido'),
    ]
    
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='monitoreos')
    participante = models.ForeignKey(Participantes, on_delete=models.CASCADE, related_name='monitoreos')
    resultado = models.OneToOneField(ResultadoEvaluacion, on_delete=models.CASCADE, related_name='monitoreo', null=True, blank=True)
    
    # Estado del monitoreo
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
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
    
    # Control de cambios de pestaña
    cambios_pestana = models.PositiveIntegerField(default=0, help_text='Número de cambios de pestaña detectados')
    alertas = models.JSONField(default=list, blank=True, help_text='Lista de alertas específicas incluyendo cambios de pestaña')
    
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
        with transaction.atomic():
            self.estado = 'finalizado'
            self.finalizado_por_admin = admin_user
            self.motivo_finalizacion = motivo
            self.fecha_finalizacion_admin = timezone.now()

            # Obtener o crear el resultado de evaluación
            if not self.resultado:
                # Obtener el siguiente número de intento
                siguiente_intento = ResultadoEvaluacion.get_siguiente_numero_intento(
                    self.evaluacion, 
                    self.participante
                )
                
                self.resultado, created = ResultadoEvaluacion.objects.get_or_create(
                    evaluacion=self.evaluacion,
                    participante=self.participante,
                    numero_intento=siguiente_intento,
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
        """Verifica si el estudiante está activo (última actividad en la última hora)"""
        tiempo_limite = timezone.now() - timezone.timedelta(hours=1)
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

