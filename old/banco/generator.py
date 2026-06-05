"""
generator.py
Orquestrador principal da geração de dados sintéticos para o banco REDS-DM1.
Lê o dataset clínico, aplica as regras de transformação e insere os dados de forma consistente no SQLite.
"""

import sqlite3
import random
import pandas as pd
import numpy as np
from datetime import datetime

import data_loader
import db_schema
import seeder
import translator

# Listas de nomes para geração aleatória e realista de brasileiros
FIRST_NAMES_M = ["João", "José", "Pedro", "Lucas", "Mateus", "Gabriel", "Rafael", "Carlos", 
                 "Francisco", "Paulo", "Fernando", "André", "Ricardo", "Antônio", "Marcos"]
FIRST_NAMES_F = ["Maria", "Ana", "Francisca", "Adriana", "Patrícia", "Amanda", "Camila", 
                 "Letícia", "Juliana", "Beatriz", "Mariana", "Débora", "Roberta", "Sandra", "Aline"]
SURNAMES = ["Silva", "Souza", "Costa", "Santos", "Oliveira", "Pereira", "Rodrigues", "Almeida", 
            "Nascimento", "Lima", "Araújo", "Carvalho", "Gomes", "Martins", "Barbosa", "Melo"]

def generate_random_name(gender: str) -> tuple:
    """Gera um nome completo de paciente e de sua mãe de forma realista."""
    surname1 = random.choice(SURNAMES)
    surname2 = random.choice(SURNAMES)
    if surname2 == surname1:
        surname2 = random.choice([s for s in SURNAMES if s != surname1])
        
    if gender == "Feminino":
        first = random.choice(FIRST_NAMES_F)
    else:
        first = random.choice(FIRST_NAMES_M)
        
    patient_name = f"{first} {surname1} {surname2}"
    
    # Nome da mãe (sempre feminino)
    mother_first = random.choice(FIRST_NAMES_F)
    mother_surname1 = random.choice(SURNAMES)
    mother_name = f"{mother_first} {mother_surname1} {surname2}"
    
    return patient_name, mother_name

def generate_synthetic_database(db_path: str = "reds_dm1.db", limit_rows: int = 15000):
    """Orquestra todo o processo de carregamento, transformação, geração e inserção."""
    print(f"\n[generator] Iniciando geração da base sintética em: {db_path}...")
    start_time = datetime.now()
    
    # 1. Carregar dados das fontes
    df = data_loader.load_clinical_data(limit_rows=limit_rows)
    municipios = data_loader.load_municipios()
    
    # Prepara vetor de probabilidade demográfica dos municípios de PE
    mun_probs = translator.get_municipio_weights(municipios)
    
    # 2. Conectar ao SQLite e preparar tabelas/seeds
    conn = sqlite3.connect(db_path)
    db_schema.create_tables(conn)
    seeder.seed_database(conn)
    
    cursor = conn.cursor()
    
    # Carrega catálogo de diagnósticos existentes para cache
    cursor.execute("SELECT ID_DIAGN, CD_DIAG FROM DIAGNOSTICO;")
    diag_catalog = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Carrega unidades existentes para vincular atendimentos aleatoriamente
    cursor.execute("SELECT ID_UNID FROM UNIDADE;")
    unidade_ids = [row[0] for row in cursor.fetchall()]
    
    # Carrega profissionais existentes
    cursor.execute("SELECT ID_PROFIS FROM PROFISSIONAL;")
    profissional_ids = [row[0] for row in cursor.fetchall()]
    
    # 3. Consolidação de Pacientes Únicos
    print("[generator] Processando pacientes únicos...")
    unique_patients = df.drop_duplicates(subset=["patient_nbr"])
    
    patient_nbr_to_id = {}
    patient_nbr_to_birth_info = {}
    patient_id_to_natural_keys = {}
    
    # Inserção de pacientes
    for idx, row in unique_patients.iterrows():
        gender = translator.translate_gender(row["gender"])
        race = translator.translate_race(row["race"])
        
        patient_name, mother_name = generate_random_name(gender)
        cpf = translator.generate_valid_cpf()
        cns = translator.generate_valid_cns()
        
        # Sorteia município
        mun_selected = random.choices(municipios, weights=mun_probs, k=1)[0]
        mun_name = mun_selected.get("nome", "Recife")
        
        # Gera data de nascimento estática
        birth_date_dt, age_years = translator.generate_birth_date(row["age"])
        birth_date_str = birth_date_dt.strftime("%Y-%m-%d")
        patient_nbr_to_birth_info[row["patient_nbr"]] = (birth_date_dt, age_years)
        
        # Gera contato e endereço sintéticos
        phone = translator.generate_phone_number()
        email = translator.generate_email(patient_name)
        tp_logr, logr, num_logr, bairro, cep = translator.generate_address()
        
        cursor.execute(
            """
            INSERT INTO PACIENTE (
                NM_PACIEN, DT_NASC, DS_CNS, CD_CPF, NM_MAE, DS_RACA, DS_NACION, NM_MUNIC, 
                SG_UF, NU_IDADE, IN_SEXO, FL_OBITO, DT_OBITO, DT_ATUALZ, DT_ATUALZ_ORIGEM,
                DS_TIPO_TEL1, DS_TIPO_TEL2, DS_TIPO_TEL3, NU_TEL1, NU_TEL2, NU_TEL3,
                DS_EMAIL, DS_TP_LOGRD, DS_LOGRD, NU_LOGRD, DS_COMPL, NM_BAIRRO, CD_CEP,
                FL_ANONIMIZADO, NM_SOCIAL
            ) VALUES (?, ?, ?, ?, ?, ?, 'Brasileira', ?, 'PE', ?, ?, 0, NULL, ?, ?, 'Celular', NULL, NULL, ?, NULL, NULL, ?, ?, ?, ?, NULL, ?, ?, '0', NULL);
            """,
            (
                patient_name, birth_date_str, cns, cpf, mother_name, race, mun_name,
                age_years, gender[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), birth_date_str,
                phone, email, tp_logr, logr, num_logr, bairro, cep
            )
        )
        db_id = cursor.lastrowid
        patient_nbr_to_id[row["patient_nbr"]] = db_id
        patient_id_to_natural_keys[db_id] = {"cpf": cpf, "cns": cns, "munic": mun_name}
        
    print(f"[generator] Inseridos {len(patient_nbr_to_id)} pacientes únicos.")
    
    # 4. Processamento de Atendimentos e Atividades Clínicas
    print("[generator] Processando atendimentos e eventos clínicos...")
    
    total_encounters = len(df)
    inserted_encounters = 0
    
    # Listas para inserção em lote (executemany) de tabelas filhas
    acolhimentos_batch = []
    atend_diagnos_batch = []
    exames_batch = []
    prescricoes_batch = []
    vacinas_batch = []
    
    for idx, row in df.iterrows():
        pat_db_id = patient_nbr_to_id[row["patient_nbr"]]
        time_hospital = int(row["time_in_hospital"])
        
        # Recupera informações de nascimento estáticas
        birth_date_dt, age_years = patient_nbr_to_birth_info[row["patient_nbr"]]
        
        # Gera cronologia do atendimento específico baseada no nascimento
        dates_info = translator.generate_encounter_dates(birth_date_dt, age_years, time_hospital)
        
        # Determina tipo de atendimento (se admission_type for emergência, etc)
        # 1: Emergency, 2: Urgent, 3: Elective
        adm_type_id = int(row["admission_type_id"]) if pd.notna(row["admission_type_id"]) else 3
        if adm_type_id == 1:
            ds_tipo = "E"
            ds_espec = "Medicina de Emergência"
        elif adm_type_id == 2:
            ds_tipo = "APS"
            ds_espec = "Clínica Médica"
        else:
            ds_tipo = "I"
            ds_espec = "Endocrinologia"
            
        unid_id = random.choice(unidade_ids)
        prof_id = random.choice(profissional_ids)
        
        # Sorteia óbito probabilístico baseado no status readmitted
        if row["readmitted"] == "<30" and age_years > 70 and random.random() < 0.15:
            cursor.execute(
                "UPDATE PACIENTE SET FL_OBITO = 1, DT_OBITO = ? WHERE ID_PACIEN = ?;",
                (dates_info["encounter_end"], pat_db_id)
            )
            
        # Insere Atendimento
        cursor.execute(
            """
            INSERT INTO ATENDIMENTO (
                ID_PACIEN, DT_MOMENT_INIC, DT_MOMENT_FIM, ID_UNID, ID_PROFIS, DS_TIPO_ATEND, 
                DS_ESPECI, DT_ATUALZ, IN_SISTEM_ORIGEM, ID_SISTEM_ORIGEM, TP_FICHA
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 'ATEND_INDIVIDUAL');
            """,
            (
                pat_db_id, dates_info["encounter_start"], dates_info["encounter_end"],
                unid_id, prof_id, ds_tipo, ds_espec, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        atend_db_id = cursor.lastrowid
        inserted_encounters += 1
        
        # Acolhimento e Triagem (Manchester)
        if adm_type_id == 1:
            cor, classif = random.choice([("VERMELHO", "MUITO URGENTE"), ("LARANJA", "MUITO URGENTE")])
        elif adm_type_id == 2:
            cor, classif = ("AMARELO", "URGENTE")
        else:
            cor, classif = random.choice([("VERDE", "POUCO URGENTE"), ("AZUL", "NÃO URGENTE")])
            
        sintoma, queixa = translator.get_symptoms(row.get("diag_1", ""), adm_type_id)
            
        acolhimentos_batch.append((
            pat_db_id, atend_db_id, dates_info["triage_start"], dates_info["triage_end"],
            cor, classif, sintoma, queixa,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1, 1, dates_info["triage_start"], prof_id,
            "Encaminhado para consulta médica."
        ))
        
        # Diagnósticos (Traduz diag_1, diag_2, diag_3)
        diags_to_map = [row.get("diag_1"), row.get("diag_2"), row.get("diag_3")]
        for d_idx, raw_diag in enumerate(diags_to_map):
            if pd.notna(raw_diag) and str(raw_diag).strip() != "?" and str(raw_diag).strip() != "":
                cid_code = translator.translate_diagnosis(raw_diag, age_years)
                
                # Se o CID não estiver no catálogo do banco, insere dinamicamente
                if cid_code not in diag_catalog:
                    cursor.execute(
                        "INSERT INTO DIAGNOSTICO (CD_DIAG, DS_DIAG, DT_ATUALZ, TP_CD_DIAG) VALUES (?, ?, ?, 'CID10');",
                        (cid_code, f"Diagnóstico clínico correspondente ao CID {cid_code}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    diag_catalog[cid_code] = cursor.lastrowid
                    
                diag_db_id = diag_catalog[cid_code]
                is_principal = "1" if d_idx == 0 else "0"
                
                atend_diagnos_batch.append((
                    is_principal, diag_db_id, atend_db_id, dates_info["encounter_start"], 1,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1
                ))
                
        # Exames (HbA1c)
        a1c_res = row.get("A1Cresult")
        if pd.notna(a1c_res) and str(a1c_res).strip() != "None":
            hba1c_val = translator.translate_hba1c(a1c_res)
            if hba1c_val is not None:
                # 1. Inserir Exame
                # O ID_PROCED 1 corresponde ao seed "DETERMINACAO DE HEMOGLOBINA GLICADA"
                cd_solic = random.randint(100000, 999999)
                cursor.execute(
                    """
                    INSERT INTO EXAME (
                        ID_UNID, ID_PACIEN, DT_REALIZACAO, ID_PROFIS_EXEC, ID_PROFIS_SOLIC, 
                        DS_MODALIDADE, IN_SISTEM_ORIGEM, ID_ATEND, ID_PROCED, DS_EXAME, DT_SOLICITACAO,
                        DT_ATUALZ, CD_ATEND, CD_SOLICITACAO, ID_SISTEM_ORIGEM
                    ) VALUES (?, ?, ?, ?, ?, 'LAB', 1, ?, 1, 'Hemoglobina Glicada HbA1c', ?, ?, ?, ?, 1);
                    """,
                    (
                        unid_id, pat_db_id, dates_info["exam_time"], prof_id, prof_id, 
                        atend_db_id, dates_info["encounter_start"],
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 200000000 + atend_db_id, cd_solic
                    )
                )
                exame_db_id = cursor.lastrowid
                
                # 2. Inserir Resultado de Exame
                cursor.execute(
                    """
                    INSERT INTO RES_EXAME (
                        DT_RES_EXAME, ID_EXAME, DS_RESULTADO, DS_CAMPO, ID_UNID, IN_SISTEM_ORIGEM,
                        DT_ATUALZ, CD_SOLICITACAO, CD_VERSAO_RES_EXAME, CD_CAMPOS_LAUDO, DT_ATUALZ_ORIGEM
                    ) VALUES (?, ?, ?, 'HbA1c', ?, 1, ?, ?, 1, 1, ?);
                    """,
                    (
                        dates_info["exam_result_time"], exame_db_id, str(hba1c_val), unid_id,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cd_solic, dates_info["exam_result_time"]
                    )
                )
                
        # Prescrições de Medicamento (Metformina, Insulina, Glibenclamida)
        prescs = translator.translate_medicines(row)
        for p in prescs:
            cd_prescr = 100000000 + atend_db_id
            cd_atend_val = 200000000 + atend_db_id
            cd_atend_emerg_val = cd_atend_val if ds_tipo == "E" else None
            prescricoes_batch.append((
                dates_info["prescription_time"], p["DS_TIPO"], p["DS_OBSERV_MEDTO"], 
                p["DS_VIA_ADMIN_MEDTO"], p["NM_MEDTO"], p["CD_MEDTO"], 
                dates_info["encounter_start"], dates_info["encounter_end"], prof_id, atend_db_id, 
                p["DS_DOSE_MEDTO"], 1,
                dates_info["prescription_time"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                cd_prescr, cd_prescr, cd_atend_val, cd_atend_emerg_val, 1
            ))
            
        # Vacinação probabilística (30% de chance para cada paciente cadastrado)
        # O histórico de vacina é anual, então geramos uma vez por paciente
        if random.random() < 0.3:
            nat_keys = patient_id_to_natural_keys[pat_db_id]
            vac_name = random.choice(["Vacina Influenza Triovalente", "Vacina Pneumococica 23-valente"])
            vacinas_batch.append((
                nat_keys["cpf"], nat_keys["cns"], "Centro de Saúde PE", nat_keys["munic"],
                dates_info["vaccine_time"], vac_name, dates_info["vaccine_time"]
            ))
 
    # 5. Inserção em Lote dos Batches
    print("[generator] Gravando registros filhos em lote...")
    
    if acolhimentos_batch:
        cursor.executemany(
            """
            INSERT INTO ACOLHIMENTO (
                ID_PACIEN, ID_ATEND, DT_ACOLMT, DT_FIM_ACOLMT, DS_COR_RISCO, DS_CLASSIF_RISCO, 
                DS_SINTOMA, DS_QUEIXA_PRINCIPAL, DT_ATUALZ, IN_SISTEM_ORIGEM, ID_SISTEM_ORIGEM,
                DT_ATUALZ_ORIGEM, ID_PROFIS, DS_RECOMENDACAO
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            acolhimentos_batch
        )
        
    if atend_diagnos_batch:
        cursor.executemany(
            """
            INSERT INTO ATEND_DIAGNOS (
                FL_DIAGN_PRINCIPAL, ID_DIAGN, ID_ATEND, DT_DIAGN, IN_SISTEM_ORIGEM,
                DT_ATUALZ, ID_SISTEM_ORIGEM
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            atend_diagnos_batch
        )
        
    if prescricoes_batch:
        cursor.executemany(
            """
            INSERT INTO PRESCRICAO_MEDICAMENTO (
                DT_MEDTO_CRIAD_EM, DS_TIPO, DS_OBSERV_MEDTO, DS_VIA_ADMIN_MEDTO, NM_MEDTO, 
                CD_MEDTO, DT_INC, DT_FIM, ID_PROFIS, ID_ATEND, DS_DOSE_MEDTO, IN_SISTEM_ORIGEM,
                DT_CRIACAO, DT_ATUALZ, CD_PRESCR_MEDTO, CD_PRESC, CD_ATEND, CD_ATEND_EMERG, ID_SISTEM_ORIGEM
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            prescricoes_batch
        )
        
    if vacinas_batch:
        cursor.executemany(
            """
            INSERT INTO IMUNIZACAO (
                CD_CPF, DS_CNS, NM_UNID_IMUN, NM_MUNIC_IMUN, DT_APLICACAO, CD_VACINA, DT_ATUALZ_ORIGEM
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            vacinas_batch
        )
        
    conn.commit()
    conn.close()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n[generator] Geração concluída com sucesso em {duration:.2f} segundos!")
    print(f"[generator] Resumo:")
    print(f"  - Atendimentos processados: {inserted_encounters}")
    print(f"  - Acolhimentos gerados: {len(acolhimentos_batch)}")
    print(f"  - Diagnósticos mapeados: {len(atend_diagnos_batch)}")
    print(f"  - Prescrições geradas: {len(prescricoes_batch)}")
    print(f"  - Vacinas aplicadas: {len(vacinas_batch)}")

if __name__ == "__main__":
    generate_synthetic_database(limit_rows=500)
