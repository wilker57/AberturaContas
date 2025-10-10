from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()

class PerfilEnum(enum.Enum):
    ADMIN = 'Administrador'
    OPERADOR = 'Operador'
    MONITOR = 'Monitor'

class StatusEnum(enum.Enum):
    ATIVO = 'Ativo'
    INATIVO = 'Inativo'

class SituacaoEnum(enum.Enum):
    EM_PREPARACAO = 'Em preparação'
    ENVIADO = 'Enviado'
    AGUARDANDO_RETORNO = 'Aguardando retorno'
    APROVADO = 'Aprovado'
    CONTA_ABERTA = 'Conta aberta'
    ERRO = 'Erro'

class Concedente(db.Model):
    __tablename__ = 'concedente'
    id_concedente = db.Column(db.Integer, primary_key=True)
    codigo_secretaria = db.Column(db.String(20), unique=True, nullable=False)
    sigla = db.Column(db.String(20), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    remessas = db.relationship('Remessa', backref='concedente', lazy=True)

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    instituicao = db.Column(db.String(100))
    perfil_enum = db.Column(db.Enum(PerfilEnum), nullable=False, default=PerfilEnum.MONITOR)
    login = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    status_enum = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.ATIVO)
    remessas = db.relationship('Remessa', backref='usuario', lazy=True)

class Banco(db.Model):
    __tablename__ = 'banco'
    id_banco = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    agencias = db.relationship('Agencia', backref='banco', lazy=True)
    remessas = db.relationship('Remessa', backref='banco', lazy=True)

class Agencia(db.Model):
    __tablename__ = 'agencia'
    id_agencia = db.Column(db.Integer, primary_key=True)
    nome_agencia = db.Column(db.String(100), nullable=False)
    num_agencia = db.Column(db.Integer, nullable=False)
    dv_agencia = db.Column(db.String(1), nullable=False)
    logadouro = db.Column(db.String(300), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    uf = db.Column(db.String(2))
    id_banco = db.Column(db.Integer, db.ForeignKey('banco.id_banco'), nullable=False)
    contas_convenio = db.relationship('ContaConvenio', backref='agencia', lazy=True)

class Remessa(db.Model):
    __tablename__ = 'remessa'
    id_remessa = db.Column(db.Integer, primary_key=True)
    num_processo = db.Column(db.String(100), unique=True, nullable=False)
    nome_proponente = db.Column(db.String(100), nullable=False)
    cpf_cnpj = db.Column(db.String(18), nullable=False)
    num_convenio = db.Column(db.String(100), nullable=False)
    situacao_enum = db.Column(db.Enum(SituacaoEnum), nullable=False, default=SituacaoEnum.EM_PREPARACAO)
    dt_remessa = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    num_remessa = db.Column(db.Integer, nullable=False)
    id_concedente = db.Column(db.Integer, db.ForeignKey('concedente.id_concedente'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_banco = db.Column(db.Integer, db.ForeignKey('banco.id_banco'))
    contas_convenio = db.relationship('ContaConvenio', backref='remessa', lazy=True)

class ContaConvenio(db.Model):
    __tablename__ = 'conta_convenio'
    id_conta_convenio = db.Column(db.Integer, primary_key=True)
    num_conta = db.Column(db.String(20), nullable=False)
    dv_conta = db.Column(db.String(1), nullable=False)
    dt_abertura = db.Column(db.Date, nullable=False)
    id_remessa = db.Column(db.Integer, db.ForeignKey('remessa.id_remessa'), nullable=False)
    id_agencia = db.Column(db.Integer, db.ForeignKey('agencia.id_agencia'), nullable=False)
