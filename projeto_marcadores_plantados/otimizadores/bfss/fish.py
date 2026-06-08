"""
Peixe (Fish) do BFSS.

Herdado de FSS-dm1-otmization/src/bfss/fish.py, com as correções:
  - avaliação delegada ao AvaliadorWrapper (regressão), em vez de embutir
    KNeighborsClassifier no próprio peixe;
  - peso inicial = W_scale/2 e limitado a [1, W_scale] (Sargo); a colega
    iniciava em 1.0 e não tinha teto;
  - guarda `r2` da posição corrente para auditoria.
"""

import numpy as np


class Fish:
    def __init__(self, num_features, avaliador, w_scale=500.0, rng=None):
        self.num_features = num_features
        self.avaliador = avaliador
        self.w_scale = float(w_scale)
        self.rng = rng if rng is not None else np.random

        # Eq. (11): posição inicial binária aleatória (~metade das variáveis ativas).
        self.position = self.rng.randint(2, size=num_features)

        # Sargo: peixe "nasce" com peso W_scale/2; peso fica entre 1 e W_scale.
        self.weight = self.w_scale / 2.0
        self.fitness = 0.0
        self.r2 = 0.0
        self.delta_fitness = 0.0

        # Avalia a posição inicial para já ter fitness/r2 definidos.
        self.fitness, self.r2 = self.avaliador.avaliar(self.position)

    def evaluate(self):
        """Reavalia a posição corrente e atualiza fitness, r2 e delta_fitness."""
        novo_fitness, novo_r2 = self.avaliador.avaliar(self.position)
        self.delta_fitness = novo_fitness - self.fitness
        self.fitness = novo_fitness
        self.r2 = novo_r2

    def individual_movement(self, s_ind_t):
        """Eq. (12): exploração individual com aceitação.

        Para cada bit, vira (flip) com probabilidade s_ind_t. A nova posição só
        é adotada se o fitness MELHORAR; caso contrário, reverte (e delta = 0).
        """
        old_position = np.copy(self.position)
        old_fitness = self.fitness
        old_r2 = self.r2

        for j in range(self.num_features):
            if self.rng.rand() < s_ind_t:
                self.position[j] = 1 - self.position[j]

        self.evaluate()

        if self.fitness <= old_fitness:
            # Rejeita o movimento: volta ao estado anterior.
            self.position = old_position
            self.fitness = old_fitness
            self.r2 = old_r2
            self.delta_fitness = 0.0
