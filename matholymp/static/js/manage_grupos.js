function confirmDeleteGrupo(id, nombre) {
    confirmDestructiveAction({
        title: '\u00bfEliminar grupo?',
        html: `\u00bfEst\u00e1s seguro de que quieres eliminar el grupo <strong>${nombre}</strong>?`,
        confirmButtonText: 'S\u00ed, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = '?delete_id=' + id;
        }
    });
}

function confirmSendEmail(id, nombreGrupo, nombreRepresentante, sendUrl) {
    confirmAppAction({
        title: '\u00bfEnviar correo?',
        html: `\u00bfEst\u00e1s seguro de que quieres enviar un correo al representante <strong>${nombreRepresentante}</strong> con la lista de participantes del grupo <strong>${nombreGrupo}</strong>?`,
        confirmButtonText: 'S\u00ed, enviar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            showAppLoading({
                title: 'Enviando correo...',
                html: 'Por favor espera mientras se env\u00eda el correo electr\u00f3nico al representante.',
            });

            fetch(sendUrl.replace('0', id), {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Error en la respuesta del servidor');
            })
            .then(data => {
                if (data.success) {
                    showAppSuccess({
                        title: 'Correo enviado',
                        text: data.message
                    });
                } else {
                    showAppError({
                        title: 'No se envi\u00f3 el correo',
                        text: data.message
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAppError({
                    title: 'Error de conexi\u00f3n',
                    text: 'Hubo un error al enviar el correo. Por favor, intenta de nuevo.'
                });
            });
        }
    });
}

function filterParticipantes(modalId) {
    const searchInput = document.getElementById('searchParticipantes' + modalId);
    if (!searchInput) {
        return;
    }

    const searchTerm = searchInput.value.toLowerCase().trim();

    let modalSelector;
    if (modalId === 'new' || modalId === 'New') {
        modalSelector = '#addGrupoModal';
    } else {
        modalSelector = `#editGrupoModal${modalId}`;
    }

    const modal = document.querySelector(modalSelector);
    if (!modal) {
        return;
    }

    const participanteItems = modal.querySelectorAll('.participante-item');

    participanteItems.forEach(item => {
        const label = item.querySelector('.form-check-label');
        if (!label) return;

        const nombre = label.querySelector('strong')?.textContent.toLowerCase() || '';
        const cedula = label.querySelector('small')?.textContent.replace(/[()]/g, '').toLowerCase() || '';

        const matches = searchTerm === '' ||
                       nombre.includes(searchTerm) ||
                       cedula.includes(searchTerm);

        if (matches) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

function clearSearch(modalId) {
    let modalSelector;
    if (modalId === 'new' || modalId === 'New') {
        modalSelector = '#addGrupoModal';
    } else {
        modalSelector = `#editGrupoModal${modalId}`;
    }

    const modal = document.querySelector(modalSelector);
    if (!modal) {
        return;
    }

    const searchInput = modal.querySelector('input[placeholder="Buscar participantes..."]');
    if (!searchInput) {
        return;
    }

    searchInput.value = '';

    const participanteItems = modal.querySelectorAll('.participante-item');
    participanteItems.forEach(item => {
        item.style.display = 'block';
    });

    searchInput.focus();
}

document.addEventListener('DOMContentLoaded', function() {
    const modals = document.querySelectorAll('[id^="editGrupoModal"], #addGrupoModal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            const searchInput = this.querySelector('input[placeholder="Buscar participantes..."]');
            if (searchInput) {
                searchInput.value = '';
                const participanteItems = this.querySelectorAll('.participante-item');
                participanteItems.forEach(item => {
                    item.style.display = 'block';
                });
            }
        });
    });

    document.addEventListener('input', function(e) {
        if (e.target.matches('input[placeholder="Buscar participantes..."]')) {
            let modalId = e.target.id.replace('searchParticipantes', '');
            filterParticipantes(modalId);
        }
    });

    document.addEventListener('keyup', function(e) {
        if (e.target.matches('input[placeholder="Buscar participantes..."]')) {
            let modalId = e.target.id.replace('searchParticipantes', '');
            filterParticipantes(modalId);
        }
    });
});
