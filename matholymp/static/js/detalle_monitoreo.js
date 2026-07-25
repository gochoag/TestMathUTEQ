document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('detalle-monitoreo-container');
    if (!container) return;

    const monitoreoId = parseInt(container.dataset.monitoreoId, 10);
    const evaluacionId = parseInt(container.dataset.evaluacionId, 10);

    const btnConfirmarAlerta = document.getElementById('btn-confirmar-alerta-manual');
    if (btnConfirmarAlerta) {
        btnConfirmarAlerta.addEventListener('click', function () {
            const tipoAlerta = document.getElementById('tipo-alerta-manual').value;
            const severidad = document.getElementById('severidad-alerta-manual').value;
            const descripcion = document.getElementById('descripcion-alerta-manual').value;

            if (!descripcion.trim()) {
                showDynamicToast({
                    type: 'warning',
                    title: 'Advertencia',
                    message: 'Por favor, ingrese una descripción para la alerta.'
                });
                return;
            }

            fetch(`/quizzes/monitoreo/${monitoreoId}/alerta/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    tipo_alerta: tipoAlerta,
                    severidad: severidad,
                    descripcion: descripcion
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const modalEl = document.getElementById('modalAlertaManual');
                    if (modalEl) {
                        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                        modal.hide();
                    }
                    location.reload();
                } else {
                    showDynamicToast({
                        type: 'danger',
                        title: 'Error',
                        message: 'Error: ' + data.error
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showDynamicToast({
                    type: 'danger',
                    title: 'Error',
                    message: 'Error al agregar la alerta'
                });
            });
        });
    }

    const btnConfirmarFinalizar = document.getElementById('btn-confirmar-finalizar-manual');
    if (btnConfirmarFinalizar) {
        btnConfirmarFinalizar.addEventListener('click', function () {
            const motivo = document.getElementById('motivo-finalizacion-manual').value;
            if (!motivo.trim()) {
                showDynamicToast({
                    type: 'warning',
                    title: 'Advertencia',
                    message: 'Por favor, ingrese un motivo para la finalización.'
                });
                return;
            }

            fetch(`/evaluacion/${evaluacionId}/monitoreo/finalizar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    monitoreo_id: monitoreoId,
                    motivo: motivo
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const modalEl = document.getElementById('modalFinalizarManual');
                    if (modalEl) {
                        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                        modal.hide();
                    }
                    location.reload();
                } else {
                    showDynamicToast({
                        type: 'danger',
                        title: 'Error',
                        message: 'Error: ' + data.error
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showDynamicToast({
                    type: 'danger',
                    title: 'Error',
                    message: 'Error al finalizar la evaluación'
                });
            });
        });
    }
});

function agregarAlertaManual() {
    const tipo = document.getElementById('tipo-alerta-manual');
    const severidad = document.getElementById('severidad-alerta-manual');
    const descripcion = document.getElementById('descripcion-alerta-manual');

    if (tipo) tipo.value = 'comportamiento';
    if (severidad) severidad.value = 'media';
    if (descripcion) descripcion.value = '';

    const modalEl = document.getElementById('modalAlertaManual');
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
    }
}

function finalizarEvaluacionManual() {
    const motivo = document.getElementById('motivo-finalizacion-manual');
    if (motivo) motivo.value = '';

    const modalEl = document.getElementById('modalFinalizarManual');
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
    }
}
