"""
main.py
Ponto de entrada (CLI) para a geração e validação da base sintética REDS-DM1.
"""

import argparse
import sys
import os
from datetime import datetime

import generator
import validator

def main():
    parser = argparse.ArgumentParser(
        description="Gerador de Dados Clínicos Sintéticos para REDS-DM1"
    )
    parser.add_argument(
        "--db", 
        type=str, 
        default="reds_dm1.db", 
        help="Caminho do arquivo do banco SQLite final (padrão: reds_dm1.db)"
    )
    parser.add_argument(
        "--rows", 
        type=int, 
        default=15000, 
        help="Quantidade de linhas do dataset Kaggle a serem processadas (padrão: 15000)"
    )
    parser.add_argument(
        "--validate-only", 
        action="store_true", 
        help="Executa apenas a validação em um banco existente"
    )
    
    args = parser.parse_args()
    
    print("=" * 65)
    print("SISTEMA GERADOR DE DADOS SINTETICOS REDS-DM1 (PERNAMBUCO/SUS)")
    print("=" * 65)
    
    start_time = datetime.now()
    
    if args.validate_only:
        if not os.path.exists(args.db):
            print(f"[ERRO] Banco de dados '{args.db}' nao existe para validacao.")
            sys.exit(1)
        success = validator.run_validation(args.db)
        sys.exit(0 if success else 1)
        
    try:
        # Executa geração
        generator.generate_synthetic_database(db_path=args.db, limit_rows=args.rows)
        
        # Executa validação
        success = validator.run_validation(args.db)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 65)
        if success:
            print(f"[SUCESSO] Banco de dados '{args.db}' gerado e validado em {duration:.2f}s!")
        else:
            print(f"[AVISO] Geracao concluida, mas ocorrem falhas de validacao. Verifique logs.")
        print("=" * 65 + "\n")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n[Erro Fatal] Ocorreu uma falha durante o processamento:\n{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
