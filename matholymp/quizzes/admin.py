from django.contrib import admin
from .models import ParticipantGroup, Participant, Quiz, Question, Option


class OptionInline(admin.TabularInline):
    model = Option
    extra = 1


class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]


admin.site.register(ParticipantGroup)
admin.site.register(Participant)
admin.site.register(Quiz)
admin.site.register(Question, QuestionAdmin)
