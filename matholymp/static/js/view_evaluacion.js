function copiarEnlace() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        showAppDialog({
            icon: 'success',
            title: 'Enlace copiado',
            text: 'El enlace ha sido copiado al portapapeles',
            timer: 1500,
            showConfirmButton: false
        });
    }).catch(() => {
        showAppDialog({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo copiar el enlace'
        });
    });
}
