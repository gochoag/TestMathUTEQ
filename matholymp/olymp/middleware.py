from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

class SessionTimeoutMiddleware:
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