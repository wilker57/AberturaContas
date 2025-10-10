#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2.extras import RealDictCursor

def execute_query(query, params=None, fetch=True):
    """Executa uma query no banco de dados"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="abertura_contas",
            user="postgres",
            password="123456"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        
        if fetch:
            result = cursor.fetchall()
        else:
            result = cursor.rowcount > 0
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return result
    except Exception as e:
        print(f"Erro ao executar query: {e}")
        return None

def test_auto_numeracao():
    """Testa o sistema de auto-numeração de remessas"""
    
    print("🧪 Testando sistema de auto-numeração de remessas...")
    
    # 1. Verificar número atual máximo
    query_max = "SELECT COALESCE(MAX(num_remessa), 0) as max_num FROM remessa"
    resultado = execute_query(query_max)
    max_atual = resultado[0]['max_num'] if resultado else 0
    print(f"📊 Número máximo atual: {max_atual}")
    
    # 2. Calcular próximo número
    proximo_num = max_atual + 1
    print(f"🔢 Próximo número a ser usado: {proximo_num}")
    
    # 3. Inserir nova remessa com auto-numeração
    query_insert = """
        INSERT INTO remessa (num_processo, nome_proponente, cpf_cnpj, num_convenio, 
                           situacao, num_remessa, id_concedente, id_usuario, id_banco)
        VALUES (%s, %s, %s, %s, %s::situacaoenum, %s, %s, %s, %s)
    """
    
    resultado_insert = execute_query(query_insert, (
        "PROC2024001",  # num_processo
        "João Silva Santos",  # nome_proponente
        "123.456.789-00",  # cpf_cnpj
        "CONV2024001",  # num_convenio
        "EM_PREPARACAO",  # situacao
        proximo_num,  # num_remessa (auto-calculado)
        13,  # id_concedente (SEDUC)
        1,  # id_usuario (assumindo usuário 1 existe)
        None  # id_banco (opcional)
    ), fetch=False)
    
    if resultado_insert:
        print("✅ Remessa criada com sucesso!")
        
        # 4. Verificar se foi inserida corretamente
        query_verifica = "SELECT id_remessa, num_remessa, num_processo, nome_proponente FROM remessa WHERE num_remessa = %s"
        remessa_criada = execute_query(query_verifica, (proximo_num,))
        
        if remessa_criada:
            print(f"✅ Verificação: Remessa {remessa_criada[0]['num_remessa']} criada corretamente")
            print(f"   ID: {remessa_criada[0]['id_remessa']}")
            print(f"   Processo: {remessa_criada[0]['num_processo']}")
            print(f"   Proponente: {remessa_criada[0]['nome_proponente']}")
        else:
            print("❌ Erro: Remessa não encontrada após inserção")
            
        # 5. Testar segunda inserção para verificar incremento
        query_max2 = "SELECT COALESCE(MAX(num_remessa), 0) + 1 as proximo_num FROM remessa"
        resultado2 = execute_query(query_max2)
        proximo_num2 = resultado2[0]['proximo_num'] if resultado2 else 1
        
        resultado_insert2 = execute_query(query_insert, (
            "PROC2024002",  # num_processo
            "Maria Oliveira",  # nome_proponente
            "987.654.321-00",  # cpf_cnpj
            "CONV2024002",  # num_convenio
            "EM_PREPARACAO",  # situacao
            proximo_num2,  # num_remessa (auto-calculado)
            13,  # id_concedente (SEDUC)
            1,  # id_usuario
            None  # id_banco
        ), fetch=False)
        
        if resultado_insert2:
            print(f"✅ Segunda remessa criada com num_remessa = {proximo_num2}")
            
            # Verificar listagem final
            query_final = "SELECT id_remessa, num_remessa, num_processo, nome_proponente FROM remessa ORDER BY num_remessa"
            todas_remessas = execute_query(query_final)
            
            print("\n📋 Todas as remessas no banco:")
            for remessa in todas_remessas:
                print(f"   {remessa['num_remessa']} - {remessa['num_processo']} - {remessa['nome_proponente']}")
                
        else:
            print("❌ Erro ao criar segunda remessa")
    else:
        print("❌ Erro ao criar primeira remessa")

def test_constraint_unique():
    """Testa se a constraint UNIQUE está funcionando"""
    print("\n🔒 Testando constraint UNIQUE...")
    
    # Tentar inserir remessa com num_remessa duplicado
    query_insert_dup = """
        INSERT INTO remessa (num_processo, nome_proponente, cpf_cnpj, num_convenio, 
                           situacao, num_remessa, id_concedente, id_usuario, id_banco)
        VALUES (%s, %s, %s, %s, %s::situacaoenum, %s, %s, %s, %s)
    """
    
    try:
        resultado_dup = execute_query(query_insert_dup, (
            "PROC2024003",  # num_processo
            "Pedro Costa",  # nome_proponente
            "111.222.333-44",  # cpf_cnpj
            "CONV2024003",  # num_convenio
            "EM_PREPARACAO",  # situacao
            1,  # num_remessa (duplicado!)
            13,  # id_concedente
            1,  # id_usuario
            None  # id_banco
        ), fetch=False)
        
        if resultado_dup:
            print("❌ ERRO: Constraint UNIQUE não está funcionando! Inserção duplicada permitida.")
        else:
            print("✅ Constraint UNIQUE funcionando corretamente")
            
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            print("✅ Constraint UNIQUE funcionando corretamente - inserção duplicada bloqueada")
        else:
            print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    test_auto_numeracao()
    test_constraint_unique()
    print("\n🎯 Teste concluído!")