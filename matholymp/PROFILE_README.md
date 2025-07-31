# Funcionalidades del Perfil de Usuario

## Descripción
Se ha implementado un sistema completo de gestión de perfiles de usuario que permite a los usuarios actualizar su información personal, cambiar su contraseña y subir una foto de perfil.

## Características Implementadas

### 1. Modelo de Perfil de Usuario
- **UserProfile**: Modelo que extiende la información del usuario
  - Campo `avatar`: Imagen de perfil del usuario
  - Campo `phone`: Número de teléfono (validación de 10 dígitos)
  - Campo `bio`: Biografía o descripción del usuario
  - Campo `fecha_actualizacion`: Timestamp de última actualización

### 2. Funcionalidades del Perfil

#### Información Personal
- Actualización de nombres y apellidos
- Cambio de correo electrónico (con validación de unicidad)
- Actualización de número de teléfono
- Edición de biografía personal

#### Gestión de Contraseñas
- Cambio de contraseña con validación
- Confirmación de contraseña actual
- Validación de coincidencia de nuevas contraseñas
- Longitud mínima de 8 caracteres

#### Foto de Perfil
- Subida de imágenes (JPG, PNG, GIF)
- Límite de tamaño: 5MB
- Preview en tiempo real
- Actualización automática en el sidebar
- Almacenamiento en `static/media/fotos/perfil/`

### 3. Interfaz de Usuario

#### Diseño Moderno y Responsivo
- Gradientes y efectos visuales atractivos
- Animaciones de entrada suaves
- Diseño adaptativo para móviles
- Iconografía de Bootstrap Icons

#### Validaciones en Tiempo Real
- Validación de formato de teléfono
- Validación de tamaño y tipo de imagen
- Validación de contraseñas
- Mensajes de error informativos

### 4. Integración con el Sistema

#### Sidebar
- El avatar se actualiza automáticamente en el sidebar
- Cambio de "Profile" a "Perfil" en el menú
- Enlace directo a la página de perfil

#### Navegación
- Breadcrumb para navegación clara
- Botones de acción intuitivos
- Modal de confirmación para cambios críticos

## Archivos Creados/Modificados

### Nuevos Archivos
- `quizzes/models.py` - Agregado modelo UserProfile
- `quizzes/views.py` - Nueva vista profile_view
- `quizzes/urls.py` - Nueva URL para perfil
- `quizzes/signals.py` - Signals para crear perfiles automáticamente
- `quizzes/management/commands/create_user_profiles.py` - Comando para crear perfiles
- `templates/quizzes/profile.html` - Template del perfil
- `static/css/profile.css` - Estilos personalizados
- `static/js/profile.js` - Funcionalidad JavaScript

### Archivos Modificados
- `templates/quizzes/sidebar.html` - Cambio de "Profile" a "Perfil"
- `quizzes/apps.py` - Registro de signals

## Instalación y Configuración

### 1. Crear Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Crear Perfiles para Usuarios Existentes
```bash
python manage.py create_user_profiles
```

### 3. Verificar Configuración de Medios
Asegúrate de que las siguientes configuraciones estén en `settings.py`:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

Y en `urls.py` principal:
```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Uso

### Acceso al Perfil
1. Inicia sesión en el sistema
2. Haz clic en tu nombre en el sidebar
3. Selecciona "Perfil" del menú desplegable

### Actualizar Información
1. Completa los campos que desees modificar
2. Para cambiar la foto, selecciona un archivo de imagen
3. Haz clic en "Actualizar Perfil"

### Cambiar Contraseña
1. Completa los campos de contraseña actual y nueva
2. Confirma la nueva contraseña
3. Haz clic en "Cambiar Contraseña"
4. Confirma en el modal que aparece

## Seguridad

### Validaciones Implementadas
- Validación de contraseña actual antes del cambio
- Validación de unicidad de correo electrónico
- Validación de formato de teléfono
- Validación de tipo y tamaño de imagen
- Protección CSRF en todos los formularios

### Restricciones
- No se pueden modificar datos sensibles como cédula
- Las contraseñas deben tener al menos 8 caracteres
- Solo se permiten archivos de imagen hasta 5MB

## Personalización

### Estilos CSS
Los estilos se pueden personalizar editando `static/css/profile.css`:
- Colores de gradientes
- Animaciones
- Tamaños y espaciados
- Efectos hover

### JavaScript
La funcionalidad se puede extender editando `static/js/profile.js`:
- Validaciones adicionales
- Nuevas animaciones
- Integración con APIs externas

## Soporte

Para reportar problemas o solicitar nuevas funcionalidades, contacta al equipo de desarrollo. 