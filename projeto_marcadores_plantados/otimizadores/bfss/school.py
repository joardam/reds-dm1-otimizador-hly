"""
Cardume (School) do BFSS — operadores coletivos.

Herdado de FSS-dm1-otmization/src/bfss/school.py. Os três operadores já eram
FIÉIS ao Sargo (2013); as correções aqui são:
  - alimentação (Eq.3) normaliza pelo MAIOR |delta| e limita o peso a [1, W_scale];
  - assinaturas sem X_train/X_test/... (a avaliação vem do AvaliadorWrapper que
    cada peixe carrega) — elimina a fonte de bug do código antigo;
  - uso de um RNG injetável para reprodutibilidade.
"""

import numpy as np
from .fish import Fish


class School:
    def __init__(self, num_fishes, num_features, avaliador,
                 w_scale=500.0, rng=None):
        self.num_fishes = num_fishes
        self.num_features = num_features
        self.avaliador = avaliador
        self.w_scale = float(w_scale)
        self.rng = rng if rng is not None else np.random

        self.fishes = [
            Fish(num_features, avaliador, w_scale=w_scale, rng=self.rng)
            for _ in range(num_fishes)
        ]

        self.total_weight = sum(f.weight for f in self.fishes)
        self.prev_total_weight = self.total_weight

    # ------------------------------------------------------------------ #
    def feed(self):
        """Eq. (3): variação de peso proporcional ao ganho de fitness.

        Após o movimento individual (com aceitação), delta_fitness >= 0, logo a
        alimentação só adiciona peso. Normaliza pelo maior |delta| do cardume e
        satura o peso em [1, W_scale].
        """
        self.prev_total_weight = self.total_weight

        max_delta = max((abs(f.delta_fitness) for f in self.fishes), default=0.0)
        if max_delta <= 0:
            return

        for f in self.fishes:
            f.weight += f.delta_fitness / max_delta
            f.weight = min(self.w_scale, max(1.0, f.weight))

        self.total_weight = sum(f.weight for f in self.fishes)

    # ------------------------------------------------------------------ #
    def instinctive_movement(self, thres_c):
        """Eq. (13)+(15)+(16): movimento instintivo coletivo.

        Constrói o vetor I ponderando posições pelos ganhos individuais, binariza
        por limiar adaptativo (thres_c * max(I)) e aproxima cada peixe virando
        UM bit divergente.
        """
        sum_delta = sum(f.delta_fitness for f in self.fishes if f.delta_fitness > 0)
        if sum_delta == 0:
            return

        # Eq. (13): I = sum(x_i * delta_i) / sum(delta_i), sobre os bem-sucedidos.
        I_cont = np.zeros(self.num_features)
        for f in self.fishes:
            if f.delta_fitness > 0:
                I_cont += f.position * f.delta_fitness
        I_cont = I_cont / sum_delta

        # Eq. (15): limiar adaptativo (garante selecionar >= 1 variável).
        max_I = np.max(I_cont)
        if max_I <= 0:
            return
        threshold = thres_c * max_I
        I_bin = (I_cont >= threshold).astype(int)

        # Eq. (16): cada peixe vira 1 bit divergente, aproximando-se de I_bin.
        for f in self.fishes:
            diff = np.where(f.position != I_bin)[0]
            if len(diff) > 0:
                bit = self.rng.choice(diff)
                f.position[bit] = 1 - f.position[bit]
            f.evaluate()

    # ------------------------------------------------------------------ #
    def volitive_movement(self, thres_v):
        """Eq. (6)+(17)+(18): movimento volitivo coletivo.

        Calcula o baricentro ponderado pelos pesos, binariza por limiar adaptativo
        e contrai o cardume em direção ao baricentro se o peso global subiu, ou
        dilata em direção ao anti-baricentro caso contrário.
        """
        # Eq. (6): baricentro B = sum(x_i * w_i) / sum(w_i).
        B_cont = np.zeros(self.num_features)
        for f in self.fishes:
            B_cont += f.position * f.weight
        if self.total_weight > 0:
            B_cont = B_cont / self.total_weight

        max_B = np.max(B_cont)
        if max_B <= 0:
            return
        threshold = thres_v * max_B
        B_bin = (B_cont >= threshold).astype(int)

        # Sucesso global da iteração -> contrai; estagnou/piorou -> dilata.
        contraindo = self.total_weight > self.prev_total_weight

        for f in self.fishes:
            # Eq. (17) contração para B; Eq. (18) dilatação para o anti-baricentro.
            alvo = B_bin if contraindo else (1 - B_bin)
            diff = np.where(f.position != alvo)[0]
            if len(diff) > 0:
                bit = self.rng.choice(diff)
                f.position[bit] = 1 - f.position[bit]
            f.evaluate()
