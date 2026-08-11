function confirmDeleteRepresentante(id, nombre) {
    confirmDestructiveAction({
        title: '¿Eliminar representante?',
        html: `¿Estás seguro de que quieres eliminar al representante <strong>${nombre}</strong>?`,
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = '?delete_id=' + id;
        }
    });
}
