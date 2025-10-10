# manage.py - Ponto de entrada da aplicação

from app import create_app

# Cria a aplicação
app = create_app()

if __name__ == "__main__":
    # Criar tabelas automaticamente na primeira execução
    with app.app_context():
        from produto.models import db
        print("🔄 Verificando/criando estrutura do banco de dados...")
        try:
            db.create_all()
            print("✅ Estrutura do banco verificada/criada com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao verificar estrutura do banco: {e}")
    
    print("🚀 Iniciando servidor Flask...")
    app.run(debug=True, host='0.0.0.0', port=5000)
