from src.database import execute

class LoginUsuario:
    @staticmethod
    def create_table():
        execute('''
        CREATE TABLE IF NOT EXISTS logins_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            data_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
        ''', commit=True)

    @staticmethod
    def log_login(usuario_id):
        execute('INSERT INTO logins_usuario (usuario_id) VALUES (?)', (usuario_id,), commit=True)

    @staticmethod
    def get_logins_by_user(usuario_id):
        cur = execute('SELECT * FROM logins_usuario WHERE usuario_id = ?', (usuario_id,))
        return cur.fetchall()
