"""
validator.py
Suite de validação para verificar a integridade relacional, cronológica e semântica
do banco de dados SQLite REDS-DM1 gerado.
"""

import sqlite3
from datetime import datetime

def run_validation(db_path: str = "reds_dm1.db") -> bool:
    """Executa verificações automatizadas de integridade e imprime estatísticas."""
    print(f"\n[validator] Iniciando validação para: {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ativa validação de chaves estrangeiras no SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    all_passed = True
    errors = []
    
    # -------------------------------------------------------------
    # 1. Contagem de Registros por Tabela
    # -------------------------------------------------------------
    print("\n[validator] --- Contagem de Registros ---")
    tables = [
        "SISTEMA_ORIGEM", "UNIDADE", "PROFISSIONAL", "PROCEDIMENTO", 
        "PACIENTE", "ATENDIMENTO", "ACOLHIMENTO", "DIAGNOSTICO", 
        "ATEND_DIAGNOS", "EXAME", "RES_EXAME", "PRESCRICAO_MEDICAMENTO", "IMUNIZACAO"
    ]
    
    stats = {}
    for t in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t};")
            count = cursor.fetchone()[0]
            stats[t] = count
            print(f"  Tabela {t:23}: {count} registros")
        except sqlite3.OperationalError as e:
            print(f"  [ERRO] Tabela {t} não encontrada ou erro de leitura: {e}")
            all_passed = False
            errors.append(f"Tabela {t} inacessível")
            
    # -------------------------------------------------------------
    # 2. Verificação de Chaves Estrangeiras (Integridade Relacional)
    # -------------------------------------------------------------
    print("\n[validator] --- Integridade Relacional ---")
    
    # Verificação nativa do SQLite
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    if fk_violations:
        print(f"  [ERRO] Encontradas {len(fk_violations)} violações de Foreign Key pelo SQLite.")
        for v in fk_violations:
            errors.append(f"Violação FK: Tabela={v[0]}, RowId={v[1]}, Parent={v[2]}, FkIndex={v[3]}")
        all_passed = False
    else:
        print("  [OK] Chaves Estrangeiras integras (SQLite PRAGMA check)")
        
    # Verificação de Chave Natural na Imunização (Vacinas)
    cursor.execute(
        """
        SELECT COUNT(*) FROM IMUNIZACAO 
        WHERE CD_CPF NOT IN (SELECT CD_CPF FROM PACIENTE);
        """
    )
    orphan_vaccines = cursor.fetchone()[0]
    if orphan_vaccines > 0:
        print(f"  [ERRO] Encontradas {orphan_vaccines} vacinas associadas a CPFs inexistentes na tabela PACIENTE.")
        errors.append(f"{orphan_vaccines} vacinas orfas por CPF")
        all_passed = False
    else:
        print("  [OK] Chaves Naturais de Imunizacao consistentes (CPF vinculados)")

    # -------------------------------------------------------------
    # 3. Verificação de Cronologia
    # -------------------------------------------------------------
    print("\n[validator] --- Integridade Cronologica ---")
    
    # A. Nascimento posterior à admissão do atendimento
    cursor.execute(
        """
        SELECT COUNT(*) FROM ATENDIMENTO a 
        JOIN PACIENTE p ON a.ID_PACIEN = p.ID_PACIEN
        WHERE datetime(p.DT_NASC) >= datetime(a.DT_MOMENT_INIC);
        """
    )
    nasc_atend_violation = cursor.fetchone()[0]
    if nasc_atend_violation > 0:
        print(f"  [ERRO] {nasc_atend_violation} atendimentos com data de admissao anterior ao nascimento do paciente.")
        errors.append(f"Admissao anterior ao nascimento: {nasc_atend_violation}")
        all_passed = False
    else:
        print("  [OK] Nascimento < Admissao")
        
    # B. Admissão posterior à alta
    cursor.execute(
        """
        SELECT COUNT(*) FROM ATENDIMENTO 
        WHERE datetime(DT_MOMENT_INIC) > datetime(DT_MOMENT_FIM);
        """
    )
    alta_violation = cursor.fetchone()[0]
    if alta_violation > 0:
        print(f"  [ERRO] {alta_violation} atendimentos com data de inicio posterior a data de termino (alta).")
        errors.append(f"Inicio do atendimento posterior a alta: {alta_violation}")
        all_passed = False
    else:
        print("  [OK] Admissao <= Alta")
        
    # C. Triagem posterior à admissão
    cursor.execute(
        """
        SELECT COUNT(*) FROM ACOLHIMENTO ac
        JOIN ATENDIMENTO at ON ac.ID_ATEND = at.ID_ATEND
        WHERE datetime(ac.DT_ACOLMT) > datetime(at.DT_MOMENT_INIC);
        """
    )
    triage_violation = cursor.fetchone()[0]
    if triage_violation > 0:
        print(f"  [ERRO] {triage_violation} triagens (ACOLHIMENTO) ocorridas apos a admissao (ATENDIMENTO).")
        errors.append(f"Triagem apos admissao: {triage_violation}")
        all_passed = False
    else:
        print("  [OK] Triagem <= Admissao")
        
    # D. Liberação do resultado antes do exame
    cursor.execute(
        """
        SELECT COUNT(*) FROM RES_EXAME r
        JOIN EXAME e ON r.ID_EXAME = e.ID_EXAME
        WHERE datetime(r.DT_RES_EXAME) < datetime(e.DT_REALIZACAO);
        """
    )
    result_violation = cursor.fetchone()[0]
    if result_violation > 0:
        print(f"  [ERRO] {result_violation} resultados de exames liberados antes da realizacao do exame.")
        errors.append(f"Resultado antes do exame: {result_violation}")
        all_passed = False
    else:
        print("  [OK] Exame Realizado <= Resultado Liberado")

    # -------------------------------------------------------------
    # 4. Consistência Semântica dos Dados
    # -------------------------------------------------------------
    print("\n[validator] --- Consistencia de Dados Clinicos ---")
    
    # A. Faixas de HbA1c
    cursor.execute("SELECT CAST(DS_RESULTADO AS REAL) FROM RES_EXAME WHERE DS_CAMPO = 'HbA1c';")
    hba1c_vals = [r[0] for r in cursor.fetchall()]
    if hba1c_vals:
        avg_hba1c = sum(hba1c_vals) / len(hba1c_vals)
        min_hba1c = min(hba1c_vals)
        max_hba1c = max(hba1c_vals)
        print(f"  [OK] Media de HbA1c: {avg_hba1c:.2f}% (Minimo: {min_hba1c}%, Maximo: {max_hba1c}%)")
        if min_hba1c < 3.0 or max_hba1c > 20.0:
            print("  [AVISO] Valores de HbA1c fora das faixas clinicas biologicas usuais.")
    else:
        print("  [AVISO] Nenhum exame de HbA1c cadastrado para analise.")
        
    # B. Gêneros Cadastrados
    cursor.execute("SELECT DISTINCT IN_SEXO FROM PACIENTE;")
    sexos = [r[0] for r in cursor.fetchall()]
    print(f"  [OK] Generos mapeados na base (PACIENTE.IN_SEXO): {sexos}")
    if any(s not in ['F', 'M'] for s in sexos):
        print("  [ERRO] Encontrados formatos incorretos para a coluna de sexo. Deve ser apenas 'F' ou 'M'.")
        errors.append("Formato incorreto de sexo")
        all_passed = False
        
    # C. Validação de CPFs e CNSs (Tamanho e padrão numérico)
    cursor.execute("SELECT CD_CPF, DS_CNS FROM PACIENTE;")
    pacientes_keys = cursor.fetchall()
    cpf_lens = [len(pk[0]) for pk in pacientes_keys if pk[0]]
    cns_lens = [len(pk[1]) for pk in pacientes_keys if pk[1]]
    if any(l != 11 for l in cpf_lens):
        print("  [ERRO] Existem CPFs com comprimento diferente de 11 caracteres.")
        errors.append("CPF com tamanho incorreto")
        all_passed = False
    if any(l != 15 for l in cns_lens):
        print("  [ERRO] Existem CNSs com comprimento diferente de 15 caracteres.")
        errors.append("CNS com tamanho incorreto")
        all_passed = False
        
    if all_passed:
        print("\n[SUCESSO] A base passou em todos os testes de validacao!")
    else:
        print(f"\n[ERRO] FALHAS ENCONTRADAS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
            
    conn.close()
    return all_passed

if __name__ == "__main__":
    run_validation()
