"""
Utilitarios para la resolución de alcance (scoping) y aislación de datos por Carrera y Concurso
en el sistema TestMathUTEQ.
"""

from .models import Concurso, AdminProfile, Carrera

def get_user_scope(user_or_request):
    """
    Determina el alcance (scope) del usuario autenticado o de la solicitud HTTP activa.
    
    Returns:
        tuple: (is_global, carrera, concurso_activo)
            - is_global (bool): True si el usuario es Superusuario y no tiene filtro restringido.
            - carrera (Carrera or None): Instancia de Carrera asignada o seleccionada en contexto.
            - concurso_activo (Concurso or None): Concurso activo seleccionado en la sesión o por defecto.
    """
    request = user_or_request if hasattr(user_or_request, 'user') else None
    user = request.user if request else user_or_request
    
    if not user or not user.is_authenticated:
        return False, None, None
        
    session_concurso_id = request.session.get('active_concurso_id') if request else None
    session_carrera_id = request.session.get('active_carrera_id') if request else None

    carrera = None
    concurso_activo = None

    if user.is_superuser:
        if session_carrera_id and str(session_carrera_id) != 'ALL':
            try:
                carrera = Carrera.objects.get(id=session_carrera_id)
            except Carrera.DoesNotExist:
                carrera = None

        if session_concurso_id and str(session_concurso_id) != 'ALL':
            try:
                concurso_activo = Concurso.objects.select_related('carrera', 'carrera__facultad').get(id=session_concurso_id)
            except (Concurso.DoesNotExist, ValueError):
                concurso_activo = None
        elif session_concurso_id is None:
            concurso_activo = Concurso.objects.order_by('-anio', '-id').first()
            if request and concurso_activo:
                request.session['active_concurso_id'] = concurso_activo.id

        return True, carrera, concurso_activo

    try:
        admin_profile = AdminProfile.objects.select_related('carrera', 'carrera__facultad').get(user=user)
        carrera = admin_profile.carrera
        
        if session_concurso_id and str(session_concurso_id) != 'ALL':
            try:
                concurso_activo = Concurso.objects.select_related('carrera', 'carrera__facultad').get(id=session_concurso_id, carrera=carrera)
            except (Concurso.DoesNotExist, ValueError):
                concurso_activo = None
        elif session_concurso_id is None and carrera:
            concurso_activo = Concurso.objects.filter(carrera=carrera).order_by('-anio', '-id').first()
            if request and concurso_activo:
                request.session['active_concurso_id'] = concurso_activo.id

        return False, carrera, concurso_activo
    except AdminProfile.DoesNotExist:
        return False, None, None

def filter_queryset_by_scope(queryset, user_or_request, model_name=None):
    """
    Aplica filtros de aislamiento de datos al queryset según el contexto de la sesión y perfil.
    """
    request = user_or_request if hasattr(user_or_request, 'user') else None
    user = request.user if request else user_or_request

    if not user or not user.is_authenticated:
        return queryset.none()

    is_global, carrera, concurso_activo = get_user_scope(user_or_request)
    model = queryset.model
    model_str = model_name or model.__name__

    session_concurso_id = request.session.get('active_concurso_id') if request else None

    # Regla 1: Administradores se filtran por CARRERA (nunca por concurso)
    if model_str == 'AdminProfile':
        if is_global:
            if carrera:
                return queryset.filter(carrera=carrera)
            return queryset
        if carrera:
            return queryset.filter(carrera=carrera)
        return queryset.none()

    # Regla 2: Participantes, Representantes, Grupos, Evaluaciones se filtran por CONCURSO ACTIVO
    if session_concurso_id and str(session_concurso_id) != 'ALL':
        try:
            cid = int(session_concurso_id)
            if model_str == 'Participantes':
                return queryset.filter(concurso_id=cid)
            elif model_str == 'Representante':
                return queryset.filter(concurso_id=cid)
            elif model_str == 'GrupoParticipantes':
                return queryset.filter(concurso_id=cid)
            elif model_str == 'Evaluacion':
                return queryset.filter(concurso_id=cid)
        except ValueError:
            pass

    # Si concurso es "ALL" o no seleccionado, filtrar por Carrera
    if is_global:
        if carrera:
            if model_str == 'Participantes':
                return queryset.filter(carrera=carrera)
            elif model_str in ['Representante', 'GrupoParticipantes', 'Evaluacion']:
                return queryset.filter(concurso__carrera=carrera)
        return queryset

    if not carrera:
        return queryset.none()

    if model_str == 'Participantes':
        return queryset.filter(carrera=carrera)
    elif model_str in ['Representante', 'GrupoParticipantes', 'Evaluacion']:
        return queryset.filter(concurso__carrera=carrera)

    return queryset

