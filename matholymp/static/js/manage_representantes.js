function confirmDeleteRepresentante(id, nombre) {
    Swal.fire({
        title: '¿Eliminar representante?',
        html: `¿Estás seguro de que quieres eliminar al representante <strong>${nombre}</strong>?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        reverseButtons: false
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = '?delete_id=' + id;
        }
    });
}
