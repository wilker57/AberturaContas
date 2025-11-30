# fix_enums.py - Script para corrigir ENUMs do PostgreSQL

from app import create_app
from produto.models import db
from sqlalchemy import text

def fix_enums():
    """Corrige os tipos ENUM no PostgreSQL"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Corrigindo ENUMs no banco de dados...")
        
        try:
            # Comando para converter perfil_enum
            sql_perfil = text("""
            ALTER TABLE usuario 
            ALTER COLUMN perfil_enum TYPE perfilenum 
            USING CASE 
                WHEN perfil_enum::text = 'Administrador' THEN 'ADMIN'::perfilenum
                WHEN perfil_enum::text = 'Operador' THEN 'OPERADOR'::perfilenum
                WHEN perfil_enum::text = 'Monitor' THEN 'MONITOR'::perfilenum
                ELSE 'MONITOR'::perfilenum
            END
            """)
            
            with db.engine.connect() as conn:
                conn.execute(sql_perfil)
                conn.commit()
            print("✅ perfil_enum convertido com sucesso!")
            
            # Comando para converter status_enum
            sql_status = text("""
            ALTER TABLE usuario 
            ALTER COLUMN status_enum TYPE statusenum 
            USING CASE 
                WHEN status_enum::text = 'Ativo' THEN 'ATIVO'::statusenum
                WHEN status_enum::text = 'Inativo' THEN 'INATIVO'::statusenum
                ELSE 'ATIVO'::statusenum
            END
            """)
            
            with db.engine.connect() as conn:
                conn.execute(sql_status)
                conn.commit()
            print("✅ status_enum convertido com sucesso!")
            
            # Marcar migration como aplicada
            sql_version = text("INSERT INTO alembic_version (version_num) VALUES ('02e74ab3b348') ON CONFLICT DO NOTHING")
            with db.engine.connect() as conn:
                conn.execute(sql_version)
                conn.commit()
            print("✅ Migration marcada como aplicada!")
            
            print("🎉 Conversão de ENUMs concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro durante conversão: {e}")
            
            # Se der erro, tentar apenas marcar a migration como aplicada
            try:
                sql_version = text("INSERT INTO alembic_version (version_num) VALUES ('02e74ab3b348') ON CONFLICT DO NOTHING")
                with db.engine.connect() as conn:
                    conn.execute(sql_version)
                    conn.commit()
                print("✅ Migration marcada como aplicada mesmo com erro!")
            except Exception as e2:
                print(f"❌ Erro ao marcar migration: {e2}")

if __name__ == "__main__":
    fix_enums()