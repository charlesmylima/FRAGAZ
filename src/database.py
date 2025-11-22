import sqlite3
from threading import Lock

_DB_PATH = "fragaz.db"
_connection = None
_lock = Lock()

def get_db():
    global _connection
    with _lock:
        if _connection is None:
            _connection = sqlite3.connect(_DB_PATH, check_same_thread=False)
            _connection.row_factory = sqlite3.Row
        return _connection

def execute(query, params=(), commit=False):
    conn = get_db()
    cur = conn.execute(query, params)
    if commit:
        conn.commit()
    return cur

def executemany(query, seq_of_params, commit=False):
    conn = get_db()
    cur = conn.executemany(query, seq_of_params)
    if commit:
        conn.commit()
    return cur

def create_triggers_and_views():
    execute('''
    CREATE TABLE IF NOT EXISTS logs_acao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        acao TEXT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''', commit=True)

    execute('''
    CREATE TRIGGER IF NOT EXISTS log_usuario_insert
    AFTER INSERT ON usuarios
    BEGIN
        INSERT INTO logs_acao (usuario_id, acao) VALUES (NEW.id, 'INSERT');
    END;
    ''', commit=True)

    execute('''
    CREATE TRIGGER IF NOT EXISTS log_usuario_update
    AFTER UPDATE ON usuarios
    BEGIN
        INSERT INTO logs_acao (usuario_id, acao) VALUES (NEW.id, 'UPDATE');
    END;
    ''', commit=True)

    execute('''
    CREATE VIEW IF NOT EXISTS logins_por_dia AS
    SELECT date(data_login) as dia, COUNT(*) as total
    FROM logins_usuario
    GROUP BY dia
    ''', commit=True)

    execute('''
    CREATE VIEW IF NOT EXISTS usuarios_por_mes AS
    SELECT strftime('%Y-%m', criado_em) as mes, COUNT(*) as total
    FROM usuarios
    GROUP BY mes
    ''', commit=True)
