#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Meta-Otimizacao: FSS encontra os hiperparametros otimos do PSO.

O PSO interno otimiza os PESOS da regressao logistica (classificador de
diabeticos "ideais"). O FSS externo otimiza os HIPERPARAMETROS do PSO
(w_in, c1, c2, LAMBDA) maximizando AUC.

Estrutura de dois niveis:
  FSS (meta-nivel: 15 peixes x 30 iteracoes)
    --> cada peixe = [w_in, c1, c2, lam]
          fitness = AUC media de CV-3 do PSO interno
                    --> PSO interno leve (15 part x 80 iter)
                          --> pesos da regressao logistica (26 features)

Reutiliza a mesma base de dados e pre-processamento do pso_diabetes.py.
As funcoes de Wellness e Fitness sao identicas ao pso_diabetes.py.
"""

import os
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split, StratifiedKFold

RNG = np.random.default_rng(42)

# --- Caminho da base de dados (pasta data/ esta um nivel acima) ---
_DIR = os.path.dirname(os.path.abspath(__file__))
CSV  = os.path.join(_DIR, '..', 'data', 'Dataset for diabetes research.csv')

# --- Mesmas listas do pso_diabetes.py (nao podem ser preditoras) ---
LABEL_COLS    = ["Age", "HbA1c", "WHO1999hbp", "TGdis", "DysHDLIDFNCEP"]
PROXY_EXCLUDE = ["HPLC", "GA", "FPG", "PG2h", "GLU", "A1cover6575", "PGclass3", "PGclass6",
                 "Bpsys", "Bpdia", "BP13085", "Hyper16", "Hyper13", "WHO1999hbp",
                 "CHOL", "TG", "HDL", "LDL", "JCDHDLdis", "DM", "DMnew3class"]
CANDIDATAS    = ["BMI", "waist1", "Waist2", "hip", "WHR", "Fat", "HR",
                 "FINS", "FCP", "INS2h", "CP2h", "HomaIR", "ISIGutt",
                 "ALT", "AST", "GGT", "ALP", "BUN", "SCRE", "TP", "ALB",
                 "Gender", "Smoking", "FatherDM", "MotherDM", "DMfamilyHistory"]

# -- Espaco de busca do FSS (hiperparametros do PSO) -------------------------
HP_NAMES = ['w_in', 'c1',  'c2',  'lam'  ]
HP_LO    = np.array([0.30,  0.50,  0.50,  0.001])
HP_HI    = np.array([0.95,  2.50,  2.50,  0.500])
HP_PAD   = np.array([0.70,  1.50,  1.50,  0.050])   # valores empiricos do pso_diabetes.py

# -- Configuracao do PSO interno (leve) --------------------------------------
PSO_N_PART = 15
PSO_N_ITER = 80

# -- Configuracao do FSS externo (meta) --------------------------------------
FSS_N_FISH = 15
FSS_N_ITER = 30
FSS_W_MIN  = 1.0
FSS_W_MAX  = 5000.0

# -- Validacao cruzada --------------------------------------------------------
CV_FOLDS = 3


# ============================================================================
# Pipeline de dados  (identica ao pso_diabetes.py — Wellness nao alterado)
# ============================================================================

def carregar_diabeticos():
    df = pd.read_csv(CSV, encoding="latin-1", low_memory=False)
    df = df[pd.to_numeric(df["DM"], errors="coerce") == 1].copy()
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    print(f"[dados] diabeticos (DM==1): {len(df)}")
    return df


def zscore(s):
    s = s.astype(float)
    return (s - s.mean()) / (s.std(ddof=0) + 1e-9)


def construir_rotulo(df):
    """Wellness identico ao pso_diabetes.py: z(idade) - z(HbA1c) - z(comorbidades)."""
    idade    = df["Age"]
    hba1c    = df["HbA1c"].fillna(df["HbA1c"].median())
    htn      = (df["WHO1999hbp"] == 1).astype(float)
    dislip   = ((df["TGdis"] == 1) | (df["DysHDLIDFNCEP"] == 1)).astype(float)
    n_comorb = htn + dislip
    wellness = zscore(idade) - zscore(hba1c) - zscore(n_comorb)
    corte    = wellness.quantile(2 / 3)
    y        = (wellness >= corte).astype(int).values
    print(f"[rotulo] ideais (1): {y.sum()} | demais (0): {len(y) - y.sum()}")
    return y


def selecionar_preditoras(df):
    cols = [c for c in CANDIDATAS
            if c in df.columns and c not in LABEL_COLS and c not in PROXY_EXCLUDE]
    cols = [c for c in cols if df[c].isna().mean() < 0.25]
    X    = df[cols].copy().fillna(df[cols].median())
    Xz   = (X - X.mean()) / (X.std(ddof=0) + 1e-9)
    print(f"[preditoras] {len(cols)} usadas: {cols}")
    return Xz.values, cols


# ============================================================================
# PSO interno  (leve — otimiza pesos da logistica)
# ============================================================================

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def auc_pesos(w, X, y):
    return roc_auc_score(y, sigmoid(X @ w[:-1] + w[-1]))


def fitness_pso(w, X, y, lam):
    """Fitness identico ao pso_diabetes.py — lam e argumento em vez de global LAMBDA."""
    p       = np.clip(sigmoid(X @ w[:-1] + w[-1]), 1e-9, 1 - 1e-9)
    logloss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return -(logloss + lam * np.sum(w[:-1] ** 2))


def pso_interno(X, y, w_in, c1, c2, lam, rng=None):
    """PSO leve — mesma logica do pso_diabetes.py, chamado pelo fitness do FSS."""
    if rng is None:
        rng = RNG
    D          = X.shape[1] + 1
    lo, hi     = -4.0, 4.0
    pos        = rng.uniform(lo, hi, (PSO_N_PART, D))
    vel        = rng.uniform(-1, 1,  (PSO_N_PART, D))
    pbest      = pos.copy()
    pbest_fit  = np.array([fitness_pso(p, X, y, lam) for p in pos])
    g          = int(pbest_fit.argmax())
    gbest      = pbest[g].copy()
    gbest_fit  = pbest_fit[g]

    for _ in range(PSO_N_ITER):
        r1, r2 = rng.random((PSO_N_PART, D)), rng.random((PSO_N_PART, D))
        vel    = w_in * vel + c1 * r1 * (pbest - pos) + c2 * r2 * (gbest - pos)
        pos    = np.clip(pos + vel, lo, hi)
        fit    = np.array([fitness_pso(p, X, y, lam) for p in pos])
        melh   = fit > pbest_fit
        pbest[melh]     = pos[melh]
        pbest_fit[melh] = fit[melh]
        if pbest_fit.max() > gbest_fit:
            g         = int(pbest_fit.argmax())
            gbest     = pbest[g].copy()
            gbest_fit = pbest_fit[g]
    return gbest


# ============================================================================
# Fitness do FSS  (CV-3 sobre o PSO interno)
# ============================================================================

def avaliar_hp(hp, Xtr, ytr):
    """
    Avalia um vetor de hiperparametros [w_in, c1, c2, lam] via CV-3.
    Retorna AUC media no conjunto de validacao — quanto maior, melhor.
    Usa apenas o conjunto de treino (sem tocar no teste) — evita data leakage.
    """
    w_in = float(np.clip(hp[0], HP_LO[0], HP_HI[0]))
    c1   = float(np.clip(hp[1], HP_LO[1], HP_HI[1]))
    c2   = float(np.clip(hp[2], HP_LO[2], HP_HI[2]))
    lam  = float(np.clip(hp[3], HP_LO[3], HP_HI[3]))

    skf  = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=7)
    aucs = []
    for tr_idx, val_idx in skf.split(Xtr, ytr):
        w_otimo = pso_interno(Xtr[tr_idx], ytr[tr_idx], w_in, c1, c2, lam)
        aucs.append(auc_pesos(w_otimo, Xtr[val_idx], ytr[val_idx]))
    return float(np.mean(aucs))


# ============================================================================
# Meta-FSS  (otimiza hiperparametros do PSO)
# ============================================================================

def meta_fss(Xtr, ytr):
    """
    FSS que busca os melhores hiperparametros do PSO interno.

    Cada 'peixe' e um vetor 4D [w_in, c1, c2, lam].
    O peso do peixe cresce quando ele encontra posicoes com maior AUC.
    Os tres movimentos (individual, instintivo, volitivo) equilibram
    exploracao e explotacao no espaco de hiperparametros.

    Retorna:
        gbest_pos  -- vetor hp otimo [w_in, c1, c2, lam]
        hist       -- lista de AUC do gbest por iteracao
    """
    D    = len(HP_LO)
    span = HP_HI - HP_LO

    # -- Inicializacao --------------------------------------------------------
    pos = RNG.uniform(HP_LO, HP_HI, (FSS_N_FISH, D))
    w_f = np.full(FSS_N_FISH, (FSS_W_MIN + FSS_W_MAX) / 2.0)
    fit = np.array([avaliar_hp(p, Xtr, ytr) for p in pos])

    gbest_idx = int(fit.argmax())
    gbest_fit = fit[gbest_idx]
    gbest_pos = pos[gbest_idx].copy()
    W_ant     = w_f.sum()
    hist      = [gbest_fit]

    # Passos decaem linearmente ate 10% do valor inicial
    step_ind_init = span * 0.10
    step_vol_init = span * 0.01

    print(f"   [meta-FSS] it=  0 | AUC_gbest={gbest_fit:.4f} | "
          f"w_in={gbest_pos[0]:.3f} c1={gbest_pos[1]:.3f} "
          f"c2={gbest_pos[2]:.3f} lam={gbest_pos[3]:.4f}")

    for it in range(1, FSS_N_ITER + 1):
        decay    = max(1.0 - it / FSS_N_ITER, 0.10)
        step_ind = step_ind_init * decay
        step_vol = step_vol_init * decay

        # -- 1. Movimento individual ------------------------------------------
        delta_pos = RNG.uniform(-step_ind, step_ind, (FSS_N_FISH, D))
        cand      = np.clip(pos + delta_pos, HP_LO, HP_HI)
        fit_cand  = np.array([avaliar_hp(c, Xtr, ytr) for c in cand])
        delta_fit = fit_cand - fit

        melh             = delta_fit > 0
        pos[melh]        = cand[melh]
        fit[melh]        = fit_cand[melh]
        delta_pos[~melh] = 0.0   # peixe que nao melhorou nao contribui ao instintivo

        # Atualizar pesos dos peixes
        max_dfit = np.abs(delta_fit).max() + 1e-12
        w_f     += delta_fit / max_dfit
        w_f      = np.clip(w_f, FSS_W_MIN, FSS_W_MAX)

        # -- 2. Movimento coletivo instintivo ---------------------------------
        dfit_pos  = np.where(delta_fit > 0, delta_fit, 0.0)
        soma_dfit = dfit_pos.sum()
        if soma_dfit > 1e-12:
            I   = (delta_pos * dfit_pos[:, None]).sum(axis=0) / soma_dfit
            pos = np.clip(pos + I, HP_LO, HP_HI)

        # -- 3. Atualizar gbest -----------------------------------------------
        best_i = int(fit.argmax())
        if fit[best_i] > gbest_fit:
            gbest_fit = fit[best_i]
            gbest_pos = pos[best_i].copy()

        # -- 4. Movimento coletivo volitivo -----------------------------------
        W_atual  = w_f.sum()
        bary     = (pos * w_f[:, None]).sum(axis=0) / W_atual
        direcao  = pos - bary
        norma    = np.linalg.norm(direcao, axis=1, keepdims=True) + 1e-12

        if W_atual > W_ant:       # cardume ganhou peso -> comprimir (explotacao)
            pos = np.clip(pos - step_vol * (direcao / norma) * span, HP_LO, HP_HI)
        else:                     # cardume perdeu peso  -> dilatar  (exploracao)
            pos = np.clip(pos + step_vol * (direcao / norma) * span, HP_LO, HP_HI)
        W_ant = W_atual

        hist.append(gbest_fit)
        if it % 5 == 0 or it == FSS_N_ITER:
            print(f"   [meta-FSS] it={it:3d} | AUC_gbest={gbest_fit:.4f} | "
                  f"w_in={gbest_pos[0]:.3f} c1={gbest_pos[1]:.3f} "
                  f"c2={gbest_pos[2]:.3f} lam={gbest_pos[3]:.4f}")

    return gbest_pos, hist


# ============================================================================
# PSO completo  (para comparacao final: padrao vs. meta-otimizado)
# ============================================================================

def pso_completo(X, y, w_in=0.7, c1=1.5, c2=1.5, lam=0.05,
                 n_part=40, n_iter=300):
    """PSO completo — mesma logica do pso_diabetes.py, com parametros configuráveis."""
    D          = X.shape[1] + 1
    lo, hi     = -4.0, 4.0
    pos        = RNG.uniform(lo, hi, (n_part, D))
    vel        = RNG.uniform(-1, 1,  (n_part, D))
    pbest      = pos.copy()
    pbest_fit  = np.array([fitness_pso(p, X, y, lam) for p in pos])
    g          = int(pbest_fit.argmax())
    gbest      = pbest[g].copy()
    gbest_fit  = pbest_fit[g]
    hist       = []

    for it in range(n_iter):
        r1, r2 = RNG.random((n_part, D)), RNG.random((n_part, D))
        vel    = w_in * vel + c1 * r1 * (pbest - pos) + c2 * r2 * (gbest - pos)
        pos    = np.clip(pos + vel, lo, hi)
        fit    = np.array([fitness_pso(p, X, y, lam) for p in pos])
        melh   = fit > pbest_fit
        pbest[melh]     = pos[melh]
        pbest_fit[melh] = fit[melh]
        if pbest_fit.max() > gbest_fit:
            g         = int(pbest_fit.argmax())
            gbest     = pbest[g].copy()
            gbest_fit = pbest_fit[g]
        hist.append(auc_pesos(gbest, X, y))
        if (it + 1) % 75 == 0:
            print(f"   PSO iter {it+1:3d} | AUC(treino)={hist[-1]:.4f}")
    return gbest, hist


# ============================================================================
# main
# ============================================================================

def main():
    df = carregar_diabeticos()
    y  = construir_rotulo(df)
    X, cols = selecionar_preditoras(df)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    # -- 1. Meta-FSS: encontrar hiperparametros otimos -----------------------
    print("\n" + "=" * 62)
    print("=== Meta-FSS: buscando hiperparametros otimos do PSO ===")
    print("=" * 62)
    print(f"   Peixes: {FSS_N_FISH} | Iteracoes FSS: {FSS_N_ITER} | CV: {CV_FOLDS}-fold")
    print(f"   PSO interno: {PSO_N_PART} part x {PSO_N_ITER} iter por avaliacao\n")
    hp_otimo, hist_fss = meta_fss(Xtr, ytr)
    w_in_opt, c1_opt, c2_opt, lam_opt = hp_otimo

    print(f"\n[meta-FSS] Hiperparametros encontrados:")
    for nome, val, pad in zip(HP_NAMES, hp_otimo, HP_PAD):
        delta = "(acima)" if val > pad else ("(abaixo)" if val < pad else "(igual)")
        print(f"   {nome:6s}: {val:.4f}  (padrao empirico: {pad:.4f})  {delta}")

    # -- 2. PSO meta-otimizado (treino completo com hp otimo) ----------------
    print("\n" + "=" * 62)
    print("=== PSO meta-otimizado (hiperparametros do FSS) ===")
    print("=" * 62)
    w_meta, hist_meta = pso_completo(Xtr, ytr,
                                     w_in=w_in_opt, c1=c1_opt,
                                     c2=c2_opt,     lam=lam_opt)
    auc_meta_tr = auc_pesos(w_meta, Xtr, ytr)
    auc_meta_te = auc_pesos(w_meta, Xte, yte)
    print(f"[PSO meta ] AUC treino={auc_meta_tr:.4f} | AUC teste={auc_meta_te:.4f}")

    # -- 3. PSO padrao (baseline empirico) -----------------------------------
    print("\n" + "=" * 62)
    print("=== PSO padrao (baseline — parametros empiricos originais) ===")
    print("=" * 62)
    w_pad, hist_pad = pso_completo(Xtr, ytr)
    auc_pad_tr = auc_pesos(w_pad, Xtr, ytr)
    auc_pad_te = auc_pesos(w_pad, Xte, yte)
    print(f"[PSO padrao] AUC treino={auc_pad_tr:.4f} | AUC teste={auc_pad_te:.4f}")

    # -- 4. Similaridade de direcao dos pesos --------------------------------
    cos = float(np.dot(w_meta[:-1], w_pad[:-1]) /
                (np.linalg.norm(w_meta[:-1]) * np.linalg.norm(w_pad[:-1]) + 1e-12))
    print(f"\n[validacao] cosseno pesos PSO-meta x PSO-padrao: {cos:.3f}")
    print(f"            (proximo de 1.0 -> ambos convergem para a mesma direcao)")

    salvar_saidas(hist_fss, hist_meta, hist_pad, hp_otimo, cols, w_meta, w_pad,
                  dict(auc_meta_tr=auc_meta_tr, auc_meta_te=auc_meta_te,
                       auc_pad_tr=auc_pad_tr,   auc_pad_te=auc_pad_te, cos=cos))


# ============================================================================
# Saidas
# ============================================================================

def salvar_saidas(hist_fss, hist_meta, hist_pad, hp_otimo, cols, w_meta, w_pad, met):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = os.path.dirname(os.path.abspath(__file__))

    # -- Figura 1 — convergencia do meta-FSS ---------------------------------
    plt.figure(figsize=(7, 4))
    plt.plot(range(len(hist_fss)), hist_fss, lw=2, color="#2563eb", label="meta-FSS (gbest)")
    plt.axhline(met['auc_pad_te'], color="#9aa4b2", lw=1.2, ls="--",
                label=f"PSO padrao AUC teste={met['auc_pad_te']:.3f}")
    plt.xlabel("Iteracao do meta-FSS")
    plt.ylabel("Melhor AUC (CV-3 no treino)")
    plt.title("Convergencia do meta-FSS\n(cada ponto = melhor hp encontrado ate ali)")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(out, "resultados_metafss_convergencia.png"), dpi=130)
    plt.close()

    # -- Figura 2 — PSO padrao x PSO meta-otimizado --------------------------
    plt.figure(figsize=(7, 4))
    plt.plot(range(1, len(hist_pad) + 1),  hist_pad,  lw=2,
             label=f"PSO padrao (empirico) AUC teste={met['auc_pad_te']:.3f}",
             color="#9aa4b2")
    plt.plot(range(1, len(hist_meta) + 1), hist_meta, lw=2,
             label=f"PSO meta-otimizado (FSS) AUC teste={met['auc_meta_te']:.3f}",
             color="#2563eb")
    plt.xlabel("Iteracao do PSO"); plt.ylabel("AUC (treino — gbest)")
    plt.title("Convergencia: PSO padrao x PSO meta-otimizado pelo FSS")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(os.path.join(out, "resultados_comparacao_convergencia.png"), dpi=130)
    plt.close()

    # -- Figura 3 — importancia das features (pesos PSO meta, top 14) --------
    pesos = w_meta[:-1]
    ordem = np.argsort(-np.abs(pesos))
    top   = [(cols[i], float(pesos[i])) for i in ordem[:14]][::-1]
    nomes = [t[0] for t in top]
    vals  = [t[1] for t in top]
    cores = ["#2e7d32" if v > 0 else "#c62828" for v in vals]
    plt.figure(figsize=(7, 6))
    plt.barh(nomes, vals, color=cores)
    plt.axvline(0, color="k", lw=.8)
    plt.xlabel("Peso (verde=+ ideal / vermelho=- ideal)")
    plt.title("Caracteristicas do individuo ideal\n(PSO com hp otimizados pelo FSS)")
    plt.tight_layout()
    plt.savefig(os.path.join(out, "resultados_importancia_meta.png"), dpi=130)
    plt.close()

    # -- RESULTADOS_META.md --------------------------------------------------
    md_path = os.path.join(out, "RESULTADOS_META.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Resultados — Meta-Otimizacao: FSS -> PSO -> Logistica\n\n")
        f.write("## Configuracao do experimento\n\n")
        f.write(f"- **meta-FSS:** {FSS_N_FISH} peixes x {FSS_N_ITER} iteracoes\n")
        f.write(f"- **PSO interno:** {PSO_N_PART} particulas x {PSO_N_ITER} iteracoes\n")
        f.write(f"- **Avaliacao:** CV-{CV_FOLDS} fold no conjunto de treino\n\n")

        f.write("## Hiperparametros encontrados pelo meta-FSS\n\n")
        f.write("| hiperparametro | valor (FSS) | valor padrao | variacao |\n")
        f.write("|---|---:|---:|---:|\n")
        for nome, val, pad in zip(HP_NAMES, hp_otimo, HP_PAD):
            delta = f"{val - pad:+.4f}"
            f.write(f"| {nome} | {val:.4f} | {pad:.4f} | {delta} |\n")

        f.write("\n## Comparacao de AUC\n\n")
        f.write("| configuracao | AUC treino | AUC teste |\n|---|---:|---:|\n")
        f.write(f"| PSO meta-otimizado (FSS) | {met['auc_meta_tr']:.4f} | {met['auc_meta_te']:.4f} |\n")
        f.write(f"| PSO padrao (empirico)    | {met['auc_pad_tr']:.4f} | {met['auc_pad_te']:.4f} |\n")

        f.write("\n## Validacao\n\n")
        f.write(f"- **Cosseno pesos PSO-meta x PSO-padrao:** {met['cos']:.3f}\n")
        f.write(f"  (proximo de 1.0 -> ambos convergem na mesma direcao)\n\n")

        f.write("## Interpretacao\n\n")
        if met['auc_meta_te'] > met['auc_pad_te'] + 0.005:
            f.write("O meta-FSS encontrou hiperparametros que melhoraram a AUC de teste.\n")
        else:
            f.write("A AUC de teste permaneceu proxima entre as configuracoes. Isso indica que\n")
            f.write("os parametros empiricos originais ja eram proximos do otimo para este\n")
            f.write("conjunto de dados — resultado igualmente valido, pois confirma a robustez\n")
            f.write("do PSO original e demonstra o funcionamento da meta-otimizacao.\n")

        f.write("\n## Saidas geradas\n\n")
        f.write("- `resultados_metafss_convergencia.png` — convergencia do meta-FSS\n")
        f.write("- `resultados_comparacao_convergencia.png` — PSO padrao x PSO meta-otimizado\n")
        f.write("- `resultados_importancia_meta.png` — importancia das features (PSO meta)\n")

    print(f"\n[saidas] {os.path.join(out, 'resultados_metafss_convergencia.png')}")
    print(f"         {os.path.join(out, 'resultados_comparacao_convergencia.png')}")
    print(f"         {os.path.join(out, 'resultados_importancia_meta.png')}")
    print(f"         {md_path}")


# ============================================================================

if __name__ == "__main__":
    main()
