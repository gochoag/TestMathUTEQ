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
            e.preventDefault(); // Siempre prevenir el envío normal del formulario
            const formData = new FormData(this);
            
            // Agregar explícitamente el campo update_profile con un valor
            formData.set('update_profile', 'true');
             
             // Mostrar indicador de carga
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Actualizando...';
            submitButton.disabled = true;
            
            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                // Verificar si la respuesta es JSON
                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/json')) {
                    return response.json().then(data => {
                        // Si el status no es ok, lanzar error con los datos JSON
                        if (!response.ok) {
                            const error = new Error(data.message || `HTTP error! status: ${response.status}`);
                            error.status = response.status;
                            error.data = data;
                            throw error;
                        }
                        return data;
                    });
                } else {
                    // Si no es JSON, lanzar error
                    return response.text().then(text => {
                        throw new Error('La respuesta del servidor no es JSON válido');
                    });
                }
            })
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
                } else {
                    // Verificar si la sesión ha expirado
                    if (data.session_expired) {
                        Swal.fire({
                            icon: 'warning',
                            title: 'Sesión Expirada',
                            text: data.message,
                            confirmButtonText: 'Recargar Página'
                        }).then((result) => {
                            if (result.isConfirmed) {
                                window.location.reload();
                            }
                        });
                    } else {
                        // Mostrar mensaje de error del servidor
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: data.message || 'Hubo un error al actualizar el perfil.'
                        });
                    }
                }
            })
            .catch(error => {
                let errorMessage = 'Hubo un error al actualizar el perfil. Por favor, intenta de nuevo.';
                let icon = 'error';
                
                // Verificar si es un error de sesión expirada
                if (error.data && error.data.session_expired) {
                    errorMessage = error.data.message;
                    icon = 'warning';
                    
                    Swal.fire({
                        icon: icon,
                        title: 'Sesión Expirada',
                        text: errorMessage,
                        confirmButtonText: 'Recargar Página'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            window.location.reload();
                        }
                    });
                    return;
                }
                
                if (error.message.includes('JSON')) {
                    errorMessage = 'Error en la respuesta del servidor. Por favor, recarga la página e intenta de nuevo.';
                } else if (error.message.includes('HTTP error')) {
                    errorMessage = 'Error de conexión con el servidor. Verifica tu conexión e intenta de nuevo.';
                } else if (error.message.includes('Failed to fetch')) {
                    errorMessage = 'Error de conexión. Verifica tu conexión a internet e intenta de nuevo.';
                }
                
                Swal.fire({
                    icon: icon,
                    title: 'Error',
                    text: errorMessage
                });
            })
            .finally(() => {
                // Restaurar el botón
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
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
        
        // Manejar envío del formulario de cambio de contraseña
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
        
        // Confirmar cambio de contraseña con AJAX
        document.getElementById('confirmPasswordChange').addEventListener('click', function() {
            const formData = new FormData(passwordForm);
            
            // Agregar explícitamente el campo change_password con un valor
            formData.set('change_password', 'true');
            
            // Mostrar indicador de carga
            const submitButton = this;
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Cambiando...';
            submitButton.disabled = true;
            
            // Cerrar el modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('passwordModal'));
            modal.hide();
            
            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                // Verificar si la respuesta es JSON
                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/json')) {
                    return response.json().then(data => {
                        // Si el status no es ok, lanzar error con los datos JSON
                        if (!response.ok) {
                            const error = new Error(data.message || `HTTP error! status: ${response.status}`);
                            error.status = response.status;
                            error.data = data;
                            throw error;
                        }
                        return data;
                    });
                } else {
                    // Si no es JSON, lanzar error
                    return response.text().then(text => {
                        throw new Error('La respuesta del servidor no es JSON válido');
                    });
                }
            })
            .then(data => {
                if (data.success) {
                    // Mostrar mensaje de éxito
                    Swal.fire({
                        icon: 'success',
                        title: '¡Éxito!',
                        text: data.message,
                        confirmButtonText: 'OK'
                    }).then((result) => {
                        // Limpiar el formulario
                        passwordForm.reset();
                        
                        // Hacer logout (automáticamente redirige al login)
                        window.location.href = '/logout/';
                    });
                } else {
                    // Verificar si la sesión ha expirado
                    if (data.session_expired) {
                        Swal.fire({
                            icon: 'warning',
                            title: 'Sesión Expirada',
                            text: data.message,
                            confirmButtonText: 'Recargar Página'
                        }).then((result) => {
                            if (result.isConfirmed) {
                                window.location.reload();
                            }
                        });
                    } else {
                        // Mostrar mensaje de error del servidor
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: data.message || 'Hubo un error al cambiar la contraseña.'
                        });
                    }
                }
            })
            .catch(error => {
                let errorMessage = 'Hubo un error al cambiar la contraseña. Por favor, intenta de nuevo.';
                let icon = 'error';
                
                // Verificar si es un error de sesión expirada
                if (error.data && error.data.session_expired) {
                    errorMessage = error.data.message;
                    icon = 'warning';
                    
                    Swal.fire({
                        icon: icon,
                        title: 'Sesión Expirada',
                        text: errorMessage,
                        confirmButtonText: 'Recargar Página'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            window.location.reload();
                        }
                    });
                    return;
                }
                
                if (error.message.includes('JSON')) {
                    errorMessage = 'Error en la respuesta del servidor. Por favor, recarga la página e intenta de nuevo.';
                } else if (error.message.includes('HTTP error')) {
                    errorMessage = 'Error de conexión con el servidor. Verifica tu conexión e intenta de nuevo.';
                } else if (error.message.includes('Failed to fetch')) {
                    errorMessage = 'Error de conexión. Verifica tu conexión a internet e intenta de nuevo.';
                }
                
                Swal.fire({
                    icon: icon,
                    title: 'Error',
                    text: errorMessage
                });
            })
            .finally(() => {
                // Restaurar el botón
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
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