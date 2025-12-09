CREATE TYPE perfil_enum AS ENUM ('Administrador', 'Operador', 'Monitor');
CREATE TYPE status_enum AS ENUM ('Ativo', 'Inativo');
CREATE TYPE situacao_enum AS ENUM ('Em preparação', 'Enviado', 'Aguardando retorno', 'Conta aberta', 'Erro');

CREATE TABLE concedente (
    id_concedente SERIAL PRIMARY KEY,
    codigo_secretaria VARCHAR(20) NOT NULL UNIQUE,
    sigla VARCHAR(20) NOT NULL,
    nome VARCHAR(100) NOT NULL
);

CREATE TABLE usuario (
    id_usuario SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    matricula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    instituicao VARCHAR(100),
    perfil_enum perfil_enum NOT NULL DEFAULT 'Monitor',
    login VARCHAR(50) UNIQUE NOT NULL,
    senha VARCHAR(100) NOT NULL,
    status_enum status_enum NOT NULL DEFAULT 'Ativo'
);

CREATE TABLE banco (
    id_banco SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL
);

CREATE TABLE agencia (
    id_agencia SERIAL PRIMARY KEY,
    nome_agencia VARCHAR(100) NOT NULL,
    num_agencia INTEGER NOT NULL,
    dv_agencia CHAR(1) NOT NULL,
    logadouro VARCHAR(300) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    uf CHAR(2),
    id_banco INTEGER NOT NULL REFERENCES banco(id_banco)
);

CREATE TABLE remessa (
    id_remessa SERIAL PRIMARY KEY,
    num_processo VARCHAR(100) UNIQUE NOT NULL,
    nome_proponente VARCHAR(100) NOT NULL,
    cpf_cnpj VARCHAR(18) NOT NULL,
    num_convenio VARCHAR(100) NOT NULL,
    situacao_enum situacao_enum NOT NULL DEFAULT 'Em preparação',
    dt_remessa DATE DEFAULT CURRENT_DATE NOT NULL,
    num_remessa INTEGER NOT NULL,
    id_concedente INTEGER NOT NULL REFERENCES concedente(id_concedente),
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario),
    id_banco INTEGER REFERENCES banco(id_banco)
);

CREATE TABLE conta_convenio (
    id_conta_convenio SERIAL PRIMARY KEY,
    num_conta VARCHAR(20) NOT NULL,
    dv_conta CHAR(1) NOT NULL,
    dt_abertura DATE NOT NULL,
    id_remessa INTEGER NOT NULL REFERENCES remessa(id_remessa),
    id_agencia INTEGER NOT NULL REFERENCES agencia(id_agencia)
);
