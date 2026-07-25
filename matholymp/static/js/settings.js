// Variables globales para categorías
let categoriaEnEdicion = null;

document.addEventListener('DOMContentLoaded', function() {
  const formAnio = document.getElementById('form_anio');
  const formEtapas = document.getElementById('form_etapas');
  const formCategoria = document.getElementById('formCategoria');
  const maxYear = window.maxYear || new Date().getFullYear();

  if (formAnio) {
    formAnio.addEventListener('submit', function(e) {
      e.preventDefault();
      const anioInput = document.getElementById('anio_concurso');
      const val = parseInt(anioInput.value || anioInput.placeholder || maxYear, 10);
      if (val > maxYear) {
        Swal.fire('Año inválido', 'No puede seleccionar un año futuro.', 'error');
        return;
      }
      Swal.fire({
        title: '¿Confirmar cambio de año?',
        text: 'Esto filtrará toda la información por el año seleccionado.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, cambiar',
        cancelButtonText: 'Cancelar'
      }).then((result) => {
        if (result.isConfirmed) {
          formAnio.submit();
        }
      });
    });
  }

  if (formEtapas) {
    formEtapas.addEventListener('submit', function(e) {
      e.preventDefault();
      Swal.fire({
        title: '¿Confirmar cambio de etapas?',
        text: 'Esto afectará la progresión entre etapas.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, cambiar',
        cancelButtonText: 'Cancelar'
      }).then((result) => {
        if (result.isConfirmed) {
          formEtapas.submit();
        }
      });
    });
  }

  // Manejo del formulario de categorías
  if (formCategoria) {
    formCategoria.addEventListener('submit', function(e) {
      e.preventDefault();
      guardarCategoria();
    });
  }

  // Limpiar modal cuando se cierre
  const modalCategoria = document.getElementById('modalCategoria');
  if (modalCategoria) {
    modalCategoria.addEventListener('hidden.bs.modal', function() {
      limpiarFormularioCategoria();
    });
  }
});

function guardarCategoria() {
  const formData = new FormData(document.getElementById('formCategoria'));
  const data = {
    nombre: formData.get('nombre').trim(),
    descripcion: formData.get('descripcion').trim(),
    activa: formData.get('activa') ? true : false
  };

  if (!data.nombre) {
    Swal.fire('Error', 'El nombre de la categoría es obligatorio', 'error');
    return;
  }

  const url = categoriaEnEdicion ? 
    window.editarCategoriaUrl.replace('/0/', `/${categoriaEnEdicion}/`) : 
    window.crearCategoriaUrl;
    
  const method = categoriaEnEdicion ? 'PUT' : 'POST';

  fetch(url, {
    method: method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    },
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      Swal.fire({
        icon: 'success',
        title: '¡Éxito!',
        text: data.message,
        timer: 1500,
        showConfirmButton: false
      }).then(() => {
        location.reload();
      });
    } else {
      Swal.fire('Error', data.error || 'Error al guardar la categoría', 'error');
    }
  })
  .catch(error => {
    Swal.fire('Error', 'Error de conexión al guardar la categoría', 'error');
  });
}

function editarCategoria(categoriaId) {
  const url = window.obtenerCategoriaUrl.replace('/0/', `/${categoriaId}/`);
  fetch(url)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        categoriaEnEdicion = categoriaId;
        
        // Llenar el formulario
        document.getElementById('nombreCategoria').value = data.categoria.nombre;
        document.getElementById('descripcionCategoria').value = data.categoria.descripcion || '';
        document.getElementById('activaCategoria').checked = data.categoria.activa;
        
        // Cambiar el título del modal
        document.getElementById('modalCategoriaLabel').innerHTML = '<i class="bi bi-pencil me-2"></i>Editar Categoría';
        document.getElementById('btnGuardarCategoria').innerHTML = '<i class="bi bi-check2-circle me-1"></i>Actualizar Categoría';
        
        // Mostrar el modal
        const modalElement = document.getElementById('modalCategoria');
        const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
        modal.show();
      } else {
        Swal.fire('Error', data.error || 'Error al cargar los datos de la categoría', 'error');
      }
    })
    .catch(error => {
      Swal.fire('Error', 'Error de conexión al cargar la categoría', 'error');
    });
}

function toggleCategoria(categoriaId, activar) {
  const accion = activar ? 'activar' : 'desactivar';
  
  Swal.fire({
    title: `¿${accion.charAt(0).toUpperCase() + accion.slice(1)} categoría?`,
    text: `Esta acción ${accion}á la categoría.`,
    icon: 'question',
    showCancelButton: true,
    confirmButtonText: `Sí, ${accion}`,
    cancelButtonText: 'Cancelar'
  }).then((result) => {
    if (result.isConfirmed) {
      const url = window.toggleCategoriaUrl.replace('/0/', `/${categoriaId}/`);
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ activa: activar })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          Swal.fire({
            icon: 'success',
            title: '¡Éxito!',
            text: data.message,
            timer: 1500,
            showConfirmButton: false
          }).then(() => {
            location.reload();
          });
        } else {
          Swal.fire('Error', data.error || 'Error al cambiar el estado de la categoría', 'error');
        }
      })
      .catch(error => {
        Swal.fire('Error', 'Error de conexión', 'error');
      });
    }
  });
}

function limpiarFormularioCategoria() {
  categoriaEnEdicion = null;
  document.getElementById('formCategoria').reset();
  document.getElementById('activaCategoria').checked = true;
  
  // Restaurar título del modal
  document.getElementById('modalCategoriaLabel').innerHTML = '<i class="bi bi-plus-circle me-2"></i>Agregar Categoría';
  document.getElementById('btnGuardarCategoria').innerHTML = '<i class="bi bi-check2-circle me-1"></i>Guardar Categoría';
}
