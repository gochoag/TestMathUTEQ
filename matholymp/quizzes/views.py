from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Evaluacion, AdminProfile, Participantes, GrupoParticipantes, Representante
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
import re
from django.core.exceptions import ValidationError
from openpyxl import load_workbook
import json
from django.http import JsonResponse


# Función helper para verificar acceso total
def has_full_access(user):
    """
    Verifica si un usuario tiene acceso total al sistema.
    Retorna True si es superuser o si es admin con acceso_total=True
    """
    if user.is_superuser:
        return True
    try:
        admin_profile = AdminProfile.objects.get(user=user)
        return admin_profile.acceso_total
    except AdminProfile.DoesNotExist:
        return False


# Vista de login

def custom_login(request):
    if request.GET.get('session_expired'):
        messages.warning(request, 'Tu sesión expiró por inactividad')
        return redirect(settings.LOGIN_URL)
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Autenticar al usuario
            user = form.get_user()
            login(request, user)
            request.session['last_activity'] = timezone.now().timestamp()
            return redirect('quizzes:dashboard')  # Redirige a la página de dashboard después del login
    else:
        form = AuthenticationForm()

    return render(request, 'quizzes/login.html', {
        'form': form,
        'messages': messages.get_messages(request)  # Pasa los mensajes existentes
    })



def custom_logout(request):
    logout(request)  # Cierra la sesión
    return redirect('quizzes:login')  # Redirige al dashboard después de cerrar sesión


def session_check(request):
    return JsonResponse({
        'is_authenticated': request.user.is_authenticated
    }, status=200 if request.user.is_authenticated else 403)



@login_required
def take_quiz(request, pk):
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    if request.method == 'POST':
        score = 0
        for pregunta in evaluacion.preguntas.all():
            selected = request.POST.get(str(pregunta.id))
            if selected and pregunta.opciones.filter(id=selected, is_correct=True).exists():
                score += 1
        return render(request, 'quizzes/result.html', {'evaluacion': evaluacion, 'score': score})
    return render(request, 'quizzes/quiz.html', {'evaluacion': evaluacion})



@login_required
def dashboard(request):
    user = request.user
    context = {}
    # Determinar el tipo de usuario
    if user.is_superuser:
        context['role'] = 'superadmin'
        context['has_full_access'] = True
    elif AdminProfile.objects.filter(user=user).exists():
        admin_profile = AdminProfile.objects.get(user=user)
        context['role'] = 'admin'
        context['has_full_access'] = admin_profile.acceso_total
        context['admin_profile'] = admin_profile
    elif Participantes.objects.filter(user=user).exists():
        context['role'] = 'participant'
        context['has_full_access'] = False
    else:
        context['role'] = 'unknown'
        context['has_full_access'] = False
    return render(request, 'quizzes/dashboard.html', context)

# Gestión de participantes
@login_required
def manage_participants(request):
    user = request.user
    # Superadmin, admin con acceso total, o admin normal pueden acceder
    if not (user.is_superuser or hasattr(user, 'adminprofile')):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('quizzes:dashboard')

    # Eliminar participante
    delete_id = request.GET.get('delete_id')
    if delete_id:
        participante = Participantes.objects.filter(id=delete_id).first()
        if participante:
            participante.user.delete()  # Elimina el usuario relacionado al participante
            participante.delete()  # Elimina el perfil de participante
        return redirect('quizzes:manage_participants')

    # Agregar participante
    if request.method == 'POST' and request.POST.get('add_participant'):
        cedula = request.POST.get('cedula')
        NombresCompletos = request.POST.get('NombresCompletos')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        edad = request.POST.get('edad')
        
        # Validar cédula y teléfono
        is_valid_cedula, error_cedula = validate_cedula_format(cedula)
        is_valid_phone, error_phone = validate_phone_format(phone)
        
        if not is_valid_cedula:
            messages.error(request, f"Cédula: {error_cedula}")
            return redirect('quizzes:manage_participants')
        
        if not is_valid_phone:
            messages.error(request, f"Teléfono: {error_phone}")
            return redirect('quizzes:manage_participants')
        
        # Crear el participante
        participante, password = Participantes.create_participant(cedula, NombresCompletos, email, phone, edad)
        #send_credentials_email(NombresCompletos, cedula, password, email, rol='Participante')
        return redirect('quizzes:manage_participants')

    # Editar participante
    if request.method == 'POST' and request.POST.get('edit_id'):
        edit_id = request.POST.get('edit_id')
        cedula = request.POST.get('cedula')
        NombresCompletos = request.POST.get('NombresCompletos')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        edad = request.POST.get('edad')
        
        # Validar cédula y teléfono
        is_valid_cedula, error_cedula = validate_cedula_format(cedula)
        is_valid_phone, error_phone = validate_phone_format(phone)
        
        if not is_valid_cedula:
            messages.error(request, f"Cédula: {error_cedula}")
            return redirect('quizzes:manage_participants')
        
        if not is_valid_phone:
            messages.error(request, f"Teléfono: {error_phone}")
            return redirect('quizzes:manage_participants')
        
        # Obtener el participante y actualizar sus datos
        participante = Participantes.objects.select_related('user').get(id=edit_id)
        user_obj = participante.user
        user_obj.username = cedula  # Actualiza el username a la cédula
        user_obj.first_name = NombresCompletos
        user_obj.email = email
        participante.cedula = cedula
        participante.NombresCompletos = NombresCompletos
        participante.email = email
        participante.phone = phone
        participante.edad = edad
        user_obj.save()
        participante.save()
        return redirect('quizzes:manage_participants')

    # Búsqueda de participantes
    search_query = request.GET.get('search', '').strip()
    participantes = Participantes.objects.select_related('user').all()
    
    if search_query:
        participantes = participantes.filter(
            Q(NombresCompletos__icontains=search_query) |
            Q(cedula__icontains=search_query)
        )
    
    # Paginación para participantes
    paginator = Paginator(participantes, 7)  # 7 elementos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'quizzes/manage_participants.html', {
        'participantes': page_obj,
        'page_obj': page_obj,
        'search_query': search_query
    })



# Gestión de admins
@login_required
def manage_admins(request):
    user = request.user
    # Solo superadmin o admin con acceso total puede gestionar otros admins
    if not (user.is_superuser or (hasattr(user, 'adminprofile') and user.adminprofile.acceso_total)):
        messages.error(request, 'Solo los administradores con acceso total pueden gestionar otros administradores.')
        return redirect('quizzes:dashboard')

    # Eliminar admin
    delete_id = request.GET.get('delete_id')
    if delete_id:
        admin = AdminProfile.objects.filter(id=delete_id).first()
        if admin:
            admin.user.delete()
            admin.delete()
        return redirect('quizzes:manage_admins')

    # Agregar admin
    if request.method == 'POST' and request.POST.get('add_admin'):
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = get_random_string(length=8)
        new_user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name, email=email)
        admin_profile = AdminProfile.objects.create(user=new_user, created_by=user, password=password)
        #send_credentials_email(first_name, username, password, email, rol='Administrador')
        return redirect('quizzes:manage_admins')

    # Editar admin
    if request.method == 'POST' and request.POST.get('edit_id'):
        edit_id = request.POST.get('edit_id')
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        admin = AdminProfile.objects.select_related('user').get(id=edit_id)
        user_obj = admin.user
        user_obj.username = username
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        user_obj.email = email
        user_obj.save()
        return redirect('quizzes:manage_admins')

    admins = AdminProfile.objects.select_related('user').all()
    return render(request, 'quizzes/manage_admins.html', {'admins': admins})


# Gestión de permisos de admins
@login_required
def manage_admin_permissions(request):
    user = request.user
    # Solo superadmin puede gestionar permisos (esto se mantiene solo para superuser)
    if not user.is_superuser:
        messages.error(request, 'Solo los superadministradores pueden gestionar permisos de otros administradores.')
        return redirect('quizzes:dashboard')

    # Cambiar acceso total de un admin
    if request.method == 'POST':
        admin_id = request.POST.get('admin_id')
        acceso_total = request.POST.get('acceso_total') == 'on'
        
        try:
            admin_profile = AdminProfile.objects.get(id=admin_id)
            admin_profile.acceso_total = acceso_total
            admin_profile.save()
            
            status = "habilitado" if acceso_total else "deshabilitado"
            messages.success(request, f'Acceso total {status} para {admin_profile.user.get_full_name()}')
        except AdminProfile.DoesNotExist:
            messages.error(request, 'Administrador no encontrado.')
        
        return redirect('quizzes:manage_admin_permissions')

    # Obtener todos los admins (excluyendo superadmins)
    admins = AdminProfile.objects.select_related('user').all()
    return render(request, 'quizzes/manage_admin_permissions.html', {'admins': admins})


# Helper para control de acceso a gestión de representantes y grupos
def can_manage_representantes(user):
    return user.is_superuser or (hasattr(user, 'adminprofile'))

# Funciones de validación
def validate_cedula_format(cedula):
    """Valida formato de cédula: exactamente 10 dígitos numéricos"""
    if not cedula or not re.match(r'^\d{10}$', cedula):
        return False, "La cédula debe tener exactamente 10 dígitos numéricos."
    return True, ""

def validate_phone_format(phone):
    """Valida formato de teléfono: exactamente 10 dígitos numéricos"""
    if phone and not re.match(r'^\d{10}$', phone):
        return False, "El teléfono debe tener exactamente 10 dígitos numéricos."
    return True, ""

# Vista para listar y registrar representantes
@login_required
def manage_representantes(request):
    if not can_manage_representantes(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('quizzes:dashboard')

    # Eliminar representante
    delete_id = request.GET.get('delete_id')
    if delete_id:
        representante = Representante.objects.filter(id=delete_id).first()
        if representante:
            representante.delete()
            messages.success(request, 'Representante eliminado exitosamente.')
        return redirect('quizzes:manage_representantes')

    if request.method == 'POST':
        # Registrar nuevo representante
        if request.POST.get('add_representante'):
            data = request.POST
            
            # Validar teléfonos
            telefono_inst = data.get('TelefonoInstitucional')
            telefono_rep = data.get('TelefonoRepresentante')
            
            is_valid_inst, error_inst = validate_phone_format(telefono_inst)
            is_valid_rep, error_rep = validate_phone_format(telefono_rep)
            
            if not is_valid_inst:
                messages.error(request, f"Teléfono Institucional: {error_inst}")
                return redirect('quizzes:manage_representantes')
            
            if not is_valid_rep:
                messages.error(request, f"Teléfono Representante: {error_rep}")
                return redirect('quizzes:manage_representantes')
            
            Representante.objects.create(
                NombreColegio=data.get('NombreColegio'),
                DireccionColegio=data.get('DireccionColegio'),
                TelefonoInstitucional=telefono_inst,
                CorreoInstitucional=data.get('CorreoInstitucional'),
                NombresRepresentante=data.get('NombresRepresentante'),
                TelefonoRepresentante=telefono_rep,
                CorreoRepresentante=data.get('CorreoRepresentante'),
            )
            messages.success(request, 'Representante registrado exitosamente.')
            return redirect('quizzes:manage_representantes')
        
        # Editar representante
        elif request.POST.get('edit_id'):
            edit_id = request.POST.get('edit_id')
            data = request.POST
            
            # Validar teléfonos
            telefono_inst = data.get('TelefonoInstitucional')
            telefono_rep = data.get('TelefonoRepresentante')
            
            is_valid_inst, error_inst = validate_phone_format(telefono_inst)
            is_valid_rep, error_rep = validate_phone_format(telefono_rep)
            
            if not is_valid_inst:
                messages.error(request, f"Teléfono Institucional: {error_inst}")
                return redirect('quizzes:manage_representantes')
            
            if not is_valid_rep:
                messages.error(request, f"Teléfono Representante: {error_rep}")
                return redirect('quizzes:manage_representantes')
            
            representante = Representante.objects.get(id=edit_id)
            representante.NombreColegio = data.get('NombreColegio')
            representante.DireccionColegio = data.get('DireccionColegio')
            representante.TelefonoInstitucional = telefono_inst
            representante.CorreoInstitucional = data.get('CorreoInstitucional')
            representante.NombresRepresentante = data.get('NombresRepresentante')
            representante.TelefonoRepresentante = telefono_rep
            representante.CorreoRepresentante = data.get('CorreoRepresentante')
            representante.save()
            messages.success(request, 'Representante actualizado exitosamente.')
            return redirect('quizzes:manage_representantes')

    representantes = Representante.objects.all()
    
    # Paginación
    paginator = Paginator(representantes, 10)  # 10 elementos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'quizzes/manage_representantes.html', {
        'representantes': page_obj,
        'page_obj': page_obj
    })

# Vista para listar y crear grupos de participantes
@login_required
def manage_grupos(request):
    if not can_manage_representantes(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('quizzes:dashboard')

    # Eliminar grupo
    delete_id = request.GET.get('delete_id')
    if delete_id:
        grupo = GrupoParticipantes.objects.filter(id=delete_id).first()
        if grupo:
            grupo.delete()
            messages.success(request, 'Grupo eliminado exitosamente.')
        return redirect('quizzes:manage_grupos')

    if request.method == 'POST':
        # Crear nuevo grupo
        if request.POST.get('add_grupo'):
            name = request.POST.get('name')
            representante_id = request.POST.get('representante')
            participantes_ids = request.POST.getlist('participantes')
            
            # Validar que el representante no esté en otro grupo
            representante = Representante.objects.get(id=representante_id)
            if representante.grupos.exists():
                messages.error(request, f'El representante "{representante.NombresRepresentante}" ya está asignado a otro grupo.')
                return redirect('quizzes:manage_grupos')
            
            # Validar que los participantes no estén en otros grupos
            participantes_seleccionados = Participantes.objects.filter(id__in=participantes_ids)
            participantes_en_otros_grupos = participantes_seleccionados.filter(grupos__isnull=False)
            
            if participantes_en_otros_grupos.exists():
                nombres_problema = [p.NombresCompletos for p in participantes_en_otros_grupos]
                messages.error(request, f'Los siguientes participantes ya están en otros grupos: {", ".join(nombres_problema)}')
                return redirect('quizzes:manage_grupos')
            
            grupo = GrupoParticipantes.objects.create(name=name, representante=representante)
            grupo.participantes.set(participantes_ids)
            messages.success(request, 'Grupo creado exitosamente.')
            return redirect('quizzes:manage_grupos')
        
        # Editar grupo
        elif request.POST.get('edit_id'):
            edit_id = request.POST.get('edit_id')
            name = request.POST.get('name')
            representante_id = request.POST.get('representante')
            participantes_ids = request.POST.getlist('participantes')
            
            # Validar que el representante no esté en otro grupo (excluyendo el grupo actual)
            representante = Representante.objects.get(id=representante_id)
            if representante.grupos.exclude(id=edit_id).exists():
                messages.error(request, f'El representante "{representante.NombresRepresentante}" ya está asignado a otro grupo.')
                return redirect('quizzes:manage_grupos')
            
            # Validar que los participantes no estén en otros grupos (excluyendo el grupo actual)
            participantes_seleccionados = Participantes.objects.filter(id__in=participantes_ids)
            participantes_en_otros_grupos = participantes_seleccionados.filter(
                grupos__isnull=False
            ).exclude(grupos=edit_id)
            
            if participantes_en_otros_grupos.exists():
                nombres_problema = [p.NombresCompletos for p in participantes_en_otros_grupos]
                messages.error(request, f'Los siguientes participantes ya están en otros grupos: {", ".join(nombres_problema)}')
                return redirect('quizzes:manage_grupos')
            
            grupo = GrupoParticipantes.objects.get(id=edit_id)
            grupo.name = name
            grupo.representante = representante
            grupo.participantes.set(participantes_ids)
            grupo.save()
            messages.success(request, 'Grupo actualizado exitosamente.')
            return redirect('quizzes:manage_grupos')

    grupos = GrupoParticipantes.objects.select_related('representante').prefetch_related('participantes').all()
    
    # Obtener representantes disponibles (que no están en ningún grupo)
    representantes_disponibles = Representante.objects.filter(grupos__isnull=True)
    
    # Obtener todos los representantes para mostrar en modales de edición
    representantes_todos = Representante.objects.all()
    
    # Obtener participantes disponibles (que no están en ningún grupo)
    participantes_disponibles = Participantes.objects.filter(grupos__isnull=True)
    
    # Obtener todos los participantes para mostrar en modales de edición
    participantes_todos = Participantes.objects.all()
    
    # Paginación para grupos
    paginator = Paginator(grupos, 10)  # 10 elementos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'quizzes/manage_grupos.html', {
        'grupos': page_obj,
        'page_obj': page_obj,
        'representantes': representantes_disponibles,  # Solo disponibles para crear
        'representantes_todos': representantes_todos,  # Todos para editar
        'participantes': participantes_disponibles,  # Solo disponibles para crear
        'participantes_todos': participantes_todos   # Todos para editar
    })


# Vista para procesar archivo Excel de participantes
@login_required
def process_excel_participants(request):
    if not can_manage_representantes(request.user):
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección.'}, status=403)
    
    if request.method == 'POST':
        try:
            # Obtener el archivo y mapeo de columnas
            excel_file = request.FILES.get('excel_file')
            column_mapping = json.loads(request.POST.get('column_mapping', '{}'))
            
            if not excel_file:
                return JsonResponse({'error': 'No se ha seleccionado ningún archivo.'}, status=400)
            
            # Cargar el archivo Excel
            workbook = load_workbook(excel_file, data_only=True)
            worksheet = workbook.active
            
            # Obtener todas las filas (excluyendo la primera que son los headers)
            rows = list(worksheet.iter_rows(min_row=2, values_only=True))
            
            # Procesar cada fila
            processed_data = []
            errors = []
            
            for row_index, row in enumerate(rows, start=2):
                if not any(row):  # Fila vacía
                    continue
                    
                row_data = {}
                row_errors = []
                
                # Mapear columnas según el mapeo proporcionado
                for excel_col, model_field in column_mapping.items():
                    try:
                        col_index = int(excel_col) - 1  # Convertir a índice base 0
                        if col_index < len(row):
                            value = row[col_index]
                            if value is not None:
                                row_data[model_field] = str(value).strip()
                            else:
                                row_data[model_field] = ''
                        else:
                            row_data[model_field] = ''
                    except (ValueError, IndexError):
                        row_data[model_field] = ''
                
                # Validar datos requeridos
                if not row_data.get('cedula'):
                    row_errors.append('Cédula es requerida')
                elif not validate_cedula_format(row_data['cedula'])[0]:
                    row_errors.append(f"Cédula inválida: {row_data['cedula']}")
                
                if not row_data.get('NombresCompletos'):
                    row_errors.append('Nombres Completos es requerido')
                
                if not row_data.get('email'):
                    row_errors.append('Email es requerido')
                elif '@' not in row_data['email']:
                    row_errors.append('Email inválido')
                
                # Validar teléfono si está presente
                if row_data.get('phone') and not validate_phone_format(row_data['phone'])[0]:
                    row_errors.append(f"Teléfono inválido: {row_data['phone']}")
                
                # Validar edad si está presente
                if row_data.get('edad'):
                    try:
                        edad = int(row_data['edad'])
                        if edad < 0 or edad > 120:
                            row_errors.append('Edad debe estar entre 0 y 120')
                    except ValueError:
                        row_errors.append('Edad debe ser un número válido')
                
                if row_errors:
                    errors.append(f"Fila {row_index}: {', '.join(row_errors)}")
                else:
                    processed_data.append({
                        'row_index': row_index,
                        'data': row_data
                    })
            
            return JsonResponse({
                'success': True,
                'data': processed_data,
                'errors': errors,
                'total_rows': len(rows),
                'valid_rows': len(processed_data),
                'error_rows': len(errors)
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error al procesar el archivo: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

# Vista para guardar participantes desde Excel
@login_required
def save_excel_participants(request):
    if not can_manage_representantes(request.user):
        return JsonResponse({'error': 'No tienes permisos para acceder a esta sección.'}, status=403)
    
    if request.method == 'POST':
        try:
            participants_data = json.loads(request.POST.get('participants_data', '[]'))
            
            created_count = 0
            errors = []
            
            for participant_info in participants_data:
                try:
                    data = participant_info['data']
                    
                    # Verificar si la cédula ya existe
                    if Participantes.objects.filter(cedula=data['cedula']).exists():
                        errors.append(f"Cédula {data['cedula']} ya existe")
                        continue
                    
                    # Crear el participante
                    participante, password = Participantes.create_participant(
                        cedula=data['cedula'],
                        NombresCompletos=data['NombresCompletos'],
                        email=data['email'],
                        phone=data.get('phone', ''),
                        edad=int(data['edad']) if data.get('edad') else None
                    )
                    
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f"Error al crear participante con cédula {data.get('cedula', 'N/A')}: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'created_count': created_count,
                'errors': errors
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error al guardar participantes: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

# Función utilitaria para enviar credenciales por correo
from django.core.mail import send_mail
from django.conf import settings
def send_credentials_email(nombre, username, password, email, rol='Administrador'):
    subject = f'Credenciales de acceso como {rol}'
    message = f"""
    Hola {nombre},

    Gracias por registrarte en nuestra plataforma. Aquí están tus credenciales:

    Usuario: {username}
    Contraseña: {password}

    Por favor, accede a la plataforma en: http://127.0.0.1:8000/

    Si tienes alguna duda o problema, no dudes en contactarnos.

    Saludos cordiales,
    El equipo de Olymp
    """

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER, 
        [email],
        fail_silently=False  
    )