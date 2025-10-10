# urls.py

from flask import Flask

# Importe seus blueprints/controllers aqui
from controllers.user_controller import user_bp
from controllers.banco_controller import banco_bp
from controllers.agencia_controller import agencia_bp
from controllers.remessa_controller import remessa_bp
from controllers.concedente_controller import concedente_bp
from controllers.conta_convenio_controller import conta_convenio_bp
from controllers.auth_controller import auth_bp
from controllers.main_controller import main_bp

def register_routes(app: Flask):
    # Cada blueprint registra um módulo de entidade
    app.register_blueprint(main_bp)             # Rotas principais (home, dashboard)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/usuarios')
    app.register_blueprint(banco_bp, url_prefix='/bancos')
    app.register_blueprint(agencia_bp, url_prefix='/agencias')
    app.register_blueprint(remessa_bp, url_prefix='/remessas')
    app.register_blueprint(concedente_bp, url_prefix='/concedentes')
    app.register_blueprint(conta_convenio_bp, url_prefix='/contas-convenio')
