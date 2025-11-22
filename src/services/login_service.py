from models.login import LoginUsuario

class LoginService:
    @staticmethod
    def registrar_login(usuario_id):
        LoginUsuario.log_login(usuario_id)

    @staticmethod
    def logins_do_usuario(usuario_id):
        return LoginUsuario.get_logins_by_user(usuario_id)
