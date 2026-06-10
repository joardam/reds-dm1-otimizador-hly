"""
Roda o BFSS na base sintética de marcadores plantados e gera um relatório
auditável (console + JSON + Markdown).

Uso:
    python rodar_bfss.py
    python rodar_bfss.py --iters 150 --fishes 30 --alpha 0.9 --seed 42

Saídas (em otimizadores/resultados/):
    bfss_resultado.json   — tudo (parâmetros, seleção, métricas, histórico)
    bfss_relatorio.md     — leitura humana, com a tabela de auditoria por variável
"""

import os
import json
import argparse
import numpy as np

from bfss.preprocessamento import preparar_dados
from bfss.avaliador import AvaliadorWrapper
from bfss.otimizador import run_bfss
from bfss.validacao import validar_selecao

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ_PLANO = os.path.dirname(AQUI)
CSV_PADRAO = os.path.join(RAIZ_PLANO, "dados_sinteticos", "saida", "base_bfss.csv")
GABARITO_PADRAO = os.path.join(RAIZ_PLANO, "dados_sinteticos", "saida", "gabarito_marcadores.json")
DIR_SAIDA = os.path.join(AQUI, "resultados")


def parse_args():
    p = argparse.ArgumentParser(description="BFSS na base de marcadores plantados.")
    p.add_argument("--csv", default=CSV_PADRAO)
    p.add_argument("--gabarito", default=GABARITO_PADRAO)
    p.add_argument("--fishes", type=int, default=30)
    p.add_argument("--iters", type=int, default=100)
    # Padrões = campeã do tuning (ver resultados/tuning.md e estabilidade.md):
    # alpha=0.8, thres_c=0.6, thres_v=0.4 -> P=1.0, R=0.89, F1=0.94 (estável nos seeds).
    p.add_argument("--alpha", type=float, default=0.8)
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--thres-c", type=float, default=0.6)
    p.add_argument("--thres-v", type=float, default=0.4)
    p.add_argument("--w-scale", type=float, default=500.0)
    p.add_argument("--seed", type=int, default=42)
    # Subamostragem do wrapper (OTIMIZAÇÃO #2). Padrão = modo rápido.
    p.add_argument("--max-treino", type=int, default=2500,
                   help="máx. linhas de treino p/ o wrapper (default 2500)")
    p.add_argument("--max-teste", type=int, default=1200,
                   help="máx. linhas de teste p/ o wrapper (default 1200)")
    p.add_argument("--completo", action="store_true",
                   help="usa a base inteira (run canônico fiel, sem subamostrar)")
    return p.parse_args()


def r2_baseline(dados, k):
    """R² usando TODAS as variáveis candidatas (referência de comparação)."""
    av = AvaliadorWrapper(dados["X_train"], dados["X_test"],
                          dados["y_train"], dados["y_test"], alpha=1.0, k=k)
    todas = np.ones(len(dados["feature_names"]), dtype=int)
    _, r2 = av.avaliar(todas)
    return r2


def main():
    args = parse_args()

    print("=" * 70)
    print("BFSS — seleção de variáveis na base sintética (marcadores plantados)")
    print("=" * 70)
    print(f"CSV:      {args.csv}")
    print(f"Gabarito: {args.gabarito}")

    max_treino = None if args.completo else args.max_treino
    max_teste = None if args.completo else args.max_teste

    dados = preparar_dados(args.csv, args.gabarito,
                           test_size=0.3, seed=args.seed,
                           max_treino=max_treino, max_teste=max_teste)

    modo = "COMPLETO (canônico)" if args.completo else "rápido (subamostrado)"
    print(f"\nModo: {modo}")
    print(f"Pacientes: {dados['n_pacientes']} | "
          f"Atendimentos: {dados['n_atendimentos']} "
          f"(wrapper: treino {dados['n_treino']} / teste {dados['n_teste']})")
    print(f"Variáveis candidatas: {len(dados['feature_names'])} "
          f"({len(dados['relevantes'])} relevantes + "
          f"{len(dados['irrelevantes'])} irrelevantes no gabarito)")

    r2_base = r2_baseline(dados, args.k)
    print(f"\nR² baseline (todas as {len(dados['feature_names'])} variáveis): {r2_base:.4f}")

    print(f"\nRodando BFSS (fishes={args.fishes}, iters={args.iters}, "
          f"alpha={args.alpha}, thres_c={args.thres_c}, thres_v={args.thres_v}, "
          f"seed={args.seed})...\n")

    res = run_bfss(
        dados,
        num_fishes=args.fishes,
        num_iterations=args.iters,
        alpha=args.alpha,
        k=args.k,
        thres_c=args.thres_c,
        thres_v=args.thres_v,
        w_scale=args.w_scale,
        seed=args.seed,
        verbose=True,
    )

    val = validar_selecao(res.selected_features,
                          dados["relevantes"], dados["irrelevantes"])

    # ---------------- Relatório no console ---------------- #
    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print(f"Selecionadas: {res.num_selecionadas} de {res.num_features} variáveis")
    print(f"Fitness (Eq.10): {res.fitness:.4f}")
    print(f"R² do subconjunto selecionado: {res.r2:.4f}  "
          f"(baseline todas: {r2_base:.4f})")
    print(f"Avaliações: {res.n_consultas} consultas -> {res.n_avaliacoes} "
          f"fits reais de KNN (cache evitou "
          f"{res.n_consultas - res.n_avaliacoes})")
    print()
    print(f"PRECISÃO: {val.precisao:.3f} | RECALL: {val.recall:.3f} | "
          f"F1: {val.f1:.3f}")
    print()
    print("Auditoria por variável (vs gabarito):")
    print(f"  [VP] acertos ({len(val.vp)}): {val.vp}")
    print(f"  [FP] falsos alarmes ({len(val.fp)}): {val.fp}")
    print(f"  [FN] relevantes perdidas ({len(val.fn)}): {val.fn}")
    print(f"  [VN] ruído corretamente descartado ({len(val.vn)}): {val.vn}")

    # ---------------- Persistência auditável ---------------- #
    os.makedirs(DIR_SAIDA, exist_ok=True)

    saida = {
        "entradas": {
            "csv": os.path.relpath(args.csv, RAIZ_PLANO),
            "gabarito": os.path.relpath(args.gabarito, RAIZ_PLANO),
            "n_pacientes": dados["n_pacientes"],
            "n_atendimentos": dados["n_atendimentos"],
            "n_treino": dados["n_treino"],
            "n_teste": dados["n_teste"],
            "candidatas": dados["feature_names"],
            "mapeamento_categorias": dados["mapeamento_categorias"],
        },
        "parametros": res.parametros,
        "resultado": {
            "selecionadas": res.selected_features,
            "num_selecionadas": res.num_selecionadas,
            "num_features": res.num_features,
            "fitness": res.fitness,
            "r2_selecionado": res.r2,
            "r2_baseline_todas": r2_base,
            "n_avaliacoes": res.n_avaliacoes,
            "n_consultas": res.n_consultas,
        },
        "validacao": {
            "precisao": val.precisao,
            "recall": val.recall,
            "f1": val.f1,
            "VP": val.vp,
            "FP": val.fp,
            "FN": val.fn,
            "VN": val.vn,
        },
        "historico": [
            {"iter": it, "fitness": fit, "r2": r2, "n_sel": n}
            for (it, fit, r2, n) in res.historico
        ],
    }

    caminho_json = os.path.join(DIR_SAIDA, "bfss_resultado.json")
    with open(caminho_json, "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=2)

    caminho_md = os.path.join(DIR_SAIDA, "bfss_relatorio.md")
    _escrever_relatorio_md(caminho_md, saida, dados)

    print(f"\nSalvo: {os.path.relpath(caminho_json, RAIZ_PLANO)}")
    print(f"Salvo: {os.path.relpath(caminho_md, RAIZ_PLANO)}")


def _escrever_relatorio_md(caminho, saida, dados):
    p = saida["parametros"]
    r = saida["resultado"]
    v = saida["validacao"]
    rel = set(dados["relevantes"])

    linhas = []
    linhas.append("# Relatório BFSS — seleção de variáveis (base de marcadores plantados)\n")
    linhas.append("## Entradas\n")
    linhas.append(f"- Base: `{saida['entradas']['csv']}`")
    linhas.append(f"- Gabarito: `{saida['entradas']['gabarito']}`")
    linhas.append(f"- Pacientes: {saida['entradas']['n_pacientes']} | "
                  f"Atendimentos: {saida['entradas']['n_atendimentos']} "
                  f"(treino {saida['entradas']['n_treino']} / teste {saida['entradas']['n_teste']})\n")

    linhas.append("## Parâmetros\n")
    linhas.append("| parâmetro | valor |\n| :-- | :-- |")
    for chave, valor in p.items():
        linhas.append(f"| {chave} | {valor} |")
    linhas.append("")

    linhas.append("## Resultado\n")
    linhas.append(f"- **Selecionadas:** {r['num_selecionadas']} de {r['num_features']}")
    linhas.append(f"- **Fitness (Eq.10):** {r['fitness']:.4f}")
    linhas.append(f"- **R² subconjunto:** {r['r2_selecionado']:.4f} "
                  f"(baseline todas as variáveis: {r['r2_baseline_todas']:.4f})")
    linhas.append(f"- **Avaliações do wrapper:** {r['n_avaliacoes']}\n")

    linhas.append("## Validação por verdade-base\n")
    linhas.append(f"- **Precisão:** {v['precisao']:.3f}")
    linhas.append(f"- **Recall:** {v['recall']:.3f}")
    linhas.append(f"- **F1:** {v['f1']:.3f}\n")

    linhas.append("### Auditoria por variável\n")
    linhas.append("| variável | no gabarito | selecionada | resultado |")
    linhas.append("| :-- | :-- | :-- | :-- |")
    selecionadas = set(r["selecionadas"])
    for col in dados["feature_names"]:
        papel = "relevante" if col in rel else "irrelevante"
        sel = "sim" if col in selecionadas else "não"
        if col in selecionadas and col in rel:
            tag = "✅ VP"
        elif col in selecionadas and col not in rel:
            tag = "⚠️ FP"
        elif col not in selecionadas and col in rel:
            tag = "❌ FN"
        else:
            tag = "✓ VN"
        linhas.append(f"| {col} | {papel} | {sel} | {tag} |")
    linhas.append("")

    with open(caminho, "w", encoding="utf-8") as fh:
        fh.write("\n".join(linhas))


if __name__ == "__main__":
    main()
