-- Schema para gestão de arquivos/versões usando PostgreSQL
-- Parte 1: estrutura inicial

-- Tabela de usuários
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo INTEGER DEFAULT 1
);

CREATE TABLE logins_usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    ip TEXT,
    user_agent TEXT,
    data_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE rotinas_notificacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT
);

CREATE TABLE usuario_notificacao (
    usuario_id INTEGER NOT NULL,
    rotina_id INTEGER NOT NULL,
    PRIMARY KEY (usuario_id, rotina_id),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY(rotina_id) REFERENCES rotinas_notificacao(id)
);

CREATE TABLE logs_acao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    acao TEXT NOT NULL,
    data_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER log_update_usuario
AFTER UPDATE ON usuarios
BEGIN
    INSERT INTO logs_acao(usuario_id, acao)
    VALUES (NEW.id, 'Atualização no cadastro de usuário');
END;

CREATE TRIGGER log_insert_usuario
AFTER INSERT ON usuarios
BEGIN
    INSERT INTO logs_acao(usuario_id, acao)
    VALUES (NEW.id, 'Usuário criado');
END;

CREATE VIEW vw_usuarios_por_mes AS
SELECT 
    strftime('%Y-%m', data_criacao) AS mes,
    COUNT(*) AS total
FROM usuarios
GROUP BY mes;

CREATE VIEW vw_logins_por_dia AS
SELECT 
    date(data_login) AS dia,
    COUNT(*) AS total
FROM logins_usuario
GROUP BY dia;
