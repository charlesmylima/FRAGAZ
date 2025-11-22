from models.usuario import Usuario
from models.login import LoginUsuario
from models.rotina_notificacao import RotinaNotificacao
from models.usuario_notificacao import UsuarioNotificacao
from models.log_acao import LogAcao
from database import create_triggers_and_views

# Setup inicial: cria tabelas e triggers/views
Usuario.create_table()
LoginUsuario.create_table()
RotinaNotificacao.create_table()
UsuarioNotificacao.create_table()
create_triggers_and_views()

# Exemplo de uso
if __name__ == "__main__":
    # Cria usuário
    Usuario.create('João', 'joao@email.com', 'senha123')
    user = Usuario.get_by_email('joao@email.com')
    print('Usuário:', dict(user))
    # Loga login
    LoginUsuario.log_login(user['id'])
    # Cria rotina de notificação
    RotinaNotificacao.create('Alerta de Teste', 'Notifica diariamente')
    rotina = RotinaNotificacao.get_all()[0]
    # Vincula usuário à rotina
    UsuarioNotificacao.create(user['id'], rotina['id'])
    # Consulta logs
    print('Logs:', [dict(l) for l in LogAcao.get_by_usuario(user['id'])])
    # Consulta view de usuários por mês
    from database import execute
    print('Usuários por mês:', [dict(r) for r in execute('SELECT * FROM usuarios_por_mes')])
