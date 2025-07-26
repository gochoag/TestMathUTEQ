from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Quiz
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login,logout

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
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == 'POST':
        score = 0
        for question in quiz.questions.all():
            selected = request.POST.get(str(question.id))
            if selected and question.options.filter(id=selected, is_correct=True).exists():
                score += 1
        return render(request, 'quizzes/result.html', {'quiz': quiz, 'score': score})
    return render(request, 'quizzes/quiz.html', {'quiz': quiz})


from .models import AdminProfile, Participant
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

@login_required
def dashboard(request):
    user = request.user
    context = {}
    # Determinar el tipo de usuario
    if user.is_superuser:
        context['role'] = 'superadmin'
    elif AdminProfile.objects.filter(user=user).exists():
        context['role'] = 'admin'
    elif Participant.objects.filter(user=user).exists():
        context['role'] = 'participant'
    else:
        context['role'] = 'unknown'
    return render(request, 'quizzes/dashboard.html', context)

# Gestión de participantes
@login_required
def manage_participants(request):
    user = request.user
    # Solo superadmin puede acceder
    if not (user.is_superuser or AdminProfile.objects.filter(user=user).exists()):
        return redirect('quizzes:dashboard')

    # Eliminar participante
    delete_id = request.GET.get('delete_id')
    if delete_id:
        participant = Participant.objects.filter(id=delete_id).first()
        if participant:
            participant.user.delete()  # Elimina el usuario relacionado al participante
            participant.delete()  # Elimina el perfil de participante
        return redirect('quizzes:manage_participants')

    # Agregar participante
    if request.method == 'POST' and request.POST.get('add_participant'):
        cedula = request.POST.get('cedula')
        nombres = request.POST.get('nombres')
        apellidos = request.POST.get('apellidos')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        # Crear el participante
        participant, password = Participant.create_participant(cedula, nombres, apellidos, email, phone)
        # Enviar las credenciales por correo
        send_credentials_email(nombres, cedula, password, email, rol='Participante')
        return redirect('quizzes:manage_participants')

    # Editar participante
    if request.method == 'POST' and request.POST.get('edit_id'):
        edit_id = request.POST.get('edit_id')
        cedula = request.POST.get('cedula')
        nombres = request.POST.get('nombres')
        apellidos = request.POST.get('apellidos')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        # Obtener el participante y actualizar sus datos
        participant = Participant.objects.select_related('user').get(id=edit_id)
        user_obj = participant.user
        user_obj.username = cedula  # Actualiza el username a la cédula
        user_obj.first_name = nombres
        user_obj.last_name = apellidos
        user_obj.email = email
        participant.cedula = cedula
        participant.nombres = nombres
        participant.apellidos = apellidos
        participant.email = email
        participant.phone = phone
        user_obj.save()
        participant.save()
        return redirect('quizzes:manage_participants')

    participants = Participant.objects.select_related('user').all()
    return render(request, 'quizzes/manage_participants.html', {'participants': participants})



# Gestión de admins
@login_required
def manage_admins(request):
    user = request.user
    # Solo superadmin puede acceder
    if not user.is_superuser:
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
        send_credentials_email(first_name, username, password, email, rol='Administrador')
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