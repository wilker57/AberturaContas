// app.js - Arquitetura Tradicional Flask
document.addEventListener('DOMContentLoaded', function () {
    // Auto-close flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.display = 'none';
        }, 5000);
    });
    
    // Close flash messages when clicking the X
    const closeButtons = document.querySelectorAll('.flash-close');
    closeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });
    
    // Set active menu item based on current URL
    setActiveMenuItem();
    
    // Form validation helpers
    addFormValidation();
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
        } else {
            link.classList.remove('active');
        }
    });
}

function addFormValidation() {
    // Add basic form validation for required fields
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
                showMessage('Por favor, preencha todos os campos obrigatórios.', 'error');
            }
        });
    });
}

function showMessage(message, type = 'info') {
    // Create a temporary flash message
    const container = document.querySelector('.main-content');
    if (!container) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `flash-message flash-${type}`;
    messageDiv.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        ${message}
        <span class="flash-close" onclick="this.parentElement.style.display='none'">&times;</span>
    `;
    
    container.insertBefore(messageDiv, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(function() {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 5000);
}

// Confirmation dialogs for delete actions
function confirmDelete(message = 'Tem certeza que deseja excluir este item?') {
    return confirm(message);
}

// Utility functions for form handling
function formatCurrency(input) {
    // Format currency inputs
    let value = input.value.replace(/\D/g, '');
    value = (value / 100).toFixed(2);
    input.value = value.replace('.', ',');
}

function formatPhone(input) {
    // Format phone inputs
    let value = input.value.replace(/\D/g, '');
    if (value.length >= 11) {
        input.value = value.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    } else if (value.length >= 10) {
        input.value = value.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    }
}

function formatCPF(input) {
    // Format CPF inputs
    let value = input.value.replace(/\D/g, '');
    if (value.length <= 11) {
        input.value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
}

function formatCNPJ(input) {
    // Format CNPJ inputs
    let value = input.value.replace(/\D/g, '');
    if (value.length <= 14) {
        input.value = value.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
}