function togglePassword() {
    const passwordInput = document.getElementById('id_password');
    const eyeIcon = document.querySelector('.login-eye-icon i');
    const toggleButton = document.querySelector('.login-eye-icon');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        eyeIcon.classList.remove('bi-eye');
        eyeIcon.classList.add('bi-eye-slash');
        toggleButton.setAttribute('aria-label', 'Ocultar contraseña');
        toggleButton.setAttribute('aria-pressed', 'true');
    } else {
        passwordInput.type = 'password';
        eyeIcon.classList.remove('bi-eye-slash');
        eyeIcon.classList.add('bi-eye');
        toggleButton.setAttribute('aria-label', 'Mostrar contraseña');
        toggleButton.setAttribute('aria-pressed', 'false');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const usernameInput = document.getElementById('id_username');
    if (usernameInput && !usernameInput.value) {
        usernameInput.focus();
    }
});



document.getElementById("anio-actual").textContent = new Date().getFullYear();
