from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now().timestamp()
            last_activity = request.session.get('last_activity', now)
            
            if (now - last_activity) > settings.SESSION_COOKIE_AGE:
                logout(request)
                # Redirige a tu vista personalizada con parámetro
                request.session.flush() 
                return redirect(f"{settings.LOGIN_URL}?session_expired=1")
            
            request.session['last_activity'] = now
            
        return self.get_response(request)