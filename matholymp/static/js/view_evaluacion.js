function copiarEnlace() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        Swal.fire({
            icon: 'success',
            title: 'Enlace copiado',
            text: 'El enlace ha sido copiado al portapapeles',
            timer: 1500,
            showConfirmButton: false
        });
    }).catch(() => {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo copiar el enlace'
        });
    });
}
