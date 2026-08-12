function confirmDeleteAdmin(id, username) {
    const requiredText = `ELIMINAR ${username}`;

    confirmDestructiveAction({
        title: '⚠️ Confirmación crítica de borrado',
        html: `
            <div class="text-start">
                <p class="mb-2">Estás a punto de eliminar de forma permanente al administrador <strong class="text-dark">${username}</strong>.</p>
                <p class="text-danger small mb-2">Para confirmar esta acción imborrable, escribe exactamente la siguiente frase en la caja de texto:</p>
                <div class="p-2 bg-light rounded text-center font-monospace fw-bold user-select-all mb-3 text-danger border border-danger">
                    ${requiredText}
                </div>
            </div>
        `,
        input: 'text',
        inputPlaceholder: `Escribe "${requiredText}"`,
        inputAttributes: {
            autocapitalize: 'off',
            autocorrect: 'off',
            autocomplete: 'off',
        },
        confirmButtonText: 'Sí, eliminar de forma permanente',
        cancelButtonText: 'Cancelar',
        preConfirm: (inputValue) => {
            if (inputValue.trim() !== requiredText) {
                showAppValidationMessage(`Debes escribir exactamente "${requiredText}" para proceder.`);
                return false;
            }
            return true;
        },
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = `?delete_id=${id}`;
        }
    });
}

function confirmSendCredentials(id, nombre, sendUrl) {
    confirmAppAction({
        title: '¿Enviar credenciales?',
        html: `¿Estás seguro de que quieres enviar las credenciales de acceso por correo al administrador <strong>${nombre}</strong>?`,
        confirmButtonText: 'Sí, enviar',
        cancelButtonText: 'Cancelar',
    }).then((result) => {
        if (!result.isConfirmed) {
            return;
        }

        showAppLoading({
            title: 'Enviando credenciales…',
            html: 'Por favor espera mientras se envían las credenciales por correo electrónico.',
        });

        fetch(sendUrl.replace('0', id), {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
            .then((response) => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Error en la respuesta del servidor');
            })
            .then((data) => {
                if (data.success) {
                    return showAppSuccess({
                        title: 'Credenciales enviadas',
                        text: data.message,
                    });
                }

                return showAppError({
                    title: 'No se enviaron las credenciales',
                    text: data.message,
                });
            })
            .catch((error) => {
                console.error('Error:', error);
                showAppError({
                    title: 'Error de conexión',
                    text: 'Hubo un error al enviar las credenciales. Por favor, intenta de nuevo.',
                });
            });
    });
}
