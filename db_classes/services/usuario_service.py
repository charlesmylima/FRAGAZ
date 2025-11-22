from db_classes.models.usuario import Usuario

class UsuarioService:
    @staticmethod
    def cadastrar(nome, email, senha):
        Usuario.create(nome, email, senha)

    @staticmethod
    def autenticar(email, senha):
        return Usuario.verify_password(email, senha)

    @staticmethod
    def atualizar(id, nome=None, email=None, senha=None):
        Usuario.update(id, nome, email, senha)

    @staticmethod
    def remover(id):
        Usuario.delete(id)

    @staticmethod
    def buscar_por_email(email):
        return Usuario.get_by_email(email)
