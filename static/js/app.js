// app.js - Flask Template Architecture with SweetAlert2 only

// Tornar showAlert global para ser acessível de qualquer lugar
window.showAlert = function(message, type = 'info') {
    // Verificar se SweetAlert2 está disponível
    if (typeof Swal === 'undefined') {
        console.error('SweetAlert2 não está carregado!');
        alert(message); // Fallback para alert nativo
        return;
    }

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
};

// Função global para confirmação de exclusão
window.confirmDelete = async function(message = 'Tem certeza que deseja excluir este item?') {
    console.log('confirmDelete chamada com mensagem:', message);
    
    // Verificar se SweetAlert2 está disponível
    if (typeof Swal === 'undefined') {
        console.error('SweetAlert2 não está carregado!');
        return confirm(message); // Fallback para confirm nativo
    }
    
    try {
        const result = await Swal.fire({
            title: 'Confirmar Exclusão',
            text: message + ' Esta ação não pode ser desfeita!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sim, excluir!',
            cancelButtonText: 'Cancelar',
            focusCancel: true,
            reverseButtons: true,
            allowOutsideClick: false,
            allowEscapeKey: true
        });
        
        console.log('Resultado do SweetAlert:', result);
        return result.isConfirmed;
    } catch (error) {
        console.error('Erro no Swal.fire:', error);
        return confirm(message); // Fallback para confirm nativo
    }
};

document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM carregado');
    console.log('SweetAlert2 disponível?', typeof Swal !== 'undefined');
    console.log('showAlert function available?', typeof window.showAlert === 'function');
    
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
    console.log('Configurando proteção para formulários de exclusão...');
    
    // Buscar todos os formulários que fazem POST para rotas de exclusão OU têm a classe delete-form
    const deleteForms = document.querySelectorAll('form[action*="excluir"], .delete-form');
    
    console.log('Encontrados', deleteForms.length, 'formulários de exclusão');
    
    deleteForms.forEach((form, index) => {
        console.log(`Configurando formulário ${index + 1}:`, form.action || 'sem action');
        
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            console.log('Formulário de exclusão submetido, interceptando...');
            
            // Pegar a mensagem do data-attribute ou determinar baseado na URL
            let message = form.getAttribute('data-message');
            
            if (!message) {
                // Determinar o tipo de item baseado na URL
                const action = form.getAttribute('action') || '';
                let itemType = 'este item';
                
                if (action.includes('usuario')) itemType = 'este usuário';
                else if (action.includes('banco')) itemType = 'este banco';
                else if (action.includes('agencia')) itemType = 'esta agência';
                else if (action.includes('concedente')) itemType = 'este concedente';
                else if (action.includes('remessa')) itemType = 'esta remessa';
                else if (action.includes('conta_convenio')) itemType = 'esta conta convênio';
                
                message = `Tem certeza que deseja excluir ${itemType}?`;
            }
            
            console.log('Chamando confirmDelete com mensagem:', message);
            
            window.confirmDelete(message).then(confirmed => {
                console.log('Resultado da confirmação:', confirmed);
                if (confirmed) {
                    console.log('Confirmado! Enviando formulário...');
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
                } else {
                    console.log('Cancelado pelo usuário');
                }
            }).catch(error => {
                console.error('Erro na confirmação:', error);
                alert('Erro ao exibir confirmação: ' + error.message);
            });
        });
    });
}
