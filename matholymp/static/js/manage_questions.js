// Variables globales
let currentPreguntaId = null;
let isEditing = false;

// La configuración de CKEditor está ahora en ckeditor_config.js
// Solo mantenemos las referencias locales necesarias

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    initializeCKEditor();
    setupEventListeners();

    // Ejecutar corrección inicial de imágenes
    corregirAlineacionImagenesMejorada();
    setTimeout(corregirAlineacionImagenesMejorada, 100);
    window.addEventListener('load', corregirAlineacionImagenesMejorada);

    // Observar cambios en el DOM para corregir imágenes dinámicamente
    const observer = new MutationObserver(function(mutations) {
        let necesitaCorreccion = false;

        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.querySelector && node.querySelector('img')) {
                            necesitaCorreccion = true;
                        }
                    }
                });
            }
        });

        if (necesitaCorreccion) {
            setTimeout(corregirAlineacionImagenesMejorada, 50);
        }
    });

    // Observar cambios en el contenido de preguntas y opciones
    const contenedores = document.querySelectorAll('.pregunta-text, .opcion-text, .cke_editable');
    contenedores.forEach(contenedor => {
        observer.observe(contenedor, {
            childList: true,
            subtree: true
        });
    });

    // Limpiar formulario si se abre el modal sin edición activa
    const modalPregunta = document.getElementById('modalPregunta');
    if (modalPregunta) {
        modalPregunta.addEventListener('show.bs.modal', function () {
            if (!currentPreguntaId) {
                clearForm();
            }
        });
    }
});

// Inicializar CKEditor
function initializeCKEditor() {
    if (window.CKEDITOR) {
        // Configuración específica para el editor de pregunta
        CKEDITOR.replace('editorPregunta', {
            ...window.ckeditorConfig,
            height: 200,
            toolbar: [
                { name: 'document', items: ['Source'] },
                { name: 'clipboard', items: ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo'] },
                { name: 'editing', items: ['Find', 'Replace', '-', 'SelectAll'] },
                '/',
                { name: 'basicstyles', items: ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat'] },
                { name: 'paragraph', items: ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'] },
                { name: 'links', items: ['Link', 'Unlink'] },
                { name: 'insert', items: ['CustomImage', 'Table', 'HorizontalRule', 'SpecialChar'] },
                '/',
                { name: 'styles', items: ['Styles', 'Format', 'Font', 'FontSize'] },
                { name: 'colors', items: ['TextColor', 'BGColor'] },
                { name: 'tools', items: ['Maximize'] }
            ]
        });
        
        // Configuración para los editores de opciones
        for (let i = 1; i <= 4; i++) {
            CKEDITOR.replace('editorOpcion' + i, {
                ...window.ckeditorConfig,
                height: 120,
                toolbar: [
                    { name: 'clipboard', items: ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo'] },
                    { name: 'basicstyles', items: ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat'] },
                    { name: 'paragraph', items: ['NumberedList', 'BulletedList', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'] },
                    { name: 'links', items: ['Link', 'Unlink'] },
                    { name: 'insert', items: ['CustomImage', 'Table', 'SpecialChar'] },
                    { name: 'styles', items: ['Format', 'Font', 'FontSize'] },
                    { name: 'colors', items: ['TextColor', 'BGColor'] }
                ]
            });
        }
    }
}

// Configurar event listeners
function setupEventListeners() {
    const btnGuardarPregunta = document.getElementById('btnGuardarPregunta');
    if (btnGuardarPregunta) {
        btnGuardarPregunta.addEventListener('click', saveQuestion);
    }
    
    // Botón para guardar cambios y redirigir a evaluaciones
    const btnGuardarPreguntas = document.getElementById('btnGuardarPreguntas');
    if (btnGuardarPreguntas) {
        btnGuardarPreguntas.addEventListener('click', function() {
            showAppDialog({
                icon: 'success',
                title: '¡Éxito!',
                text: 'Las preguntas se han guardado correctamente',
                confirmButtonText: 'Continuar',
                customClass: {
                    container: 'swal-over-modal'
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = '/evaluaciones/';
                }
            });
        });
    }
    
    // Limpiar formulario cuando se cierre el modal
    const modalPregunta = document.getElementById('modalPregunta');
    if (modalPregunta) {
        modalPregunta.addEventListener('hidden.bs.modal', clearForm);
    }
}

// Función para procesar imágenes base64 antes de guardar
async function processBase64Images(content) {
    const imgRegex = /<img[^>]+src="data:image\/[^;]+;base64,[^"]+"/g;
    const base64Regex = /data:image\/[^;]+;base64,([^"]+)/;
    
    let processedContent = content;
    const matches = content.match(imgRegex);
    
    if (matches) {
        for (const match of matches) {
            const base64Match = match.match(base64Regex);
            if (base64Match) {
                try {
                    // Convertir base64 a blob y subir como archivo
                    const base64Data = base64Match[1];
                    const byteCharacters = atob(base64Data);
                    const byteNumbers = new Array(byteCharacters.length);
                    for (let i = 0; i < byteCharacters.length; i++) {
                        byteNumbers[i] = byteCharacters.charCodeAt(i);
                    }
                    const byteArray = new Uint8Array(byteNumbers);
                    const blob = new Blob([byteArray], {type: 'image/png'});
                    
                    // Crear FormData y subir
                    const formData = new FormData();
                    formData.append('upload', blob, 'formula.png');
                    
                    // Subir imagen y reemplazar con URL
                    const response = await fetch(window.uploadImageUrl, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    
                    if (data.url) {
                        processedContent = processedContent.replace(match, match.replace(base64Regex, data.url));
                    } else {
                        console.error('No se recibió URL en la respuesta:', data);
                    }
                } catch (error) {
                    console.error('Error uploading image:', error);
                    // Continuar con el contenido original si hay error
                }
            }
        }
    }
    
    return processedContent;
}

// Función principal para guardar pregunta
async function saveQuestion() {
    // Verificar si se pueden modificar las preguntas
    if (window.canModifyQuestions === false) {
        showAppDialog({
            icon: 'warning',
            title: 'Operación no permitida',
            text: window.restrictionMessage || 'No se pueden agregar preguntas en este momento.',
            confirmButtonText: 'Entendido',
            customClass: {
                container: 'swal-over-modal'
            }
        });
        return;
    }

    // Obtener datos de los editores CKEditor
    let pregunta = CKEDITOR.instances.editorPregunta.getData();
    let opciones = [];
    
    for (let i = 1; i <= 4; i++) {
        const opcion = CKEDITOR.instances['editorOpcion' + i].getData();
        opciones.push(opcion);
    }
    
    // Procesar imágenes base64 en pregunta y opciones
    try {
        pregunta = await processBase64Images(pregunta);
        
        for (let i = 0; i < opciones.length; i++) {
            opciones[i] = await processBase64Images(opciones[i]);
        }
    } catch (error) {
        console.error('Error processing images:', error);
        showAppDialog({
            icon: 'warning',
            title: 'Advertencia',
            text: 'Hubo un problema procesando las imágenes. Continuando con el guardado...',
            customClass: {
                container: 'swal-over-modal'
            }
        });
    }
    
    // Obtener la opción correcta seleccionada
    const opcionCorrecta = document.querySelector('input[name="opcion_correcta"]:checked');
    
    // Obtener los puntos
    const puntosRaw = document.getElementById('puntosPregunta').value;
    const puntos = parseInt(puntosRaw, 10);
    
    // Obtener la categoría
    const categoriaElement = document.getElementById('categoriaPregunta');
    const categoria = categoriaElement ? categoriaElement.value : null;
    
    // Validaciones
    if (!pregunta.trim()) {
        showAppDialog({
            icon: 'error',
            title: 'Error',
            text: 'El enunciado de la pregunta es obligatorio',
            customClass: {
                container: 'swal-over-modal'
            }
        });
        return;
    }
    
    if (!opcionCorrecta) {
        showAppDialog({
            icon: 'error',
            title: 'Error',
            text: 'Debe seleccionar una opción correcta',
            customClass: {
                container: 'swal-over-modal'
            }
        });
        return;
    }
    
    // Validar categoría
    if (!categoria || categoria === '' || categoria === '0') {
        showAppDialog({
            icon: 'error',
            title: 'Error',
            text: 'Debe seleccionar una categoría',
            customClass: {
                container: 'swal-over-modal'
            }
        });
        return;
    }
    
    // Validar puntos
    if (isNaN(puntos) || puntos < 1 || puntos > 10) {
        showAppDialog({
            icon: 'error',
            title: 'Error',
            text: 'Los puntos deben estar entre 1 y 10',
            customClass: {
                container: 'swal-over-modal'
            }
        });
        return;
    }
    
    // Verificar que todas las opciones tengan contenido
    for (let i = 0; i < opciones.length; i++) {
        if (!opciones[i].trim()) {
            showAppDialog({
                icon: 'error',
                title: 'Error',
                text: `La opción ${'ABCD'[i]} es obligatoria`,
                customClass: {
                    container: 'swal-over-modal'
                }
            });
            return;
        }
    }
    
    // Preparar datos para enviar
    const categoriaInt = parseInt(categoria);
    if (isNaN(categoriaInt)) {
        showAppDialog({
            icon: 'error',
            title: 'Error',
            text: 'La categoría seleccionada no es válida',
            customClass: {
                container: 'swal-over-modal'
            }
        });
        return;
    }
    
    const data = {
        pregunta: pregunta,
        opciones: opciones,
        opcion_correcta: opcionCorrecta.value,
        puntos: puntos,  // ya es entero por parseInt en L197
        categoria: categoriaInt
    };
    
    // Mostrar indicador de carga
    const actionText = isEditing ? 'Actualizando' : 'Guardando';
    showAppLoading({
        title: `${actionText} pregunta...`,
        html: 'Por favor espera mientras se procesa la pregunta.',
        allowOutsideClick: false,
        allowEscapeKey: false,
    });
    
    // Deshabilitar el botón de guardar
    const btnGuardar = document.getElementById('btnGuardarPregunta');
    if (btnGuardar) {
        btnGuardar.disabled = true;
    }

    // Determinar URL según si es edición o creación
    const url = isEditing ?
        window.updateQuestionUrl.replace('/0/', `/${currentPreguntaId}/`) :
        window.saveQuestionUrl;

    // Enviar datos al backend
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });

        const responseData = await response.json();

        // Rehabilitar el botón de guardar
        if (btnGuardar) {
            btnGuardar.disabled = false;
        }

        if (responseData.success) {
            closeAppDialog();

            // Cerrar el modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalPregunta'));
            modal.hide();

            // Mostrar mensaje de éxito
            showAppDialog({
                icon: 'success',
                title: '¡Éxito!',
                text: responseData.message,
                timer: 2000,
                showConfirmButton: false,
                customClass: {
                    container: 'swal-over-modal'
                }
            });

            // Recargar la página para mostrar la nueva pregunta
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            closeAppDialog();

            showAppDialog({
                icon: 'error',
                title: 'Error',
                text: responseData.error,
                customClass: {
                    container: 'swal-over-modal'
                }
            });
        }
    } catch (error) {
        // Rehabilitar el botón de guardar
        if (btnGuardar) {
            btnGuardar.disabled = false;
        }

        closeAppDialog();

        console.error('Error:', error);
        showAppDialog({
            icon: 'error',
            title: 'Error',
            text: 'Error de red o del servidor',
            customClass: {
                container: 'swal-over-modal'
            }
        });
    }
}

// Función para eliminar pregunta
function deletePregunta(preguntaId) {
    // Verificar si se pueden modificar las preguntas
    if (window.canModifyQuestions === false) {
        showAppDialog({
            icon: 'warning',
            title: 'Operación no permitida',
            text: window.restrictionMessage || 'No se pueden eliminar preguntas en este momento.',
            confirmButtonText: 'Entendido',
            customClass: {
                container: 'swal-over-modal'
            }
        });
        return;
    }

    confirmDestructiveAction({
        title: '¿Estás seguro?',
        text: "Esta acción no se puede deshacer. Se eliminará la pregunta y todas sus opciones.",
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        customClass: {
            container: 'swal-over-modal'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(window.deleteQuestionUrl.replace('/0/', `/${preguntaId}/`), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAppDialog({
                        icon: 'success',
                        title: '¡Eliminada!',
                        text: data.message,
                        timer: 2000,
                        showConfirmButton: false,
                        customClass: {
                            container: 'swal-over-modal'
                        }
                    });
                    
                    // Eliminar la pregunta del DOM
                    const preguntaCard = document.querySelector(`[data-pregunta-id="${preguntaId}"]`);
                    if (preguntaCard) {
                        preguntaCard.style.animation = 'fadeOut 0.5s ease-out';
                        setTimeout(() => {
                            preguntaCard.remove();
                            // Actualizar números de pregunta
                            updatePreguntaNumbers();
                        }, 500);
                    }
                } else {
                    showAppDialog({
                        icon: 'error',
                        title: 'Error',
                        text: data.error,
                        customClass: {
                            container: 'swal-over-modal'
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAppDialog({
                    icon: 'error',
                    title: 'Error',
                    text: 'Error de red o del servidor',
                    customClass: {
                        container: 'swal-over-modal'
                    }
                });
            });
        }
    });
}

// Función para editar pregunta
async function editPregunta(preguntaId) {
    // Verificar si se pueden modificar las preguntas
    if (window.canModifyQuestions === false) {
        showAppDialog({
            icon: 'warning',
            title: 'Operación no permitida',
            text: window.restrictionMessage || 'No se pueden editar preguntas en este momento.',
            confirmButtonText: 'Entendido',
            customClass: {
                container: 'swal-over-modal'
            }
        });
        return;
    }

    try {
        // Mostrar loading
        showAppDialog({
            title: 'Cargando...',
            text: 'Obteniendo datos de la pregunta',
            allowOutsideClick: false,
            didOpen: () => {
                showAppLoader();
            },
            customClass: {
                container: 'swal-over-modal'
            }
        });
        
        // Obtener datos de la pregunta
        const response = await fetch(window.getQuestionDataUrl.replace('0', preguntaId));
        const data = await response.json();
        
        if (data.success) {
            // Cerrar loading
            closeAppDialog();
            
            // Configurar modo edición
            currentPreguntaId = preguntaId;
            isEditing = true;
            
            // Llenar el formulario con los datos
            CKEDITOR.instances.editorPregunta.setData(data.data.pregunta);
            
            for (let i = 0; i < data.data.opciones.length; i++) {
                CKEDITOR.instances['editorOpcion' + (i + 1)].setData(data.data.opciones[i]);
            }
            
            // Marcar la opción correcta
            const opcionCorrecta = document.querySelector(`input[name="opcion_correcta"][value="${data.data.opcion_correcta}"]`);
            if (opcionCorrecta) {
                opcionCorrecta.checked = true;
            }
            
            // Establecer los puntos
            const puntosInput = document.getElementById('puntosPregunta');
            if (puntosInput && data.data.puntos) {
                puntosInput.value = data.data.puntos;
            }
            
            // Establecer la categoría
            const categoriaSelect = document.getElementById('categoriaPregunta');
            if (categoriaSelect && data.data.categoria) {
                categoriaSelect.value = data.data.categoria;
            }
            
            // Cambiar título del modal
            const modalTitle = document.querySelector('#modalPregunta .modal-title');
            if (modalTitle) {
                modalTitle.innerHTML = '<i class="bi bi-pencil-square me-2"></i>Editar Pregunta';
            }
            
            // Cambiar texto del botón
            const btnGuardar = document.getElementById('btnGuardarPregunta');
            if (btnGuardar) {
                btnGuardar.textContent = 'Actualizar Pregunta';
            }
            
            // Abrir el modal
            const modal = new bootstrap.Modal(document.getElementById('modalPregunta'));
            modal.show();
            
            // Corregir imágenes después de abrir el modal
            setTimeout(corregirAlineacionImagenesMejorada, 200);
            
        } else {
            showAppDialog({
                icon: 'error',
                title: 'Error',
                text: data.error,
                customClass: {
                    container: 'swal-over-modal'
                }
            });
        }
    } catch (error) {
        console.error('Error:', error);
        showAppDialog({
            icon: 'error',
            title: 'Error',
            text: 'Error de red o del servidor',
            customClass: {
                container: 'swal-over-modal'
            }
        });
    }
}

// Función para actualizar números de pregunta
function updatePreguntaNumbers() {
    const preguntaCards = document.querySelectorAll('.pregunta-card');
    preguntaCards.forEach((card, index) => {
        const numberBadge = card.querySelector('.number-badge');
        if (numberBadge) {
            numberBadge.textContent = index + 1;
        }
    });
}

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

// Limpiar formulario
function clearForm() {
    if (CKEDITOR.instances.editorPregunta) {
        CKEDITOR.instances.editorPregunta.setData('');
    }
    
    for (let i = 1; i <= 4; i++) {
        if (CKEDITOR.instances['editorOpcion' + i]) {
            CKEDITOR.instances['editorOpcion' + i].setData('');
        }
    }
    
    // Desmarcar opción correcta
    const opcionCorrecta = document.querySelector('input[name="opcion_correcta"]:checked');
    if (opcionCorrecta) {
        opcionCorrecta.checked = false;
    }
    
    // Resetear puntos
    const puntosInput = document.getElementById('puntosPregunta');
    if (puntosInput) {
        puntosInput.value = '1';
    }
    
    // Resetear categoría
    const categoriaSelect = document.getElementById('categoriaPregunta');
    if (categoriaSelect) {
        categoriaSelect.value = '';
    }
    
    // Resetear variables
    currentPreguntaId = null;
    isEditing = false;
    
    // Cambiar título del modal
    const modalTitle = document.querySelector('#modalPregunta .modal-title');
    if (modalTitle) {
        modalTitle.innerHTML = '<i class="bi bi-plus-circle me-2"></i>Agregar Pregunta';
    }
    
    // Cambiar texto del botón y asegurar que esté habilitado
    const btnGuardar = document.getElementById('btnGuardarPregunta');
    if (btnGuardar) {
        btnGuardar.textContent = 'Guardar Pregunta';
        btnGuardar.disabled = false; // Asegurar que esté habilitado
    }
}

// Función para actualizar puntos de una pregunta
async function actualizarPuntos(preguntaId, puntos) {
    // Verificar si se pueden modificar las preguntas
    if (window.canModifyQuestions === false) {
        // Mostrar mensaje y revertir el valor
        showAppDialog({
            icon: 'warning',
            title: 'Operación no permitida',
            text: window.restrictionMessage || 'No se pueden modificar preguntas en este momento.',
            confirmButtonText: 'Entendido',
            customClass: {
                container: 'swal-over-modal'
            }
        });
        
        // Revertir el valor del input
        const input = document.querySelector(`[onchange="actualizarPuntos(${preguntaId}, this.value)"]`);
        if (input) {
            input.value = input.defaultValue || input.getAttribute('data-original-value') || 1;
        }
        return;
    }

    try {
        const response = await fetch(window.updatePuntosUrl.replace('/0/', `/${preguntaId}/`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ puntos: puntos })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Mostrar notificación de éxito
            showAppDialog({
                icon: 'success',
                title: 'Éxito',
                text: 'Puntos actualizados correctamente',
                timer: 1500,
                showConfirmButton: false,
                customClass: {
                    container: 'swal-over-modal'
                }
            });
        } else {
            showAppDialog({
                icon: 'error',
                title: 'Error',
                text: data.error,
                customClass: {
                    container: 'swal-over-modal'
                }
            });
        }
    } catch (error) {
        console.error('Error:', error);
        showAppDialog({
            icon: 'error',
            title: 'Error',
            text: 'Error de red o del servidor',
            customClass: {
                container: 'swal-over-modal'
            }
        });
    }
}


// Función mejorada para corregir la alineación de imágenes
function corregirAlineacionImagenesMejorada() {
    // Buscar todas las imágenes en el contenido de preguntas y opciones
    const todasLasImagenes = document.querySelectorAll('.pregunta-text img, .opcion-text img, .cke_editable img');
    
    todasLasImagenes.forEach(img => {
        // Aplicar estilos base para todas las imágenes
        img.style.verticalAlign = 'middle';
        img.style.position = 'relative';
        img.style.top = '0';
        img.style.margin = '0';
        img.style.display = 'inline';
        
        // Buscar y corregir elementos padre problemáticos
        let elementoPadre = img.parentElement;
        while (elementoPadre && (elementoPadre.tagName === 'SPAN' || elementoPadre.tagName === 'DIV')) {
            const computedStyle = window.getComputedStyle(elementoPadre);
            
            // Corregir estilos problemáticos
            if (computedStyle.verticalAlign !== 'middle') {
                elementoPadre.style.verticalAlign = 'middle';
            }
            if (computedStyle.position !== 'static') {
                elementoPadre.style.position = 'static';
            }
            if (computedStyle.top !== 'auto') {
                elementoPadre.style.top = 'auto';
            }
            if (computedStyle.display === 'inline-block') {
                elementoPadre.style.display = 'inline';
            }
            
            elementoPadre = elementoPadre.parentElement;
        }
    });
    
    // Corregir estilos de alineación en spans del contenido
    const spansDeContenido = document.querySelectorAll('.pregunta-text span, .opcion-text span, .cke_editable span');
    
    spansDeContenido.forEach(span => {
        const computedStyle = window.getComputedStyle(span);
        
        // Estilos de alineación esperados
        const estilosDeAlineacion = {
            'verticalAlign': 'middle',
            'position': 'static',
            'top': 'auto',
            'display': 'inline'
        };

        // Aplicar correcciones solo si es necesario
        Object.entries(estilosDeAlineacion).forEach(([propiedad, valor]) => {
            if (computedStyle[propiedad] !== valor) {
                span.style[propiedad] = valor;
            }
        });
    });
}

// Funciones para la gestión de cuotas de preguntas por Unidad Temática
function actualizarTotalCuotasVisual() {
    let total = 0;
    document.querySelectorAll('.cuota-unidad-input').forEach(input => {
        total += parseInt(input.value || 0);
    });
    const badge = document.getElementById('badgeTotalCuotas');
    const notice = document.getElementById('recommendedQuotaNotice');
    if (badge) {
        badge.textContent = total;
    }
    if (notice) {
        if (total === 10) {
            notice.innerHTML = '<span class="text-success"><i class="bi bi-check-circle me-1"></i>Estándar de 10 preguntas alcanzado</span>';
        } else {
            notice.innerHTML = '<span class="text-primary">(Recomendado: 10 preguntas)</span>';
        }
    }
}

async function guardarCuotasUnidad() {
    if (!window.canModifyQuestions) {
        showAppDialog({
            icon: 'warning',
            title: 'Acción no permitida',
            text: window.restrictionMessage || 'No se pueden modificar las cuotas de esta evaluación.'
        });
        return;
    }

    const cuotas_unidades = [];
    let total = 0;
    document.querySelectorAll('.cuota-unidad-input').forEach(input => {
        const uId = input.getAttribute('data-unidad-id');
        const cant = parseInt(input.value || 0);
        if (uId) {
            cuotas_unidades.push({ unidad_id: parseInt(uId), cantidad: cant });
            total += cant;
        }
    });

    if (total <= 0) {
        showAppDialog({
            icon: 'error',
            title: 'Total de preguntas inválido',
            text: 'La suma total de preguntas a mostrar debe ser mayor a 0.'
        });
        return;
    }

    showAppDialog({
        title: 'Guardando distribución...',
        text: 'Por favor espera',
        allowOutsideClick: false,
        didOpen: () => { showAppLoader(); }
    });

    try {
        const response = await fetch(window.updateCuotasUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ cuotas_unidades })
        });
        const data = await response.json();
        if (data.success) {
            showAppDialog({
                icon: 'success',
                title: '¡Guardado!',
                text: data.message || 'Distribución de preguntas actualizada exitosamente.',
                timer: 1500,
                showConfirmButton: false
            });
            actualizarTotalCuotasVisual();
        } else {
            showAppDialog({
                icon: 'error',
                title: 'Error',
                text: data.error || 'No se pudo guardar la distribución.'
            });
        }
    } catch (error) {
        console.error('Error al guardar cuotas:', error);
        showAppDialog({
            icon: 'error',
            title: 'Error de red',
            text: 'Ocurrió un error al guardar la distribución de preguntas.'
        });
    }
}

