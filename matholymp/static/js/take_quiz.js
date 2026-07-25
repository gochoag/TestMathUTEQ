// Variables globales de la evaluación
let tiempoRestante = window.tiempoRestante;
let timerInterval;
let guardadoInterval;
let evaluacionEnviandose = false;
let evaluacionFinalizadaAdmin = false;
let verificacionInterval;
let modalMostrandose = false;

// Variables para control de cambios de pestaña
let cambiosPestana = window.cambiosPestana;
const maxCambiosPestana = 4;
let documentoVisible = true;
let advertenciasMostradas = false;

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Activar modo evaluación (ocultar sidebar)
    activarModoEvaluacion();
    
    inicializarEvaluacion();
    configurarEventos();
    configurarControlPestanas();
    
    // Mostrar advertencia si ya hay cambios de pestaña registrados al continuar
    if (window.continuarEvaluacion && cambiosPestana > 0) {
        setTimeout(() => {
            if (cambiosPestana > 0 && cambiosPestana < maxCambiosPestana) {
                const cambiosRestantes = maxCambiosPestana - cambiosPestana;
                Swal.fire({
                    icon: 'warning',
                    title: 'Advertencia de Continuación',
                    html: `
                        <div class="text-center">
                            <p><strong>Esta evaluación tiene cambios de pestaña registrados.</strong></p>
                            <div class="alert alert-warning">
                                <strong>Cambios registrados:</strong> ${cambiosPestana}/${maxCambiosPestana}
                            </div>
                            <div class="alert alert-info">
                                <strong>Cambios restantes:</strong> ${cambiosRestantes}
                            </div>
                            <p class="text-muted">
                                <i class="bi bi-exclamation-triangle"></i>
                                Si realizas ${cambiosRestantes} cambio${cambiosRestantes !== 1 ? 's' : ''} más, 
                                tu evaluación se finalizará automáticamente con puntaje de 0/10.
                            </p>
                        </div>
                    `,
                    confirmButtonText: 'Entendido',
                    timer: 5000,
                    showConfirmButton: true,
                    customClass: {
                        popup: 'swal-wide'
                    }
                });
            }
        }, 2000);
    }
    
    iniciarTimer();
    iniciarGuardadoAutomatico();
    cargarProgresoGuardado();
});

// Función para limpiar todos los intervalos y timers
function limpiarIntervalos() {
    if (verificacionInterval) {
        clearInterval(verificacionInterval);
    }
    if (timerInterval) {
        clearInterval(timerInterval);
    }
    if (guardadoInterval) {
        clearInterval(guardadoInterval);
    }
}

// Función de inicialización
function inicializarEvaluacion() {
    actualizarProgreso();
    actualizarNavegacion();
    actualizarContadorCambiosPestana();
    iniciarVerificacionEstado();
    
    if (window.continuarEvaluacion) {
        Swal.fire({
            icon: 'info',
            title: 'Continuando Evaluación',
            text: 'Se ha detectado una evaluación en progreso. Tu tiempo y respuestas han sido restaurados.',
            timer: 3000,
            showConfirmButton: false
        });
    }
}

// Función para verificar periódicamente si la evaluación fue finalizada administrativamente
function iniciarVerificacionEstado() {
    verificarEstadoEvaluacion();
    
    verificacionInterval = setInterval(function() {
        if (!evaluacionFinalizadaAdmin) {
            verificarEstadoEvaluacion();
        }
    }, 5000);
}

// Verificar estado de la evaluación
function verificarEstadoEvaluacion() {
    fetch(window.verificarEstadoUrl)
        .then(response => response.json())
        .then(data => {
            if (data.finalizada_admin && !evaluacionFinalizadaAdmin && !modalMostrandose) {
                evaluacionFinalizadaAdmin = true;
                modalMostrandose = true;
                
                limpiarIntervalos();
                evaluacionEnviandose = true;
                
                Swal.fire({
                    icon: 'error',
                    title: 'Evaluación Finalizada',
                    html: `
                        <p>Tu evaluación ha sido finalizada administrativamente.</p>
                        <p><strong>Motivo:</strong> ${data.motivo}</p>
                        <p><strong>Administrador:</strong> ${data.admin}</p>
                        <p>Tu puntaje será de 0/10.</p>
                    `,
                    confirmButtonText: 'Entendido',
                    allowOutsideClick: false,
                    allowEscapeKey: false
                }).then(() => {
                    window.location.href = window.quizUrl;
                });
            } else {
                if (data.cambios_pestana_actuales !== undefined && data.cambios_pestana_actuales !== cambiosPestana) {
                    console.log(`DEBUG - Cambios de pestañas actualizados por admin: ${cambiosPestana} → ${data.cambios_pestana_actuales}`);
                    
                    const cambiosAnteriores = cambiosPestana;
                    cambiosPestana = data.cambios_pestana_actuales;
                    
                    actualizarContadorCambiosPestana();
                    
                    Swal.fire({
                        icon: 'info',
                        title: 'Cambios de Pestañas Actualizados',
                        html: `
                            <div class="text-center">
                                <p>Un administrador ha reducido tus cambios de pestaña:</p>
                                <div class="alert alert-info">
                                    <strong>Anterior:</strong> ${cambiosAnteriores}/4<br>
                                    <strong>Nuevo:</strong> ${cambiosPestana}/4
                                </div>
                                <p class="text-success">
                                    <i class="bi bi-check-circle"></i>
                                    Puedes continuar con tu evaluación normalmente.
                                </p>
                            </div>
                        `,
                        timer: 5000,
                        showConfirmButton: true,
                        confirmButtonText: 'Continuar'
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error verificando estado de evaluación:', error);
        });
}

// Activar modo evaluación (ocultar sidebar)
function activarModoEvaluacion() {
    document.body.classList.add('evaluacion-activa');
}

// Desactivar modo evaluación (mostrar sidebar)
function desactivarModoEvaluacion() {
    document.body.classList.remove('evaluacion-activa');
}

// Configurar control de cambios de pestañas
function configurarControlPestanas() {
    document.addEventListener('visibilitychange', function() {
        if (document.hidden && documentoVisible && !evaluacionEnviandose && !evaluacionFinalizadaAdmin) {
            documentoVisible = false;
            cambiosPestana++;
            
            console.log(`DEBUG - Cambio de pestaña detectado. Total: ${cambiosPestana}/${maxCambiosPestana}`);
            
            registrarCambioPestana();
            
            if (cambiosPestana >= maxCambiosPestana) {
                finalizarPorCambiosPestana();
            } else {
                mostrarAdvertenciaCambioPestana();
            }
        } else if (!document.hidden && !documentoVisible) {
            documentoVisible = true;
        }
    });
    
    window.addEventListener('blur', function() {
        if (documentoVisible && !evaluacionEnviandose && !evaluacionFinalizadaAdmin) {
            setTimeout(function() {
                if (!document.hasFocus() && documentoVisible) {
                    documentoVisible = false;
                    cambiosPestana++;
                    
                    console.log(`DEBUG - Cambio de ventana detectado. Total: ${cambiosPestana}/${maxCambiosPestana}`);
                    
                    registrarCambioPestana();
                    
                    if (cambiosPestana >= maxCambiosPestana) {
                        finalizarPorCambiosPestana();
                    } else {
                        mostrarAdvertenciaCambioPestana();
                    }
                }
            }, 100);
        }
    });
    
    window.addEventListener('focus', function() {
        if (!documentoVisible) {
            documentoVisible = true;
        }
    });
}

// Registrar cambio de pestaña en el servidor
function registrarCambioPestana() {
    actualizarContadorCambiosPestana();
    
    fetch(window.registrarCambioPestanaUrl, {
        method: 'POST',
        keepalive: true,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            cambios_pestana: cambiosPestana,
            tiempo_restante: tiempoRestante
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Cambio de pestaña registrado exitosamente');
        } else {
            console.error('Error al registrar cambio de pestaña:', data.error);
        }
    })
    .catch(error => {
        console.error('Error registrando cambio de pestaña:', error);
    });
}

// Actualizar contador visual de cambios de pestaña
function actualizarContadorCambiosPestana() {
    const contador = document.getElementById('tabChangesCounter');
    if (contador) {
        contador.textContent = `${cambiosPestana}/${maxCambiosPestana}`;
        
        if (cambiosPestana === 0) {
            contador.className = 'fw-bold fs-6 text-success';
        } else if (cambiosPestana === 1) {
            contador.className = 'fw-bold fs-6 text-warning';
        } else if (cambiosPestana === 2) {
            contador.className = 'fw-bold fs-6 text-danger';
        } else if (cambiosPestana === 3) {
            contador.className = 'fw-bold fs-6 text-danger';
        } else if (cambiosPestana >= 4) {
            contador.className = 'fw-bold fs-6 text-danger bg-danger text-white px-2 rounded';
        }
    }
}

// Mostrar advertencia de cambio de pestaña
function mostrarAdvertenciaCambioPestana() {
    const cambiosRestantes = maxCambiosPestana - cambiosPestana;
    
    if (!advertenciasMostradas) {
        advertenciasMostradas = true;
        
        Swal.fire({
            icon: 'warning',
            title: 'Advertencia de Cambio de Pestaña',
            html: `
                <div class="text-center">
                    <p><strong>Has cambiado de pestaña o ventana durante la evaluación.</strong></p>
                    <div class="alert alert-warning">
                        <strong>Cambios realizados:</strong> ${cambiosPestana}/${maxCambiosPestana}
                    </div>
                    <div class="alert alert-info">
                        <strong>Cambios restantes:</strong> ${cambiosRestantes}
                    </div>
                    <p class="text-muted">
                        <i class="bi bi-exclamation-triangle"></i>
                        Si realizas ${cambiosRestantes} cambio${cambiosRestantes !== 1 ? 's' : ''} más, 
                        tu evaluación se finalizará automáticamente con puntaje de 0/10.
                    </p>
                </div>
            `,
            confirmButtonText: 'Entendido',
            allowOutsideClick: false,
            allowEscapeKey: false,
            customClass: {
                popup: 'swal-wide'
            }
        }).then(() => {
            advertenciasMostradas = false;
        });
    }
}

// Finalizar evaluación por exceso de cambios de pestaña
function finalizarPorCambiosPestana() {
    limpiarIntervalos();
    
    evaluacionEnviandose = true;
    evaluacionFinalizadaAdmin = true;
    modalMostrandose = true;
    
    enviarEvaluacionPorCambiosPestana();
}

// Enviar evaluación por cambios de pestaña
function enviarEvaluacionPorCambiosPestana() {
    Swal.fire({
        icon: 'error',
        title: 'Evaluación Finalizada Automáticamente',
        html: `
            <div class="text-center">
                <p><strong>Has excedido el límite de cambios de pestaña permitidos.</strong></p>
                <div class="alert alert-danger">
                    <strong>Cambios realizados:</strong> ${cambiosPestana}/${maxCambiosPestana}
                </div>
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i>
                    <strong>Tu puntaje será de 0/10</strong>
                </div>
                <p class="text-muted">
                    La evaluación se enviará automáticamente.
                </p>
            </div>
        `,
        confirmButtonText: 'Entendido',
        allowOutsideClick: false,
        allowEscapeKey: false,
        customClass: {
            popup: 'swal-wide'
        }
    }).then(() => {
        desactivarModoEvaluacion();
        
        const form = document.getElementById('quizForm');
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'finalizada_por_cambios_pestana';
        input.value = 'true';
        form.appendChild(input);
        
        form.submit();
    });
}

// Configurar eventos
function configurarEventos() {
    document.querySelectorAll('input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', function() {
            actualizarProgreso();
            guardarRespuestaAutomatica();
        });
    });
    
    document.querySelectorAll('.question-nav-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const questionNum = this.getAttribute('data-question');
            mostrarPregunta(questionNum);
        });
    });
    
    window.addEventListener('beforeunload', function(e) {
        if (tiempoRestante > 0 && !evaluacionEnviandose && !evaluacionFinalizadaAdmin && !modalMostrandose) {
            guardarRespuestaAutomatica();
            e.preventDefault();
            e.returnValue = '';
        }
    });
    
    window.addEventListener('unload', function() {
        desactivarModoEvaluacion();
    });
}

// Función para iniciar timer
function iniciarTimer() {
    timerInterval = setInterval(function() {
        tiempoRestante--;
        
        if (tiempoRestante <= 0) {
            clearInterval(timerInterval);
            tiempoRestante = 0;
            enviarEvaluacionAutomaticamente();
        }
        
        actualizarTimer();
    }, 1000);
    
    actualizarTimer();
}

// Actualizar display del timer
function actualizarTimer() {
    const minutos = Math.floor(tiempoRestante / 60);
    const segundos = tiempoRestante % 60;
    const tiempoFormateado = `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
    
    document.getElementById('timer').textContent = tiempoFormateado;
    document.getElementById('tiempo_restante').value = tiempoRestante;
    
    const tiempoTotal = window.tiempoTotal || 3600;
    const porcentaje = tiempoTotal > 0 ? (tiempoRestante / tiempoTotal) * 100 : 0;
    const progressBar = document.getElementById('progressBar');
    
    progressBar.style.width = porcentaje + '%';
    
    if (tiempoRestante <= 300) {
        progressBar.className = 'progress-bar bg-danger';
    } else if (tiempoRestante <= 600) {
        progressBar.className = 'progress-bar bg-warning';
    } else {
        progressBar.className = 'progress-bar bg-success';
    }
}

// Función para cargar progreso guardado automáticamente
function cargarProgresoGuardado() {
    if (window.continuarEvaluacion && window.resultadoExiste && window.respuestasGuardadas) {
        const respuestasGuardadas = window.respuestasGuardadas;
        console.log('DEBUG - Cargando respuestas guardadas:', respuestasGuardadas);
        
        Object.keys(respuestasGuardadas).forEach(preguntaKey => {
            const opcionId = respuestasGuardadas[preguntaKey];
            if (opcionId) {
                const radio = document.getElementById(`opcion_${opcionId}`);
                if (radio) {
                    radio.checked = true;
                    console.log(`DEBUG - Respuesta cargada: ${preguntaKey} = ${opcionId}`);
                } else {
                    console.log(`DEBUG - No se encontró radio para opción: ${opcionId}`);
                }
            }
        });
        
        setTimeout(() => {
            actualizarProgreso();
            actualizarNavegacion();
        }, 100);
    } else {
        console.log('DEBUG - No se puede continuar evaluación o no hay respuestas guardadas');
    }
}

// Función para guardado automático
function iniciarGuardadoAutomatico() {
    guardadoInterval = setInterval(function() {
        guardarRespuestaAutomatica();
    }, 30000);
}

// Guardar respuestas automáticamente
function guardarRespuestaAutomatica() {
    const respuestas = {};
    document.querySelectorAll('input[type="radio"]:checked').forEach(radio => {
        respuestas[radio.name] = radio.value;
    });
    
    console.log('DEBUG - Guardando respuestas automáticamente:', respuestas);
    console.log('DEBUG - Tiempo restante:', tiempoRestante);
    
    fetch(window.guardarRespuestaAutomaticaUrl, {
        method: 'POST',
        keepalive: true,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            respuestas: respuestas,
            tiempo_restante: tiempoRestante
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Progreso guardado automáticamente exitosamente');
        } else {
            console.error('Error al guardar automáticamente:', data.error);
            if (data.redirect && !evaluacionFinalizadaAdmin && !modalMostrandose) {
                evaluacionFinalizadaAdmin = true;
                modalMostrandose = true;
                
                limpiarIntervalos();
                evaluacionEnviandose = true;
                
                Swal.fire({
                    icon: 'error',
                    title: 'Evaluación Finalizada',
                    text: 'Tu evaluación ha sido finalizada administrativamente. Tu puntaje será de 0/10.',
                    confirmButtonText: 'Entendido',
                    allowOutsideClick: false,
                    allowEscapeKey: false
                }).then(() => {
                    window.location.href = window.quizUrl;
                });
            }
        }
    })
    .catch(error => {
        console.error('Error guardando progreso:', error);
    });
}

// Actualizar progreso
function actualizarProgreso() {
    const totalPreguntas = window.totalPreguntas;
    const respuestas = document.querySelectorAll('input[type="radio"]:checked');
    const respondidas = respuestas.length;
    const sinResponder = totalPreguntas - respondidas;
    
    document.getElementById('progressText').textContent = `${respondidas}/${totalPreguntas}`;
    document.getElementById('answeredCount').textContent = respondidas;
    document.getElementById('unansweredCount').textContent = sinResponder;
    
    const porcentaje = totalPreguntas > 0 ? (respondidas / totalPreguntas) * 100 : 0;
    document.getElementById('questionProgress').style.width = porcentaje + '%';
    
    actualizarNavegacion();
}

// Actualizar navegación
function actualizarNavegacion() {
    document.querySelectorAll('.question-nav-btn').forEach(btn => {
        const questionNum = btn.getAttribute('data-question');
        const pregunta = document.getElementById(`question-${questionNum}`);
        if (pregunta) {
            const respuestas = pregunta.querySelectorAll('input[type="radio"]:checked');
            if (respuestas.length > 0) {
                btn.className = 'btn btn-success btn-sm w-100 question-nav-btn';
            } else {
                btn.className = 'btn btn-outline-secondary btn-sm w-100 question-nav-btn';
            }
        }
    });
}

// Mostrar pregunta específica
function mostrarPregunta(numero) {
    document.querySelectorAll('.question-container').forEach(container => {
        container.style.display = 'none';
    });
    
    const pregunta = document.getElementById(`question-${numero}`);
    if (pregunta) {
        pregunta.style.display = 'block';
        pregunta.scrollIntoView({ behavior: 'smooth' });
    }
}

// Confirmar envío
function confirmarEnvio() {
    const totalPreguntas = window.totalPreguntas;
    const respuestas = document.querySelectorAll('input[type="radio"]:checked');
    const respondidas = respuestas.length;
    const sinResponder = totalPreguntas - respondidas;
    
    const minutos = Math.floor(tiempoRestante / 60);
    const segundos = tiempoRestante % 60;
    const tiempoFormateado = `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
    
    document.getElementById('modalAnsweredCount').textContent = respondidas;
    document.getElementById('modalUnansweredCount').textContent = sinResponder;
    document.getElementById('modalTimeRemaining').textContent = tiempoFormateado;
    
    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();
}

// Enviar evaluación
function enviarEvaluacion() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
    if (modal) {
        modal.hide();
    }
    
    evaluacionEnviandose = true;
    desactivarModoEvaluacion();
    document.getElementById('quizForm').submit();
}

// Envío automático cuando se acaba el tiempo
function enviarEvaluacionAutomaticamente() {
    Swal.fire({
        icon: 'warning',
        title: '¡Tiempo Agotado!',
        text: 'Se ha agotado el tiempo de la evaluación. Se enviará automáticamente.',
        showConfirmButton: false,
        timer: 2000
    }).then(() => {
        evaluacionEnviandose = true;
        desactivarModoEvaluacion();
        document.getElementById('quizForm').submit();
    });
}

// Función para obtener CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
