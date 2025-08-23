from django.contrib import admin
from .models import GrupoParticipantes, Participantes, Evaluacion, Pregunta, Opcion, AdminProfile, SolicitudClaveTemporal, IntentoEvaluacion, ResultadoEvaluacion


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 1


class PreguntaAdmin(admin.ModelAdmin):
    inlines = [OpcionInline]


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'acceso_total', 'created_by')
    list_filter = ('acceso_total',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_editable = ('acceso_total',)


admin.site.register(GrupoParticipantes)
admin.site.register(Participantes)
admin.site.register(Evaluacion)
admin.site.register(Pregunta, PreguntaAdmin)
admin.site.register(Opcion)


@admin.register(SolicitudClaveTemporal)
class SolicitudClaveTemporalAdmin(admin.ModelAdmin):
    list_display = ('username', 'tipo_usuario', 'email', 'fecha_solicitud', 'procesada')
    list_filter = ('tipo_usuario', 'procesada', 'fecha_solicitud')
    search_fields = ('username', 'email')
    readonly_fields = ('fecha_solicitud',)
    list_editable = ('procesada',)
    ordering = ('-fecha_solicitud',)
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('username', 'tipo_usuario', 'email')
        }),
        ('Información de la Solicitud', {
            'fields': ('fecha_solicitud',)
        }),
        ('Estado', {
            'fields': ('procesada', 'mensaje_error')
        }),
    )

@admin.register(IntentoEvaluacion)
class IntentoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('participante', 'evaluacion', 'intentos_utilizados', 'intentos_permitidos', 'puede_realizar_intento', 'fecha_modificacion', 'modificado_por')
    list_filter = ('evaluacion__etapa', 'evaluacion__anio', 'fecha_modificacion')
    search_fields = ('participante__NombresCompletos', 'participante__cedula', 'evaluacion__title')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    list_editable = ('intentos_permitidos',)
    ordering = ('-fecha_modificacion',)
    
    fieldsets = (
        ('Información General', {
            'fields': ('evaluacion', 'participante')
        }),
        ('Configuración de Intentos', {
            'fields': ('intentos_permitidos', 'intentos_utilizados')
        }),
        ('Información de Seguimiento', {
            'fields': ('fecha_creacion', 'fecha_modificacion', 'modificado_por')
        }),
    )
    
    def puede_realizar_intento(self, obj):
        return obj.puede_realizar_intento()
    puede_realizar_intento.boolean = True
    puede_realizar_intento.short_description = 'Puede Realizar Intento'

@admin.register(ResultadoEvaluacion)
class ResultadoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('participante', 'evaluacion', 'numero_intento', 'puntos_obtenidos', 'es_mejor_intento', 'completada', 'fecha_fin')
    list_filter = ('evaluacion__etapa', 'evaluacion__anio', 'completada', 'es_mejor_intento', 'fecha_fin')
    search_fields = ('participante__NombresCompletos', 'participante__cedula', 'evaluacion__title')
    readonly_fields = ('fecha_inicio', 'fecha_fin', 'ultima_actividad')
    ordering = ('-fecha_fin', '-puntos_obtenidos')
    
    fieldsets = (
        ('Información General', {
            'fields': ('evaluacion', 'participante', 'numero_intento')
        }),
        ('Puntuación', {
            'fields': ('puntos_obtenidos', 'puntos_totales', 'puntaje', 'es_mejor_intento')
        }),
        ('Tiempo y Estado', {
            'fields': ('fecha_inicio', 'fecha_fin', 'tiempo_utilizado', 'completada', 'ultima_actividad')
        }),
        ('Datos Adicionales', {
            'fields': ('tiempo_restante', 'respuestas_guardadas'),
            'classes': ('collapse',)
        }),
    )
