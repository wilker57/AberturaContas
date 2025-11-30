#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from produto.views import execute_query, check_password_hash

def test_login(login, senha):
    print(f"=== Testando login: {login} ===")
    
    # Testar a consulta diretamente
    query = "SELECT id_usuario, login, nome, senha, perfil_enum FROM usuario WHERE login = %s"
    users = execute_query(query, (login,))
    print(f"Resultado da consulta: {users}")
    
    if users and len(users) > 0:
        user = users[0]
        print(f"Usuario encontrado:")
        print(f"  - ID: {user['id_usuario']}")
        print(f"  - Login: {user['login']}")
        print(f"  - Nome: {user['nome']}")
        print(f"  - Perfil: {user['perfil_enum']}")
        print(f"  - Senha length: {len(user['senha']) if user['senha'] else 0}")
        print(f"  - Senha preview: {user['senha'][:20] if user['senha'] else 'None'}...")
        
        # Testar a verificação da senha
        try:
            if user['senha']:
                result = check_password_hash(user['senha'], senha)
                print(f"  - Verificacao da senha: {result}")
                return result
            else:
                print("  - ERRO: Campo senha está vazio!")
                return False
        except Exception as e:
            print(f"  - ERRO na verificacao: {e}")
            return False
    else:
        print("Usuario nao encontrado")
        return False

if __name__ == "__main__":
    # Testar com dados conhecidos
    test_login('pauloc', '123456')
    print()
    test_login('teste', '123456')