document.addEventListener('DOMContentLoaded', function () {
    const btnSolicitarClave = document.getElementById('btnSolicitarClave');
    const formClaveTemporal = document.getElementById('formClaveTemporal');
    const usernameInput = document.getElementById('username');
    
    if (!btnSolicitarClave) return;
    const url = btnSolicitarClave.dataset.url;

    btnSolicitarClave.addEventListener('click', function () {
        const username = usernameInput ? usernameInput.value.trim() : '';

        if (!username) {
            showAppWarning({
                title: 'Campo requerido',
                text: 'Por favor, ingrese su nombre de usuario.'
            });
            return;
        }

        confirmAppAction({
            title: 'Confirmar solicitud',
            text: `¿Está seguro de que "${username}" es su usuario correcto? Se enviará una nueva contraseña a su correo electrónico.`,
            confirmButtonText: 'Sí, enviar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                solicitarClaveTemporal(username);
            }
        });
    });

    function solicitarClaveTemporal(username) {
        showAppLoading({
            title: 'Procesando solicitud...',
            text: 'Verificando usuario y enviando correo...',
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
                showAppSuccess({
                    title: '¡Solicitud enviada!',
                    text: data.message
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
                showAppError({
                    title: 'No se pudo procesar la solicitud',
                    text: data.message
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAppError({
                title: 'Error de conexión',
                text: 'Ha ocurrido un error al procesar su solicitud. Por favor, intente nuevamente.'
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
