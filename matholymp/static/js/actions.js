// Sidebar toggle desde el header
function hideSidebarOnMobile() {
  const sidebar = document.getElementById("sidebar");
  if (window.innerWidth < 992 && sidebar) {
    sidebar.classList.remove("show");
    document.body.classList.remove("sidebar-expanded");
  }
}
document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("sidebar");
  const toggleBtnHeader = document.getElementById("sidebarToggleBtnHeader");

  if (!sidebar || !toggleBtnHeader) {
    return;
  }

  toggleBtnHeader.addEventListener("click", function () {
    if (window.innerWidth >= 992) {
      document.body.classList.toggle("sidebar-collapsed");
      return;
    }

    sidebar.classList.toggle("show");
    document.body.classList.toggle("sidebar-expanded");
  });

  window.addEventListener("resize", function () {
    if (window.innerWidth >= 992) {
      sidebar.classList.remove("show");
      document.body.classList.remove("sidebar-expanded");
    }
  });
});

// Confirmación SweetAlert2 para cerrar sesión
function confirmLogout(e) {
  e.preventDefault();
  confirmAppAction({
    title: "¿Estás seguro?",
    text: "Estás a punto de cerrar sesión",
    icon: "warning",
    confirmButtonText: "Sí, cerrar sesión",
    cancelButtonText: "Cancelar",
  }).then((result) => {
    if (result.isConfirmed) {
      document.getElementById("logoutForm").submit();
    }
  });
}

// Mostrar/ocultar contraseña en login
function togglePassword() {
  const passwordField = document.getElementById("id_password");
  const eyeIcon = document.querySelector(".login-eye-icon i");
  if (passwordField.type === "password") {
    passwordField.type = "text";
    eyeIcon.classList.remove("bi-eye");
    eyeIcon.classList.add("bi-eye-slash");
  } else {
    passwordField.type = "password";
    eyeIcon.classList.remove("bi-eye-slash");
    eyeIcon.classList.add("bi-eye");
  }
}
