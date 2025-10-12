// app.js - Flask Template Architecture
document.addEventListener('DOMContentLoaded', function () {
    // Convert Flash messages to SweetAlert2
    convertFlashMessagesToSweetAlert();
    
    setActiveMenuItem();
    addFormValidation();
    protectDeleteForms();
});

function setActiveMenuItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href === currentPath || 
            (currentPath.startsWith('/bancos') && href.includes('/bancos')) ||
            (currentPath.startsWith('/agencias') && href.includes('/agencias')) ||
            (currentPath.startsWith('/concedentes') && href.includes('/concedentes')) ||
            (currentPath.startsWith('/usuarios') && href.includes('/usuarios')) ||
            (currentPath.startsWith('/remessas') && href.includes('/remessas')) ||
            (currentPath.startsWith('/contas-convenio') && href.includes('/contas_convenio'))
        ) {
            link.classList.add('active');
        }
    });
}

function addFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('error');
                    isValid = false;
                } else {
                    field.classList.remove('error');
                }
            });
            
            if (!isValid) {
                event.preventDefault();
                showAlert('Por favor, preencha todos os campos obrigatórios.', 'error');
            }
        });
    });
}

// Convert Flash messages to SweetAlert2
function convertFlashMessagesToSweetAlert() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        const messageText = message.textContent.replace('×', '').trim();
        let category = 'info';
        
        // Determinar categoria pela classe CSS
        if (message.classList.contains('flash-success')) {
            category = 'success';
        } else if (message.classList.contains('flash-error')) {
            category = 'error';
        } else if (message.classList.contains('flash-warning')) {
            category = 'warning';
        }
        
        // Ocultar a mensagem flash original
        message.style.display = 'none';
        
        // Personalizar mensagem para exclusões bem-sucedidas
        if (category === 'success' && messageText.includes('excluído')) {
            Swal.fire({
                title: '✅ Excluído com sucesso!',
                text: messageText,
                icon: 'success',
                confirmButtonColor: '#27ae60',
                confirmButtonText: '<i class="fas fa-check"></i> OK',
                customClass: {
                    confirmButton: 'btn btn-success'
                },
                buttonsStyling: false,
                timer: 3000,
                timerProgressBar: true
            });
        } else {
            // Exibir usando SweetAlert2 padrão para outras mensagens
            showAlert(messageText, category);
        }
    });
}

// SweetAlert2 for alerts
function showAlert(message, type = 'info') {
    let icon, title;
    
    switch (type) {
        case 'success':
            icon = 'success';
            title = 'Sucesso';
            break;
        case 'error':
            icon = 'error';
            title = 'Erro';
            break;
        case 'warning':
            icon = 'warning';
            title = 'Atenção';
            break;
        default:
            icon = 'info';
            title = 'Informação';
    }
    
    Swal.fire({
        title: title,
        text: message,
        icon: icon,
        confirmButtonColor: '#3498db',
        confirmButtonText: '<i class="fas fa-check"></i> OK',
        customClass: {
            confirmButton: 'btn btn-primary'
        },
        buttonsStyling: false,
        timer: type === 'success' ? 3000 : undefined,
        timerProgressBar: type === 'success'
    });
}

// SweetAlert2 for delete confirmations
async function confirmDelete(message = 'Tem certeza que deseja excluir este item?') {
    const result = await Swal.fire({
        title: '⚠️ Confirmar Exclusão',
        html: `<p style="font-size: 16px; margin: 10px 0;">${message}</p><p style="color: #dc3545; font-weight: bold;">Esta ação não pode ser desfeita!</p>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '<i class="fas fa-trash"></i> Sim, excluir!',
        cancelButtonText: '<i class="fas fa-times"></i> Cancelar',
        customClass: {
            confirmButton: 'btn btn-danger',
            cancelButton: 'btn btn-secondary',
            popup: 'swal-delete-popup',
            title: 'swal-delete-title'
        },
        buttonsStyling: false,
        focusCancel: true,
        reverseButtons: true,
        showClass: {
            popup: 'animate__animated animate__fadeInDown animate__faster'
        },
        hideClass: {
            popup: 'animate__animated animate__fadeOutUp animate__faster'
        }
    });
    return result.isConfirmed;
}

function handleDeleteConfirm(event, message) {
    event.preventDefault();
    const form = event.target;
    
    confirmDelete(message).then(confirmed => {
        if (confirmed) {
            // Exibir loading durante o processo de exclusão
            Swal.fire({
                title: 'Excluindo...',
                html: 'Por favor aguarde',
                icon: 'info',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            form.submit();
        }
    });
    
    return false;
}

// Format utilities
function formatCurrency(input) {
    let value = input.value.replace(/\D/g, '');
    value = (value / 100).toFixed(2);
    input.value = value.replace('.', ',');
}

function formatPhone(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length >= 11) {
        input.value = value.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    } else if (value.length >= 10) {
        input.value = value.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    }
}

function formatCPF(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length <= 11) {
        input.value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
}

function formatCNPJ(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length <= 14) {
        input.value = value.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
}

// Modal controls
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        modal.classList.remove('active');
    }
}

// Table utilities
function filterTable(tableId, searchValue) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');
    const searchTerm = searchValue.toLowerCase();
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        let found = false;
        cells.forEach(cell => {
            if (cell.textContent.toLowerCase().includes(searchTerm)) {
                found = true;
            }
        });
        row.style.display = found ? '' : 'none';
    });
}

function sortTable(table, column, direction) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aVal = a.children[column].textContent.trim();
        const bVal = b.children[column].textContent.trim();
        return direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// Proteção adicional para formulários de exclusão
function protectDeleteForms() {
    // Buscar todos os formulários que fazem POST para rotas de exclusão
    const deleteForms = document.querySelectorAll('form[action*="excluir"]');
    
    deleteForms.forEach(form => {
        // Verificar se já tem o onsubmit configurado
        if (!form.hasAttribute('onsubmit')) {
            form.addEventListener('submit', function(event) {
                event.preventDefault();
                
                // Determinar o tipo de item baseado na URL
                const action = form.getAttribute('action');
                let itemType = 'este item';
                
                if (action.includes('usuario')) itemType = 'este usuário';
                else if (action.includes('banco')) itemType = 'este banco';
                else if (action.includes('agencia')) itemType = 'esta agência';
                else if (action.includes('concedente')) itemType = 'este concedente';
                else if (action.includes('remessa')) itemType = 'esta remessa';
                else if (action.includes('conta_convenio')) itemType = 'esta conta convênio';
                
                const message = `Tem certeza que deseja excluir ${itemType}?`;
                
                confirmDelete(message).then(confirmed => {
                    if (confirmed) {
                        // Exibir loading durante o processo de exclusão
                        Swal.fire({
                            title: 'Excluindo...',
                            html: 'Por favor aguarde',
                            icon: 'info',
                            allowOutsideClick: false,
                            allowEscapeKey: false,
                            showConfirmButton: false,
                            didOpen: () => {
                                Swal.showLoading();
                            }
                        });
                        form.submit();
                    }
                });
            });
        }
    });
}
