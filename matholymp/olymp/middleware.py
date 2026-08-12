import threading
from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

_thread_locals = threading.local()

def get_current_request():
    """Retorna el objeto request HTTP de la petición activa en el hilo actual."""
    return getattr(_thread_locals, 'request', None)

def get_current_user():
    """Retorna el usuario de la petición activa en el hilo actual."""
    request = get_current_request()
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None

def get_current_ip():
    """Retorna la dirección IP de la petición activa en el hilo actual."""
    request = get_current_request()
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    return None

class AuditMiddleware:
    """
    Middleware que captura la petición HTTP actual en thread-local memory
    para permitir que las Signals de auditoría asocien usuario e IP automáticamente.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response

class SessionTimeoutMiddleware:
    """
    Middleware que controla la expiración de sesión por inactividad.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now().timestamp()
            last_activity = request.session.get('last_activity', now)
            
            if (now - last_activity) > settings.SESSION_COOKIE_AGE:
                logout(request)
                request.session.flush()
                
                # Verificar si es una petición AJAX
                is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                
                if is_ajax:
                    # Para peticiones AJAX, devolver JSON en lugar de redirect
                    return JsonResponse({
                        'success': False,
                        'message': 'Tu sesión ha expirado. Por favor, recarga la página.',
                        'session_expired': True
                    }, status=401)
                else:
                    # Para peticiones normales, redirigir a login
                    return redirect(f"{settings.LOGIN_URL}?session_expired=1")
            
            request.session['last_activity'] = now
            
        return self.get_response(request)