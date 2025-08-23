import os
from decouple import config
# Importar ImproperlyConfigured para manejar errores de configuración
from django.core.exceptions import ImproperlyConfigured
from django.db.models.expressions import F
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = config('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'quizzes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'olymp.middleware.SessionTimeoutMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'olymp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'olymp.wsgi.application'
ASGI_APPLICATION = 'olymp.asgi.application'


# Funcion para obtener las variables de entorno (Borrar si no se usa)
def get_env(name, default=None):
    val = os.environ.get(name, default)
    if val is None:
        raise ImproperlyConfigured(f"Falta la variable de entorno {name}")
    return val

    
# Configuración de Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(get_env('REDIS_HOST', '127.0.0.1'), 6379)],
        },
    },
}


DATABASES = {
    'default': {
        'ENGINE':   get_env('DB_ENGINE',   'django.db.backends.mysql'),
        'NAME':     get_env('DB_NAME',     'testmath'),
        'USER':     get_env('DB_USER',     'testuser'),
        'PASSWORD': get_env('DB_PASSWORD', 'testpass'),
        'HOST':     get_env('DB_HOST',     'db'),
        'PORT':     get_env('DB_PORT',     '3306'),
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'es-ec'

TIME_ZONE = 'America/Guayaquil'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]



# Configuración para archivos media (imágenes subidas por CKEditor)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGIN_URL = 'quizzes:login'
# Redirección después del login
LOGIN_REDIRECT_URL = '/dashboard/'


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')  
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')  




# Tiempo de sesión en segundos (30 minutos = 1800 segundos)
SESSION_COOKIE_AGE = 1800

# La sesión expira cuando el usuario cierra el navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Configuración de mensajes para Bootstrap
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Renovar la sesión con cada request
SESSION_SAVE_EVERY_REQUEST = True

# Control de páginas de error personalizadas
# Cambiar a False para deshabilitar las páginas 404 personalizadas
ENABLE_CUSTOM_ERROR_PAGES = True