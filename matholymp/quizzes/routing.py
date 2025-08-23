from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/monitoreo/evaluacion/(?P<evaluacion_id>\d+)/$', consumers.MonitoreoEvaluacionConsumer.as_asgi()),
    re_path(r'ws/evaluacion/(?P<evaluacion_id>\d+)/participante/(?P<participante_id>\d+)/$', consumers.EvaluacionParticipanteConsumer.as_asgi()),
]
