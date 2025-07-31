// Funcionalidad específica para la página de perfil
document.addEventListener('DOMContentLoaded', function() {
    // Preview de imagen
    const avatarInput = document.getElementById('avatar');
    const avatarPreview = document.querySelector('.avatar-preview img');
    const avatarPlaceholder = document.querySelector('.avatar-preview .bg-light');
    
    // Manejar envío del formulario de perfil
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            const formData = new FormData(this);
            
            // Si hay un archivo de avatar, usar AJAX para actualizar
            if (avatarInput && avatarInput.files.length > 0) {
                e.preventDefault();
                
                fetch(window.location.href, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Actualizar avatar en el sidebar
                        updateSidebarAvatar(data.avatar_url);
                        
                        // Mostrar mensaje de éxito
                        Swal.fire({
                            icon: 'success',
                            title: '¡Éxito!',
                            text: data.message,
                            timer: 2000,
                            showConfirmButton: false
                        });
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Hubo un error al actualizar el perfil.'
                    });
                });
            }
        });
    }
    
    // Función para actualizar el avatar en el sidebar
    function updateSidebarAvatar(avatarUrl) {
        const sidebarAvatar = document.querySelector('.sidebar-user img');
        const sidebarIcon = document.querySelector('.sidebar-user .bi-person-circle');
        
        if (avatarUrl) {
            if (sidebarAvatar) {
                sidebarAvatar.src = avatarUrl;
            } else if (sidebarIcon) {
                sidebarIcon.parentElement.innerHTML = `<img src="${avatarUrl}" alt="avatar" width="36" height="36" class="rounded-circle me-2">`;
            }
        }
    }
    
    // Preview de imagen cuando se selecciona un archivo
    if (avatarInput) {
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Validar tamaño (5MB)
                if (file.size > 5 * 1024 * 1024) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Archivo demasiado grande',
                        text: 'El archivo es demasiado grande. El tamaño máximo es 5MB.'
                    });
                    this.value = '';
                    return;
                }
                
                // Validar tipo
                if (!file.type.startsWith('image/')) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Tipo de archivo no válido',
                        text: 'Por favor selecciona un archivo de imagen válido.'
                    });
                    this.value = '';
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    if (avatarPreview) {
                        avatarPreview.src = e.target.result;
                    } else if (avatarPlaceholder) {
                        avatarPlaceholder.innerHTML = `<img src="${e.target.result}" alt="Avatar" class="rounded-circle img-thumbnail" style="width: 150px; height: 150px; object-fit: cover;">`;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Validación de contraseñas
    const passwordForm = document.getElementById('passwordForm');
    const newPassword = document.getElementById('new_password');
    const confirmPassword = document.getElementById('confirm_password');
    
    if (passwordForm && newPassword && confirmPassword) {
        function validatePasswords() {
            if (newPassword.value !== confirmPassword.value) {
                confirmPassword.setCustomValidity('Las contraseñas no coinciden');
            } else {
                confirmPassword.setCustomValidity('');
            }
        }
        
        newPassword.addEventListener('input', validatePasswords);
        confirmPassword.addEventListener('input', validatePasswords);
        
        // Confirmación de cambio de contraseña
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (newPassword.value !== confirmPassword.value) {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Las contraseñas no coinciden'
                });
                return;
            }
            
            // Mostrar modal de confirmación
            const modal = new bootstrap.Modal(document.getElementById('passwordModal'));
            modal.show();
        });
        
        document.getElementById('confirmPasswordChange').addEventListener('click', function() {
            passwordForm.submit();
        });
    }
    
    // Validación de teléfono
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            // Solo permitir números
            this.value = this.value.replace(/\D/g, '');
            
            // Limitar a 10 dígitos
            if (this.value.length > 10) {
                this.value = this.value.slice(0, 10);
            }
        });
    }
    
    // Animaciones de entrada
    const profileCards = document.querySelectorAll('.profile-card');
    profileCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
}); 