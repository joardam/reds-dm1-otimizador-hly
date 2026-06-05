"""
seeder.py
Popula as tabelas de domínio e catálogos de referência (Sementes) no banco SQLite
para garantir a integridade referencial dos atendimentos, exames e diagnósticos.
"""

import sqlite3

# 1. Dados de SISTEMA_ORIGEM
SISTEMAS = [
    ("REDS-PE", "Rede Estadual de Dados em Saúde - Pernambuco"),
    ("E-SUS", "Sistema de Informação da Atenção Básica (APS)")
]

# 2. Dados de UNIDADE (Hospitais / Unidades em PE)
UNIDADES = [
    ("2280261", "Hospital Agamenon Magalhães", "2026-05-24T12:00:00", "10572048000109", 5),
    ("2280253", "Hospital da Restauração", "2026-05-24T12:00:00", "10572048000281", 5),
    ("2280164", "Hospital Getúlio Vargas", "2026-05-24T12:00:00", "10572048000362", 5),
    ("2280245", "Hospital Otávio de Freitas", "2026-05-24T12:00:00", "10572048000443", 5),
    ("2280180", "Hospital Barão de Lucena", "2026-05-24T12:00:00", "10572048000524", 5),
    ("2291247", "IMIP - Instituto de Medicina Integral", "2026-05-24T12:00:00", "33406242000171", 5)
]

# 3. Dados de PROFISSIONAL
PROFISSIONAIS = [
    ("Dr. Carlos Eduardo Santos", "11122233344", 1, "0", 101, "2026-05-24T12:00:00"),
    ("Dra. Ana Beatris Lima", "22233344455", 1, "0", 102, "2026-05-24T12:00:00"),
    ("Dr. Marcos André Melo", "33344455566", 1, "0", 103, "2026-05-24T12:00:00"),
    ("Dra. Patrícia Helena Costa", "44455566677", 1, "0", 104, "2026-05-24T12:00:00"),
    ("Dr. Ricardo Alexandre Silva", "55566677788", 1, "0", 105, "2026-05-24T12:00:00")
]

# 4. Dados de PROCEDIMENTO (SIGTAP)
PROCEDIMENTOS = [
    ("0202010471", "DETERMINACAO DE HEMOGLOBINA GLICADA", "SIGTAP", "2026-05-24T12:00:00"),
    ("0202010188", "DOSAGEM DE GLICOSE", "SIGTAP", "2026-05-24T12:00:00"),
    ("0301060061", "ATENDIMENTO DE URGENCIA EM ATENCAO ESPECIALIZADA", "SIGTAP", "2026-05-24T12:00:00"),
    ("0301010072", "CONSULTA MEDICA EM ATENCAO PRIMARIA", "SIGTAP", "2026-05-24T12:00:00")
]

# 5. Dados de DIAGNOSTICO (CID-10 para mapeamento)
DIAGNOSTICOS = [
    ("E10", "Diabetes mellitus insulinodependente (Tipo 1)", "2026-05-24T12:00:00", "CID10"),
    ("E10.9", "Diabetes mellitus tipo 1 sem complicacoes", "2026-05-24T12:00:00", "CID10"),
    ("E11", "Diabetes mellitus nao-insulinodependente (Tipo 2)", "2026-05-24T12:00:00", "CID10"),
    ("E11.9", "Diabetes mellitus tipo 2 sem complicacoes", "2026-05-24T12:00:00", "CID10"),
    ("N18", "Insuficiencia renal cronica", "2026-05-24T12:00:00", "CID10"),
    ("N18.9", "Insuficiencia renal cronica nao especificada", "2026-05-24T12:00:00", "CID10"),
    ("I10", "Hipertensao essencial (primaria)", "2026-05-24T12:00:00", "CID10"),
    ("I50", "Insuficiencia cardiaca", "2026-05-24T12:00:00", "CID10"),
    ("I50.9", "Insuficiencia cardiaca nao especificada", "2026-05-24T12:00:00", "CID10"),
    ("I64", "Acidente vascular cerebral nao especificado", "2026-05-24T12:00:00", "CID10"),
    ("I21", "Infarto agudo do miocardio", "2026-05-24T12:00:00", "CID10"),
    ("I21.9", "Infarto agudo do miocardio nao especificado", "2026-05-24T12:00:00", "CID10"),
    ("O24", "Diabetes mellitus na gravidez", "2026-05-24T12:00:00", "CID10")
]

def seed_database(conn: sqlite3.Connection):
    """Insere os dados de domínio necessários para garantir integridade."""
    cursor = conn.cursor()
    
    # 1. Inserir SISTEMA_ORIGEM
    cursor.executemany(
        "INSERT OR IGNORE INTO SISTEMA_ORIGEM (NOME, LABEL) VALUES (?, ?);",
        SISTEMAS
    )
    
    # 2. Inserir UNIDADE
    cursor.executemany(
        "INSERT OR IGNORE INTO UNIDADE (CD_CNES, NM_UNID, DT_ATUALZ, CNPJ_RESPONSAVEL, TP_UNID) VALUES (?, ?, ?, ?, ?);",
        UNIDADES
    )
    
    # 3. Inserir PROFISSIONAL
    cursor.executemany(
        "INSERT OR IGNORE INTO PROFISSIONAL (NM_PROFIS, CD_CPF, IN_SISTEM_ORIGEM, FL_ANONIMIZADO, ID_SISTEM_ORIGEM, DT_ATUALZ) VALUES (?, ?, ?, ?, ?, ?);",
        PROFISSIONAIS
    )
    
    # 4. Inserir PROCEDIMENTO
    cursor.executemany(
        "INSERT OR IGNORE INTO PROCEDIMENTO (CD_PROCED, DS_PROCED, TP_CD_PROCED, DT_ATUALZ) VALUES (?, ?, ?, ?);",
        PROCEDIMENTOS
    )
    
    # 5. Inserir DIAGNOSTICO
    cursor.executemany(
        "INSERT OR IGNORE INTO DIAGNOSTICO (CD_DIAG, DS_DIAG, DT_ATUALZ, TP_CD_DIAG) VALUES (?, ?, ?, ?);",
        DIAGNOSTICOS
    )
    
    conn.commit()
    print("[seeder] Dados de domínio (sementes) inseridos com sucesso.")

if __name__ == "__main__":
    conn = sqlite3.connect("test_reds.db")
    # Cria esquema primeiro
    import db_schema
    db_schema.create_tables(conn)
    seed_database(conn)
    conn.close()
    import os
    os.remove("test_reds.db")
