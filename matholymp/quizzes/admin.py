from django.contrib import admin
from .models import GrupoParticipantes, Participantes, Evaluacion, Pregunta, Opcion, AdminProfile, SolicitudClaveTemporal


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
