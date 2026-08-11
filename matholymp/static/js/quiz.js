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
            
            confirmAppAction({
                title: title,
                text: text,
                confirmButtonText: 'Sí, iniciar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Mostrar loading
                    showAppLoading({
                        title: 'Cargando evaluación...',
                        text: 'Por favor espera mientras se prepara la evaluación',
                        icon: 'info',
                        allowOutsideClick: false,
                        allowEscapeKey: false,
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
