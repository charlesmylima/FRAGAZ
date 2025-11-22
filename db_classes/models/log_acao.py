from db_classes.database import execute

class LogAcao:
    @staticmethod
    def get_all():
        cur = execute('SELECT * FROM logs_acao')
        return cur.fetchall()

    @staticmethod
    def get_by_usuario(usuario_id):
        cur = execute('SELECT * FROM logs_acao WHERE usuario_id = ?', (usuario_id,))
        return cur.fetchall()
