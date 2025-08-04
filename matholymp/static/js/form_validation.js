/**
 * Form Validation Helper
 * Proporciona validación visual y limpieza automática para campos de formulario
 * 
 * Funcionalidades:
 * - Limpia espacios al perder el foco (blur)
 * - Limpia espacios al pegar contenido (paste)
 * - Convierte a minúsculas automáticamente (correos)
 * - Valida formato básico de campos
 * - Aplica clases visuales Bootstrap (is-valid/is-invalid)
 * - Previene envío de formularios con campos inválidos
 */

// Función para limpiar y normalizar input de correo
function cleanEmailInput(input) {
    if (!input) return;
    
    let value = input.value.trim().toLowerCase();
    input.value = value;
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(value);
    
    if (value && !isValid) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
    } else if (value && isValid) {
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
    } else {
        input.classList.remove('is-valid', 'is-invalid');
    }
    
    return value;
}

// Función para validar y limpiar input de cédula
function cleanCedulaInput(input) {
    if (!input) return;
    
    // Remover espacios y caracteres no numéricos
    let value = input.value.replace(/\D/g, '');
    input.value = value;
    
    const isValid = /^\d{10}$/.test(value);
    
    if (value && !isValid) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
    } else if (value && isValid) {
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
    } else {
        input.classList.remove('is-valid', 'is-invalid');
    }
    
    return value;
}

// Función para validar y limpiar input de teléfono
function cleanPhoneInput(input) {
    if (!input) return;
    
    // Remover espacios y caracteres no numéricos
    let value = input.value.replace(/\D/g, '');
    input.value = value;
    
    const isValid = /^\d{10}$/.test(value);
    
    if (value && !isValid) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
    } else if (value && isValid) {
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
    } else {
        input.classList.remove('is-valid', 'is-invalid');
    }
    
    return value;
}

// Función para validar un formulario completo
function validateForm(form) {
    if (!form) return false;
    
    let isValid = true;
    const invalidFields = [];
    
    // Validar correos electrónicos
    const emailInputs = form.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        const value = input.value.trim();
        if (value && !validateEmail(value)) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
            isValid = false;
            invalidFields.push(input);
        } else if (value && validateEmail(value)) {
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
        }
    });
    
    // Validar cédulas
    const cedulaInputs = form.querySelectorAll('input[name="cedula"]');
    cedulaInputs.forEach(input => {
        const value = input.value.replace(/\D/g, '');
        if (value && !validateCedula(value)) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
            isValid = false;
            invalidFields.push(input);
        } else if (value && validateCedula(value)) {
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
        }
    });
    
    // Validar teléfonos
    const phoneInputs = form.querySelectorAll('input[name="phone"], input[name="TelefonoInstitucional"], input[name="TelefonoRepresentante"], input[type="tel"]');
    phoneInputs.forEach(input => {
        const value = input.value.replace(/\D/g, '');
        if (value && !validatePhone(value)) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
            isValid = false;
            invalidFields.push(input);
        } else if (value && validatePhone(value)) {
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
        }
    });
    
    // Si hay campos inválidos, hacer scroll al primero y enfocar
    if (!isValid && invalidFields.length > 0) {
        const firstInvalidField = invalidFields[0];
        firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        firstInvalidField.focus();
    }
    
    return isValid;
}

// Función para inicializar la validación de todos los campos
function initializeFormValidation() {
    // Validación de correos electrónicos
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            cleanEmailInput(this);
        });
        
        input.addEventListener('paste', function() {
            setTimeout(() => {
                cleanEmailInput(this);
            }, 10);
        });
        
        input.addEventListener('input', function() {
            if (this.value !== this.value.trim()) {
                this.value = this.value.trim();
            }
        });
        
        input.addEventListener('change', function() {
            cleanEmailInput(this);
        });
    });
    
    // Validación de cédulas
    const cedulaInputs = document.querySelectorAll('input[name="cedula"]');
    cedulaInputs.forEach(input => {
        input.addEventListener('blur', function() {
            cleanCedulaInput(this);
        });
        
        input.addEventListener('paste', function() {
            setTimeout(() => {
                cleanCedulaInput(this);
            }, 10);
        });
        
        input.addEventListener('input', function() {
            // Solo permitir números
            this.value = this.value.replace(/\D/g, '');
            if (this.value.length > 10) {
                this.value = this.value.slice(0, 10);
            }
        });
        
        input.addEventListener('change', function() {
            cleanCedulaInput(this);
        });
    });
    
    // Validación de teléfonos (incluye phone, TelefonoInstitucional, TelefonoRepresentante)
    const phoneInputs = document.querySelectorAll('input[name="phone"], input[name="TelefonoInstitucional"], input[name="TelefonoRepresentante"], input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('blur', function() {
            cleanPhoneInput(this);
        });
        
        input.addEventListener('paste', function() {
            setTimeout(() => {
                cleanPhoneInput(this);
            }, 10);
        });
        
        input.addEventListener('input', function() {
            // Solo permitir números
            this.value = this.value.replace(/\D/g, '');
            if (this.value.length > 10) {
                this.value = this.value.slice(0, 10);
            }
        });
        
        input.addEventListener('change', function() {
            cleanPhoneInput(this);
        });
    });
    
    // Interceptar envío de formularios para validación previa
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Solo validar formularios que no sean de logout o similares
            if (!form.id || !form.id.includes('logout')) {
                if (!validateForm(this)) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            }
        });
    });
}

// Función para validar un correo específico
function validateEmail(email) {
    if (!email) return false;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email.trim().toLowerCase());
}

// Función para validar una cédula específica
function validateCedula(cedula) {
    if (!cedula) return false;
    return /^\d{10}$/.test(cedula.replace(/\D/g, ''));
}

// Función para validar un teléfono específico
function validatePhone(phone) {
    if (!phone) return false;
    return /^\d{10}$/.test(phone.replace(/\D/g, ''));
}

// Función para obtener el valor limpio de un input de correo
function getCleanEmailValue(input) {
    if (!input) return '';
    return cleanEmailInput(input);
}

// Función para obtener el valor limpio de un input de cédula
function getCleanCedulaValue(input) {
    if (!input) return '';
    return cleanCedulaInput(input);
}

// Función para obtener el valor limpio de un input de teléfono
function getCleanPhoneValue(input) {
    if (!input) return '';
    return cleanPhoneInput(input);
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeFormValidation();
});

// También inicializar para contenido dinámico (modales, etc.)
document.addEventListener('shown.bs.modal', function() {
    initializeFormValidation();
});

// Exportar funciones para uso global
window.FormValidation = {
    cleanEmailInput,
    cleanCedulaInput,
    cleanPhoneInput,
    validateForm,
    initializeFormValidation,
    validateEmail,
    validateCedula,
    validatePhone,
    getCleanEmailValue,
    getCleanCedulaValue,
    getCleanPhoneValue
}; 