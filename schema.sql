-- Schema para gestão de arquivos/versões usando PostgreSQL
-- Parte 1: estrutura inicial

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id          SERIAL PRIMARY KEY,
    nome        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    criado_em   TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Tabela principal de arquivos
CREATE TABLE IF NOT EXISTS arquivos (
    id             SERIAL PRIMARY KEY,
    nome           TEXT NOT NULL,
    caminho        TEXT NOT NULL,
    proprietario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    is_public      BOOLEAN DEFAULT FALSE,
    criado_em      TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Índices úteis
CREATE INDEX IF NOT EXISTS idx_arquivos_proprietario ON arquivos(proprietario_id);

-- Fim da primeira etapa
