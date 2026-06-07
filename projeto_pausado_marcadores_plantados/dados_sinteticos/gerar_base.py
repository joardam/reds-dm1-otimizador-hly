"""
gerar_base.py — Gera a base sintética longitudinal de DM1 com MARCADORES PLANTADOS.

Emite, em dados_sinteticos/saida/:
  - base_bfss.csv            : tabela plana (1 linha por atendimento) -> entrada do BFSS
  - reds_dm1_sintetico.db    : banco RELACIONAL REDS íntegro (FKs, cronologia, faixas válidas)
  - gabarito_marcadores.json : manifesto-máquina do gabarito (relevantes x ruído + parâmetros)
  - pacientes_resumo.csv     : HLY total por paciente (apoio à etapa 2 da política)

Modelo numérico: ver dados_sinteticos/MODELO_NUMERICO.md e simulador_hly/modelo_hly.py.
Uso: python3 dados_sinteticos/gerar_base.py
"""

from __future__ import annotations
import os
import sys
import json
import sqlite3
from datetime import date, timedelta

import numpy as np
import pandas as pd

# torna o pacote simulador_hly importável (raiz do projeto = pai desta pasta)
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)
from simulador_hly import modelo_hly as M  # noqa: E402

SEED = 42
N_PACIENTES = 500
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")

MUNICIPIOS = [  # municípios de PE (equidade do MOFSS; SEM efeito em HLY)
    "Recife", "Jaboatão dos Guararapes", "Olinda", "Caruaru", "Petrolina",
    "Paulista", "Cabo de Santo Agostinho", "Camaragibe", "Garanhuns", "Vitória de Santo Antão",
]
RACAS = ["Branca", "Parda", "Preta", "Amarela", "Indígena"]
SEXOS = ["F", "M"]

# marca de insulina DENTRO de cada nível = ruído (o sinal é o nível, não a marca)
MARCAS_POR_NIVEL = {
    0: ["NPH-Genérico", "NPH-MarcaA", "Regular-MarcaB"],
    1: ["Glargina-MarcaC", "Detemir-MarcaD", "Asparte-MarcaE"],
    2: ["Asparte-Bomba-MarcaF", "Lispro-Bomba-MarcaG"],
    3: ["Asparte-Bomba-MarcaF", "Lispro-Bomba-MarcaG"],
}
# medicamentos prescritos por nível (modalidade + tier) -> vão para PRESCRICAO_MEDICAMENTO
MEDS_POR_NIVEL = {
    0: [("Insulina NPH", "subcutânea"), ("Insulina Regular", "subcutânea")],
    1: [("Insulina Glargina", "subcutânea"), ("Insulina Asparte", "subcutânea")],
    2: [("Insulina Asparte", "bomba (CSII)")],
    3: [("Insulina Asparte", "bomba (CSII)"), ("Sensor CGM", "dispositivo")],
}
# CID-10 das complicações (DM1 = E10.x; cardiovascular = I25.9)
CID = {
    "base":   ("E10.9", "Diabetes mellitus tipo 1 sem complicações"),
    "renal":  ("E10.2", "Diabetes mellitus tipo 1 com complicações renais"),
    "retino": ("E10.3", "Diabetes mellitus tipo 1 com complicações oftálmicas"),
    "neuro":  ("E10.4", "Diabetes mellitus tipo 1 com complicações neurológicas"),
    "cardio": ("I25.9", "Doença isquêmica crônica do coração"),
}

RUIDO_COLS = [f"RUIDO_{i:02d}" for i in range(1, 11)]


# ----------------------------------------------------------------- simulação de 1 paciente
def simular_paciente(pid: int, rng: np.random.Generator) -> tuple[dict, list[dict]]:
    idade0 = int(np.clip(rng.normal(35, 15), 12, 70))
    hba1c = float(np.clip(rng.normal(8.5, 1.5), 5.5, 13.0))
    m3 = float(rng.beta(2, 2))
    nivel = int(rng.choice([0, 1, 2, 3], p=[0.40, 0.30, 0.20, 0.10]))
    dx0 = int(rng.integers(0, max(1, min(idade0 - 5, 20))))  # anos de diagnóstico no baseline
    sexo = rng.choice(SEXOS)
    raca = rng.choice(RACAS)
    munic = rng.choice(MUNICIPIOS)
    frag = float(rng.normal(0, 1))  # fragilidade: desloca os hazards de comorbidade (independe do dano)

    # horizonte: 15-25 anos, sem ultrapassar ~85 anos de idade
    T = int(rng.integers(15, 26))
    T = max(10, min(T, 85 - idade0))

    ano_entrada = int(rng.integers(1995, 2006))
    dt_nasc = date(ano_entrada - idade0, 1, 1) + timedelta(days=int(rng.integers(0, 365)))

    dano = 0.0
    anos_acima_alvo = 0
    renal = cardio = retino = neuro = 0
    visitas = []

    for t in range(T):
        idade = idade0 + t
        dx_anos = dx0 + t
        dano += M.incremento_dano(hba1c)  # acumulador (memória metabólica)

        # onset de comorbidades (uma vez positivas, permanecem) — janelas de latência
        if not retino and dx_anos >= 3 and rng.random() < M.hazard_retinopatia(dano, idade, frag):
            retino = 1
        if not renal and dx_anos >= 5 and rng.random() < M.hazard_renal(dano, idade, frag):
            renal = 1
        if not neuro and dx_anos >= 5 and rng.random() < M.hazard_neuropatia(dano, frag):
            neuro = 1
        if not cardio and idade >= 40 and rng.random() < M.hazard_cardiovascular(dano, idade, frag):
            cardio = 1

        dhly = M.delta_hly(nivel, hba1c, dano, m3, idade, renal, cardio, retino, neuro, rng)

        dt_atend = date(ano_entrada + t, 1, 1) + timedelta(days=int(rng.integers(0, 60)))
        visitas.append({
            "ID_PACIEN": pid, "ANO_SEGUIMENTO": t, "DT_ATENDIMENTO": dt_atend.isoformat(),
            # --- features RELEVANTES (gabarito) ---
            "NU_IDADE": idade, "EXAME_HBA1C": round(hba1c, 2),
            "DANO_ACUMULADO": round(dano, 3), "MARCADOR_RESPOSTA": round(m3, 4),
            "NIVEL_TRATAMENTO": nivel, "IS_RENAL": renal, "IS_CARDIOVASCULAR": cardio,
            "IS_RETINOPATIA": retino, "IS_NEUROPATIA": neuro,
            # --- features IRRELEVANTES (ruído/distrator) ---
            "TEMPO_DIAGNOSTICO": dx_anos, "IN_SEXO": sexo, "DS_RACA": raca, "NM_MUNIC": munic,
            "INSULINA_MARCA": rng.choice(MARCAS_POR_NIVEL[nivel]),
            "PRESSAO_ARTERIAL": round(float(np.clip(rng.normal(125, 15), 90, 200)), 1),
            **{c: round(float(rng.normal(0, 1)), 4) for c in RUIDO_COLS},
            # --- alvo ---
            "DELTA_HLY": round(dhly, 5),
            # apoio à montagem do banco relacional
            "_DT_NASC": dt_nasc.isoformat(), "_SEXO": sexo, "_RACA": raca, "_MUNIC": munic,
        })

        # transição para o próximo período
        anos_acima_alvo = anos_acima_alvo + 1 if hba1c > 8.0 else 0
        nivel = M.regra_escalada(nivel, anos_acima_alvo, rng)
        hba1c = M.proxima_hba1c(hba1c, nivel, m3, rng)

    paciente = {
        "ID_PACIEN": pid, "NM_PACIEN": f"Paciente Sintetico {pid:04d}",
        "DT_NASC": dt_nasc.isoformat(), "NU_IDADE": idade0, "IN_SEXO": sexo,
        "DS_RACA": raca, "NM_MUNIC": munic, "MARCADOR_RESPOSTA": round(m3, 4),
        "CD_CPF": "".join(str(d) for d in rng.integers(0, 10, 11)),
        "DS_CNS": "".join(str(d) for d in rng.integers(0, 10, 15)),
    }
    return paciente, visitas


# ----------------------------------------------------------------- banco relacional REDS
DDL = """
CREATE TABLE SISTEMA_ORIGEM (IN_SISTEM_ORIGEM INTEGER PRIMARY KEY, NOME TEXT NOT NULL);
CREATE TABLE UNIDADE (ID_UNID INTEGER PRIMARY KEY, CD_CNES TEXT UNIQUE NOT NULL,
    NM_UNID TEXT NOT NULL, NM_MUNIC TEXT NOT NULL);
CREATE TABLE PROFISSIONAL (ID_PROFIS INTEGER PRIMARY KEY, NM_PROFIS TEXT NOT NULL,
    CD_CPF TEXT UNIQUE NOT NULL);
CREATE TABLE PACIENTE (
    ID_PACIEN INTEGER PRIMARY KEY, NM_PACIEN TEXT NOT NULL, DT_NASC TEXT NOT NULL,
    CD_CPF TEXT UNIQUE NOT NULL, DS_CNS TEXT UNIQUE NOT NULL, DS_RACA TEXT, NM_MUNIC TEXT NOT NULL,
    NU_IDADE INTEGER, IN_SEXO TEXT, MARCADOR_RESPOSTA REAL);
CREATE TABLE ATENDIMENTO (
    ID_ATEND INTEGER PRIMARY KEY, ID_PACIEN INTEGER NOT NULL, ID_UNID INTEGER NOT NULL,
    DT_MOMENT_INIC TEXT NOT NULL, DT_MOMENT_FIM TEXT NOT NULL, NU_IDADE INTEGER,
    NIVEL_TRATAMENTO INTEGER, TEMPO_DIAGNOSTICO INTEGER, COMPLEMENTAR TEXT,
    FOREIGN KEY (ID_PACIEN) REFERENCES PACIENTE (ID_PACIEN),
    FOREIGN KEY (ID_UNID) REFERENCES UNIDADE (ID_UNID));
CREATE TABLE DIAGNOSTICO (ID_DIAGN INTEGER PRIMARY KEY, CD_DIAG TEXT UNIQUE NOT NULL,
    DS_DIAG TEXT NOT NULL, TP_CD_DIAG TEXT NOT NULL);
CREATE TABLE ATEND_DIAGNOS (
    ID_ATEND_DIAGNOS INTEGER PRIMARY KEY, ID_ATEND INTEGER NOT NULL, ID_DIAGN INTEGER NOT NULL,
    FL_DIAGN_PRINCIPAL TEXT NOT NULL, DT_DIAGN TEXT NOT NULL,
    FOREIGN KEY (ID_ATEND) REFERENCES ATENDIMENTO (ID_ATEND),
    FOREIGN KEY (ID_DIAGN) REFERENCES DIAGNOSTICO (ID_DIAGN));
CREATE TABLE EXAME (
    ID_EXAME INTEGER PRIMARY KEY, ID_ATEND INTEGER NOT NULL, ID_PACIEN INTEGER NOT NULL,
    DT_REALIZACAO TEXT NOT NULL, DS_EXAME TEXT,
    FOREIGN KEY (ID_ATEND) REFERENCES ATENDIMENTO (ID_ATEND),
    FOREIGN KEY (ID_PACIEN) REFERENCES PACIENTE (ID_PACIEN));
CREATE TABLE RES_EXAME (
    ID_RES_EXAME INTEGER PRIMARY KEY, ID_EXAME INTEGER NOT NULL, DT_RES_EXAME TEXT NOT NULL,
    DS_CAMPO TEXT NOT NULL, DS_RESULTADO TEXT NOT NULL,
    FOREIGN KEY (ID_EXAME) REFERENCES EXAME (ID_EXAME));
CREATE TABLE PRESCRICAO_MEDICAMENTO (
    ID_PRESCR_MEDTO INTEGER PRIMARY KEY, ID_ATEND INTEGER NOT NULL, NM_MEDTO TEXT NOT NULL,
    DS_DOSE_MEDTO TEXT, DS_VIA_ADMIN_MEDTO TEXT, DT_INC TEXT NOT NULL,
    FOREIGN KEY (ID_ATEND) REFERENCES ATENDIMENTO (ID_ATEND));
"""


def construir_banco(db_path: str, pacientes: list[dict], visitas: list[dict]):
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.executescript(DDL)

    cur.execute("INSERT INTO SISTEMA_ORIGEM VALUES (1, 'TESTBED_SINTETICO');")
    for i, mun in enumerate(MUNICIPIOS, start=1):
        cur.execute("INSERT INTO UNIDADE VALUES (?,?,?,?)",
                    (i, f"{7000000 + i}", f"Unidade de Saúde {mun}", mun))
    cur.execute("INSERT INTO PROFISSIONAL VALUES (1, 'Equipe Endocrinologia', '00000000001');")

    # catálogo de diagnósticos
    cid_to_id = {}
    for j, (chave, (cd, ds)) in enumerate(CID.items(), start=1):
        cur.execute("INSERT INTO DIAGNOSTICO VALUES (?,?,?,?)", (j, cd, ds, "CID10"))
        cid_to_id[chave] = j

    unid_de_munic = {mun: i for i, mun in enumerate(MUNICIPIOS, start=1)}

    for p in pacientes:
        cur.execute("""INSERT INTO PACIENTE (ID_PACIEN,NM_PACIEN,DT_NASC,CD_CPF,DS_CNS,DS_RACA,
                       NM_MUNIC,NU_IDADE,IN_SEXO,MARCADOR_RESPOSTA) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (p["ID_PACIEN"], p["NM_PACIEN"], p["DT_NASC"], p["CD_CPF"], p["DS_CNS"],
                     p["DS_RACA"], p["NM_MUNIC"], p["NU_IDADE"], p["IN_SEXO"], p["MARCADOR_RESPOSTA"]))

    aid = eid = rid = did = presc = 0
    for v in visitas:
        aid += 1
        munic = v["_MUNIC"]
        # COMPLEMENTAR guarda os marcadores plantados que não têm coluna REDS própria (JSON legítimo)
        compl = json.dumps({
            "DELTA_HLY": v["DELTA_HLY"], "MARCADOR_RESPOSTA": v["MARCADOR_RESPOSTA"],
            "INSULINA_MARCA": v["INSULINA_MARCA"], "PRESSAO_ARTERIAL": v["PRESSAO_ARTERIAL"],
            **{c: v[c] for c in RUIDO_COLS},
        }, ensure_ascii=False)
        cur.execute("""INSERT INTO ATENDIMENTO (ID_ATEND,ID_PACIEN,ID_UNID,DT_MOMENT_INIC,
                       DT_MOMENT_FIM,NU_IDADE,NIVEL_TRATAMENTO,TEMPO_DIAGNOSTICO,COMPLEMENTAR)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (aid, v["ID_PACIEN"], unid_de_munic[munic], v["DT_ATENDIMENTO"],
                     v["DT_ATENDIMENTO"], v["NU_IDADE"], v["NIVEL_TRATAMENTO"],
                     v["TEMPO_DIAGNOSTICO"], compl))

        # diagnóstico base + complicações presentes nesta visita
        did += 1
        cur.execute("INSERT INTO ATEND_DIAGNOS VALUES (?,?,?,?,?)",
                    (did, aid, cid_to_id["base"], "1", v["DT_ATENDIMENTO"]))
        for chave, flag in (("renal", v["IS_RENAL"]), ("retino", v["IS_RETINOPATIA"]),
                            ("neuro", v["IS_NEUROPATIA"]), ("cardio", v["IS_CARDIOVASCULAR"])):
            if flag:
                did += 1
                cur.execute("INSERT INTO ATEND_DIAGNOS VALUES (?,?,?,?,?)",
                            (did, aid, cid_to_id[chave], "0", v["DT_ATENDIMENTO"]))

        # exames: HbA1c (M1) e os marcadores temporais como resultados de exame legítimos
        for campo, valor in (("HbA1c", v["EXAME_HBA1C"]), ("DANO_ACUMULADO", v["DANO_ACUMULADO"])):
            eid += 1
            cur.execute("INSERT INTO EXAME VALUES (?,?,?,?,?)",
                        (eid, aid, v["ID_PACIEN"], v["DT_ATENDIMENTO"], campo))
            rid += 1
            cur.execute("INSERT INTO RES_EXAME VALUES (?,?,?,?,?)",
                        (rid, eid, v["DT_ATENDIMENTO"], campo, str(valor)))

        # prescrição = medicamentos do nível (modalidade + tier)
        for nm, via in MEDS_POR_NIVEL[v["NIVEL_TRATAMENTO"]]:
            presc += 1
            cur.execute("""INSERT INTO PRESCRICAO_MEDICAMENTO (ID_PRESCR_MEDTO,ID_ATEND,NM_MEDTO,
                           DS_DOSE_MEDTO,DS_VIA_ADMIN_MEDTO,DT_INC) VALUES (?,?,?,?,?,?)""",
                        (presc, aid, nm, "dose padrão", via, v["DT_ATENDIMENTO"]))

    conn.commit()
    conn.close()


# ----------------------------------------------------------------- gabarito (manifesto-máquina)
def escrever_gabarito(path: str):
    gabarito = {
        "alvo_regressao": "DELTA_HLY",
        "relevantes": ["NU_IDADE", "EXAME_HBA1C", "DANO_ACUMULADO", "MARCADOR_RESPOSTA",
                       "NIVEL_TRATAMENTO", "IS_RENAL", "IS_CARDIOVASCULAR", "IS_RETINOPATIA",
                       "IS_NEUROPATIA"],
        "irrelevantes": ["TEMPO_DIAGNOSTICO", "IN_SEXO", "DS_RACA", "NM_MUNIC", "INSULINA_MARCA",
                         "PRESSAO_ARTERIAL", *RUIDO_COLS],
        "notas": {
            "TEMPO_DIAGNOSTICO": "distrator CORRELACIONADO (o driver causal é DANO_ACUMULADO)",
            "NM_MUNIC": "dimensão de equidade do MOFSS; NÃO preditor de HLY",
            "INSULINA_MARCA": "marca dentro do mesmo nível = ruído (sinal é o NIVEL_TRATAMENTO)",
        },
        "parametros": {
            "ALVO_HBA1C": M.ALVO_HBA1C, "POTENCIA_TRATAMENTO": M.POTENCIA_TRATAMENTO,
            "PISO_HBA1C": M.PISO_HBA1C, "W_M1": M.W_M1, "W_M3": M.W_M3, "DANO_K": M.DANO_K,
            "RUIDO_DHLY": M.RUIDO_DHLY,
        },
        "seed": SEED, "n_pacientes": N_PACIENTES,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(gabarito, f, ensure_ascii=False, indent=2)


# ----------------------------------------------------------------- main
def main():
    os.makedirs(SAIDA, exist_ok=True)
    rng = np.random.default_rng(SEED)

    pacientes, todas_visitas = [], []
    for pid in range(1, N_PACIENTES + 1):
        p, vis = simular_paciente(pid, rng)
        pacientes.append(p)
        todas_visitas.extend(vis)

    df = pd.DataFrame(todas_visitas)
    df.insert(1, "ID_ATEND", range(1, len(df) + 1))

    # tabela plana do BFSS (sem as colunas auxiliares "_*")
    cols_bfss = [c for c in df.columns if not c.startswith("_")]
    df_bfss = df[cols_bfss]
    df_bfss.to_csv(os.path.join(SAIDA, "base_bfss.csv"), index=False)

    # resumo por paciente (apoio à etapa 2 — política HLY x Custo x Equidade)
    resumo = (df.groupby("ID_PACIEN")
              .agg(NU_IDADE_BASELINE=("NU_IDADE", "min"), IN_SEXO=("IN_SEXO", "first"),
                   DS_RACA=("DS_RACA", "first"), NM_MUNIC=("NM_MUNIC", "first"),
                   MARCADOR_RESPOSTA=("MARCADOR_RESPOSTA", "first"), N_VISITAS=("ID_ATEND", "count"),
                   HLY_TOTAL=("DELTA_HLY", "sum"), HBA1C_MEDIA=("EXAME_HBA1C", "mean"),
                   DANO_FINAL=("DANO_ACUMULADO", "max"), NIVEL_FINAL=("NIVEL_TRATAMENTO", "max"))
              .round(3).reset_index())
    resumo.to_csv(os.path.join(SAIDA, "pacientes_resumo.csv"), index=False)

    construir_banco(os.path.join(SAIDA, "reds_dm1_sintetico.db"), pacientes, todas_visitas)
    escrever_gabarito(os.path.join(SAIDA, "gabarito_marcadores.json"))

    print(f"[gerar_base] {len(pacientes)} pacientes | {len(df)} atendimentos (linhas BFSS)")
    print(f"[gerar_base] HLY total medio/paciente: {resumo['HLY_TOTAL'].mean():.2f} "
          f"(min {resumo['HLY_TOTAL'].min():.2f} / max {resumo['HLY_TOTAL'].max():.2f})")
    print(f"[gerar_base] HbA1c media global: {df['EXAME_HBA1C'].mean():.2f}% "
          f"[{df['EXAME_HBA1C'].min():.1f}–{df['EXAME_HBA1C'].max():.1f}]")
    print(f"[gerar_base] prevalencia final de comorbidades (ultima visita):")
    ult = df.sort_values("ANO_SEGUIMENTO").groupby("ID_PACIEN").tail(1)
    for c in ["IS_RENAL", "IS_CARDIOVASCULAR", "IS_RETINOPATIA", "IS_NEUROPATIA"]:
        print(f"            {c:18}: {100 * ult[c].mean():.1f}%")
    print(f"[gerar_base] artefatos em: {SAIDA}")


if __name__ == "__main__":
    main()
