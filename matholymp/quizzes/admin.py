from django.contrib import admin
from .models import (
    GrupoParticipantes, Participantes, Evaluacion, Pregunta, Opcion, 
    AdminProfile, SolicitudClaveTemporal, UnidadTematica, Categoria, Tema, 
    EvaluacionCuotaUnidad, Facultad, Carrera, Concurso, AuditLog
)


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 1


class PreguntaAdmin(admin.ModelAdmin):
    inlines = [OpcionInline]


class EvaluacionCuotaUnidadInline(admin.TabularInline):
    model = EvaluacionCuotaUnidad
    extra = 1


@admin.register(Facultad)
class FacultadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'siglas', 'activa', 'fecha_creacion')
    search_fields = ('nombre', 'siglas')


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'facultad', 'codigo', 'activa', 'fecha_creacion')
    list_filter = ('facultad', 'activa')
    search_fields = ('nombre', 'codigo')


@admin.register(Concurso)
class ConcursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'carrera', 'anio', 'num_etapas', 'estado', 'fecha_inicio', 'fecha_fin')
    list_filter = ('carrera', 'estado', 'anio')
    search_fields = ('nombre',)


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('title', 'concurso', 'etapa', 'start_time', 'end_time', 'duration_minutes', 'preguntas_a_mostrar')
    list_filter = ('concurso', 'etapa')
    inlines = [EvaluacionCuotaUnidadInline]


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'carrera', 'acceso_total', 'created_by')
    list_filter = ('carrera', 'acceso_total')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_editable = ('acceso_total',)


@admin.register(UnidadTematica)
class UnidadTematicaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('numero',)


@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'unidad', 'activa', 'fecha_creacion')
    list_filter = ('unidad', 'activa')
    search_fields = ('nombre', 'descripcion')


admin.site.register(GrupoParticipantes)
admin.site.register(Participantes)
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


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'usuario_ejecutor', 'accion', 'ip_address', 'detalles')
    list_filter = ('accion', 'fecha_hora')
    search_fields = ('usuario_ejecutor__username', 'detalles', 'ip_address')
    readonly_fields = ('usuario_ejecutor', 'accion', 'detalles', 'ip_address', 'fecha_hora')

