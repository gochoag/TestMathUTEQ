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

// Sidebar toggle desde el header
function hideSidebarOnMobile() {
  if(window.innerWidth < 992) {
    document.getElementById('sidebar').classList.remove('show');
    document.body.classList.remove('sidebar-expanded');
  }
}
document.addEventListener('DOMContentLoaded', function() {
  const sidebar = document.getElementById('sidebar');
  const toggleBtnHeader = document.getElementById('sidebarToggleBtnHeader');
  if(toggleBtnHeader) {
    toggleBtnHeader.addEventListener('click', function() {
      sidebar.classList.toggle('show');
      document.body.classList.toggle('sidebar-expanded');
    });
  }
});

// Confirmación SweetAlert2 para cerrar sesión
function confirmLogout(e) {
  e.preventDefault();
  Swal.fire({
    title: '¿Estás seguro?',
    text: 'Estás a punto de cerrar sesión',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#3085d6',
    cancelButtonColor: '#d33',
    confirmButtonText: 'Sí, cerrar sesión',
    cancelButtonText: 'Cancelar'
  }).then((result) => {
    if (result.isConfirmed) {
      document.getElementById('logoutForm').submit();
    }
  });
}

// Mostrar/ocultar contraseña en login
function togglePassword() {
    const passwordField = document.getElementById('id_password');
    const eyeIcon = document.querySelector('.login-eye-icon i');
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        eyeIcon.classList.remove('bi-eye');
        eyeIcon.classList.add('bi-eye-slash');
    } else {
        passwordField.type = 'password';
        eyeIcon.classList.remove('bi-eye-slash');
        eyeIcon.classList.add('bi-eye');
    }
}
