"""
Pré-processamento da base sintética para o BFSS.

Esta parte NÃO existe no código da colega (a base dela era 100% numérica) — é
exatamente o que "faltava conectar" à nossa base. Responsabilidades:

  - definir as variáveis CANDIDATAS a partir do gabarito (relevantes + irrelevantes),
    garantindo alinhamento 1-para-1 entre bits do BFSS e a verdade-base;
  - descartar colunas administrativas (IDs, data, ano de seguimento, alvo);
  - codificar as colunas de texto em UM inteiro por coluna (label encoding), para
    preservar o mapeamento "1 bit = 1 variável = 1 entrada do gabarito" — one-hot
    quebraria essa correspondência e a métrica de precisão/recall;
  - padronizar (StandardScaler) ajustado SÓ no treino, indispensável p/ o KNN
    (distância euclidiana é sensível à escala — algo ausente no código original);
  - separar treino/teste por PACIENTE (GroupShuffleSplit) para evitar vazamento
    de um mesmo paciente entre treino e teste (a base é longitudinal).
"""

import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupShuffleSplit

ALVO = "DELTA_HLY"
COLUNA_GRUPO = "ID_PACIEN"
COLUNAS_TEXTO = ["IN_SEXO", "DS_RACA", "NM_MUNIC", "INSULINA_MARCA"]


def carregar_gabarito(caminho_gabarito):
    with open(caminho_gabarito, "r", encoding="utf-8") as fh:
        return json.load(fh)


def preparar_dados(caminho_csv, caminho_gabarito, test_size=0.3, seed=42,
                   max_treino=None, max_teste=None):
    """Carrega a base, monta as candidatas e devolve os conjuntos para o BFSS.

    OTIMIZAÇÃO #2 (subamostragem): se `max_treino`/`max_teste` forem definidos,
    sorteia (com a `seed`) até esse nº de linhas para o wrapper. Reduz o custo do
    KNN (∝ n_treino × n_teste) sem mudar quais variáveis são candidatas. Use
    `None` (padrão) para o run canônico completo e fiel.

    Retorna um dicionário com tudo o que o otimizador e a auditoria precisam.
    """
    df = pd.read_csv(caminho_csv)
    gabarito = carregar_gabarito(caminho_gabarito)

    # Candidatas = união relevantes + irrelevantes do gabarito (na ordem do gabarito).
    candidatas = list(gabarito["relevantes"]) + list(gabarito["irrelevantes"])

    faltando = [c for c in candidatas if c not in df.columns]
    if faltando:
        raise ValueError(f"Colunas do gabarito ausentes na base: {faltando}")
    if ALVO not in df.columns:
        raise ValueError(f"Alvo '{ALVO}' ausente na base.")

    grupos = df[COLUNA_GRUPO].values
    y = df[ALVO].astype(float).values

    # Codifica texto em inteiro (uma coluna por variável) preservando o mapeamento.
    X_df = df[candidatas].copy()
    mapeamento_categorias = {}
    for col in COLUNAS_TEXTO:
        if col in X_df.columns:
            codes, uniques = pd.factorize(X_df[col])
            X_df[col] = codes
            mapeamento_categorias[col] = list(map(str, uniques))

    X_df = X_df.astype(float)
    if X_df.isna().any().any():
        # Defensivo: imputa mediana se algum NaN aparecer em versões futuras da base.
        X_df = X_df.fillna(X_df.median(numeric_only=True))

    feature_names = list(X_df.columns)
    X = X_df.values

    # Split por paciente (sem vazamento longitudinal).
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    idx_train, idx_test = next(gss.split(X, y, groups=grupos))

    # OTIMIZAÇÃO #2: subamostragem opcional das linhas do wrapper.
    rng = np.random.RandomState(seed)
    if max_treino is not None and len(idx_train) > max_treino:
        idx_train = rng.choice(idx_train, size=max_treino, replace=False)
    if max_teste is not None and len(idx_test) > max_teste:
        idx_test = rng.choice(idx_test, size=max_teste, replace=False)

    # Padronização ajustada apenas no treino.
    scaler = StandardScaler().fit(X[idx_train])
    X_train = scaler.transform(X[idx_train])
    X_test = scaler.transform(X[idx_test])

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y[idx_train],
        "y_test": y[idx_test],
        "feature_names": feature_names,
        "relevantes": list(gabarito["relevantes"]),
        "irrelevantes": list(gabarito["irrelevantes"]),
        "gabarito": gabarito,
        "n_pacientes": int(pd.unique(grupos).size),
        "n_atendimentos": int(len(df)),
        "n_treino": int(len(idx_train)),
        "n_teste": int(len(idx_test)),
        "mapeamento_categorias": mapeamento_categorias,
    }
