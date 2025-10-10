# fix_enums_complete.py - Script completo para corrigir ENUMs

from app import create_app
from produto.models import db
from sqlalchemy import text

def fix_enums_complete():
    """Corrige os tipos ENUM no PostgreSQL removendo defaults primeiro"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Corrigindo ENUMs no banco de dados (método completo)...")
        
        try:
            # Passo 1: Remover valores padrão
            print("1️⃣ Removendo valores padrão...")
            
            sql_remove_defaults = text("""
            ALTER TABLE usuario 
            ALTER COLUMN perfil_enum DROP DEFAULT,
            ALTER COLUMN status_enum DROP DEFAULT
            """)
            
            with db.engine.connect() as conn:
                conn.execute(sql_remove_defaults)
                conn.commit()
            print("✅ Valores padrão removidos!")
            
            # Passo 2: Converter perfil_enum
            print("2️⃣ Convertendo perfil_enum...")
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
            print("✅ perfil_enum convertido!")
            
            # Passo 3: Converter status_enum
            print("3️⃣ Convertendo status_enum...")
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
            print("✅ status_enum convertido!")
            
            # Passo 4: Redefinir valores padrão
            print("4️⃣ Redefinindo valores padrão...")
            sql_set_defaults = text("""
            ALTER TABLE usuario 
            ALTER COLUMN perfil_enum SET DEFAULT 'MONITOR'::perfilenum,
            ALTER COLUMN status_enum SET DEFAULT 'ATIVO'::statusenum
            """)
            
            with db.engine.connect() as conn:
                conn.execute(sql_set_defaults)
                conn.commit()
            print("✅ Valores padrão redefinidos!")
            
            print("🎉 Conversão de ENUMs concluída com sucesso!")
            
            # Verificar se funcionou
            print("🔍 Verificando conversão...")
            sql_check = text("SELECT perfil_enum, status_enum FROM usuario LIMIT 1")
            with db.engine.connect() as conn:
                result = conn.execute(sql_check).fetchone()
                if result:
                    print(f"✅ Dados verificados: perfil={result[0]}, status={result[1]}")
                else:
                    print("⚠️ Nenhum usuário encontrado para verificação")
            
        except Exception as e:
            print(f"❌ Erro durante conversão: {e}")
            return False
            
        return True

if __name__ == "__main__":
    success = fix_enums_complete()
    if success:
        print("\n🎊 PROCESSO CONCLUÍDO COM SUCESSO!")
        print("Agora você pode executar: python manage.py")
    else:
        print("\n💥 PROCESSO FALHOU!")
        print("Verifique os erros acima.")