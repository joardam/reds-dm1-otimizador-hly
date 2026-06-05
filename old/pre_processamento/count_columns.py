import os
import sqlite3

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    db_path = os.path.join(project_root, "banco", "reds_dm1_clean.db")
    
    print("=================================================================")
    print("CONTAGEM DE COLUNAS DAS TABELAS CITADAS NA SEÇÃO 5 DO PDF")
    print("=================================================================\n")
    
    if not os.path.exists(db_path):
        print(f"[AVISO] Banco limpo nao encontrado em: {db_path}")
        print("Por favor, execute o script clean_database.py primeiro.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    listed_tables = [
        "EXAME_CLEAN",
        "PRESCRICAO_CLEAN",
        "PACIENTE_CLEAN",
        "APS_CADASTRO_INDV", # Nao existe fisicamente
        "ACOLHIMENTO_CLEAN",
        "ATENDIMENTO_CLEAN"
    ]
    
    total_listed_cols = 0
    missing_tables = []
    
    for table in listed_tables:
        try:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            if not columns:
                missing_tables.append(table)
                continue
            
            print(f"Tabela: {table} ({len(columns)} colunas)")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            total_listed_cols += len(columns)
            print("-" * 50)
        except Exception as e:
            missing_tables.append(table)
            
    if missing_tables:
        print("\nTabelas citadas no PDF que NÃO estão fisicamente no banco SQLite limpo:")
        for table in missing_tables:
            print(f"  - {table}")
            
    print(f"\nTotal de colunas nas tabelas físicas da Seção 5: {total_listed_cols}")
    
    print("\n" + "=" * 65)
    print("RESUMO DE TODAS AS TABELAS FÍSICAS DO BANCO SQLite LIMPO")
    print("=" * 65)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    all_tables = [row[0] for row in cursor.fetchall() if row[0] != "sqlite_sequence"]
    
    total_db_cols = 0
    for table in all_tables:
        cursor.execute(f"PRAGMA table_info({table});")
        cols_count = len(cursor.fetchall())
        print(f"  * {table:<25} : {cols_count} colunas")
        total_db_cols += cols_count
        
    print(f"\nTotal geral de colunas no banco SQLite limpo: {total_db_cols}")
    conn.close()

if __name__ == "__main__":
    main()
