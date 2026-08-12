"""
Decoradores de control de acceso y permisos para el sistema TestMathUTEQ.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import AdminProfile

def is_ajax_or_json(request):
    """Verifica si la petición HTTP es de tipo AJAX o JSON."""
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.META.get('HTTP_ACCEPT', '') or
        request.content_type == 'application/json'
    )

def superuser_required(view_func):
    """
    Decorador que restringe el acceso EXCLUSIVAMENTE a Superadministradores (user.is_superuser).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if is_ajax_or_json(request):
                return JsonResponse({'success': False, 'error': 'Usuario no autenticado.'}, status=401)
            return redirect('quizzes:login')

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if is_ajax_or_json(request):
            return JsonResponse({'success': False, 'error': 'Acceso denegado. Requiere privilegios de Superadministrador.'}, status=403)

        messages.error(request, 'Solo los superadministradores pueden acceder a esta sección.')
        return redirect('quizzes:dashboard')
    return _wrapped_view

def full_access_required(view_func):
    """
    Decorador que restringe el acceso a Superadministradores o Administradores con acceso_total = True.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if is_ajax_or_json(request):
                return JsonResponse({'success': False, 'error': 'Usuario no autenticado.'}, status=401)
            return redirect('quizzes:login')

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        try:
            admin_profile = AdminProfile.objects.get(user=request.user)
            if admin_profile.acceso_total:
                return view_func(request, *args, **kwargs)
        except AdminProfile.DoesNotExist:
            pass

        if is_ajax_or_json(request):
            return JsonResponse({'success': False, 'error': 'Acceso denegado. Se requieren permisos de Acceso Total.'}, status=403)

        messages.error(request, 'Solo los administradores con acceso total pueden acceder a esta sección.')
        return redirect('quizzes:dashboard')
    return _wrapped_view

def admin_required(view_func):
    """
    Decorador que permite el acceso a cualquier usuario administrativo (Superadmin, Admin Acceso Total o Admin Normal).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if is_ajax_or_json(request):
                return JsonResponse({'success': False, 'error': 'Usuario no autenticado.'}, status=401)
            return redirect('quizzes:login')

        if request.user.is_superuser or hasattr(request.user, 'adminprofile'):
            return view_func(request, *args, **kwargs)

        if is_ajax_or_json(request):
            return JsonResponse({'success': False, 'error': 'Acceso denegado. Requiere perfil administrativo.'}, status=403)

        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('quizzes:dashboard')
    return _wrapped_view
