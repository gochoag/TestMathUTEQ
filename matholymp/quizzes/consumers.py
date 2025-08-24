import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Evaluacion, MonitoreoEvaluacion, Participantes, ResultadoEvaluacion


class MonitoreoEvaluacionConsumer(AsyncWebsocketConsumer):
    """
    Consumer para el monitoreo en tiempo real de evaluaciones por parte de administradores
    """
    
    async def connect(self):
        self.evaluacion_id = self.scope['url_route']['kwargs']['evaluacion_id']
        self.group_name = f'monitoreo_evaluacion_{self.evaluacion_id}'
        
        # Verificar que el usuario sea administrador
        user = self.scope["user"]
        if not user.is_authenticated or not (user.is_staff or user.is_superuser):
            await self.close()
            return
        
        # Verificar que la evaluación existe
        evaluacion_exists = await self.check_evaluacion_exists()
        if not evaluacion_exists:
            await self.close()
            return
        
        # Unirse al grupo
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar datos iniciales del monitoreo
        await self.send_initial_monitoring_data()
    
    async def disconnect(self, close_code):
        # Abandonar el grupo
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Manejar mensajes recibidos del frontend
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_update':
                # Solicitud de actualización manual
                await self.send_monitoring_update()
            elif message_type == 'finalizar_evaluacion':
                # Finalizar evaluación de un participante
                await self.handle_finalizar_evaluacion(data)
            elif message_type == 'agregar_alerta':
                # Agregar alerta a un participante
                await self.handle_agregar_alerta(data)
                
        except json.JSONDecodeError:
            await self.send_error_message('Formato de mensaje inválido')
    
    # Funciones auxiliares para eliminar duplicación
    async def send_success_message(self, message):
        """Enviar mensaje de éxito"""
        await self.send(text_data=json.dumps({
            'type': 'success',
            'message': message
        }))
    
    async def send_error_message(self, message):
        """Enviar mensaje de error"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    async def handle_operation_result(self, success, success_message, error_message):
        """Manejar resultado de operaciones de manera uniforme"""
        if success:
            await self.send_success_message(success_message)
            # Enviar actualización a todo el grupo
            await self.send_monitoring_update()
        else:
            await self.send_error_message(error_message)
    
    async def intentos_updated(self, event):
        """
        Manejar actualización de intentos de un participante
        """
        await self.send(text_data=json.dumps({
            'type': 'intentos_updated',
            'participante_id': event['participante_id'],
            'participante_nombre': event.get('participante_nombre', ''),
            'participante_cedula': event.get('participante_cedula', ''),
            'nuevos_intentos': event['nuevos_intentos'],
            'intentos_utilizados': event['intentos_utilizados'],
            'puede_realizar_intento': event['puede_realizar_intento'],
            'timestamp': timezone.now().isoformat()
        }))
    
    async def evaluacion_finalizada_admin(self, event):
        """
        Manejar finalización administrativa de evaluación
        """
        await self.send(text_data=json.dumps({
            'type': 'evaluacion_finalizada_admin',
            'participante_id': event['participante_id'],
            'participante_nombre': event.get('participante_nombre', ''),
            'participante_cedula': event.get('participante_cedula', ''),
            'monitoreo_id': event.get('monitoreo_id', ''),
            'motivo': event['motivo'],
            'admin': event['admin'],
            'timestamp': event['timestamp']
        }))
    
    async def send_initial_monitoring_data(self):
        """
        Enviar datos iniciales del monitoreo
        """
        monitoring_data = await self.get_monitoring_data()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': monitoring_data
        }))
    
    async def send_monitoring_update(self):
        """
        Enviar actualización del monitoreo al grupo
        """
        monitoring_data = await self.get_monitoring_data()
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'monitoring_update',
                'data': monitoring_data
            }
        )
    
    async def monitoring_update(self, event):
        """
        Enviar actualización del monitoreo al cliente
        """
        await self.send(text_data=json.dumps({
            'type': 'monitoring_update',
            'data': event['data']
        }))
    
    async def participant_update(self, event):
        """
        Manejar actualizaciones específicas de participantes
        """
        await self.send(text_data=json.dumps({
            'type': 'participant_update',
            'participant_id': event['participant_id'],
            'event_type': event.get('event_type', 'update'),
            'data': event['data']
        }))
    
    async def handle_finalizar_evaluacion(self, data):
        """
        Manejar finalización administrativa de evaluación
        """
        try:
            monitoreo_id = data.get('monitoreo_id')
            motivo = data.get('motivo')
            
            if not monitoreo_id or not motivo:
                await self.send_error_message('Datos insuficientes para finalizar evaluación')
                return
            
            success = await self.finalizar_evaluacion_participante(monitoreo_id, motivo)
            await self.handle_operation_result(
                success, 
                'Evaluación finalizada correctamente',
                'Error al finalizar la evaluación'
            )
                
        except Exception as e:
            await self.send_error_message(f'Error interno: {str(e)}')
    
    async def handle_agregar_alerta(self, data):
        """
        Manejar agregar alerta a un participante
        """
        try:
            monitoreo_id = data.get('monitoreo_id')
            tipo_alerta = data.get('tipo_alerta')
            severidad = data.get('severidad')
            descripcion = data.get('descripcion')
            
            if not all([monitoreo_id, tipo_alerta, severidad, descripcion]):
                await self.send_error_message('Datos insuficientes para agregar alerta')
                return
            
            success = await self.agregar_alerta_participante(monitoreo_id, tipo_alerta, severidad, descripcion)
            await self.handle_operation_result(
                success,
                'Alerta agregada correctamente',
                'Error al agregar la alerta'
            )
                
        except Exception as e:
            await self.send_error_message(f'Error interno: {str(e)}')
    
    @database_sync_to_async
    def check_evaluacion_exists(self):
        """Verificar que la evaluación existe"""
        return Evaluacion.objects.filter(id=self.evaluacion_id).exists()
    
    @database_sync_to_async
    def get_monitoring_data(self):
        """
        Obtener datos del monitoreo de la evaluación
        """
        try:
            evaluacion = Evaluacion.objects.get(id=self.evaluacion_id)
            
            # Obtener todos los participantes autorizados
            participantes_autorizados = evaluacion.get_participantes_autorizados()
            total_participantes = len(participantes_autorizados)
            
            # Obtener todos los monitoreos para esta evaluación
            monitoreos = MonitoreoEvaluacion.objects.filter(evaluacion=evaluacion).select_related(
                'participante', 'resultado'
            )
            
            # Contar estadísticas
            participantes_activos = 0
            participantes_finalizados = 0
            participantes_pendientes = 0
            
            # Crear un set de participantes que ya tienen monitoreo
            participantes_con_monitoreo = set()
            
            monitoreos_data = []
            
            for monitoreo in monitoreos:
                participantes_con_monitoreo.add(monitoreo.participante.id)
                
                # Determinar si está activo (última actividad en los últimos 5 minutos)
                tiempo_limite = timezone.now() - timedelta(minutes=5)
                esta_activo = monitoreo.ultima_actividad > tiempo_limite
                
                if monitoreo.estado == 'finalizado':
                    participantes_finalizados += 1
                elif esta_activo and monitoreo.estado == 'activo':
                    participantes_activos += 1
                else:
                    participantes_pendientes += 1
                
                # Obtener información de intentos
                intento_info = evaluacion.get_o_crear_intento_participante(monitoreo.participante)
                puede_realizar_intento = intento_info.puede_realizar_intento()
                
                # Corregir lógica de número de intento actual
                if monitoreo.estado == 'finalizado':
                    # Si está finalizado, mostrar el último intento realizado
                    numero_intento_actual = intento_info.intentos_utilizados
                else:
                    # Si está activo, mostrar el intento actual (no el siguiente)
                    numero_intento_actual = intento_info.intentos_utilizados
                
                # Obtener información del resultado si existe
                puntaje = 0
                puntaje_numerico = "0.000/10"
                tiene_resultado_completado = False
                
                if monitoreo.resultado and monitoreo.resultado.completada:
                    tiene_resultado_completado = True
                    puntaje = float(monitoreo.resultado.get_puntaje_porcentaje())
                    puntaje_numerico = monitoreo.resultado.get_puntaje_numerico()
                
                monitoreo_data = {
                    'id': monitoreo.id,
                    'participante_id': monitoreo.participante.id,
                    'participante_nombre': monitoreo.participante.NombresCompletos,
                    'participante_cedula': monitoreo.participante.cedula,
                    'estado': monitoreo.estado,
                    'esta_activo': esta_activo,
                    'pagina_actual': monitoreo.pagina_actual,
                    'preguntas_respondidas': monitoreo.preguntas_respondidas,
                    'preguntas_revisadas': monitoreo.preguntas_revisadas,
                    'porcentaje_avance': monitoreo.get_porcentaje_avance(),
                    'ultima_actividad': monitoreo.ultima_actividad.isoformat(),
                    'alertas_count': len(monitoreo.alertas_detectadas),
                    'alertas_detectadas': monitoreo.alertas_detectadas,
                    'intentos_utilizados': intento_info.intentos_utilizados,
                    'intentos_permitidos': intento_info.intentos_permitidos,
                    'puede_realizar_intento': puede_realizar_intento,
                    'numero_intento_actual': numero_intento_actual,
                    'puntaje': puntaje,
                    'puntaje_numerico': puntaje_numerico,
                    'tiene_resultado_completado': tiene_resultado_completado,
                    'finalizado_por_admin': bool(monitoreo.finalizado_por_admin),
                    'motivo_finalizacion': monitoreo.motivo_finalizacion or '',
                }
                
                monitoreos_data.append(monitoreo_data)
            
            # Los participantes pendientes son los que no tienen monitoreo + los que están inactivos
            participantes_sin_monitoreo = total_participantes - len(participantes_con_monitoreo)
            participantes_pendientes += participantes_sin_monitoreo
            
            return {
                'evaluacion': {
                    'id': evaluacion.id,
                    'title': evaluacion.title,
                    'etapa': evaluacion.etapa,
                    'etapa_display': evaluacion.get_etapa_display(),
                },
                'estadisticas': {
                    'total_participantes': total_participantes,
                    'participantes_activos': participantes_activos,
                    'participantes_finalizados': participantes_finalizados,
                    'participantes_pendientes': participantes_pendientes,
                },
                'monitoreos': monitoreos_data,
                'timestamp': timezone.now().isoformat()
            }
            
        except Evaluacion.DoesNotExist:
            return {'error': 'Evaluación no encontrada'}
        except Exception as e:
            return {'error': f'Error al obtener datos: {str(e)}'}
    
    @database_sync_to_async
    def finalizar_evaluacion_participante(self, monitoreo_id, motivo):
        """
        Finalizar evaluación de un participante por decisión administrativa
        """
        try:
            monitoreo = MonitoreoEvaluacion.objects.get(id=monitoreo_id)
            admin_user = User.objects.get(id=self.scope["user"].id)
            
            monitoreo.finalizar_por_admin(admin_user, motivo)
            return True
            
        except (MonitoreoEvaluacion.DoesNotExist, User.DoesNotExist):
            return False
        except Exception:
            return False
    
    @database_sync_to_async
    def agregar_alerta_participante(self, monitoreo_id, tipo_alerta, severidad, descripcion):
        """
        Agregar alerta a un participante
        """
        try:
            monitoreo = MonitoreoEvaluacion.objects.get(id=monitoreo_id)
            monitoreo.agregar_alerta(tipo_alerta, descripcion, severidad)
            return True
            
        except MonitoreoEvaluacion.DoesNotExist:
            return False
        except Exception:
            return False


class EvaluacionParticipanteConsumer(AsyncWebsocketConsumer):
    """
    Consumer para el monitoreo individual de un participante durante la evaluación
    """
    
    async def connect(self):
        self.evaluacion_id = self.scope['url_route']['kwargs']['evaluacion_id']
        self.participante_id = self.scope['url_route']['kwargs']['participante_id']
        self.group_name = f'evaluacion_{self.evaluacion_id}_participante_{self.participante_id}'
        self.monitoring_group_name = f'monitoreo_evaluacion_{self.evaluacion_id}'
        
        # Verificar autenticación y autorización
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return
        
        # Verificar que el participante puede acceder a esta evaluación
        can_access = await self.check_participant_access()
        if not can_access:
            await self.close()
            return
        
        # Unirse al grupo individual
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Crear o actualizar monitoreo
        await self.create_or_update_monitoring()
    
    async def disconnect(self, close_code):
        # Abandonar el grupo
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        
        # Actualizar última actividad
        await self.update_last_activity()
    
    async def receive(self, text_data):
        """
        Manejar mensajes del participante durante la evaluación
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'heartbeat':
                # Latido del corazón para mantener conexión activa
                await self.handle_heartbeat(data)
            elif message_type == 'page_change':
                # Cambio de página
                await self.handle_page_change(data)
            elif message_type == 'answer_update':
                # Actualización de respuesta
                await self.handle_answer_update(data)
            elif message_type == 'progress_update':
                # Actualización de progreso
                await self.handle_progress_update(data)
            elif message_type == 'auto_save':
                # Guardado automático de respuestas
                await self.handle_auto_save(data)
            elif message_type == 'evaluation_completed':
                # Evaluación completada
                await self.handle_evaluation_completed(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato de mensaje inválido'
            }))
    
    async def evaluation_terminated(self, event):
        """
        Manejar finalización administrativa de evaluación
        """
        await self.send(text_data=json.dumps({
            'type': 'evaluation_terminated',
            'motivo': event['motivo'],
            'admin': event['admin'],
            'timestamp': event['timestamp']
        }))
    
    async def handle_heartbeat(self, data):
        """
        Manejar latido del corazón y actualizar actividad
        """
        await self.update_monitoring_activity(data)
        
        # Notificar al grupo de monitoreo sobre la actividad
        await self.notify_monitoring_group('heartbeat', {
            'ultima_actividad': timezone.now().isoformat(),
            'tiempo_activo': data.get('active_time', 0)
        })
        
        # Responder con confirmación
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_ack',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def handle_page_change(self, data):
        """
        Manejar cambio de página del participante
        """
        page_number = data.get('page', 1)
        await self.update_page_activity(page_number)
        
        # Notificar al grupo de monitoreo
        await self.notify_monitoring_group('page_change', {
            'page': page_number,
            'ultima_actividad': timezone.now().isoformat()
        })
    
    async def handle_answer_update(self, data):
        """
        Manejar actualización de respuesta
        """
        await self.update_monitoring_activity(data)
        
        # Notificar al grupo de monitoreo
        await self.notify_monitoring_group('answer_update', {
            'ultima_actividad': timezone.now().isoformat(),
            'respuesta_actualizada': True
        })
    
    async def handle_progress_update(self, data):
        """
        Manejar actualización de progreso
        """
        preguntas_respondidas = data.get('answered_questions', 0)
        preguntas_revisadas = data.get('reviewed_questions', 0)
        
        await self.update_progress(preguntas_respondidas, preguntas_revisadas)
        
        # Notificar al grupo de monitoreo
        await self.notify_monitoring_group('progress_update', {
            'answered_questions': preguntas_respondidas,
            'reviewed_questions': preguntas_revisadas,
            'ultima_actividad': timezone.now().isoformat()
        })
    
    async def handle_auto_save(self, data):
        """
        Manejar guardado automático de respuestas
        """
        respuestas = data.get('respuestas', {})
        tiempo_restante = data.get('tiempo_restante', 0)
        
        # Guardar respuestas en la base de datos
        await self.save_auto_save_data(respuestas, tiempo_restante)
        
        # Notificar al grupo de monitoreo sobre el guardado
        await self.notify_monitoring_group('auto_save', {
            'respuestas_count': len(respuestas),
            'preguntas_respondidas': len([r for r in respuestas.values() if r]),
            'porcentaje_avance': await self.calculate_progress_percentage(respuestas),
            'ultima_actividad': timezone.now().isoformat()
        })
        
        # Confirmar guardado al participante
        await self.send(text_data=json.dumps({
            'type': 'auto_save_confirmed',
            'timestamp': timezone.now().isoformat(),
            'respuestas_guardadas': len(respuestas)
        }))
    
    async def handle_evaluation_completed(self, data):
        """
        Manejar finalización de evaluación
        """
        await self.complete_monitoring()
        
        # Notificar al grupo de monitoreo con datos completos
        await self.notify_monitoring_group('evaluation_completed', {
            'estado': 'finalizado',
            'ultima_actividad': timezone.now().isoformat(),
            'preguntas_respondidas': data.get('final_answers', 0),
            'preguntas_revisadas': data.get('final_reviewed', 0),
            'resultado_id': data.get('resultado_id')
        })
    
    async def notify_monitoring_group(self, event_type, data):
        """
        Notificar al grupo de monitoreo sobre cambios del participante
        """
        await self.channel_layer.group_send(
            self.monitoring_group_name,
            {
                'type': 'participant_update',
                'participant_id': self.participante_id,
                'event_type': event_type,
                'data': data
            }
        )
    
    @database_sync_to_async
    def check_participant_access(self):
        """
        Verificar que el participante puede acceder a esta evaluación
        """
        try:
            evaluacion = Evaluacion.objects.get(id=self.evaluacion_id)
            participante = Participantes.objects.get(id=self.participante_id)
            
            # Verificar que el usuario pertenece al participante
            if self.scope["user"] != participante.user:
                return False
            
            # Verificar que el participante está autorizado para esta evaluación
            participantes_autorizados = evaluacion.get_participantes_autorizados()
            return participante in participantes_autorizados
            
        except (Evaluacion.DoesNotExist, Participantes.DoesNotExist):
            return False
    
    @database_sync_to_async
    def create_or_update_monitoring(self):
        """
        Crear o actualizar el registro de monitoreo
        """
        try:
            evaluacion = Evaluacion.objects.get(id=self.evaluacion_id)
            participante = Participantes.objects.get(id=self.participante_id)
            
            monitoreo, created = MonitoreoEvaluacion.objects.get_or_create(
                evaluacion=evaluacion,
                participante=participante,
                defaults={
                    'estado': 'activo',
                    'ultima_actividad': timezone.now(),
                    'tiempo_activo': 0,
                    'tiempo_inactivo': 0,
                    'pagina_actual': 1,
                    'preguntas_respondidas': 0,
                    'preguntas_revisadas': 0,
                    'alertas_detectadas': [],
                }
            )
            
            if not created:
                # Si ya existe, verificar si debe cambiar de 'finalizado' a 'activo'
                if monitoreo.estado == 'finalizado':
                    # Es un nuevo intento, cambiar estado a activo
                    monitoreo.estado = 'activo'
                    monitoreo.preguntas_respondidas = 0
                    monitoreo.preguntas_revisadas = 0
                    monitoreo.pagina_actual = 1
                    monitoreo.resultado = None  # Limpiar resultado anterior
                    
                    # Notificar al grupo de monitoreo sobre el nuevo intento
                    asyncio.create_task(self.notify_monitoring_group('new_attempt', {
                        'estado': 'activo',
                        'preguntas_respondidas': 0,
                        'preguntas_revisadas': 0,
                        'pagina_actual': 1,
                        'ultima_actividad': timezone.now().isoformat()
                    }))
                
                # Actualizar actividad
                monitoreo.ultima_actividad = timezone.now()
                monitoreo.save()
            
            return monitoreo.id
            
        except (Evaluacion.DoesNotExist, Participantes.DoesNotExist):
            return None
    
    # Función auxiliar para eliminar duplicación en actualizaciones de monitoreo
    @database_sync_to_async
    def _update_monitoring_field(self, field_name, value, additional_data=None):
        """
        Función auxiliar para actualizar campos del monitoreo de manera uniforme
        """
        try:
            monitoreo = MonitoreoEvaluacion.objects.get(
                evaluacion_id=self.evaluacion_id,
                participante_id=self.participante_id
            )
            
            # Actualizar campo específico
            setattr(monitoreo, field_name, value)
            
            # Actualizar última actividad
            monitoreo.ultima_actividad = timezone.now()
            
            # Actualizar campos adicionales si se proporcionan
            if additional_data:
                for field, val in additional_data.items():
                    setattr(monitoreo, field, val)
            
            monitoreo.save()
            
        except MonitoreoEvaluacion.DoesNotExist:
            pass
    
    @database_sync_to_async
    def update_monitoring_activity(self, data):
        """
        Actualizar actividad del monitoreo
        """
        additional_data = {}
        if 'active_time' in data:
            additional_data['tiempo_activo'] = data['active_time']
        
        self._update_monitoring_field('ultima_actividad', timezone.now(), additional_data)
    
    @database_sync_to_async
    def update_page_activity(self, page_number):
        """
        Actualizar actividad de página
        """
        self._update_monitoring_field('pagina_actual', page_number)
    
    @database_sync_to_async
    def update_progress(self, preguntas_respondidas, preguntas_revisadas):
        """
        Actualizar progreso del participante
        """
        additional_data = {
            'preguntas_respondidas': preguntas_respondidas,
            'preguntas_revisadas': preguntas_revisadas
        }
        self._update_monitoring_field('ultima_actividad', timezone.now(), additional_data)
    
    @database_sync_to_async
    def update_last_activity(self):
        """
        Actualizar última actividad al desconectar
        """
        self._update_monitoring_field('ultima_actividad', timezone.now())
    
    @database_sync_to_async
    def complete_monitoring(self):
        """
        Completar el monitoreo cuando la evaluación finaliza
        """
        additional_data = {'estado': 'finalizado'}
        self._update_monitoring_field('ultima_actividad', timezone.now(), additional_data)
    
    @database_sync_to_async
    def get_monitoring_data(self):
        """
        Obtener datos del monitoreo para este participante
        """
        try:
            monitoreo = MonitoreoEvaluacion.objects.get(
                evaluacion_id=self.evaluacion_id,
                participante_id=self.participante_id
            )
            
            return {
                'id': monitoreo.id,
                'estado': monitoreo.estado,
                'pagina_actual': monitoreo.pagina_actual,
                'preguntas_respondidas': monitoreo.preguntas_respondidas,
                'preguntas_reviewed': monitoreo.preguntas_revisadas,
                'porcentaje_avance': monitoreo.get_porcentaje_avance(),
                'ultima_actividad': monitoreo.ultima_actividad.isoformat(),
            }
        except MonitoreoEvaluacion.DoesNotExist:
            return None
    
    @database_sync_to_async
    def calculate_progress_percentage(self, respuestas):
        """
        Calcular porcentaje de progreso basado en respuestas
        """
        try:
            evaluacion = Evaluacion.objects.get(id=self.evaluacion_id)
            total_preguntas = evaluacion.preguntas.count()
            respuestas_respondidas = len([r for r in respuestas.values() if r])
            
            if total_preguntas > 0:
                return round((respuestas_respondidas / total_preguntas) * 100, 1)
            return 0
        except Evaluacion.DoesNotExist:
            return 0
    
    @database_sync_to_async
    def save_auto_save_data(self, respuestas, tiempo_restante):
        """
        Guardar respuestas automáticamente en la base de datos
        """
        try:
            evaluacion = Evaluacion.objects.get(id=self.evaluacion_id)
            participante = Participantes.objects.get(id=self.participante_id)
            
            # Obtener o crear el resultado de la evaluación
            resultado, created = ResultadoEvaluacion.objects.get_or_create(
                evaluacion=evaluacion,
                participante=participante,
                defaults={
                    'completada': False,
                    'fecha_inicio': timezone.now(),
                    'respuestas_guardadas': {},
                    'tiempo_total': 0
                }
            )
            
            # Actualizar respuestas guardadas
            if not resultado.respuestas_guardadas:
                resultado.respuestas_guardadas = {}
            
            # Convertir nombres de preguntas del formato 'pregunta_X' a 'X'
            respuestas_actualizadas = {}
            for pregunta_key, opcion_id in respuestas.items():
                if pregunta_key.startswith('pregunta_'):
                    pregunta_id = pregunta_key.replace('pregunta_', '')
                    respuestas_actualizadas[pregunta_id] = opcion_id
                else:
                    respuestas_actualizadas[pregunta_key] = opcion_id
            
            resultado.respuestas_guardadas.update(respuestas_actualizadas)
            resultado.fecha_ultima_actividad = timezone.now()
            resultado.tiempo_restante = tiempo_restante
            resultado.save()
            
            # Actualizar monitoreo
            monitoreo = MonitoreoEvaluacion.objects.get(
                evaluacion=evaluacion,
                participante=participante
            )
            
            # Contar preguntas respondidas
            preguntas_respondidas = len([r for r in resultado.respuestas_guardadas.values() if r])
            monitoreo.preguntas_respondidas = preguntas_respondidas
            monitoreo.ultima_actividad = timezone.now()
            monitoreo.save()
            
            print(f"Auto-save completado para participante {participante.id}: {preguntas_respondidas} respuestas guardadas")
            
        except (Evaluacion.DoesNotExist, Participantes.DoesNotExist, MonitoreoEvaluacion.DoesNotExist) as e:
            print(f"Error en auto-save: {e}")
        except Exception as e:
            print(f"Error inesperado en auto-save: {e}")
