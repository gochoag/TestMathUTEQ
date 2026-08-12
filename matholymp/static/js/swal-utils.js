/* Configuración global de SweetAlert2 para EVAUTEQ. */
(function configureEvaSwal() {
    if (!window.Swal) {
        return;
    }

    const baseSwal = window.Swal;
    const appSwal = baseSwal.mixin({
        confirmButtonColor: '#087c3f',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Continuar',
        cancelButtonText: 'Cancelar',
        reverseButtons: false,
        focusCancel: true,
        customClass: {
            popup: 'eva-swal-popup',
            title: 'eva-swal-title',
            htmlContainer: 'eva-swal-content',
            confirmButton: 'eva-swal-confirm',
            cancelButton: 'eva-swal-cancel',
        },
    });

    // Mantiene disponibles los métodos estáticos usados por módulos antiguos.
    [
        'close',
        'showLoading',
        'isLoading',
        'showValidationMessage',
        'resetValidationMessage',
    ].forEach((method) => {
        if (typeof appSwal[method] !== 'function' && typeof baseSwal[method] === 'function') {
            appSwal[method] = baseSwal[method].bind(baseSwal);
        }
    });

    // Compatibilidad: todos los Swal.fire existentes heredan este tema global.
    window.Swal = appSwal;

    // Punto de entrada para avisos personalizados que no encajan en un helper semántico.
    window.showAppDialog = function showAppDialog(...args) {
        return appSwal.fire(...args);
    };

    window.closeAppDialog = function closeAppDialog() {
        return appSwal.close();
    };

    window.showAppLoader = function showAppLoader() {
        return appSwal.showLoading();
    };

    window.isAppLoading = function isAppLoading() {
        return appSwal.isLoading();
    };

    window.showAppLoading = function showAppLoading(options = {}) {
        const { didOpen, ...alertOptions } = options;
        return appSwal.fire({
            title: 'Procesando…',
            text: 'Espere un momento.',
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            ...alertOptions,
            didOpen: () => {
                appSwal.showLoading();
                if (typeof didOpen === 'function') {
                    didOpen();
                }
            },
        });
    };

    window.showAppSuccess = function showAppSuccess(options = {}) {
        return appSwal.fire({
            icon: 'success',
            title: 'Operación completada',
            confirmButtonText: 'Entendido',
            ...options,
        });
    };

    window.showAppError = function showAppError(options = {}) {
        return appSwal.fire({
            icon: 'error',
            title: 'No se pudo completar la acción',
            confirmButtonColor: '#c93c3c',
            confirmButtonText: 'Entendido',
            ...options,
        });
    };

    window.showAppWarning = function showAppWarning(options = {}) {
        return appSwal.fire({
            icon: 'warning',
            title: 'Revisa la información',
            confirmButtonText: 'Entendido',
            ...options,
        });
    };

    // Variante amplia para mensajes con información detallada o contenido HTML.
    window.showAppWideAlert = function showAppWideAlert(options = {}) {
        return appSwal.fire({
            width: 'min(37.5rem, calc(100vw - 2rem))',
            ...options,
        });
    };

    window.showAppValidationMessage = function showAppValidationMessage(message) {
        appSwal.showValidationMessage(message);
    };

    // Confirmación estándar para guardar, enviar, iniciar o cambiar estados.
    window.confirmAppAction = function confirmAppAction(options = {}) {
        return appSwal.fire({
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Continuar',
            cancelButtonText: 'Cancelar',
            ...options,
        });
    };

    // Variante para operaciones irreversibles, con una señal visual de riesgo.
    window.confirmDestructiveAction = function confirmDestructiveAction(options = {}) {
        return window.confirmAppAction({
            icon: 'warning',
            confirmButtonColor: '#c93c3c',
            confirmButtonText: 'Sí, eliminar',
            ...options,
        });
    };
}());
