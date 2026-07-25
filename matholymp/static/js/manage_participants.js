function confirmDelete(id, nombre) {
    Swal.fire({
        title: '\u00bfEliminar participante?',
        html: `\u00bfEst\u00e1s seguro de que quieres eliminar al participante <strong>${nombre}</strong>?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'S\u00ed, eliminar',
        cancelButtonText: 'Cancelar',
        reverseButtons: false
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = '?delete_id=' + id;
        }
    });
}

function confirmSendCredentials(id, nombre, sendUrl) {
    Swal.fire({
        title: '\u00bfEnviar credenciales?',
        html: `\u00bfEst\u00e1s seguro de que quieres enviar las credenciales de acceso por correo al participante <strong>${nombre}</strong>?`,
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
