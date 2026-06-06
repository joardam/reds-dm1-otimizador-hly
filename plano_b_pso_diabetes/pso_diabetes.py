#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plano B — PSO sobre coorte de diabéticos (bimodal dataset, n=357).

OBJETIVO (Opção B): identificar o "indivíduo ideal" (diabético que envelheceu bem) e descobrir,
via PSO, QUAIS OUTRAS características o distinguem.

Como funciona:
  1) Define o rótulo "ideal" a partir de {idade(+), HbA1c(-), nº de comorbidades(-)} -> terço superior.
  2) O PSO otimiza os PESOS de uma regressão logística que prevê esse rótulo a partir de
     características que NÃO entram no rótulo (antropometria, insulina, HOMA, enzimas, estilo de
     vida, histórico familiar...). Pesos altos = características do indivíduo ideal.
  3) Validação: compara o ótimo do PSO com a logística analítica do sklearn (devem bater).

Honestidade: base é rastreio metabólico adulto (China, 2012); NÃO distingue T1D/T2D -> "diabetes
tipo não especificado". O entregável é o OTIMIZADOR; a base é testbed.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

RNG = np.random.default_rng(42)
CSV = "data/Dataset for diabetes research.csv"

# --- Colunas que FORMAM o rótulo (não podem ser preditoras: seria circular) ---
LABEL_COLS = ["Age", "HbA1c", "WHO1999hbp", "TGdis", "DysHDLIDFNCEP"]
# --- Proxies de glicose/lipídio/PA: também ficam fora dos preditores ---
PROXY_EXCLUDE = ["HPLC", "GA", "FPG", "PG2h", "GLU", "A1cover6575", "PGclass3", "PGclass6",
                 "Bpsys", "Bpdia", "BP13085", "Hyper16", "Hyper13", "WHO1999hbp",
                 "CHOL", "TG", "HDL", "LDL", "JCDHDLdis", "DM", "DMnew3class"]
# --- Candidatas a preditoras (as "outras características" a descobrir) ---
CANDIDATAS = ["BMI", "waist1", "Waist2", "hip", "WHR", "Fat", "HR",
              "FINS", "FCP", "INS2h", "CP2h", "HomaIR", "ISIGutt",
              "ALT", "AST", "GGT", "ALP", "BUN", "SCRE", "TP", "ALB",
              "Gender", "Smoking", "FatherDM", "MotherDM", "DMfamilyHistory"]


def carregar_diabeticos():
    df = pd.read_csv(CSV, encoding="latin-1", low_memory=False)
    df = df[pd.to_numeric(df["DM"], errors="coerce") == 1].copy()
    # tudo numérico; vazios viram NaN
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    print(f"[dados] diabéticos (DM==1): {len(df)}")
    return df


def zscore(s):
    s = s.astype(float)
    return (s - s.mean()) / (s.std(ddof=0) + 1e-9)


def construir_rotulo(df):
    """Rótulo 'ideal' = terço superior de wellness = z(idade) - z(HbA1c) - z(nº comorbidades)."""
    idade = df["Age"]
    hba1c = df["HbA1c"].fillna(df["HbA1c"].median())
    htn = (df["WHO1999hbp"] == 1).astype(float)
    dislip = ((df["TGdis"] == 1) | (df["DysHDLIDFNCEP"] == 1)).astype(float)
    n_comorb = htn + dislip                                   # 0, 1 ou 2
    wellness = zscore(idade) - zscore(hba1c) - zscore(n_comorb)
    corte = wellness.quantile(2 / 3)                          # terço superior = ideal
    y = (wellness >= corte).astype(int).values
    print(f"[rótulo] ideais (1): {y.sum()} | demais (0): {len(y) - y.sum()} "
          f"| comorbidades médias: ideais={n_comorb[y==1].mean():.2f} vs demais={n_comorb[y==0].mean():.2f}")
    print(f"[rótulo] idade média: ideais={idade[y==1].mean():.1f} vs demais={idade[y==0].mean():.1f} "
          f"| HbA1c média: ideais={hba1c[y==1].mean():.2f} vs demais={hba1c[y==0].mean():.2f}")
    return y


def selecionar_preditoras(df):
    cols = [c for c in CANDIDATAS
            if c in df.columns and c not in LABEL_COLS and c not in PROXY_EXCLUDE]
    # mantém só as com < 25% de ausência
    cols = [c for c in cols if df[c].isna().mean() < 0.25]
    print(f"[preditoras] {len(cols)} usadas: {cols}")
    X = df[cols].copy()
    X = X.fillna(X.median())          # imputa mediana
    Xz = (X - X.mean()) / (X.std(ddof=0) + 1e-9)   # padroniza
    return Xz.values, cols


LAMBDA = 0.05   # força da regularização L2 (mantém pesos finitos e interpretáveis)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def auc_pesos(w, X, y):
    p = sigmoid(X @ w[:-1] + w[-1])
    return roc_auc_score(y, p)


def fitness(w, X, y):
    """Maximizar = -(log-loss + L2). É o MESMO objetivo da logística do sklearn -> comparável."""
    p = sigmoid(X @ w[:-1] + w[-1])
    p = np.clip(p, 1e-9, 1 - 1e-9)
    logloss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return -(logloss + LAMBDA * np.sum(w[:-1] ** 2))   # bias não é penalizado


def pso(X, y, n_part=40, n_iter=300):
    """PSO clássico maximizando -(log-loss + L2) da logística (pesos = posição da partícula)."""
    D = X.shape[1] + 1                       # + bias
    lo, hi = -4.0, 4.0
    pos = RNG.uniform(lo, hi, (n_part, D))
    vel = RNG.uniform(-1, 1, (n_part, D))
    pbest = pos.copy()
    pbest_fit = np.array([fitness(p, X, y) for p in pos])
    g = int(pbest_fit.argmax())
    gbest = pbest[g].copy(); gbest_fit = pbest_fit[g]
    w_in, c1, c2 = 0.7, 1.5, 1.5
    hist = []
    for it in range(n_iter):
        r1, r2 = RNG.random((n_part, D)), RNG.random((n_part, D))
        vel = w_in * vel + c1 * r1 * (pbest - pos) + c2 * r2 * (gbest - pos)
        pos = np.clip(pos + vel, lo, hi)
        fit = np.array([fitness(p, X, y) for p in pos])
        melhorou = fit > pbest_fit
        pbest[melhorou] = pos[melhorou]; pbest_fit[melhorou] = fit[melhorou]
        if pbest_fit.max() > gbest_fit:
            g = int(pbest_fit.argmax()); gbest = pbest[g].copy(); gbest_fit = pbest_fit[g]
        hist.append(auc_pesos(gbest, X, y))
        if (it + 1) % 75 == 0:
            print(f"   PSO iter {it+1:3d} | fitness={gbest_fit:.4f} | AUC(treino)={hist[-1]:.4f}")
    return gbest, gbest_fit, hist


def main():
    df = carregar_diabeticos()
    y = construir_rotulo(df)
    X, cols = selecionar_preditoras(df)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    print("\n=== PSO (otimiza pesos da logística) ===")
    w, _, hist = pso(Xtr, ytr)
    auc_tr = auc_pesos(w, Xtr, ytr)
    auc_te = auc_pesos(w, Xte, yte)
    print(f"[PSO] AUC treino={auc_tr:.4f} | AUC teste={auc_te:.4f}")

    print("\n=== Baseline sklearn (logística analítica) — validação do PSO ===")
    C = 0.5 / (len(ytr) * LAMBDA)          # C do sklearn equivalente ao nosso LAMBDA
    lr = LogisticRegression(max_iter=2000, C=C).fit(Xtr, ytr)
    auc_lr = roc_auc_score(yte, lr.predict_proba(Xte)[:, 1])
    w_lr = lr.coef_[0]
    cos = float(np.dot(w[:-1], w_lr) / (np.linalg.norm(w[:-1]) * np.linalg.norm(w_lr) + 1e-12))
    print(f"[sklearn] AUC teste={auc_lr:.4f}")
    print(f"[validação] similaridade (cosseno) dos pesos PSO×sklearn = {cos:.3f}  "
          f"(perto de 1.0 => PSO resolveu a mesma otimização)")

    print("\n=== Características do indivíduo IDEAL (pesos do PSO, ordenados) ===")
    pesos = w[:-1]
    ordem = np.argsort(-np.abs(pesos))
    linhas = []
    for i in ordem:
        sinal = "↑ (mais = mais ideal)" if pesos[i] > 0 else "↓ (menos = mais ideal)"
        print(f"   {cols[i]:18s} peso={pesos[i]:+.3f}  {sinal}")
        linhas.append((cols[i], float(pesos[i])))

    print("\n=== Perfil descritivo: média ideais vs demais (variáveis originais) ===")
    desc = df[cols].copy()
    perfil = []
    for c in cols:
        m1 = desc[c][y == 1].mean(); m0 = desc[c][y == 0].mean()
        print(f"   {c:18s} ideais={m1:8.2f} | demais={m0:8.2f} | dif={m1-m0:+.2f}")
        perfil.append((c, float(m1), float(m0)))

    salvar_saidas(hist, linhas, perfil, dict(auc_tr=auc_tr, auc_te=auc_te, auc_lr=auc_lr,
                  cos=cos, n=len(y), n_ideal=int(y.sum())))


def salvar_saidas(hist, linhas, perfil, met):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Figura 1 — convergência do PSO
    plt.figure(figsize=(7, 4))
    plt.plot(range(1, len(hist) + 1), hist, lw=2)
    plt.xlabel("Iteração"); plt.ylabel("AUC (treino) do melhor (gbest)")
    plt.title("Convergência do PSO"); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig("resultados_convergencia_pso.png", dpi=130); plt.close()

    # Figura 2 — importância das características (pesos), top 14 por |peso|
    top = linhas[:14][::-1]
    nomes = [t[0] for t in top]; vals = [t[1] for t in top]
    cores = ["#2e7d32" if v > 0 else "#c62828" for v in vals]
    plt.figure(figsize=(7, 6))
    plt.barh(nomes, vals, color=cores)
    plt.axvline(0, color="k", lw=.8)
    plt.xlabel("Peso (verde=+ ideal / vermelho=- ideal)")
    plt.title("Características do indivíduo ideal (pesos do PSO)")
    plt.tight_layout(); plt.savefig("resultados_importancia.png", dpi=130); plt.close()

    # Resumo em markdown
    with open("RESULTADOS.md", "w", encoding="utf-8") as f:
        f.write("# Resultados — PSO sobre diabéticos (bimodal, n=357)\n\n")
        f.write(f"- Indivíduos: {met['n']} (ideais={met['n_ideal']}, demais={met['n']-met['n_ideal']})\n")
        f.write(f"- AUC PSO: treino={met['auc_tr']:.3f} | teste={met['auc_te']:.3f}\n")
        f.write(f"- AUC sklearn (baseline): teste={met['auc_lr']:.3f}\n")
        f.write(f"- Validação PSO×sklearn (cosseno dos pesos): {met['cos']:.3f}\n\n")
        f.write("## Características do indivíduo ideal (pesos do PSO)\n\n")
        f.write("| característica | peso | direção |\n|---|---:|---|\n")
        for nome, p in linhas:
            f.write(f"| {nome} | {p:+.3f} | {'mais = ideal' if p>0 else 'menos = ideal'} |\n")
        f.write("\n## Perfil descritivo (média ideais vs demais)\n\n")
        f.write("| variável | ideais | demais | dif |\n|---|---:|---:|---:|\n")
        for c, m1, m0 in perfil:
            f.write(f"| {c} | {m1:.2f} | {m0:.2f} | {m1-m0:+.2f} |\n")
    print("\n[saídas] resultados_convergencia_pso.png, resultados_importancia.png, RESULTADOS.md")


if __name__ == "__main__":
    main()
