// Variables globales para el modal de Excel
let excelHeaders = [];
let columnMapping = {};
let processedData = [];
let excelProcessingErrors = [];

// Utilidad para escapar HTML en textos dinámicos
function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Función para procesar el archivo Excel
function processExcelFile() {
    const fileInput = document.getElementById('excelFile');
    const file = fileInput.files[0];
    
    if (!file) {
        Swal.fire({
            icon: 'warning',
            title: 'Archivo requerido',
            text: 'Por favor selecciona un archivo Excel.',
        });
        return;
    }
    
    // Leer el archivo para obtener los headers
    const reader = new FileReader();
    reader.onload = function(e) {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, {type: 'array'});
        const worksheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, {header: 1});
        
        if (jsonData.length > 0) {
            excelHeaders = jsonData[0];
            populateColumnMapping();
            showStep2();
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Archivo inválido',
                text: 'El archivo Excel está vacío o no contiene datos válidos.',
            });
        }
    };
    reader.readAsArrayBuffer(file);
}

// Función para poblar el mapeo de columnas
function populateColumnMapping() {
    const selects = ['mapCedula', 'mapNombres', 'mapEmail', 'mapTelefono', 'mapEdad'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Seleccionar columna...</option>';
        
        excelHeaders.forEach((header, index) => {
            const option = document.createElement('option');
            option.value = index + 1; // +1 porque las columnas empiezan en 1
            option.textContent = `${index + 1}. ${header || `Columna ${index + 1}`}`;
            select.appendChild(option);
        });
    });
}

// Función para previsualizar datos
function previewData() {
    // Validar que se hayan seleccionado los campos requeridos
    const requiredFields = ['mapCedula', 'mapNombres', 'mapEmail'];
    const missingFields = [];
    
    requiredFields.forEach(fieldId => {
        const select = document.getElementById(fieldId);
        if (!select.value) {
            missingFields.push(select.previousElementSibling.textContent.split('(')[0].trim());
        }
    });
    
    if (missingFields.length > 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Campos requeridos',
            text: `Por favor selecciona los campos requeridos: ${missingFields.join(', ')}`,
        });
        return;
    }
    
    // Construir el mapeo de columnas
    columnMapping = {
        [document.getElementById('mapCedula').value]: 'cedula',
        [document.getElementById('mapNombres').value]: 'NombresCompletos',
        [document.getElementById('mapEmail').value]: 'email'
    };
    
    const mapTelefono = document.getElementById('mapTelefono').value;
    const mapEdad = document.getElementById('mapEdad').value;
    
    if (mapTelefono) columnMapping[mapTelefono] = 'phone';
    if (mapEdad) columnMapping[mapEdad] = 'edad';
    
    // Mostrar indicador de carga
    Swal.fire({
        title: 'Procesando archivo...',
        html: 'Por favor espera mientras se procesa el archivo Excel.',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        customClass: {
            container: 'swal2-container-over-modal',
            popup: 'swal2-popup-over-modal'
        },
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    // Enviar archivo al servidor para procesamiento
    const formData = new FormData();
    formData.append('excel_file', document.getElementById('excelFile').files[0]);
    formData.append('column_mapping', JSON.stringify(columnMapping));
    
    // Obtener la URL de la vista desde un atributo data del modal
    const modal = document.getElementById('loadExcelModal');
    const processUrl = modal.getAttribute('data-process-url');
    const saveUrl = modal.getAttribute('data-save-url');
    
    fetch(processUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        // Cerrar el loading
        Swal.close();
        
        if (data.success) {
            processedData = data.data;
            displayPreview(data);
            showStep3();
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error al procesar el archivo',
                text: 'Error: ' + data.error,
                customClass: {
                    container: 'swal2-container-over-modal',
                    popup: 'swal2-popup-over-modal'
                }
            });
        }
    })
    .catch(error => {
        // Cerrar el loading
        Swal.close();
        
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error al procesar el archivo',
            text: 'Por favor intenta de nuevo.',
            customClass: {
                container: 'swal2-container-over-modal',
                popup: 'swal2-popup-over-modal'
            }
        });
    });
}

// Función para mostrar la previsualización
function displayPreview(data) {
    const statsDiv = document.getElementById('previewStats');
    const errorsDiv = document.getElementById('previewErrors');
    const tableBody = document.getElementById('previewTableBody');
    const saveBtn = document.getElementById('saveBtn');
    excelProcessingErrors = Array.isArray(data.errors) ? data.errors : [];
    
    // Mostrar estadísticas
    statsDiv.innerHTML = `
        <i class="fas fa-chart-bar"></i>
        <strong>Resumen:</strong> ${data.valid_rows} filas válidas de ${data.total_rows} totales
        ${data.error_rows > 0 ? `(${data.error_rows} con errores)` : ''}
    `;
    
    // Mostrar errores si los hay
    if (excelProcessingErrors.length > 0) {
        errorsDiv.style.display = 'block';
        const limitedList = excelProcessingErrors
            .slice(0, 5)
            .map(error => `<li>${escapeHtml(error)}</li>`) 
            .join('');
        const remainingCount = Math.max(0, excelProcessingErrors.length - 5);
        const moreIndicator = remainingCount > 0
            ? `<li>... y ${remainingCount} errores más <button type="button" id="showAllErrorsBtn" class="btn btn-link p-0 ms-1">Ver todos</button></li>`
            : '';
        errorsDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Errores encontrados:</strong>
            <ul class="mb-0 mt-2">${limitedList}${moreIndicator}</ul>
        `;
        if (remainingCount > 0) {
            const btn = document.getElementById('showAllErrorsBtn');
            if (btn) {
                btn.addEventListener('click', function() {
                    Swal.fire({
                        icon: 'info',
                        title: 'Todos los errores',
                        html: `
                            <div style="max-height: 320px; overflow-y: auto; text-align: left;">
                                <ul>
                                    ${excelProcessingErrors.map(e => `<li>${escapeHtml(e)}</li>`).join('')}
                                </ul>
                            </div>
                        `,
                        width: 700,
                        customClass: {
                            container: 'swal2-container-over-modal',
                            popup: 'swal2-popup-over-modal'
                        }
                    });
                });
            }
        }
    } else {
        errorsDiv.style.display = 'none';
    }
    
    // Mostrar tabla de previsualización
    tableBody.innerHTML = '';
    data.data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.row_index}</td>
            <td>${item.data.cedula || ''}</td>
            <td>${item.data.NombresCompletos || ''}</td>
            <td>${item.data.email || ''}</td>
            <td>${item.data.phone || ''}</td>
            <td>${item.data.edad || ''}</td>
        `;
        tableBody.appendChild(row);
    });
    
    // Mostrar botón de guardar solo si hay datos válidos
    if (data.valid_rows > 0) {
        saveBtn.style.display = 'block';
    } else {
        saveBtn.style.display = 'none';
    }
}

// Función para guardar participantes
function saveParticipants() {
    if (processedData.length === 0) {
        Swal.fire({
            icon: 'warning',
            title: 'No hay datos válidos',
            text: 'Por favor verifica los datos y vuelve a intentar.',
        });
        return;
    }

    Swal.fire({
        title: `¿Guardar participantes?`,
        text: `Se guardarán ${processedData.length} participantes.`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Sí, guardar',
        cancelButtonText: 'Cancelar',
        customClass: {
            container: 'swal2-container-over-modal',
            popup: 'swal2-popup-over-modal'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // Mostrar indicador de carga con título y mensaje personalizados
            Swal.fire({
                title: 'Guardando participantes...',
                html: 'Por favor espera mientras se guardan los participantes en la base de datos.',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                customClass: {
                    container: 'swal2-container-over-modal',
                    popup: 'swal2-popup-over-modal'
                },
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            const formData = new FormData();
            formData.append('participants_data', JSON.stringify(processedData));

            const modal = document.getElementById('loadExcelModal');
            const saveUrl = modal.getAttribute('data-save-url');

            fetch(saveUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                // Cerrar el loading
                Swal.close();
                
                if (data.success) {
                    let errorHtml = '';
                    if (data.errors.length > 0) {
                        const shownErrors = data.errors
                            .slice(0, 5)
                            .map(err => `<li>${escapeHtml(err)}</li>`) 
                            .join('');
                        const remainingCount = Math.max(0, data.errors.length - 5);
                        const moreErrors = remainingCount > 0 
                            ? `<li>...y ${remainingCount} errores más <button type="button" id="showAllSavedErrorsBtn" class="btn btn-link p-0 ms-1">Ver todos</button></li>`
                            : '';
                        errorHtml = `
                            <div class="mt-3 text-start">
                                <strong>Errores:</strong>
                                <ul>${shownErrors}${moreErrors}</ul>
                            </div>
                        `;
                    }

                    Swal.fire({
                        icon: 'success',
                        title: 'Participantes guardados',
                        html: `Se guardaron <strong>${data.created_count}</strong> participantes exitosamente.` + errorHtml,
                        confirmButtonText: 'Aceptar',
                        customClass: {
                            container: 'swal2-container-over-modal',
                            popup: 'swal2-popup-over-modal'
                        },
                        didOpen: () => {
                            const btn = document.getElementById('showAllSavedErrorsBtn');
                            if (btn) {
                                btn.addEventListener('click', function() {
                                    Swal.fire({
                                        icon: 'info',
                                        title: 'Todos los errores',
                                        html: `
                                            <div style="max-height: 320px; overflow-y: auto; text-align: left;">
                                                <ul>
                                                    ${data.errors.map(e => `<li>${escapeHtml(e)}</li>`).join('')}
                                                </ul>
                                            </div>
                                        `,
                                        width: 700,
                                        customClass: {
                                            container: 'swal2-container-over-modal',
                                            popup: 'swal2-popup-over-modal'
                                        }
                                    });
                                });
                            }
                        }
                    }).then(() => {
                        location.reload();
                    });

                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error al guardar',
                        text: data.error,
                        customClass: {
                            container: 'swal2-container-over-modal',
                            popup: 'swal2-popup-over-modal'
                        }
                    });
                }
            })
            .catch(error => {
                // Cerrar el loading
                Swal.close();
                
                console.error('Error:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error de red',
                    text: 'No se pudo guardar los participantes. Por favor intenta de nuevo.',
                    customClass: {
                        container: 'swal2-container-over-modal',
                        popup: 'swal2-popup-over-modal'
                    }
                });
            });
        }
    });
}

// Funciones para navegar entre pasos
function showStep1() {
    document.getElementById('step1').style.display = 'block';
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step3').style.display = 'none';
}

function showStep2() {
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'block';
    document.getElementById('step3').style.display = 'none';
}

function showStep3() {
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step3').style.display = 'block';
}

// Inicialización del modal cuando se carga el DOM
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('loadExcelModal');
    if (modal) {
        // Agregar token CSRF al modal
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        modal.querySelector('form').appendChild(csrfInput);
    }
}); 