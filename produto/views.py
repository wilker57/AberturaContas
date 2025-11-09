# views.py - Arquitetura Tradicional com SQL Direto

from flask import Blueprint, render_template, redirect, url_for, session, request, flash, make_response
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from datetime import date
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

views_bp = Blueprint('views', __name__)

# ===========================
# FUNÇÕES AUXILIARES DE SENHA
# ===========================

def generate_password_hash(password):
    #Gera hash bcrypt para a senha
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def check_password_hash(hashed_password, password):
    #Verifica se a senha corresponde ao hash
    try:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Erro na verificação de senha: {e}")
        return False

# Configuração do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'database': 'abertura_contas',
    'user': 'postgres',
    'password': 'wil874408',
    'port': 5432
}

def get_db_connection():
    #Cria uma conexão com o banco de dados PostgreSQL
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar com o banco: {e}")
        return None

def execute_query(query, params=None, fetch=True):
    #Executa uma query no banco de dados
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or ())
        
        if fetch:
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
            conn.commit()
            return result
        else:
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        conn.rollback()
        print(f"ERRO SQL - Query: {query}")
        print(f"ERRO SQL - Params: {params}")
        print(f"ERRO SQL - Detalhes: {e}")
        print(f"ERRO SQL - Tipo: {type(e).__name__}")
        return None
    finally:
        cursor.close()
        conn.close()

# ===========================
# ROTAS DE AUTENTICAÇÃO
# ===========================

@views_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    return redirect(url_for('views.dashboard'))

@views_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('login')
        senha = request.form.get('senha')
        
        # Validação básica
        if not login_input or not senha:
            flash('Login e senha são obrigatórios', 'error')
            return render_template('auth/login.html')
        
        # Buscar usuário por login
        query = "SELECT id_usuario, login, nome, senha, perfil_enum FROM usuario WHERE login = %s"
        user = execute_query(query, (login_input,))
        
        if user and len(user) > 0:
            user = user[0]
            # Verificar se a senha foi recuperada corretamente
            if user['senha'] and check_password_hash(user['senha'], senha):
                session['user_id'] = user['id_usuario']
                session['user_name'] = user['nome']
                session['user_profile'] = user['perfil_enum']
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('views.dashboard'))
        
        flash('Login ou senha inválidos', 'error')
    
    return render_template('auth/login.html')

@views_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    print(f"DEBUG - Método da requisição: {request.method}")
    print(f"DEBUG - Dados do formulário: {request.form}")
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        matricula = request.form.get('matricula')
        email = request.form.get('email')
        instituicao = request.form.get('instituicao')
        login = request.form.get('login')
        senha = request.form.get('senha')
        perfil_enum = request.form.get('perfil_enum', 'MONITOR')
        
        # Debug logs
        print(f"DEBUG - Dados recebidos:")
        print(f"Nome: {nome}")
        print(f"Matricula: {matricula}")
        print(f"Email: {email}")
        print(f"Instituicao: {instituicao}")
        print(f"Login: {login}")
        print(f"Senha: {'***' if senha else 'None'}")
        print(f"Perfil: {perfil_enum}")
        
        # Validação básica
        if not all([nome, matricula, email, instituicao, login, senha]):
            print("DEBUG - Erro: Campos obrigatórios faltando")
            flash('Todos os campos são obrigatórios!', 'error')
            return render_template('auth/register.html')
        
        # Verificar se já existe usuário com mesmo login, email ou matrícula
        check_query = """
            SELECT COUNT(*) as count FROM usuario 
            WHERE login = %s OR email = %s OR matricula = %s
        """
        existing_user = execute_query(check_query, (login, email, matricula), fetch=True)
        print(f"DEBUG - Verificação de usuário existente: {existing_user}")
        
        if existing_user and existing_user[0]['count'] > 0:
            print("DEBUG - Erro: Usuário já existe")
            flash('Usuário com este login, email ou matrícula já existe!', 'error')
            return render_template('auth/register.html')
        
        senha_hash = generate_password_hash(senha)
        print(f"DEBUG - Hash da senha gerado: {'***' if senha_hash else 'None'}")
        
        query = """
            INSERT INTO usuario (nome, matricula, email, instituicao, login, senha, perfil_enum)
            VALUES (%s, %s, %s, %s, %s, %s, %s::perfilenum)
        """
        
        print(f"DEBUG - Executando query de inserção...")
        result = execute_query(query, (nome, matricula, email, instituicao, login, senha_hash, perfil_enum), fetch=False)
        print(f"DEBUG - Resultado da inserção: {result}")
        
        if result and result > 0:
            print("DEBUG - Cadastro realizado com sucesso!")
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('views.login'))
        else:
            print("DEBUG - Erro na inserção")
            flash('Erro ao cadastrar usuário. Tente novamente.', 'error')
    
    print("DEBUG - Renderizando template de registro")
    return render_template('auth/register.html')

@views_bp.route('/esqueci-senha')
def forgot_password():
    return render_template('auth/forgot-password.html')

@views_bp.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('views.login'))

# ===========================
# DASHBOARD
# ===========================

@views_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    # Estatísticas para o dashboard
    stats = {}
    
    # Total de usuários
    result = execute_query("SELECT COUNT(*) as total FROM usuario")
    stats['total_usuarios'] = result[0]['total'] if result else 0
    
    # Total de bancos
    result = execute_query("SELECT COUNT(*) as total FROM banco")
    stats['total_bancos'] = result[0]['total'] if result else 0
    
    # Total de agências
    result = execute_query("SELECT COUNT(*) as total FROM agencia")
    stats['total_agencias'] = result[0]['total'] if result else 0
    
    # Total de remessas
    result = execute_query("SELECT COUNT(*) as total FROM remessa")
    stats['total_remessas'] = result[0]['total'] if result else 0
    
    # Total de concedentes
    result = execute_query("SELECT COUNT(*) as total FROM concedente")
    stats['total_concedentes'] = result[0]['total'] if result else 0
    
    # Total de contas
    result = execute_query("SELECT COUNT(*) as total FROM conta_convenio")
    stats['total_contas'] = result[0]['total'] if result else 0

    # ADICIONE: status das remessas
    remessas = {}
    
    # Contagem de remessas por status
    result = execute_query("SELECT COUNT(*) as total FROM remessa WHERE situacao = 'Em Preparação'")
    remessas['preparacao'] = result[0]['total'] if result else 0
    
    result = execute_query("SELECT COUNT(*) as total FROM remessa WHERE situacao = 'Enviado'")
    remessas['enviado'] = result[0]['total'] if result else 0
    
    result = execute_query("SELECT COUNT(*) as total FROM remessa WHERE situacao = 'Aguardando retorno'")
    remessas['aguardando'] = result[0]['total'] if result else 0
    
    result = execute_query("SELECT COUNT(*) as total FROM remessa WHERE situacao = 'Pendente de envio'")
    remessas['pendente'] = result[0]['total'] if result else 0
    
    result = execute_query("SELECT COUNT(*) as total FROM remessa WHERE situacao = 'Conta Aberta'")
    remessas['aberta'] = result[0]['total'] if result else 0
    
    result = execute_query("SELECT COUNT(*) as total FROM remessa WHERE situacao = 'Erro'")
    remessas['erro'] = result[0]['total'] if result else 0
    
    return render_template('dashboard.html', stats=stats, remessas=remessas)

# ===========================
# CRUD - BANCOS
# ===========================

@views_bp.route('/bancos')
def bancos():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = "SELECT * FROM banco ORDER BY nome"
    bancos_list = execute_query(query)
    
    return render_template('bancos/list.html', bancos=bancos_list)

@views_bp.route('/bancos/criar', methods=['GET', 'POST'])
def criar_banco():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        
        query = "INSERT INTO banco (nome) VALUES (%s)"
        result = execute_query(query, (nome,), fetch=False)
        
        if result:
            flash('Banco criado com sucesso!', 'success')
            return redirect(url_for('views.bancos'))
        else:
            flash('Erro ao criar banco.', 'error')
    
    return render_template('bancos/create.html')

@views_bp.route('/bancos/editar/<int:id_banco>', methods=['GET', 'POST'])
def editar_banco(id_banco):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        
        query = "UPDATE banco SET nome = %s WHERE id_banco = %s"
        result = execute_query(query, (nome, id_banco), fetch=False)
        
        if result:
            flash('Banco atualizado com sucesso!', 'success')
            return redirect(url_for('views.bancos'))
        else:
            flash('Erro ao atualizar banco.', 'error')
    
    # GET - Buscar dados do banco para edição
    query = "SELECT * FROM banco WHERE id_banco = %s"
    banco = execute_query(query, (id_banco,))
    
    if not banco:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('views.bancos'))
    
    return render_template('bancos/edit.html', banco=banco[0])

@views_bp.route('/bancos/excluir/<int:id_banco>', methods=['POST'])
def excluir_banco(id_banco):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = "DELETE FROM banco WHERE id_banco = %s"
    result = execute_query(query, (id_banco,), fetch=False)
    
    if result:
        flash('Banco excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir banco.', 'error')
    
    return redirect(url_for('views.bancos'))

# ===========================
# CRUD - AGÊNCIAS
# ===========================

@views_bp.route('/agencias')
def agencias():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = """
        SELECT *,
        (SELECT nome FROM banco WHERE banco.id_banco = agencia.id_banco) AS banco_nome
        FROM agencia
<<<<<<< HEAD
        ORDER BY nome_agencia;
=======
        ORDER BY a.nome_agencia;
>>>>>>> cc6496e378aa030fad768eface98cc66458af699
    """
    agencias_list = execute_query(query)
    
    return render_template('agencias/list.html', agencias=agencias_list)

@views_bp.route('/agencias/criar', methods=['GET', 'POST'])
def criar_agencia():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        nome_agencia = request.form.get('nome_agencia')
        num_agencia = request.form.get('num_agencia')
        dv_agencia = request.form.get('dv_agencia')
        logadouro = request.form.get('logadouro')
        cidade = request.form.get('cidade')
        uf = request.form.get('uf')
        id_banco = request.form.get('id_banco')
        
        query = """
            INSERT INTO agencia (nome_agencia, num_agencia, dv_agencia, logadouro, cidade, uf, id_banco)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        result = execute_query(query, (nome_agencia, num_agencia, dv_agencia, logadouro, cidade, uf, id_banco), fetch=False)
        
        if result:
            flash('Agência criada com sucesso!', 'success')
            return redirect(url_for('views.agencias'))
        else:
            flash('Erro ao criar agência.', 'error')
    
    # Buscar bancos para o formulário
    query_bancos = "SELECT * FROM banco ORDER BY nome"
    bancos = execute_query(query_bancos)
    
    return render_template('agencias/create.html', bancos=bancos)

@views_bp.route('/agencias/editar/<int:id_agencia>', methods=['GET', 'POST'])
def editar_agencia(id_agencia):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        nome_agencia = request.form.get('nome_agencia')
        num_agencia = request.form.get('num_agencia')
        dv_agencia = request.form.get('dv_agencia')
        logadouro = request.form.get('logadouro')
        cidade = request.form.get('cidade')
        uf = request.form.get('uf')
        id_banco = request.form.get('id_banco')
        
        query = """
            UPDATE agencia 
            SET nome_agencia = %s, num_agencia = %s, dv_agencia = %s, 
                logadouro = %s, cidade = %s, uf = %s, id_banco = %s
            WHERE id_agencia = %s
        """
        result = execute_query(query, (nome_agencia, num_agencia, dv_agencia, logadouro, cidade, uf, id_banco, id_agencia), fetch=False)
        
        if result:
            flash('Agência atualizada com sucesso!', 'success')
            return redirect(url_for('views.agencias'))
        else:
            flash('Erro ao atualizar agência.', 'error')
    
    # GET - Buscar dados da agência para edição
    query = """
        SELECT *,
        (SELECT nome FROM banco WHERE banco.id_banco = agencia.id_banco) AS banco_nome
        FROM agencia
        WHERE id_agencia = %s;
    """
    agencia = execute_query(query, (id_agencia,))
    
    # Buscar bancos para o formulário
    query_bancos = "SELECT * FROM banco ORDER BY nome"
    bancos = execute_query(query_bancos)
    
    if not agencia:
        flash('Agência não encontrada.', 'error')
        return redirect(url_for('views.agencias'))
    
    return render_template('agencias/edit.html', agencia=agencia[0], bancos=bancos)

@views_bp.route('/agencias/excluir/<int:id_agencia>', methods=['POST'])
def excluir_agencia(id_agencia):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = "DELETE FROM agencia WHERE id_agencia = %s"
    result = execute_query(query, (id_agencia,), fetch=False)
    
    if result:
        flash('Agência excluída com sucesso!', 'success')
    else:
        flash('Erro ao excluir agência.', 'error')
    
    return redirect(url_for('views.agencias'))

# ===========================
# CRUD - CONCEDENTES
# ===========================

@views_bp.route('/concedentes')
def concedentes():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = "SELECT * FROM concedente ORDER BY nome"
    concedentes_list = execute_query(query)
    
    return render_template('concedentes/list.html', concedentes=concedentes_list)

@views_bp.route('/concedentes/criar', methods=['GET', 'POST'])
def criar_concedente():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        codigo_secretaria = request.form.get('codigo_secretaria')
        sigla = request.form.get('sigla')
        nome = request.form.get('nome')
        
        query = """
            INSERT INTO concedente (codigo_secretaria, sigla, nome)
            VALUES (%s, %s, %s)
        """
        result = execute_query(query, (codigo_secretaria, sigla, nome), fetch=False)
        
        if result:
            flash('Concedente criado com sucesso!', 'success')
            return redirect(url_for('views.concedentes'))
        else:
            flash('Erro ao criar concedente.', 'error')
    
    return render_template('concedentes/create.html')

@views_bp.route('/concedentes/editar/<int:id_concedente>', methods=['GET', 'POST'])
def editar_concedente(id_concedente):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        codigo_secretaria = request.form.get('codigo_secretaria')
        sigla = request.form.get('sigla')
        nome = request.form.get('nome')
        
        query = """
            UPDATE concedente 
            SET codigo_secretaria = %s, sigla = %s, nome = %s
            WHERE id_concedente = %s
        """
        result = execute_query(query, (codigo_secretaria, sigla, nome, id_concedente), fetch=False)
        
        if result:
            flash('Concedente atualizado com sucesso!', 'success')
            return redirect(url_for('views.concedentes'))
        else:
            flash('Erro ao atualizar concedente.', 'error')
    
    # GET - Buscar dados do concedente para edição
    query = "SELECT * FROM concedente WHERE id_concedente = %s"
    concedente = execute_query(query, (id_concedente,))
    
    if not concedente:
        flash('Concedente não encontrado.', 'error')
        return redirect(url_for('views.concedentes'))
    
    return render_template('concedentes/edit.html', concedente=concedente[0])

@views_bp.route('/concedentes/excluir/<int:id_concedente>', methods=['POST'])
def excluir_concedente(id_concedente):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = "DELETE FROM concedente WHERE id_concedente = %s"
    result = execute_query(query, (id_concedente,), fetch=False)
    
    if result:
        flash('Concedente excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir concedente.', 'error')
    
    return redirect(url_for('views.concedentes'))

# ===========================
# CRUD - USUÁRIOS
# ===========================

@views_bp.route('/usuarios')
def usuarios():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = "SELECT * FROM usuario ORDER BY nome"
    usuarios_list = execute_query(query)
    
    return render_template('usuarios/list.html', usuarios=usuarios_list)

@views_bp.route('/usuarios/criar', methods=['GET', 'POST'])
def criar_usuario():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        matricula = request.form.get('matricula')
        email = request.form.get('email')
        instituicao = request.form.get('instituicao')
        login = request.form.get('login')
        senha = request.form.get('senha')
        perfil_enum = request.form.get('perfil_enum', 'MONITOR')
        
        senha_hash = generate_password_hash(senha)
        
        query = """
            INSERT INTO usuario (nome, matricula, email, instituicao, login, senha, perfil_enum)
            VALUES (%s, %s, %s, %s, %s, %s, %s::perfilenum)
        """
        result = execute_query(query, (nome, matricula, email, instituicao, login, senha_hash, perfil_enum), fetch=False)
        
        if result:
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('views.usuarios'))
        else:
            flash('Erro ao criar usuário.', 'error')
    
    return render_template('usuarios/create.html')

@views_bp.route('/usuarios/editar/<int:id_usuario>', methods=['GET', 'POST'])
def editar_usuario(id_usuario):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        matricula = request.form.get('matricula')
        email = request.form.get('email')
        instituicao = request.form.get('instituicao')
        login = request.form.get('login')
        perfil_enum = request.form.get('perfil_enum')
        nova_senha = request.form.get('nova_senha')
        
        # Se nova senha foi fornecida, inclua na atualização
        if nova_senha:
            senha_hash = generate_password_hash(nova_senha)
            query = """
                UPDATE usuario 
                SET nome = %s, matricula = %s, email = %s, instituicao = %s, 
                    login = %s, perfil_enum = %s::perfilenum, senha = %s
                WHERE id_usuario = %s
            """
            result = execute_query(query, (nome, matricula, email, instituicao, login, perfil_enum, senha_hash, id_usuario), fetch=False)
        else:
            query = """
                UPDATE usuario 
                SET nome = %s, matricula = %s, email = %s, instituicao = %s, 
                    login = %s, perfil_enum = %s::perfilenum
                WHERE id_usuario = %s
            """
            result = execute_query(query, (nome, matricula, email, instituicao, login, perfil_enum, id_usuario), fetch=False)
        #aLTERÇÃO SENHA
        if result:
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('views.usuarios'))
        else:
            flash('Erro ao atualizar usuário.', 'error')
    
    # GET - Buscar dados do usuário para edição
    query = "SELECT * FROM usuario WHERE id_usuario = %s"
    usuario = execute_query(query, (id_usuario,))
    
    if not usuario:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('views.usuarios'))
    
    return render_template('usuarios/edit.html', usuario=usuario[0])

@views_bp.route('/usuarios/excluir/<int:id_usuario>', methods=['POST'])
def excluir_usuario(id_usuario):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = "DELETE FROM usuario WHERE id_usuario = %s"
    result = execute_query(query, (id_usuario,), fetch=False)
    
    if result:
        flash('Usuário excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir usuário.', 'error')
    
    return redirect(url_for('views.usuarios'))

# ===========================
# CRUD - REMESSAS
# ===========================

@views_bp.route('/remessas')
def remessas():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = """
        SELECT *,
<<<<<<< HEAD
=======
        (SELECT nome_agencia FROM agencia WHERE agencia.id_banco = remessa.id_banco) AS nome_agencia,
>>>>>>> cc6496e378aa030fad768eface98cc66458af699
        (SELECT nome FROM concedente WHERE concedente.id_concedente = remessa.id_concedente) AS concedente_nome,
        (SELECT nome FROM usuario WHERE usuario.id_usuario = remessa.id_usuario) AS usuario_nome,
        (SELECT nome FROM banco WHERE banco.id_banco = remessa.id_banco) AS banco_nome
        FROM remessa
        ORDER BY dt_remessa DESC;
    """ 
    remessas_list = execute_query(query)
    
    return render_template('remessas/list.html', remessas=remessas_list)

@views_bp.route('/remessas/criar', methods=['GET', 'POST'])
def criar_remessa():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        num_processo = request.form.get('num_processo')
        nome_proponente = request.form.get('nome_proponente')
        cpf_cnpj = request.form.get('cpf_cnpj')
        num_convenio = request.form.get('num_convenio')
        situacao = request.form.get('situacao', 'Em Preparação')
        id_concedente = request.form.get('id_concedente')
        id_banco = request.form.get('id_banco')
        
        # Validação básica
        if not all([num_processo, nome_proponente, cpf_cnpj, num_convenio, id_concedente]):
            flash('Todos os campos obrigatórios devem ser preenchidos!', 'error')
            # Buscar dados para formulário novamente
            query_concedentes = "SELECT * FROM concedente ORDER BY nome"
            concedentes = execute_query(query_concedentes)
            query_bancos = "SELECT * FROM banco ORDER BY nome"
            bancos = execute_query(query_bancos)
            return render_template('remessas/create.html', concedentes=concedentes, bancos=bancos)
        
        # Calcular próximo num_remessa automaticamente
        query_max = "SELECT COALESCE(MAX(num_remessa), 0) + 1 as proximo_num FROM remessa"
        resultado_max = execute_query(query_max)
        proximo_num_remessa = resultado_max[0]['proximo_num'] if resultado_max else 1
        
        query = """
            INSERT INTO remessa (num_processo, nome_proponente, cpf_cnpj, num_convenio, 
                               situacao, num_remessa, id_concedente, id_usuario, id_banco)
            VALUES (%s, %s, %s, %s, %s::situacao_enum, %s, %s, %s, %s)
        """
        result = execute_query(query, (num_processo, nome_proponente, cpf_cnpj, num_convenio, 
                                      situacao, proximo_num_remessa, id_concedente, session['user_id'], id_banco), fetch=False)
        
        if result and result > 0:
            flash('Remessa criada com sucesso!', 'success')
            return redirect(url_for('views.remessas'))
        else:
            flash('Erro ao criar remessa.', 'error')
    
    # Buscar dados para formulário
    query_concedentes = "SELECT * FROM concedente ORDER BY nome"
    concedentes = execute_query(query_concedentes)
    
    query_bancos = "SELECT * FROM banco ORDER BY nome"
    bancos = execute_query(query_bancos)
    
    return render_template('remessas/create.html', concedentes=concedentes, bancos=bancos)

@views_bp.route('/remessas/editar/<int:id_remessa>', methods=['GET', 'POST'])
def editar_remessa(id_remessa):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        num_processo = request.form.get('num_processo')
        nome_proponente = request.form.get('nome_proponente')
        cpf_cnpj = request.form.get('cpf_cnpj')
        num_convenio = request.form.get('num_convenio')
        situacao = request.form.get('situacao')
        id_concedente = request.form.get('id_concedente')
        id_banco = request.form.get('id_banco')
        
        # num_remessa NÃO é alterado na edição - mantém o valor original
        query = """
            UPDATE remessa 
            SET num_processo = %s, nome_proponente = %s, cpf_cnpj = %s, num_convenio = %s,
                situacao = %s::situacao_enum, id_concedente = %s, id_banco = %s
            WHERE id_remessa = %s
        """
        result = execute_query(query, (num_processo, nome_proponente, cpf_cnpj, num_convenio,
                                      situacao, id_concedente, id_banco, id_remessa), fetch=False)
        
        if result:
            flash('Remessa atualizada com sucesso!', 'success')
            return redirect(url_for('views.remessas'))
        else:
            flash('Erro ao atualizar remessa.', 'error')
    
    # GET - Buscar dados da remessa para edição
    query = """
        SELECT *,
        (SELECT nome FROM concedente WHERE concedente.id_concedente = remessa.id_concedente) AS concedente_nome,
        (SELECT nome FROM banco WHERE banco.id_banco = remessa.id_banco) AS banco_nome
        FROM remessa 
        WHERE id_remessa = %s;
    """
    remessa = execute_query(query, (id_remessa,))
    
    # Buscar dados para formulário
    query_concedentes = "SELECT * FROM concedente ORDER BY nome"
    concedentes = execute_query(query_concedentes)
    
    query_bancos = "SELECT * FROM banco ORDER BY nome"
    bancos = execute_query(query_bancos)
    
    if not remessa:
        flash('Remessa não encontrada.', 'error')
        return redirect(url_for('views.remessas'))
    
    return render_template('remessas/edit.html', remessa=remessa[0], concedentes=concedentes, bancos=bancos)

@views_bp.route('/remessas/excluir/<int:id_remessa>', methods=['POST'])
def excluir_remessa(id_remessa):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = "DELETE FROM remessa WHERE id_remessa = %s"
    result = execute_query(query, (id_remessa,), fetch=False)
    
    if result:
        flash('Remessa excluída com sucesso!', 'success')
    else:
        flash('Erro ao excluir remessa.', 'error')
    
    return redirect(url_for('views.remessas'))
#Gerar PDF da remessa
@views_bp.route('/remessas/editar/<int:id_remessa>/gerar-pdf')
def gerar_pdf(id_remessa):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))

    # Buscar dados completos da remessa
    query = """
        SELECT 
            r.num_remessa, r.num_processo, r.nome_proponente, r.cpf_cnpj, r.num_convenio, r.situacao,
            r.dt_remessa,
            c.nome AS concedente_nome,
            u.nome AS usuario_nome,
            b.nome AS banco_nome
        FROM remessa r
        LEFT JOIN concedente c ON r.id_concedente = c.id_concedente
        LEFT JOIN usuario u ON r.id_usuario = u.id_usuario
        LEFT JOIN banco b ON r.id_banco = b.id_banco
        WHERE r.id_remessa = %s;
    """
    remessa_data = execute_query(query, (id_remessa,))

    if not remessa_data:
        flash('Remessa não encontrada.', 'error')
        return redirect(url_for('views.remessas'))

    remessa = remessa_data[0]

    # Configuração do PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Desenhar o conteúdo do PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(inch, height - inch, f"Detalhes da Remessa Nº: {remessa['num_remessa']}")

    p.setFont("Helvetica", 12)
    y_position = height - 1.5 * inch

    def draw_line(label, value, y):
        p.setFont("Helvetica-Bold", 12)
        p.drawString(inch, y, f"{label}:")
        p.setFont("Helvetica", 12)
        p.drawString(inch + 2 * inch, y, str(value) if value is not None else "N/A")
        return y - 0.3 * inch

    y_position = draw_line("Número do Processo", remessa['num_processo'], y_position)
    y_position = draw_line("Nome do Proponente", remessa['nome_proponente'], y_position)
    y_position = draw_line("CPF/CNPJ", remessa['cpf_cnpj'], y_position)
    y_position = draw_line("Número do Convênio", remessa['num_convenio'], y_position)
    y_position = draw_line("Situação", remessa['situacao'], y_position)
    y_position = draw_line("Data da Remessa", remessa['dt_remessa'].strftime('%d/%m/%Y') if remessa['dt_remessa'] else "N/A", y_position)
    y_position = draw_line("Concedente", remessa['concedente_nome'], y_position)
    y_position = draw_line("Usuário Responsável", remessa['usuario_nome'], y_position)
    y_position = draw_line("Banco", remessa['banco_nome'], y_position)

    p.showPage()
    p.save()

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=remessa_{remessa["num_remessa"]}.pdf'
    
    return response

# ===========================
# CRUD - CONTAS CONVÊNIO
# ===========================

@views_bp.route('/contas-convenio')
def contas_convenio():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = """
        SELECT *,
        (SELECT num_processo FROM remessa WHERE remessa.id_remessa = conta_convenio.id_remessa) AS num_processo,
        (SELECT nome_proponente FROM remessa WHERE remessa.id_remessa = conta_convenio.id_remessa) AS nome_proponente,
        (SELECT nome_agencia FROM agencia WHERE agencia.id_agencia = conta_convenio.id_agencia) AS nome_agencia,
        (SELECT nome FROM banco WHERE banco.id_banco = (SELECT id_banco FROM agencia WHERE agencia.id_agencia = conta_convenio.id_agencia)) AS banco_nome
        FROM conta_convenio
        ORDER BY dt_abertura DESC;
    """
    contas_list = execute_query(query)
    
    return render_template('contas-convenio/list.html', contas=contas_list)

@views_bp.route('/contas-convenio/criar', methods=['GET', 'POST'])
def criar_conta_convenio():
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        num_conta = request.form.get('num_conta')
        dv_conta = request.form.get('dv_conta')
        dt_abertura = request.form.get('dt_abertura')
        id_remessa = request.form.get('id_remessa')
        id_agencia = request.form.get('id_agencia')
        
        query = """
            INSERT INTO conta_convenio (num_conta, dv_conta, dt_abertura, id_remessa, id_agencia)
            VALUES (%s, %s, %s, %s, %s)
        """
        result = execute_query(query, (num_conta, dv_conta, dt_abertura, id_remessa, id_agencia), fetch=False)
        
        if result:
            flash('Conta de convênio criada com sucesso!', 'success')
            return redirect(url_for('views.contas_convenio'))
        else:
            flash('Erro ao criar conta de convênio.', 'error')
    
    # Buscar dados para formulário
    query_remessas = "SELECT * FROM remessa ORDER BY num_processo"
    remessas = execute_query(query_remessas)
    
    query_agencias = """
        SELECT *,
        (SELECT nome FROM banco WHERE banco.id_banco = agencia.id_banco) AS banco_nome
        FROM agencia
        ORDER BY nome_agencia;
    """
    agencias = execute_query(query_agencias)
    
    return render_template('contas-convenio/create.html', remessas=remessas, agencias=agencias)

@views_bp.route('/contas-convenio/editar/<int:id_conta_convenio>', methods=['GET', 'POST'])
def editar_conta_convenio(id_conta_convenio):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        num_conta = request.form.get('num_conta')
        dv_conta = request.form.get('dv_conta')
        dt_abertura = request.form.get('dt_abertura')
        id_remessa = request.form.get('id_remessa')
        id_agencia = request.form.get('id_agencia')
        
        query = """
            UPDATE conta_convenio 
            SET num_conta = %s, dv_conta = %s, dt_abertura = %s, id_remessa = %s, id_agencia = %s
            WHERE id_conta_convenio = %s
        """
        result = execute_query(query, (num_conta, dv_conta, dt_abertura, id_remessa, id_agencia, id_conta_convenio), fetch=False)
        
        if result:
            flash('Conta de convênio atualizada com sucesso!', 'success')
            return redirect(url_for('views.contas_convenio'))
        else:
            flash('Erro ao atualizar conta de convênio.', 'error')
    
    # GET - Buscar dados da conta para edição
    query = """
        SELECT *,
        (SELECT num_processo FROM remessa WHERE remessa.id_remessa = cc.id_remessa) AS num_processo,
        (SELECT nome_agencia FROM agencia WHERE agencia.id_agencia = cc.id_agencia) AS nome_agencia,
<<<<<<< HEAD
        (SELECT nome FROM banco WHERE banco.id_banco = (SELECT id_banco FROM agencia WHERE agencia.id_agencia = cc.id_agencia)) AS banco_nome
=======
        (SELECT nome FROM banco WHERE banco.id_banco = (SELECT id_banco FROM agencia WHERE agencia.id_agencia = cc.id_agencia) AS banco_nome
>>>>>>> cc6496e378aa030fad768eface98cc66458af699
        FROM conta_convenio cc
        WHERE cc.id_conta_convenio = %s
    """
    conta = execute_query(query, (id_conta_convenio,))
    
    # Buscar dados para formulário
    query_remessas = "SELECT * FROM remessa ORDER BY num_processo"
    remessas = execute_query(query_remessas)
    
    query_agencias = """
        SELECT *,
        (SELECT nome FROM banco WHERE banco.id_banco = agencia.id_banco) AS banco_nome
        FROM agencia
        ORDER by nome_agencia;
    """
    agencias = execute_query(query_agencias)
    
    if not conta:
        flash('Conta de convênio não encontrada.', 'error')
        return redirect(url_for('views.contas_convenio'))
    
    return render_template('contas-convenio/edit.html', conta=conta[0], remessas=remessas, agencias=agencias)

@views_bp.route('/contas-convenio/excluir/<int:id_conta_convenio>', methods=['POST'])
def excluir_conta_convenio(id_conta_convenio):
    if 'user_id' not in session:
        return redirect(url_for('views.login'))
    
    query = "DELETE FROM conta_convenio WHERE id_conta_convenio = %s"
    result = execute_query(query, (id_conta_convenio,), fetch=False)
    
    if result:
        flash('Conta de convênio excluída com sucesso!', 'success')
    else:
        flash('Erro ao excluir conta de convênio.', 'error')
    
    return redirect(url_for('views.contas_convenio'))
