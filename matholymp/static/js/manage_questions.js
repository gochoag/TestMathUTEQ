// Variables globales
let currentPreguntaId = null;
let isEditing = false;

// Configuración de CKEditor
const ckeditorConfig = {
    extraPlugins: 'pastefromword,customimagehandler',
    removePlugins: 'exportpdf,uploadimage',
    allowedContent: true,
    forcePasteAsPlainText: false,
    pasteFromWordPromptCleanup: true,
    keystrokes: [
        [ CKEDITOR.CTRL + 86 /* V */, 'PasteFromWord' ],
        [ CKEDITOR.CTRL + CKEDITOR.SHIFT + 86 /* Ctrl+Shift+V */, 'pastetext' ]
    ],
    // Deshabilitar el manejo automático de imágenes del portapapeles
    clipboard_handleImages: false,
    // Configuración para extraer imágenes base64
    pasteFilter: {
        elementNames: [
            { element: 'img', attributes: '!src' }
        ]
    }
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Crear plugin personalizado para manejar imágenes
    if (window.CKEDITOR) {
        CKEDITOR.plugins.add('customimagehandler', {
            init: function(editor) {
                // Agregar comando personalizado para insertar imagen
                editor.addCommand('insertImage', {
                    exec: function(editor) {
                        // Crear input file oculto
                        const input = document.createElement('input');
                        input.type = 'file';
                        input.accept = 'image/*';
                        input.style.display = 'none';
                        document.body.appendChild(input);
                        
                        input.onchange = function(e) {
                            const file = e.target.files[0];
                            if (file) {
                                const formData = new FormData();
                                formData.append('upload', file);
                                
                                fetch(uploadImageUrl, {
                                    method: 'POST',
                                    headers: {
                                        'X-CSRFToken': getCookie('csrftoken')
                                    },
                                    body: formData
                                })
                                .then(response => response.json())
                                .then(data => {
                                    if (data.url) {
                                        editor.insertHtml(`<img src="${data.url}" alt="Imagen" style="max-width: 100%; height: auto;" />`);
                                    } else {
                                        Swal.fire({
                                            icon: 'error',
                                            title: 'Error',
                                            text: 'No se pudo subir la imagen',
                                            customClass: {
                                                container: 'swal-over-modal'
                                            }
                                        });
                                    }
                                })
                                .catch(error => {
                                    console.error('Error uploading image:', error);
                                    Swal.fire({
                                        icon: 'error',
                                        title: 'Error',
                                        text: 'Error al subir la imagen',
                                        customClass: {
                                            container: 'swal-over-modal'
                                        }
                                    });
                                });
                            }
                            document.body.removeChild(input);
                        };
                        
                        input.click();
                    }
                });
                
                // Agregar botón a la toolbar
                editor.ui.addButton('CustomImage', {
                    label: 'Insertar Imagen',
                    command: 'insertImage',
                    toolbar: 'insert'
                });
                
                // Agregar comando para pegar imagen del portapapeles
                editor.addCommand('pasteImage', {
                    exec: function(editor) {
                        // Crear un área temporal para pegar
                        const tempDiv = document.createElement('div');
                        tempDiv.contentEditable = true;
                        tempDiv.style.position = 'absolute';
                        tempDiv.style.left = '-9999px';
                        tempDiv.style.top = '-9999px';
                        document.body.appendChild(tempDiv);
                        
                        // Enfocar el área temporal
                        tempDiv.focus();
                        
                        // Simular Ctrl+V
                        const pasteEvent = new KeyboardEvent('keydown', {
                            key: 'v',
                            code: 'KeyV',
                            ctrlKey: true,
                            bubbles: true
                        });
                        
                        tempDiv.dispatchEvent(pasteEvent);
                        
                        // Esperar un momento y verificar si se pegó algo
                        setTimeout(() => {
                            const pastedContent = tempDiv.innerHTML;
                            
                            // Buscar imágenes base64
                            const imgRegex = /<img[^>]+src="data:image\/[^;]+;base64,[^"]+"/g;
                            const matches = pastedContent.match(imgRegex);
                            
                            if (matches && matches.length > 0) {
                                // Procesar imágenes
                                let uploadPromises = [];
                                
                                for (const match of matches) {
                                    const base64Match = match.match(/data:image\/[^;]+;base64,([^"]+)/);
                                    if (base64Match) {
                                        const base64Data = base64Match[1];
                                        const byteCharacters = atob(base64Data);
                                        const byteNumbers = new Array(byteCharacters.length);
                                        for (let i = 0; i < byteCharacters.length; i++) {
                                            byteNumbers[i] = byteCharacters.charCodeAt(i);
                                        }
                                        const byteArray = new Uint8Array(byteNumbers);
                                        const blob = new Blob([byteArray], {type: 'image/png'});
                                        
                                        const formData = new FormData();
                                        formData.append('upload', blob, 'pasted-image.png');
                                        
                                        const uploadPromise = fetch(uploadImageUrl, {
                                            method: 'POST',
                                            headers: {
                                                'X-CSRFToken': getCookie('csrftoken')
                                            },
                                            body: formData
                                        })
                                        .then(response => response.json())
                                        .then(data => {
                                            if (data.url) {
                                                return data.url;
                                            }
                                            throw new Error('No se recibió URL en la respuesta');
                                        });
                                        
                                        uploadPromises.push(uploadPromise);
                                    }
                                }
                                
                                // Procesar silenciosamente sin mostrar indicador
                                
                                // Esperar a que todas las imágenes se suban
                                Promise.all(uploadPromises)
                                    .then(urls => {
                                        // Insertar todas las imágenes silenciosamente
                                        urls.forEach(url => {
                                            editor.insertHtml(`<img src="${url}" alt="Imagen" style="max-width: 100%; height: auto; margin: 5px 0;" />`);
                                        });
                                    })
                                    .catch(error => {
                                        console.error('Error uploading pasted image:', error);
                                        // Procesar silenciosamente sin mostrar error
                                    });
                            } else {
                                // No se encontraron imágenes - procesar silenciosamente
                                console.log('No se detectó ninguna imagen en el portapapeles');
                            }
                            
                            // Limpiar área temporal
                            document.body.removeChild(tempDiv);
                        }, 100);
                    }
                });
                
                // Agregar botón para pegar imagen
                editor.ui.addButton('PasteImage', {
                    label: 'Pegar Imagen',
                    command: 'pasteImage',
                    toolbar: 'insert'
                });
            }
        });
    }
    
    initializeCKEditor();
    setupEventListeners();
});

// Inicializar CKEditor
function initializeCKEditor() {
    if (window.CKEDITOR) {
        // Configuración específica para cada editor
        const preguntaEditor = CKEDITOR.replace('editorPregunta', {
            ...ckeditorConfig,
            height: 200,
            toolbar: [
                { name: 'document', items: ['Source'] },
                { name: 'clipboard', items: ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo'] },
                { name: 'editing', items: ['Find', 'Replace', '-', 'SelectAll', '-', 'SpellChecker', 'Scayt'] },
                { name: 'forms', items: ['Form', 'Checkbox', 'Radio', 'TextField', 'Textarea', 'Select', 'Button', 'ImageButton', 'HiddenField'] },
                '/',
                { name: 'basicstyles', items: ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat'] },
                { name: 'paragraph', items: ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', 'CreateDiv', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock', '-', 'BidiLtr', 'BidiRtl'] },
                { name: 'links', items: ['Link', 'Unlink', 'Anchor'] },
                { name: 'insert', items: ['CustomImage', 'PasteImage', 'Table', 'HorizontalRule', 'Smiley', 'SpecialChar', 'PageBreak', 'Iframe'] },
                '/',
                { name: 'styles', items: ['Styles', 'Format', 'Font', 'FontSize'] },
                { name: 'colors', items: ['TextColor', 'BGColor'] },
                { name: 'tools', items: ['Maximize', 'ShowBlocks'] }
            ]
        });
        
        // Configuración para los editores de opciones
        for (let i = 1; i <= 4; i++) {
            CKEDITOR.replace('editorOpcion' + i, {
                ...ckeditorConfig,
                height: 120,
                toolbar: [
                    { name: 'clipboard', items: ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo'] },
                    { name: 'basicstyles', items: ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat'] },
                    { name: 'paragraph', items: ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'] },
                    { name: 'links', items: ['Link', 'Unlink'] },
                    { name: 'insert', items: ['CustomImage', 'PasteImage', 'Table', 'HorizontalRule', 'SpecialChar'] },
                    { name: 'styles', items: ['Styles', 'Format', 'Font', 'FontSize'] },
                    { name: 'colors', items: ['TextColor', 'BGColor'] }
                ]
            });
        }
        
        // Configurar manejo de imágenes del portapapeles
        CKEDITOR.on('instanceReady', function(evt) {
            const editor = evt.editor;
            
            // Manejar imágenes del portapapeles
            editor.on('paste', function(e) {
                const data = e.data;
                const html = data.dataValue;
                
                // Buscar imágenes base64 en el HTML pegado
                const imgRegex = /<img[^>]+src="data:image\/[^;]+;base64,[^"]+"/g;
                const matches = html.match(imgRegex);
                
                if (matches) {
                    // Cancelar el evento de pegado por defecto
                    e.cancel();
                    
                    // Procesar cada imagen base64 de forma asíncrona
                    let processedHtml = html;
                    let uploadPromises = [];
                    
                    // Procesar silenciosamente sin mostrar indicador
                    
                    for (const match of matches) {
                        const base64Match = match.match(/data:image\/[^;]+;base64,([^"]+)/);
                        if (base64Match) {
                            const base64Data = base64Match[1];
                            const byteCharacters = atob(base64Data);
                            const byteNumbers = new Array(byteCharacters.length);
                            for (let i = 0; i < byteCharacters.length; i++) {
                                byteNumbers[i] = byteCharacters.charCodeAt(i);
                            }
                            const byteArray = new Uint8Array(byteNumbers);
                            const blob = new Blob([byteArray], {type: 'image/png'});
                            
                            // Crear promesa para subir imagen
                            const uploadPromise = fetch(uploadImageUrl, {
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': getCookie('csrftoken')
                                },
                                body: (() => {
                                    const formData = new FormData();
                                    formData.append('upload', blob, 'pasted-image.png');
                                    return formData;
                                })()
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.url) {
                                    return { original: match, replacement: data.url };
                                }
                                throw new Error('No se recibió URL en la respuesta');
                            });
                            
                            uploadPromises.push(uploadPromise);
                        }
                    }
                    
                    // Esperar a que todas las imágenes se suban
                    Promise.all(uploadPromises)
                        .then(results => {
                            let finalHtml = processedHtml;
                            results.forEach(result => {
                                finalHtml = finalHtml.replace(
                                    result.original, 
                                    result.original.replace(/data:image\/[^;]+;base64,[^"]+/, result.replacement)
                                );
                            });
                            
                            // Insertar el contenido procesado silenciosamente
                            editor.insertHtml(finalHtml);
                        })
                        .catch(error => {
                            console.error('Error uploading pasted images:', error);
                            // Procesar silenciosamente sin mostrar error
                        });
                }
            });
            
            // Manejar también el evento de pegado de archivos
            editor.on('paste', function(e) {
                const data = e.data;
                const files = data.dataTransfer ? data.dataTransfer.files : null;
                
                if (files && files.length > 0) {
                    e.cancel();
                    
                    let uploadPromises = [];
                    
                    // Procesar silenciosamente sin mostrar indicador
                    
                    for (let i = 0; i < files.length; i++) {
                        const file = files[i];
                        
                        // Verificar que sea una imagen
                        if (file.type.startsWith('image/')) {
                            const formData = new FormData();
                            formData.append('upload', file);
                            
                            const uploadPromise = fetch(uploadImageUrl, {
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': getCookie('csrftoken')
                                },
                                body: formData
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.url) {
                                    return data.url;
                                }
                                throw new Error('No se recibió URL en la respuesta');
                            });
                            
                            uploadPromises.push(uploadPromise);
                        }
                    }
                    
                    // Esperar a que todas las imágenes se suban
                    Promise.all(uploadPromises)
                        .then(urls => {
                            // Insertar todas las imágenes silenciosamente
                            urls.forEach(url => {
                                editor.insertHtml(`<img src="${url}" alt="Imagen" style="max-width: 100%; height: auto; margin: 5px 0;" />`);
                            });
                        })
                        .catch(error => {
                            console.error('Error uploading files:', error);
                            // Procesar silenciosamente sin mostrar error
                        });
                }
            });
        });
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
            Swal.fire({
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
                    const response = await fetch(uploadImageUrl, {
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
        Swal.fire({
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
    
    // Validaciones
    if (!pregunta.trim()) {
        Swal.fire({
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
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Debe seleccionar una opción correcta',
            customClass: {
                container: 'swal-over-modal'
            }
        });
        return;
    }
    
    // Verificar que todas las opciones tengan contenido
    for (let i = 0; i < opciones.length; i++) {
        if (!opciones[i].trim()) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: `La opción ${String.fromCharCode(65 + i)} (${'ABCD'[i]}) es obligatoria`,
                customClass: {
                    container: 'swal-over-modal'
                }
            });
            return;
        }
    }
    
    // Preparar datos para enviar
    const data = {
        pregunta: pregunta,
        opciones: opciones,
        opcion_correcta: opcionCorrecta.value
    };
    
    // Determinar URL según si es edición o creación
    const url = isEditing ? 
        updateQuestionUrl.replace('0', currentPreguntaId) : 
        saveQuestionUrl;
    
    // Enviar datos al backend
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Cerrar el modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalPregunta'));
            modal.hide();
            
            // Mostrar mensaje de éxito
            Swal.fire({
                icon: 'success',
                title: '¡Éxito!',
                text: data.message,
                timer: 2000,
                showConfirmButton: false,
                customClass: {
                    container: 'swal-over-modal'
                }
            });
            
            // Recargar la página para mostrar la nueva pregunta
            setTimeout(() => window.location.reload(), 2000);
        } else {
            Swal.fire({
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
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error de red o del servidor',
            customClass: {
                container: 'swal-over-modal'
            }
        });
    });
}

// Función para eliminar pregunta
function deletePregunta(preguntaId) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Esta acción no se puede deshacer. Se eliminará la pregunta y todas sus opciones.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        customClass: {
            container: 'swal-over-modal'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(deleteQuestionUrl.replace('0', preguntaId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
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
                    Swal.fire({
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
                Swal.fire({
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
    try {
        // Mostrar loading
        Swal.fire({
            title: 'Cargando...',
            text: 'Obteniendo datos de la pregunta',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            },
            customClass: {
                container: 'swal-over-modal'
            }
        });
        
        // Obtener datos de la pregunta
        const response = await fetch(getQuestionDataUrl.replace('0', preguntaId));
        const data = await response.json();
        
        if (data.success) {
            // Cerrar loading
            Swal.close();
            
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
            
        } else {
            Swal.fire({
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
        Swal.fire({
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
    
    // Resetear variables
    currentPreguntaId = null;
    isEditing = false;
    
    // Cambiar título del modal
    const modalTitle = document.querySelector('#modalPregunta .modal-title');
    if (modalTitle) {
        modalTitle.innerHTML = '<i class="bi bi-plus-circle me-2"></i>Agregar Pregunta';
    }
    
    // Cambiar texto del botón
    const btnGuardar = document.getElementById('btnGuardarPregunta');
    if (btnGuardar) {
        btnGuardar.textContent = 'Guardar Pregunta';
    }
} 