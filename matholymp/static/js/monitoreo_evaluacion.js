// Estado global del monitoreo
let autoRefreshInterval;
let currentMonitoreoId = null;
let lastMonitoreoData = {};
let searchTimeout;
let totalParticipantes = 0;

// Función para formatear tiempo en segundos
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) return `${hours}h ${minutes}m ${secs}s`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
}

// Función para obtener el color de badge según el estado
function getEstadoColor(estaActivo, estado, haIniciado, intentosDisponibles) {
    if (estado === 'finalizado' && intentosDisponibles === 0) return 'secondary';
    if (estado === 'suspendido') return 'danger';
    if (estado === 'activo') return 'success';
    if (estado === 'inactivo' && intentosDisponibles > 0) return 'warning';
    if (estado === 'finalizado' && intentosDisponibles > 0) return 'warning';
    if (!haIniciado || estado === 'pendiente') return 'info';
    return 'secondary';
}

// Función para obtener el texto del estado
function getEstadoText(estaActivo, estado, haIniciado, intentosDisponibles) {
    if (estado === 'activo') return 'Rindiendo';
    if (estado === 'inactivo' && intentosDisponibles > 0) return 'Puede reiniciar';
    if (estado === 'finalizado' && intentosDisponibles === 0) return 'Finalizado';
    if (estado === 'finalizado' && intentosDisponibles > 0) return 'Puede reiniciar';
    if (estado === 'suspendido') return 'Suspendido';
    if (!haIniciado || estado === 'pendiente') return 'Pendiente';
    return 'Estado desconocido';
}

// Genera el HTML interno de una fila de la tabla de monitoreo
function generarFilaMonitoreo(monitoreo) {
    // Columna Progreso/Puntaje
    let progresoPuntajeContent = '';

    if (monitoreo.estado === 'finalizado' && monitoreo.intentos_disponibles === 0) {
        if (monitoreo.tiene_resultado_completado) {
            const puntajeColor = monitoreo.puntaje >= 7 ? 'success' : monitoreo.puntaje >= 5 ? 'warning' : 'danger';
            progresoPuntajeContent = `
                <div class="text-center">
                    <strong class="text-${puntajeColor}">${monitoreo.puntaje_numerico || 0}</strong><br>
                    <small class="text-muted">${monitoreo.puntaje || 0}%</small>
                </div>`;
        } else {
            progresoPuntajeContent = `
                <div class="text-center">
                    <span class="badge bg-secondary"><i class="bi bi-check-circle"></i> Completado</span>
                </div>`;
        }
    } else if ((monitoreo.estado === 'finalizado' || monitoreo.estado === 'inactivo') && monitoreo.intentos_disponibles > 0) {
        progresoPuntajeContent = `
            <div class="text-center">
                <span class="badge bg-warning"><i class="bi bi-arrow-clockwise"></i> Puede reiniciar</span>
            </div>`;
    } else if (!monitoreo.ha_iniciado || monitoreo.estado === 'pendiente') {
        progresoPuntajeContent = `
            <div class="text-center">
                <span class="badge bg-info"><i class="bi bi-clock"></i> Sin iniciar</span>
            </div>`;
    } else {
        const porcentaje = monitoreo.porcentaje_avance || 0;
        progresoPuntajeContent = `
            <div class="progress" style="height: 20px;">
                <div class="progress-bar ${porcentaje > 0 ? 'bg-primary' : 'bg-light'}" role="progressbar"
                     style="width: ${porcentaje}%"
                     aria-valuenow="${porcentaje}" aria-valuemin="0" aria-valuemax="100">
                    ${porcentaje}%
                </div>
            </div>
            <small class="text-muted">
                ${monitoreo.preguntas_respondidas || 0} respondidas / ${monitoreo.preguntas_revisadas || 0} revisadas
            </small>`;
    }

    // Columna Última Actividad
    let ultimaActividadContent;
    if (!monitoreo.ha_iniciado || monitoreo.estado === 'pendiente') {
        ultimaActividadContent = '<span class="text-muted"><i class="bi bi-dash-circle"></i> Sin iniciar</span>';
    } else if (monitoreo.ultima_actividad) {
        const fechaActividad = new Date(monitoreo.ultima_actividad);
        const diferencia = Math.floor((new Date() - fechaActividad) / 60000);
        const colorActividad = diferencia > 10 ? 'danger' : diferencia > 5 ? 'warning' : 'success';
        ultimaActividadContent = `<span class="text-${colorActividad}">
            <i class="bi bi-clock"></i> ${fechaActividad.toLocaleTimeString()}
            ${diferencia > 0 ? `<br><small class="text-muted">Hace ${diferencia} min</small>` : ''}
        </span>`;
    } else {
        ultimaActividadContent = '<span class="text-warning"><i class="bi bi-exclamation-triangle"></i> Sin registro</span>';
    }

    // Columna Intentos
    const intentosUsados = monitoreo.intentos_usados || 0;
    const intentosDisponibles = monitoreo.intentos_disponibles || 0;
    const intentosTotales = intentosUsados + intentosDisponibles;
    const intentosBadge = `<span class="badge ${intentosDisponibles > 0 ? 'bg-success' : 'bg-danger'}" title="Disponibles/Total">
        ${intentosDisponibles}/${intentosTotales}
    </span>`;

    // Columna Cambios Pestañas
    const cambiosActuales = monitoreo.cambios_pestana_actuales || 0;
    const cambiosMaximo = monitoreo.cambios_pestana_maximo || 4;
    let cambiosBadgeColor = 'bg-success';
    if (cambiosActuales >= cambiosMaximo) cambiosBadgeColor = 'bg-danger';
    else if (cambiosActuales > cambiosMaximo / 2) cambiosBadgeColor = 'bg-warning text-dark';
    const cambiosBadge = `<span class="badge ${cambiosBadgeColor}" title="Cambios/Máximo">${cambiosActuales}/${cambiosMaximo}</span>`;

    // Columna Acciones
    let accionesContent;
    if (monitoreo.intentos_disponibles > 0) {
        if (monitoreo.estado === 'pendiente' || !monitoreo.ha_iniciado) {
            accionesContent = `<button type="button" class="btn btn-outline-info" disabled title="Esperando que inicie">
                <i class="bi bi-hourglass-split"></i> Esperando
            </button>`;
        } else if (monitoreo.estado === 'activo') {
            accionesContent = `
                <button type="button" class="btn btn-outline-warning"
                        onclick="agregarAlerta(${monitoreo.id})" title="Agregar alerta">
                    <i class="bi bi-exclamation-triangle"></i>
                </button>
                <button type="button" class="btn btn-outline-danger"
                        onclick="reducirCambiosPestana(${monitoreo.participante_id}, '${monitoreo.participante_nombre}', ${cambiosActuales}, ${cambiosMaximo})"
                        title="Reducir cambios de pestañas">
                    <i class="bi bi-dash-circle"></i>
                </button>
                <button type="button" class="btn btn-outline-danger"
                        onclick="finalizarEvaluacion(${monitoreo.id}, '${monitoreo.participante_nombre}')"
                        title="Finalizar evaluación">
                    <i class="bi bi-stop-circle"></i>
                </button>`;
        } else {
            accionesContent = `<button type="button" class="btn btn-outline-success" disabled title="Puede reiniciar cuando quiera">
                <i class="bi bi-play-circle"></i> Disponible
            </button>`;
        }
    } else {
        accionesContent = `<button type="button" class="btn btn-outline-success"
                onclick="darNuevoIntento(${monitoreo.participante_id}, '${monitoreo.participante_nombre}', ${intentosUsados}, ${intentosTotales})"
                title="Dar nuevo intento">
            <i class="bi bi-arrow-clockwise"></i>
        </button>`;
    }

    return `
        <td>
            <strong>${monitoreo.participante_nombre}</strong><br>
            <small class="text-muted">${monitoreo.participante_cedula}</small>
        </td>
        <td>
            <span class="badge bg-${getEstadoColor(monitoreo.esta_activo, monitoreo.estado, monitoreo.ha_iniciado, monitoreo.intentos_disponibles)}">
                ${getEstadoText(monitoreo.esta_activo, monitoreo.estado, monitoreo.ha_iniciado, monitoreo.intentos_disponibles)}
            </span>
        </td>
        <td>${progresoPuntajeContent}</td>
        <td>${ultimaActividadContent}</td>
        <td>${intentosBadge}</td>
        <td>${cambiosBadge}</td>
        <td>
            ${monitoreo.alertas_count > 0
                ? `<span class="badge bg-danger">${monitoreo.alertas_count}</span>`
                : '<span class="badge bg-success">0</span>'
            }
        </td>
        <td>
            <div class="btn-group btn-group-sm" role="group">
                <button type="button" class="btn btn-outline-info"
                        onclick="verDetalles(${monitoreo.id})" title="Ver detalles">
                    <i class="bi bi-eye"></i>
                </button>
                ${accionesContent}
            </div>
        </td>
    `;
}

// Notifica al admin cuando detecta cambios importantes entre actualizaciones
function notificarCambioEstado(monitoreo, estadoAnterior) {
    if (!estadoAnterior) return;
    const nombre = monitoreo.participante_nombre;

    if (estadoAnterior.estado === 'pendiente' && monitoreo.ha_iniciado) {
        showDynamicToast({ type: 'info', title: 'Participante iniciado', message: `${nombre} ha comenzado la evaluación` });
    } else if ((estadoAnterior.estado === 'finalizado' || estadoAnterior.estado === 'inactivo') && monitoreo.estado === 'activo') {
        showDynamicToast({ type: 'info', title: 'Nuevo intento iniciado', message: `${nombre} ha iniciado un nuevo intento de evaluación` });
    } else if (monitoreo.alertas_count > (estadoAnterior.alertas_count || 0)) {
        showDynamicToast({ type: 'warning', title: 'Nueva alerta', message: `Se agregó una alerta para ${nombre}` });
    } else if (estadoAnterior.esta_activo && !monitoreo.esta_activo && monitoreo.estado !== 'finalizado') {
        showDynamicToast({ type: 'warning', title: 'Participante inactivo', message: `${nombre} lleva más de 1 hora sin actividad` });
    }
}

// Detecta si un registro de monitoreo cambió respecto al cache anterior
function hasMonitoreoChanged(current, previous) {
    if (!previous) return true;
    return (
        current.estado !== previous.estado ||
        current.ha_iniciado !== previous.ha_iniciado ||
        current.esta_activo !== previous.esta_activo ||
        current.porcentaje_avance !== previous.porcentaje_avance ||
        current.preguntas_respondidas !== previous.preguntas_respondidas ||
        current.alertas_count !== previous.alertas_count ||
        current.ultima_actividad !== previous.ultima_actividad ||
        current.intentos_usados !== previous.intentos_usados ||
        current.intentos_disponibles !== previous.intentos_disponibles ||
        current.cambios_pestana_actuales !== previous.cambios_pestana_actuales
    );
}

// Carga y actualiza la tabla de monitoreo desde el backend
function cargarMonitoreo() {
    fetch(window.monitoreoEstadoUrl)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            if (!data.monitoreos || !Array.isArray(data.monitoreos)) {
                throw new Error('Datos de monitoreo inválidos');
            }

            const tbody = document.getElementById('tbody-monitoreo');
            const isFirstLoad = Object.keys(lastMonitoreoData).length === 0;

            if (isFirstLoad) {
                tbody.innerHTML = '';
                data.monitoreos.forEach(monitoreo => {
                    const row = document.createElement('tr');
                    row.id = `monitoreo-row-${monitoreo.id}`;
                    row.innerHTML = generarFilaMonitoreo(monitoreo);
                    tbody.appendChild(row);
                    lastMonitoreoData[monitoreo.id] = { ...monitoreo };
                });
            } else {
                data.monitoreos.forEach(monitoreo => {
                    const rowId = `monitoreo-row-${monitoreo.id}`;
                    const existingRow = document.getElementById(rowId);
                    const hasChanged = hasMonitoreoChanged(monitoreo, lastMonitoreoData[monitoreo.id]);

                    if (hasChanged) {
                        if (lastMonitoreoData[monitoreo.id]) {
                            notificarCambioEstado(monitoreo, lastMonitoreoData[monitoreo.id]);
                        }

                        if (existingRow) {
                            existingRow.classList.add('fila-actualizada');
                            existingRow.style.background = '#fff3cd';
                            existingRow.innerHTML = generarFilaMonitoreo(monitoreo);
                            setTimeout(() => {
                                existingRow.style.background = '';
                                existingRow.classList.remove('fila-actualizada');
                            }, 1000);
                        } else {
                            const row = document.createElement('tr');
                            row.id = rowId;
                            row.innerHTML = generarFilaMonitoreo(monitoreo);
                            tbody.appendChild(row);
                        }
                    }

                    lastMonitoreoData[monitoreo.id] = { ...monitoreo };
                });
            }

            document.getElementById('last-update').textContent = new Date(data.timestamp).toLocaleTimeString();

            setTimeout(() => {
                const filas = document.querySelectorAll('#tabla-monitoreo tbody tr');
                updateSearchCounter(filas.length, '');
                refreshSearch();
            }, 100);
        })
        .catch(error => {
            console.error('Error al cargar monitoreo:', error);
            document.getElementById('tbody-monitoreo').innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-danger">
                        <i class="bi bi-exclamation-triangle"></i>
                        Error al cargar los datos del monitoreo. Verificando conexión...
                    </td>
                </tr>`;
        });
}

// Abre el modal para finalizar la evaluación de un participante
function finalizarEvaluacion(monitoreoId, participanteNombre) {
    currentMonitoreoId = monitoreoId;
    document.getElementById('participante-nombre').textContent = participanteNombre;
    document.getElementById('motivo-finalizacion').value = '';
    const el = document.getElementById('modalFinalizar');
    const modal = bootstrap.Modal.getInstance(el) || new bootstrap.Modal(el);
    modal.show();
}

// Abre el modal para agregar una alerta a un participante
function agregarAlerta(monitoreoId) {
    currentMonitoreoId = monitoreoId;
    document.getElementById('tipo-alerta').value = 'comportamiento';
    document.getElementById('severidad-alerta').value = 'media';
    document.getElementById('descripcion-alerta').value = '';
    const el = document.getElementById('modalAlerta');
    const modal = bootstrap.Modal.getInstance(el) || new bootstrap.Modal(el);
    modal.show();
}

// Navega a la página de detalles del monitoreo
function verDetalles(monitoreoId) {
    window.location.href = window.detalleMonitoreoUrl.replace('/0/', `/${monitoreoId}/`);
}

// Abre el modal para dar nuevo intento a un participante
function darNuevoIntento(participanteId, nombreParticipante, intentosUsados = 0, intentosTotales = 1) {
    window.currentParticipanteId = participanteId;
    window.currentParticipanteNombre = nombreParticipante;

    document.getElementById('nombre-participante-intento').textContent = nombreParticipante;
    document.getElementById('intentos-usados').textContent = intentosUsados;
    document.getElementById('intentos-totales').textContent = intentosTotales;
    document.getElementById('cantidad-intentos').value = '1';

    actualizarNuevoTotal();
    const el = document.getElementById('modalNuevoIntento');
    const modal = bootstrap.Modal.getInstance(el) || new bootstrap.Modal(el);
    modal.show();
}

// Abre el modal para reducir cambios de pestaña de un participante
function reducirCambiosPestana(participanteId, nombreParticipante, cambiosActuales = 0, cambiosMaximo = 4) {
    if (cambiosActuales === 0) {
        showDynamicToast({ type: 'warning', title: 'Sin cambios', message: `${nombreParticipante} no ha realizado cambios de pestañas.` });
        return;
    }

    window.currentParticipanteIdReducir = participanteId;
    window.currentParticipanteNombreReducir = nombreParticipante;
    window.currentCambiosActuales = cambiosActuales;

    document.getElementById('nombre-participante-reducir').textContent = nombreParticipante;
    document.getElementById('cambios-actuales').textContent = cambiosActuales;
    document.getElementById('cambios-maximo').textContent = cambiosMaximo;

    const selectReducir = document.getElementById('cantidad-reducir');
    selectReducir.innerHTML = '';
    for (let i = 1; i <= Math.min(cambiosActuales, 4); i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = `${i} cambio${i > 1 ? 's' : ''}`;
        if (i === 1) option.selected = true;
        selectReducir.appendChild(option);
    }

    actualizarNuevoTotalCambios();
    const el = document.getElementById('modalReducirCambiosPestana');
    const modal = bootstrap.Modal.getInstance(el) || new bootstrap.Modal(el);
    modal.show();
}

// Actualiza el badge "Nuevo Total" en el modal de nuevo intento
function actualizarNuevoTotal() {
    const intentosTotales = parseInt(document.getElementById('intentos-totales').textContent, 10) || 0;
    const cantidadAdicional = parseInt(document.getElementById('cantidad-intentos').value, 10) || 0;
    const el = document.getElementById('nuevo-total');
    el.textContent = intentosTotales + cantidadAdicional;
    el.style.transform = 'scale(1.2)';
    el.style.transition = 'transform 0.2s ease';
    setTimeout(() => { el.style.transform = 'scale(1)'; }, 200);
}

// Actualiza el badge "Nuevo Total" en el modal de reducir cambios
function actualizarNuevoTotalCambios() {
    const cambiosActuales = window.currentCambiosActuales || 0;
    const cantidadReducir = parseInt(document.getElementById('cantidad-reducir').value, 10) || 0;
    const nuevoTotal = Math.max(0, cambiosActuales - cantidadReducir);
    const el = document.getElementById('nuevo-total-cambios');
    el.textContent = nuevoTotal;
    el.className = `badge fs-6 ${nuevoTotal === 0 ? 'bg-success' : nuevoTotal === 1 ? 'bg-warning' : 'bg-danger'}`;
    el.style.transform = 'scale(1.2)';
    el.style.transition = 'transform 0.2s ease';
    setTimeout(() => { el.style.transform = 'scale(1)'; }, 200);
}

// ==================== FUNCIONALIDAD DE BÚSQUEDA ====================

function normalizeText(text) {
    return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function highlightMatch(text, searchTerm) {
    if (!searchTerm) return text;
    const normalizedText = normalizeText(text);
    const normalizedSearch = normalizeText(searchTerm);
    if (!normalizedText.includes(normalizedSearch)) return text;
    const regex = new RegExp(`(${escapeRegExp(searchTerm)})`, 'gi');
    return text.replace(regex, '<mark class="bg-warning">$1</mark>');
}

function removeHighlight(fila) {
    fila.querySelectorAll('mark.bg-warning').forEach(el => { el.outerHTML = el.textContent; });
}

function highlightText(fila, searchTerm) {
    removeHighlight(fila);
    const cell = fila.querySelector('td:first-child');
    if (cell) cell.innerHTML = highlightMatch(cell.textContent, searchTerm);
}

function updateSearchCounter(visibleCount, searchTerm) {
    const counter = document.getElementById('search-results-count');
    const total = document.querySelectorAll('#tabla-monitoreo tbody tr').length || totalParticipantes;
    if (searchTerm === '') {
        counter.textContent = `Mostrando ${total} participante${total !== 1 ? 's' : ''}`;
        counter.className = 'text-muted';
    } else {
        counter.textContent = `${visibleCount} de ${total} participante${visibleCount !== 1 ? 's' : ''} encontrado${visibleCount !== 1 ? 's' : ''}`;
        counter.className = visibleCount > 0 ? 'text-info' : 'text-warning';
    }
}

function handleNoResults(visibleCount, searchTerm) {
    let noResultsMsg = document.getElementById('no-results-message');
    if (visibleCount === 0 && searchTerm !== '') {
        if (!noResultsMsg) {
            noResultsMsg = document.createElement('tr');
            noResultsMsg.id = 'no-results-message';
            noResultsMsg.innerHTML = `
                <td colspan="8" class="text-center py-5 text-muted">
                    <i class="fas fa-search-minus fa-3x mb-3 d-block"></i>
                    <h5>No se encontraron participantes</h5>
                    <p class="mb-0">Intenta con otros términos de búsqueda o verifica la ortografía.</p>
                </td>`;
            document.querySelector('#tabla-monitoreo tbody')?.appendChild(noResultsMsg);
        }
        noResultsMsg.style.display = '';
    } else if (noResultsMsg) {
        noResultsMsg.style.display = 'none';
    }
}

function searchParticipantes(searchTerm) {
    const normalizedSearch = normalizeText(searchTerm);
    let visibleCount = 0;

    document.querySelectorAll('#tabla-monitoreo tbody tr').forEach(fila => {
        const cell = fila.querySelector('td:first-child');
        if (!cell) return;

        const matches = normalizeText(cell.textContent).includes(normalizedSearch);

        if (matches || searchTerm === '') {
            fila.style.display = '';
            fila.classList.remove('search-no-results');
            visibleCount++;
            if (searchTerm !== '') highlightText(fila, searchTerm);
            else removeHighlight(fila);
        } else {
            fila.style.display = 'none';
            fila.classList.add('search-no-results');
        }
    });

    updateSearchCounter(visibleCount, searchTerm);
    handleNoResults(visibleCount, searchTerm);
}

function clearSearch() {
    const searchInput = document.getElementById('search-participantes');
    searchInput.value = '';
    searchInput.focus();
    searchParticipantes('');
    searchInput.style.transition = 'all 0.3s ease';
    searchInput.style.transform = 'scale(1.02)';
    setTimeout(() => { searchInput.style.transform = 'scale(1)'; }, 150);
}

function refreshSearch() {
    const searchInput = document.getElementById('search-participantes');
    if (searchInput && searchInput.value) {
        searchParticipantes(searchInput.value);
    }
}

// ==================== FIN FUNCIONALIDAD DE BÚSQUEDA ====================

// ==================== INICIALIZACIÓN ====================

document.addEventListener('DOMContentLoaded', function() {
    const evaluacionId = window.evaluacionId;

    // Carga inicial de datos
    cargarMonitoreo();

    // Auto-refresh
    const autoRefreshCheckbox = document.getElementById('auto-refresh');
    function toggleAutoRefresh() {
        if (autoRefreshCheckbox.checked) {
            autoRefreshInterval = setInterval(cargarMonitoreo, 5000);
        } else {
            clearInterval(autoRefreshInterval);
        }
    }
    autoRefreshCheckbox.addEventListener('change', toggleAutoRefresh);
    toggleAutoRefresh();

    // Actualización dinámica del nuevo total de intentos
    document.getElementById('cantidad-intentos').addEventListener('change', actualizarNuevoTotal);

    // Actualización dinámica del nuevo total de cambios de pestaña
    document.getElementById('cantidad-reducir').addEventListener('change', actualizarNuevoTotalCambios);

    // Confirmar finalización
    document.getElementById('btn-confirmar-finalizar').addEventListener('click', async function() {
        const motivo = document.getElementById('motivo-finalizacion').value;
        if (!motivo.trim()) {
            showDynamicToast({ type: 'warning', title: 'Advertencia', message: 'Por favor, ingrese un motivo para la finalización.' });
            return;
        }

        try {
            const response = await fetch(window.finalizarEvaluacionUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ monitoreo_id: currentMonitoreoId, motivo })
            });
            const data = await response.json();
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('modalFinalizar')).hide();
                cargarMonitoreo();
                showDynamicToast({ type: 'success', title: 'Éxito', message: data.message });
            } else {
                showDynamicToast({ type: 'danger', title: 'Error', message: data.error });
            }
        } catch (error) {
            console.error('Error:', error);
            showDynamicToast({ type: 'danger', title: 'Error', message: 'Error al finalizar la evaluación' });
        }
    });

    // Confirmar alerta
    document.getElementById('btn-confirmar-alerta').addEventListener('click', async function() {
        const tipoAlerta = document.getElementById('tipo-alerta').value;
        const severidad = document.getElementById('severidad-alerta').value;
        const descripcion = document.getElementById('descripcion-alerta').value;

        if (!descripcion.trim()) {
            showDynamicToast({ type: 'warning', title: 'Advertencia', message: 'Por favor, ingrese una descripción para la alerta.' });
            return;
        }

        try {
            const alertaUrl = window.agregarAlertaUrl.replace('/0/', `/${currentMonitoreoId}/`);
            const response = await fetch(alertaUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ tipo_alerta: tipoAlerta, severidad, descripcion })
            });
            const data = await response.json();
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('modalAlerta')).hide();
                cargarMonitoreo();
                showDynamicToast({ type: 'success', title: 'Éxito', message: data.message });
            } else {
                showDynamicToast({ type: 'danger', title: 'Error', message: data.error });
            }
        } catch (error) {
            console.error('Error:', error);
            showDynamicToast({ type: 'danger', title: 'Error', message: 'Error al agregar la alerta' });
        }
    });

    // Confirmar nuevo intento
    document.getElementById('btn-confirmar-nuevo-intento').addEventListener('click', async function() {
        const participanteId = window.currentParticipanteId;
        const cantidadIntentos = document.getElementById('cantidad-intentos').value;

        if (!participanteId) {
            showDynamicToast({ type: 'danger', title: 'Error', message: 'No se ha seleccionado un participante válido.' });
            return;
        }
        if (!cantidadIntentos || cantidadIntentos < 1) {
            showDynamicToast({ type: 'warning', title: 'Advertencia', message: 'Por favor, ingrese una cantidad válida de intentos.' });
            return;
        }

        try {
            const response = await fetch(window.darNuevoIntentoUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ participante_id: participanteId, cantidad_intentos: parseInt(cantidadIntentos, 10) })
            });
            const data = await response.json();
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('modalNuevoIntento')).hide();
                cargarMonitoreo();
                showDynamicToast({ type: 'success', title: 'Éxito', message: data.message });
                window.currentParticipanteId = null;
                window.currentParticipanteNombre = null;
            } else {
                showDynamicToast({ type: 'danger', title: 'Error', message: data.error });
            }
        } catch (error) {
            console.error('Error:', error);
            showDynamicToast({ type: 'danger', title: 'Error', message: 'Error al procesar el nuevo intento' });
        }
    });

    // Confirmar reducción de cambios de pestaña
    document.getElementById('btn-confirmar-reducir').addEventListener('click', async function() {
        const participanteId = window.currentParticipanteIdReducir;
        const cantidadReducir = document.getElementById('cantidad-reducir').value;

        if (!participanteId) {
            showDynamicToast({ type: 'danger', title: 'Error', message: 'No se ha seleccionado un participante válido.' });
            return;
        }
        if (!cantidadReducir || cantidadReducir < 1) {
            showDynamicToast({ type: 'warning', title: 'Advertencia', message: 'Por favor, seleccione una cantidad válida para reducir.' });
            return;
        }

        try {
            const response = await fetch(window.reducirCambiosPestanaUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ participante_id: participanteId, cantidad_reduccion: parseInt(cantidadReducir, 10) })
            });
            const data = await response.json();
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('modalReducirCambiosPestana')).hide();
                cargarMonitoreo();
                showDynamicToast({ type: 'success', title: 'Éxito', message: data.message });
                window.currentParticipanteIdReducir = null;
                window.currentParticipanteNombreReducir = null;
                window.currentCambiosActuales = null;
            } else {
                showDynamicToast({ type: 'danger', title: 'Error', message: data.error });
            }
        } catch (error) {
            console.error('Error:', error);
            showDynamicToast({ type: 'danger', title: 'Error', message: 'Error al procesar la reducción de cambios' });
        }
    });

    // Búsqueda
    const searchInput = document.getElementById('search-participantes');
    const clearButton = document.getElementById('clear-search');

    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => searchParticipantes(e.target.value), 300);
        });
        searchInput.addEventListener('paste', function(e) {
            setTimeout(() => searchParticipantes(e.target.value), 100);
        });
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(searchTimeout);
                searchParticipantes(e.target.value);
            }
        });
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Escape') clearSearch();
        });
    }

    if (clearButton) {
        clearButton.addEventListener('click', clearSearch);
    }

    // Inicializar contador una vez que la tabla tenga datos
    setTimeout(() => {
        const filas = document.querySelectorAll('#tabla-monitoreo tbody tr');
        if (filas.length > 0) {
            totalParticipantes = filas.length;
            updateSearchCounter(filas.length, '');
        }
    }, 1000);
});
