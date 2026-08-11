// Estado global del monitoreo
let autoRefreshInterval;
let currentMonitoreoId = null;
let lastMonitoreoData = {};
let searchTimeout;
let totalParticipantes = 0;
let monitoreoRequestInFlight = false;

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

function crearElemento(tag, className = '', text = null) {
    const elemento = document.createElement(tag);
    if (className) elemento.className = className;
    if (text !== null) elemento.textContent = text;
    return elemento;
}

function crearBoton(className, title, icono, callback, texto = '') {
    const boton = crearElemento('button', `btn ${className}`);
    boton.type = 'button';
    boton.title = title;
    boton.setAttribute('aria-label', title);
    boton.appendChild(crearElemento('i', `bi ${icono}`));
    if (texto) boton.append(` ${texto}`);
    if (callback) boton.addEventListener('click', callback);
    else boton.disabled = true;
    return boton;
}

// Genera una fila sin interpolar datos del participante como HTML ni JavaScript.
function generarFilaMonitoreo(monitoreo) {
    const fila = document.createElement('tr');
    fila.id = `monitoreo-row-${monitoreo.id}`;

    const intentosUsados = monitoreo.intentos_usados || 0;
    const intentosDisponibles = monitoreo.intentos_disponibles || 0;
    const intentosTotales = intentosUsados + intentosDisponibles;
    const cambiosActuales = monitoreo.cambios_pestana_actuales || 0;
    const cambiosMaximo = monitoreo.cambios_pestana_maximo || 4;

    const participante = crearElemento('td');
    participante.appendChild(crearElemento('strong', '', monitoreo.participante_nombre));
    participante.appendChild(document.createElement('br'));
    participante.appendChild(crearElemento('small', 'text-muted', monitoreo.participante_cedula));
    fila.appendChild(participante);

    const estado = crearElemento('td');
    estado.appendChild(crearElemento(
        'span',
        `badge bg-${getEstadoColor(monitoreo.esta_activo, monitoreo.estado, monitoreo.ha_iniciado, intentosDisponibles)}`,
        getEstadoText(monitoreo.esta_activo, monitoreo.estado, monitoreo.ha_iniciado, intentosDisponibles)
    ));
    fila.appendChild(estado);

    const progreso = crearElemento('td');
    if (monitoreo.estado === 'finalizado' && intentosDisponibles === 0 && monitoreo.tiene_resultado_completado) {
        const puntaje = Number(monitoreo.puntos_obtenidos || 0);
        const color = puntaje >= 7 ? 'success' : puntaje >= 5 ? 'warning' : 'danger';
        const contenedor = crearElemento('div', 'text-center');
        contenedor.appendChild(crearElemento('strong', `text-${color}`, monitoreo.puntaje_numerico || '0.000/10'));
        progreso.appendChild(contenedor);
    } else if ((monitoreo.estado === 'finalizado' || monitoreo.estado === 'inactivo') && intentosDisponibles > 0) {
        progreso.appendChild(crearElemento('span', 'badge bg-warning', 'Puede reiniciar'));
    } else if (!monitoreo.ha_iniciado || monitoreo.estado === 'pendiente') {
        progreso.appendChild(crearElemento('span', 'badge bg-info', 'Sin iniciar'));
    } else {
        const porcentaje = Math.max(0, Math.min(100, Number(monitoreo.porcentaje_avance || 0)));
        const barra = crearElemento('div', 'progress');
        barra.style.height = '20px';
        const progresoBarra = crearElemento('div', `progress-bar ${porcentaje > 0 ? 'bg-primary' : 'bg-light'}`, `${porcentaje}%`);
        progresoBarra.style.width = `${porcentaje}%`;
        progresoBarra.setAttribute('role', 'progressbar');
        progresoBarra.setAttribute('aria-valuenow', porcentaje);
        progresoBarra.setAttribute('aria-valuemin', '0');
        progresoBarra.setAttribute('aria-valuemax', '100');
        barra.appendChild(progresoBarra);
        progreso.append(barra, crearElemento('small', 'text-muted', `${monitoreo.preguntas_respondidas || 0} respondidas / ${monitoreo.preguntas_revisadas || 0} revisadas`));
    }
    fila.appendChild(progreso);

    const actividad = crearElemento('td');
    if (!monitoreo.ha_iniciado || monitoreo.estado === 'pendiente') {
        actividad.appendChild(crearElemento('span', 'text-muted', 'Sin iniciar'));
    } else if (monitoreo.ultima_actividad) {
        const fecha = new Date(monitoreo.ultima_actividad);
        const minutos = Math.max(0, Math.floor((Date.now() - fecha.getTime()) / 60000));
        const color = minutos >= 5 ? 'danger' : minutos >= 3 ? 'warning' : 'success';
        actividad.appendChild(crearElemento('span', `text-${color}`, fecha.toLocaleTimeString()));
        if (minutos > 0) {
            actividad.appendChild(document.createElement('br'));
            actividad.appendChild(crearElemento('small', 'text-muted', `Hace ${minutos} min`));
        }
    } else {
        actividad.appendChild(crearElemento('span', 'text-warning', 'Sin registro'));
    }
    fila.appendChild(actividad);

    const intentos = crearElemento('td');
    const intentosBadge = crearElemento('span', `badge ${intentosDisponibles > 0 ? 'bg-success' : 'bg-danger'}`, `${intentosDisponibles}/${intentosTotales}`);
    intentosBadge.title = 'Disponibles/Total';
    intentos.appendChild(intentosBadge);
    fila.appendChild(intentos);

    const cambios = crearElemento('td');
    const claseCambios = cambiosActuales >= cambiosMaximo ? 'bg-danger' : cambiosActuales > cambiosMaximo / 2 ? 'bg-warning text-dark' : 'bg-success';
    cambios.appendChild(crearElemento('span', `badge ${claseCambios}`, `${cambiosActuales}/${cambiosMaximo}`));
    fila.appendChild(cambios);

    const alertas = crearElemento('td');
    alertas.appendChild(crearElemento('span', `badge ${monitoreo.alertas_count > 0 ? 'bg-danger' : 'bg-success'}`, monitoreo.alertas_count || 0));
    fila.appendChild(alertas);

    const acciones = crearElemento('td');
    const grupo = crearElemento('div', 'btn-group btn-group-sm');
    grupo.setAttribute('role', 'group');
    if (monitoreo.resultado_id) {
        grupo.appendChild(crearBoton('btn-outline-info', 'Ver detalles', 'bi-eye', () => verDetalles(monitoreo.resultado_id)));
    } else {
        grupo.appendChild(crearBoton('btn-outline-info', 'Aún no hay un intento para revisar', 'bi-eye', null));
    }

    if (monitoreo.estado === 'activo' && monitoreo.resultado_id) {
        grupo.appendChild(crearBoton('btn-outline-warning', 'Agregar alerta', 'bi-exclamation-triangle', () => agregarAlerta(monitoreo.resultado_id)));
        grupo.appendChild(crearBoton('btn-outline-danger', 'Reducir cambios de pestañas', 'bi-dash-circle', () => reducirCambiosPestana(monitoreo.participante_id, monitoreo.participante_nombre, cambiosActuales, cambiosMaximo)));
        grupo.appendChild(crearBoton('btn-outline-danger', 'Finalizar evaluación', 'bi-stop-circle', () => finalizarEvaluacion(monitoreo.resultado_id, monitoreo.participante_nombre)));
    } else if (intentosDisponibles === 0) {
        grupo.appendChild(crearBoton('btn-outline-success', 'Dar nuevo intento', 'bi-arrow-clockwise', () => darNuevoIntento(monitoreo.participante_id, monitoreo.participante_nombre, intentosUsados, intentosTotales)));
    } else {
        grupo.appendChild(crearBoton('btn-outline-secondary', monitoreo.ha_iniciado ? 'Puede reiniciar cuando quiera' : 'Esperando que inicie', monitoreo.ha_iniciado ? 'bi-play-circle' : 'bi-hourglass-split', null, monitoreo.ha_iniciado ? 'Disponible' : 'Esperando'));
    }
    acciones.appendChild(grupo);
    fila.appendChild(acciones);
    return fila;
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
        showDynamicToast({ type: 'warning', title: 'Participante inactivo', message: `${nombre} lleva más de 5 minutos sin actividad` });
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

function actualizarEstadisticas(monitoreos) {
    const activos = monitoreos.filter(item => item.estado === 'activo').length;
    const finalizados = monitoreos.filter(item => item.estado === 'finalizado').length;
    const pendientes = monitoreos.length - activos - finalizados;
    document.getElementById('stat-activos').textContent = activos;
    document.getElementById('stat-finalizados').textContent = finalizados;
    document.getElementById('stat-pendientes').textContent = pendientes;
    document.getElementById('stat-total').textContent = monitoreos.length;
    totalParticipantes = monitoreos.length;
}

function mostrarErrorMonitoreo() {
    const tbody = document.getElementById('tbody-monitoreo');
    tbody.replaceChildren();
    const fila = document.createElement('tr');
    const celda = crearElemento('td', 'text-center text-danger', 'Error al cargar los datos del monitoreo. Verificando conexión...');
    celda.colSpan = 8;
    fila.appendChild(celda);
    tbody.appendChild(fila);
}

// Carga y actualiza la tabla de monitoreo sin solapar solicitudes HTTP.
async function cargarMonitoreo() {
    if (monitoreoRequestInFlight) return;
    monitoreoRequestInFlight = true;
    try {
        const response = await fetch(window.monitoreoEstadoUrl, { credentials: 'same-origin' });
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        const data = await response.json();
        if (!Array.isArray(data.monitoreos)) throw new Error('Datos de monitoreo inválidos');

        const tbody = document.getElementById('tbody-monitoreo');
        const nuevosDatos = {};
        const filasActuales = new Map(
            [...tbody.querySelectorAll('tr[id^="monitoreo-row-"]')].map(fila => [fila.id, fila])
        );

        data.monitoreos.forEach(monitoreo => {
            const rowId = `monitoreo-row-${monitoreo.id}`;
            const filaAnterior = filasActuales.get(rowId);
            const datosAnteriores = lastMonitoreoData[monitoreo.id];
            const cambio = hasMonitoreoChanged(monitoreo, datosAnteriores);

            if (!filaAnterior || cambio) {
                if (datosAnteriores) notificarCambioEstado(monitoreo, datosAnteriores);
                const nuevaFila = generarFilaMonitoreo(monitoreo);
                if (filaAnterior) {
                    nuevaFila.classList.add('fila-actualizada');
                    nuevaFila.style.background = '#fff3cd';
                    filaAnterior.replaceWith(nuevaFila);
                    setTimeout(() => {
                        nuevaFila.style.background = '';
                        nuevaFila.classList.remove('fila-actualizada');
                    }, 1000);
                } else {
                    tbody.appendChild(nuevaFila);
                }
            }
            filasActuales.delete(rowId);
            nuevosDatos[monitoreo.id] = { ...monitoreo };
        });

        // Elimina filas de participantes que ya no pertenecen a la evaluación.
        filasActuales.forEach(fila => fila.remove());
        lastMonitoreoData = nuevosDatos;
        actualizarEstadisticas(data.monitoreos);
        document.getElementById('last-update').textContent = new Date(data.timestamp).toLocaleTimeString();
        refreshSearch();
        updateSearchCounter(document.querySelectorAll('#tabla-monitoreo tbody tr[id^="monitoreo-row-"]').length, document.getElementById('search-participantes').value);
    } catch (error) {
        console.error('Error al cargar monitoreo:', error);
        // Se vacía el cache para que una recuperación reconstruya la tabla completa.
        lastMonitoreoData = {};
        mostrarErrorMonitoreo();
    } finally {
        monitoreoRequestInFlight = false;
    }
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

function updateSearchCounter(visibleCount, searchTerm) {
    const counter = document.getElementById('search-results-count');
    const total = totalParticipantes;
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

    document.querySelectorAll('#tabla-monitoreo tbody tr[id^="monitoreo-row-"]').forEach(fila => {
        const cell = fila.querySelector('td:first-child');
        if (!cell) return;

        const matches = normalizeText(cell.textContent).includes(normalizedSearch);

        if (matches || searchTerm === '') {
            fila.style.display = '';
            fila.classList.remove('search-no-results');
            visibleCount++;
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
        clearInterval(autoRefreshInterval);
        if (autoRefreshCheckbox.checked) {
            autoRefreshInterval = setInterval(cargarMonitoreo, 10000);
        }
    }
    autoRefreshCheckbox.addEventListener('change', toggleAutoRefresh);
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            clearInterval(autoRefreshInterval);
        } else if (autoRefreshCheckbox.checked) {
            cargarMonitoreo();
            toggleAutoRefresh();
        }
    });
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
