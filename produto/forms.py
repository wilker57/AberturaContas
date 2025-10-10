from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from datetime import date

class LoginForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired(), Length(min=3, max=50)])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(min=2, max=100)])
    matricula = StringField('Matrícula', validators=[DataRequired(), Length(min=1, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=200)])
    instituicao = StringField('Instituição', validators=[Length(max=100)])
    perfil = SelectField('Perfil', choices=[
        ('admin', 'Administrador'),
        ('operador', 'Operador'),
        ('monitor', 'Monitor')
    ], validators=[DataRequired()])
    login = StringField('Login', validators=[DataRequired(), Length(min=3, max=50)])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[
        DataRequired(), 
        EqualTo('senha', message='As senhas devem ser iguais')
    ])
    status = SelectField('Status', choices=[
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo')
    ], validators=[DataRequired()])
    submit = SubmitField('Cadastrar')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Recuperar Senha')

class RemessaForm(FlaskForm):
    num_processo = StringField('Número do Processo', validators=[DataRequired(), Length(min=1, max=100)])
    nome_proponente = StringField('Nome do Proponente', validators=[DataRequired(), Length(min=2, max=100)])
    cpf_cnpj = StringField('CPF/CNPJ', validators=[DataRequired(), Length(min=11, max=18)])
    num_convenio = StringField('Número do Convênio', validators=[DataRequired(), Length(min=1, max=100)])
    situacao = SelectField('Situação', choices=[
        ('em preparação', 'Em Preparação'),
        ('enviado', 'Enviado'),
        ('aguardando retorno', 'Aguardando Retorno'),
        ('aprovado', 'Aprovado'),
        ('conta aberta', 'Conta Aberta'),
        ('erro', 'Erro')
    ], validators=[DataRequired()])
    dt_remessa = DateField('Data da Remessa', default=date.today, validators=[DataRequired()])
    num_remessa = IntegerField('Número da Remessa', validators=[DataRequired()])
    id_concedente = SelectField('Concedente', coerce=int, validators=[DataRequired()])
    id_banco = SelectField('Banco', coerce=int)
    submit = SubmitField('Salvar')

class ConcedenteForm(FlaskForm):
    codigo_concedente = StringField('Código do Concedente', validators=[DataRequired(), Length(min=1, max=10)])
    sigla = StringField('Sigla', validators=[DataRequired(), Length(min=1, max=10)])
    nome = StringField('Nome do Concedente', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Salvar')

class BancoForm(FlaskForm):
    nome = StringField('Nome do Banco', validators=[DataRequired(), Length(min=2, max=100)])
    codigo = StringField('Código do Banco', validators=[DataRequired(), Length(min=1, max=10)])
    submit = SubmitField('Salvar')

class AgenciaForm(FlaskForm):
    nome_agencia = StringField('Nome da Agência', validators=[DataRequired(), Length(min=2, max=100)])
    num_agencia = StringField('Número da Agência', validators=[DataRequired(), Length(min=1, max=10)])
    dv_agencia = StringField('DV Agência', validators=[DataRequired(), Length(min=1, max=1)])
    logradouro = StringField('Logradouro', validators=[Length(max=200)])
    cidade = StringField('Cidade', validators=[Length(max=100)])
    uf = StringField('UF', validators=[Length(min=2, max=2)])
    id_banco = SelectField('Banco', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Salvar')        

class ContaConvenioForm(FlaskForm):
    num_conta = StringField('Número da Conta', validators=[DataRequired(), Length(min=1, max=20)])
    dv_conta = StringField('DV', validators=[DataRequired(), Length(min=1, max=1)])
    dt_abertura = DateField('Data de Abertura', validators=[DataRequired()])
    id_remessa = SelectField('Remessa', coerce=int, validators=[DataRequired()])
    id_agencia = SelectField('Agência', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Salvar')
