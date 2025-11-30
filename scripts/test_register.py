#!/usr/bin/env python3
"""
Script de teste para verificar se o cadastro de usuários está funcionando
"""

import requests
import json

# URL base da aplicação
BASE_URL = "http://127.0.0.1:5000"

def test_register():
    """Testa o cadastro de um novo usuário"""
    
    # Dados do usuário de teste
    user_data = {
        'nome': 'João Silva Teste',
        'matricula': '12345678',
        'email': 'joao.teste@email.com',
        'instituicao': 'FUNDES',
        'login': 'joaosilva',
        'senha': 'senha123',
        'confirm_senha': 'senha123'
    }
    
    print("🧪 Testando cadastro de usuário...")
    print(f"📊 Dados do usuário: {json.dumps(user_data, indent=2, ensure_ascii=False)}")
    
    try:
        # Faz a requisição POST para o endpoint de registro
        response = requests.post(f"{BASE_URL}/registrar", data=user_data, allow_redirects=False)
        
        print(f"📋 Status Code: {response.status_code}")
        print(f"📍 Headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            print("✅ Redirecionamento detectado - cadastro provavelmente bem-sucedido!")
            print(f"🔗 Redirecionando para: {response.headers.get('Location', 'N/A')}")
        elif response.status_code == 200:
            print("⚠️ Status 200 - pode haver erro no formulário")
            print(f"📄 Conteúdo da resposta (primeiros 500 chars):")
            print(response.text[:500])
        else:
            print(f"❌ Erro no cadastro - Status: {response.status_code}")
            print(f"📄 Resposta: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor Flask")
        print("🔍 Verifique se o servidor está rodando em http://127.0.0.1:5000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

def test_users_list():
    """Testa a listagem de usuários"""
    print("\n🧪 Testando listagem de usuários...")
    
    try:
        response = requests.get(f"{BASE_URL}/usuarios")
        print(f"📋 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Listagem acessível")
        else:
            print(f"❌ Erro na listagem - Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao acessar listagem: {e}")

if __name__ == "__main__":
    test_register()
    test_users_list()