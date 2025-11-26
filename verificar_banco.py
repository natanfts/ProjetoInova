"""
Script para verificar o conteúdo do banco SQLite e confirmar a migração do CSV.
"""

import sqlite3
from pathlib import Path
from src.config.config import Config

def verificar_banco():
    """Verifica o conteúdo do banco SQLite."""
    db_path = Config.DB_PATH
    
    if not db_path.exists():
        print(f"❌ Banco SQLite não encontrado: {db_path}")
        return
    
    print(f"📦 Verificando banco SQLite: {db_path}")
    print(f"   Tamanho: {db_path.stat().st_size} bytes\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifica tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas = [row[0] for row in cursor.fetchall()]
    print(f"📋 Tabelas encontradas: {', '.join(tabelas)}\n")
    
    # Verifica gestos (tabela antiga)
    cursor.execute("SELECT COUNT(*) FROM gestos")
    count_gestos = cursor.fetchone()[0]
    print(f"📊 Gestos na tabela 'gestos' (compatibilidade): {count_gestos}")
    if count_gestos > 0:
        cursor.execute("SELECT dedos, mensagem FROM gestos LIMIT 5")
        print("   Primeiros gestos:")
        for dedos, mensagem in cursor.fetchall():
            print(f"     - {dedos}: {mensagem[:50]}...")
    print()
    
    # Verifica configurações simplificadas
    cursor.execute("SELECT COUNT(*) FROM config_gestos")
    count_config = cursor.fetchone()[0]
    print(f"⚙️  Configurações na tabela 'config_gestos': {count_config}")
    if count_config > 0:
        cursor.execute("SELECT num_dedos, mensagem, prioridade FROM config_gestos ORDER BY num_dedos")
        print("   Configurações:")
        for num_dedos, mensagem, prioridade in cursor.fetchall():
            print(f"     - {num_dedos} dedo(s): {mensagem[:50]}... (prioridade: {prioridade})")
    else:
        print("   ⚠️  Nenhuma configuração encontrada!")
    print()
    
    # Verifica pacientes
    cursor.execute("SELECT COUNT(*) FROM pacientes")
    count_pacientes = cursor.fetchone()[0]
    print(f"👤 Pacientes cadastrados: {count_pacientes}")
    if count_pacientes > 0:
        cursor.execute("SELECT id, nome, quarto, ativo FROM pacientes LIMIT 5")
        print("   Pacientes:")
        for id, nome, quarto, ativo in cursor.fetchall():
            status = "✅ Ativo" if ativo else "❌ Inativo"
            print(f"     - {id}: {nome} (Quarto {quarto}) - {status}")
    print()
    
    # Verifica histórico
    cursor.execute("SELECT COUNT(*) FROM historico_solicitacoes")
    count_historico = cursor.fetchone()[0]
    print(f"📜 Solicitações no histórico: {count_historico}")
    
    conn.close()
    
    print("\n✅ Verificação concluída!")

if __name__ == "__main__":
    verificar_banco()

