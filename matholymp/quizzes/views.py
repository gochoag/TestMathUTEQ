from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .email_utils import generate_email_messages
from .models import Evaluacion, AdminProfile, Participantes, GrupoParticipantes, Representante, SolicitudClaveTemporal, UserProfile, MonitoreoEvaluacion, IntentosParticipante
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import models
import re
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from openpyxl import load_workbook
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import os
from django.conf import settings
from .models import Pregunta, Opcion
from .models import ResultadoEvaluacion
from django.db.models import Avg
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False





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


# Función para validar contraseñas de forma robusta
def validate_password_strength(password, username):
    """
    Valida la fortaleza de una contraseña.
    
    Args:
        password (str): La contraseña a validar
        username (str): El nombre de usuario para verificar similitud
    
    Returns:
        str or None: Mensaje de error si la contraseña no es válida, None si es válida
    """
    # 1. Validar longitud mínima
    if len(password) < 6:
        return 'La contraseña debe tener al menos 6 caracteres.'
    
    # 2. Validar que no sea similar al nombre de usuario
    if password.lower() in username.lower() or username.lower() in password.lower():
        return 'La contraseña no puede ser similar al nombre de usuario.'
    
    # 3. Validar que no sea completamente numérica
    if password.isdigit():
        return 'La contraseña no puede ser completamente numérica.'
    
    # 4. Validar contraseñas comunes
    common_passwords = ['12345678', '123456','1234567', '123456789', 'password', 'contraseña', 'qwerty123', '87654321', 'abc12345']
    if password.lower() in common_passwords:
        return 'La contraseña es demasiado común. Elige una más segura.'
    
    # 5. Validar que tenga al menos una letra y un número
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return 'La contraseña debe contener al menos una letra y un número.'
    
    # Si llegamos aquí, la contraseña es válida
    return None


# Vista de login

def custom_login(request):
    # Si el usuario ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('quizzes:dashboard')
        
    if request.GET.get('session_expired'):
        messages.warning(request, 'Tu sesión expiró por inactividad')
        return redirect(settings.LOGIN_URL)
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Buscar usuario por username case-insensitive
        try:
            user_obj = User.objects.get(username__iexact=username)
            # Intentar autenticar con el username real (case-sensitive) pero password
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            login(request, user)
            request.session['last_activity'] = timezone.now().timestamp()
            messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
            return redirect('quizzes:dashboard')
        else:
            # Mostrar mensaje de error específico
            if not username:
                messages.error(request, 'Por favor, ingresa tu nombre de usuario.')
            elif not password:
                messages.error(request, 'Por favor, ingresa tu contraseña.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos. Por favor, verifica tus credenciales.')
    
    # Crear un formulario vacío para el template
    form = AuthenticationForm()

    return render(request, 'quizzes/login.html', {
        'form': form,
        'messages': messages.get_messages(request)
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
    
    # Verificar que sea estudiante
    if not Participantes.objects.filter(user=request.user).exists():
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('quizzes:dashboard')
    
    # Obtener el participante
    participante = Participantes.objects.get(user=request.user)
    
    # Verificar que el participante esté autorizado para esta evaluación
    participantes_autorizados = evaluacion.get_participantes_autorizados()
    if participante not in participantes_autorizados:
        messages.error(request, 'No estás autorizado para rendir esta evaluación.')
        return redirect('quizzes:quiz')

    # VERIFICAR INTENTOS DISPONIBLES antes de proceder
    intentos_disponibles = participante.get_intentos_disponibles(evaluacion)
    if intentos_disponibles <= 0:
        intentos_usados = participante.get_intentos_usados(evaluacion)
        messages.error(request, f'Has agotado tus intentos para esta evaluación. Intentos utilizados: {intentos_usados}')
        return redirect('quizzes:quiz')
    
    # Verificar si hay un intento activo (no completado)
    resultado_activo = ResultadoEvaluacion.objects.filter(
        evaluacion=evaluacion,
        participante=participante,
        completada=False
    ).first()
    
    # Logging para debugging
    if resultado_activo:
        print(f"DEBUG - Resultado activo encontrado para {participante.NombresCompletos}")
        print(f"DEBUG - Respuestas guardadas: {resultado_activo.respuestas_guardadas}")
        print(f"DEBUG - Tiempo restante: {resultado_activo.tiempo_restante}")
    else:
        print(f"DEBUG - No hay resultado activo para {participante.NombresCompletos}")
    
    # Si hay un intento activo, verificar si puede continuarlo
    continuar_evaluacion = False
    if resultado_activo:
        # Usar el tiempo_restante guardado en lugar de recalcular
        tiempo_restante_guardado = resultado_activo.tiempo_restante or 0
        
        # Si hay tiempo restante guardado, usar ese valor
        if tiempo_restante_guardado > 0:
            continuar_evaluacion = True
            # Actualizar última actividad
            resultado_activo.ultima_actividad = timezone.now()
            resultado_activo.save()
            
            # Actualizar monitoreo al continuar evaluación
            try:
                monitoreo = MonitoreoEvaluacion.objects.filter(
                    evaluacion=evaluacion,
                    participante=participante
                ).first()
                
                if monitoreo:
                    # Obtener preguntas para calcular progreso actual
                    preguntas_mostradas = evaluacion.get_preguntas_para_estudiante(participante.id)
                    respuestas_actuales = resultado_activo.respuestas_guardadas or {}
                    preguntas_respondidas = len([r for r in respuestas_actuales.values() if r])
                    
                    monitoreo.preguntas_respondidas = preguntas_respondidas
                    monitoreo.preguntas_revisadas = len(preguntas_mostradas)
                    monitoreo.ultima_actividad = timezone.now()
                    monitoreo.save()
                    
                    print(f"DEBUG - Monitoreo actualizado al continuar: {preguntas_respondidas}/{len(preguntas_mostradas)} preguntas")
            except Exception as e:
                print(f"Error al actualizar monitoreo al continuar: {e}")
                pass
        else:
            # Si no hay tiempo restante guardado, calcular basado en fecha_inicio
            tiempo_transcurrido = (timezone.now() - resultado_activo.fecha_inicio).total_seconds()
            tiempo_total = evaluacion.duration_minutes * 60  # en segundos
            tiempo_restante = max(0, tiempo_total - tiempo_transcurrido)
            
            if tiempo_restante > 0:
                continuar_evaluacion = True
                resultado_activo.tiempo_restante = int(tiempo_restante)
                resultado_activo.ultima_actividad = timezone.now()
                resultado_activo.save()
                
                # Actualizar monitoreo al continuar evaluación con tiempo calculado
                try:
                    monitoreo = MonitoreoEvaluacion.objects.filter(
                        evaluacion=evaluacion,
                        participante=participante
                    ).first()
                    
                    if monitoreo:
                        # Obtener preguntas para calcular progreso actual
                        preguntas_mostradas = evaluacion.get_preguntas_para_estudiante(participante.id)
                        respuestas_actuales = resultado_activo.respuestas_guardadas or {}
                        preguntas_respondidas = len([r for r in respuestas_actuales.values() if r])
                        
                        monitoreo.preguntas_respondidas = preguntas_respondidas
                        monitoreo.preguntas_revisadas = len(preguntas_mostradas)
                        monitoreo.ultima_actividad = timezone.now()
                        monitoreo.save()
                        
                        print(f"DEBUG - Monitoreo actualizado al continuar (tiempo calculado): {preguntas_respondidas}/{len(preguntas_mostradas)} preguntas")
                except Exception as e:
                    print(f"Error al actualizar monitoreo al continuar (tiempo calculado): {e}")
                    pass
            else:
                # Si se acabó el tiempo, finalizar este intento
                respuestas_guardadas = resultado_activo.respuestas_guardadas or {}
                preguntas_mostradas = evaluacion.get_preguntas_para_estudiante(participante.id)
                
                score = 0
                puntos_obtenidos = 0
                total_questions = len(preguntas_mostradas)
                
                for pregunta in preguntas_mostradas:
                    pregunta_key = f'pregunta_{pregunta.id}'
                    if pregunta_key in respuestas_guardadas and respuestas_guardadas[pregunta_key]:
                        # Nuevo sistema de puntuación:
                        # Correcta: +1 punto, Incorrecta: -0.25 puntos, No respondida: 0 puntos
                        if pregunta.opciones.filter(id=respuestas_guardadas[pregunta_key], is_correct=True).exists():
                            score += 1
                            puntos_obtenidos += 1  # +1 punto por respuesta correcta
                        else:
                            puntos_obtenidos -= 0.25  # -0.25 puntos por respuesta incorrecta
                    # Si no hay respuesta seleccionada, no se suma ni resta nada (0 puntos)
                
                # Ponderar a escala de 10 puntos
                puntaje_ponderado = (puntos_obtenidos / total_questions) * 10 if total_questions > 0 else 0
                # Asegurar que el puntaje no sea negativo
                puntaje_ponderado = max(0, puntaje_ponderado)
                
                # Calcular porcentaje basado en puntaje ponderado
                percentage = (puntaje_ponderado / 10) * 100
                
                # Calcular tiempo utilizado cuando se agota el tiempo
                if resultado_activo.fecha_inicio:
                    tiempo_utilizado = (timezone.now() - resultado_activo.fecha_inicio).total_seconds() / 60  # en minutos
                else:
                    tiempo_utilizado = evaluacion.duration_minutes
                
                resultado_activo.puntaje = percentage
                resultado_activo.puntos_obtenidos = puntaje_ponderado  # Guardar puntaje ponderado sobre 10
                resultado_activo.puntos_totales = 10  # Puntos totales siempre son 10
                resultado_activo.tiempo_utilizado = tiempo_utilizado
                resultado_activo.fecha_fin = timezone.now()
                resultado_activo.completada = True
                resultado_activo.tiempo_restante = 0
                resultado_activo.save()
                
                # Actualizar el monitoreo (el intento ya se registra con el resultado completado)
                monitoreo = MonitoreoEvaluacion.objects.filter(
                    evaluacion=evaluacion,
                    participante=participante
                ).first()
                if monitoreo:
                    monitoreo.estado = 'finalizado'
                    monitoreo.resultado = resultado_activo
                    monitoreo.save()
                
                messages.warning(request, f'Se acabó el tiempo para esta evaluación. Puntuación: {resultado_activo.get_puntaje_numerico()}')
                return redirect('quizzes:quiz')
    
    # Si no hay intento en progreso, verificar ventana de acceso solo para nuevos ingresos
    if not continuar_evaluacion:
        if evaluacion.is_not_started():
            messages.warning(request, 'Esta evaluación aún no ha comenzado.')
            return redirect('quizzes:quiz')
        
        if evaluacion.is_finished():
            messages.warning(request, 'Esta evaluación ya ha finalizado.')
            return redirect('quizzes:quiz')
        
        if not evaluacion.is_available():
            messages.warning(request, 'Esta evaluación no está disponible en este momento.')
            return redirect('quizzes:quiz')
        
        # Crear o actualizar el monitoreo para este estudiante
        try:
            monitoreo, created = MonitoreoEvaluacion.objects.get_or_create(
                evaluacion=evaluacion,
                participante=participante,
                defaults={'resultado': resultado_activo} if resultado_activo else {}
            )
            
            # Si el monitoreo existe y el participante tiene intentos disponibles, reactivarlo
            if not created:
                intentos_disponibles_monitoreo = participante.get_intentos_disponibles(evaluacion)
                if intentos_disponibles_monitoreo > 0:
                    # Si tenía estado finalizado pero ahora tiene intentos, reactivarlo
                    if monitoreo.estado == 'finalizado':
                        monitoreo.estado = 'activo'
                        monitoreo.ultima_actividad = timezone.now()
                        monitoreo.save()
                        print(f"Reactivando monitoreo para {participante.NombresCompletos} - Nuevo intento detectado")
                
                # Actualizar resultado activo si corresponde
                if resultado_activo and not monitoreo.resultado:
                    monitoreo.resultado = resultado_activo
                    monitoreo.save()
        except Exception as e:
            # Si hay error al crear el monitoreo, continuar sin él
            print(f"Error al actualizar monitoreo: {e}")
            pass
    
    if request.method == 'POST':
        # Verificar si la evaluación fue finalizada por cambios de pestaña
        finalizada_por_cambios_pestana = request.POST.get('finalizada_por_cambios_pestana') == 'true'
        
        if finalizada_por_cambios_pestana:
            # Finalización por cambios de pestaña - asignar puntaje de 0
            score = 0
            puntos_obtenidos = 0
            puntos_totales = 10
            percentage = 0
            
            # Calcular tiempo utilizado
            tiempo_utilizado = 0
            if resultado_activo:
                tiempo_total = evaluacion.duration_minutes * 60  # en segundos
                tiempo_restante = int(request.POST.get('tiempo_restante', 0))
                tiempo_utilizado = tiempo_total - tiempo_restante
            
            # Obtener respuestas guardadas hasta el momento de la finalización
            respuestas_finales = {}
            if resultado_activo and resultado_activo.respuestas_guardadas:
                respuestas_finales = resultado_activo.respuestas_guardadas
            
        else:
            # Procesar envío normal de evaluación con nuevo sistema de puntuación
            score = 0
            puntos_obtenidos = 0
            puntos_totales = 0
            preguntas_mostradas = evaluacion.get_preguntas_para_estudiante(participante.id)
            total_questions = len(preguntas_mostradas)
            
            respuestas_finales = {}
            for pregunta in preguntas_mostradas:
                selected = request.POST.get(f'pregunta_{pregunta.id}')
                respuestas_finales[f'pregunta_{pregunta.id}'] = selected
                
                # Nuevo sistema de puntuación:
                # Correcta: +1 punto, Incorrecta: -0.25 puntos, No respondida: 0 puntos
                if selected:
                    if pregunta.opciones.filter(id=selected, is_correct=True).exists():
                        score += 1
                        puntos_obtenidos += 1  # +1 punto por respuesta correcta
                    else:
                        puntos_obtenidos -= 0.25  # -0.25 puntos por respuesta incorrecta
                # Si no hay respuesta seleccionada, no se suma ni resta nada (0 puntos)
            
            # Ponderar a escala de 10 puntos
            puntaje_ponderado = (puntos_obtenidos / total_questions) * 10 if total_questions > 0 else 0
            # Asegurar que el puntaje no sea negativo
            puntaje_ponderado = max(0, puntaje_ponderado)
            puntos_obtenidos = puntaje_ponderado
            puntos_totales = 10
            
            # Calcular porcentaje basado en puntos totales (mantener compatibilidad)
            percentage = (puntaje_ponderado / 10) * 100
            
            # Calcular tiempo utilizado
            tiempo_utilizado = 0
            if resultado_activo:
                tiempo_total = evaluacion.duration_minutes * 60  # en segundos
                tiempo_restante = int(request.POST.get('tiempo_restante', 0))
                tiempo_utilizado = tiempo_total - tiempo_restante
        
        # Guardar resultado en la base de datos con nuevo sistema de puntuación
        if resultado_activo:
            resultado_activo.puntaje = percentage
            resultado_activo.puntos_obtenidos = puntos_obtenidos  # Guardar puntaje ponderado sobre 10
            resultado_activo.puntos_totales = puntos_totales  # Puntos totales siempre son 10
            resultado_activo.tiempo_utilizado = tiempo_utilizado // 60  # convertir a minutos
            resultado_activo.fecha_fin = timezone.now()
            resultado_activo.completada = True
            resultado_activo.respuestas_guardadas = respuestas_finales
            resultado_activo.tiempo_restante = 0
            resultado_activo.save()
            
            # Actualizar el monitoreo (el intento se registra con el resultado completado)
            monitoreo = MonitoreoEvaluacion.objects.filter(
                evaluacion=evaluacion,
                participante=participante
            ).first()
            if monitoreo:
                monitoreo.estado = 'finalizado'
                monitoreo.resultado = resultado_activo
                
                # Si fue finalizada por cambios de pestaña, agregar información al monitoreo
                if finalizada_por_cambios_pestana:
                    if monitoreo.alertas is None:
                        monitoreo.alertas = []
                    
                    monitoreo.alertas.append({
                        'tipo': 'finalizacion_automatica',
                        'mensaje': f'Evaluación finalizada automáticamente por exceso de cambios de pestaña (3/3)',
                        'timestamp': timezone.now().isoformat(),
                        'motivo': 'cambios_pestana_excedidos',
                        'cambios_realizados': monitoreo.cambios_pestana or 3
                    })
                    
                    # Marcar la finalización administrativa en el monitoreo
                    monitoreo.finalizado_por_admin = request.user
                    monitoreo.motivo_finalizacion = 'Evaluación finalizada automáticamente por exceder el límite de cambios de pestaña (3/3)'
                    monitoreo.fecha_finalizacion_admin = timezone.now()
                
                monitoreo.save()
                
        else:
            # Obtener el siguiente número de intento
            siguiente_intento = ResultadoEvaluacion.get_siguiente_numero_intento(evaluacion, participante)
            
            nuevo_resultado = ResultadoEvaluacion.objects.create(
                evaluacion=evaluacion,
                participante=participante,
                numero_intento=siguiente_intento,
                puntaje=percentage,
                puntos_obtenidos=puntos_obtenidos,  # Guardar puntaje ponderado sobre 10
                puntos_totales=puntos_totales,  # Puntos totales siempre son 10
                tiempo_utilizado=tiempo_utilizado // 60,
                fecha_fin=timezone.now(),
                completada=True,
                respuestas_guardadas=respuestas_finales,
                tiempo_restante=0
            )
            
            # Actualizar el monitoreo (el intento se registra con el resultado completado)
            monitoreo = MonitoreoEvaluacion.objects.filter(
                evaluacion=evaluacion,
                participante=participante
            ).first()
            if monitoreo:
                monitoreo.estado = 'finalizado'
                monitoreo.resultado = nuevo_resultado
                
                # Si fue finalizada por cambios de pestaña, agregar información al monitoreo
                if finalizada_por_cambios_pestana:
                    if monitoreo.alertas is None:
                        monitoreo.alertas = []
                    
                    monitoreo.alertas.append({
                        'tipo': 'finalizacion_automatica',
                        'mensaje': f'Evaluación finalizada automáticamente por exceso de cambios de pestaña (3/3)',
                        'timestamp': timezone.now().isoformat(),
                        'motivo': 'cambios_pestana_excedidos',
                        'cambios_realizados': monitoreo.cambios_pestana or 3
                    })
                    
                    # Marcar la finalización administrativa en el monitoreo
                    monitoreo.finalizado_por_admin = request.user
                    monitoreo.motivo_finalizacion = 'Evaluación finalizada automáticamente por exceder el límite de cambios de pestaña (3/3)'
                    monitoreo.fecha_finalizacion_admin = timezone.now()
                
                monitoreo.save()
        
        # Agregar un mensaje específico si fue finalizada por cambios de pestaña
        if finalizada_por_cambios_pestana:
            messages.warning(request, 'Tu evaluación fue finalizada automáticamente por exceder el límite de cambios de pestaña permitidos (3/3). Tu puntaje es 0/10.')
        
        return render(request, 'quizzes/result.html', {
            'evaluacion': evaluacion, 
            'resultado': resultado_activo if resultado_activo else nuevo_resultado,
            'score': score,
            'total_questions': len(preguntas_mostradas) if not finalizada_por_cambios_pestana else 0,
            'percentage': percentage,
            'finalizada_por_cambios_pestana': finalizada_por_cambios_pestana
        })
    
    # Obtener preguntas para este estudiante específico
    preguntas_mostradas = evaluacion.get_preguntas_para_estudiante(participante.id)
    
    if not preguntas_mostradas:
        messages.error(request, 'Esta evaluación no tiene preguntas configuradas.')
        return redirect('quizzes:quiz')
    
    # Si no hay intento en progreso, crear uno nuevo
    if not continuar_evaluacion:
        tiempo_total = evaluacion.duration_minutes * 60  # en segundos
        
        # Obtener el siguiente número de intento
        siguiente_intento = ResultadoEvaluacion.get_siguiente_numero_intento(evaluacion, participante)
        
        resultado_activo = ResultadoEvaluacion.objects.create(
            evaluacion=evaluacion,
            participante=participante,
            numero_intento=siguiente_intento,
            fecha_inicio=timezone.now(),
            tiempo_restante=tiempo_total
        )
        
        # Actualizar monitoreo al crear nuevo intento
        try:
            monitoreo = MonitoreoEvaluacion.objects.filter(
                evaluacion=evaluacion,
                participante=participante
            ).first()
            
            if monitoreo:
                # Al crear un nuevo resultado, activar el monitoreo
                monitoreo.estado = 'activo'
                monitoreo.resultado = resultado_activo
                monitoreo.ultima_actividad = timezone.now()
                
                # Inicializar datos de progreso
                monitoreo.preguntas_respondidas = 0
                monitoreo.preguntas_revisadas = len(preguntas_mostradas)
                
                monitoreo.save()
                print(f"Activando monitoreo para {participante.NombresCompletos} - Iniciando nuevo intento {siguiente_intento}")
                print(f"DEBUG - Inicializando monitoreo: 0/{len(preguntas_mostradas)} preguntas")
        except Exception as e:
            print(f"Error al activar monitoreo: {e}")
            pass
    
    context = {
        'evaluacion': evaluacion,
        'preguntas': preguntas_mostradas,
        'resultado': resultado_activo,
        'tiempo_total': evaluacion.duration_minutes * 60,  # en segundos
        'continuar_evaluacion': continuar_evaluacion
    }
    
    # Logging para debugging del contexto
    if resultado_activo:
        print(f"DEBUG - Contexto resultado tiene respuestas_guardadas: {resultado_activo.respuestas_guardadas}")
        print(f"DEBUG - continuar_evaluacion: {continuar_evaluacion}")
    
    return render(request, 'quizzes/take_quiz.html', context)

@csrf_exempt
@login_required
def guardar_respuesta_automatica(request, pk):
    """
    Vista para guardado automático de respuestas
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        evaluacion = get_object_or_404(Evaluacion, pk=pk)
        participante = Participantes.objects.get(user=request.user)
        
        # Verificar que el participante esté autorizado
        participantes_autorizados = evaluacion.get_participantes_autorizados()
        if participante not in participantes_autorizados:
            return JsonResponse({'success': False, 'error': 'No autorizado'})
        
        # Verificar si la evaluación fue finalizada administrativamente
        monitoreo_existente = MonitoreoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            estado='finalizado'
        ).first()
        
        if monitoreo_existente and monitoreo_existente.finalizado_por_admin:
            return JsonResponse({
                'success': False, 
                'error': 'Evaluación finalizada administrativamente',
                'redirect': True
            })
        
        # Obtener o crear resultado activo (no completado)
        resultado, created = ResultadoEvaluacion.objects.get_or_create(
            evaluacion=evaluacion,
            participante=participante,
            completada=False,
            defaults={
                'fecha_inicio': timezone.now(),
                'tiempo_restante': evaluacion.duration_minutes * 60
            }
        )
        
        # Si no se creó nuevo y no tiene tiempo_restante, asignarlo
        if not created and not resultado.tiempo_restante:
            resultado.tiempo_restante = evaluacion.duration_minutes * 60
            resultado.save()
        
        # Verificación adicional: No permitir guardado si ya está completada
        if resultado.completada:
            return JsonResponse({
                'success': False, 
                'error': 'Esta evaluación ya ha sido completada',
                'redirect': True
            })
        
        # Actualizar respuestas guardadas
        import json
        data = json.loads(request.body.decode('utf-8'))
        respuestas = data.get('respuestas', {})
        tiempo_restante = data.get('tiempo_restante', evaluacion.duration_minutes * 60)
        
        # Asegurar que respuestas_guardadas esté inicializado
        if resultado.respuestas_guardadas is None:
            resultado.respuestas_guardadas = {}
        
        # Logging para debugging
        print(f"DEBUG - Guardando respuestas para {participante.NombresCompletos}: {respuestas}")
        print(f"DEBUG - Respuestas anteriores: {resultado.respuestas_guardadas}")
        
        # Hacer una copia del diccionario para evitar problemas de referencia
        respuestas_actualizadas = resultado.respuestas_guardadas.copy()
        respuestas_actualizadas.update(respuestas)
        
        resultado.respuestas_guardadas = respuestas_actualizadas
        resultado.tiempo_restante = tiempo_restante
        resultado.ultima_actividad = timezone.now()
        resultado.save()
        
        # Verificar que se guardó correctamente
        resultado.refresh_from_db()
        print(f"DEBUG - Respuestas después de guardar (verificación): {resultado.respuestas_guardadas}")
        
        # Actualizar monitoreo
        try:
            monitoreo, created = MonitoreoEvaluacion.objects.get_or_create(
                evaluacion=evaluacion,
                participante=participante,
                defaults={'resultado': resultado}
            )
            
            # Si no se creó nuevo, actualizar el resultado si es necesario
            if not created and not monitoreo.resultado:
                monitoreo.resultado = resultado
                monitoreo.save()
            
            # Calcular estadísticas del monitoreo
            preguntas_respondidas = len([r for r in respuestas.values() if r])
            preguntas_mostradas = evaluacion.get_preguntas_para_estudiante(participante.id)
            total_preguntas = len(preguntas_mostradas)
            
            # Actualizar datos del monitoreo
            monitoreo.preguntas_respondidas = preguntas_respondidas
            monitoreo.preguntas_revisadas = total_preguntas
            monitoreo.tiempo_activo += 30  # Asumir 30 segundos de actividad por guardado
            monitoreo.ultima_actividad = timezone.now()
            monitoreo.save()
            
            print(f"DEBUG - Monitoreo actualizado: {preguntas_respondidas}/{total_preguntas} preguntas")
            
        except Exception as e:
            # Si hay error al actualizar el monitoreo, continuar sin él
            print(f"DEBUG - Error al actualizar monitoreo: {e}")
            pass
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
def registrar_cambio_pestana(request, pk):
    """
    Vista para registrar cambios de pestaña durante la evaluación
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        evaluacion = get_object_or_404(Evaluacion, pk=pk)
        participante = Participantes.objects.get(user=request.user)
        
        # Verificar que el participante esté autorizado
        participantes_autorizados = evaluacion.get_participantes_autorizados()
        if participante not in participantes_autorizados:
            return JsonResponse({'success': False, 'error': 'No autorizado'})
        
        # Verificar si la evaluación fue finalizada administrativamente
        monitoreo_existente = MonitoreoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            estado='finalizado'
        ).first()
        
        if monitoreo_existente and monitoreo_existente.finalizado_por_admin:
            return JsonResponse({
                'success': False, 
                'error': 'Evaluación finalizada administrativamente',
                'redirect': True
            })
        
        # Obtener resultado actual
        resultado = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            completada=False
        ).first()
        
        if not resultado:
            return JsonResponse({
                'success': False, 
                'error': 'No se encontró una evaluación activa'
            })
        
        # Procesar datos del cambio de pestaña
        import json
        data = json.loads(request.body.decode('utf-8'))
        cambios_pestana = data.get('cambios_pestana', 0)
        tiempo_restante = data.get('tiempo_restante', 0)
        
        # Actualizar información de cambios de pestaña en el resultado
        if not hasattr(resultado, 'cambios_pestana') or resultado.cambios_pestana is None:
            resultado.cambios_pestana = 0
            
        resultado.cambios_pestana = cambios_pestana
        resultado.tiempo_restante = tiempo_restante
        resultado.ultima_actividad = timezone.now()
        resultado.save()
        
        # Actualizar monitoreo con información del cambio de pestaña
        try:
            monitoreo, created = MonitoreoEvaluacion.objects.get_or_create(
                evaluacion=evaluacion,
                participante=participante,
                defaults={'resultado': resultado}
            )
            
            if not created and not monitoreo.resultado:
                monitoreo.resultado = resultado
                monitoreo.save()
            
            # Registrar alerta de cambio de pestaña
            from datetime import datetime
            alerta_texto = f"Cambio de pestaña #{cambios_pestana} - Tiempo restante: {tiempo_restante//60}:{tiempo_restante%60:02d}"
            
            if monitoreo.alertas is None:
                monitoreo.alertas = []
            
            monitoreo.alertas.append({
                'tipo': 'cambio_pestana',
                'mensaje': alerta_texto,
                'timestamp': datetime.now().isoformat(),
                'cambio_numero': cambios_pestana,
                'tiempo_restante': tiempo_restante
            })
            
            monitoreo.cambios_pestana = cambios_pestana
            monitoreo.ultima_actividad = timezone.now()
            monitoreo.save()
            
            print(f"DEBUG - Cambio de pestaña #{cambios_pestana} registrado para {participante.NombresCompletos}")
            
        except Exception as e:
            print(f"DEBUG - Error al actualizar monitoreo con cambio de pestaña: {e}")
            pass
        
        return JsonResponse({
            'success': True,
            'cambios_pestana': cambios_pestana,
            'mensaje': f'Cambio de pestaña #{cambios_pestana} registrado'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
def verificar_estado_evaluacion(request, pk):
    """
    Endpoint para verificar si la evaluación fue finalizada administrativamente
    y obtener el estado actualizado de cambios de pestañas
    """
    try:
        evaluacion = get_object_or_404(Evaluacion, pk=pk)
        participante = Participantes.objects.get(user=request.user)
        
        # Obtener resultado activo (no completado)
        resultado_activo = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            completada=False
        ).first()
        
        # Verificar si la evaluación fue finalizada administrativamente
        monitoreo = MonitoreoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            estado='finalizado'
        ).first()
        
        response_data = {'finalizada_admin': False}
        
        if monitoreo and monitoreo.finalizado_por_admin:
            response_data.update({
                'finalizada_admin': True,
                'motivo': monitoreo.motivo_finalizacion,
                'admin': monitoreo.finalizado_por_admin.get_full_name() or monitoreo.finalizado_por_admin.username
            })
        
        # Incluir información actualizada de cambios de pestañas si hay resultado activo
        if resultado_activo:
            cambios_actuales = getattr(resultado_activo, 'cambios_pestana', 0) or 0
            response_data.update({
                'cambios_pestana_actuales': cambios_actuales,
                'cambios_pestana_maximo': 3
            })
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'finalizada_admin': False, 'error': str(e)})

@csrf_exempt
@login_required
def obtener_progreso_evaluacion(request, pk):
    """
    Vista para obtener progreso guardado de una evaluación
    """
    try:
        evaluacion = get_object_or_404(Evaluacion, pk=pk)
        participante = Participantes.objects.get(user=request.user)
        
        resultado = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            completada=False
        ).first()
        
        if resultado:
            return JsonResponse({
                'success': True,
                'respuestas': resultado.respuestas_guardadas,
                'tiempo_restante': resultado.tiempo_restante,
                'ultima_actividad': resultado.ultima_actividad.isoformat()
            })
        else:
            return JsonResponse({
                'success': True,
                'respuestas': {},
                'tiempo_restante': evaluacion.duration_minutes * 60,
                'ultima_actividad': None
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

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
        context['has_full_access'] = True  # Todos los administradores tienen acceso completo
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
        
        # Verificar si la cédula ya existe (global)
        if Participantes.objects.filter(cedula=cedula).exists():
            messages.error(request, f"La cédula {cedula} ya está registrada por otro participante.")
            return redirect('quizzes:manage_participants')
        
        # Convertir edad vacía a None
        if edad == '':
            edad = None
        elif edad:
            try:
                edad = int(edad)
            except ValueError:
                messages.error(request, "La edad debe ser un número válido.")
                return redirect('quizzes:manage_participants')
        
        # Crear el participante con manejo de validaciones
        try:
            participante, password = Participantes.create_participant(cedula, NombresCompletos, email, phone, edad)
            messages.success(request, f"Participante {NombresCompletos} creado correctamente.")
            return redirect('quizzes:manage_participants')
        except ValidationError as e:
            error_message = extract_validation_error_message(e)
            messages.error(request, f"{error_message}")
            return redirect('quizzes:manage_participants')
        except Exception as e:
            messages.error(request, f"Error inesperado al crear participante: {str(e)}")
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
        
        # Verificar si la nueva cédula ya existe en otro participante (global)
        if cedula != participante.cedula:
            if Participantes.objects.filter(cedula=cedula).exclude(id=participante.id).exists():
                messages.error(request, f"La cédula {cedula} ya está registrada por otro participante.")
                return redirect('quizzes:manage_participants')
        
        # Validar correo único si cambió
        if email != participante.email:  # Solo verificar si el correo cambió
            email_normalized = email.lower().strip()
            
            # Verificar si ya existe otro participante con este correo
            if Participantes.objects.filter(email__iexact=email_normalized).exclude(id=participante.id).exists():
                messages.error(request, f"El correo {email} ya está registrado por otro participante.")
                return redirect('quizzes:manage_participants')
            
            # Verificar conflictos con representantes
            from quizzes.models import Representante
            if Representante.objects.filter(
                models.Q(CorreoInstitucional__iexact=email_normalized) | 
                models.Q(CorreoRepresentante__iexact=email_normalized)
            ).exists():
                messages.error(request, f"El correo {email} ya está siendo usado por un representante.")
                return redirect('quizzes:manage_participants')
        
        # Convertir edad vacía a None
        if edad == '':
            edad = None
        elif edad:
            try:
                edad = int(edad)
            except ValueError:
                messages.error(request, "La edad debe ser un número válido.")
                return redirect('quizzes:manage_participants')
        
        try:
            # Usar transacción para asegurar consistencia
            from django.db import transaction
            with transaction.atomic():
                # Mantener username igual a la cédula
                user_obj.username = cedula
                user_obj.first_name = NombresCompletos
                user_obj.email = email.lower().strip()  # Normalizar correo
                participante.cedula = cedula
                participante.NombresCompletos = NombresCompletos
                participante.email = email.lower().strip()  # Normalizar correo
                participante.phone = phone
                participante.edad = edad
                
                # Validar y guardar
                user_obj.full_clean()
                participante.full_clean()
                user_obj.save()
                participante.save()
                
            messages.success(request, f"Participante {NombresCompletos} actualizado correctamente.")
            return redirect('quizzes:manage_participants')
            
        except ValidationError as e:
            error_message = extract_validation_error_message(e)
            messages.error(request, f"Error de validación: {error_message}")
            return redirect('quizzes:manage_participants')
        except IntegrityError as e:
            if 'email' in str(e).lower():
                messages.error(request, 'El correo electrónico ya está en uso.')
            elif 'cedula' in str(e).lower():
                messages.error(request, 'La cédula ya está registrada.')
            else:
                messages.error(request, 'Error de integridad en la base de datos.')
            return redirect('quizzes:manage_participants')
        except Exception as e:
            messages.error(request, f'Error inesperado al actualizar participante: {str(e)}')
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
        
        # Validar campos obligatorios
        if not username or not first_name or not email:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('quizzes:manage_admins')
        
        # Normalizar email
        email_normalized = email.lower().strip()
        
        # Verificar si el username ya existe
        if User.objects.filter(username=username).exists():
            messages.error(request, f"El nombre de usuario '{username}' ya está registrado por otro usuario.")
            return redirect('quizzes:manage_admins')
        
        # Verificar si el email ya existe
        if User.objects.filter(email__iexact=email_normalized).exists():
            messages.error(request, f"El correo electrónico '{email}' ya está registrado por otro usuario.")
            return redirect('quizzes:manage_admins')
        
        # Verificar conflictos con participantes y representantes
        if Participantes.objects.filter(email__iexact=email_normalized).exists():
            messages.error(request, f"El correo '{email}' ya está siendo usado por un participante.")
            return redirect('quizzes:manage_admins')
        
        if Representante.objects.filter(
            models.Q(CorreoInstitucional__iexact=email_normalized) | 
            models.Q(CorreoRepresentante__iexact=email_normalized)
        ).exists():
            messages.error(request, f"El correo '{email}' ya está siendo usado por un representante.")
            return redirect('quizzes:manage_admins')
        
        try:
            password = get_random_string(length=8)
            new_user = User.objects.create_user(
                username=username, 
                password=password, 
                first_name=first_name, 
                last_name=last_name, 
                email=email_normalized
            )
            admin_profile = AdminProfile.objects.create(user=new_user, created_by=user, password=password)
            messages.success(request, f"Administrador {first_name} {last_name} creado correctamente.")
            return redirect('quizzes:manage_admins')
        except IntegrityError as e:
            if 'username' in str(e).lower():
                messages.error(request, 'El nombre de usuario ya está en uso.')
            elif 'email' in str(e).lower():
                messages.error(request, 'El correo electrónico ya está en uso.')
            else:
                messages.error(request, 'Error de integridad en la base de datos.')
            return redirect('quizzes:manage_admins')
        except Exception as e:
            messages.error(request, f'Error inesperado al crear administrador: {str(e)}')
            return redirect('quizzes:manage_admins')

    # Editar admin
    if request.method == 'POST' and request.POST.get('edit_id'):
        edit_id = request.POST.get('edit_id')
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        
        # Validar campos obligatorios
        if not username or not first_name or not email:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('quizzes:manage_admins')
        
        try:
            admin = AdminProfile.objects.select_related('user').get(id=edit_id)
            user_obj = admin.user
            
            # Normalizar email
            email_normalized = email.lower().strip()
            
            # Verificar si el nuevo username ya existe en otro usuario
            if username != user_obj.username and User.objects.filter(username=username).exists():
                messages.error(request, f"El nombre de usuario '{username}' ya está registrado por otro usuario.")
                return redirect('quizzes:manage_admins')
            
            # Verificar si el nuevo email ya existe en otro usuario
            if email_normalized != user_obj.email and User.objects.filter(email__iexact=email_normalized).exists():
                messages.error(request, f"El correo electrónico '{email}' ya está registrado por otro usuario.")
                return redirect('quizzes:manage_admins')
            
            # Verificar conflictos con participantes y representantes
            if email_normalized != user_obj.email:
                if Participantes.objects.filter(email__iexact=email_normalized).exists():
                    messages.error(request, f"El correo '{email}' ya está siendo usado por un participante.")
                    return redirect('quizzes:manage_admins')
                
                if Representante.objects.filter(
                    models.Q(CorreoInstitucional__iexact=email_normalized) | 
                    models.Q(CorreoRepresentante__iexact=email_normalized)
                ).exists():
                    messages.error(request, f"El correo '{email}' ya está siendo usado por un representante.")
                    return redirect('quizzes:manage_admins')
            
            # Usar transacción para asegurar consistencia
            from django.db import transaction
            with transaction.atomic():
                user_obj.username = username
                user_obj.first_name = first_name
                user_obj.last_name = last_name
                user_obj.email = email_normalized
                
                # Validar y guardar
                user_obj.full_clean()
                user_obj.save()
            
            messages.success(request, f"Administrador {first_name} {last_name} actualizado correctamente.")
            return redirect('quizzes:manage_admins')
            
        except AdminProfile.DoesNotExist:
            messages.error(request, 'Administrador no encontrado.')
            return redirect('quizzes:manage_admins')
        except ValidationError as e:
            error_message = extract_validation_error_message(e)
            messages.error(request, f"Error de validación: {error_message}")
            return redirect('quizzes:manage_admins')
        except IntegrityError as e:
            if 'username' in str(e).lower():
                messages.error(request, 'El nombre de usuario ya está en uso.')
            elif 'email' in str(e).lower():
                messages.error(request, 'El correo electrónico ya está en uso.')
            else:
                messages.error(request, 'Error de integridad en la base de datos.')
            return redirect('quizzes:manage_admins')
        except Exception as e:
            messages.error(request, f'Error inesperado al actualizar administrador: {str(e)}')
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

def extract_validation_error_message(validation_error):
    """
    Extrae el mensaje de error de un ValidationError de manera segura
    
    Args:
        validation_error: La excepción ValidationError
    
    Returns:
        str: El mensaje de error como cadena simple
    """
    if hasattr(validation_error, 'message_dict'):
        # Si es un diccionario de errores, tomar el primer mensaje
        if validation_error.message_dict:
            first_field = list(validation_error.message_dict.keys())[0]
            first_messages = validation_error.message_dict[first_field]
            if isinstance(first_messages, list) and first_messages:
                return first_messages[0]
            else:
                return str(first_messages)
        else:
            return str(validation_error)
    elif hasattr(validation_error, 'messages') and validation_error.messages:
        # Si es una lista de mensajes, tomar el primero
        if isinstance(validation_error.messages, list) and validation_error.messages:
            return validation_error.messages[0]
        else:
            return str(validation_error.messages)
    else:
        # Si es un mensaje simple
        return str(validation_error)

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
            
            # Validar campos obligatorios
            required_fields = ['NombreColegio', 'DireccionColegio', 'TelefonoInstitucional', 
                             'CorreoInstitucional', 'NombresRepresentante', 'TelefonoRepresentante', 
                             'CorreoRepresentante']
            for field in required_fields:
                if not data.get(field):
                    messages.error(request, f"El campo {field} es obligatorio.")
                    return redirect('quizzes:manage_representantes')
            
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
            
            # Normalizar correos
            correo_inst = data.get('CorreoInstitucional').lower().strip()
            correo_rep = data.get('CorreoRepresentante').lower().strip()
            
            # Verificar conflictos con otros modelos usando la función de validación
            try:
                from .models import validate_email_across_all_models
                validate_email_across_all_models(correo_inst)
                validate_email_across_all_models(correo_rep)
            except ValidationError as e:
                error_message = extract_validation_error_message(e)
                messages.error(request, error_message)
                return redirect('quizzes:manage_representantes')
            
            try:
                # Usar transacción para asegurar consistencia
                from django.db import transaction
                with transaction.atomic():
                    representante = Representante.objects.create(
                        NombreColegio=data.get('NombreColegio'),
                        DireccionColegio=data.get('DireccionColegio'),
                        TelefonoInstitucional=telefono_inst,
                        CorreoInstitucional=correo_inst,
                        NombresRepresentante=data.get('NombresRepresentante'),
                        TelefonoRepresentante=telefono_rep,
                        CorreoRepresentante=correo_rep,
                    )
                    # Validar el objeto creado
                    representante.full_clean()
                
                messages.success(request, 'Representante registrado exitosamente.')
                return redirect('quizzes:manage_representantes')
                
            except ValidationError as e:
                error_message = extract_validation_error_message(e)
                messages.error(request, f"Error de validación: {error_message}")
                return redirect('quizzes:manage_representantes')
            except IntegrityError as e:
                if 'correo' in str(e).lower():
                    messages.error(request, 'Uno de los correos ya está en uso.')
                else:
                    messages.error(request, 'Error de integridad en la base de datos.')
                return redirect('quizzes:manage_representantes')
            except Exception as e:
                messages.error(request, f'Error inesperado al crear representante: {str(e)}')
                return redirect('quizzes:manage_representantes')
        
        # Editar representante
        elif request.POST.get('edit_id'):
            edit_id = request.POST.get('edit_id')
            data = request.POST
            
            # Validar campos obligatorios
            required_fields = ['NombreColegio', 'DireccionColegio', 'TelefonoInstitucional', 
                             'CorreoInstitucional', 'NombresRepresentante', 'TelefonoRepresentante', 
                             'CorreoRepresentante']
            for field in required_fields:
                if not data.get(field):
                    messages.error(request, f"El campo {field} es obligatorio.")
                    return redirect('quizzes:manage_representantes')
            
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
            
            try:
                representante = Representante.objects.get(id=edit_id)
                
                # Normalizar correos
                correo_inst = data.get('CorreoInstitucional').lower().strip()
                correo_rep = data.get('CorreoRepresentante').lower().strip()
                
                # Verificar conflictos solo si los correos cambiaron
                if correo_inst != representante.CorreoInstitucional:
                    try:
                        from .models import validate_email_across_all_models
                        validate_email_across_all_models(correo_inst, exclude_representante_id=representante.id)
                    except ValidationError as e:
                        error_message = extract_validation_error_message(e)
                        messages.error(request, error_message)
                        return redirect('quizzes:manage_representantes')
                
                if correo_rep != representante.CorreoRepresentante:
                    try:
                        from .models import validate_email_across_all_models
                        validate_email_across_all_models(correo_rep, exclude_representante_id=representante.id)
                    except ValidationError as e:
                        error_message = extract_validation_error_message(e)
                        messages.error(request, error_message)
                        return redirect('quizzes:manage_representantes')
                
                # Usar transacción para asegurar consistencia
                from django.db import transaction
                with transaction.atomic():
                    representante.NombreColegio = data.get('NombreColegio')
                    representante.DireccionColegio = data.get('DireccionColegio')
                    representante.TelefonoInstitucional = telefono_inst
                    representante.CorreoInstitucional = correo_inst
                    representante.NombresRepresentante = data.get('NombresRepresentante')
                    representante.TelefonoRepresentante = telefono_rep
                    representante.CorreoRepresentante = correo_rep
                    
                    # Validar y guardar
                    representante.full_clean()
                    representante.save()
                
                messages.success(request, 'Representante actualizado exitosamente.')
                return redirect('quizzes:manage_representantes')
                
            except Representante.DoesNotExist:
                messages.error(request, 'Representante no encontrado.')
                return redirect('quizzes:manage_representantes')
            except ValidationError as e:
                error_message = extract_validation_error_message(e)
                messages.error(request, f"Error de validación: {error_message}")
                return redirect('quizzes:manage_representantes')
            except IntegrityError as e:
                if 'correo' in str(e).lower():
                    messages.error(request, 'Uno de los correos ya está en uso.')
                else:
                    messages.error(request, 'Error de integridad en la base de datos.')
                return redirect('quizzes:manage_representantes')
            except Exception as e:
                messages.error(request, f'Error inesperado al actualizar representante: {str(e)}')
                return redirect('quizzes:manage_representantes')

    from .models import SystemConfig
    representantes = Representante.objects.filter(anio=SystemConfig.get_active_year())
    
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

    from .models import SystemConfig
    grupos = GrupoParticipantes.objects.select_related('representante').prefetch_related('participantes').filter(anio=SystemConfig.get_active_year())
    
    # Obtener representantes disponibles (que no están en ningún grupo)
    representantes_disponibles = Representante.objects.filter(grupos__isnull=True, anio=SystemConfig.get_active_year())
    
    # Obtener todos los representantes para mostrar en modales de edición
    representantes_todos = Representante.objects.filter(anio=SystemConfig.get_active_year())
    
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
                else:
                    # Validar que el correo no esté duplicado
                    email_normalized = row_data['email'].lower().strip()
                    
                    # Verificar si ya existe un participante con este correo
                    if Participantes.objects.filter(email__iexact=email_normalized).exists():
                        row_errors.append(f'Ya existe un participante con el correo "{row_data["email"]}"')
                    
                    # Verificar si el correo está siendo usado por un representante
                    if Representante.objects.filter(
                        Q(CorreoInstitucional__iexact=email_normalized) |
                        Q(CorreoRepresentante__iexact=email_normalized)
                    ).exists():
                        row_errors.append(f'El correo "{row_data["email"]}" ya está siendo usado por un representante')
                
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


@login_required
def quiz_view(request):
    """
    Vista que maneja las evaluaciones según el rol del usuario:
    - Superuser: muestra manage_quizs.html para gestionar evaluaciones
    - Admin (con o sin acceso_total): muestra manage_quizs.html para gestionar evaluaciones
    - Estudiante: muestra quiz.html para ver evaluaciones disponibles
    """
    user = request.user
    
    # Determinar el tipo de usuario
    is_admin = user.is_superuser or AdminProfile.objects.filter(user=user).exists()
    
    if is_admin:
        # Es admin (superuser, admin con acceso_total, o admin sin acceso_total) - mostrar gestión de evaluaciones
        return manage_quizs(request)
    else:
        # Es estudiante - mostrar evaluaciones disponibles
        return student_quizs(request)

@login_required
def manage_quizs(request):
    """
    Vista para que los administradores gestionen las evaluaciones
    Acceso permitido para:
    - Superuser
    - Admin con acceso_total = True
    - Admin con acceso_total = False
    """
    user = request.user
    
    # Verificar que sea admin (superuser o admin con perfil)
    is_superuser = user.is_superuser
    is_admin = AdminProfile.objects.filter(user=user).exists()
    
    if not (is_superuser or is_admin):
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('quizzes:dashboard')
    
    # Obtener evaluaciones del año activo
    from .models import SystemConfig
    evaluaciones = Evaluacion.objects.filter(anio=SystemConfig.get_active_year()).order_by('-start_time')
    
    # Determinar el tipo específico de admin para el contexto
    if is_superuser:
        admin_type = 'superuser'
        has_full_access = True
    elif is_admin:
        admin_profile = AdminProfile.objects.get(user=user)
        admin_type = 'admin_full' if admin_profile.acceso_total else 'admin_limited'
        has_full_access = True  # Todos los administradores tienen acceso completo
    else:
        admin_type = 'unknown'
        has_full_access = False
    
    context = {
        'evaluaciones': evaluaciones,
        'role': 'admin',
        'admin_type': admin_type,
        'has_full_access': has_full_access,
        'num_etapas': SystemConfig.get_num_etapas(),
        'now': timezone.now(),
        'user': user
    }
    
    return render(request, 'quizzes/manage_quizs.html', context)

@login_required
def student_quizs(request):
    """
    Vista para que los estudiantes vean las evaluaciones disponibles
    """
    # Verificar que sea estudiante
    if not Participantes.objects.filter(user=request.user).exists():
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('quizzes:dashboard')
    
    participante = Participantes.objects.get(user=request.user)
    
    # Obtener evaluaciones del año activo
    from .models import SystemConfig
    todas_evaluaciones = Evaluacion.objects.filter(anio=SystemConfig.get_active_year()).order_by('etapa', 'start_time')
    
    # Filtrar evaluaciones autorizadas para este participante y agregar información de estado
    evaluaciones_autorizadas = []
    for evaluacion in todas_evaluaciones:
        participantes_autorizados = evaluacion.get_participantes_autorizados()
        if participante in participantes_autorizados:
            # Verificar si hay un intento en progreso con tiempo restante
            resultado_activo = evaluacion.resultados.filter(
                participante=participante, 
                completada=False
            ).first()
            
            puede_continuar = False
            puede_iniciar = False
            
            if resultado_activo:
                # Calcular tiempo transcurrido desde el inicio
                tiempo_transcurrido = (timezone.now() - resultado_activo.fecha_inicio).total_seconds()
                tiempo_total = evaluacion.duration_minutes * 60  # en segundos
                tiempo_restante = max(0, tiempo_total - tiempo_transcurrido)
                
                # Si aún hay tiempo restante, puede continuar (sin importar la ventana de acceso)
                if tiempo_restante > 0:
                    puede_continuar = True
            else:
                # Si no hay intento activo, verificar si puede iniciar uno nuevo
                # Verificar ventana de acceso Y intentos disponibles
                if evaluacion.is_available():
                    # Verificar si tiene intentos disponibles
                    intentos_disponibles = participante.get_intentos_disponibles(evaluacion)
                    if intentos_disponibles > 0:
                        puede_iniciar = True
            
            # Obtener el mejor resultado completado (si existe) para mostrar información
            mejor_resultado = ResultadoEvaluacion.get_mejor_resultado(evaluacion, participante)
            
            # Obtener información de intentos
            intentos_disponibles = participante.get_intentos_disponibles(evaluacion)
            intentos_usados = participante.get_intentos_usados(evaluacion)
            intentos_totales = intentos_disponibles + intentos_usados
            
            evaluaciones_autorizadas.append({
                'evaluacion': evaluacion,
                'resultado_activo': resultado_activo,  # Intento en progreso
                'mejor_resultado': mejor_resultado,    # Mejor intento completado
                'puede_continuar': puede_continuar,
                'puede_iniciar': puede_iniciar,
                'intentos_disponibles': intentos_disponibles,
                'intentos_usados': intentos_usados,
                'intentos_totales': intentos_totales
            })
    
    context = {
        'evaluaciones': evaluaciones_autorizadas,
        'role': 'student',
        'current_time': timezone.now(),
        'now': timezone.now(),
        'participante': participante
    }
    return render(request, 'quizzes/quiz.html', context)

@login_required
def student_results(request):
    """
    Vista para que los estudiantes vean sus resultados
    """
    # Verificar que sea estudiante
    if not Participantes.objects.filter(user=request.user).exists():
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('quizzes:dashboard')
    
    participante = Participantes.objects.get(user=request.user)
    
    # Obtener resultados del participante
    resultados = ResultadoEvaluacion.objects.filter(
        participante=participante,
        completada=True
    ).select_related('evaluacion').order_by('evaluacion__etapa', '-fecha_fin')
    
    context = {
        'participante': participante,
        'resultados': resultados,
        'role': 'student'
    }
    return render(request, 'quizzes/student_results.html', context)

@login_required
def manage_questions(request, eval_id):
    """
    Vista para gestionar las preguntas de una evaluación específica
    """
    evaluacion = get_object_or_404(Evaluacion, pk=eval_id)
    # Optimizar consulta para incluir opciones y evitar N+1
    preguntas = evaluacion.preguntas.prefetch_related('opciones').order_by('id')
    context = {
        'evaluacion': evaluacion,
        'preguntas': preguntas
    }
    return render(request, 'quizzes/manage_questions.html', context)

@csrf_exempt
@login_required
def create_evaluacion(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body.decode('utf-8'))
        title = data.get('title')
        etapa = data.get('etapa')
        start_date = data.get('start_date')
        start_time = data.get('start_time')
        end_date = data.get('end_date')
        end_time = data.get('end_time')
        duration = data.get('duration')
        preguntas_a_mostrar = data.get('preguntas_a_mostrar', 10)
        description = data.get('description', '')
        
        from datetime import datetime
        from django.utils import timezone
        try:
            start_dt = timezone.make_aware(datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M"))
            end_dt = timezone.make_aware(datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M"))
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Formato de fecha/hora inválido.'}, status=400)
        
        if not title or not etapa or not duration or not start_date or not start_time or not end_date or not end_time:
            return JsonResponse({'success': False, 'error': 'Faltan campos obligatorios.'}, status=400)
        
        # Validar etapa
        try:
            from .models import SystemConfig
            etapa = int(etapa)
            allowed_etapas = [1, 3] if SystemConfig.get_num_etapas() == 2 else [1, 2, 3]
            if etapa not in allowed_etapas:
                return JsonResponse({'success': False, 'error': 'Etapa inválida para la configuración actual.'}, status=400)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Etapa debe ser un número.'}, status=400)
        
        # Validar preguntas a mostrar
        try:
            preguntas_a_mostrar = int(preguntas_a_mostrar)
            if preguntas_a_mostrar < 1 or preguntas_a_mostrar > 100:
                return JsonResponse({'success': False, 'error': 'Preguntas a mostrar debe estar entre 1 y 100.'}, status=400)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Preguntas a mostrar debe ser un número.'}, status=400)
        
        try:
            evaluacion = Evaluacion.objects.create(
                title=title,
                etapa=etapa,
                start_time=start_dt,
                end_time=end_dt,
                duration_minutes=int(duration),
                preguntas_a_mostrar=preguntas_a_mostrar
            )
            return JsonResponse({
                'success': True, 
                'id': evaluacion.id, 
                'title': evaluacion.title,
                'etapa': evaluacion.etapa,
                'etapa_display': evaluacion.get_etapa_display()
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

@csrf_exempt
@login_required
def upload_image(request):
    """
    Vista para subir imágenes desde CKEditor
    """
    if request.method == 'POST':
        if request.FILES.get('upload'):
            uploaded_file = request.FILES['upload']
            
            # Validar que sea una imagen (permitir más formatos)
            allowed_types = [
                'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
                'image/bmp', 'image/webp', 'image/tiff', 'image/svg+xml'
            ]
            
            # Si el content_type no está en la lista, verificar la extensión del archivo
            if uploaded_file.content_type not in allowed_types:
                # Verificar extensión del archivo como respaldo
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg']
                
                if file_extension not in allowed_extensions:
                    return JsonResponse({
                        'error': {
                            'message': f'Formato de imagen no soportado. Formatos permitidos: JPEG, PNG, GIF, BMP, WebP, TIFF, SVG'
                        }
                    }, status=400)
            
            # Crear directorio si no existe en media/ckeditor_uploads
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'ckeditor_uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generar nombre único para el archivo
            import uuid
            file_extension = os.path.splitext(uploaded_file.name)[1]
            filename = f"{uuid.uuid4()}{file_extension}"
            filepath = os.path.join(upload_dir, filename)
            
            # Guardar el archivo
            with open(filepath, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Retornar URL para CKEditor (usando media URL)
            file_url = f"{settings.MEDIA_URL}ckeditor_uploads/{filename}"
            
            return JsonResponse({
                'url': file_url,
                'uploaded': 1,
                'fileName': filename
            })
        else:
            return JsonResponse({
                'error': {
                    'message': 'No se recibió ningún archivo'
                }
            }, status=400)
    
    return JsonResponse({
        'error': {
            'message': 'Método no permitido'
        }
    }, status=405)

@csrf_exempt
@login_required
def save_question(request, eval_id):
    """
    Vista para guardar una pregunta y sus opciones
    """
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body.decode('utf-8'))
            
            # Obtener la evaluación
            evaluacion = get_object_or_404(Evaluacion, pk=eval_id)
            
            # Obtener datos del formulario
            pregunta_texto = data.get('pregunta', '').strip()
            opciones = data.get('opciones', [])
            opcion_correcta = data.get('opcion_correcta')
            puntos = data.get('puntos', 1)
            
            # Validaciones
            if not pregunta_texto:
                return JsonResponse({
                    'success': False, 
                    'error': 'El enunciado de la pregunta es obligatorio'
                }, status=400)
            
            if len(opciones) != 4:
                return JsonResponse({
                    'success': False, 
                    'error': 'Debe proporcionar exactamente 4 opciones'
                }, status=400)
            
            if not opcion_correcta or not opcion_correcta.isdigit() or int(opcion_correcta) < 1 or int(opcion_correcta) > 4:
                return JsonResponse({
                    'success': False, 
                    'error': 'Debe seleccionar una opción correcta válida'
                }, status=400)
            
            # Validar puntos
            try:
                puntos = int(puntos)
                if puntos < 1 or puntos > 10:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Los puntos deben estar entre 1 y 10'
                    }, status=400)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False, 
                    'error': 'Los puntos deben ser un número válido'
                }, status=400)
            
            # Crear la pregunta
            pregunta = Pregunta.objects.create(
                evaluacion=evaluacion,
                text=pregunta_texto,
                puntos=puntos
            )
            
            # Validar que todas las opciones tengan contenido
            for i, opcion_texto in enumerate(opciones):
                if not opcion_texto.strip():
                    return JsonResponse({
                        'success': False, 
                        'error': f'La opción {chr(65 + i)} ({"ABCD"[i]}) es obligatoria'
                    }, status=400)
            
            # Crear las opciones
            opcion_correcta_index = int(opcion_correcta) - 1  # Convertir a índice 0-based
            
            for i, opcion_texto in enumerate(opciones):
                Opcion.objects.create(
                    pregunta=pregunta,
                    text=opcion_texto.strip(),
                    is_correct=(i == opcion_correcta_index)
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Pregunta guardada exitosamente',
                'pregunta_id': pregunta.id,
                'total_preguntas': evaluacion.preguntas.count()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'error': 'Datos JSON inválidos'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error al guardar la pregunta: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False, 
        'error': 'Método no permitido'
    }, status=405)

@csrf_exempt
@login_required
def delete_question(request, pk):
    """
    Vista para eliminar una pregunta y sus opciones
    """
    if request.method == 'POST':
        try:
            pregunta = get_object_or_404(Pregunta, pk=pk)
            evaluacion = pregunta.evaluacion
            
            # Eliminar la pregunta (esto también eliminará las opciones por CASCADE)
            pregunta.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Pregunta eliminada exitosamente',
                'total_preguntas': evaluacion.preguntas.count()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error al eliminar la pregunta: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False, 
        'error': 'Método no permitido'
    }, status=405)


@csrf_exempt
@login_required
def get_question_data(request, pk):
    """
    Vista para obtener los datos de una pregunta para edición
    """
    if request.method == 'GET':
        try:
            pregunta = get_object_or_404(Pregunta, pk=pk)
            opciones = pregunta.opciones.all().order_by('id')
            
            # Encontrar la opción correcta
            opcion_correcta = None
            for i, opcion in enumerate(opciones):
                if opcion.is_correct:
                    opcion_correcta = i + 1
                    break
            
            return JsonResponse({
                'success': True,
                'data': {
                    'pregunta': pregunta.text,
                    'opciones': [opcion.text for opcion in opciones],
                    'opcion_correcta': opcion_correcta,
                    'puntos': pregunta.puntos
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error al obtener datos de la pregunta: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False, 
        'error': 'Método no permitido'
    }, status=405)


@csrf_exempt
@login_required
def update_question(request, pk):
    """
    Vista para actualizar una pregunta existente
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pregunta = get_object_or_404(Pregunta, pk=pk)
            
            # Validar datos
            pregunta_texto = data.get('pregunta', '').strip()
            opciones = data.get('opciones', [])
            opcion_correcta = data.get('opcion_correcta')
            puntos = data.get('puntos', 1)
            
            if not pregunta_texto:
                return JsonResponse({
                    'success': False, 
                    'error': 'El enunciado de la pregunta es obligatorio'
                }, status=400)
            
            if not opcion_correcta:
                return JsonResponse({
                    'success': False, 
                    'error': 'Debe seleccionar una opción correcta'
                }, status=400)
            
            # Validar puntos
            try:
                puntos = int(puntos)
                if puntos < 1 or puntos > 10:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Los puntos deben estar entre 1 y 10'
                    }, status=400)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False, 
                    'error': 'Los puntos deben ser un número válido'
                }, status=400)
            
            # Validar que todas las opciones tengan contenido
            for i, opcion_texto in enumerate(opciones):
                if not opcion_texto.strip():
                    return JsonResponse({
                        'success': False, 
                        'error': f'La opción {chr(65 + i)} ({"ABCD"[i]}) es obligatoria'
                    }, status=400)
            
            # Actualizar la pregunta
            pregunta.text = pregunta_texto
            pregunta.puntos = puntos
            pregunta.save()
            
            # Eliminar opciones existentes y crear nuevas
            pregunta.opciones.all().delete()
            
            # Crear las nuevas opciones
            opcion_correcta_index = int(opcion_correcta) - 1  # Convertir a índice 0-based
            
            for i, opcion_texto in enumerate(opciones):
                Opcion.objects.create(
                    pregunta=pregunta,
                    text=opcion_texto.strip(),
                    is_correct=(i == opcion_correcta_index)
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Pregunta actualizada exitosamente'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'error': 'Datos JSON inválidos'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error al actualizar la pregunta: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False, 
        'error': 'Método no permitido'
    }, status=405)

# Nuevas vistas para las opciones del dropdown de evaluaciones

@login_required
def view_evaluacion(request, pk):
    """
    Vista para ver los detalles de una evaluación
    """
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    # Verificar permisos (solo admins pueden ver detalles)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('quizzes:dashboard')
    
    context = {
        'evaluacion': evaluacion,
        'preguntas': evaluacion.preguntas.prefetch_related('opciones').all(),
        'total_preguntas': evaluacion.preguntas.count(),
        'participantes_count': Participantes.objects.count()
    }
    
    return render(request, 'quizzes/view_evaluacion.html', context)

@login_required
def edit_evaluacion(request, pk):
    """
    Vista para editar una evaluación
    """
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    # Verificar permisos básicos (solo admins pueden editar)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('quizzes:dashboard')
    
    # Todos los administradores pueden editar evaluaciones de cualquier etapa
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            # Validar datos
            title = data.get('title', '').strip()
            start_date = data.get('start_date')
            start_time = data.get('start_time')
            end_date = data.get('end_date')
            end_time = data.get('end_time')
            duration = data.get('duration')
            preguntas_a_mostrar = data.get('preguntas_a_mostrar', 10)
            
            if not all([title, start_date, start_time, end_date, end_time, duration]):
                return JsonResponse({
                    'success': False, 
                    'error': 'Todos los campos son obligatorios'
                }, status=400)
            
            # Convertir fechas
            from datetime import datetime
            start_dt = timezone.make_aware(datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M"))
            end_dt = timezone.make_aware(datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M"))
            
            # Validar que la fecha de inicio sea anterior a la de fin
            if start_dt >= end_dt:
                return JsonResponse({
                    'success': False, 
                    'error': 'La fecha de inicio debe ser anterior a la fecha de finalización'
                }, status=400)
            
            # Validar preguntas a mostrar
            try:
                preguntas_a_mostrar = int(preguntas_a_mostrar)
                if preguntas_a_mostrar < 1 or preguntas_a_mostrar > 100:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Preguntas a mostrar debe estar entre 1 y 100'
                    }, status=400)
            except ValueError:
                return JsonResponse({
                    'success': False, 
                    'error': 'Preguntas a mostrar debe ser un número'
                }, status=400)
            
            # Actualizar evaluación
            evaluacion.title = title
            evaluacion.etapa = int(data.get('etapa', evaluacion.etapa))
            evaluacion.start_time = start_dt
            evaluacion.end_time = end_dt
            evaluacion.duration_minutes = int(duration)
            evaluacion.preguntas_a_mostrar = preguntas_a_mostrar
            evaluacion.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Evaluación actualizada exitosamente',
                'evaluacion': {
                    'id': evaluacion.id,
                    'title': evaluacion.title,
                    'start_time': evaluacion.start_time.strftime("%d/%m/%Y %H:%M"),
                    'end_time': evaluacion.end_time.strftime("%d/%m/%Y %H:%M"),
                    'duration_minutes': evaluacion.duration_minutes,
                    'preguntas_a_mostrar': evaluacion.preguntas_a_mostrar,
                    'status': evaluacion.get_status(),
                    'status_display': evaluacion.get_status_display()
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'error': 'Datos JSON inválidos'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error al actualizar la evaluación: {str(e)}'
            }, status=500)
    
    # GET request - mostrar formulario de edición
    context = {
        'evaluacion': evaluacion
    }
    return render(request, 'quizzes/edit_evaluacion.html', context)

@login_required
def evaluacion_results(request, pk):
    """
    Vista para ver los resultados de una evaluación
    """
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    # Verificar permisos (solo admins pueden ver resultados)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('quizzes:dashboard')
    
    context = {
        'evaluacion': evaluacion,
        'total_preguntas': evaluacion.preguntas.count(),
        'participantes_count': Participantes.objects.count(),
        'evaluacion_status': evaluacion.get_status(),
        'evaluacion_status_display': evaluacion.get_status_display()
    }
    
    return render(request, 'quizzes/evaluacion_results.html', context)

@csrf_exempt
@login_required
def delete_evaluacion(request, pk):
    """
    Vista para eliminar una evaluación
    """
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    # Verificar permisos básicos (solo admins pueden eliminar)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('quizzes:dashboard')
    
    # Todos los administradores pueden eliminar evaluaciones de cualquier etapa
    
    if request.method == 'POST':
        try:
            evaluacion.delete()
            return JsonResponse({
                'success': True,
                'message': 'Evaluación eliminada exitosamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al eliminar la evaluación: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)

@login_required
def ranking_evaluacion(request, pk):
    """
    Vista para mostrar el ranking de una evaluación
    """
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    # Verificar permisos
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('quizzes:dashboard')
    
    # Obtener resultados ordenados por puntaje y tiempo - solo el mejor por participante
    from django.db.models import Max
    
    # Primero, obtener el mejor puntaje por participante
    mejores_puntajes = ResultadoEvaluacion.objects.filter(
        evaluacion=evaluacion,
        completada=True
    ).values('participante').annotate(
        mejor_puntaje=Max('puntos_obtenidos')
    )
    
    # Crear una lista de participantes con sus mejores puntajes
    participantes_con_mejor_puntaje = []
    for item in mejores_puntajes:
        participante_id = item['participante']
        mejor_puntaje = item['mejor_puntaje']
        
        # Obtener todos los intentos con el mejor puntaje para este participante
        intentos_con_mejor_puntaje = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante_id=participante_id,
            completada=True,
            puntos_obtenidos=mejor_puntaje,
            fecha_inicio__isnull=False,
            fecha_fin__isnull=False
        )
        
        # De los intentos con el mejor puntaje, seleccionar el más rápido (menor tiempo real)
        mejor_resultado = None
        menor_tiempo = float('inf')
        
        for intento in intentos_con_mejor_puntaje:
            tiempo_real = (intento.fecha_fin - intento.fecha_inicio).total_seconds()
            if tiempo_real < menor_tiempo:
                menor_tiempo = tiempo_real
                mejor_resultado = intento
        
        if mejor_resultado:
            participantes_con_mejor_puntaje.append(mejor_resultado)
    
    # Ordenar por puntaje descendente y tiempo real ascendente
    def get_tiempo_real(resultado):
        if resultado.fecha_inicio and resultado.fecha_fin:
            return (resultado.fecha_fin - resultado.fecha_inicio).total_seconds()
        return float('inf')  # Si no tiene fechas, lo colocamos al final
    
    resultados = sorted(participantes_con_mejor_puntaje, key=lambda x: (-x.puntos_obtenidos, get_tiempo_real(x)))
    
    # Calcular estadísticas
    total_participantes = len(resultados)
    
    # Calcular promedio de puntos obtenidos (número, no porcentaje)
    promedio_puntos = sum(r.puntos_obtenidos for r in resultados) / total_participantes if total_participantes > 0 else 0
    
    # Calcular tiempo promedio real (usando fechas de inicio y fin)
    tiempo_total_minutos = 0
    resultados_con_tiempo_real = 0
    
    for resultado in resultados:
        if resultado.fecha_inicio and resultado.fecha_fin:
            tiempo_segundos = (resultado.fecha_fin - resultado.fecha_inicio).total_seconds()
            tiempo_minutos = tiempo_segundos / 60
            tiempo_total_minutos += tiempo_minutos
            resultados_con_tiempo_real += 1
    
    promedio_tiempo = tiempo_total_minutos / resultados_con_tiempo_real if resultados_con_tiempo_real > 0 else 0
    
    # Determinar ganadores según la etapa y configuración
    ganadores = []
    from .models import SystemConfig
    num_etapas = SystemConfig.get_num_etapas()
    if evaluacion.etapa == 1:
        top_n = 15 if num_etapas == 3 else 5
        if total_participantes >= top_n:
            ganadores = resultados[:top_n]
    elif evaluacion.etapa == 2:
        # En flujo de 3 etapas, etapa 2 muestra top 5; en flujo de 2 etapas no debería usarse
        if num_etapas == 3 and total_participantes >= 5:
            ganadores = resultados[:5]
    elif evaluacion.etapa == 3 and total_participantes >= 5:
        ganadores = resultados[:5]
    
    context = {
        'evaluacion': evaluacion,
        'resultados': resultados,
        'total_participantes': total_participantes,
        'promedio_puntaje': round(promedio_puntos, 3),  # Mostrar como número con 3 decimales
        'promedio_tiempo': round(promedio_tiempo, 1),   # Mostrar tiempo en minutos con 1 decimal
        'ganadores': ganadores,
        'num_etapas': num_etapas
    }
    
    return render(request, 'quizzes/ranking_evaluacion.html', context)

@csrf_exempt
@login_required
def gestionar_participantes_evaluacion(request, pk):
    """
    Vista para gestionar participantes de una evaluación
    """
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    # Verificar permisos
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        return JsonResponse({
            'success': False, 
            'error': 'No tienes permisos para acceder a esta funcionalidad.'
        }, status=403)
    
    if request.method == 'GET':
        try:
            # Obtener grupos con conteo de participantes
            grupos = []
            for grupo in GrupoParticipantes.objects.all():
                grupos.append({
                    'id': grupo.id,
                    'name': grupo.name,
                    'participantes_count': grupo.participantes.count()
                })
            
            # Obtener participantes individuales según la etapa y permisos del usuario
            participantes_individuales = []
            
            if evaluacion.etapa == 1:
                # Para etapa 1: todos los participantes individuales
                for participante in Participantes.objects.all():
                    if not participante.grupos.exists():
                        participantes_individuales.append({
                            'id': participante.id,
                            'NombresCompletos': participante.NombresCompletos,
                            'cedula': participante.cedula
                        })
            elif evaluacion.etapa == 2:
                # Para etapa 2: solo aplica si el sistema está en 3 etapas
                from .models import SystemConfig
                if SystemConfig.get_num_etapas() == 3:
                    if has_full_access(request.user):
                        participantes_automaticos = evaluacion.get_participantes_etapa2()
                        participantes_automaticos_ids = set(p.id for p in participantes_automaticos)
                        # Primero automáticos
                        for participante in participantes_automaticos:
                            participantes_individuales.append({
                                'id': participante.id,
                                'NombresCompletos': participante.NombresCompletos,
                                'cedula': participante.cedula
                            })
                        # Luego el resto
                        for participante in Participantes.objects.all():
                            if participante.id not in participantes_automaticos_ids:
                                participantes_individuales.append({
                                    'id': participante.id,
                                    'NombresCompletos': participante.NombresCompletos,
                                    'cedula': participante.cedula
                                })
                    else:
                        if evaluacion.participantes_individuales.exists():
                            participantes_actuales = evaluacion.participantes_individuales.all()
                        else:
                            participantes_actuales = evaluacion.get_participantes_etapa2()
                        for participante in participantes_actuales:
                            participantes_individuales.append({
                                'id': participante.id,
                                'NombresCompletos': participante.NombresCompletos,
                                'cedula': participante.cedula
                            })
            elif evaluacion.etapa == 3:
                # Para etapa 3: soportar flujo de 3 etapas y de 2 etapas (saltando etapa 2)
                from .models import SystemConfig
                if has_full_access(request.user):
                    participantes_automaticos = evaluacion.get_participantes_etapa3()
                    participantes_automaticos_ids = set(p.id for p in participantes_automaticos)
                    for participante in participantes_automaticos:
                        participantes_individuales.append({
                            'id': participante.id,
                            'NombresCompletos': participante.NombresCompletos,
                            'cedula': participante.cedula
                        })
                    for participante in Participantes.objects.all():
                        if participante.id not in participantes_automaticos_ids:
                            participantes_individuales.append({
                                'id': participante.id,
                                'NombresCompletos': participante.NombresCompletos,
                                'cedula': participante.cedula
                            })
                else:
                    if evaluacion.participantes_individuales.exists():
                        participantes_actuales = evaluacion.participantes_individuales.all()
                    else:
                        participantes_actuales = evaluacion.get_participantes_etapa3()
                    for participante in participantes_actuales:
                        participantes_individuales.append({
                            'id': participante.id,
                            'NombresCompletos': participante.NombresCompletos,
                            'cedula': participante.cedula
                        })
            

            
            # Obtener grupos y participantes asignados actualmente
            grupos_asignados = []
            for grupo in evaluacion.grupos_participantes.all():
                grupos_asignados.append({
                    'id': grupo.id,
                    'name': grupo.name,
                    'participantes_count': grupo.participantes.count()
                })
            
            participantes_asignados = []
            for participante in evaluacion.participantes_individuales.all():
                participantes_asignados.append({
                    'id': participante.id,
                    'NombresCompletos': participante.NombresCompletos,
                    'cedula': participante.cedula
                })
            
            # Para superusuarios en etapas avanzadas, incluir automáticos si no hay asignados manualmente
            participantes_automaticos = []
            if has_full_access(request.user) and evaluacion.etapa in [2, 3] and not evaluacion.participantes_individuales.exists():
                from .models import SystemConfig
                if evaluacion.etapa == 2 and SystemConfig.get_num_etapas() == 3:
                    participantes_automaticos = evaluacion.get_participantes_etapa2()
                elif evaluacion.etapa == 3:
                    participantes_automaticos = evaluacion.get_participantes_etapa3()
                
                # Agregar información de que son automáticos
                for participante in participantes_automaticos:
                    participantes_asignados.append({
                        'id': participante.id,
                        'NombresCompletos': participante.NombresCompletos,
                        'cedula': participante.cedula,
                        'automatico': True  # Marcar como automático
                    })
            
            # Para otros casos, marcar como manual
            if not participantes_automaticos:
                for item in participantes_asignados:
                    item['automatico'] = False
            
            return JsonResponse({
                'success': True,
                'grupos': grupos,
                'participantes_individuales': participantes_individuales,
                'grupos_asignados': grupos_asignados,
                'participantes_asignados': participantes_asignados,
                'etapa': evaluacion.etapa
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al cargar datos: {str(e)}'
            }, status=500)
    
    elif request.method == 'POST':
        try:
            import json
            data = json.loads(request.body.decode('utf-8'))
            
            # Verificar permisos para etapas avanzadas
            if evaluacion.etapa != 1 and not has_full_access(request.user):
                return JsonResponse({
                    'success': False,
                    'error': 'Solo los superusuarios y administradores con acceso total pueden modificar participantes en etapas avanzadas.'
                }, status=403)
            
            grupos_ids = data.get('grupos', [])
            participantes_individuales_ids = data.get('participantes_individuales', [])
            
            # Para etapa 1: actualizar grupos y participantes individuales
            if evaluacion.etapa == 1:
                from django.db import transaction
                with transaction.atomic():
                    # Actualizar grupos asignados
                    evaluacion.grupos_participantes.clear()
                    if grupos_ids:
                        grupos = GrupoParticipantes.objects.filter(id__in=grupos_ids)
                        evaluacion.grupos_participantes.add(*grupos)
                    
                    # Actualizar participantes individuales asignados
                    evaluacion.participantes_individuales.clear()
                    if participantes_individuales_ids:
                        participantes = Participantes.objects.filter(id__in=participantes_individuales_ids)
                        evaluacion.participantes_individuales.add(*participantes)
            
            # Para etapas 2 y 3: solo superusuarios y admins con acceso total pueden modificar
            elif evaluacion.etapa in [2, 3] and has_full_access(request.user):
                # Limpiar participantes individuales actuales
                evaluacion.participantes_individuales.clear()
                
                # Agregar solo los participantes seleccionados por el usuario autorizado
                if participantes_individuales_ids:
                    participantes = Participantes.objects.filter(id__in=participantes_individuales_ids)
                    evaluacion.participantes_individuales.add(*participantes)
            
            return JsonResponse({
                'success': True,
                'message': 'Participantes asignados correctamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al guardar datos: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)

@login_required
def exportar_resultado_pdf(request, pk):
    """
    Vista para exportar resultado de evaluación a PDF con diseño moderno y profesional
    """
    try:
        evaluacion = get_object_or_404(Evaluacion, pk=pk)
        participante = Participantes.objects.get(user=request.user)
        
        # Verificar que el participante tenga resultado para esta evaluación
        resultado = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            completada=True
        ).first()
        
        if not resultado:
            messages.error(request, 'No tienes resultados para esta evaluación.')
            return redirect('quizzes:student_results')
        
        # Crear el PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="resultado_{evaluacion.title}_{participante.cedula}.pdf"'
        
        # Crear el documento PDF con márgenes optimizados
        doc = SimpleDocTemplate(response, pagesize=A4, 
                              leftMargin=0.6*inch, rightMargin=0.6*inch,
                              topMargin=0.6*inch, bottomMargin=0.6*inch)
        elements = []
        
        # Definir paleta de colores moderna y elegante
        primary_color = colors.Color(0.15, 0.35, 0.75)  # Azul corporativo
        secondary_color = colors.Color(0.95, 0.95, 0.98)  # Gris muy claro
        accent_color = colors.Color(0.12, 0.55, 0.35)  # Verde moderno
        header_bg = colors.Color(0.08, 0.25, 0.55)  # Azul más oscuro para encabezado
        success_color = colors.Color(0.1, 0.6, 0.1)  # Verde para éxito
        warning_color = colors.Color(0.8, 0.6, 0.1)  # Amarillo para advertencia
        danger_color = colors.Color(0.8, 0.1, 0.1)  # Rojo para peligro
        
        # Estilos mejorados
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'ModernTitle',
            parent=styles['Heading1'],
            fontSize=22,
            spaceAfter=18,
            alignment=1,  # Centrado
            textColor=primary_color,
            fontName='Helvetica-Bold',
            spaceBefore=8,
            leading=26
        )
        
        subtitle_style = ParagraphStyle(
            'ModernSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            alignment=1,  # Centrado
            textColor=colors.Color(0.3, 0.3, 0.3),
            fontName='Helvetica',
            leading=18
        )
        
        etapa_style = ParagraphStyle(
            'EtapaStyle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Centrado
            textColor=accent_color,
            fontName='Helvetica-Bold',
            spaceBefore=10,
            leading=22
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.Color(0.2, 0.2, 0.2),
            fontName='Helvetica',
            leading=16
        )
        
        # Título principal con mejor formato
        title = Paragraph("OLIMPIADAS DE MATEMÁTICAS<br/>CARRERA MECÁNICA", title_style)
        elements.append(title)
        
        # Manejo mejorado de logos
        logo_mecanica = None
        logo_uteq = None
        
        # Cargar Logo Mecánica
        logo_mecanica_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logoMecanica.png')
        if os.path.exists(logo_mecanica_path):
            try:
                logo_mecanica = Image(logo_mecanica_path, width=1.6*inch, height=1.2*inch)
            except Exception as e:
                print(f"Error al cargar logo Mecánica: {e}")
        
        # Cargar Logo UTEQ
        logo_uteq_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-uteq.png')
        if os.path.exists(logo_uteq_path):
            try:
                logo_uteq = Image(logo_uteq_path, width=1.6*inch, height=1.2*inch)
            except Exception as e:
                print(f"Error al cargar logo UTEQ: {e}")
        
        # Tabla de logos mejorada
        if logo_mecanica or logo_uteq:
            logo_row = []
            
            if logo_mecanica:
                logo_row.append(logo_mecanica)
            else:
                logo_row.append(Paragraph("", styles['Normal']))
            
            logo_row.append(Paragraph("", styles['Normal']))  # Espacio central
            
            if logo_uteq:
                logo_row.append(logo_uteq)
            else:
                logo_row.append(Paragraph("", styles['Normal']))
            
            logo_table = Table([logo_row], colWidths=[2.4*inch, 1.2*inch, 2.4*inch])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('ALIGN', (2, 0), (2, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, 0), 0),
                ('RIGHTPADDING', (0, 0), (-1, 0), 0),
                ('TOPPADDING', (0, 0), (-1, 0), 5),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ]))
            
            elements.append(logo_table)
            elements.append(Spacer(1, 20))
        
        # Información de la etapa
        etapa_text = f"CERTIFICADO DE PARTICIPACIÓN - ETAPA {evaluacion.etapa}"
        elements.append(Paragraph(etapa_text, etapa_style))
        
        # Información adicional
        evaluacion_info = f"Evaluación: {evaluacion.title}"
        elements.append(Paragraph(evaluacion_info, subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Información del participante en un recuadro elegante
        participante_info = [
            ['Campo', 'Información'],
            ['Participante', participante.NombresCompletos],
            ['Cédula de Identidad', participante.cedula],
            ['Correo Electrónico', participante.email if participante.email else 'No registrado'],
        ]
        
        info_table = Table(participante_info, colWidths=[2.2*inch, 3.8*inch])
        info_table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Cuerpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.7, 0.7, 0.7)),
            ('LINEBELOW', (0, 0), (-1, 0), 2, header_bg),
            
            # Alineación
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Filas alternadas
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('BACKGROUND', (0, 2), (-1, 2), secondary_color),
            ('BACKGROUND', (0, 3), (-1, 3), colors.white),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 25))
        
        # Resultados de la evaluación
        results_title_style = ParagraphStyle(
            'ResultsTitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            alignment=1,
            textColor=primary_color,
            fontName='Helvetica-Bold'
        )
        
        elements.append(Paragraph("RESULTADOS DE LA EVALUACIÓN", results_title_style))
        
        # Calcular puntuación en formato mejorado
        puntaje_porcentaje = resultado.puntaje if hasattr(resultado, 'puntaje') else (resultado.puntos_obtenidos / resultado.puntos_totales * 100 if resultado.puntos_totales > 0 else 0)
        puntaje_numerico = resultado.puntos_obtenidos if hasattr(resultado, 'puntos_obtenidos') else 0
        puntos_totales = resultado.puntos_totales if hasattr(resultado, 'puntos_totales') else 0
        
        # Tabla de resultados mejorada
        resultados_data = [
            ['Métrica', 'Resultado'],
            ['Nota Final', f"{puntaje_numerico:.3f}"],
            ['Tiempo Utilizado', resultado.get_tiempo_formateado()],
            ['Fecha de Finalización', resultado.fecha_fin.strftime("%d/%m/%Y a las %H:%M") if resultado.fecha_fin else 'No disponible'],
        ]
        
        results_table = Table(resultados_data, colWidths=[2.5*inch, 3.5*inch])
        results_table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
            ('TOPPADDING', (0, 0), (-1, 0), 15),
            
            # Cuerpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('TOPPADDING', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            
            # Bordes elegantes
            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.6, 0.6, 0.6)),
            ('LINEBELOW', (0, 0), (-1, 0), 2, header_bg),
            
            # Alineación
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Filas alternadas
            ('BACKGROUND', (0, 1), (-1, 1), secondary_color),
            ('BACKGROUND', (0, 2), (-1, 2), colors.white),
            ('BACKGROUND', (0, 3), (-1, 3), secondary_color),
        ]))
        
        # Destacar la puntuación final con color según el rendimiento
        if puntaje_porcentaje >= 80:
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (1, 1), (1, 1), success_color),
                ('TEXTCOLOR', (1, 1), (1, 1), colors.white),
                ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
            ]))
        elif puntaje_porcentaje >= 60:
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (1, 1), (1, 1), warning_color),
                ('TEXTCOLOR', (1, 1), (1, 1), colors.white),
                ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
            ]))
        else:
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (1, 1), (1, 1), danger_color),
                ('TEXTCOLOR', (1, 1), (1, 1), colors.white),
                ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
            ]))
        
        elements.append(results_table)
        elements.append(Spacer(1, 25))
        
        # Comentario personalizado según puntuación
        comment_style = ParagraphStyle(
            'CommentStyle',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            alignment=1,  # Centrado
            fontName='Helvetica',
            leading=16
        )
        
        if puntaje_porcentaje >= 90:
            mensaje = "<b>¡EXCELENTE DESEMPEÑO!</b><br/>"
        elif puntaje_porcentaje >= 80:
            mensaje = "<b>¡MUY BUEN TRABAJO!</b><br/>"
        elif puntaje_porcentaje >= 70:
            mensaje = "<b>BUEN DESEMPEÑO</b><br/>"
        elif puntaje_porcentaje >= 60:
            mensaje = "<b>DESEMPEÑO ACEPTABLE</b><br/>"
        else:
            mensaje = "<b>OPORTUNIDAD DE MEJORA</b><br/>"

        
        comment_paragraph = Paragraph(mensaje, comment_style)
        elements.append(comment_paragraph)
        elements.append(Spacer(1, 20))
        
        # Pie de página con información institucional
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,  # Centrado
            textColor=colors.Color(0.4, 0.4, 0.4),
            fontName='Helvetica-Oblique',
            leading=12
        )
        
        fecha_emision = timezone.now().strftime("%d de %B de %Y")
        footer_text = f"<i>Documento generado automáticamente el {fecha_emision}<br/>Universidad Técnica Estatal de Quevedo - Carrera de Ingeniería Mecánica</i>"
        elements.append(Paragraph(footer_text, footer_style))
        
        # Construir el PDF
        doc.build(elements)
        
        return response
        
    except Participantes.DoesNotExist:
        messages.error(request, 'No se encontró información del participante.')
        return redirect('quizzes:student_results')
    except Exception as e:
        messages.error(request, f'Error generando PDF: {str(e)}')
        return redirect('quizzes:student_results')

@csrf_exempt
@login_required
def actualizar_puntos_pregunta(request, pk):
    """
    Vista para actualizar los puntos de una pregunta individual
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pregunta = get_object_or_404(Pregunta, pk=pk)
            
            puntos = data.get('puntos', 1)
            
            # Validar puntos
            try:
                puntos = int(puntos)
                if puntos < 1 or puntos > 10:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Los puntos deben estar entre 1 y 10'
                    }, status=400)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False, 
                    'error': 'Los puntos deben ser un número válido'
                }, status=400)
            
            # Actualizar puntos
            pregunta.puntos = puntos
            pregunta.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Puntos actualizados exitosamente',
                'puntos': puntos
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'error': 'Datos JSON inválidos'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error al actualizar puntos: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False, 
        'error': 'Método no permitido'
    }, status=405)

@login_required
def send_participants_email(request, grupo_id):
    """
    Envía un correo al representante con la lista de participantes del grupo
    """
    if not can_manage_representantes(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('quizzes:dashboard')
    
    try:
        grupo = GrupoParticipantes.objects.select_related('representante').prefetch_related('participantes').get(id=grupo_id)
        
        if not grupo.representante:
            messages.error(request, 'Este grupo no tiene un representante asignado.')
            return redirect('quizzes:manage_grupos')
        
        if not grupo.participantes.exists():
            messages.error(request, 'Este grupo no tiene participantes asignados.')
            return redirect('quizzes:manage_grupos')
        
        # Crear tabla HTML moderna con los datos de los participantes
        participantes_html = """
        <table style="width: 100%; border-collapse: collapse; background: white;">
            <thead>
                <tr>
                    <th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; padding: 15px 10px; text-align: left; font-weight: 600; font-size: 14px;">Cédula</th>
                    <th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; padding: 15px 10px; text-align: left; font-weight: 600; font-size: 14px;">Nombres Completos</th>
                    <th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; padding: 15px 10px; text-align: left; font-weight: 600; font-size: 14px;">Email</th>
                    <!--<th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; padding: 15px 10px; text-align: left; font-weight: 600; font-size: 14px;">Teléfono</th>-->
                    <!--<th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; padding: 15px 10px; text-align: left; font-weight: 600; font-size: 14px;">Edad</th>-->
                    <th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; padding: 15px 10px; text-align: left; font-weight: 600; font-size: 14px;">Usuario</th>
                    <th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; padding: 15px 10px; text-align: left; font-weight: 600; font-size: 14px;">Contraseña</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for participante in grupo.participantes.all():
            # Si no tiene contraseña temporal, generar una nueva
            if not participante.password_temporal:
                nueva_password = get_random_string(length=6)
                participante.password_temporal = nueva_password
                participante.save()
                # Actualizar también la contraseña del usuario
                participante.user.set_password(nueva_password)
                participante.user.save()
            else:
                nueva_password = participante.password_temporal
            
            participantes_html += f"""
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <td style="padding: 12px 10px; font-size: 13px; font-weight: 600; color: #333;">{participante.cedula}</td>
                    <td style="padding: 12px 10px; font-size: 13px; color: #555;">{participante.NombresCompletos}</td>
                    <td style="padding: 12px 10px; font-size: 13px; color: #667eea;">{participante.email}</td>
                    <!--<td style="padding: 12px 10px; font-size: 13px; color: #666;">{participante.phone or 'No registrado'}</td>-->
                    <!--<td style="padding: 12px 10px; font-size: 13px; color: #666;">{participante.edad or 'No registrado'}</td>-->
                    <td style="padding: 12px 10px; font-size: 13px; font-family: 'Courier New', monospace; font-weight: 600; color: #667eea;">{participante.user.username}</td>
                    <td style="padding: 12px 10px; font-size: 13px; font-family: 'Courier New', monospace; font-weight: 600; color: #e74c3c; background: #fdf2f2; border-radius: 4px;">{nueva_password}</td>
                </tr>
            """
        
        participantes_html += """
            </tbody>
        </table>
        """
        
        # Crear el mensaje del correo usando la función global
        subject = f'Lista de Participantes - Grupo: {grupo.name}'
        
        # Preparar contenido adicional para la función global
        additional_content = {
            'participantes_html': participantes_html,
            'total_participantes': grupo.participantes.count()
        }
        
        # Generar mensajes usando la función global
        plain_message, html_message = generate_email_messages(
            subject=subject,
            nombre=grupo.representante.NombresRepresentante,
            system_name=grupo.name,
            username='',  # No aplica para lista de participantes
            nueva_password='',  # No aplica para lista de participantes
            email_type='participants_list',
            additional_content=additional_content
        )
        
        # Enviar el correo
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [grupo.representante.CorreoRepresentante],
            fail_silently=False,
            html_message=html_message
        )
        
        # Verificar si es una petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # Para peticiones AJAX, devolver JSON
            return JsonResponse({
                'success': True,
                'message': f'Correo enviado exitosamente al representante {grupo.representante.NombresRepresentante}.'
            })
        else:
            # Para peticiones normales, usar mensajes y redirecciones
            messages.success(request, f'Correo enviado exitosamente al representante {grupo.representante.NombresRepresentante}.')
            return redirect('quizzes:manage_grupos')
        
    except GrupoParticipantes.DoesNotExist:
        error_msg = 'El grupo especificado no existe.'
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': error_msg
            })
        else:
            messages.error(request, error_msg)
            return redirect('quizzes:manage_grupos')
    except Exception as e:
        error_msg = f'Error al enviar el correo: {str(e)}'
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': error_msg
            })
        else:
            messages.error(request, error_msg)
            return redirect('quizzes:manage_grupos')

@login_required
def send_credentials_email(request, user_type, user_id):
    """Enviar correo con credenciales a un participante o administrador"""
    try:
        if user_type == 'participante':
            user_obj = Participantes.objects.get(id=user_id)
            nombre = user_obj.NombresCompletos
            email = user_obj.email
            username = user_obj.user.username
            
            # Siempre generar una nueva contraseña temporal
            nueva_password = get_random_string(length=6)
            user_obj.password_temporal = nueva_password
            user_obj.save()
            # Actualizar también la contraseña del usuario
            user_obj.user.set_password(nueva_password)
            user_obj.user.save()
            
            subject = f'Credenciales de Acceso - Sistema Olymp'
            system_name = 'Sistema Olymp'
            
        elif user_type == 'admin':
            user_obj = AdminProfile.objects.get(id=user_id)
            nombre = user_obj.user.get_full_name()
            email = user_obj.user.email
            username = user_obj.user.username
            
            # Siempre generar una nueva contraseña
            nueva_password = get_random_string(length=8)
            user_obj.password = nueva_password
            user_obj.save()
            # Actualizar también la contraseña del usuario
            user_obj.user.set_password(nueva_password)
            user_obj.user.save()
            
            subject = f'Credenciales de Acceso - Panel de Administración Olymp'
            system_name = 'Panel de Administración Olymp'
            
        else:
            messages.error(request, 'Tipo de usuario no válido.')
            return redirect('quizzes:dashboard')
        
        # Generar mensajes usando la función global
        plain_message, html_message = generate_email_messages(
            subject=subject,
            nombre=nombre,
            system_name=system_name,
            username=username,
            nueva_password=nueva_password,
            email_type='credentials'
        )
        
        # Enviar el correo
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
            html_message=html_message
        )
        
        # Verificar si es una petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # Para peticiones AJAX, devolver JSON
            return JsonResponse({
                'success': True,
                'message': f'Correo enviado exitosamente al {"participante" if user_type == "participante" else "administrador"} {nombre}.'
            })
        else:
            # Para peticiones normales, usar mensajes y redirecciones
            if user_type == 'participante':
                messages.success(request, f'Correo enviado exitosamente al participante {nombre}.')
                return redirect('quizzes:manage_participants')
            else:
                messages.success(request, f'Correo enviado exitosamente al administrador {nombre}.')
                return redirect('quizzes:manage_admins')
        
    except (Participantes.DoesNotExist, AdminProfile.DoesNotExist):
        error_msg = 'El usuario especificado no existe.'
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': error_msg
            })
        else:
            messages.error(request, error_msg)
            return redirect('quizzes:dashboard')
    except Exception as e:
        error_msg = f'Error al enviar el correo: {str(e)}'
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': error_msg
            })
        else:
            messages.error(request, error_msg)
            return redirect('quizzes:dashboard')


@login_required
def profile_view(request):
    """Vista para mostrar y editar el perfil del usuario"""
    # Obtener o crear el perfil del usuario
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Verificar si el usuario es un participante
    try:
        participante = Participantes.objects.get(user=request.user)
        is_participante = True
        # Para participantes, usar el teléfono del modelo Participantes
        phone_value = participante.phone
    except Participantes.DoesNotExist:
        is_participante = False
        # Para otros usuarios, usar el teléfono del UserProfile
        phone_value = profile.phone
    
    # Verificar si es una petición AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        # Procesar el formulario de actualización de perfil
        if 'update_profile' in request.POST:
            try:
                # Actualizar información básica
                full_name = request.POST.get('full_name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                bio = request.POST.get('bio', '').strip()
                
                # Validar que se proporcione el nombre completo
                if not full_name:
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': 'El campo Nombres Completos es obligatorio.'
                        })
                    else:
                        messages.error(request, 'El campo Nombres Completos es obligatorio.')
                        return redirect('quizzes:profile')
                
                # Normalizar email siempre
                email_normalized = email.lower().strip()
                
                # Validar email único solo si cambió
                if email != request.user.email:
                    # Verificar si ya existe otro usuario con este correo
                    if User.objects.filter(email__iexact=email_normalized).exclude(id=request.user.id).exists():
                        if is_ajax:
                            return JsonResponse({
                                'success': False,
                                'message': 'El correo electrónico ya está en uso por otro usuario.'
                            })
                        else:
                            messages.error(request, 'El correo electrónico ya está en uso por otro usuario.')
                            return redirect('quizzes:profile')
                    
                    # Si es participante, verificar conflictos con representantes
                    if is_participante:
                        if Representante.objects.filter(
                            models.Q(CorreoInstitucional__iexact=email_normalized) | 
                            models.Q(CorreoRepresentante__iexact=email_normalized)
                        ).exists():
                            if is_ajax:
                                return JsonResponse({
                                    'success': False,
                                    'message': 'El correo electrónico ya está siendo usado por un representante.'
                                })
                            else:
                                messages.error(request, 'El correo electrónico ya está siendo usado por un representante.')
                                return redirect('quizzes:profile')
                
                # Validar formato de teléfono si se proporciona
                if phone and not re.match(r'^\d{10}$', phone):
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': 'El teléfono debe tener exactamente 10 dígitos numéricos.'
                        })
                    else:
                        messages.error(request, 'El teléfono debe tener exactamente 10 dígitos numéricos.')
                        return redirect('quizzes:profile')
                
                # Actualizar usuario - dividir el nombre completo en first_name y last_name
                # Si hay espacios, el primer espacio separa nombres de apellidos
                name_parts = full_name.split(' ', 1)
                if len(name_parts) > 1:
                    first_name = name_parts[0]
                    last_name = name_parts[1]
                else:
                    first_name = full_name
                    last_name = ''
                
                try:
                    # Usar transacción para asegurar consistencia
                    from django.db import transaction
                    with transaction.atomic():
                        request.user.first_name = first_name
                        request.user.last_name = last_name
                        request.user.email = email_normalized
                        
                        # Validar y guardar usuario
                        request.user.full_clean()
                        request.user.save()
                        
                        # Actualizar perfil según el tipo de usuario
                        if is_participante:
                            # Para participantes, actualizar el teléfono en el modelo Participantes
                            participante.phone = phone
                            participante.email = email_normalized  # Actualizar también el correo del participante
                            participante.full_clean()
                            participante.save()
                            # También actualizar el UserProfile para bio y avatar
                            profile.bio = bio
                        else:
                            # Para otros usuarios, actualizar el UserProfile
                            profile.phone = phone
                            profile.bio = bio
                        
                        # Procesar nueva foto si se subió
                        if 'avatar' in request.FILES:
                            # Eliminar foto anterior si existe
                            if profile.avatar:
                                try:
                                    os.remove(profile.avatar.path)
                                except:
                                    pass
                            
                            profile.avatar = request.FILES['avatar']
                        
                        profile.full_clean()
                        profile.save()
                        
                except ValidationError as e:
                    error_message = extract_validation_error_message(e)
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': f'Error de validación: {error_message}'
                        })
                    else:
                        messages.error(request, f'Error de validación: {error_message}')
                        return redirect('quizzes:profile')
                except IntegrityError as e:
                    if 'email' in str(e).lower():
                        error_msg = 'El correo electrónico ya está en uso.'
                    elif 'phone' in str(e).lower():
                        error_msg = 'El teléfono ya está registrado.'
                    else:
                        error_msg = 'Error de integridad en la base de datos.'
                    
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': error_msg
                        })
                    else:
                        messages.error(request, error_msg)
                        return redirect('quizzes:profile')
                
                # Si es AJAX, devolver JSON
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'Perfil actualizado exitosamente.',
                        'avatar_url': profile.avatar.url if profile.avatar else None
                    })
                
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('quizzes:profile')
                
            except Exception as e:
                # Para peticiones AJAX, siempre devolver JSON
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': f'Error al actualizar el perfil: {str(e)}'
                    })
                else:
                    messages.error(request, f'Error al actualizar el perfil: {str(e)}')
                    return redirect('quizzes:profile')
        
        # Procesar cambio de contraseña
        elif 'change_password' in request.POST:
            try:
                current_password = request.POST.get('current_password')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                
                # Validar contraseña actual
                if not request.user.check_password(current_password):
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': 'La contraseña actual es incorrecta.'
                        })
                    else:
                        messages.error(request, 'La contraseña actual es incorrecta.')
                        return redirect('quizzes:profile')
                
                # Validar que las nuevas contraseñas coincidan
                if new_password != confirm_password:
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': 'Las nuevas contraseñas no coinciden.'
                        })
                    else:
                        messages.error(request, 'Las nuevas contraseñas no coinciden.')
                        return redirect('quizzes:profile')
                
                # Validar contraseña usando función reutilizable
                error_message = validate_password_strength(new_password, request.user.username)
                
                if error_message:
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': error_message
                        })
                    else:
                        messages.error(request, error_message)
                        return redirect('quizzes:profile')
                
                # Cambiar contraseña
                request.user.set_password(new_password)
                request.user.save()
                
                # Re-autenticar al usuario
                login(request, request.user)
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'Contraseña cambiada exitosamente.'
                    })
                else:
                    messages.success(request, 'Contraseña cambiada exitosamente.')
                    return redirect('quizzes:profile')
                    
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': f'Error al cambiar la contraseña: {str(e)}'
                    })
                else:
                    messages.error(request, f'Error al cambiar la contraseña: {str(e)}')
                    return redirect('quizzes:profile')
        else:
            # Si es AJAX pero no se reconoce el tipo de formulario
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'Tipo de formulario no reconocido.'
                })
    
    # Si es una petición AJAX GET, devolver error
    if is_ajax:
        return JsonResponse({
            'success': False,
            'message': 'Método no permitido para peticiones AJAX.'
        })
    
    context = {
        'profile': profile,
        'user': request.user,
        'phone_value': phone_value,
    }
    return render(request, 'quizzes/profile.html', context)


@login_required
def exportar_ranking_pdf(request, pk):
    """
    Genera un PDF del ranking de una evaluación específica con diseño moderno
    Muestra solo el mejor resultado de cada participante
    """
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    # Verificar permisos
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        messages.error(request, 'No tienes permisos para acceder a esta funcionalidad.')
        return redirect('quizzes:dashboard')
    
    # Obtener resultados únicos por participante - SOLO EL MEJOR PUNTAJE
    from django.db.models import Max
    
    # Obtener el mejor puntaje por participante
    mejores_puntajes = ResultadoEvaluacion.objects.filter(
        evaluacion=evaluacion,
        completada=True
    ).values('participante').annotate(
        mejor_puntaje=Max('puntos_obtenidos')
    )
    
    # Obtener los resultados únicos con mejor puntaje
    participantes_con_mejor_puntaje = []
    for item in mejores_puntajes:
        participante_id = item['participante']
        mejor_puntaje = item['mejor_puntaje']
        
        # Obtener todos los intentos con el mejor puntaje para este participante
        intentos_con_mejor_puntaje = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante_id=participante_id,
            completada=True,
            puntos_obtenidos=mejor_puntaje,
            fecha_inicio__isnull=False,
            fecha_fin__isnull=False
        )
        
        # De los intentos con el mejor puntaje, seleccionar el más rápido (menor tiempo real)
        mejor_resultado = None
        menor_tiempo = float('inf')
        
        for intento in intentos_con_mejor_puntaje:
            tiempo_real = (intento.fecha_fin - intento.fecha_inicio).total_seconds()
            if tiempo_real < menor_tiempo:
                menor_tiempo = tiempo_real
                mejor_resultado = intento
        
        if mejor_resultado:
            participantes_con_mejor_puntaje.append(mejor_resultado)
    
    # Ordenar por puntaje descendente y tiempo real ascendente
    def get_tiempo_real(resultado):
        if resultado.fecha_inicio and resultado.fecha_fin:
            return (resultado.fecha_fin - resultado.fecha_inicio).total_seconds()
        return float('inf')  # Si no tiene fechas, lo colocamos al final
    
    resultados = sorted(participantes_con_mejor_puntaje, key=lambda x: (-x.puntos_obtenidos, get_tiempo_real(x)))
    
    # Crear el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ranking_etapa_{evaluacion.etapa}_{evaluacion.title}.pdf"'
    
    # Crear el documento PDF con márgenes optimizados
    doc = SimpleDocTemplate(response, pagesize=A4, 
                          leftMargin=0.6*inch, rightMargin=0.6*inch,
                          topMargin=0.6*inch, bottomMargin=0.6*inch)
    elements = []
    
    # Definir paleta de colores moderna y elegante
    primary_color = colors.Color(0.15, 0.35, 0.75)  # Azul corporativo
    secondary_color = colors.Color(0.95, 0.95, 0.98)  # Gris muy claro
    accent_color = colors.Color(0.12, 0.55, 0.35)  # Verde moderno
    header_bg = colors.Color(0.08, 0.25, 0.55)  # Azul más oscuro para encabezado
    gold_color = colors.Color(1, 0.84, 0)  # Oro
    silver_color = colors.Color(0.75, 0.75, 0.75)  # Plata
    bronze_color = colors.Color(0.80, 0.50, 0.20)  # Bronce
    
    # Estilos mejorados
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ModernTitle',
        parent=styles['Heading1'],
        fontSize=22,
        spaceAfter=18,
        alignment=1,  # Centrado
        textColor=primary_color,
        fontName='Helvetica-Bold',
        spaceBefore=8,
        leading=26
    )
    
    subtitle_style = ParagraphStyle(
        'ModernSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        alignment=1,  # Centrado
        textColor=colors.Color(0.3, 0.3, 0.3),
        fontName='Helvetica',
        leading=18
    )
    
    etapa_style = ParagraphStyle(
        'EtapaStyle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        alignment=1,  # Centrado
        textColor=accent_color,
        fontName='Helvetica-Bold',
        spaceBefore=10,
        leading=22
    )
    
    # Título principal con mejor formato
    title = Paragraph("OLIMPIADAS DE MATEMÁTICAS<br/>CARRERA MECÁNICA", title_style)
    elements.append(title)
    
    # Manejo mejorado de logos
    logo_mecanica = None
    logo_uteq = None
    
    # Cargar Logo Mecánica
    logo_mecanica_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logoMecanica.png')
    if os.path.exists(logo_mecanica_path):
        try:
            logo_mecanica = Image(logo_mecanica_path, width=1.6*inch, height=1.2*inch)
        except Exception as e:
            print(f"Error al cargar logo Mecánica: {e}")
    
    # Cargar Logo UTEQ
    logo_uteq_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-uteq.png')
    if os.path.exists(logo_uteq_path):
        try:
            logo_uteq = Image(logo_uteq_path, width=1.6*inch, height=1.2*inch)
        except Exception as e:
            print(f"Error al cargar logo UTEQ: {e}")
    
    # Tabla de logos mejorada
    if logo_mecanica or logo_uteq:
        logo_row = []
        
        if logo_mecanica:
            logo_row.append(logo_mecanica)
        else:
            logo_row.append(Paragraph("", styles['Normal']))
        
        logo_row.append(Paragraph("", styles['Normal']))  # Espacio central
        
        if logo_uteq:
            logo_row.append(logo_uteq)
        else:
            logo_row.append(Paragraph("", styles['Normal']))
        
        logo_table = Table([logo_row], colWidths=[2.4*inch, 1.2*inch, 2.4*inch])
        logo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, 0), 0),
            ('RIGHTPADDING', (0, 0), (-1, 0), 0),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ]))
        
        elements.append(logo_table)
        elements.append(Spacer(1, 20))
    
    # Información de la etapa
    etapa_text = f"RESULTADOS OFICIALES - ETAPA {evaluacion.etapa}"
    elements.append(Paragraph(etapa_text, etapa_style))
    
    # Información adicional
    fecha_info = f"Evaluación: {evaluacion.title}"
    elements.append(Paragraph(fecha_info, subtitle_style))
    elements.append(Spacer(1, 15))
    
    # Subtítulo del ranking
    ranking_subtitle = Paragraph("Ranking Final de Participantes", subtitle_style)
    elements.append(ranking_subtitle)
    elements.append(Spacer(1, 15))
    
    # Preparar datos de la tabla
    table_data = [['Pos.', 'Participante', 'Cédula', 'Puntaje', 'Tiempo', 'Estado']]
    
    from .models import SystemConfig
    num_etapas = SystemConfig.get_num_etapas()
    
    for i, resultado in enumerate(resultados, 1):
        # Determinar estado según la etapa y configuración
        if evaluacion.etapa == 1 and i <= (15 if num_etapas == 3 else 5):
            estado = "Clasificado"
        elif evaluacion.etapa == 2 and num_etapas == 3 and i <= 5:
            estado = "Finalista"
        elif evaluacion.etapa == 3:
            if i == 1:
                estado = "Oro"
            elif i == 2 or i == 3:
                estado = "Plata"
            elif i == 4 or i == 5:
                estado = "Bronce"
            else:
                estado = "Participante"
        else:
            estado = "Participante"
        
        # Formatear puntaje - usar puntos_obtenidos directamente
        puntaje_str = f"{resultado.puntos_obtenidos:.3f}"
        
        # Agregar fila a la tabla
        table_data.append([
            str(i),
            resultado.participante.NombresCompletos,
            resultado.participante.cedula,
            puntaje_str,
            resultado.get_tiempo_formateado(),
            estado
        ])
    
    # Crear tabla con anchos optimizados
    table = Table(table_data, colWidths=[0.6*inch, 2.6*inch, 1.2*inch, 0.8*inch, 1.0*inch, 1.3*inch])
    
    # Estilo moderno y elegante de la tabla
    table_style = TableStyle([
        # Encabezado principal
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Cuerpo de la tabla
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        
        # Bordes elegantes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.7, 0.7, 0.7)),
        ('LINEBELOW', (0, 0), (-1, 0), 2, header_bg),
        
        # Alineación
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Nombres a la izquierda
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Posición centrada
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Cédula centrada
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Puntaje centrado
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Tiempo centrado
        ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Estado centrado
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    # Aplicar filas alternadas correctamente
    for i in range(1, len(table_data)):
        if i % 2 == 0:  # Filas pares (índice par, pero es fila impar visualmente)
            table_style.add('BACKGROUND', (0, i), (-1, i), secondary_color)
        else:  # Filas impares (índice impar, pero es fila par visualmente)
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.white)
    
    # Aplicar colores especiales para estados de medalleros
    for i, resultado in enumerate(resultados, 1):
        row_index = i  # i ya es el índice correcto (empieza en 1)
        
        if evaluacion.etapa == 3:
            if i == 1:  # Oro
                table_style.add('BACKGROUND', (5, row_index), (5, row_index), gold_color)
                table_style.add('TEXTCOLOR', (5, row_index), (5, row_index), colors.black)
                table_style.add('FONTNAME', (5, row_index), (5, row_index), 'Helvetica-Bold')
            elif i == 2 or i == 3:  # Plata
                table_style.add('BACKGROUND', (5, row_index), (5, row_index), silver_color)
                table_style.add('TEXTCOLOR', (5, row_index), (5, row_index), colors.black)
                table_style.add('FONTNAME', (5, row_index), (5, row_index), 'Helvetica-Bold')
            elif i == 4 or i == 5:  # Bronce
                table_style.add('BACKGROUND', (5, row_index), (5, row_index), bronze_color)
                table_style.add('TEXTCOLOR', (5, row_index), (5, row_index), colors.white)
                table_style.add('FONTNAME', (5, row_index), (5, row_index), 'Helvetica-Bold')
        elif (evaluacion.etapa == 1 and i <= (15 if num_etapas == 3 else 5)) or \
             (evaluacion.etapa == 2 and num_etapas == 3 and i <= 5):
            table_style.add('BACKGROUND', (5, row_index), (5, row_index), accent_color)
            table_style.add('TEXTCOLOR', (5, row_index), (5, row_index), colors.white)
            table_style.add('FONTNAME', (5, row_index), (5, row_index), 'Helvetica-Bold')
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Agregar información de estadísticas al final
    if resultados:
        elements.append(Spacer(1, 20))
        
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,  # Centrado
            textColor=colors.Color(0.4, 0.4, 0.4),
            fontName='Helvetica'
        )
        
        total_participantes = len(resultados)
        promedio_puntos = sum(r.puntos_obtenidos for r in resultados) / total_participantes
        
        stats_text = f"Total de participantes: {total_participantes} | Promedio general: {promedio_puntos:.1f} puntos"
        elements.append(Paragraph(stats_text, stats_style))
    
    # Construir el PDF
    doc.build(elements)
    
    return response

# ============================================================================
# VISTAS PARA MONITOREO EN TIEMPO REAL
# ============================================================================

@login_required
def monitoreo_evaluacion(request, pk):
    """
    Vista principal para el monitoreo en tiempo real de una evaluación
    """
    # Verificar permisos básicos (solo admins pueden acceder al monitoreo)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        messages.error(request, 'No tienes permisos para acceder al monitoreo en tiempo real.')
        return redirect('quizzes:dashboard')
    
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    # Obtener todos los monitoreos activos para esta evaluación
    monitoreos = MonitoreoEvaluacion.objects.filter(
        evaluacion=evaluacion,
        estado='activo'
    ).select_related('participante', 'resultado')
    
    # Estadísticas generales
    total_participantes = len(evaluacion.get_participantes_autorizados())
    participantes_activos = monitoreos.filter(ultima_actividad__gte=timezone.now() - timezone.timedelta(minutes=5)).count()
    participantes_finalizados = MonitoreoEvaluacion.objects.filter(
        evaluacion=evaluacion,
        estado='finalizado'
    ).count()
    
    context = {
        'evaluacion': evaluacion,
        'monitoreos': monitoreos,
        'total_participantes': total_participantes,
        'participantes_activos': participantes_activos,
        'participantes_finalizados': participantes_finalizados,
        'participantes_pendientes': total_participantes - participantes_activos - participantes_finalizados,
    }
    
    return render(request, 'quizzes/monitoreo_evaluacion.html', context)


@csrf_exempt
@login_required
def actualizar_monitoreo(request, pk):
    """
    Endpoint para actualizar el estado del monitoreo desde el frontend
    """
    # Verificar permisos básicos (solo admins pueden actualizar monitoreo)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        participante_id = data.get('participante_id')
        evaluacion_id = data.get('evaluacion_id')
        
        # Obtener o crear el monitoreo
        participante = get_object_or_404(Participantes, pk=participante_id)
        evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
        resultado = get_object_or_404(ResultadoEvaluacion, participante=participante, evaluacion=evaluacion)
        
        monitoreo, created = MonitoreoEvaluacion.objects.get_or_create(
            evaluacion=evaluacion,
            participante=participante,
            defaults={'resultado': resultado}
        )
        
        if not created:
            monitoreo.resultado = resultado
        
        # Actualizar datos del monitoreo
        monitoreo.pagina_actual = data.get('pagina_actual', monitoreo.pagina_actual)
        monitoreo.preguntas_respondidas = data.get('preguntas_respondidas', monitoreo.preguntas_respondidas)
        monitoreo.preguntas_revisadas = data.get('preguntas_revisadas', monitoreo.preguntas_revisadas)
        monitoreo.tiempo_activo = data.get('tiempo_activo', monitoreo.tiempo_activo)
        monitoreo.tiempo_inactivo = data.get('tiempo_inactivo', monitoreo.tiempo_inactivo)
        
        # Verificar inactividad (más de 5 minutos sin actividad)
        tiempo_ultima_actividad = (timezone.now() - monitoreo.ultima_actividad).total_seconds()
        if tiempo_ultima_actividad > 300:  # 5 minutos
            monitoreo.agregar_alerta('inactividad', f'Estudiante inactivo por {int(tiempo_ultima_actividad/60)} minutos', 'media')
        
        monitoreo.save()
        
        return JsonResponse({
            'success': True,
            'monitoreo_id': monitoreo.id,
            'ultima_actividad': monitoreo.ultima_actividad.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
def obtener_estado_monitoreo(request, pk):
    """
    Endpoint para obtener el estado actual del monitoreo
    """
    # Verificar permisos básicos (solo admins pueden acceder al estado del monitoreo)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    # Obtener todos los participantes autorizados
    participantes_autorizados = evaluacion.get_participantes_autorizados()
    datos_monitoreo = []
    
    for participante in participantes_autorizados:
        # Verificar si el participante tiene un resultado completado
        resultado = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            completada=True
        ).first()
        
        # Obtener o crear el monitoreo para este participante
        monitoreo, created = MonitoreoEvaluacion.objects.get_or_create(
            evaluacion=evaluacion,
            participante=participante,
            defaults={'resultado': resultado} if resultado else {}
        )
        
        # Si el participante tiene un resultado completado, asegurar que el monitoreo esté finalizado
        if resultado and monitoreo.estado != 'finalizado':
            monitoreo.estado = 'finalizado'
            monitoreo.resultado = resultado
            monitoreo.save()
        
        # Si no hay resultado completado pero el monitoreo está finalizado, cambiar a activo
        if not resultado and monitoreo.estado == 'finalizado':
            monitoreo.estado = 'activo'
            monitoreo.save()
        
        # Calcular intentos para este participante
        intentos_disponibles = participante.get_intentos_disponibles(evaluacion)
        intentos_usados = participante.get_intentos_usados(evaluacion)
        
        # Lógica mejorada para manejar estados con nuevos intentos
        # 1. Si tiene resultado completado y NO hay intentos disponibles -> Finalizado
        # 2. Si tiene resultado completado pero SÍ hay intentos disponibles -> Inactivo (puede hacer nuevo intento)
        # 3. Si NO tiene resultado completado pero tiene intentos disponibles -> Depende si ha iniciado o no
        # 4. Si está rindiendo actualmente (resultado no completado) -> Activo
        
        # Verificar si tiene un resultado actualmente en progreso (no completado)
        resultado_en_progreso = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            completada=False
        ).first()
        
        # Actualizar lógica del estado del monitoreo
        if resultado_en_progreso:
            # Está rindiendo actualmente
            if monitoreo.estado != 'activo':
                monitoreo.estado = 'activo'
                monitoreo.resultado = resultado_en_progreso
                monitoreo.ultima_actividad = timezone.now()
                monitoreo.save()
        elif resultado and intentos_disponibles == 0:
            # Tiene resultado completado y NO tiene más intentos -> Finalizado definitivo
            if monitoreo.estado != 'finalizado':
                monitoreo.estado = 'finalizado'
                monitoreo.resultado = resultado
                monitoreo.save()
        elif resultado and intentos_disponibles > 0:
            # Tiene resultado completado pero SÍ tiene intentos disponibles -> Puede reiniciar
            if monitoreo.estado == 'finalizado':
                monitoreo.estado = 'inactivo'  # Puede iniciar nuevo intento cuando quiera
                monitoreo.save()
        elif not resultado and intentos_disponibles > 0:
            # No ha completado ningún intento pero tiene intentos -> Pendiente
            if monitoreo.estado == 'finalizado':
                monitoreo.estado = 'pendiente'
                monitoreo.save()
        
        # Verificar si el participante ha iniciado alguna vez la evaluación
        # (si tiene cualquier resultado, completado o no)
        ha_iniciado = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante
        ).exists()
        
        # Agregar datos del monitoreo
        datos_monitoreo.append({
            'id': monitoreo.id,
            'participante_id': monitoreo.participante.id,
            'participante_nombre': monitoreo.participante.NombresCompletos,
            'participante_cedula': monitoreo.participante.cedula,
            'estado': monitoreo.estado,
            'esta_activo': monitoreo.esta_activo() if monitoreo.estado == 'activo' else False,
            'ha_iniciado': ha_iniciado,  # Ha iniciado si tiene cualquier resultado
            'preguntas_respondidas': monitoreo.preguntas_respondidas,
            'preguntas_revisadas': monitoreo.preguntas_revisadas,
            'porcentaje_avance': round(monitoreo.get_porcentaje_avance(), 1),
            'ultima_actividad': monitoreo.ultima_actividad.isoformat(),
            'alertas_count': len(monitoreo.alertas_detectadas),
            'alertas_recientes': [
                alerta for alerta in monitoreo.alertas_detectadas[-3:]  # Últimas 3 alertas
            ],
            'tiene_resultado_completado': resultado is not None,
            'puntaje': resultado.puntaje if resultado else None,
            'puntaje_numerico': resultado.get_puntaje_numerico() if resultado else None,
            # CAMPOS DE INTENTOS
            'intentos_disponibles': intentos_disponibles,
            'intentos_usados': intentos_usados,
            # CAMPOS DE CAMBIOS DE PESTAÑAS
            'cambios_pestana_actuales': resultado_en_progreso.cambios_pestana if resultado_en_progreso and hasattr(resultado_en_progreso, 'cambios_pestana') else (resultado.cambios_pestana if resultado and hasattr(resultado, 'cambios_pestana') else 0),
            'cambios_pestana_maximo': 3  # Límite máximo de cambios de pestañas
        })
    
    return JsonResponse({
        'monitoreos': datos_monitoreo,
        'timestamp': timezone.now().isoformat()
    })


@csrf_exempt
@login_required
def finalizar_evaluacion_admin(request, pk):
    """
    Endpoint para finalizar una evaluación por decisión administrativa
    """
    # Verificar permisos básicos (solo admins pueden finalizar evaluaciones)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        monitoreo_id = data.get('monitoreo_id')
        motivo = data.get('motivo', 'Finalización administrativa')
        
        monitoreo = get_object_or_404(MonitoreoEvaluacion, pk=monitoreo_id)
        
        # Finalizar la evaluación
        monitoreo.finalizar_por_admin(request.user, motivo)
        
        return JsonResponse({
            'success': True,
            'message': f'Evaluación de {monitoreo.participante.NombresCompletos} finalizada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def detalle_monitoreo(request, monitoreo_id):
    """
    Vista para ver el detalle completo de un monitoreo específico
    """
    # Verificar permisos básicos (solo admins pueden acceder al detalle del monitoreo)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        messages.error(request, 'No tienes permisos para acceder a esta funcionalidad.')
        return redirect('quizzes:dashboard')
    
    monitoreo = get_object_or_404(MonitoreoEvaluacion, pk=monitoreo_id)
    
    context = {
        'monitoreo': monitoreo,
        'evaluacion': monitoreo.evaluacion,
        'participante': monitoreo.participante,
        'resultado': monitoreo.resultado,
    }
    
    return render(request, 'quizzes/detalle_monitoreo.html', context)


@csrf_exempt
@login_required
def agregar_alerta_manual(request, monitoreo_id):
    """
    Endpoint para agregar alertas manuales desde el panel de administración
    """
    # Verificar permisos básicos (solo admins pueden agregar alertas manuales)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        tipo_alerta = data.get('tipo_alerta')
        descripcion = data.get('descripcion')
        severidad = data.get('severidad', 'baja')
        
        monitoreo = get_object_or_404(MonitoreoEvaluacion, pk=monitoreo_id)
        monitoreo.agregar_alerta(tipo_alerta, descripcion, severidad)
        
        return JsonResponse({
            'success': True,
            'message': 'Alerta agregada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def send_credentials_for_clave_temporal(tipo_usuario, user_id):
    """
    Función auxiliar para generar nueva contraseña y enviar email de credenciales
    para la funcionalidad de solicitar clave temporal.
    
    Args:
        tipo_usuario (str): 'participante' o 'admin'
        user_id (int): ID del usuario
    
    Returns:
        tuple: (success, message, email) donde success es bool, message es str, email es str
    """
    try:
        if tipo_usuario == 'participante':
            user_obj = Participantes.objects.get(id=user_id)
            nombre = user_obj.NombresCompletos
            email = user_obj.email
            username = user_obj.user.username
            
            # Generar nueva contraseña temporal
            nueva_password = get_random_string(length=6)
            user_obj.password_temporal = nueva_password
            user_obj.save()
            # Actualizar también la contraseña del usuario
            user_obj.user.set_password(nueva_password)
            user_obj.user.save()
            
            subject = f'Credenciales de Acceso - Sistema Olymp'
            system_name = 'Sistema Olymp'
            
        else:  # admin
            user_obj = AdminProfile.objects.get(id=user_id)
            nombre = user_obj.user.get_full_name()
            email = user_obj.user.email
            username = user_obj.user.username
            
            # Generar nueva contraseña
            nueva_password = get_random_string(length=8)
            user_obj.password = nueva_password
            user_obj.save()
            # Actualizar también la contraseña del usuario
            user_obj.user.set_password(nueva_password)
            user_obj.user.save()
            
            subject = f'Credenciales de Acceso - Panel de Administración Olymp'
            system_name = 'Panel de Administración Olymp'
        
        # Generar mensajes usando la función global
        plain_message, html_message = generate_email_messages(
            subject=subject,
            nombre=nombre,
            system_name=system_name,
            username=username,
            nueva_password=nueva_password,
            email_type='credentials'
        )
        
        # Enviar el correo
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
            html_message=html_message
        )
        
        return True, f'Se ha enviado una nueva contraseña temporal a su correo electrónico ({email}).', email
        
    except Exception as email_error:
        return False, f'Error al enviar el correo: {str(email_error)}', email if 'email' in locals() else None


@csrf_exempt
def solicitar_clave_temporal(request):
    """
    Endpoint para solicitar una nueva clave temporal
    No requiere login ya que es para usuarios que olvidaron su contraseña
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        
        if not username:
            return JsonResponse({
                'success': False, 
                'message': 'El nombre de usuario es requerido.'
            })
        
        # Buscar el usuario (puede ser admin o participante)
        tipo_usuario = None
        email = None
        user_id = None
        
        # Primero buscar como administrador
        try:
            admin_profile = AdminProfile.objects.get(user__username__iexact=username)
            tipo_usuario = 'admin'
            email = admin_profile.user.email
            user_id = admin_profile.id
        except AdminProfile.DoesNotExist:
            # Si no es admin, buscar como participante
            try:
                participante = Participantes.objects.get(user__username__iexact=username)
                tipo_usuario = 'participante'
                email = participante.email
                user_id = participante.id
            except Participantes.DoesNotExist:
                # Intentar buscar por cédula (solo para participantes)
                try:
                    participante = Participantes.objects.get(cedula=username)
                    tipo_usuario = 'participante'
                    email = participante.email
                    user_id = participante.id
                except Participantes.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': f'El usuario "{username}" no existe en el sistema.'
                    })
        
        # Verificar si puede solicitar (máximo 3 por semana)
        solicitudes_semana = SolicitudClaveTemporal.contar_solicitudes_semana(username, tipo_usuario)
        if solicitudes_semana >= 3:
            return JsonResponse({
                'success': False,
                'message': f'Ha excedido el límite de solicitudes. Ya ha solicitado {solicitudes_semana} veces esta semana. El límite es de 3 solicitudes por semana.'
            })
        
        # Crear registro de solicitud
        solicitud = SolicitudClaveTemporal.objects.create(
            username=username,
            tipo_usuario=tipo_usuario,
            email=email
        )
        
        # Generar nueva contraseña y enviar email usando la función auxiliar
        success, message, email_sent = send_credentials_for_clave_temporal(tipo_usuario, user_id)
        
        if success:
            # Marcar solicitud como procesada
            solicitud.procesada = True
            solicitud.save()
            
            return JsonResponse({
                'success': True,
                'message': message
            })
        else:
            # Si hay error en el envío, marcar como fallida
            solicitud.procesada = False
            solicitud.mensaje_error = message
            solicitud.save()
            
            return JsonResponse({
                'success': False,
                'message': message
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Error en el formato de datos enviados.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required
def settings_view(request):
    """Vista de configuración general."""
    # Permitir solo superusuarios o administradores con acceso total
    if not (request.user.is_superuser or has_full_access(request.user)):
        messages.error(request, 'No tiene permisos para acceder a Configuración.')
        return redirect('quizzes:dashboard')
    from .models import SystemConfig
    if request.method == 'POST':
        try:
            if 'num_etapas' in request.POST:
                num_etapas_val = int(request.POST.get('num_etapas'))
                if num_etapas_val not in [2, 3]:
                    messages.error(request, 'Valor de etapas inválido. Debe ser 2 o 3.')
                    return redirect('quizzes:settings')
                obj = SystemConfig.objects.first()
                if obj is None:
                    obj = SystemConfig(num_etapas=num_etapas_val)
                else:
                    obj.num_etapas = num_etapas_val
                obj.save()
                messages.success(request, f'Configuración actualizada a {num_etapas_val} etapas.')
                return redirect('quizzes:settings')
            if 'anio_concurso' in request.POST:
                anio_val = int(request.POST.get('anio_concurso'))
                current_year = timezone.now().year
                if anio_val > current_year:
                    messages.error(request, 'El año no puede ser superior al año actual.')
                    return redirect('quizzes:settings')
                obj = SystemConfig.objects.first()
                if obj is None:
                    obj = SystemConfig(active_year=anio_val)
                else:
                    obj.active_year = anio_val
                obj.save()
                messages.success(request, f'Año activo actualizado a {anio_val}.')
                return redirect('quizzes:settings')
        except Exception as e:
            messages.error(request, f'No se pudo guardar la configuración: {str(e)}')
            return redirect('quizzes:settings')
    # GET
    context = {
        'num_etapas': SystemConfig.get_num_etapas(),
        'active_year': SystemConfig.get_active_year(),
        'now': timezone.now(),
    }
    return render(request, 'quizzes/settings.html', context)


def custom_404_view(request, exception=None, path=None):
    """Vista personalizada para errores 404"""
    from django.conf import settings
    from django.http import Http404
    from django.shortcuts import render
    
    # Si está deshabilitado, usar comportamiento estándar de Django
    if not getattr(settings, 'ENABLE_CUSTOM_ERROR_PAGES', True):
        raise Http404("Página no encontrada")
    
    # Si viene de una URL catch-all, path será el parámetro
    # Si viene del handler404, exception será el parámetro
    requested_url = path if path else request.path
    
    context = {
        'error_message': 'La página que buscas no existe',
        'error_code': '404',
        'error_description': 'El endpoint o URL solicitado no fue encontrado en nuestro servidor.',
        'requested_url': requested_url,
        'suggested_actions': [
            'Verifica que la URL esté escrita correctamente',
            'Regresa a la página principal',
            'Contacta al administrador si crees que esto es un error'
        ]
    }
    return render(request, 'errors/404.html', context, status=404)


@csrf_exempt
@login_required
def dar_nuevo_intento_evaluacion(request, pk):
    """
    Vista para dar un nuevo intento a un participante en una evaluación específica
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    # Verificar permisos básicos (solo admins pueden dar nuevos intentos)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
    
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    try:
        data = json.loads(request.body)
        participante_id = data.get('participante_id')
        
        if not participante_id:
            return JsonResponse({'success': False, 'error': 'ID del participante requerido'})
        
        participante = get_object_or_404(Participantes, id=participante_id)
        
        # Verificar que el participante esté autorizado para esta evaluación
        participantes_autorizados = evaluacion.get_participantes_autorizados()
        if participante not in participantes_autorizados:
            return JsonResponse({'success': False, 'error': 'Participante no autorizado para esta evaluación'})
        
        # Obtener el monitoreo actual del participante
        monitoreo = MonitoreoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante
        ).first()
        
        if not monitoreo:
            return JsonResponse({'success': False, 'error': 'No se encontró monitoreo para este participante'})
        
        # Verificar los intentos actuales del participante
        intentos_disponibles = participante.get_intentos_disponibles(evaluacion)
        intentos_usados = participante.get_intentos_usados(evaluacion)
        
        # Crear o actualizar el registro de intentos para otorgar uno adicional
        intento_config, created = IntentosParticipante.objects.get_or_create(
            participante=participante,
            evaluacion=evaluacion,
            defaults={
                'intentos_maximos': participante.intentos_maximos_default + 1,
                'creado_por': request.user,
                'motivo': 'Intento adicional otorgado por administrador'
            }
        )
        
        if not created:
            # Si ya existe, incrementar los intentos máximos
            intento_config.intentos_maximos += 1
            intento_config.save()
        
        # Recalcular los intentos disponibles después del otorgamiento
        nuevos_intentos_disponibles = participante.get_intentos_disponibles(evaluacion)
        
        # Si el participante está finalizado pero ahora tiene intentos, reactivarlo
        if monitoreo.estado == 'finalizado' and nuevos_intentos_disponibles > 0:
            monitoreo.estado = 'inactivo'  # Lo ponemos en inactivo para que pueda reiniciar
            monitoreo.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Se ha otorgado un nuevo intento a {participante.NombresCompletos}. Intentos disponibles: {nuevos_intentos_disponibles}',
            'intentos_disponibles': nuevos_intentos_disponibles,
            'intentos_usados': participante.get_intentos_usados(evaluacion)
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
def reducir_cambios_pestana(request, pk):
    """
    Vista para reducir la cantidad de cambios de pestañas a un participante
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    # Verificar permisos básicos (solo admins pueden reducir cambios de pestañas)
    if not (request.user.is_superuser or hasattr(request.user, 'adminprofile')):
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
    
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    
    try:
        data = json.loads(request.body)
        participante_id = data.get('participante_id')
        cantidad_reduccion = int(data.get('cantidad_reduccion', 1))
        
        if not participante_id:
            return JsonResponse({'success': False, 'error': 'ID del participante requerido'})
        
        if cantidad_reduccion <= 0:
            return JsonResponse({'success': False, 'error': 'La cantidad de reducción debe ser mayor a 0'})
        
        participante = get_object_or_404(Participantes, id=participante_id)
        
        # Verificar que el participante esté autorizado para esta evaluación
        participantes_autorizados = evaluacion.get_participantes_autorizados()
        if participante not in participantes_autorizados:
            return JsonResponse({'success': False, 'error': 'Participante no autorizado para esta evaluación'})
        
        # Obtener el resultado activo (no completado) del participante
        resultado_activo = ResultadoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante,
            completada=False
        ).first()
        
        if not resultado_activo:
            return JsonResponse({'success': False, 'error': 'El participante no tiene una evaluación activa'})
        
        # Verificar que el participante tenga cambios de pestañas registrados
        cambios_actuales = resultado_activo.cambios_pestana or 0
        
        if cambios_actuales == 0:
            return JsonResponse({'success': False, 'error': 'El participante no ha realizado cambios de pestañas'})
        
        # Calcular nueva cantidad (no puede ser menor a 0)
        nuevos_cambios = max(0, cambios_actuales - cantidad_reduccion)
        
        # Actualizar el resultado
        resultado_activo.cambios_pestana = nuevos_cambios
        resultado_activo.save()
        
        # También actualizar el monitoreo si existe
        monitoreo = MonitoreoEvaluacion.objects.filter(
            evaluacion=evaluacion,
            participante=participante
        ).first()
        
        if monitoreo:
            monitoreo.cambios_pestana = nuevos_cambios
            
            # Agregar una alerta administrativa del cambio
            from datetime import datetime
            alerta = {
                'tipo': 'admin_reduccion_pestanas',
                'mensaje': f'Cambios de pestaña reducidos por administrador: {cambios_actuales} → {nuevos_cambios}',
                'timestamp': datetime.now().isoformat(),
                'admin_usuario': request.user.username,
                'cantidad_reducida': cantidad_reduccion
            }
            
            if monitoreo.alertas is None:
                monitoreo.alertas = []
            
            monitoreo.alertas.append(alerta)
            monitoreo.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Se redujeron {cantidad_reduccion} cambios de pestaña a {participante.NombresCompletos}',
            'cambios_anteriores': cambios_actuales,
            'cambios_nuevos': nuevos_cambios,
            'cantidad_reducida': cantidad_reduccion
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'La cantidad de reducción debe ser un número válido'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})