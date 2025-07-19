function confirmDelete(id, nombre) {
    Swal.fire({
        title: '¿Eliminar participante?',
        text: nombre,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = '/gestionar-participantes/?delete_id=' + id;
        }
    })
}

function confirmDeleteAdmin(id, nombre) {
    Swal.fire({
        title: '¿Eliminar administrador?',
        text: nombre,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = '/gestionar-admins/?delete_id=' + id;
        }
    })
}
