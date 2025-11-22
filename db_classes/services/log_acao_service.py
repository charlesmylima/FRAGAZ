from db_classes.models.log_acao import LogAcao

class LogAcaoService:
    @staticmethod
    def listar_todos():
        return LogAcao.get_all()

    @staticmethod
    def listar_por_usuario(usuario_id):
        return LogAcao.get_by_usuario(usuario_id)
