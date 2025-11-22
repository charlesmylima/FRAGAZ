from models.rotina_notificacao import RotinaNotificacao

class RotinaService:
    @staticmethod
    def cadastrar(nome, descricao, ativo=1):
        RotinaNotificacao.create(nome, descricao, ativo)

    @staticmethod
    def atualizar(id, nome=None, descricao=None, ativo=None):
        RotinaNotificacao.update(id, nome, descricao, ativo)

    @staticmethod
    def remover(id):
        RotinaNotificacao.delete(id)

    @staticmethod
    def listar():
        return RotinaNotificacao.get_all()
