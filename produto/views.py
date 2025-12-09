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

from datetime import date





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



# Conexo com o banco de dados

def get_db_connection():

    """Cria uma conexo com o banco de dados PostgreSQL."""
    try:

        return psycopg2.connect(**DB_CONFIG)

    except Exception as e:

        print(f"[DB] Erro ao conectar: {e}")

        return None



# Funcao generica para executar queries

def _run_query(query, params=None, fetch_mode="all"):



    """

    Funo interna genrica para executar queries.

    

    fetch_mode:

      - 'all'      -> retorna lista de registros (SELECT)

      - 'one'      -> retorna um Ãºnico registro ou None

      - 'rowcount' -> retorna nÃºmero de linhas afetadas (INSERT/UPDATE/DELETE)

    """

    # Abre conexao

    conn = get_db_connection()

    if not conn:

        return None

    # Define cursor

    params = params or ()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Execucao da query

    try:

        cursor.execute(query, params)

    # Obtem resultado conforme modo

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



# Retorna um unico registro

def fetch_one(query, params=None):

    return _run_query(query, params, fetch_mode="one")



# INSERT/UPDATE/DELETE

def execute(query, params=None):

    """INSERT/UPDATE/DELETE - retorna nmero de linhas afetadas ou None."""

    return _run_query(query, params, fetch_mode="rowcount")



# Contagem de registros

# executa query de contagem

def count(table_name, where_clause=None, params=None):

    """Retorna COUNT(*) de uma tabela, com clusula WHERE"""

    query = f"SELECT COUNT(*) AS total FROM {table_name}"

    # Adiciona clusula WHERE se fornecida
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

        print(f"[AUTH] Erro na verificao de senha: {e}")

        return False



# Mapear perfil

def map_perfil_enum(value):

    """Mapeia valores de perfil para o formato correto do banco"""

    if not value:

        return "MONITOR"

    

    mapping = {

        "ADMINISTRADOR": "ADMIN",

        "ADMIN": "ADMIN",

        "Administrador": "ADMIN",

        "OPERADOR": "OPERADOR", 

        "Operador": "OPERADOR",

        "MONITOR": "MONITOR",

        "Monitor": "MONITOR"

    }

    return mapping.get(value, "MONITOR")

# Mapear status

def map_status_enum(value):

    """Mapeia valores de status para o formato correto do banco"""

    if not value:

        return "ATIVO"

    

    mapping = {

        "ATIVO": "ATIVO",

        "Ativo": "ATIVO",

        "INATIVO": "INATIVO",

        "Inativo": "INATIVO"

    }

    return mapping.get(value, "ATIVO")





# ===========================

# DECORATOR DE LOGIN

# ===========================



# Decorator para exigir login



def login_required(view_func):

    """Decorator simples para exigir login em rotas protegidas."""



    @wraps(view_func)

    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            flash(" Sua sesso expirou ou voc precisa fazer login para acessar esta pgina.", "warning")

            return redirect(url_for("views.login"))

        return view_func(*args, **kwargs)



    return wrapper





# ===========================

# AUTENTICACAO

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

# Validacao basica

        if not login_input or not senha:

            flash("Login e senha sao obrigatorios", "error")
            return render_template("auth/login.html")

# Busca usurio no banco
        user = fetch_one(

            """

            SELECT id_usuario, login, nome, senha, perfil_enum

            FROM usuario

            WHERE login = %s

            """,

            (login_input,),

        )

# Verifica senha correspondente ao usurio

        if user and user["senha"] and check_password_hash(user["senha"], senha):

            session["user_id"] = user["id_usuario"]

            session["user_name"] = user["nome"]

            session["user_profile"] = user["perfil_enum"]



            flash("Login realizado com sucesso!", "success")

            return redirect(url_for("views.dashboard"))



        flash("Usurio ou senha incorretos. Verifique suas credenciais e tente novamente.", "error")

        return redirect(url_for("views.login"))



    return render_template("auth/login.html")



# REGISTRO

@views_bp.route("/registrar", methods=["GET", "POST"])

def registrar():

    form_data = {}

# Carrega dados do formulario se houver

    if request.method == "POST":

        form_data = request.form.to_dict()



        nome = form_data.get("nome")

        matricula = form_data.get("matricula")

        email = form_data.get("email")

        instituicao = form_data.get("instituicao")

        login_input = form_data.get("login")

        senha = form_data.get("senha")

        perfil_enum = form_data.get("perfil_enum", "MONITOR")

        status_enum = form_data.get("status_enum", "ATIVO")

        

        

    # Validacao basica

        if not all([nome, matricula, email, instituicao, login_input, senha]):

            flash("Todos os campos sao obrigatorios!", "error")
            return redirect(url_for("views.registrar"))

        

        # Verifica se ja existe usuario com mesmo login, email ou matricula

        existing = fetch_one(

            """

            SELECT COUNT(*) AS count

            FROM usuario

            WHERE login = %s OR email = %s OR matricula = %s

            """,

            (login_input, email, matricula),

        )

        if existing and existing["count"] > 0:

            flash("Usurio com este login, email ou matrcula j existe!", "error")

            return render_template("auth/register.html", form_data=form_data)

    # Gera hash da senha

        senha_hash = generate_password_hash(senha)

    # insere novo usurio

        result = execute(

            """

            INSERT INTO usuario (nome, matricula, email, instituicao, login, senha, perfil_enum, status_enum)

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

            """,

            (nome, matricula, email, instituicao, login_input, senha_hash, perfil_enum, status_enum),

        )

    # se o resultado for positivo, redireciona para login

        if result and result > 0:

            flash("Usurio cadastrado com sucesso!", "success")

            return redirect(url_for("views.login"))



        flash("Erro ao cadastrar usurio. Tente novamente.", "error")

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

            flash("E-mail no encontrado.", "error")

            return render_template("auth/forgot-password.html", form_data=form_data, show_new_password=False)



        if stage == "reset":

            nova_senha = form_data.get("nova_senha", "").strip()

            confirmar_senha = form_data.get("confirmar_senha", "").strip()



            if not all([nova_senha, confirmar_senha]):

                flash("Informe a nova senha e a confirmao.", "error")

                show_new_password = True

                return render_template("auth/forgot-password.html", form_data=form_data, show_new_password=show_new_password)



            if nova_senha != confirmar_senha:

                flash("As senhas digitadas no conferem.", "error")

                show_new_password = True

                return render_template("auth/forgot-password.html", form_data=form_data, show_new_password=show_new_password)



            senha_hash = generate_password_hash(nova_senha)

            result = execute(

                "UPDATE usuario SET senha = %s WHERE email = %s",

                (senha_hash, email),

            )



            if result and result > 0:

                flash("Senha redefinida com sucesso. Faa login com a nova senha.", "success")

                return redirect(url_for("views.login"))



            flash("No foi possvel redefinir a senha. Tente novamente.", "error")

            show_new_password = True

        else:

            # E-mail vlido encontrado, exibe campos de nova senha

            flash("E-mail encontrado. Informe a nova senha.", "info")

            show_new_password = True



    return render_template("auth/forgot-password.html", form_data=form_data, show_new_password=show_new_password)



# LOGOUT

@views_bp.route("/logout")

def logout():

    session.clear()

    flash(" Sua sesso foi encerrada com sucesso. At logo!", "info")

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

    # Contagem por situacao de remessa
    remessas = {
        "preparacao": count("remessa", "situacao = 'Em Preparação'"),
        "enviado": count("remessa", "situacao = 'Enviado'"),
        "aguardando": count("remessa", "situacao = 'Aguardando retorno'"),
        "pendente": count("remessa", "situacao = 'Pendente de envio'"),
        "aberta": count("remessa", "situacao = 'Conta Aberta'"),
        "erro": count("remessa", "situacao = 'Erro'"),
    }

    return render_template("dashboard.html", stats=stats, remessas=remessas)


# ===========================

# CRUD - BANCOS

# ===========================









@views_bp.route("/bancos")

@login_required

def bancos():

    # Paginação

    page = request.args.get("page", 1, type=int)

    per_page = 5

    offset = (page - 1) * per_page

    

    search_term = request.args.get("search", "").strip()
    situacao_filter = request.args.get("situacao", "").strip()

    query = "SELECT * FROM banco"

    params = []

    

    where_clause = ""

    if search_term:

        where_clause = """

 WHERE (

        CAST(id_banco AS TEXT) ILIKE %s OR

        nome ILIKE %s

 )

        """

        like = f"%{search_term}%"

        params.extend([like, like])

    

    # Contar total

    count_query = f"SELECT COUNT(*) as count FROM banco{where_clause}"

    count_params = params[:]

    result = fetch_one(count_query, count_params)

    total_items = result['count'] if result else 0

    total_pages = (total_items + per_page - 1) // per_page

    

    query += where_clause

    query += " ORDER BY id_banco, nome LIMIT %s OFFSET %s"

    params.extend([per_page, offset])



    bancos_list = fetch_all(query, params)

    

    start_item = offset + 1 if bancos_list else 0

    end_item = min(offset + per_page, total_items)

    

    return render_template(

        "bancos/list.html",

        bancos=bancos_list,

        search_term=search_term,

        current_page=page,

        total_pages=total_pages,

        total_items=total_items,

        start_item=start_item,

        end_item=end_item,

    )





@views_bp.route("/bancos/criar", methods=["GET", "POST"])

@login_required

def criar_banco():

    form_data = {}

# Carrega dados do formulrio se houver

    if request.method == "POST":

        form_data = request.form.to_dict()

        id_banco = form_data.get("id_banco")

        nome = form_data.get("nome")

    # Validao bsica

        if not id_banco or not nome:

            flash("Cdigo do Banco e Nome so obrigatrios.", "error")
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

        flash("Erro ao criar banco. Verifique se o cdigo j existe.", "error")

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

        flash("Banco no encontrado.", "error")

        return redirect(url_for("views.bancos"))

    # RENDERIZA FORMULRIO COM DADOS ATUAIS
    return render_template("bancos/edit.html", banco=banco)





@views_bp.route("/bancos/excluir/<int:id_banco>", methods=["POST"])

@login_required

def excluir_banco(id_banco):

    print(f"[DEBUG] Tentando excluir banco id_banco={id_banco}")



    # SELECT na prpria tabela

    banco = fetch_one("SELECT * FROM banco WHERE id_banco = %s", (id_banco,))

    print(f"[DEBUG] Banco encontrado: {banco}")



    if not banco:

        flash("Banco no encontrado (id invlido).", "error")

        return redirect(url_for("views.bancos"))



    # Verifica dependencia: agencia vinculada

    agencia_vinculada = fetch_one(

        "SELECT 1 FROM agencia WHERE id_banco = %s LIMIT 1",

        (id_banco,),

    )

    if agencia_vinculada:

        flash(

            "No  possvel excluir o banco: existem agncias vinculadas a ele.",

            "error",

        )

        return redirect(url_for("views.bancos"))



    # Tenta excluir

    try:

        result = execute("DELETE FROM banco WHERE id_banco = %s", (id_banco,))

        print(f"[DEBUG] Resultado do DELETE banco: {result}")

    except Exception as e:

        print(f"[ERRO EXCLUIR BANCO] {e}")

        flash("Erro ao excluir banco (restricao no banco de dados).", "error")

        return redirect(url_for("views.bancos"))



    if result and result > 0:

        flash("Excluido com sucesso!", "success")

    else:

        flash("Erro ao excluir banco.", "error")



    return redirect(url_for("views.bancos"))









# ===========================

# CRUD - AGENCIAS

# ===========================





@views_bp.route("/agencias")

@login_required

def agencias():

    # Paginacao

    page = request.args.get("page", 1, type=int)

    per_page = 5

    offset = (page - 1) * per_page

    

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

    

    where_clause = ""

    if filters:

        where_clause = " WHERE " + " AND ".join(filters)

    

    # Contar total

    count_query = f"SELECT COUNT(*) as count FROM agencia a{where_clause}"

    count_params = params[:]

    result = fetch_one(count_query, count_params)

    total_items = result['count'] if result else 0

    total_pages = (total_items + per_page - 1) // per_page

    

    base_query += where_clause

    base_query += " ORDER BY a.nome_agencia, a.num_agencia LIMIT %s OFFSET %s" #offset serve para pular os primeiros registros

    params.extend([per_page, offset])



    agencias_list = fetch_all(base_query, params)

    

    start_item = offset + 1 if agencias_list else 0

    end_item = min(offset + per_page, total_items)

    

    return render_template(

        "agencias/list.html",

        agencias=agencias_list,

        search_term=search_term,

        current_page=page,

        total_pages=total_pages,

        total_items=total_items,

        start_item=start_item,

        end_item=end_item,

    )





@views_bp.route("/agencias/criar", methods=["GET", "POST"])

@login_required

def criar_agencia():

    form_data = {}



    # Carrega bancos sempre

    bancos = fetch_all("SELECT * FROM banco ORDER BY nome")

    # Carrega dados do formulario se houver

    if request.method == "POST":

        form_data = request.form.to_dict()

        nome_agencia = form_data.get("nome_agencia")

        num_agencia = form_data.get("num_agencia")

        dv_agencia = form_data.get("dv_agencia")

        logradouro = form_data.get("logadouro")

        cidade = form_data.get("cidade")

        uf = form_data.get("uf")

        id_banco = form_data.get("id_banco")



        # Validacao basica

        if not all([nome_agencia, num_agencia, dv_agencia, cidade, uf, id_banco]):

            flash("Preencha todos os campos obrigatorios.", "error")
            return render_template("agencias/create.html", bancos=bancos, form_data=form_data)



        result = execute(

            """

            INSERT INTO agencia (nome_agencia, num_agencia, dv_agencia, logadouro, cidade, uf, id_banco)

            VALUES (%s, %s, %s, %s, %s, %s, %s)

            """,

            (nome_agencia, num_agencia, dv_agencia, logradouro, cidade, uf, id_banco),

        )



        if result and result > 0:

            flash("Agencia criada com sucesso!", "success")

            return redirect(url_for("views.agencias"))



        flash("Erro ao criar agencia.", "error")

        return render_template("agencias/create.html", bancos=bancos, form_data=form_data)



    return render_template("agencias/create.html", bancos=bancos, form_data=form_data)





@views_bp.route("/agencias/editar/<int:id_agencia>", methods=["GET", "POST"])

@login_required

def editar_agencia(id_agencia):

    # Buscar dados da agencia

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

        flash("Agencia nao encontrada.", "error")

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

    # editando agencia

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

            flash("Agencia atualizada com sucesso!", "success")

            return redirect(url_for("views.agencias"))



        flash("Erro ao atualizar agencia.", "error")



    return render_template("agencias/edit.html", agencia=agencia, bancos=bancos)





@views_bp.route("/agencias/excluir/<int:id_agencia>", methods=["POST"])

@login_required

def excluir_agencia(id_agencia):

    print(f"[DEBUG] Tentando excluir agencia id_agencia={id_agencia}")



    # SELECT na propria tabela
    agencia = fetch_one(

        "SELECT * FROM agencia WHERE id_agencia = %s",

        (id_agencia,),

    )

    print(f"[DEBUG] Agencia encontrada: {agencia}")



    if not agencia:

        flash("Agencia nao encontrada (id invalido).", "error")

        return redirect(url_for("views.agencias"))



    # Verifica dependencia: conta_convenio vinculada

    conta_vinculada = fetch_one(

        "SELECT 1 FROM conta_convenio WHERE id_agencia = %s LIMIT 1",

        (id_agencia,),

    )

    if conta_vinculada:

        flash(

            "Não é possível excluir a agencia: existem contas de convenio vinculadas.",

            "error",

        )

        return redirect(url_for("views.agencias"))



    # Tenta excluir

    try:

        result = execute("DELETE FROM agencia WHERE id_agencia = %s", (id_agencia,))

        print(f"[DEBUG] Resultado do DELETE agÃªncia: {result}")

    except Exception as e:

        print(f"[ERRO EXCLUIR AGENCIA] {e}")

        flash("Erro ao excluir agencia (restricao no banco de dados).", "error")

        return redirect(url_for("views.agencias"))



    if result and result > 0:

        flash("Excluido com sucesso!", "success")

    else:

        flash("Erro ao excluir agencia.", "error")


    return redirect(url_for("views.agencias"))







# ===========================

# CRUD - CONCEDENTES

# ===========================





@views_bp.route("/concedentes")

@login_required

def concedentes():

    # Paginao

    page = request.args.get("page", 1, type=int)

    per_page = 5

    offset = (page - 1) * per_page

    

    search_term = request.args.get("search", "").strip()

    query = "SELECT * FROM concedente"

    params = []

    

    where_clause = ""

    if search_term:

        where_clause = """

 WHERE (

        sigla ILIKE %s OR

        nome ILIKE %s

 )

        """

        like = f"%{search_term}%"

        params.extend([like, like])

    

    # Contar total

    count_query = f"SELECT COUNT(*) as count FROM concedente{where_clause}"

    count_params = params[:]

    result = fetch_one(count_query, count_params)

    total_items = result['count'] if result else 0

    total_pages = (total_items + per_page - 1) // per_page

    

    query += where_clause

    query += " ORDER BY codigo_secretaria, sigla LIMIT %s OFFSET %s"

    params.extend([per_page, offset])



    concedentes_list = fetch_all(query, params)

    

    start_item = offset + 1 if concedentes_list else 0

    end_item = min(offset + per_page, total_items)

    

    return render_template(

        "concedentes/list.html",

        concedentes=concedentes_list,

        search_term=search_term,

        current_page=page,

        total_pages=total_pages,

        total_items=total_items,

        start_item=start_item,

        end_item=end_item,

    )





@views_bp.route("/concedentes/criar", methods=["GET", "POST"])

@login_required

def criar_concedente():

    form_data = {}

    # Carrega dados do formulario se houver

    if request.method == "POST":

        form_data = request.form.to_dict()

        codigo_secretaria = form_data.get("codigo_secretaria")

        sigla = form_data.get("sigla")

        nome = form_data.get("nome")



        # Validao bsica

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

        flash("Concedente nao encontrado.", "error")

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



    # 1) SELECT na propria tabela

    concedente = fetch_one(

        "SELECT * FROM concedente WHERE id_concedente = %s",

        (id_concedente,),

    )

    print(f"[DEBUG] Concedente encontrado: {concedente}")



    if not concedente:

        flash("Concedente no encontrado.", "error")

        return redirect(url_for("views.concedentes"))



    # 2) Verifica dependencia: remessas vinculadas

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

        flash("Erro ao excluir concedente (restricao no banco de dados).", "error")

        return redirect(url_for("views.concedentes"))



    if result and result > 0:

        flash("Excluido com sucesso!", "success")

    else:

        flash("Erro ao excluir concedente.", "error")



    return redirect(url_for("views.concedentes"))









# ===========================

# CRUD - USUARIOS

# ===========================





@views_bp.route("/usuarios")

@login_required

def usuarios():

    # Paginação

    page = request.args.get("page", 1, type=int)

    per_page = 5

    offset = (page - 1) * per_page

    

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

        filters.append("perfil_enum = %s")

        params.append(perfil_filter)



    if status_filter:

        filters.append("status_enum = %s")

        params.append(status_filter)



    where_clause = ""

    if filters:

        where_clause = " WHERE " + " AND ".join(filters)

    

    # Contar total

    count_query = f"SELECT COUNT(*) as count FROM usuario{where_clause}"

    result = fetch_one(count_query, params)

    total_items = result['count'] if result else 0

    total_pages = (total_items + per_page - 1) // per_page

    

    query += where_clause

    query += " ORDER BY nome LIMIT %s OFFSET %s" #offset serve para pular os primeiros registros

    params.extend([per_page, offset])



    usuarios_list = fetch_all(query, params)

    

    start_item = offset + 1 if usuarios_list else 0

    end_item = min(offset + per_page, total_items)

    

    return render_template(

        "usuarios/list.html",

        usuarios=usuarios_list,

        search_term=search_term,

        perfil_filter=perfil_filter,

        status_filter=status_filter,

        current_page=page,

        total_pages=total_pages,

        total_items=total_items,

        start_item=start_item,

        end_item=end_item,

    )





@views_bp.route("/usuarios/criar", methods=["GET", "POST"])

@login_required

def criar_usuario():

    # Verificar se o usuario logado  administrador

    user_profile = session.get("user_profile", "MONITOR")

    if user_profile != "ADMIN":

        flash("Acesso negado. Somente administradores podem criar usurios.", "error")

        return redirect(url_for("views.usuarios"))

    

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

        status_enum = form_data.get("status_enum", "ATIVO")

        



        if not all([nome, matricula, email, instituicao, login_input, senha]):

            flash("Todos os campos so obrigatrios.", "error")

            return render_template("usuarios/create.html", form_data=form_data)



        senha_hash = generate_password_hash(senha)



        result = execute(

            """

            INSERT INTO usuario (nome, matricula, email, instituicao, login, senha, perfil_enum, status_enum)

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

            """,

            (nome, matricula, email, instituicao, login_input, senha_hash, perfil_enum, status_enum),

        )



        if result and result > 0:

            flash("Usuario criado com sucesso!", "success")

            return redirect(url_for("views.usuarios"))



        flash("Erro ao criar usuario. Verifique se o login, e-mail ou matricula ja existem.", "error")

        return render_template("usuarios/create.html", form_data=form_data)



    return render_template("usuarios/create.html", form_data=form_data)





@views_bp.route("/usuarios/editar/<int:id_usuario>", methods=["GET", "POST"])

@login_required

def editar_usuario(id_usuario):

    usuario = fetch_one("SELECT * FROM usuario WHERE id_usuario = %s", (id_usuario,))

    if not usuario:

        flash("Usuario nao encontrado.", "error")

        return redirect(url_for("views.usuarios"))



    # Verificar se o usuario pode editar: admin pode editar qualquer um, outros podem editar a si mesmos

    user_profile = session.get("user_profile", "MONITOR")

    current_user_id = session.get("user_id")

    

    if user_profile != "ADMIN" and current_user_id != id_usuario:

        flash("Acesso negado, usuário não autorizado.", "error")

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

        status_enum = form_data.get("status_enum", usuario.get("status_enum", "ATIVO"))

        nova_senha = form_data.get("nova_senha")

        

        # Validacao de permissao: Apenas administradores podem alterar perfil, senha e status

        user_profile = session.get("user_profile", "MONITOR")

        if user_profile != "ADMIN":

            # Se nao  admin, manter valores originais do usuario

            perfil_enum = usuario.get("perfil_enum")

            status_enum = usuario.get("status_enum")

            nova_senha = None  # Nao permitir alteracao de senha

        

        



        if not all([nome, matricula, email, instituicao, login_input]):

            flash("Todos os campos obrigatrios devem ser preenchidos.", "error")

            # Preenche usuario exibido com o que o usuario digitou

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

                       perfil_enum = %s,

                       status_enum = %s,

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

                       perfil_enum = %s,

                       status_enum = %s

                 WHERE id_usuario  = %s

                """,

                (nome, matricula, email, instituicao, login_input, perfil_enum, status_enum, id_usuario),

            )



        if result and result > 0:

            flash("Usurio atualizado com sucesso!", "success")

            return redirect(url_for("views.usuarios"))



        flash("Erro ao atualizar usuario.", "error")

        usuario_atualizado = {**usuario, **form_data}

        return render_template("usuarios/edit.html", usuario=usuario_atualizado)



    return render_template("usuarios/edit.html", usuario=usuario)





@views_bp.route("/usuarios/excluir/<int:id_usuario>", methods=["POST"])

@login_required

def excluir_usuario(id_usuario):

    # Verificar se o usurio logado  administrador

    user_profile = session.get("user_profile", "MONITOR")

    if user_profile != "ADMIN":

        flash("Acesso negado. Somente administradores podem excluir usuarios.", "error")

        return redirect(url_for("views.usuarios"))

        

    print(f"[DEBUG] Tentando excluir usurio id_usuario={id_usuario}")



    # 1) SELECT na propria tabela
    usuario = fetch_one("SELECT * FROM usuario WHERE id_usuario = %s", (id_usuario,))

    print(f"[DEBUG] Usuario encontrado: {usuario}")

    if not usuario:

        flash("Usuario nao encontrado.", "error")
        return redirect(url_for("views.usuarios"))



    # 2) Verifica dependncia: remessas vinculadas

    remessa_vinculada = fetch_one(

        "SELECT 1 FROM remessa WHERE id_usuario = %s LIMIT 1",

        (id_usuario,),

    )

    if remessa_vinculada:

        flash(

            "No  possvel excluir o usurio: existem remessas vinculadas a ele.",

            "error",

        )

        return redirect(url_for("views.usuarios"))



    # 3) Tenta excluir

    try:

        result = execute("DELETE FROM usuario WHERE id_usuario = %s", (id_usuario,))

        print(f"[DEBUG] Resultado do DELETE usurio: {result}")

    except Exception as e:

        print(f"[ERRO EXCLUIR USUARIO] {e}")

        flash("Erro ao excluir usuario (restricao no banco de dados).", "error")

        return redirect(url_for("views.usuarios"))



    if result and result > 0:

        flash("Excluido com sucesso!", "success")

    else:

        flash("Erro ao excluir usuario.", "error")

    return redirect(url_for("views.usuarios"))







# ===========================

# CRUD - REMESSAS

# ===========================





@views_bp.route("/remessas")
@login_required
def remessas():
    page = request.args.get("page", 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    search_term = request.args.get("search", "").strip()
    situacao_filter = request.args.get("situacao", "").strip()
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
    
    filters = []
    params = []
    if search_term:
        filters.append("r.nome_proponente ILIKE %s")
        params.append(f"%{search_term}%")
    if situacao_filter:
        filters.append("r.situacao = %s")
        params.append(situacao_filter)
    if situacao_filter:
        filters.append("r.situacao = %s")
        params.append(situacao_filter)
    if situacao_filter:
        filters.append("r.situacao = %s")
        params.append(situacao_filter)
    if date_from:
        filters.append("DATE(r.dt_remessa) = %s")
        params.append(date_from)
    
    where_clause = ""
    if filters:
        where_clause = " WHERE " + " AND ".join(filters)
    
    count_query = f"SELECT COUNT(*) as count FROM remessa r{where_clause}"
    result = fetch_one(count_query, params)
    total_items = result['count'] if result else 0
    total_pages = (total_items + per_page - 1) // per_page
    
    base_query += where_clause
    base_query += " ORDER BY r.nome_proponente LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    
    remessas_list = fetch_all(base_query, params)

    agencias_modal = fetch_all(
        """
        SELECT
            a.*,
            (SELECT nome FROM banco b WHERE b.id_banco = a.id_banco) AS banco_nome
        FROM agencia a
        ORDER BY a.nome_agencia
        """
    )
    
    start_item = offset + 1 if remessas_list else 0
    end_item = min(offset + per_page, total_items)
    
    return render_template(
        "remessas/list.html",
        remessas=remessas_list,
        search_term=search_term,
        date_from=date_from,
        situacao_filter=situacao_filter,
        current_page=page,
        total_pages=total_pages,
        total_items=total_items,
        start_item=start_item,
        end_item=end_item,
        agencias_modal=agencias_modal,
        date=date,
    )


@views_bp.route("/remessas/vincular-conta", methods=["POST"])
@login_required
def vincular_conta_remessa():
    num_conta = request.form.get("num_conta")
    dv_conta = request.form.get("dv_conta")
    dt_abertura = request.form.get("dt_abertura")
    id_remessa = request.form.get("id_remessa")
    id_agencia = request.form.get("id_agencia")

    if not all([num_conta, dv_conta, dt_abertura, id_remessa, id_agencia]):
        flash("Preencha agencia, conta, dgito e data de abertura.", "error")
        return redirect(url_for("views.remessas"))

    # Inserir conta e atualizar situacao da remessa para Conta Aberta
    conta_result = execute(
        """
        INSERT INTO conta_convenio (num_conta, dv_conta, dt_abertura, id_remessa, id_agencia)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (num_conta, dv_conta, dt_abertura, id_remessa, id_agencia),
    )
    if conta_result and conta_result > 0:
        execute(
            "UPDATE remessa SET situacao = 'Conta Aberta' WHERE id_remessa = %s",
            (id_remessa,),
        )
        flash("Conta vinculada e remessa marcada como Conta Aberta.", "success")
    else:
        flash("Erro ao vincular conta  remessa.", "error")

    return redirect(url_for("views.remessas"))






@views_bp.route("/remessas/criar", methods=["GET", "POST"])

@login_required

def criar_remessa():

    form_data = {}



    # Buscar dados para formulrio 

    concedentes = fetch_all("SELECT * FROM concedente ORDER BY nome")

    bancos = fetch_all("SELECT * FROM banco ORDER BY nome")



    if request.method == "POST":

        form_data = request.form.to_dict()



        num_processo = form_data.get("num_processo")

        nome_proponente = form_data.get("nome_proponente")

        cpf_cnpj = form_data.get("cpf_cnpj")

        num_convenio = form_data.get("num_convenio")

        situacao = form_data.get("situacao", "Em Preparacao")

        id_concedente = form_data.get("id_concedente")

        id_banco = form_data.get("id_banco")



        if not all([num_processo, nome_proponente, cpf_cnpj, num_convenio, id_concedente]):

            flash("Todos os campos obrigatrios devem ser preenchidos!", "error")

            return render_template(

                "remessas/create.html",

                concedentes=concedentes,

                bancos=bancos,

                form_data=form_data,

            )



        # Proximo numero de remessa

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

    # Buscar dados para carregar a edicao   

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

        flash("Remessa no encontrada.", "error")

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

        flash("Remessa no encontrada.", "error")

        return redirect(url_for("views.remessas"))



    # Verifica se ha conta_convenio vinculada

    conta_vinculada = fetch_one(

        "SELECT 1 FROM conta_convenio WHERE id_remessa = %s LIMIT 1",

        (id_remessa,),

    )

    if conta_vinculada:

        flash(

            "Nao e possivel excluir a remessa: existem contas de convenio vinculadas.",

            "error",

        )

        return redirect(url_for("views.remessas"))



    try:

        result = execute("DELETE FROM remessa WHERE id_remessa = %s", (id_remessa,))

        print(f"[DEBUG] Resultado do DELETE remessa: {result}")

    except Exception as e:

        print(f"[ERRO EXCLUIR REMESSA] {e}")

        flash("Erro ao excluir remessa (restricao no banco de dados).", "error")

        return redirect(url_for("views.remessas"))



    if result and result > 0:

        flash("Excluido com sucesso!", "success")

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

            (SELECT b.nome FROM banco     b WHERE b.id_banco      = r.id_banco)      AS banco_nome,
            (
                SELECT MAX(cc.dt_abertura)
                FROM conta_convenio cc
                WHERE cc.id_remessa = r.id_remessa
            ) AS dt_abertura_conta

        FROM remessa r

        WHERE r.id_remessa = %s

    """

    remessa = fetch_one(query, (id_remessa,))



    if not remessa:

        flash("Remessa nao encontrada.", "error")

        return redirect(url_for("views.remessas"))



    # Apenas renderiza a pagina de visualizacao

    return render_template("remessas/view.html", remessa=remessa)







# ===========================

# CRUD - CONTAS CONVENIO

# ===========================





@views_bp.route("/contas-convenio", methods=["GET", "POST"])

@login_required

def contas_convenio():
    page = request.args.get("page", 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    search_term = request.args.get("search", "").strip()
    situacao_filter = request.args.get("situacao", "").strip()

    base_query = """
        SELECT
            cc.*,
            r.num_processo,
            r.nome_proponente,
            r.num_remessa,
            r.cpf_cnpj,
            r.situacao,
            (SELECT a.nome_agencia FROM agencia a WHERE a.id_agencia = cc.id_agencia) AS nome_agencia,
            (
                SELECT b.nome
                FROM banco b
                WHERE b.id_banco = (
                    SELECT ag.id_banco FROM agencia ag WHERE ag.id_agencia = cc.id_agencia
                )
            ) AS banco_nome
        FROM conta_convenio cc
        JOIN remessa r ON r.id_remessa = cc.id_remessa
    """
    params = []
    filters = []

    if search_term:
        filters.append("r.nome_proponente ILIKE %s")
        params.append(f"%{search_term}%")
    if situacao_filter:
        filters.append("r.situacao = %s")
        params.append(situacao_filter)

    where_clause = ""
    if filters:
        where_clause = " WHERE " + " AND ".join(filters)

    count_query = f"SELECT COUNT(*) as count FROM conta_convenio cc JOIN remessa r ON r.id_remessa = cc.id_remessa{where_clause}"
    total_items_row = fetch_one(count_query, params)
    total_items = total_items_row["count"] if total_items_row else 0
    total_pages = (total_items + per_page - 1) // per_page

    base_query += """
        {where}
        ORDER BY
            r.nome_proponente,
            (SELECT a.nome_agencia FROM agencia a WHERE a.id_agencia = cc.id_agencia),
            cc.dt_abertura DESC
        LIMIT %s OFFSET %s
    """.format(where=where_clause)
    params.extend([per_page, offset])

    contas_list = fetch_all(base_query, params)

    start_item = offset + 1 if contas_list else 0
    end_item = min(offset + per_page, total_items)

    form_defaults = {"id_remessa": None, "dt_abertura": date.today().isoformat()}

    return render_template(
        "contas-convenio/list.html",
        contas=contas_list,
        search_term=search_term,
        situacao_filter=situacao_filter,
        current_page=page,
        total_pages=total_pages,
        total_items=total_items,
        start_item=start_item,
        end_item=end_item,
        remessas_options=[],
        selected_remessa=None,
        agencias=[],
        form_defaults=form_defaults,
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

            flash("Todos os campos sao obrigatorios.", "error")

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

            flash("Conta de convenio criada com sucesso!", "success")

            return redirect(url_for("views.contas_convenio", id_remessa=id_remessa))



        flash("Erro ao criar conta de convenio.", "error")



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
               (SELECT nome_proponente FROM remessa r WHERE r.id_remessa = cc.id_remessa) AS nome_proponente,
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
        flash("Conta de convenio nao encontrada.", "error")
        return redirect(url_for("views.contas_convenio"))

    if request.method == "POST":
        num_conta = request.form.get("num_conta")
        dv_conta = request.form.get("dv_conta")
        dt_abertura = request.form.get("dt_abertura")

        result = execute(
            """
            UPDATE conta_convenio
               SET num_conta   = %s,
                   dv_conta    = %s,
                   dt_abertura = %s
             WHERE id_conta_convenio = %s
            """,
            (num_conta, dv_conta, dt_abertura, id_conta_convenio),
        )

        if result and result > 0:
            flash("Conta de convenio atualizada com sucesso!", "success")
            return redirect(url_for("views.contas_convenio"))

        flash("Erro ao atualizar conta de convenio.", "error")

    return render_template(
        "contas-convenio/edit.html",
        conta=conta,
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

        flash("Conta de convenio nao encontrada.", "error")

        return redirect(url_for("views.contas_convenio"))



    try:

        result = execute(

            "DELETE FROM conta_convenio WHERE id_conta_convenio = %s",

            (id_conta_convenio,),

        )

        print(f"[DEBUG] Resultado do DELETE conta_convenio: {result}")

    except Exception as e:

        print(f"[ERRO EXCLUIR CONTA_CONVENIO] {e}")

        flash("Erro ao excluir conta de convenio (restricao no banco de dados).", "error")

        return redirect(url_for("views.contas_convenio"))



    if result and result > 0:
        flash("Conta de convenio excluida com sucesso!", "success")

    else:

        flash("Erro ao excluir conta de convenio.", "error")


    return redirect(url_for("views.contas_convenio"))






