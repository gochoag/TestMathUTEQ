// Inicializa todos los toasts
document.addEventListener('DOMContentLoaded', function() {
    const toasts = [].slice.call(document.querySelectorAll('.toast'));
    
    toasts.forEach(toastEl => {
      // Configura delay según el tipo (más largo para warnings)
      const delay = toastEl.classList.contains('bg-warning') ? 7000 : 5000;
      toastEl.dataset.bsDelay = delay;
      
      const toast = new bootstrap.Toast(toastEl);
      toast.show();
      
      // Elimina el toast del DOM cuando se oculta
      toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
      });
    });
  });
  
  // Función global para mostrar toasts desde JS
  function showDynamicToast({type = 'info', title, message, delay = 5000}) {
    const container = document.querySelector('.toast-container') || createToastContainer();
    const toastId = 'toast-' + Date.now();
    
    container.insertAdjacentHTML('beforeend', `
      <div id="${toastId}" class="toast fade" role="alert" data-bs-delay="${delay}">
        <div class="toast-header bg-${type} text-white">
          <strong class="me-auto">${title || type.charAt(0).toUpperCase() + type.slice(1)}</strong>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body bg-light rounded-bottom">
          ${message}
        </div>
      </div>
    `);
    
    const toast = new bootstrap.Toast(document.getElementById(toastId));
    toast.show();
  }
  
  function createToastContainer() {
    const body = document.body;
    body.insertAdjacentHTML('beforeend', `
      <div class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index: 1100"></div>
    `);
    return body.lastElementChild;
  }