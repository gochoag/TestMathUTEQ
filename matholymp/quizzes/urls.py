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
    path('gestionar-participantes/', views.manage_participants, name='manage_participants'),
    path('gestionar-admins/', views.manage_admins, name='manage_admins'),
    path('gestionar-permisos/', views.manage_admin_permissions, name='manage_admin_permissions'),
    path('gestionar-representantes/', views.manage_representantes, name='manage_representantes'),
    path('gestionar-grupos/', views.manage_grupos, name='manage_grupos'),
    path('procesar-excel-participantes/', views.process_excel_participants, name='process_excel_participants'),
    path('guardar-excel-participantes/', views.save_excel_participants, name='save_excel_participants'),
]
