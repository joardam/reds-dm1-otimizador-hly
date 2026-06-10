"""
Varredura de hiperparâmetros do BFSS (modo rápido / subamostrado).

Objetivo: o recall já fica em 1.0; queremos empurrar a PRECISÃO (menos falsos
positivos de ruído) sem perder marcadores relevantes. O parâmetro-chave é o
`alpha` da Eq.(10): quanto menor, maior a pressão por parcimônia (subconjuntos
menores -> menos ruído), mas se for baixo demais pode derrubar marcadores fracos.
Também varremos os limiares adaptativos `thres_c`/`thres_v`.

Procedimento:
  1. Grade grossa com seed fixo -> ranqueia por F1 (depois precisão).
  2. Top-3 revalidados em vários seeds -> média ± desvio (estabilidade).

Saídas auditáveis: resultados/tuning.csv e resultados/tuning.md.
Os dados (subamostra) são fixos (seed 42) em toda a grade -> comparação justa;
só o seed do BFSS varia na etapa de estabilidade.
"""

import os
import csv
import statistics as stats

from bfss.preprocessamento import preparar_dados
from bfss.avaliador import AvaliadorWrapper
from bfss.otimizador import run_bfss
from bfss.validacao import validar_selecao
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
CSV = os.path.join(RAIZ, "dados_sinteticos", "saida", "base_bfss.csv")
GAB = os.path.join(RAIZ, "dados_sinteticos", "saida", "gabarito_marcadores.json")
DIR = os.path.join(AQUI, "resultados")

# Grade.
ALPHAS = [0.6, 0.7, 0.8, 0.9]
THRES_C = [0.2, 0.4, 0.6]
THRES_V = [0.2, 0.4]
ITERS_GRADE = 50
SEEDS_ESTAB = [42, 7, 123, 2024]


def avaliar_config(dados, alpha, tc, tv, iters, seed):
    res = run_bfss(dados, num_fishes=30, num_iterations=iters,
                   alpha=alpha, k=5, thres_c=tc, thres_v=tv,
                   seed=seed, verbose=False)
    val = validar_selecao(res.selected_features,
                          dados["relevantes"], dados["irrelevantes"])
    return res, val


def main():
    print("Preparando dados (modo rápido: 2500 treino / 1200 teste)...")
    dados = preparar_dados(CSV, GAB, seed=42, max_treino=2500, max_teste=1200)

    # baseline R² (todas as variáveis)
    av = AvaliadorWrapper(dados["X_train"], dados["X_test"],
                          dados["y_train"], dados["y_test"], alpha=1.0, k=5)
    _, r2_base = av.avaliar(np.ones(len(dados["feature_names"]), dtype=int))
    print(f"R² baseline (todas {len(dados['feature_names'])}): {r2_base:.4f}\n")

    linhas = []
    total = len(ALPHAS) * len(THRES_C) * len(THRES_V)
    i = 0
    print(f"=== Etapa 1: grade grossa ({total} configs, {ITERS_GRADE} iters, seed 42) ===")
    for alpha in ALPHAS:
        for tc in THRES_C:
            for tv in THRES_V:
                i += 1
                res, val = avaliar_config(dados, alpha, tc, tv, ITERS_GRADE, 42)
                linhas.append({
                    "alpha": alpha, "thres_c": tc, "thres_v": tv,
                    "n_sel": res.num_selecionadas,
                    "precisao": round(val.precisao, 3),
                    "recall": round(val.recall, 3),
                    "f1": round(val.f1, 3),
                    "r2": round(res.r2, 4),
                })
                print(f"  [{i:02d}/{total}] alpha={alpha} tc={tc} tv={tv} "
                      f"-> P={val.precisao:.2f} R={val.recall:.2f} "
                      f"F1={val.f1:.2f} n_sel={res.num_selecionadas}")

    # Ranqueia: F1 desc, depois precisão, depois recall, depois menos features.
    linhas.sort(key=lambda d: (d["f1"], d["precisao"], d["recall"], -d["n_sel"]),
                reverse=True)

    print("\n=== Top 8 da grade (ordenado por F1) ===")
    print(f"{'alpha':>5} {'tc':>4} {'tv':>4} {'n_sel':>5} {'P':>5} {'R':>5} {'F1':>5} {'R2':>6}")
    for d in linhas[:8]:
        print(f"{d['alpha']:>5} {d['thres_c']:>4} {d['thres_v']:>4} "
              f"{d['n_sel']:>5} {d['precisao']:>5} {d['recall']:>5} "
              f"{d['f1']:>5} {d['r2']:>6}")

    # Etapa 2: estabilidade dos top-3 em vários seeds.
    print(f"\n=== Etapa 2: estabilidade dos top-3 em seeds {SEEDS_ESTAB} ===")
    estabilidade = []
    for d in linhas[:3]:
        ps, rs, fs, ns = [], [], [], []
        for s in SEEDS_ESTAB:
            res, val = avaliar_config(dados, d["alpha"], d["thres_c"],
                                      d["thres_v"], ITERS_GRADE, s)
            ps.append(val.precisao); rs.append(val.recall)
            fs.append(val.f1); ns.append(res.num_selecionadas)
        reg = {
            "alpha": d["alpha"], "thres_c": d["thres_c"], "thres_v": d["thres_v"],
            "P_med": round(stats.mean(ps), 3), "P_dp": round(stats.pstdev(ps), 3),
            "R_med": round(stats.mean(rs), 3), "R_dp": round(stats.pstdev(rs), 3),
            "F1_med": round(stats.mean(fs), 3), "F1_dp": round(stats.pstdev(fs), 3),
            "n_sel_med": round(stats.mean(ns), 1),
        }
        estabilidade.append(reg)
        print(f"  alpha={reg['alpha']} tc={reg['thres_c']} tv={reg['thres_v']} "
              f"-> P={reg['P_med']}±{reg['P_dp']} "
              f"R={reg['R_med']}±{reg['R_dp']} "
              f"F1={reg['F1_med']}+-{reg['F1_dp']} n_sel~{reg['n_sel_med']}")

    # Persistência.
    os.makedirs(DIR, exist_ok=True)
    with open(os.path.join(DIR, "tuning.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
        w.writeheader(); w.writerows(linhas)

    with open(os.path.join(DIR, "tuning.md"), "w", encoding="utf-8") as fh:
        fh.write("# Tuning BFSS — grade rápida (subamostrada)\n\n")
        fh.write(f"R² baseline (todas as variáveis): {r2_base:.4f}\n\n")
        fh.write("## Grade (ordenada por F1)\n\n")
        fh.write("| alpha | thres_c | thres_v | n_sel | P | R | F1 | R² |\n")
        fh.write("| --: | --: | --: | --: | --: | --: | --: | --: |\n")
        for d in linhas:
            fh.write(f"| {d['alpha']} | {d['thres_c']} | {d['thres_v']} | "
                     f"{d['n_sel']} | {d['precisao']} | {d['recall']} | "
                     f"{d['f1']} | {d['r2']} |\n")
        fh.write("\n## Estabilidade dos top-3 (média ± desvio em "
                 f"{len(SEEDS_ESTAB)} seeds)\n\n")
        fh.write("| alpha | thres_c | thres_v | P | R | F1 | n_sel |\n")
        fh.write("| --: | --: | --: | --: | --: | --: | --: |\n")
        for r in estabilidade:
            fh.write(f"| {r['alpha']} | {r['thres_c']} | {r['thres_v']} | "
                     f"{r['P_med']}±{r['P_dp']} | {r['R_med']}±{r['R_dp']} | "
                     f"{r['F1_med']}±{r['F1_dp']} | {r['n_sel_med']} |\n")

    print(f"\nSalvo: {os.path.relpath(os.path.join(DIR,'tuning.csv'), RAIZ)}")
    print(f"Salvo: {os.path.relpath(os.path.join(DIR,'tuning.md'), RAIZ)}")


if __name__ == "__main__":
    main()
