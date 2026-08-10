document.getElementById('editEvaluacionForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const form = this;
    const saveUrl = form.dataset.saveUrl;
    const redirectUrl = form.dataset.redirectUrl;

    const title = document.getElementById('evaluacionTitle').value.trim();
    const duration = document.getElementById('evaluacionDuration').value;
    const startDate = document.getElementById('evaluacionStartDate').value;
    const startTime = document.getElementById('evaluacionStartTime').value;
    const endDate = document.getElementById('evaluacionEndDate').value;
    const endTime = document.getElementById('evaluacionEndTime').value;

    if (!title || !duration || !startDate || !startTime || !endDate || !endTime) {
        Swal.fire({
            icon: 'error',
            title: 'Campos requeridos',
            text: 'Por favor, completa todos los campos obligatorios.'
        });
        return;
    }

    if (duration < 1 || duration > 480) {
        Swal.fire({
            icon: 'error',
            title: 'Duracion invalida',
            text: 'La duracion debe estar entre 1 y 480 minutos.'
        });
        return;
    }

    const startDateTime = new Date(`${startDate} ${startTime}`);
    const endDateTime = new Date(`${endDate} ${endTime}`);

    if (startDateTime >= endDateTime) {
        Swal.fire({
            icon: 'error',
            title: 'Fechas invalidas',
            text: 'La fecha de inicio debe ser anterior a la fecha de finalizacion.'
        });
        return;
    }

    Swal.fire({
        title: 'Guardando...',
        text: 'Por favor espera',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    fetch(saveUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            title: title,
            duration: duration,
            start_date: startDate,
            start_time: startTime,
            end_date: endDate,
            end_time: endTime
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: '¡Guardado!',
                text: 'La evaluacion ha sido actualizada exitosamente',
                timer: 1500,
                showConfirmButton: false
            }).then(() => {
                window.location.href = redirectUrl;
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.error || 'Error al actualizar la evaluacion'
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error de conexion al actualizar la evaluacion'
        });
    });
});

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
