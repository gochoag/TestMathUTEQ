/**
 * JavaScript para la página de gestión de permisos de administradores
 * manage_admin_permissions.js
 *
 * Maneja la confirmación con SweetAlert2 antes de habilitar/deshabilitar
 * el acceso total de un administrador.
 */

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.btn-swal-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const form     = btn.closest('form');
            const username = btn.dataset.username;
            const action   = btn.textContent.trim(); // "Habilitar" o "Deshabilitar"

            Swal.fire({
                title: `¿Seguro que quieres ${action.toLowerCase()}?`,
                text: `Control de acceso para ${username}`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, adelante',
                cancelButtonText: 'Cancelar',
            }).then((result) => {
                if (result.isConfirmed) {
                    form.submit();
                }
            });
        });
    });
});
