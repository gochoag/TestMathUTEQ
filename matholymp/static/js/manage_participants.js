function confirmDelete(id, nombre) {
    confirmDestructiveAction({
        title: '¿Eliminar participante?',
        html: `¿Estás seguro de que quieres eliminar al participante <strong>${nombre}</strong>?`,
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = `?delete_id=${id}`;
        }
    });
}

function confirmSendCredentials(id, nombre, sendUrl) {
    confirmAppAction({
        title: '¿Enviar credenciales?',
        html: `¿Estás seguro de que quieres enviar las credenciales de acceso por correo al participante <strong>${nombre}</strong>?`,
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
