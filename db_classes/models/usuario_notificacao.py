from db_classes.database import execute

class UsuarioNotificacao:
    @staticmethod
    def create_table():
        execute('''
        CREATE TABLE IF NOT EXISTS usuario_notificacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            rotina_id INTEGER,
            ativo INTEGER DEFAULT 1,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY(rotina_id) REFERENCES rotinas_notificacao(id)
        )
        ''', commit=True)

    @staticmethod
    def create(usuario_id, rotina_id, ativo=1):
        execute('INSERT INTO usuario_notificacao (usuario_id, rotina_id, ativo) VALUES (?, ?, ?)', (usuario_id, rotina_id, ativo), commit=True)

    @staticmethod
    def update(id, ativo=None):
        fields, params = [], []
        if ativo is not None:
            fields.append("ativo = ?")
            params.append(ativo)
        params.append(id)
        execute(f'UPDATE usuario_notificacao SET {", ".join(fields)} WHERE id = ?', params, commit=True)

    @staticmethod
    def delete(id):
        execute('DELETE FROM usuario_notificacao WHERE id = ?', (id,), commit=True)

    @staticmethod
    def get_by_usuario(usuario_id):
        cur = execute('SELECT * FROM usuario_notificacao WHERE usuario_id = ?', (usuario_id,))
        return cur.fetchall()
