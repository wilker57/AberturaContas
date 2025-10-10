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
    });
}

// Exemplo: Salvar usuário via formulário
function saveUsuario(event) {
    event.preventDefault();
    // ... pegar dados, validar, chamar backend, etc.
}

// Exemplo: Salvar/remover/editar remessa
function salvarRemessa(event) {
    event.preventDefault();
    // ... pegar dados, validar, chamar backend, etc.
}

// Abrir modal
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        modal.classList.add('active');
    }
}

// Fechar modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        modal.classList.remove('active');
    }
}

// Filtrar tabela por termo (search)
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
            if (cell.textContent.toLowerCase().includes(searchTerm)) found = true;
        });
        row.style.display = found ? '' : 'none';
    });
}

// Ordenação simples para tabelas
function sortTable(table, column, direction) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort((a, b) => {
        const aVal = a.children[column].textContent.trim();
        const bVal = b.children[column].textContent.trim();
        if (direction === 'asc') return aVal.localeCompare(bVal);
        else return bVal.localeCompare(aVal);
    });
    rows.forEach(row => tbody.appendChild(row));
}

// Função para alternar entre telas (login -> dashboard)
function showScreen(screenId) {
    // Ocultar todas as telas
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Mostrar a tela especificada
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
    }
}

// Função para mostrar tela de registro
function showRegister() {
    showScreen('register-screen');
}

// Função para mostrar tela de login
function showLogin() {
    showScreen('login-screen');
}

// Função para mostrar tela de esqueci a senha
function showForgotPassword() {
    showScreen('forgot-password-screen');
}

// Função para alternar entre páginas dentro do dashboard
function showPage(pageId) {
    // Ocultar todas as páginas
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Mostrar a página especificada
    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.classList.add('active');
    }
}

// Função de login com integração à API
function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('login')?.value;
    const password = document.getElementById('senha')?.value;
    
    if (!username || !password) {
        showAlert('login-alert', 'Por favor, preencha usuário e senha', 'error');
        return;
    }
    
    // Fazer requisição AJAX para o backend
    const formData = new FormData();
    formData.append('login', username);
    formData.append('senha', password);
    
    fetch('/login', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Login bem-sucedido, mostrar dashboard
            showScreen('main-screen');
            showPage('dashboard-page');
            loadDashboardData();
        } else {
            // Erro no login
            showAlert('login-alert', data.message || 'Erro ao fazer login', 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showAlert('login-alert', 'Erro de conexão com o servidor', 'error');
    });
}

// Função de registro simulada (deve ser implementada com backend)
function handleRegister(event) {
    event.preventDefault();
    
    const nome = document.getElementById('register-nome')?.value;
    const matricula = document.getElementById('register-matricula')?.value;
    const email = document.getElementById('register-email')?.value;
    const instituicao = document.getElementById('register-instituicao')?.value;
    const login = document.getElementById('register-login')?.value;
    const senha = document.getElementById('register-senha')?.value;
    const confirmSenha = document.getElementById('register-confirm-senha')?.value;
    
    // Validações básicas
    if (!nome || !matricula || !email || !instituicao || !login || !senha || !confirmSenha) {
        showAlert('register-alert', 'Por favor, preencha todos os campos', 'error');
        return;
    }
    
    if (senha !== confirmSenha) {
        showAlert('register-alert', 'As senhas não coincidem', 'error');
        return;
    }
    
    // Simulação de cadastro bem-sucedido
    showAlert('register-alert', 'Cadastro realizado com sucesso! Redirecionando para login...', 'success');
    
    // Após 2 segundos, voltar para tela de login
    setTimeout(() => {
        showLogin();
    }, 2000);
}

// Função para carregar dados do dashboard
function loadDashboardData() {
    fetch('/api/dashboard-stats')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Erro ao carregar dados do dashboard:', data.error);
            return;
        }
        
        // Atualizar elementos do dashboard com os dados
        const elements = {
            'total-usuarios': data.total_usuarios || 0,
            'total-bancos': data.total_bancos || 0,
            'total-agencias': data.total_agencias || 0,
            'total-remessas': data.total_remessas || 0,
            'total-concedentes': data.total_concedentes || 0,
            'total-contas': data.total_contas || 0
        };
        
        Object.keys(elements).forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = elements[id];
            }
        });
    })
    .catch(error => {
        console.error('Erro ao carregar dados do dashboard:', error);
    });
}

// Carregar dados quando a página estiver pronta
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se usuário está logado e carregar dados se necessário
    fetch('/api/user-info')
    .then(response => response.json())
    .then(data => {
        if (!data.error) {
            // Usuário está logado, mostrar dashboard
            showScreen('main-screen');
            showPage('dashboard-page');
            loadDashboardData();
        } else {
            // Usuário não está logado, mostrar tela de login
            showScreen('login-screen');
        }
    })
    .catch(error => {
        console.error('Erro ao verificar autenticação:', error);
        showScreen('login-screen');
    });
});

// Função para mostrar alertas
function showAlert(alertId, message, type) {
    const alert = document.getElementById(alertId);
    if (alert) {
        const span = alert.querySelector('span');
        const icon = alert.querySelector('i');
        
        if (span) span.textContent = message;
        
        // Remover classes de tipo anteriores
        alert.classList.remove('alert-error', 'alert-success', 'alert-warning', 'alert-info');
        
        // Adicionar classe do tipo
        if (type) alert.classList.add(`alert-${type}`);
        
        // Atualizar ícone baseado no tipo
        if (icon) {
            icon.className = 'fas';
            switch (type) {
                case 'success':
                    icon.classList.add('fa-check-circle');
                    break;
                case 'error':
                    icon.classList.add('fa-exclamation-circle');
                    break;
                case 'warning':
                    icon.classList.add('fa-exclamation-triangle');
                    break;
                case 'info':
                default:
                    icon.classList.add('fa-info-circle');
                    break;
            }
        }
        
        // Mostrar alerta
        alert.classList.remove('hidden');
        
        // Auto-ocultar após 5 segundos
        setTimeout(() => {
            alert.classList.add('hidden');
        }, 5000);
    }
}

// Função de logout
function logoutUser() {
    // Limpar dados do usuário
    currentUser = null;
    authToken = null;
    
    // Voltar para tela de login
    showScreen('login-screen');
}
