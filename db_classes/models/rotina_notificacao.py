from db_classes.database import execute

class RotinaNotificacao:
    @staticmethod
    def create_table():
        execute('''
        CREATE TABLE IF NOT EXISTS rotinas_notificacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            ativo INTEGER DEFAULT 1
        )
        ''', commit=True)

    @staticmethod
    def create(nome, descricao, ativo=1):
        execute('INSERT INTO rotinas_notificacao (nome, descricao, ativo) VALUES (?, ?, ?)', (nome, descricao, ativo), commit=True)

    @staticmethod
    def update(id, nome=None, descricao=None, ativo=None):
        fields, params = [], []
        if nome:
            fields.append("nome = ?")
            params.append(nome)
        if descricao:
            fields.append("descricao = ?")
            params.append(descricao)
        if ativo is not None:
            fields.append("ativo = ?")
            params.append(ativo)
        params.append(id)
        execute(f'UPDATE rotinas_notificacao SET {", ".join(fields)} WHERE id = ?', params, commit=True)

    @staticmethod
    def delete(id):
        execute('DELETE FROM rotinas_notificacao WHERE id = ?', (id,), commit=True)

    @staticmethod
    def get_all():
        cur = execute('SELECT * FROM rotinas_notificacao')
        return cur.fetchall()
