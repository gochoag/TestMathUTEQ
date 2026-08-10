function confirmDeleteAdmin(id, username) {
    const requiredText = `ELIMINAR ${username}`;
    Swal.fire({
        title: '⚠️ Confirmaci\u00f3n Cr\u00edtica de Borrado',
        html: `
            <div class="text-start">
                <p class="mb-2">Est\u00e1s a punto de eliminar de forma permanente al administrador <strong class="text-dark">${username}</strong>.</p>
                <p class="text-danger small mb-2">Para confirmar esta acci\u00f3n imborrable, escribe exactamente la siguiente frase en la caja de texto:</p>
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
            autocomplete: 'off'
        },
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'S\u00ed, eliminar de forma permanente',
        confirmButtonColor: '#dc3545',
        cancelButtonText: 'Cancelar',
        reverseButtons: false,
        preConfirm: (inputValue) => {
            if (inputValue.trim() !== requiredText) {
                Swal.showValidationMessage(`Debes escribir exactamente "${requiredText}" para proceder.`);
                return false;
            }
            return true;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = '?delete_id=' + id;
        }
    });
}

function confirmSendCredentials(id, nombre, sendUrl) {
    Swal.fire({
        title: '\u00bfEnviar credenciales?',
        html: `\u00bfEst\u00e1s seguro de que quieres enviar las credenciales de acceso por correo al administrador <strong>${nombre}</strong>?`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'S\u00ed, enviar',
        cancelButtonText: 'Cancelar',
        reverseButtons: false
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'Enviando credenciales...',
                html: 'Por favor espera mientras se env\u00edan las credenciales por correo electr\u00f3nico.',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            fetch(sendUrl.replace('0', id), {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Error en la respuesta del servidor');
            })
            .then(data => {
                Swal.close();

                if (data.success) {
                    showDynamicToast({
                        type: 'success',
                        title: '\u00c9xito',
                        message: data.message
                    });
                } else {
                    showDynamicToast({
                        type: 'danger',
                        title: 'Error',
                        message: data.message
                    });
                }
            })
            .catch(error => {
                Swal.close();

                console.error('Error:', error);
                showDynamicToast({
                    type: 'danger',
                    title: 'Error',
                    message: 'Hubo un error al enviar las credenciales. Por favor, intenta de nuevo.'
                });
            });
        }
    });
}
