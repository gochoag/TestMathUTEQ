document.addEventListener('DOMContentLoaded', function() {
    // Confirmación SOLO para iniciar nueva evaluación (primera vez o nuevo intento)
    document.querySelectorAll('.confirm-start-quiz').forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const quizTitle = this.getAttribute('data-quiz-title');
            const isRetry = this.getAttribute('data-is-retry') === 'true';
            const quizUrl = this.getAttribute('href');
            
            const title = isRetry ? '¿Iniciar nuevo intento?' : '¿Iniciar evaluación?';
            const text = isRetry ? 
                `¿Estás seguro de que deseas iniciar un nuevo intento de la evaluación "${quizTitle}"?` :
                `¿Estás seguro de que deseas iniciar la evaluación "${quizTitle}"?`;
            
            Swal.fire({
                title: title,
                text: text,
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#007bff',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sí, iniciar',
                cancelButtonText: 'Cancelar',
                reverseButtons: false,
                customClass: {
                    popup: 'swal-popup-quiz-confirm'
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    // Mostrar loading
                    Swal.fire({
                        title: 'Cargando evaluación...',
                        text: 'Por favor espera mientras se prepara la evaluación',
                        icon: 'info',
                        allowOutsideClick: false,
                        allowEscapeKey: false,
                        showConfirmButton: false,
                        didOpen: () => {
                            Swal.showLoading();
                        }
                    });
                    
                    // Redirigir después de un breve delay
                    setTimeout(() => {
                        window.location.href = quizUrl;
                    }, 1000);
                }
            });
        });
    });
});
