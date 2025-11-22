from db_classes.database import execute
import bcrypt

class Usuario:
    @staticmethod
    def create_table():
        execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''', commit=True)

    @staticmethod
    def create(nome, email, senha):
        senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
        execute('INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)', (nome, email, senha_hash), commit=True)

    @staticmethod
    def get_by_email(email):
        cur = execute('SELECT * FROM usuarios WHERE email = ?', (email,))
        return cur.fetchone()

    @staticmethod
    def verify_password(email, senha):
        user = Usuario.get_by_email(email)
        if user:
            return bcrypt.checkpw(senha.encode(), user['senha_hash'].encode())
        return False

    @staticmethod
    def update(id, nome=None, email=None, senha=None):
        fields, params = [], []
        if nome:
            fields.append("nome = ?")
            params.append(nome)
        if email:
            fields.append("email = ?")
            params.append(email)
        if senha:
            fields.append("senha_hash = ?")
            params.append(bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode())
        params.append(id)
        execute(f'UPDATE usuarios SET {", ".join(fields)} WHERE id = ?', params, commit=True)

    @staticmethod
    def delete(id):
        execute('DELETE FROM usuarios WHERE id = ?', (id,), commit=True)
