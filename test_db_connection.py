#!/usr/bin/env python
import sys
import os

# Adiciona o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import get_conn, close_connection
    print(" Módulo config importado com sucesso!")
except ImportError as e:
    print(f" Erro ao importar config: {e}")
    sys.exit(1)

def test_database_connection():
    
    
    print("\n🔍 Iniciando teste de conexão com o banco de dados...")
    print("=" * 50)
    
    try:
        # Tenta estabelecer conexão
        print("🔌 Tentando conectar ao banco 'abertura_contas'...")
        conn = get_conn()
        
        if conn:
            print(" Conexão estabelecida com sucesso!")
            
            # Testa se consegue executar uma query simples
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f" Versão do PostgreSQL: {version[0]}")
            
            # Testa se o banco existe e está acessível
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            print(f"🗄️ Banco de dados atual: {db_name[0]}")
            
            # Fecha cursor
            cursor.close()
            
            # Fecha conexão
            close_connection(conn)
            print("✅ Teste de conexão concluído com sucesso!")
            
        else:
            print(" Falha ao estabelecer conexão!")
            return False
            
    except Exception as e:
        print(f" Erro durante o teste: {e}")
        return False
    
    print("=" * 50)
    return True

if __name__ == "__main__":
    print("🚀 TESTE DE CONEXÃO COM BANCO DE DADOS")
    success = test_database_connection()
    
    if success:
        print("\n🎉 Todos os testes passaram!")
        sys.exit(0)
    else:
        print("\n💥 Teste falhou! Verifique as configurações do banco.")
        sys.exit(1)