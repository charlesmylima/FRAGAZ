from db_classes.models.usuario_notificacao import UsuarioNotificacao

class NotificacaoService:
    @staticmethod
    def vincular_usuario_rotina(usuario_id, rotina_id, ativo=1):
        UsuarioNotificacao.create(usuario_id, rotina_id, ativo)

    @staticmethod
    def atualizar_vinculo(id, ativo=None):
        UsuarioNotificacao.update(id, ativo)

    @staticmethod
    def remover_vinculo(id):
        UsuarioNotificacao.delete(id)

    @staticmethod
    def listar_por_usuario(usuario_id):
        return UsuarioNotificacao.get_by_usuario(usuario_id)
