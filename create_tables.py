# create_tables.py - Script simples para criar tabelas no banco

import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.getcwd())

try:
    from app import create_app
    from produto.models import db
    
    print("🚀 CRIANDO TABELAS NO BANCO DE DADOS")
    print("=" * 50)
    
    # Cria aplicação
    app = create_app()
    
    with app.app_context():
        print("🔄 Conectando ao banco de dados...")
        
        # Testa conexão primeiro
        try:
            from config import get_conn
            conn = get_conn()
            if conn:
                print("✅ Conexão com banco confirmada!")
                conn.close()
            else:
                print("❌ Falha na conexão com banco!")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Erro ao testar conexão: {e}")
            sys.exit(1)
        
        # Cria tabelas
        print("🔄 Criando estrutura das tabelas...")
        try:
            # Lista as tabelas que serão criadas
            print("📋 Tabelas a serem criadas:")
            for table_name in db.metadata.tables.keys():
                print(f"   - {table_name}")
            
            # Cria todas as tabelas
            db.create_all()
            print("✅ Todas as tabelas foram criadas com sucesso!")
            
            # Verifica se as tabelas foram criadas
            print("\n🔍 Verificando tabelas criadas...")
            inspector = db.inspect(db.engine)
            created_tables = inspector.get_table_names()
            
            if created_tables:
                print("✅ Tabelas encontradas no banco:")
                for table in created_tables:
                    print(f"   - {table}")
            else:
                print("⚠️ Nenhuma tabela encontrada no banco")
            
            print("\n🎉 Processo concluído com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            sys.exit(1)

except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erro geral: {e}")
    sys.exit(1)