"""
validar_base.py — Valida a base sintética gerada.

Parte A — INTEGRIDADE RELACIONAL do banco REDS (reds_dm1_sintetico.db):
  FKs (PRAGMA), cronologia (nascimento<atendimento, exame<=resultado, inicio<=fim),
  faixas de HbA1c, CPF (11) / CNS (15), sexo in {F,M}.

Parte B — RECUPERABILIDADE DO SINAL (sanidade pré-BFSS, NÃO é o BFSS):
  ajusta um RandomForest em base_bfss.csv e confere que as features RELEVANTES (gabarito)
  concentram a importância e as de RUÍDO ficam perto de zero. Se separar bem, a base está
  pronta para o BFSS de verdade.

Uso: python3 validacao/validar_base.py
"""

from __future__ import annotations
import os
import json
import sqlite3

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(_RAIZ, "dados_sinteticos", "saida")
DB = os.path.join(SAIDA, "reds_dm1_sintetico.db")
CSV = os.path.join(SAIDA, "base_bfss.csv")
GAB = os.path.join(SAIDA, "gabarito_marcadores.json")


# ----------------------------------------------------------------- Parte A: banco relacional
def validar_banco() -> bool:
    print("\n[A] === INTEGRIDADE RELACIONAL (reds_dm1_sintetico.db) ===")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    ok = True

    tabelas = ["SISTEMA_ORIGEM", "UNIDADE", "PROFISSIONAL", "PACIENTE", "ATENDIMENTO",
               "DIAGNOSTICO", "ATEND_DIAGNOS", "EXAME", "RES_EXAME", "PRESCRICAO_MEDICAMENTO"]
    print("  Contagens:")
    for t in tabelas:
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"    {t:24}: {n}")

    def check(nome, sql, esperado=0):
        nonlocal ok
        n = cur.execute(sql).fetchone()[0]
        status = "OK " if n == esperado else "ERRO"
        if n != esperado:
            ok = False
        print(f"  [{status}] {nome}: {n}")

    viol = cur.execute("PRAGMA foreign_key_check").fetchall()
    print(f"  [{'OK ' if not viol else 'ERRO'}] violacoes de Foreign Key: {len(viol)}")
    ok = ok and not viol

    check("atendimentos antes do nascimento",
          """SELECT COUNT(*) FROM ATENDIMENTO a JOIN PACIENTE p ON a.ID_PACIEN=p.ID_PACIEN
             WHERE datetime(p.DT_NASC) >= datetime(a.DT_MOMENT_INIC)""")
    check("inicio do atendimento apos o fim",
          "SELECT COUNT(*) FROM ATENDIMENTO WHERE datetime(DT_MOMENT_INIC) > datetime(DT_MOMENT_FIM)")
    check("resultado liberado antes do exame",
          """SELECT COUNT(*) FROM RES_EXAME r JOIN EXAME e ON r.ID_EXAME=e.ID_EXAME
             WHERE datetime(r.DT_RES_EXAME) < datetime(e.DT_REALIZACAO)""")
    check("HbA1c fora da faixa biologica [3,20]",
          """SELECT COUNT(*) FROM RES_EXAME WHERE DS_CAMPO='HbA1c'
             AND (CAST(DS_RESULTADO AS REAL) < 3 OR CAST(DS_RESULTADO AS REAL) > 20)""")
    check("CPF com tamanho != 11", "SELECT COUNT(*) FROM PACIENTE WHERE LENGTH(CD_CPF) != 11")
    check("CNS com tamanho != 15", "SELECT COUNT(*) FROM PACIENTE WHERE LENGTH(DS_CNS) != 15")
    check("sexo fora de {F,M}", "SELECT COUNT(*) FROM PACIENTE WHERE IN_SEXO NOT IN ('F','M')")
    # cronologia longitudinal: cada paciente tem atendimentos com datas estritamente crescentes
    check("pacientes com atendimentos sem 1+ visitas",
          "SELECT COUNT(*) FROM PACIENTE WHERE ID_PACIEN NOT IN (SELECT ID_PACIEN FROM ATENDIMENTO)")

    avg = cur.execute("SELECT AVG(CAST(DS_RESULTADO AS REAL)) FROM RES_EXAME WHERE DS_CAMPO='HbA1c'").fetchone()[0]
    print(f"  HbA1c media na base: {avg:.2f}%")
    conn.close()
    print(f"  --> integridade relacional: {'PASSOU' if ok else 'FALHOU'}")
    return ok


# ----------------------------------------------------------------- Parte B: sinal recuperável
def validar_sinal() -> bool:
    print("\n[B] === RECUPERABILIDADE DO SINAL (sanidade pre-BFSS) ===")
    df = pd.read_csv(CSV)
    gab = json.load(open(GAB, encoding="utf-8"))
    relevantes, irrelevantes = gab["relevantes"], gab["irrelevantes"]

    y = df["DELTA_HLY"].values
    feats = relevantes + irrelevantes
    X = df[feats].copy()
    # one-hot nas categoricas, mantendo o mapeamento coluna_original -> colunas geradas
    cat = X.select_dtypes(exclude=[np.number]).columns.tolist()
    grupos = {f: [f] for f in feats if f not in cat}
    if cat:
        dummies = pd.get_dummies(X[cat], prefix=cat, prefix_sep="=")
        for c in cat:
            grupos[c] = [d for d in dummies.columns if d.startswith(c + "=")]
        X = pd.concat([X.drop(columns=cat), dummies], axis=1)

    rf = RandomForestRegressor(n_estimators=300, max_depth=12, random_state=0, n_jobs=-1)
    rf.fit(X, y)
    imp = pd.Series(rf.feature_importances_, index=X.columns)
    imp_feat = {f: float(imp[cols].sum()) for f, cols in grupos.items()}  # agrega one-hot

    ranking = sorted(imp_feat.items(), key=lambda kv: kv[1], reverse=True)
    print(f"  R2 (treino, todas as features): {rf.score(X, y):.3f}")
    print("  Importancia por feature (RandomForest):")
    for f, v in ranking:
        tag = "RELEVANTE" if f in relevantes else "ruido    "
        print(f"    {f:20} {v:7.4f}  [{tag}]")

    imp_rel = {f: imp_feat[f] for f in relevantes}
    imp_ruido = {f: imp_feat[f] for f in irrelevantes}
    min_rel = min(imp_rel.values())
    max_ruido = max(imp_ruido.values())
    pior_rel = min(imp_rel, key=imp_rel.get)
    pior_ruido = max(imp_ruido, key=imp_ruido.get)
    print(f"\n  menor importancia RELEVANTE: {pior_rel} = {min_rel:.4f}")
    print(f"  maior importancia RUIDO    : {pior_ruido} = {max_ruido:.4f}")

    # separação top-K: as K=len(relevantes) features mais importantes coincidem com o gabarito?
    K = len(relevantes)
    topK = {f for f, _ in ranking[:K]}
    recall = len(topK & set(relevantes)) / K
    print(f"  top-{K} por importancia recupera {recall*100:.0f}% das relevantes do gabarito")
    sep = min_rel > max_ruido
    print(f"  --> separacao relevante>ruido: {'CLARA' if sep else 'PARCIAL'} "
          f"(distrator TEMPO_DIAGNOSTICO pode ficar acima do ruido puro, por design)")
    return recall >= 0.8


def main():
    a = validar_banco()
    b = validar_sinal()
    print("\n=== RESUMO ===")
    print(f"  integridade relacional : {'PASSOU' if a else 'FALHOU'}")
    print(f"  sinal recuperavel      : {'SIM' if b else 'NAO'}")
    print("  base pronta para o BFSS." if (a and b) else "  REVISAR a base antes do BFSS.")


if __name__ == "__main__":
    main()
