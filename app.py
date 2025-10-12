# app.py - Aplicação Flask Principal

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import get_conn
import os

def create_app():
    """Factory function para criar a aplicação Flask"""
    
    app = Flask(__name__)
    
    # Configurações da aplicação
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:wil874408@localhost:5432/abertura_contas'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True  # Para debug - remover em produção
    
    # Inicializa extensões
    from produto.models import db
    db.init_app(app)
    
    # Inicializa Flask-Migrate (se disponível)
    try:
        from flask_migrate import Migrate
        migrate = Migrate(app, db)
        print(" Flask-Migrate configurado!")
    except ImportError:
        print(" Flask-Migrate não disponível - usando db.create_all()")
    
    # Registra blueprints/rotas
    try:
        from produto.views import views_bp
        app.register_blueprint(views_bp)
        print(" Views registradas com sucesso!")
    except ImportError as e:
        print(f" Erro ao importar views: {e}")
        # Fallback: criar rotas básicas se views não funcionar
        @app.route('/')
        def index():
            return "Sistema de Abertura de Contas - Flask App funcionando!"
        
        @app.route('/health')
        def health():
            try:
                # Testa conexão com banco
                conn = get_conn()
                if conn:
                    conn.close()
                    return {"status": "ok", "database": "connected"}
                else:
                    return {"status": "error", "database": "disconnected"}, 500
            except Exception as e:
                return {"status": "error", "database": f"error: {str(e)}"}, 500
    
    # Context processor para templates
    @app.context_processor
    def inject_user():
        return dict(user=None)  # Implementar autenticação depois
    
    return app

if __name__ == "__main__":
    app = create_app()
    
    # Criar tabelas se não existirem
    with app.app_context():
        from produto.models import db
        print("🔄 Criando tabelas no banco de dados...")
        try:
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)