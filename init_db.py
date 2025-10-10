# init_db.py - Script para inicializar banco de dados

from app import create_app
from produto.models import db
from flask_migrate import Migrate, init, migrate, upgrade
import os

def init_database():
    """Inicializa o banco de dados e migrations"""
    
    app = create_app()
    
    # Configura Flask-Migrate
    migrate_obj = Migrate(app, db)
    
    with app.app_context():
        print("🔄 Inicializando sistema de migrations...")
        
        # Verifica se já existe pasta migrations
        if not os.path.exists('migrations'):
            print("📁 Criando pasta de migrations...")
            try:
                init()
                print("✅ Sistema de migrations inicializado!")
            except Exception as e:
                print(f"❌ Erro ao inicializar migrations: {e}")
                return False
        else:
            print("📁 Pasta migrations já existe!")
        
        # Cria primeira migration
        print("🔄 Criando migration inicial...")
        try:
            migrate(message='Initial migration - Sistema Abertura Contas')
            print("✅ Migration inicial criada!")
        except Exception as e:
            print(f"⚠️ Migration já pode existir ou erro: {e}")
        
        # Aplica migrations
        print("🔄 Aplicando migrations ao banco de dados...")
        try:
            upgrade()
            print("✅ Migrations aplicadas com sucesso!")
            print("🎉 Banco de dados configurado e pronto para uso!")
            return True
        except Exception as e:
            print(f"❌ Erro ao aplicar migrations: {e}")
            # Fallback: criar tabelas diretamente
            print("🔄 Tentando criar tabelas diretamente...")
            try:
                db.create_all()
                print("✅ Tabelas criadas diretamente!")
                return True
            except Exception as e2:
                print(f"❌ Erro ao criar tabelas: {e2}")
                return False

if __name__ == "__main__":
    print("🚀 INICIALIZANDO BANCO DE DADOS")
    print("=" * 50)
    
    success = init_database()
    
    if success:
        print("\n🎉 Inicialização concluída com sucesso!")
        print("Agora você pode executar: python manage.py")
    else:
        print("\n💥 Falha na inicialização!")
        print("Verifique as configurações do banco de dados.")