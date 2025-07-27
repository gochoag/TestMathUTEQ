from django.contrib import admin
from .models import GrupoParticipantes, Participantes, Evaluacion, Pregunta, Opcion, AdminProfile


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
