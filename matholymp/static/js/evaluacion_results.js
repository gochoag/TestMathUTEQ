/**
 * JavaScript para la página de resultados de evaluación
 * Maneja gráficos, filtros, modales y funciones de exportación
 */

// Variables globales para datos
let analisisData = [];
let categoriasData = [];
let distribucionData = [];
let preguntasData = [];
let ckeditorRetroalimentacion = null;

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeData();
    initCharts();
    setupEventListeners();
});

/**
 * Inicializa los datos desde el template
 */
function initializeData() {
    // Los datos se pasarán desde el template HTML
    const analisisElement = document.getElementById('analisis-data');
    if (analisisElement) {
        try {
            analisisData = JSON.parse(analisisElement.textContent);
        } catch (e) {
            console.warn('Error al parsear datos de análisis:', e);
            analisisData = [];
        }
    }
}

/**
 * Configura los event listeners
 */
function setupEventListeners() {
    // Event listeners para los selectores de filtro
    const grupoSelect = document.getElementById('grupoSelect');
    const categoriaSelect = document.getElementById('categoriaSelect');
    
    if (grupoSelect) {
        grupoSelect.addEventListener('change', aplicarFiltros);
    }
    
    if (categoriaSelect) {
        categoriaSelect.addEventListener('change', aplicarFiltros);
    }
    
    // Event listener para limpiar el CKEditor cuando se cierre el modal
    const retroalimentacionModal = document.getElementById('retroalimentacionModal');
    if (retroalimentacionModal) {
        retroalimentacionModal.addEventListener('hidden.bs.modal', function () {
            // Limpiar el CKEditor si existe
            if (ckeditorRetroalimentacion) {
                try {
                    ckeditorRetroalimentacion.destroy();
                    ckeditorRetroalimentacion = null;
                } catch (error) {
                    console.warn('Error al destruir CKEditor:', error);
                }
            }
            
            // Resetear el contenido del modal
            document.getElementById('loadingRetroalimentacion').style.display = 'none';
            document.getElementById('retroalimentacionPersonalizadaSection').style.display = 'none';
            document.getElementById('analisisAutomaticoSection').style.display = 'none';
            
            // Ocultar botones
            const btnDescargar = document.getElementById('btnDescargarRetro');
            const btnEnviarCorreo = document.getElementById('btnEnviarCorreo');
            if (btnDescargar) btnDescargar.style.display = 'none';
            if (btnEnviarCorreo) btnEnviarCorreo.style.display = 'none';
        });
    }
}

/**
 * Inicializa todos los gráficos
 */
function initCharts() {
    initDistribucionChart();
    initPreguntasChart();
    initCategoriasChart();
}

/**
 * Inicializa el gráfico de distribución de puntajes
 */
function initDistribucionChart() {
    const ctx = document.getElementById('distribucionChart');
    if (!ctx || !distribucionData.length) return;
    
    new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: distribucionData.map(item => `${item.rango} puntos`),
            datasets: [{
                label: 'Número de Estudiantes',
                data: distribucionData.map(item => item.count),
                backgroundColor: [
                    'rgba(220, 53, 69, 0.8)',   // 0-2: Rojo
                    'rgba(255, 193, 7, 0.8)',   // 2-4: Amarillo
                    'rgba(255, 193, 7, 0.8)',   // 4-6: Amarillo
                    'rgba(40, 167, 69, 0.8)',   // 6-8: Verde
                    'rgba(40, 167, 69, 0.8)'    // 8-10: Verde
                ],
                borderColor: [
                    'rgba(220, 53, 69, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(40, 167, 69, 1)',
                    'rgba(40, 167, 69, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Distribución de Puntajes'
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

/**
 * Inicializa el gráfico de rendimiento por pregunta
 */
function initPreguntasChart() {
    const ctx = document.getElementById('preguntasChart');
    if (!ctx || !analisisData.length) return;
    
    new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: analisisData.map((_, index) => `P${index + 1}`),
            datasets: [{
                label: '% de Acierto',
                data: analisisData.map(item => parseFloat(item.porcentaje_correctas) || 0),
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Porcentaje de Acierto por Pregunta'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            elements: {
                point: {
                    radius: 5,
                    hoverRadius: 8
                }
            }
        }
    });
}

/**
 * Inicializa el gráfico de rendimiento por categorías
 */
function initCategoriasChart() {
    const ctx = document.getElementById('categoriaChart');
    if (!ctx || !categoriasData.length) return;
    
    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: categoriasData.map(item => item.nombre),
            datasets: [{
                data: categoriasData.map(item => parseFloat(item.porcentaje) || 0),
                backgroundColor: [
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(255, 205, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(153, 102, 255, 0.8)',
                    'rgba(255, 159, 64, 0.8)',
                    'rgba(199, 199, 199, 0.8)',
                    'rgba(83, 102, 255, 0.8)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 205, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(199, 199, 199, 1)',
                    'rgba(83, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Distribución de Rendimiento por Categoría'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed.toFixed(1) + '%';
                        }
                    }
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

/**
 * Aplica los filtros seleccionados
 */
function aplicarFiltros() {
    const grupoSelect = document.getElementById('grupoSelect');
    const categoriaSelect = document.getElementById('categoriaSelect');
    const currentUrl = new URL(window.location);
    
    // Filtro de grupo
    const grupoId = grupoSelect ? grupoSelect.value : 'todos';
    if (grupoId === 'todos') {
        currentUrl.searchParams.delete('grupo');
    } else {
        currentUrl.searchParams.set('grupo', grupoId);
    }
    
    // Filtro de categoría
    const categoriaId = categoriaSelect ? categoriaSelect.value : 'todas';
    if (categoriaId === 'todas') {
        currentUrl.searchParams.delete('categoria');
    } else {
        currentUrl.searchParams.set('categoria', categoriaId);
    }
    
    window.location.href = currentUrl.toString();
}

/**
 * Limpia todos los filtros
 */
function limpiarFiltros() {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.delete('grupo');
    currentUrl.searchParams.delete('categoria');
    window.location.href = currentUrl.toString();
}

/**
 * Muestra una pregunta en el modal
 */
function verPregunta(preguntaId) {
    const modal = new bootstrap.Modal(document.getElementById('preguntaModal'));
    const modalBody = document.getElementById('preguntaModalBody');
    
    // Mostrar loading
    modalBody.innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2">Cargando pregunta...</p>
        </div>
    `;
    
    modal.show();
    
    // Obtener la URL base desde el template
    const urlTemplate = document.querySelector('[data-question-url]')?.dataset.questionUrl;
    if (!urlTemplate) {
        modalBody.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Error: URL de pregunta no configurada.
            </div>
        `;
        return;
    }
    
    // Cargar datos de la pregunta
    fetch(urlTemplate.replace('0', preguntaId))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                modalBody.innerHTML = generateQuestionHTML(data.data);
                
                // Renderizar LaTeX si es necesario
                if (window.MathJax) {
                    MathJax.typesetPromise([modalBody]);
                }
            } else {
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar la pregunta: ${data.error || 'Error desconocido'}
                    </div>
                `;
            }
        })
        .catch(error => {
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error de conexión al cargar la pregunta.
                </div>
            `;
        });
}

/**
 * Genera el HTML para mostrar una pregunta
 */
function generateQuestionHTML(data) {
    return `
        <div class="card">
            <div class="card-header bg-light">
                <h6 class="mb-0"><strong>Enunciado:</strong></h6>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <div class="question-text p-3 bg-light rounded">
                        ${data.pregunta}
                    </div>
                </div>
                
                <h6 class="fw-bold mb-3">Opciones:</h6>
                <div class="options-section">
                    ${data.opciones.map((opcionTexto, index) => {
                        const esCorrecta = (data.opcion_correcta === index + 1);
                        return `
                            <div class="option-item mb-2 p-3 rounded ${esCorrecta ? 'bg-success bg-opacity-10 border border-success' : 'bg-light border border-light'}">
                                <div class="d-flex align-items-start">
                                    <div class="option-indicator me-3 mt-1">
                                        ${esCorrecta ? '<i class="bi bi-check-circle-fill text-success fs-5"></i>' : '<i class="bi bi-circle text-muted"></i>'}
                                    </div>
                                    <div class="option-content flex-grow-1">
                                        <div class="option-text mb-1 ${esCorrecta ? 'text-success fw-bold' : ''}">
                                            ${opcionTexto}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
                
                <div class="mt-3 p-2 bg-info bg-opacity-10 rounded">
                    <small class="text-info">
                        <i class="bi bi-info-circle me-1"></i>
                        <strong>Puntos:</strong> ${data.puntos} punto(s)
                    </small>
                </div>
            </div>
        </div>
    `;
}

/**
 * Genera retroalimentación para el grupo seleccionado
 */
function generarRetroalimentacion() {
    const grupoSeleccionado = document.querySelector('[data-grupo-seleccionado]')?.dataset.grupoSeleccionado;
    
    if (!grupoSeleccionado) {
        if (window.Swal) {
            Swal.fire({
                icon: 'warning',
                title: 'Selecciona un Grupo',
                text: 'Debes seleccionar un grupo específico para generar retroalimentación.',
                confirmButtonText: 'Entendido'
            });
        } else {
            alert('Debes seleccionar un grupo específico para generar retroalimentación.');
        }
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('retroalimentacionModal'));
    const modalBody = document.getElementById('retroalimentacionModalBody');
    const btnDescargar = document.getElementById('btnDescargarRetro');
    const btnEnviarCorreo = document.getElementById('btnEnviarCorreo');
    
    // Ocultar botones inicialmente
    if (btnDescargar) btnDescargar.style.display = 'none';
    if (btnEnviarCorreo) btnEnviarCorreo.style.display = 'none';
    
    // Mostrar loading
    document.getElementById('loadingRetroalimentacion').style.display = 'block';
    document.getElementById('retroalimentacionPersonalizadaSection').style.display = 'none';
    document.getElementById('analisisAutomaticoSection').style.display = 'none';
    
    modal.show();
    
    // Inicializar CKEditor después de mostrar el modal
    setTimeout(() => {
        initializeCKEditorRetroalimentacion();
        
        // Generar contenido de análisis
        const analisisHTML = generateRetroalimentacionHTML();
        document.getElementById('analisisContent').innerHTML = analisisHTML;
        
        // Mostrar secciones
        document.getElementById('loadingRetroalimentacion').style.display = 'none';
        document.getElementById('retroalimentacionPersonalizadaSection').style.display = 'block';
        document.getElementById('analisisAutomaticoSection').style.display = 'block';
        
        // Mostrar botones
        if (btnDescargar) btnDescargar.style.display = 'inline-block';
        if (btnEnviarCorreo) btnEnviarCorreo.style.display = 'inline-block';
    }, 500);
}

/**
 * Inicializa CKEditor para retroalimentación personalizada
 */
function initializeCKEditorRetroalimentacion() {
    if (ckeditorRetroalimentacion) {
        return; // Ya está inicializado
    }
    
    if (window.CKEDITOR) {
        try {
            ckeditorRetroalimentacion = CKEDITOR.replace('editorRetroalimentacion', {
                ...window.ckeditorConfig,
                height: 300,
                toolbar: [
                    { name: 'clipboard', items: ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo'] },
                    { name: 'basicstyles', items: ['Bold', 'Italic', 'Underline', 'Strike', '-', 'RemoveFormat'] },
                    '/',
                    { name: 'paragraph', items: ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote'] },
                    { name: 'links', items: ['Link', 'Unlink'] },
                    { name: 'styles', items: ['Format', 'Font', 'FontSize'] },
                    { name: 'colors', items: ['TextColor', 'BGColor'] }
                ]
            });
        } catch (error) {
            console.error('Error al inicializar CKEditor:', error);
        }
    }
}

/**
 * Genera el HTML de retroalimentación
 */
function generateRetroalimentacionHTML() {
    if (!categoriasData.length) {
        return `
            <div class="alert alert-info">
                <h6><i class="bi bi-info-circle me-2"></i>Sin datos suficientes</h6>
                <p>No hay suficientes datos para generar retroalimentación detallada.</p>
            </div>
        `;
    }
    
    const grupoSeleccionado = document.querySelector('[data-grupo-seleccionado]')?.dataset.grupoSeleccionado || 'el Grupo';
    
    // Calcular promedio general como calificación sobre 10
    const promedioGeneral = (categoriasData.reduce((sum, c) => sum + c.porcentaje, 0) / categoriasData.length) / 10;
    
    return `
        <div class="row">
            <div class="col-12">
                
                <div class="alert alert-primary">
                    <h6><i class="bi bi-clipboard-data me-2"></i>Resumen del Rendimiento</h6>
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Categorías evaluadas:</strong> ${categoriasData.length}</p>
                            <p class="mb-0"><strong>Calificación promedio:</strong> <span class="badge ${promedioGeneral >= 7 ? 'bg-success' : promedioGeneral >= 5 ? 'bg-warning' : 'bg-danger'} fs-6">${promedioGeneral.toFixed(2)} / 10</span></p>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header bg-light">
                        <h6 class="mb-0"><i class="bi bi-list-check me-2"></i>Rendimiento por Categoría</h6>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr>
                                        <th>Categoría</th>
                                        <th class="text-center">Preguntas</th>
                                        <th class="text-center">% Acierto</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${categoriasData.map(c => `
                                        <tr>
                                            <td><strong>${c.nombre}</strong></td>
                                            <td class="text-center">${c.preguntas}</td>
                                            <td class="text-center">
                                                <span class="badge ${c.porcentaje >= 70 ? 'bg-success' : c.porcentaje >= 50 ? 'bg-warning' : 'bg-danger'}">${c.porcentaje}%</span>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    `;
}

/**
 * Descarga la retroalimentación en PDF
 */
function descargarRetroalimentacion() {
    const grupoSeleccionado = document.querySelector('[data-grupo-seleccionado]')?.dataset.grupoSeleccionado;
    const grupoId = document.querySelector('[data-grupo-id]')?.dataset.grupoId;
    
    if (!grupoId) {
        if (window.Swal) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo identificar el grupo seleccionado.',
                confirmButtonText: 'Entendido'
            });
        }
        return;
    }
    
    // Obtener contenido del CKEditor (puede estar vacío)
    let retroalimentacionPersonalizada = '';
    if (ckeditorRetroalimentacion) {
        retroalimentacionPersonalizada = ckeditorRetroalimentacion.getData();
    }
    
    // Obtener categorías que necesitan refuerzo
    const categoriasDificiles = categoriasData.filter(c => c.porcentaje < 50);
    const categoriasMedias = categoriasData.filter(c => c.porcentaje >= 50 && c.porcentaje < 80);
    
    // Mostrar mensaje de confirmación
    if (window.Swal) {
        Swal.fire({
            title: '¿Descargar Retroalimentación?',
            html: `
                <p>Se generará un PDF con la retroalimentación del grupo <strong>${grupoSeleccionado}</strong> que incluye:</p>
                <ul class="text-start">
                    <li>Retroalimentación ${retroalimentacionPersonalizada ? '(incluida)' : '(opcional)'}</li>
                    <li>Análisis de categorías a reforzar</li>
                    <li>Mensaje de agradecimiento</li>
                </ul>
            `,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Descargar PDF',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#0d6efd',
            showLoaderOnConfirm: true,
            preConfirm: () => {
                return descargarPDF(grupoId, retroalimentacionPersonalizada, categoriasDificiles, categoriasMedias);
            },
            allowOutsideClick: () => !Swal.isLoading()
        });
    } else {
        // Si no hay SweetAlert2, descargar directamente
        descargarPDF(grupoId, retroalimentacionPersonalizada, categoriasDificiles, categoriasMedias);
    }
}

/**
 * Descarga el PDF de retroalimentación
 */
async function descargarPDF(grupoId, retroalimentacionPersonalizada, categoriasDificiles, categoriasMedias) {
    try {
        const descargarUrl = document.querySelector('[data-descargar-retroalimentacion-url]')?.dataset.descargarRetroalimentacionUrl;
        
        if (!descargarUrl) {
            throw new Error('No se encontró la URL de descarga');
        }
        
        const response = await fetch(descargarUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                grupo_id: grupoId,
                retroalimentacion_personalizada: retroalimentacionPersonalizada,
                categorias_dificiles: categoriasDificiles,
                categorias_medias: categoriasMedias
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al generar el PDF');
        }
        
        // Obtener el blob del PDF
        const blob = await response.blob();
        
        // Crear un enlace temporal para descargar
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // Obtener nombre del archivo del header Content-Disposition
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'Retroalimentacion.pdf';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        if (window.Swal) {
            Swal.fire({
                icon: 'success',
                title: 'PDF Descargado',
                text: 'El PDF de retroalimentación se ha descargado correctamente.',
                confirmButtonText: 'Entendido',
                timer: 3000
            });
        }
        
    } catch (error) {
        console.error('Error al descargar PDF:', error);
        
        if (window.Swal) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message || 'Ocurrió un error al descargar el PDF. Por favor, intente nuevamente.',
                confirmButtonText: 'Entendido'
            });
        } else {
            alert('Error al descargar el PDF: ' + (error.message || 'Error desconocido'));
        }
        
        throw error;
    }
}

/**
 * Envía la retroalimentación por correo electrónico
 */
function enviarCorreoRetroalimentacion() {
    const grupoSeleccionado = document.querySelector('[data-grupo-seleccionado]')?.dataset.grupoSeleccionado;
    const grupoId = document.querySelector('[data-grupo-id]')?.dataset.grupoId;
    
    if (!grupoId) {
        if (window.Swal) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo identificar el grupo seleccionado.',
                confirmButtonText: 'Entendido'
            });
        }
        return;
    }
    
    // Obtener contenido del CKEditor (puede estar vacío)
    let retroalimentacionPersonalizada = '';
    if (ckeditorRetroalimentacion) {
        retroalimentacionPersonalizada = ckeditorRetroalimentacion.getData();
    }
    
    // Obtener categorías que necesitan refuerzo
    const categoriasDificiles = categoriasData.filter(c => c.porcentaje < 50);
    const categoriasMedias = categoriasData.filter(c => c.porcentaje >= 50 && c.porcentaje < 80);
    
    // Confirmar envío
    if (window.Swal) {
        Swal.fire({
            title: '¿Enviar Retroalimentación?',
            html: `
                <p>Se enviará un correo electrónico al representante del grupo <strong>${grupoSeleccionado}</strong> con:</p>
                <ul class="text-start">
                    <li>Retroalimentación ${retroalimentacionPersonalizada ? '(incluida)' : '(no incluida)'}</li>
                    <li>Análisis de categorías a reforzar</li>
                    <li>Archivo Excel con resultados detallados</li>
                </ul>
            `,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#0d6efd',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, enviar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                enviarCorreo(grupoId, retroalimentacionPersonalizada);
            }
        });
    } else {
        if (confirm(`¿Enviar retroalimentación al grupo ${grupoSeleccionado}?`)) {
            enviarCorreo(grupoId, retroalimentacionPersonalizada);
        }
    }
}

/**
 * Función auxiliar para enviar el correo
 */
function enviarCorreo(grupoId, retroalimentacionPersonalizada) {
    const url = document.querySelector('[data-enviar-retroalimentacion-url]')?.dataset.enviarRetroalimentacionUrl;
    
    if (!url) {
        if (window.Swal) {
            Swal.fire({
                icon: 'error',
                title: 'Error de Configuración',
                text: 'URL de envío no configurada.',
                confirmButtonText: 'Entendido'
            });
        }
        return;
    }
    
    // Mostrar indicador de carga
    if (window.Swal) {
        Swal.fire({
            title: 'Enviando Correo...',
            html: 'Por favor espera mientras se envía la retroalimentación.',
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
    }
    
    // Obtener token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
    
    // Preparar datos
    const data = {
        grupo_id: grupoId,
        retroalimentacion_personalizada: retroalimentacionPersonalizada,
        categorias_dificiles: categoriasData.filter(c => c.porcentaje < 50).map(c => ({
            nombre: c.nombre,
            porcentaje: c.porcentaje,
            preguntas: c.preguntas
        })),
        categorias_medias: categoriasData.filter(c => c.porcentaje >= 50 && c.porcentaje < 80).map(c => ({
            nombre: c.nombre,
            porcentaje: c.porcentaje,
            preguntas: c.preguntas
        }))
    };
    
    // Enviar solicitud
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (window.Swal) {
                Swal.fire({
                    icon: 'success',
                    title: '¡Correo Enviado!',
                    text: data.message || 'La retroalimentación ha sido enviada exitosamente.',
                    confirmButtonText: 'Entendido'
                });
            } else {
                alert('Correo enviado exitosamente.');
            }
            
            // Cerrar el modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('retroalimentacionModal'));
            if (modal) {
                modal.hide();
            }
        } else {
            if (window.Swal) {
                Swal.fire({
                    icon: 'error',
                    title: 'Error al Enviar',
                    text: data.error || 'Hubo un problema al enviar el correo.',
                    confirmButtonText: 'Entendido'
                });
            } else {
                alert('Error: ' + (data.error || 'Hubo un problema al enviar el correo.'));
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (window.Swal) {
            Swal.fire({
                icon: 'error',
                title: 'Error de Conexión',
                text: 'No se pudo conectar con el servidor. Inténtalo de nuevo.',
                confirmButtonText: 'Entendido'
            });
        } else {
            alert('Error de conexión. Inténtalo de nuevo.');
        }
    });
}

/**
 * Función para obtener cookie CSRF
 */
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

/**
 * Exporta los resultados
 */
function exportarResultados() {
    const grupoSelect = document.getElementById('grupoSelect');
    const grupoActual = grupoSelect ? grupoSelect.value : 'todos';
    
    // Obtener URL base desde el template
    const exportUrl = document.querySelector('[data-export-url]')?.dataset.exportUrl;
    if (!exportUrl) {
        if (window.Swal) {
            Swal.fire({
                icon: 'error',
                title: 'Error de Configuración',
                text: 'URL de exportación no configurada.',
                confirmButtonText: 'Entendido'
            });
        }
        return;
    }
    
    // Construir URL con filtros
    let finalUrl = exportUrl;
    if (grupoActual !== 'todos') {
        finalUrl += `?grupo=${grupoActual}`;
    }
    
    // Obtener token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    fetch(finalUrl, {
        method: 'GET',
        headers: {
            'X-CSRFToken': csrfToken || ''
        }
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Error al exportar resultados');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // Nombre del archivo con filtro si aplica
        let fileName = 'resultados_evaluacion';
        if (grupoActual !== 'todos' && grupoSelect) {
            const grupoNombre = grupoSelect.options[grupoSelect.selectedIndex].text;
            fileName += `_${grupoNombre.replace(/\s+/g, '_')}`;
        }
        fileName += '.xlsx';
        
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        if (window.Swal) {
            Swal.fire({
                icon: 'success',
                title: 'Exportación Exitosa',
                text: 'Los resultados han sido descargados exitosamente.',
                confirmButtonText: 'Entendido'
            });
        }
    })
    .catch(error => {
        console.error('Error al exportar:', error);
        if (window.Swal) {
            Swal.fire({
                icon: 'error',
                title: 'Error al Exportar',
                text: 'Hubo un problema al exportar los resultados. Inténtalo de nuevo.',
                confirmButtonText: 'Entendido'
            });
        }
    });
}

/**
 * Imprime el reporte
 */
function imprimirReporte() {
    window.print();
}

/**
 * Función para actualizar datos de categorías (llamada desde el template)
 */
function setCategoriasData(data) {
    categoriasData = data;
}

/**
 * Función para actualizar datos de distribución (llamada desde el template)
 */
function setDistribucionData(data) {
    distribucionData = data;
}

/**
 * Función para actualizar datos de preguntas (llamada desde el template)
 */
function setPreguntasData(data) {
    preguntasData = data;
    analisisData = data; // Mantener compatibilidad
}