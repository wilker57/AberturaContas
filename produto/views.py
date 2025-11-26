from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request,
    flash,
    make_response,
)
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import io
from functools import wraps


views_bp = Blueprint("views", __name__)

# ===========================
# CONFIG / DB / HELPERS
# ===========================

DB_CONFIG = {
    "host": "localhost",
    "database": "abertura_contas",
    "user": "postgres",
    "password": "wil874408",
    "port": 5432,
}

# Conexão com o banco de dados
def get_db_connection():
    """Cria uma conexão com o banco de dados PostgreSQL."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"[DB] Erro ao conectar: {e}")
        return None

# Função genérica para executar queries
def _run_query(query, params=None, fetch_mode="all"):

    """
    Função interna genérica para executar queries.
    
    fetch_mode:
      - 'all'      -> retorna lista de registros (SELECT)
      - 'one'      -> retorna um único registro ou None
      - 'rowcount' -> retorna número de linhas afetadas (INSERT/UPDATE/DELETE)
    """
    # Abre conexão
    conn = get_db_connection()
    if not conn:
        return None
    # Define cursor
    params = params or ()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    # Execução da query
    try:
        cursor.execute(query, params)
    # Obtém resultado conforme modo
        if fetch_mode == "all":
            result = cursor.fetchall()
        elif fetch_mode == "one":
            result = cursor.fetchone()
        elif fetch_mode == "rowcount":
            result = cursor.rowcount
        else:
            result = None

        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        print(f"[DB] ERRO SQL - Query: {query}")
        print(f"[DB] ERRO SQL - Params: {params}")
        print(f"[DB] ERRO SQL - Detalhes: {e} ({type(e).__name__})")
        return None
    finally:
        cursor.close()
        conn.close()

# Retorna todos os registros
def fetch_all(query, params=None):
    return _run_query(query, params, fetch_mode="all") or []

# Retorna um único registro
def fetch_one(query, params=None):
    return _run_query(query, params, fetch_mode="one")

# INSERT/UPDATE/DELETE
def execute(query, params=None):
    """INSERT/UPDATE/DELETE - retorna número de linhas afetadas ou None."""
    return _run_query(query, params, fetch_mode="rowcount")

# Contagem de registros
# executa query de contagem
def count(table_name, where_clause=None, params=None):
    """Retorna COUNT(*) de uma tabela, com cláusula WHERE"""
    query = f"SELECT COUNT(*) AS total FROM {table_name}"
    # Adiciona cláusula WHERE se fornecida
    if where_clause:
        query += f" WHERE {where_clause}"
    row = fetch_one(query, params)
    return row["total"] if row else 0


# ===========================
# SENHAS
# ===========================

# Gerar hash de senha
def generate_password_hash(password):
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")

# Verificar senha
def check_password_hash(hashed_password, password):
    # Verifica se a senha corresponde ao hash armazenado
    try:
        password_bytes = password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"[AUTH] Erro na verificação de senha: {e}")
        return False


# ===========================
# DECORATOR DE LOGIN
# ===========================

# Decorator para exigir login

def login_required(view_func):
    """Decorator simples para exigir login em rotas protegidas."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("views.login"))
        return view_func(*args, **kwargs)

    return wrapper


# ===========================
# AUTENTICAÇÃO
# ===========================

# ROTA RAIZ
@views_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("views.login"))
    return redirect(url_for("views.dashboard"))

# LOGIN metodos GET e POST
@views_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_input = request.form.get("login")
        senha = request.form.get("senha")
# Validação básica
        if not login_input or not senha:
            flash("Login e senha são obrigatórios", "error")
            return render_template("auth/login.html")
# Busca usuário no banco
        user = fetch_one(
            """
            SELECT id_usuario, login, nome, senha, perfil_enum
            FROM usuario
            WHERE login = %s
            """,
            (login_input,),
        )
# Verifica senha correspondente ao usuário
        if user and user["senha"] and check_password_hash(user["senha"], senha):
            session["user_id"] = user["id_usuario"]
            session["user_name"] = user["nome"]
            session["user_profile"] = user["perfil_enum"]

            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("views.dashboard"))

        flash("Login ou senha inválidos", "error")

    return render_template("auth/login.html")

# REGISTRO
@views_bp.route("/registrar", methods=["GET", "POST"])
def registrar():
    form_data = {}
# Carrega dados do formulário se houver
    if request.method == "POST":
        form_data = request.form.to_dict()

        nome = form_data.get("nome")
        matricula = form_data.get("matricula")
        email = form_data.get("email")
        instituicao = form_data.get("instituicao")
        login_input = form_data.get("login")
        senha = form_data.get("senha")
        perfil_enum = form_data.get("perfil_enum", "MONITOR")
        status_enum = form_data.get("status_enum", "ATIVO").upper()
        status_enum = form_data.get("status_enum", "ATIVO").upper()
    # Validação básica
        if not all([nome, matricula, email, instituicao, login_input, senha]):
            flash("Todos os campos são obrigatórios!", "error")
            return render_template("auth/register.html", form_data=form_data)
        
        # Verifica se já existe usuário com mesmo login, email ou matrícula
        existing = fetch_one(
            """
            SELECT COUNT(*) AS count
            FROM usuario
            WHERE login = %s OR email = %s OR matricula = %s
            """,
            (login_input, email, matricula),
        )
        if existing and existing["count"] > 0:
            flash("Usuário com este login, email ou matrícula já existe!", "error")
            return render_template("auth/register.html", form_data=form_data)
    # Gera hash da senha
        senha_hash = generate_password_hash(senha)
    # insere novo usuário
        result = execute(
            """
            INSERT INTO usuario (nome, matricula, email, instituicao, login, senha, perfil_enum, status_enum)
            VALUES (%s, %s, %s, %s, %s, %s, %s::perfilenum, %s::statusenum)
            """,
            (nome, matricula, email, instituicao, login_input, senha_hash, perfil_enum, status_enum),
        )
    # se o resultado for positivo, redireciona para login
        if result and result > 0:
            flash("Usuário cadastrado com sucesso!", "success")
            return redirect(url_for("views.login"))

        flash("Erro ao cadastrar usuário. Tente novamente.", "error")
        return render_template("auth/register.html", form_data=form_data)

    return render_template("auth/register.html", form_data=form_data)

# ESQUECI MINHA SENHA
@views_bp.route("/esqueci-senha", methods=["GET", "POST"])
def forgot_password():
    form_data = {}
    show_new_password = False

    if request.method == "POST":
        form_data = request.form.to_dict()
        email = form_data.get("email", "").strip()
        stage = form_data.get("stage", "verify")

        if not email:
            flash("Informe o e-mail cadastrado.", "error")
            return render_template("auth/forgot-password.html", form_data=form_data, show_new_password=False)

        usuario = fetch_one(
            "SELECT id_usuario FROM usuario WHERE email = %s",
            (email,),
        )

        if not usuario:
            flash("E-mail não encontrado.", "error")
            return render_template("auth/forgot-password.html", form_data=form_data, show_new_password=False)

        if stage == "reset":
            nova_senha = form_data.get("nova_senha", "").strip()
            confirmar_senha = form_data.get("confirmar_senha", "").strip()

            if not all([nova_senha, confirmar_senha]):
                flash("Informe a nova senha e a confirmação.", "error")
                show_new_password = True
                return render_template("auth/forgot-password.html", form_data=form_data, show_new_password=show_new_password)

            if nova_senha != confirmar_senha:
                flash("As senhas digitadas não conferem.", "error")
                show_new_password = True
                return render_template("auth/forgot-password.html", form_data=form_data, show_new_password=show_new_password)

            senha_hash = generate_password_hash(nova_senha)
            result = execute(
                "UPDATE usuario SET senha = %s WHERE email = %s",
                (senha_hash, email),
            )

            if result and result > 0:
                flash("Senha redefinida com sucesso. Faça login com a nova senha.", "success")
                return redirect(url_for("views.login"))

            flash("Não foi possível redefinir a senha. Tente novamente.", "error")
            show_new_password = True
        else:
            # E-mail válido encontrado, exibe campos de nova senha
            flash("E-mail encontrado. Informe a nova senha.", "info")
            show_new_password = True

    return render_template("auth/forgot-password.html", form_data=form_data, show_new_password=show_new_password)

# LOGOUT
@views_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso!", "info")
    return redirect(url_for("views.login"))


# ===========================
# DASHBOARD
# ===========================


@views_bp.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "total_usuarios": count("usuario"),
        "total_bancos": count("banco"),
        "total_agencias": count("agencia"),
        "total_remessas": count("remessa"),
        "total_concedentes": count("concedente"),
        "total_contas": count("conta_convenio"),
    }
    # Contagem por situação de remessa
    remessas = {
        "preparacao": count("remessa", "situacao = 'Em Preparação'"),
        "enviado": count("remessa", "situacao = 'Enviado'"),
        "aguardando": count("remessa", "situacao = 'Aguardando retorno'"),
        "pendente": count("remessa", "situacao = 'Pendente de envio'"),
        "aberta": count("remessa", "situacao = 'Conta Aberta'"),
        "erro": count("remessa", "situacao = 'Erro'"),
        "aprovado": count("remessa", "situacao = 'Aprovado'"),
    }

    return render_template("dashboard.html", stats=stats, remessas=remessas)


# ===========================
# CRUD - BANCOS
# ===========================
# Adiciona filtro de busca se fornecido



@views_bp.route("/bancos")
@login_required
def bancos():
    search_term = request.args.get("search", "").strip() #strip retira espaços em branco
    query = "SELECT * FROM banco"
    params = []
#CAST converte id_banco para texto para permitir busca parcial
#ILIKE igenora maiúsculas/minúsculas
    if search_term:
        query += """
 WHERE (
        CAST(id_banco AS TEXT) ILIKE %s OR
        nome ILIKE %s
 )
        """
        like = f"%{search_term}%"
        params.extend([like, like])

    query += " ORDER BY id_banco, nome"

    bancos_list = fetch_all(query, params)
    return render_template(
        "bancos/list.html",
        bancos=bancos_list,
        search_term=search_term,
    )


@views_bp.route("/bancos/criar", methods=["GET", "POST"])
@login_required
def criar_banco():
    form_data = {}
# Carrega dados do formulário se houver
    if request.method == "POST":
        form_data = request.form.to_dict()
        id_banco = form_data.get("id_banco")
        nome = form_data.get("nome")
    # Validação básica
        if not id_banco or not nome:
            flash("Código do Banco e Nome são obrigatórios.", "error")
            return render_template("bancos/create.html", form_data=form_data)
    # Tenta inserir novo banco
        result = execute(
            "INSERT INTO banco (id_banco, nome) VALUES (%s, %s)",
            (id_banco, nome),
        )
    # Verifica resultado
        if result and result > 0:
            flash("Banco criado com sucesso!", "success")
            return redirect(url_for("views.bancos"))
    # Erro ao inserir
        flash("Erro ao criar banco. Verifique se o código já existe.", "error")
        return render_template("bancos/create.html", form_data=form_data)

    return render_template("bancos/create.html", form_data=form_data)


@views_bp.route("/bancos/editar/<int:id_banco>", methods=["GET", "POST"])
@login_required
def editar_banco(id_banco):
    if request.method == "POST":
        nome = request.form.get("nome")
        result = execute(
            "UPDATE banco SET nome = %s WHERE id_banco = %s",
            (nome, id_banco),
        )

        if result and result > 0:
            flash("Banco atualizado com sucesso!", "success")
            return redirect(url_for("views.bancos"))

        flash("Erro ao atualizar banco.", "error")

    banco = fetch_one("SELECT * FROM banco WHERE id_banco = %s", (id_banco,))
    if not banco:
        flash("Banco não encontrado.", "error")
        return redirect(url_for("views.bancos"))
    # RENDERIZA FORMULÁRIO COM DADOS ATUAIS
    return render_template("bancos/edit.html", banco=banco)


@views_bp.route("/bancos/excluir/<int:id_banco>", methods=["POST"])
@login_required
def excluir_banco(id_banco):
    print(f"[DEBUG] Tentando excluir banco id_banco={id_banco}")

    # SELECT na própria tabela
    banco = fetch_one("SELECT * FROM banco WHERE id_banco = %s", (id_banco,))
    print(f"[DEBUG] Banco encontrado: {banco}")

    if not banco:
        flash("Banco não encontrado (id inválido).", "error")
        return redirect(url_for("views.bancos"))

    # Verifica dependência: agência vinculada
    agencia_vinculada = fetch_one(
        "SELECT 1 FROM agencia WHERE id_banco = %s LIMIT 1",
        (id_banco,),
    )
    if agencia_vinculada:
        flash(
            "Não é possível excluir o banco: existem agências vinculadas a ele.",
            "error",
        )
        return redirect(url_for("views.bancos"))

    # Tenta excluir
    try:
        result = execute("DELETE FROM banco WHERE id_banco = %s", (id_banco,))
        print(f"[DEBUG] Resultado do DELETE banco: {result}")
    except Exception as e:
        print(f"[ERRO EXCLUIR BANCO] {e}")
        flash("Erro ao excluir banco (restrição no banco de dados).", "error")
        return redirect(url_for("views.bancos"))

    if result and result > 0:
        flash("Excluído com sucesso!", "success")
    else:
        flash("Erro ao excluir banco.", "error")

    return redirect(url_for("views.bancos"))




# ===========================
# CRUD - AGÊNCIAS
# ===========================


@views_bp.route("/agencias")
@login_required
def agencias():
    search_term = request.args.get("search", "").strip()
    base_query = """
        SELECT a.*,
               (SELECT nome FROM banco WHERE banco.id_banco = a.id_banco) AS banco_nome
          FROM agencia a
    """
    params = []
    filters = []

    if search_term:
        filters.append(
            """
            (
                a.nome_agencia ILIKE %s OR
                CAST(a.num_agencia AS TEXT) ILIKE %s
            )
            """
        )
        like = f"%{search_term}%"
        params.extend([like, like])

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    base_query += " ORDER BY a.nome_agencia, a.num_agencia"

    agencias_list = fetch_all(base_query, params)
    return render_template(
        "agencias/list.html",
        agencias=agencias_list,
        search_term=search_term,
    )


@views_bp.route("/agencias/criar", methods=["GET", "POST"])
@login_required
def criar_agencia():
    form_data = {}

    # Carrega bancos sempre
    bancos = fetch_all("SELECT * FROM banco ORDER BY nome")
    # Carrega dados do formulário se houver
    if request.method == "POST":
        form_data = request.form.to_dict()
        nome_agencia = form_data.get("nome_agencia")
        num_agencia = form_data.get("num_agencia")
        dv_agencia = form_data.get("dv_agencia")
        logradouro = form_data.get("logadouro")
        cidade = form_data.get("cidade")
        uf = form_data.get("uf")
        id_banco = form_data.get("id_banco")

        # Validação básica
        if not all([nome_agencia, num_agencia, dv_agencia, cidade, uf, id_banco]):
            flash("Preencha todos os campos obrigatórios.", "error")
            return render_template("agencias/create.html", bancos=bancos, form_data=form_data)

        result = execute(
            """
            INSERT INTO agencia (nome_agencia, num_agencia, dv_agencia, logadouro, cidade, uf, id_banco)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (nome_agencia, num_agencia, dv_agencia, logradouro, cidade, uf, id_banco),
        )

        if result and result > 0:
            flash("Agência criada com sucesso!", "success")
            return redirect(url_for("views.agencias"))

        flash("Erro ao criar agência.", "error")
        return render_template("agencias/create.html", bancos=bancos, form_data=form_data)

    return render_template("agencias/create.html", bancos=bancos, form_data=form_data)


@views_bp.route("/agencias/editar/<int:id_agencia>", methods=["GET", "POST"])
@login_required
def editar_agencia(id_agencia):
    # Buscar dados da agência
    agencia = fetch_one(
        """
        SELECT a.*,
               (SELECT nome FROM banco WHERE banco.id_banco = a.id_banco) AS banco_nome
        FROM agencia a
        WHERE a.id_agencia = %s;
        """,
        (id_agencia,),
    )
    if not agencia:
        flash("Agência não encontrada.", "error")
        return redirect(url_for("views.agencias"))
    
    # Carregar bancos para o select
    bancos = fetch_all("SELECT * FROM banco ORDER BY nome")

    if request.method == "POST":
        nome_agencia = request.form.get("nome_agencia")
        num_agencia = request.form.get("num_agencia")
        dv_agencia = request.form.get("dv_agencia")
        logradouro = request.form.get("logadouro")
        cidade = request.form.get("cidade")
        uf = request.form.get("uf")
        id_banco = request.form.get("id_banco")
    # editando agência
        result = execute(
            """
            UPDATE agencia
               SET nome_agencia = %s,
                   num_agencia  = %s,
                   dv_agencia   = %s,
                   logadouro    = %s,
                   cidade       = %s,
                   uf           = %s,
                   id_banco     = %s
             WHERE id_agencia   = %s
            """,
            (nome_agencia, num_agencia, dv_agencia, logradouro, cidade, uf, id_banco, id_agencia),
        )

        if result and result > 0:
            flash("Agência atualizada com sucesso!", "success")
            return redirect(url_for("views.agencias"))

        flash("Erro ao atualizar agência.", "error")

    return render_template("agencias/edit.html", agencia=agencia, bancos=bancos)


@views_bp.route("/agencias/excluir/<int:id_agencia>", methods=["POST"])
@login_required
def excluir_agencia(id_agencia):
    print(f"[DEBUG] Tentando excluir agência id_agencia={id_agencia}")

    # SELECT na própria tabela
    agencia = fetch_one(
        "SELECT * FROM agencia WHERE id_agencia = %s",
        (id_agencia,),
    )
    print(f"[DEBUG] Agência encontrada: {agencia}")

    if not agencia:
        flash("Agência não encontrada (id inválido).", "error")
        return redirect(url_for("views.agencias"))

    # Verifica dependência: conta_convenio vinculada
    conta_vinculada = fetch_one(
        "SELECT 1 FROM conta_convenio WHERE id_agencia = %s LIMIT 1",
        (id_agencia,),
    )
    if conta_vinculada:
        flash(
            "Não é possível excluir a agência: existem contas de convênio vinculadas.",
            "error",
        )
        return redirect(url_for("views.agencias"))

    # Tenta excluir
    try:
        result = execute("DELETE FROM agencia WHERE id_agencia = %s", (id_agencia,))
        print(f"[DEBUG] Resultado do DELETE agência: {result}")
    except Exception as e:
        print(f"[ERRO EXCLUIR AGENCIA] {e}")
        flash("Erro ao excluir agência (restrição no banco de dados).", "error")
        return redirect(url_for("views.agencias"))

    if result and result > 0:
        flash("Excluído com sucesso!", "success")
    else:
        flash("Erro ao excluir agência.", "error")

    return redirect(url_for("views.agencias"))



# ===========================
# CRUD - CONCEDENTES
# ===========================


@views_bp.route("/concedentes")
@login_required
def concedentes():
    search_term = request.args.get("search", "").strip()
    query = "SELECT * FROM concedente"
    params = []

    if search_term:
        query += """
 WHERE (
        sigla ILIKE %s OR
        nome ILIKE %s
 )
        """
        like = f"%{search_term}%"
        params.extend([like, like])

    query += " ORDER BY codigo_secretaria, sigla"

    concedentes_list = fetch_all(query, params)
    return render_template(
        "concedentes/list.html",
        concedentes=concedentes_list,
        search_term=search_term,
    )


@views_bp.route("/concedentes/criar", methods=["GET", "POST"])
@login_required
def criar_concedente():
    form_data = {}
    # Carrega dados do formulário se houver
    if request.method == "POST":
        form_data = request.form.to_dict()
        codigo_secretaria = form_data.get("codigo_secretaria")
        sigla = form_data.get("sigla")
        nome = form_data.get("nome")

        # Validação básica
        if not all([codigo_secretaria, sigla, nome]):
            flash("Todos os campos são obrigatórios.", "error")
            return render_template("concedentes/create.html", form_data=form_data)

        result = execute(
            """
            INSERT INTO concedente (codigo_secretaria, sigla, nome)
            VALUES (%s, %s, %s)
            """,
            (codigo_secretaria, sigla, nome),
        )

        # Verifica resultado
        if result and result > 0:
            flash("Concedente criado com sucesso!", "success")
            return redirect(url_for("views.concedentes"))

        flash("Erro ao criar concedente. Verifique os dados e tente novamente.", "error")
        return render_template("concedentes/create.html", form_data=form_data)

    return render_template("concedentes/create.html", form_data=form_data)


@views_bp.route("/concedentes/editar/<int:id_concedente>", methods=["GET", "POST"])
@login_required
def editar_concedente(id_concedente):
    concedente = fetch_one(
        "SELECT * FROM concedente WHERE id_concedente = %s",
        (id_concedente,),
    )
    if not concedente:
        flash("Concedente não encontrado.", "error")
        return redirect(url_for("views.concedentes"))

    if request.method == "POST":
        codigo_secretaria = request.form.get("codigo_secretaria")
        sigla = request.form.get("sigla")
        nome = request.form.get("nome")

        result = execute(
            """
            UPDATE concedente
               SET codigo_secretaria = %s,
                   sigla             = %s,
                   nome              = %s
             WHERE id_concedente     = %s
            """,
            (codigo_secretaria, sigla, nome, id_concedente),
        )

        if result and result > 0:
            flash("Concedente atualizado com sucesso!", "success")
            return redirect(url_for("views.concedentes"))

        flash("Erro ao atualizar concedente.", "error")

    return render_template("concedentes/edit.html", concedente=concedente)


@views_bp.route("/concedentes/excluir/<int:id_concedente>", methods=["POST"])
@login_required
def excluir_concedente(id_concedente):
    print(f"[DEBUG] Tentando excluir concedente id_concedente={id_concedente}")

    # 1) SELECT na própria tabela
    concedente = fetch_one(
        "SELECT * FROM concedente WHERE id_concedente = %s",
        (id_concedente,),
    )
    print(f"[DEBUG] Concedente encontrado: {concedente}")

    if not concedente:
        flash("Concedente não encontrado.", "error")
        return redirect(url_for("views.concedentes"))

    # 2) Verifica dependência: remessas vinculadas
    remessa_vinculada = fetch_one(
        "SELECT 1 FROM remessa WHERE id_concedente = %s LIMIT 1",
        (id_concedente,),
    )
    if remessa_vinculada:
        flash(
            "Não é possível excluir o concedente: existem remessas vinculadas a ele.",
            "error",
        )
        return redirect(url_for("views.concedentes"))

    # 3) Tenta excluir
    try:
        result = execute(
            "DELETE FROM concedente WHERE id_concedente = %s",
            (id_concedente,),
        )
        print(f"[DEBUG] Resultado do DELETE concedente: {result}")
    except Exception as e:
        print(f"[ERRO EXCLUIR CONCEDENTE] {e}")
        flash("Erro ao excluir concedente (restrição no banco de dados).", "error")
        return redirect(url_for("views.concedentes"))

    if result and result > 0:
        flash("Excluído com sucesso!", "success")
    else:
        flash("Erro ao excluir concedente.", "error")

    return redirect(url_for("views.concedentes"))




# ===========================
# CRUD - USUÁRIOS
# ===========================


@views_bp.route("/usuarios")
@login_required
def usuarios():
    search_term = request.args.get("search", "").strip()
    perfil_filter = request.args.get("perfil", "").strip().upper()
    status_filter = request.args.get("status", "").strip().upper()
    query = "SELECT * FROM usuario"
    params = []
    filters = []

    if search_term:
        filters.append("nome ILIKE %s")
        params.append(f"%{search_term}%")

    if perfil_filter:
        filters.append("perfil_enum = %s::perfilenum")
        params.append(perfil_filter)

    if status_filter:
        filters.append("status_enum = %s::statusenum")
        params.append(status_filter)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY nome"

    usuarios_list = fetch_all(query, params)
    return render_template(
        "usuarios/list.html",
        usuarios=usuarios_list,
        search_term=search_term,
        perfil_filter=perfil_filter,
        status_filter=status_filter,
    )


@views_bp.route("/usuarios/criar", methods=["GET", "POST"])
@login_required
def criar_usuario():
    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict()
        nome = form_data.get("nome")
        matricula = form_data.get("matricula")
        email = form_data.get("email")
        instituicao = form_data.get("instituicao")
        login_input = form_data.get("login")
        senha = form_data.get("senha")
        perfil_enum = form_data.get("perfil_enum", "MONITOR")
        status_enum = form_data.get("status_enum", "ATIVO").upper()

        if not all([nome, matricula, email, instituicao, login_input, senha]):
            flash("Todos os campos são obrigatórios.", "error")
            return render_template("usuarios/create.html", form_data=form_data)

        senha_hash = generate_password_hash(senha)

        result = execute(
            """
            INSERT INTO usuario (nome, matricula, email, instituicao, login, senha, perfil_enum, status_enum)
            VALUES (%s, %s, %s, %s, %s, %s, %s::perfilenum, %s::statusenum)
            """,
            (nome, matricula, email, instituicao, login_input, senha_hash, perfil_enum, status_enum),
        )

        if result and result > 0:
            flash("Usuário criado com sucesso!", "success")
            return redirect(url_for("views.usuarios"))

        flash("Erro ao criar usuário. Verifique se o login, e-mail ou matrícula já existem.", "error")
        return render_template("usuarios/create.html", form_data=form_data)

    return render_template("usuarios/create.html", form_data=form_data)


@views_bp.route("/usuarios/editar/<int:id_usuario>", methods=["GET", "POST"])
@login_required
def editar_usuario(id_usuario):
    usuario = fetch_one("SELECT * FROM usuario WHERE id_usuario = %s", (id_usuario,))
    if not usuario:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for("views.usuarios"))

    form_data = usuario.copy()

    if request.method == "POST":
        form_data = request.form.to_dict()
        nome = form_data.get("nome")
        matricula = form_data.get("matricula")
        email = form_data.get("email")
        instituicao = form_data.get("instituicao")
        login_input = form_data.get("login")
        perfil_enum = form_data.get("perfil_enum", usuario.get("perfil_enum"))
        status_enum = form_data.get("status_enum", usuario.get("status_enum", "ATIVO")).upper()
        nova_senha = form_data.get("nova_senha")

        if not all([nome, matricula, email, instituicao, login_input]):
            flash("Todos os campos obrigatórios devem ser preenchidos.", "error")
            # Preenche usuario exibido com o que o usuário digitou
            usuario_atualizado = {**usuario, **form_data}
            return render_template(
                "usuarios/edit.html",
                usuario=usuario_atualizado,
            )

        if nova_senha:
            senha_hash = generate_password_hash(nova_senha)
            result = execute(
                """
                UPDATE usuario
                   SET nome        = %s,
                       matricula   = %s,
                       email       = %s,
                       instituicao = %s,
                       login       = %s,
                       perfil_enum = %s::perfilenum,
                       status_enum = %s::statusenum,
                       senha       = %s
                 WHERE id_usuario  = %s
                """,
                (nome, matricula, email, instituicao, login_input, perfil_enum, status_enum, senha_hash, id_usuario),
            )
        else:
            result = execute(
                """
                UPDATE usuario
                   SET nome        = %s,
                       matricula   = %s,
                       email       = %s,
                       instituicao = %s,
                       login       = %s,
                       perfil_enum = %s::perfilenum,
                       status_enum = %s::statusenum
                 WHERE id_usuario  = %s
                """,
                (nome, matricula, email, instituicao, login_input, perfil_enum, status_enum, id_usuario),
            )

        if result and result > 0:
            flash("Usuário atualizado com sucesso!", "success")
            return redirect(url_for("views.usuarios"))

        flash("Erro ao atualizar usuário.", "error")
        usuario_atualizado = {**usuario, **form_data}
        return render_template("usuarios/edit.html", usuario=usuario_atualizado)

    return render_template("usuarios/edit.html", usuario=usuario)


@views_bp.route("/usuarios/excluir/<int:id_usuario>", methods=["POST"])
@login_required
def excluir_usuario(id_usuario):
    print(f"[DEBUG] Tentando excluir usuário id_usuario={id_usuario}")

    # 1) SELECT na própria tabela
    usuario = fetch_one("SELECT * FROM usuario WHERE id_usuario = %s", (id_usuario,))
    print(f"[DEBUG] Usuário encontrado: {usuario}")

    if not usuario:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for("views.usuarios"))

    # 2) Verifica dependência: remessas vinculadas
    remessa_vinculada = fetch_one(
        "SELECT 1 FROM remessa WHERE id_usuario = %s LIMIT 1",
        (id_usuario,),
    )
    if remessa_vinculada:
        flash(
            "Não é possível excluir o usuário: existem remessas vinculadas a ele.",
            "error",
        )
        return redirect(url_for("views.usuarios"))

    # 3) Tenta excluir
    try:
        result = execute("DELETE FROM usuario WHERE id_usuario = %s", (id_usuario,))
        print(f"[DEBUG] Resultado do DELETE usuário: {result}")
    except Exception as e:
        print(f"[ERRO EXCLUIR USUARIO] {e}")
        flash("Erro ao excluir usuário (restrição no banco de dados).", "error")
        return redirect(url_for("views.usuarios"))

    if result and result > 0:
        flash("Excluído com sucesso!", "success")
    else:
        flash("Erro ao excluir usuário.", "error")

    return redirect(url_for("views.usuarios"))



# ===========================
# CRUD - REMESSAS
# ===========================


@views_bp.route("/remessas")
@login_required
def remessas():
    # Filtros de busca
    search_term = request.args.get("search", "").strip()
    # data a partir de
    date_from = request.args.get("date_from", "").strip()
    situacao_filter = request.args.get("situacao", "").strip()

    base_query = """
        SELECT
            r.*,
            (
                SELECT ag.nome_agencia
                FROM agencia ag
                WHERE ag.id_agencia = (
                    SELECT MIN(cc.id_agencia)
                    FROM conta_convenio cc
                    WHERE cc.id_remessa = r.id_remessa
                )
            ) AS nome_agencia,
            (SELECT c.nome FROM concedente c WHERE c.id_concedente = r.id_concedente) AS concedente_nome,
            (SELECT u.nome FROM usuario u WHERE u.id_usuario = r.id_usuario) AS usuario_nome,
            (SELECT b.nome FROM banco b WHERE b.id_banco = r.id_banco) AS banco_nome
        FROM remessa r
    """
    # Construir cláusula WHERE 
    filters = []
    params = []
    # Filtro de busca geral (nome do proponente)
    if search_term:
        filters.append("r.nome_proponente ILIKE %s")
        params.append(f"%{search_term}%")
    if situacao_filter:
        filters.append("r.situacao = %s")
        params.append(situacao_filter)
    # Filtro de data
    if date_from:
        filters.append("DATE(r.dt_remessa) = %s")
        params.append(date_from)
    # Adiciona filtros à query principal
    if filters:
        base_query += " WHERE " + " AND ".join(filters)
    # Ordenação por nome do proponente
    base_query += " ORDER BY r.nome_proponente"
    
    remessas_list = fetch_all(base_query, params)
    return render_template(
        "remessas/list.html",
        remessas=remessas_list,
        search_term=search_term,
        date_from=date_from,
        situacao_filter=situacao_filter,
    )


@views_bp.route("/remessas/criar", methods=["GET", "POST"])
@login_required
def criar_remessa():
    form_data = {}

    # Buscar dados para formulário 
    concedentes = fetch_all("SELECT * FROM concedente ORDER BY nome")
    bancos = fetch_all("SELECT * FROM banco ORDER BY nome")

    if request.method == "POST":
        form_data = request.form.to_dict()

        num_processo = form_data.get("num_processo")
        nome_proponente = form_data.get("nome_proponente")
        cpf_cnpj = form_data.get("cpf_cnpj")
        num_convenio = form_data.get("num_convenio")
        situacao = form_data.get("situacao", "Em Preparação")
        id_concedente = form_data.get("id_concedente")
        id_banco = form_data.get("id_banco")

        if not all([num_processo, nome_proponente, cpf_cnpj, num_convenio, id_concedente]):
            flash("Todos os campos obrigatórios devem ser preenchidos!", "error")
            return render_template(
                "remessas/create.html",
                concedentes=concedentes,
                bancos=bancos,
                form_data=form_data,
            )

        # Próximo número de remessa
        resultado_max = fetch_one(
            "SELECT COALESCE(MAX(num_remessa), 0) + 1 AS proximo_num FROM remessa"
        )
        proximo_num_remessa = resultado_max["proximo_num"] if resultado_max else 1

        query_insert = """
            INSERT INTO remessa (
                num_processo, nome_proponente, cpf_cnpj, num_convenio,
                situacao, num_remessa, id_concedente, id_usuario, id_banco
            ) VALUES (
                %s, %s, %s, %s, %s::situacao_enum, %s, %s, %s, %s
            )
        """
    #inserir remessa
        try:
            result = execute(
                query_insert,
                (
                    num_processo,
                    nome_proponente,
                    cpf_cnpj,
                    num_convenio,
                    situacao,
                    proximo_num_remessa,
                    id_concedente,
                    session["user_id"],
                    id_banco,
                ),
            )
        except Exception:
            flash("Erro ao criar remessa (erro no banco de dados).", "error")
            return render_template(
                "remessas/create.html",
                concedentes=concedentes,
                bancos=bancos,
                form_data=form_data,
            )

        if result and result > 0:
            flash("Remessa criada com sucesso!", "success")
            return redirect(url_for("views.remessas"))

        flash("Erro ao criar remessa.", "error")
        return render_template(
            "remessas/create.html",
            concedentes=concedentes,
            bancos=bancos,
            form_data=form_data,
        )

    # GET
    return render_template(
        "remessas/create.html",
        concedentes=concedentes,
        bancos=bancos,
        form_data=form_data,
    )


@views_bp.route("/remessas/editar/<int:id_remessa>", methods=["GET", "POST"])
@login_required
def editar_remessa(id_remessa):
    # Buscar dados para carregar a edição
    remessa = fetch_one(
        """
        SELECT r.*,
               (SELECT nome FROM concedente c WHERE c.id_concedente = r.id_concedente) AS concedente_nome,
               (SELECT nome FROM banco b       WHERE b.id_banco      = r.id_banco)      AS banco_nome
          FROM remessa r
         WHERE r.id_remessa = %s
        """,
        (id_remessa,),
    )
    if not remessa:
        flash("Remessa não encontrada.", "error")
        return redirect(url_for("views.remessas"))

    concedentes = fetch_all("SELECT * FROM concedente ORDER BY nome")
    bancos = fetch_all("SELECT * FROM banco ORDER BY nome")

    if request.method == "POST":
        num_processo = request.form.get("num_processo")
        nome_proponente = request.form.get("nome_proponente")
        cpf_cnpj = request.form.get("cpf_cnpj")
        num_convenio = request.form.get("num_convenio")
        situacao = request.form.get("situacao")
        id_concedente = request.form.get("id_concedente")
        id_banco = request.form.get("id_banco")

        result = execute(
            """
            UPDATE remessa
               SET num_processo    = %s,
                   nome_proponente = %s,
                   cpf_cnpj        = %s,
                   num_convenio    = %s,
                   situacao        = %s::situacao_enum,
                   id_concedente   = %s,
                   id_banco        = %s
             WHERE id_remessa      = %s
            """,
            (
                num_processo,
                nome_proponente,
                cpf_cnpj,
                num_convenio,
                situacao,
                id_concedente,
                id_banco,
                id_remessa,
            ),
        )

        if result and result > 0:
            flash("Remessa atualizada com sucesso!", "success")
            return redirect(url_for("views.remessas"))

        flash("Erro ao atualizar remessa.", "error")

    return render_template(
        "remessas/edit.html",
        remessa=remessa,
        concedentes=concedentes,
        bancos=bancos,
    )


@views_bp.route("/remessas/excluir/<int:id_remessa>", methods=["POST"])
@login_required
def excluir_remessa(id_remessa):
    print(f"[DEBUG] Tentando excluir remessa id_remessa={id_remessa}")

    remessa = fetch_one("SELECT * FROM remessa WHERE id_remessa = %s", (id_remessa,))
    print(f"[DEBUG] Remessa encontrada: {remessa}")

    if not remessa:
        flash("Remessa não encontrada.", "error")
        return redirect(url_for("views.remessas"))

    # Verifica se há conta_convenio vinculada
    conta_vinculada = fetch_one(
        "SELECT 1 FROM conta_convenio WHERE id_remessa = %s LIMIT 1",
        (id_remessa,),
    )
    if conta_vinculada:
        flash(
            "Não é possível excluir a remessa: existem contas de convênio vinculadas.",
            "error",
        )
        return redirect(url_for("views.remessas"))

    try:
        result = execute("DELETE FROM remessa WHERE id_remessa = %s", (id_remessa,))
        print(f"[DEBUG] Resultado do DELETE remessa: {result}")
    except Exception as e:
        print(f"[ERRO EXCLUIR REMESSA] {e}")
        flash("Erro ao excluir remessa (restrição no banco de dados).", "error")
        return redirect(url_for("views.remessas"))

    if result and result > 0:
        flash("Excluído com sucesso!", "success")
    else:
        flash("Erro ao excluir remessa.", "error")

    return redirect(url_for("views.remessas"))



@views_bp.route("/remessas/visualizar/<int:id_remessa>")
@login_required
def visualizar_remessa(id_remessa):
    # Buscar dados completos da remessa
    query = """
        SELECT
            r.*,
            (SELECT c.nome FROM concedente c WHERE c.id_concedente = r.id_concedente) AS concedente_nome,
            (SELECT u.nome FROM usuario   u WHERE u.id_usuario    = r.id_usuario)    AS usuario_nome,
            (SELECT b.nome FROM banco     b WHERE b.id_banco      = r.id_banco)      AS banco_nome
        FROM remessa r
        WHERE r.id_remessa = %s
    """
    remessa = fetch_one(query, (id_remessa,))

    if not remessa:
        flash("Remessa não encontrada.", "error")
        return redirect(url_for("views.remessas"))

    # Apenas renderiza a página de visualização
    return render_template("remessas/view.html", remessa=remessa)



# ===========================
# CRUD - CONTAS CONVÊNIO
# ===========================


@views_bp.route("/contas-convenio")
@login_required
def contas_convenio():
    search_term = request.args.get("search", "").strip()
    base_query = """
        SELECT
            cc.*,
            (SELECT r.num_processo FROM remessa r WHERE r.id_remessa = cc.id_remessa) AS num_processo,
            (SELECT r.nome_proponente FROM remessa r WHERE r.id_remessa = cc.id_remessa) AS nome_proponente,
            (SELECT a.nome_agencia FROM agencia a WHERE a.id_agencia = cc.id_agencia) AS nome_agencia,
            (
                SELECT b.nome
                FROM banco b
                WHERE b.id_banco = (
                    SELECT ag.id_banco FROM agencia ag WHERE ag.id_agencia = cc.id_agencia
                )
            ) AS banco_nome
        FROM conta_convenio cc
    """
    params = []

    if search_term:
        base_query += """
 WHERE (
        (SELECT r.nome_proponente FROM remessa r WHERE r.id_remessa = cc.id_remessa) ILIKE %s
 )
        """
        like = f"%{search_term}%"
        params.extend([like])

    base_query += " ORDER BY cc.dt_abertura DESC"

    contas_list = fetch_all(base_query, params)
    return render_template(
        "contas-convenio/list.html",
        contas=contas_list,
        search_term=search_term,
    )


@views_bp.route("/contas-convenio/criar", methods=["GET", "POST"])
@login_required
def criar_conta_convenio():
    form_data = {}

    remessas = fetch_all("SELECT * FROM remessa ORDER BY nome_proponente, num_processo")
    agencias = fetch_all(
        """
        SELECT a.*,
               (SELECT nome FROM banco b WHERE b.id_banco = a.id_banco) AS banco_nome
          FROM agencia a
         ORDER BY banco_nome, a.nome_agencia;
        """
    )

    if request.method == "POST":
        form_data = request.form.to_dict()
        num_conta = form_data.get("num_conta")
        dv_conta = form_data.get("dv_conta")
        dt_abertura = form_data.get("dt_abertura")
        id_remessa = form_data.get("id_remessa")
        id_agencia = form_data.get("id_agencia")

        if not all([num_conta, dv_conta, dt_abertura, id_remessa, id_agencia]):
            flash("Todos os campos são obrigatórios.", "error")
            return render_template(
                "contas-convenio/create.html",
                remessas=remessas,
                agencias=agencias,
                form_data=form_data,
            )

        result = execute(
            """
            INSERT INTO conta_convenio (num_conta, dv_conta, dt_abertura, id_remessa, id_agencia)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (num_conta, dv_conta, dt_abertura, id_remessa, id_agencia),
        )

        if result and result > 0:
            flash("Conta de convênio criada com sucesso!", "success")
            return redirect(url_for("views.contas_convenio"))

        flash("Erro ao criar conta de convênio.", "error")

    return render_template(
        "contas-convenio/create.html",
        remessas=remessas,
        agencias=agencias,
        form_data=form_data,
    )


@views_bp.route("/contas-convenio/editar/<int:id_conta_convenio>", methods=["GET", "POST"])
@login_required
def editar_conta_convenio(id_conta_convenio):
    conta = fetch_one(
        """
        SELECT cc.*,
               (SELECT num_processo FROM remessa r WHERE r.id_remessa = cc.id_remessa) AS num_processo,
               (SELECT nome_agencia FROM agencia a WHERE a.id_agencia = cc.id_agencia) AS nome_agencia,
               (SELECT nome FROM banco b WHERE b.id_banco = (
                    SELECT id_banco FROM agencia a2 WHERE a2.id_agencia = cc.id_agencia
               )) AS banco_nome
          FROM conta_convenio cc
         WHERE cc.id_conta_convenio = %s
        """,
        (id_conta_convenio,),
    )
    if not conta:
        flash("Conta de convênio não encontrada.", "error")
        return redirect(url_for("views.contas_convenio"))

    remessas = fetch_all("SELECT * FROM remessa ORDER BY nome_proponente, num_processo")
    agencias = fetch_all(
        """
        SELECT a.*,
               (SELECT nome FROM banco b WHERE b.id_banco = a.id_banco) AS banco_nome
          FROM agencia a
         ORDER BY banco_nome, a.nome_agencia;
        """
    )

    if request.method == "POST":
        num_conta = request.form.get("num_conta")
        dv_conta = request.form.get("dv_conta")
        dt_abertura = request.form.get("dt_abertura")
        id_remessa = request.form.get("id_remessa")
        id_agencia = request.form.get("id_agencia")

        result = execute(
            """
            UPDATE conta_convenio
               SET num_conta   = %s,
                   dv_conta    = %s,
                   dt_abertura = %s,
                   id_remessa  = %s,
                   id_agencia  = %s
             WHERE id_conta_convenio = %s
            """,
            (num_conta, dv_conta, dt_abertura, id_remessa, id_agencia, id_conta_convenio),
        )

        if result and result > 0:
            flash("Conta de convênio atualizada com sucesso!", "success")
            return redirect(url_for("views.contas_convenio"))

        flash("Erro ao atualizar conta de convênio.", "error")

    return render_template(
        "contas-convenio/edit.html",
        conta=conta,
        remessas=remessas,
        agencias=agencias,
    )

@views_bp.route("/contas-convenio/excluir/<int:id_conta_convenio>", methods=["POST"])
@login_required
def excluir_conta_convenio(id_conta_convenio):
    print(f"[DEBUG] Tentando excluir conta_convenio id_conta_convenio={id_conta_convenio}")

    conta = fetch_one(
        "SELECT * FROM conta_convenio WHERE id_conta_convenio = %s",
        (id_conta_convenio,),
    )
    print(f"[DEBUG] Conta_convenio encontrada: {conta}")

    if not conta:
        flash("Conta de convênio não encontrada.", "error")
        return redirect(url_for("views.contas_convenio"))

    try:
        result = execute(
            "DELETE FROM conta_convenio WHERE id_conta_convenio = %s",
            (id_conta_convenio,),
        )
        print(f"[DEBUG] Resultado do DELETE conta_convenio: {result}")
    except Exception as e:
        print(f"[ERRO EXCLUIR CONTA_CONVENIO] {e}")
        flash("Erro ao excluir conta de convênio (restrição no banco de dados).", "error")
        return redirect(url_for("views.contas_convenio"))

    if result and result > 0:
        flash("Conta de convênio excluída com sucesso!", "success")
    else:
        flash("Erro ao excluir conta de convênio.", "error")

    return redirect(url_for("views.contas_convenio"))

