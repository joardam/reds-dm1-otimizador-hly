import os
import sqlite3
import pandas as pd
import numpy as np

def create_clean_database():
    # Caminhos baseados na pasta onde o script está localizado
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    orig_db_path = os.path.join(project_root, "banco", "reds_dm1.db")
    clean_db_path = os.path.join(project_root, "banco", "reds_dm1_clean.db")
    
    print(f"[clean_database] Conectando ao banco original: {orig_db_path}")
    if not os.path.exists(orig_db_path):
        print(f"[ERRO] Banco original nao encontrado em: {orig_db_path}")
        return
        
    conn_orig = sqlite3.connect(orig_db_path)
    
    print(f"[clean_database] Criando/sobrescrevendo banco limpo: {clean_db_path}")
    conn_clean = sqlite3.connect(clean_db_path)
    
    # 1. Limpar e transferir PACIENTE
    print("[clean_database] Limpando dados de PACIENTE...")
    df_paciente = pd.read_sql_query(
        "SELECT ID_PACIEN, NU_IDADE, IN_SEXO, NM_MUNIC, DS_RACA, FL_OBITO FROM PACIENTE", 
        conn_orig
    )
    df_paciente.to_sql("PACIENTE_CLEAN", conn_clean, if_exists="replace", index=False)
    
    # 2. Limpar e transferir ATENDIMENTO
    print("[clean_database] Limpando dados de ATENDIMENTO...")
    df_atend = pd.read_sql_query(
        "SELECT ID_ATEND, ID_PACIEN, DS_TIPO_ATEND, DS_ESPECI, DT_MOMENT_INIC, DT_MOMENT_FIM FROM ATENDIMENTO", 
        conn_orig
    )
    # Calcula duração em dias para servir como custo ou duração de internação
    df_atend['DT_MOMENT_INIC'] = pd.to_datetime(df_atend['DT_MOMENT_INIC'])
    df_atend['DT_MOMENT_FIM'] = pd.to_datetime(df_atend['DT_MOMENT_FIM'])
    df_atend['TEMPO_INTERNACAO_DIAS'] = (df_atend['DT_MOMENT_FIM'] - df_atend['DT_MOMENT_INIC']).dt.total_seconds() / (24 * 3600)
    df_atend['TEMPO_INTERNACAO_DIAS'] = df_atend['TEMPO_INTERNACAO_DIAS'].round(2)
    df_atend.to_sql("ATENDIMENTO_CLEAN", conn_clean, if_exists="replace", index=False)
    
    # 3. Limpar e transferir ACOLHIMENTO
    print("[clean_database] Limpando dados de ACOLHIMENTO...")
    df_acol = pd.read_sql_query(
        "SELECT ID_ATEND, DS_COR_RISCO, DS_CLASSIF_RISCO, DS_SINTOMA FROM ACOLHIMENTO", 
        conn_orig
    )
    df_acol.to_sql("ACOLHIMENTO_CLEAN", conn_clean, if_exists="replace", index=False)
    
    # 4. Limpar e transferir DIAGNOSTICO e ATEND_DIAGNOS
    print("[clean_database] Limpando dados de DIAGNOSTICOS...")
    df_diag = pd.read_sql_query(
        """
        SELECT ad.ID_ATEND, d.CD_DIAG, ad.FL_DIAGN_PRINCIPAL 
        FROM ATEND_DIAGNOS ad
        JOIN DIAGNOSTICO d ON ad.ID_DIAGN = d.ID_DIAGN
        """,
        conn_orig
    )
    df_diag.to_sql("DIAGNOSTICO_CLEAN", conn_clean, if_exists="replace", index=False)
    
    # 5. Limpar e transferir RES_EXAME e EXAME (HbA1c)
    print("[clean_database] Limpando dados de EXAMES (HbA1c)...")
    df_exames = pd.read_sql_query(
        """
        SELECT e.ID_ATEND, re.DS_CAMPO, CAST(re.DS_RESULTADO AS REAL) as VALOR_RESULTADO
        FROM RES_EXAME re
        JOIN EXAME e ON re.ID_EXAME = e.ID_EXAME
        WHERE re.DS_CAMPO = 'HbA1c'
        """,
        conn_orig
    )
    df_exames.to_sql("EXAME_CLEAN", conn_clean, if_exists="replace", index=False)
    
    # 6. Limpar e transferir PRESCRICAO_MEDICAMENTO
    print("[clean_database] Limpando dados de PRESCRICAO_MEDICAMENTO...")
    df_prescr = pd.read_sql_query(
        "SELECT ID_ATEND, NM_MEDTO, DS_DOSE_MEDTO, DS_VIA_ADMIN_MEDTO FROM PRESCRICAO_MEDICAMENTO", 
        conn_orig
    )
    df_prescr.to_sql("PRESCRICAO_CLEAN", conn_clean, if_exists="replace", index=False)
    
    # -------------------------------------------------------------
    # 7. CONSTRUÇÃO DO MODEL_DATASET CONSOLIDADO (TABELA PLANA)
    # -------------------------------------------------------------
    print("\n[clean_database] Iniciando a consolidacao do MODEL_DATASET plano...")
    
    df_model = pd.merge(df_atend, df_paciente, on="ID_PACIEN", how="inner")
    df_model = pd.merge(df_model, df_acol, on="ID_ATEND", how="left")
    
    df_exames_pivot = df_exames.pivot_table(
        index="ID_ATEND", 
        columns="DS_CAMPO", 
        values="VALOR_RESULTADO", 
        aggfunc="mean"
    ).reset_index()
    
    if "HbA1c" in df_exames_pivot.columns:
        df_exames_pivot.rename(columns={"HbA1c": "EXAME_HBA1C"}, inplace=True)
    else:
        df_exames_pivot["EXAME_HBA1C"] = np.nan
        
    df_model = pd.merge(df_model, df_exames_pivot, on="ID_ATEND", how="left")
    
    meds_grouped = df_prescr.groupby(["ID_ATEND", "NM_MEDTO"]).size().unstack(fill_value=0).reset_index()
    
    # Mapeamento expandido para TODAS as drogas do Kaggle (Crucial para o BFSS)
    med_cols = {
        "Cloridrato de Metformina (850mg)": "MED_METFORMINA",
        "Insulina Humana (NPH/Regular)": "MED_INSULINA",
        "Glipizida (5mg)": "MED_GLIPIZIDA",
        "Glibenclamida (5mg)": "MED_GLIBENCLAMIDA",
        "Repaglinida (2mg)": "MED_REPAGLINIDA",
        "Nateglinida (120mg)": "MED_NATEGLINIDA",
        "Clorpropamida (250mg)": "MED_CLORPROPAMIDA",
        "Glimepirida (2mg)": "MED_GLIMEPIRIDA",
        "Aceto-hexamida": "MED_ACETOHEXAMIDA",
        "Tolbutamida": "MED_TOLBUTAMIDA",
        "Pioglitazona (30mg)": "MED_PIOGLITAZONA",
        "Rosiglitazona (4mg)": "MED_ROSIGLITAZONA",
        "Acarbose (50mg)": "MED_ACARBOSE",
        "Miglitol (50mg)": "MED_MIGLITOL",
        "Troglitazona": "MED_TROGLITAZONA",
        "Tolazamida": "MED_TOLAZAMIDA",
        "Exameida": "MED_EXAMEIDA",
        "Citogliptina": "MED_CITOGLIPTINA",
        "Glibenclamida + Metformina": "MED_GLIBENCLAMIDA_METFORMINA",
        "Glipizida + Metformina": "MED_GLIPIZIDA_METFORMINA",
        "Glimepirida + Pioglitazona": "MED_GLIMEPIRIDA_PIOGLITAZONA",
        "Metformina + Rosiglitazona": "MED_METFORMINA_ROSIGLITAZONA",
        "Metformina + Pioglitazona": "MED_METFORMINA_PIOGLITAZONA",
        # Legado (caso a base bruta ainda tenha essas nomenclaturas)
        "Insulina Humana NPH": "MED_INSULINA_NPH",
        "Insulina Humana Regular": "MED_INSULINA_REGULAR"
    }
    
    for orig_name, clean_name in med_cols.items():
        if orig_name in meds_grouped.columns:
            df_model[clean_name] = df_model["ID_ATEND"].map(
                meds_grouped.set_index("ID_ATEND")[orig_name]
            ).fillna(0).astype(int)
        else:
            df_model[clean_name] = 0
            
    df_diag['IS_RENAL'] = df_diag['CD_DIAG'].str.startswith('N18').astype(int)
    df_diag['IS_CARDIOVASCULAR'] = df_diag['CD_DIAG'].str.startswith(('I21', 'I50', 'I10', 'I64')).astype(int)
    
    diag_grouped = df_diag.groupby('ID_ATEND').agg({
        'IS_RENAL': 'max',
        'IS_CARDIOVASCULAR': 'max'
    }).reset_index()
    
    df_model = pd.merge(df_model, diag_grouped, on="ID_ATEND", how="left")
    df_model['IS_RENAL'] = df_model['IS_RENAL'].fillna(0).astype(int)
    df_model['IS_CARDIOVASCULAR'] = df_model['IS_CARDIOVASCULAR'].fillna(0).astype(int)
    
    df_model['DS_COR_RISCO'] = df_model['DS_COR_RISCO'].fillna("VERDE")
    df_model['DS_CLASSIF_RISCO'] = df_model['DS_CLASSIF_RISCO'].fillna("POUCO URGENTE")
    df_model['EXAME_HBA1C'] = df_model['EXAME_HBA1C'].fillna(df_model['EXAME_HBA1C'].mean())
    
    # Montando a lista de colunas dinamicamente para incluir todos os remédios mapeados
    model_columns = [
        "ID_ATEND", "ID_PACIEN",
        "NU_IDADE", "IN_SEXO", "NM_MUNIC", "DS_RACA",
        "DS_TIPO_ATEND", "DS_ESPECI", "TEMPO_INTERNACAO_DIAS",
        "DS_COR_RISCO", "DS_CLASSIF_RISCO",
        "EXAME_HBA1C",
        "IS_RENAL", "IS_CARDIOVASCULAR",
        "FL_OBITO"
    ]
    # Injeta todas as colunas de medicamentos (ex: MED_METFORMINA, MED_INSULINA, etc)
    model_columns.extend(list(med_cols.values()))
    
    df_model_clean = df_model[model_columns].copy()
    
    df_model_clean.to_sql("MODEL_DATASET", conn_clean, if_exists="replace", index=False)
    
    print("\n========================================================")
    print("NOVA BASE DE DADOS LIMPA GERADA COM SUCESSO!")
    print("========================================================")
    cursor = conn_clean.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        cols = cursor.fetchall()
        print(f"- {table:<20} : {len(cols)} colunas")
        
    print(f"\nTamanho da tabela MODEL_DATASET consolidada: {df_model_clean.shape[0]} linhas por {df_model_clean.shape[1]} colunas.")
    
    conn_orig.close()
    conn_clean.close()

if __name__ == "__main__":
    create_clean_database()
