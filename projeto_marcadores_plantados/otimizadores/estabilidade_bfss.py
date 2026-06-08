"""
Estabilidade das melhores configs do tuning, em vários seeds.

Responde: "o resultado da grade (seed 42) se sustenta, ou foi sorte?"
Avalia duas configs escolhidas da grade:
  - CAMPEA       (melhor F1):        alpha=0.8, thres_c=0.6, thres_v=0.4
  - RECALL_TOTAL (recall=1.0 + menos ruido): alpha=0.9, thres_c=0.6, thres_v=0.2

Para cada config roda N seeds, reporta media +- desvio de P/R/F1/n_sel e a
FREQUENCIA com que cada variavel foi selecionada (auditoria de estabilidade da
selecao). Saida ASCII-safe + resultados/estabilidade.md.
"""

import os
import statistics as stats
from collections import Counter
import numpy as np

from bfss.preprocessamento import preparar_dados
from bfss.otimizador import run_bfss
from bfss.validacao import validar_selecao

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
CSV = os.path.join(RAIZ, "dados_sinteticos", "saida", "base_bfss.csv")
GAB = os.path.join(RAIZ, "dados_sinteticos", "saida", "gabarito_marcadores.json")
DIR = os.path.join(AQUI, "resultados")

SEEDS = [42, 7, 123, 2024]
ITERS = 50
CONFIGS = {
    "CAMPEA (F1)":          dict(alpha=0.8, thres_c=0.6, thres_v=0.4),
    "RECALL_TOTAL":         dict(alpha=0.9, thres_c=0.6, thres_v=0.2),
}


def main():
    print("Preparando dados (subamostra 2500/1200, seed 42)...")
    dados = preparar_dados(CSV, GAB, seed=42, max_treino=2500, max_teste=1200)
    rel = set(dados["relevantes"])

    blocos = []
    for nome, cfg in CONFIGS.items():
        print(f"\n=== {nome}: {cfg} | seeds {SEEDS} ===")
        ps, rs, fs, ns = [], [], [], []
        freq = Counter()
        for s in SEEDS:
            res = run_bfss(dados, num_fishes=30, num_iterations=ITERS,
                           seed=s, verbose=False, **cfg)
            val = validar_selecao(res.selected_features,
                                  dados["relevantes"], dados["irrelevantes"])
            ps.append(val.precisao); rs.append(val.recall)
            fs.append(val.f1); ns.append(res.num_selecionadas)
            freq.update(res.selected_features)
            print(f"  seed {s:>4}: P={val.precisao:.2f} R={val.recall:.2f} "
                  f"F1={val.f1:.2f} n_sel={res.num_selecionadas}")

        resumo = dict(
            nome=nome, cfg=cfg,
            P=(stats.mean(ps), stats.pstdev(ps)),
            R=(stats.mean(rs), stats.pstdev(rs)),
            F1=(stats.mean(fs), stats.pstdev(fs)),
            n=(stats.mean(ns), stats.pstdev(ns)),
            freq=freq,
        )
        blocos.append(resumo)
        print(f"  >> P={resumo['P'][0]:.3f}+-{resumo['P'][1]:.3f} "
              f"R={resumo['R'][0]:.3f}+-{resumo['R'][1]:.3f} "
              f"F1={resumo['F1'][0]:.3f}+-{resumo['F1'][1]:.3f} "
              f"n_sel={resumo['n'][0]:.1f}+-{resumo['n'][1]:.1f}")

    # Persistencia (UTF-8).
    os.makedirs(DIR, exist_ok=True)
    cam = os.path.join(DIR, "estabilidade.md")
    with open(cam, "w", encoding="utf-8") as fh:
        fh.write("# Estabilidade do BFSS (seeds " + str(SEEDS) + ")\n\n")
        fh.write(f"Subamostra 2500/1200, {ITERS} iters, 30 peixes.\n\n")
        fh.write("## Resumo (media +- desvio)\n\n")
        fh.write("| config | alpha | tc | tv | P | R | F1 | n_sel |\n")
        fh.write("| :-- | --: | --: | --: | --: | --: | --: | --: |\n")
        for b in blocos:
            c = b["cfg"]
            fh.write(f"| {b['nome']} | {c['alpha']} | {c['thres_c']} | "
                     f"{c['thres_v']} | {b['P'][0]:.3f}+-{b['P'][1]:.3f} | "
                     f"{b['R'][0]:.3f}+-{b['R'][1]:.3f} | "
                     f"{b['F1'][0]:.3f}+-{b['F1'][1]:.3f} | "
                     f"{b['n'][0]:.1f}+-{b['n'][1]:.1f} |\n")
        for b in blocos:
            fh.write(f"\n## {b['nome']} - frequencia de selecao por variavel "
                     f"({len(SEEDS)} seeds)\n\n")
            fh.write("| variavel | papel | selecionada (de N seeds) |\n")
            fh.write("| :-- | :-- | --: |\n")
            for col in dados["feature_names"]:
                papel = "relevante" if col in rel else "ruido"
                fh.write(f"| {col} | {papel} | {b['freq'].get(col,0)}/{len(SEEDS)} |\n")

    print(f"\nSalvo: {os.path.relpath(cam, RAIZ)}")


if __name__ == "__main__":
    main()
