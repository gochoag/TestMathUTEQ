document.addEventListener('DOMContentLoaded', function () {
    const btnSolicitarClave = document.getElementById('btnSolicitarClave');
    const formClaveTemporal = document.getElementById('formClaveTemporal');
    const usernameInput = document.getElementById('username');
    
    if (!btnSolicitarClave) return;
    const url = btnSolicitarClave.dataset.url;

    btnSolicitarClave.addEventListener('click', function () {
        const username = usernameInput ? usernameInput.value.trim() : '';

        if (!username) {
            Swal.fire({
                icon: 'warning',
                title: 'Campo requerido',
                text: 'Por favor, ingrese su nombre de usuario.',
                confirmButtonColor: '#00923f'
            });
            return;
        }

        Swal.fire({
            icon: 'question',
            title: 'Confirmar solicitud',
            text: `¿Está seguro de que "${username}" es su usuario correcto? Se enviará una nueva contraseña a su correo electrónico.`,
            showCancelButton: true,
            confirmButtonText: 'Sí, enviar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#00923f',
            cancelButtonColor: '#6c757d'
        }).then((result) => {
            if (result.isConfirmed) {
                solicitarClaveTemporal(username);
            }
        });
    });

    function solicitarClaveTemporal(username) {
        Swal.fire({
            title: 'Procesando solicitud...',
            text: 'Verificando usuario y enviando correo...',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                username: username
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: '¡Solicitud enviada!',
                    text: data.message,
                    confirmButtonColor: '#28a745'
                }).then(() => {
                    const modalEl = document.getElementById('modalClaveTemporal');
                    if (modalEl) {
                        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                        modal.hide();
                    }
                    if (formClaveTemporal) {
                        formClaveTemporal.reset();
                    }
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message,
                    confirmButtonColor: '#dc3545'
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error de conexión',
                text: 'Ha ocurrido un error al procesar su solicitud. Por favor, intente nuevamente.',
                confirmButtonColor: '#dc3545'
            });
        });
    }

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
});
