"""
Laço principal do BFSS (single-objective) — orquestra os operadores.

Sequência por iteração (Sargo 2013):
    1. movimento individual (com aceitação)   -> Eq.(12)
    2. alimentação                            -> Eq.(3)
    3. movimento instintivo coletivo          -> Eq.(13/15/16)
    4. movimento volitivo coletivo            -> Eq.(6/17/18)

CORREÇÃO importante de auditoria: rastreia o MELHOR-GLOBAL ao longo de todas as
iterações. Os movimentos coletivos NÃO têm aceitação, então a população final
pode não conter a melhor solução já vista — pegar `max(fishes)` só no fim (como
o código da colega fazia) pode reportar uma solução pior. Aqui guardamos a
melhor de todas e devolvemos essa.
"""

from dataclasses import dataclass, field
from typing import List
import numpy as np

from .avaliador import AvaliadorWrapper
from .school import School


@dataclass
class ResultadoBFSS:
    selected_features: List[str]
    fitness: float
    r2: float
    num_selecionadas: int
    num_features: int
    historico: list = field(default_factory=list)  # (iter, fitness, r2, n_sel)
    n_avaliacoes: int = 0   # fits reais de KNN (cache miss)
    n_consultas: int = 0    # total de chamadas ao avaliador
    parametros: dict = field(default_factory=dict)


def run_bfss(dados,
             num_fishes=30,
             num_iterations=100,
             alpha=0.9,
             k=5,
             thres_c=0.3,
             thres_v=0.3,
             s_ind_start=0.1,
             s_ind_end=0.001,
             w_scale=500.0,
             seed=42,
             verbose=True):
    """Executa o BFSS sobre os dados já preparados por `preparar_dados`.

    `dados` é o dicionário retornado por preprocessamento.preparar_dados.
    Retorna um ResultadoBFSS (auditável).
    """
    rng = np.random.RandomState(seed)

    feature_names = dados["feature_names"]
    num_features = len(feature_names)

    avaliador = AvaliadorWrapper(
        dados["X_train"], dados["X_test"],
        dados["y_train"], dados["y_test"],
        alpha=alpha, k=k,
    )

    cardume = School(num_fishes, num_features, avaliador,
                     w_scale=w_scale, rng=rng)

    # Melhor-global (elitismo apenas para reporte; não interfere na dinâmica).
    melhor_pos = None
    melhor_fit = -np.inf
    melhor_r2 = 0.0
    historico = []

    for t in range(num_iterations):
        # Eq. (4): decaimento linear do passo individual.
        s_ind_t = s_ind_start - ((s_ind_start - s_ind_end) / num_iterations) * t

        for fish in cardume.fishes:
            fish.individual_movement(s_ind_t)
        cardume.feed()
        cardume.instinctive_movement(thres_c)
        cardume.volitive_movement(thres_v)

        # Melhor da iteração (entre todos os peixes).
        melhor_iter = max(cardume.fishes, key=lambda f: f.fitness)
        if melhor_iter.fitness > melhor_fit:
            melhor_fit = melhor_iter.fitness
            melhor_pos = np.copy(melhor_iter.position)
            melhor_r2 = melhor_iter.r2

        n_sel = int(np.sum(melhor_iter.position))
        historico.append((t + 1, float(melhor_iter.fitness),
                          float(melhor_iter.r2), n_sel))
        if verbose:
            print(f"  iter {t+1:03d}/{num_iterations} | "
                  f"fitness(melhor-global) {melhor_fit:.4f} | "
                  f"R²(global) {melhor_r2:.4f} | "
                  f"n_sel(iter) {n_sel:02d}")

    selecionadas = [feature_names[i] for i in range(num_features)
                    if melhor_pos[i] == 1]

    return ResultadoBFSS(
        selected_features=selecionadas,
        fitness=float(melhor_fit),
        r2=float(melhor_r2),
        num_selecionadas=len(selecionadas),
        num_features=num_features,
        historico=historico,
        n_avaliacoes=avaliador.n_avaliacoes,
        n_consultas=avaliador.n_consultas,
        parametros={
            "num_fishes": num_fishes,
            "num_iterations": num_iterations,
            "alpha": alpha,
            "k": k,
            "thres_c": thres_c,
            "thres_v": thres_v,
            "s_ind_start": s_ind_start,
            "s_ind_end": s_ind_end,
            "w_scale": w_scale,
            "seed": seed,
        },
    )
