from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('', views.custom_login, name='home'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('session-check/', views.session_check, name='session_check'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('quiz/<int:pk>/', views.take_quiz, name='take_quiz'),
    path('gestionar-participantes/', views.manage_participants, name='manage_participants'),
    path('gestionar-admins/', views.manage_admins, name='manage_admins'),
]
