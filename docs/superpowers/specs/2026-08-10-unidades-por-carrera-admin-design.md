# Creación de unidades por carrera de administrador

## Objetivo

Permitir que un administrador con acceso total cree unidades temáticas para su
carrera asignada sin seleccionar ni enviar manualmente esa carrera.

## Roles y flujo

- El superusuario conserva el selector de carrera y puede crear unidades para
  cualquier carrera activa.
- Un administrador no-superusuario autorizado para Configuración ve solamente
  número, nombre y descripción. Al enviar el formulario, el servidor asocia la
  unidad con `request.user.adminprofile.carrera`.
- El servidor no usa un `carrera_id` proveniente del formulario de un
  administrador. Si el perfil no tiene carrera, no crea la unidad y muestra un
  error explícito.

## Cambio técnico

`settings_view` resolverá la carrera de administradores desde `AdminProfile`
para crear y listar unidades y concursos. La plantilla consultará el mismo
perfil para decidir si muestra el selector exclusivo del superusuario. No se
requieren cambios de modelos ni migraciones.

## Validación

Se comprobará que la vista y la plantilla no dependan de `user.carrera`, que
el archivo Python compile, y que el formulario para administradores no
contenga un selector ni un campo oculto de carrera.
