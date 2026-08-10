from .models import Concurso, Carrera, AdminProfile

def concurso_context_processor(request):
    """
    Context processor global que provee el concurso activo y concursos disponibles
    para el selector de contexto en el Navbar.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {}

    user = request.user
    
    # Obtener IDs guardados en la sesión
    session_concurso_id = request.session.get('active_concurso_id')
    session_carrera_id = request.session.get('active_carrera_id')

    active_concurso = None
    available_concursos = []
    available_carreras = []
    active_carrera = None

    if user.is_superuser:
        available_carreras = Carrera.objects.select_related('facultad').all().order_by('nombre')
        
        if session_carrera_id and str(session_carrera_id) != 'ALL':
            try:
                active_carrera = Carrera.objects.get(id=session_carrera_id)
                concursos_qs = Concurso.objects.filter(carrera_id=session_carrera_id)
            except Carrera.DoesNotExist:
                concursos_qs = Concurso.objects.all()
        else:
            concursos_qs = Concurso.objects.all()
            
        available_concursos = list(concursos_qs.select_related('carrera', 'carrera__facultad').order_by('-anio', '-id'))

    else:
        # Administrador secundario
        try:
            admin_profile = AdminProfile.objects.select_related('carrera', 'carrera__facultad').get(user=user)
            active_carrera = admin_profile.carrera
            if active_carrera:
                available_concursos = list(Concurso.objects.filter(carrera=active_carrera).select_related('carrera', 'carrera__facultad').order_by('-anio', '-id'))
        except AdminProfile.DoesNotExist:
            pass

    # Resolver el concurso activo de la sesión
    if session_concurso_id == 'ALL':
        active_concurso = None
    elif session_concurso_id is not None:
        try:
            active_concurso = Concurso.objects.select_related('carrera', 'carrera__facultad').get(id=session_concurso_id)
        except (Concurso.DoesNotExist, ValueError):
            active_concurso = None

    # Si no hay concurso activo definido en sesión, tomar automáticamente el más reciente disponible
    if session_concurso_id is None and available_concursos:
        active_concurso = available_concursos[0]
        request.session['active_concurso_id'] = active_concurso.id

    return {
        'active_concurso': active_concurso,
        'active_concurso_id': session_concurso_id if session_concurso_id is not None else (active_concurso.id if active_concurso else 'ALL'),
        'available_concursos': available_concursos,
        'available_carreras': available_carreras,
        'active_carrera_filter': active_carrera,
        'active_carrera_filter_id': session_carrera_id if session_carrera_id else (active_carrera.id if active_carrera else 'ALL'),
    }
