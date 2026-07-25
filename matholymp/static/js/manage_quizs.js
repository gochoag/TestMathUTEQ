// Variables globales para el modal de participantes
let currentEvaluacionId = null;
let currentEtapa = null;

// Función para obtener el CSRF token
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

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    const createQuizModal = document.getElementById('createQuizModal');
    if (createQuizModal) {
        createQuizModal.addEventListener('show.bs.modal', function() {
            const today = new Date().toISOString().split('T')[0];
            const startDate = document.getElementById('start_date');
            const endDate = document.getElementById('end_date');
            const startTime = document.getElementById('start_time');
            const endTime = document.getElementById('end_time');
            const duration = document.getElementById('duration');
            const preguntas = document.getElementById('preguntas_a_mostrar');

            if (startDate) startDate.value = today;
            if (endDate) endDate.value = today;
            if (startTime) startTime.value = '';
            if (endTime) endTime.value = '';
            if (duration) duration.value = '60';
            if (preguntas) preguntas.value = '10';
        });
    }
});

// Función para crear evaluación
async function createQuiz() {
    const titleEl = document.getElementById('quizTitle');
    const etapaEl = document.getElementById('etapa');
    const durationEl = document.getElementById('duration');
    const preguntasEl = document.getElementById('preguntas_a_mostrar');
    const startDateEl = document.getElementById('start_date');
    const startTimeEl = document.getElementById('start_time');
    const endDateEl = document.getElementById('end_date');
    const endTimeEl = document.getElementById('end_time');
    const descriptionEl = document.getElementById('quizDescription');

    const title = titleEl ? titleEl.value.trim() : '';
    const etapa = etapaEl ? etapaEl.value : '';
    const durationVal = durationEl ? durationEl.value : '';
    const duration = parseInt(durationVal, 10);
    const preguntas_a_mostrar = preguntasEl ? preguntasEl.value : '10';
    const startDate = startDateEl ? startDateEl.value : '';
    const startTime = startTimeEl ? startTimeEl.value : '';
    const endDate = endDateEl ? endDateEl.value : '';
    const endTime = endTimeEl ? endTimeEl.value : '';
    const description = descriptionEl ? descriptionEl.value.trim() : '';

    // Validación de campos requeridos
    if (!title || !etapa || !duration || !startDate || !startTime || !endDate || !endTime) {
        Swal.fire({
            icon: 'error',
            title: 'Campos requeridos',
            text: 'Por favor, completa todos los campos obligatorios.',
            customClass: { container: 'swal-over-modal' }
        });
        return;
    }

    // Validar duración
    if (isNaN(duration) || duration < 1 || duration > 480) {
        Swal.fire({
            icon: 'error',
            title: 'Duración inválida',
            text: 'La duración debe estar entre 1 y 480 minutos.',
            customClass: { container: 'swal-over-modal' }
        });
        return;
    }

    // Validar fechas
    const startDateTime = new Date(`${startDate}T${startTime}`);
    const endDateTime = new Date(`${endDate}T${endTime}`);

    if (startDateTime >= endDateTime) {
        Swal.fire({
            icon: 'error',
            title: 'Fechas inválidas',
            text: 'La fecha de inicio debe ser anterior a la fecha de finalización.',
            customClass: { container: 'swal-over-modal' }
        });
        return;
    }

    Swal.fire({
        title: 'Creando evaluación...',
        text: 'Por favor espera',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); },
        customClass: { container: 'swal-over-modal' }
    });

    try {
        const response = await fetch(window.createEvaluacionUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                title,
                etapa,
                duration,
                preguntas_a_mostrar,
                start_date: startDate,
                start_time: startTime,
                end_date: endDate,
                end_time: endTime,
                description
            })
        });

        const data = await response.json();

        if (data.success) {
            const modalEl = document.getElementById('createQuizModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                modal.hide();
            }

            await Swal.fire({
                icon: 'success',
                title: '¡Creada exitosamente!',
                text: 'La evaluación ha sido creada correctamente',
                timer: 1500,
                showConfirmButton: false,
                customClass: { container: 'swal-over-modal' }
            });

            window.location.reload();
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.error || 'Error al crear la evaluación',
                customClass: { container: 'swal-over-modal' }
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error de conexión al crear la evaluación',
            customClass: { container: 'swal-over-modal' }
        });
    }
}

// Función para gestionar participantes
async function gestionarParticipantes(evaluacionId, evaluacionTitle, etapa) {
    currentEvaluacionId = evaluacionId;
    currentEtapa = etapa;

    const titleEl = document.getElementById('evaluacionTitle');
    if (titleEl) {
        titleEl.textContent = evaluacionTitle;
    }

    const modalEl = document.getElementById('gestionarParticipantesModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
    }

    await cargarDatosParticipantes(evaluacionId, etapa);
}

// Función para cargar datos de participantes
async function cargarDatosParticipantes(evaluacionId, etapa) {
    try {
        const response = await fetch(window.participantesUrl.replace('/0/', `/${evaluacionId}/`), {
            method: 'GET',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!response.ok) {
            throw new Error('Error al cargar datos');
        }

        const data = await response.json();

        if (data.success) {
            renderizarGrupos(data.grupos, data.grupos_asignados, etapa);
            renderizarParticipantesIndividuales(data.participantes_individuales, data.participantes_asignados, etapa);
            configurarBusqueda();
            configurarPermisosUI(etapa);
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.error || 'Error al cargar los datos',
                customClass: { container: 'swal-over-modal' }
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error de conexión al cargar los datos',
            customClass: { container: 'swal-over-modal' }
        });
    }
}

// Configura permisos de botones según etapa y nivel de acceso
function configurarPermisosUI(etapa) {
    const isSuperUser = window.isSuperUser;
    const bloqueado = etapa !== 1 && !isSuperUser;
    const msgTooltip = 'Solo los superusuarios y administradores con acceso total pueden modificar participantes en etapas avanzadas';

    const btnGuardar = document.getElementById('btnGuardarParticipantes');
    if (btnGuardar) {
        if (bloqueado) {
            btnGuardar.disabled = true;
            btnGuardar.innerHTML = '<i class="bi bi-lock me-1"></i> Solo Superusuarios';
            btnGuardar.className = 'btn btn-secondary';
            btnGuardar.title = msgTooltip;
        } else {
            btnGuardar.disabled = false;
            btnGuardar.innerHTML = '<i class="bi bi-check-circle me-1"></i> Guardar Cambios';
            btnGuardar.className = 'btn btn-primary';
            btnGuardar.title = '';
        }
    }

    const btnSeleccionar = document.getElementById('btnSeleccionarTodosIndividuales');
    const btnDeseleccionar = document.getElementById('btnDeseleccionarTodosIndividuales');

    [btnSeleccionar, btnDeseleccionar].forEach(btn => {
        if (!btn) return;
        if (bloqueado) {
            btn.disabled = true;
            btn.className = 'btn btn-sm btn-outline-secondary disabled';
            btn.title = msgTooltip;
        } else {
            btn.disabled = false;
            btn.className = btn === btnSeleccionar ? 'btn btn-sm btn-outline-primary' : 'btn btn-sm btn-outline-secondary';
            btn.title = '';
        }
    });
}

// Función para renderizar grupos
function renderizarGrupos(grupos, gruposAsignados, etapa) {
    const gruposList = document.getElementById('gruposList');
    if (!gruposList) return;
    gruposList.innerHTML = '';

    if (etapa === 1) {
        grupos.forEach(grupo => {
            const isSelected = gruposAsignados.some(g => g.id === grupo.id);
            const div = document.createElement('div');
            div.className = 'form-check mb-2';
            div.innerHTML = `
                <input class="form-check-input" type="checkbox" value="${grupo.id}"
                       id="grupo_${grupo.id}" ${isSelected ? 'checked' : ''}>
                <label class="form-check-label" for="grupo_${grupo.id}">
                    <strong>${grupo.name}</strong>
                    <small class="text-muted">(${grupo.participantes_count} participantes)</small>
                </label>
            `;
            gruposList.appendChild(div);
        });
    } else {
        if (gruposAsignados.length > 0) {
            gruposAsignados.forEach(grupo => {
                const div = document.createElement('div');
                div.className = 'alert alert-info mb-2';
                div.innerHTML = `
                    <i class="bi bi-info-circle me-2"></i>
                    <strong>${grupo.name}</strong> - ${grupo.participantes_count} participantes
                `;
                gruposList.appendChild(div);
            });
        } else {
            const div = document.createElement('div');
            div.className = 'alert alert-warning mb-2';
            div.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i> No hay grupos asignados para esta evaluación';
            gruposList.appendChild(div);
        }
    }
}

// Función para renderizar participantes individuales
function renderizarParticipantesIndividuales(participantes, participantesAsignados, etapa) {
    const individualesList = document.getElementById('individualesList');
    if (!individualesList) return;
    individualesList.innerHTML = '';
    const isSuperUser = window.isSuperUser;

    if (etapa === 1) {
        participantes.forEach(participante => {
            const isSelected = participantesAsignados.some(p => p.id === participante.id);
            const div = document.createElement('div');
            div.className = 'form-check mb-2';
            div.innerHTML = `
                <input class="form-check-input" type="checkbox" value="${participante.id}"
                       id="participante_${participante.id}" ${isSelected ? 'checked' : ''}>
                <label class="form-check-label" for="participante_${participante.id}">
                    <strong>${participante.NombresCompletos}</strong>
                    <small class="text-muted">(${participante.cedula})</small>
                </label>
            `;
            individualesList.appendChild(div);
        });
    } else {
        if (participantes.length > 0) {
            participantes.forEach(participante => {
                const participanteAsignado = participantesAsignados.find(p => p.id === participante.id);
                const isSelected = !!participanteAsignado;
                const esAutomatico = participanteAsignado && participanteAsignado.automatico;
                const badgeAutomatico = esAutomatico
                    ? '<span class="badge bg-success ms-2">Preseleccionado</span>'
                    : '<span class="badge bg-primary ms-2">Manual</span>';

                const div = document.createElement('div');

                if (isSuperUser) {
                    div.className = 'form-check mb-2';
                    div.innerHTML = `
                        <input class="form-check-input" type="checkbox" value="${participante.id}"
                               id="participante_${participante.id}" ${isSelected ? 'checked' : ''}>
                        <label class="form-check-label" for="participante_${participante.id}">
                            <strong>${participante.NombresCompletos}</strong>
                            <small class="text-muted">(${participante.cedula})</small>
                            ${badgeAutomatico}
                        </label>
                    `;
                } else if (isSelected) {
                    div.className = 'alert alert-success mb-2';
                    div.innerHTML = `
                        <i class="bi bi-person-check me-2"></i>
                        <strong>${participante.NombresCompletos}</strong> - ${participante.cedula}
                        ${badgeAutomatico}
                    `;
                }

                if (div.innerHTML.trim()) {
                    individualesList.appendChild(div);
                }
            });

            const tienePreseleccionados = participantesAsignados.some(p => p.automatico);
            if (tienePreseleccionados && !isSuperUser) {
                const infoDiv = document.createElement('div');
                infoDiv.className = 'alert alert-info mb-2';
                infoDiv.innerHTML = `
                    <i class="bi bi-info-circle me-2"></i>
                    <strong>Información:</strong> Los participantes marcados como "Preseleccionado" fueron
                    seleccionados automáticamente basándose en el ranking de la etapa anterior.
                `;
                individualesList.appendChild(infoDiv);
            }
        } else {
            const div = document.createElement('div');
            div.className = 'alert alert-warning mb-2';
            div.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i> No hay participantes preseleccionados para esta evaluación';
            individualesList.appendChild(div);
        }
    }
}

// Configura los filtros de búsqueda en tiempo real
function configurarBusqueda() {
    const buscarGrupos = document.getElementById('buscarGrupos');
    if (buscarGrupos) {
        buscarGrupos.value = '';
        buscarGrupos.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            document.querySelectorAll('#gruposList .form-check').forEach(item => {
                const label = item.querySelector('label');
                const texto = label ? label.textContent.toLowerCase() : '';
                item.style.display = texto.includes(searchTerm) ? 'block' : 'none';
            });
        });
    }

    const buscarIndividuales = document.getElementById('buscarIndividuales');
    if (buscarIndividuales) {
        buscarIndividuales.value = '';
        buscarIndividuales.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            document.querySelectorAll('#individualesList .form-check, #individualesList .alert').forEach(item => {
                const label = item.querySelector('label');
                const texto = item.classList.contains('form-check')
                    ? (label ? label.textContent.toLowerCase() : '')
                    : item.textContent.toLowerCase();
                item.style.display = texto.includes(searchTerm) ? 'block' : 'none';
            });
        });
    }
}

// Seleccionar/deseleccionar grupos visibles
function seleccionarTodosGrupos() {
    document.querySelectorAll('#gruposList .form-check-input:not([style*="display: none"])').forEach(cb => cb.checked = true);
}

// Deseleccionar grupos visibles
function deseleccionarTodosGrupos() {
    document.querySelectorAll('#gruposList .form-check-input:not([style*="display: none"])').forEach(cb => cb.checked = false);
}

// Seleccionar participantes individuales visibles
function seleccionarTodosIndividuales() {
    document.querySelectorAll('#individualesList .form-check-input:not([style*="display: none"])').forEach(cb => cb.checked = true);
}

// Deseleccionar participantes individuales visibles
function deseleccionarTodosIndividuales() {
    document.querySelectorAll('#individualesList .form-check-input:not([style*="display: none"])').forEach(cb => cb.checked = false);
}

// Función para guardar participantes
async function guardarParticipantes() {
    if (currentEtapa !== 1 && !window.isSuperUser) {
        Swal.fire({
            icon: 'warning',
            title: 'Acceso Restringido',
            text: 'Solo los superusuarios y administradores con acceso total pueden modificar participantes en etapas avanzadas.',
            customClass: { container: 'swal-over-modal' }
        });
        return;
    }

    const gruposSeleccionados = currentEtapa === 1
        ? Array.from(document.querySelectorAll('#gruposList .form-check-input:checked')).map(cb => cb.value)
        : [];

    const participantesSeleccionados = Array.from(
        document.querySelectorAll('#individualesList .form-check-input:checked')
    ).map(cb => cb.value);

    Swal.fire({
        title: 'Guardando cambios...',
        text: 'Por favor espera',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); },
        customClass: { container: 'swal-over-modal' }
    });

    try {
        const response = await fetch(window.participantesUrl.replace('/0/', `/${currentEvaluacionId}/`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                grupos: gruposSeleccionados,
                participantes_individuales: participantesSeleccionados
            })
        });

        const data = await response.json();

        if (data.success) {
            await Swal.fire({
                icon: 'success',
                title: '¡Guardado exitosamente!',
                text: 'Los participantes han sido asignados correctamente',
                timer: 1500,
                showConfirmButton: false,
                customClass: { container: 'swal-over-modal' }
            });

            const modalEl = document.getElementById('gestionarParticipantesModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                modal.hide();
            }
            window.location.reload();
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.error || 'Error al guardar los cambios',
                customClass: { container: 'swal-over-modal' }
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error de conexión al guardar los cambios',
            customClass: { container: 'swal-over-modal' }
        });
    }
}

// Función para eliminar evaluación
function deleteEvaluacion(evaluacionId, evaluacionTitle) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: `¿Realmente quieres eliminar la evaluación "${evaluacionTitle}"? Esta acción no se puede deshacer.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        customClass: { container: 'swal-over-modal' }
    }).then(async (result) => {
        if (!result.isConfirmed) return;

        Swal.fire({
            title: 'Eliminando...',
            text: 'Por favor espera',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading(); },
            customClass: { container: 'swal-over-modal' }
        });

        try {
            const response = await fetch(window.deleteEvaluacionUrl.replace('/0/', `/${evaluacionId}/`), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            const data = await response.json();

            if (data.success) {
                await Swal.fire({
                    icon: 'success',
                    title: '¡Eliminada!',
                    text: 'La evaluación ha sido eliminada exitosamente',
                    timer: 1500,
                    showConfirmButton: false,
                    customClass: { container: 'swal-over-modal' }
                });
                window.location.reload();
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.error || 'Error al eliminar la evaluación',
                    customClass: { container: 'swal-over-modal' }
                });
            }
        } catch (error) {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Error de conexión al eliminar la evaluación',
                customClass: { container: 'swal-over-modal' }
            });
        }
    });
}
