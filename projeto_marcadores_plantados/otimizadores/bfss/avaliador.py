"""
Avaliador (função de fitness) do BFSS — abordagem WRAPPER.

CORREÇÃO PRINCIPAL em relação ao código da colega:
o alvo `DELTA_HLY` é CONTÍNUO, então o wrapper usa `KNeighborsRegressor`
+ R² (regressão), e NÃO `KNeighborsClassifier` + acurácia (classificação).
Jogar um alvo contínuo num classificador trataria cada valor float como uma
classe distinta -> acurácia ≈ 0 e fitness sem sentido.

Fitness — Eq. (10) de Sargo (2013), mantida na forma original:

    fitness = alpha * desempenho + (1 - alpha) * (Nt - Ns) / Nt

onde:
  - desempenho     = R² do KNN-regressor no conjunto de teste (recortado em [0, 1]);
  - Nt             = nº total de variáveis candidatas;
  - Ns             = nº de variáveis selecionadas (bits = 1);
  - (Nt - Ns)/Nt   = redução de dimensionalidade (recompensa subconjuntos menores);
  - alpha ∈ [0, 1] = peso entre desempenho e parcimônia (Sargo usa um único alpha;
                     a colega usava dois pesos soltos weight_acc/weight_feat).
"""

import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import r2_score


class AvaliadorWrapper:
    """Encapsula treino/teste e o cálculo do fitness de um subconjunto de bits.

    Centralizar a avaliação aqui (em vez de espalhar X_train/X_test/... pelas
    assinaturas de Fish e School) reduz a superfície de erro — foi exatamente
    onde o `bfss_optimizer.py` da colega ficou inconsistente (assinaturas que
    não batiam) e quebrou.
    """

    def __init__(self, X_train, X_test, y_train, y_test,
                 alpha=0.9, k=5, n_jobs=1):
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.num_features = X_train.shape[1]
        self.alpha = float(alpha)
        self.k = int(k)
        # n_jobs: no regime subamostrado (KNN pequeno) n_jobs=1 é ~1.6x MAIS
        # rápido que -1 (overhead de threads). Mantido configurável; padrão 1.
        self.n_jobs = n_jobs

        # OTIMIZAÇÃO #1: memoização. Após a convergência, muitos peixes repetem a
        # mesma posição; cachear evita refazer o fit/predict (custoso) do KNN.
        # Resultado-preservante: cache hit devolve exatamente o mesmo valor.
        self._cache = {}
        self.n_consultas = 0   # total de chamadas a avaliar()
        self.n_avaliacoes = 0  # fits reais de KNN (cache miss) — custo de verdade

    def avaliar(self, position):
        """Avalia um vetor binário de seleção.

        Retorna (fitness, r2): fitness é o valor da Eq.(10); r2 é o R² bruto
        (pode ser negativo) guardado só para auditoria/relatório.
        """
        self.n_consultas += 1
        position = np.asarray(position)
        chave = position.tobytes()
        cached = self._cache.get(chave)
        if cached is not None:
            return cached

        selected = np.where(position == 1)[0]
        num_selected = len(selected)

        # Penalidade máxima se nenhum atributo estiver ativo.
        if num_selected == 0:
            self._cache[chave] = (0.0, 0.0)
            return 0.0, 0.0

        self.n_avaliacoes += 1
        model = KNeighborsRegressor(n_neighbors=self.k, n_jobs=self.n_jobs)
        model.fit(self.X_train[:, selected], self.y_train)
        pred = model.predict(self.X_test[:, selected])
        r2 = r2_score(self.y_test, pred)

        # Desempenho recortado em [0, 1] para casar de escala com a parcela de
        # parcimônia (também em [0, 1]) e manter a Eq.(10) bem condicionada.
        desempenho = max(0.0, r2)
        reducao = (self.num_features - num_selected) / self.num_features
        fitness = self.alpha * desempenho + (1.0 - self.alpha) * reducao

        resultado = (fitness, r2)
        self._cache[chave] = resultado
        return resultado
