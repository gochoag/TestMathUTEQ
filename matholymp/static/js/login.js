function togglePassword() {
    const passwordInput = document.getElementById('id_password');
    const eyeIcon = document.querySelector('.login-eye-icon i');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        eyeIcon.classList.remove('bi-eye');
        eyeIcon.classList.add('bi-eye-slash');
    } else {
        passwordInput.type = 'password';
        eyeIcon.classList.remove('bi-eye-slash');
        eyeIcon.classList.add('bi-eye');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const usernameInput = document.getElementById('id_username');
    if (usernameInput && !usernameInput.value) {
        usernameInput.focus();
    }
});
