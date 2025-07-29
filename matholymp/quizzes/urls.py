from django.contrib.auth.decorators import login_required
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic import RedirectView

app_name = 'quizzes'

urlpatterns = [
    path('', login_required(RedirectView.as_view(pattern_name='quizzes:dashboard', permanent=False)), name='home'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('session-check/', views.session_check, name='session_check'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('quiz/<int:pk>/', views.take_quiz, name='take_quiz'),
    path('quiz/<int:pk>/guardar/', views.guardar_respuesta_automatica, name='guardar_respuesta_automatica'),
    path('quiz/<int:pk>/progreso/', views.obtener_progreso_evaluacion, name='obtener_progreso_evaluacion'),
    path('evaluaciones/', views.quiz_view, name='quiz'),  # Nueva URL para evaluaciones
    path('evaluaciones/crear/', views.create_evaluacion, name='create_evaluacion'),
    path('mis-resultados/', views.student_results, name='student_results'),
    path('resultado/<int:pk>/pdf/', views.exportar_resultado_pdf, name='exportar_resultado_pdf'),
    path('evaluacion/<int:eval_id>/preguntas/', views.manage_questions, name='manage_questions'),
    path('evaluacion/<int:eval_id>/preguntas/guardar/', views.save_question, name='save_question'),
    path('pregunta/<int:pk>/eliminar/', views.delete_question, name='delete_question'),
    path('pregunta/<int:pk>/datos/', views.get_question_data, name='get_question_data'),
    path('pregunta/<int:pk>/actualizar/', views.update_question, name='update_question'),
    path('pregunta/<int:pk>/puntos/', views.actualizar_puntos_pregunta, name='actualizar_puntos_pregunta'),
    
    # Nuevas URLs para las opciones del dropdown de evaluaciones
    path('evaluacion/<int:pk>/ver/', views.view_evaluacion, name='view_evaluacion'),
    path('evaluacion/<int:pk>/editar/', views.edit_evaluacion, name='edit_evaluacion'),
    path('evaluacion/<int:pk>/resultados/', views.evaluacion_results, name='evaluacion_results'),
    path('evaluacion/<int:pk>/eliminar/', views.delete_evaluacion, name='delete_evaluacion'),
    path('evaluacion/<int:pk>/ranking/', views.ranking_evaluacion, name='ranking_evaluacion'),
    path('evaluacion/<int:pk>/participantes/', views.gestionar_participantes_evaluacion, name='gestionar_participantes_evaluacion'),
    
    path('gestionar-participantes/', views.manage_participants, name='manage_participants'),
    path('gestionar-admins/', views.manage_admins, name='manage_admins'),
    path('gestionar-permisos/', views.manage_admin_permissions, name='manage_admin_permissions'),
    path('gestionar-representantes/', views.manage_representantes, name='manage_representantes'),
    path('gestionar-grupos/', views.manage_grupos, name='manage_grupos'),
    path('procesar-excel-participantes/', views.process_excel_participants, name='process_excel_participants'),
    path('guardar-excel-participantes/', views.save_excel_participants, name='save_excel_participants'),
    path('upload-image/', views.upload_image, name='upload_image'),
]
