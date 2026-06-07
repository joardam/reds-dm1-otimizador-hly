"""
modelo_hly.py — Simulador individual de Anos de Vida Saudáveis (HLY) com MARCADORES PLANTADOS.

Forma fechada e determinística (a menos de ruído pequeno) => o gabarito de "quais variáveis têm
efeito" é fato da base. Ancorado em DCCT/EDIC (memória metabólica / efeito legado), ADA (alvo de
HbA1c 7%) e na escada de tratamento do design (`docs/desenho_marcadores.md`).

Decisões numéricas documentadas em `dados_sinteticos/MODELO_NUMERICO.md`.
"""

from __future__ import annotations
import math
import numpy as np

# ------------------------------------------------------------------ PARÂMETROS (o "gabarito")
ALVO_HBA1C = 7.0  # alvo ADA (%) — referência do acumulador de dano

# potência do tratamento por nível da escada (0->3), monótona crescente.
# Degraus largos => o NIVEL tem efeito DIRETO identificável (não só mediado pela HbA1c).
POTENCIA_TRATAMENTO = {0: 0.55, 1: 0.70, 2: 0.85, 3: 1.00}

# piso de HbA1c alcançável por nível (melhor tecnologia -> piso menor)
PISO_HBA1C = {0: 8.5, 1: 7.8, 2: 7.2, 3: 6.8}

# pesos da responsividade (combinação contínua de M1 e M3)
W_M1, W_M3 = 0.6, 0.4

# faixa de saúde da HbA1c: 5.5% -> 1.0 (ótimo), 10.5% -> 0.0 (ruim)
HBA1C_OTIMO, HBA1C_RUIM = 5.5, 10.5

# fator idade: jovem ganha mais
IDADE_REF, IDADE_SLOPE, IDADE_PISO = 12, 0.008, 0.45

# fator dano: exp(-K * dano) -> teto multiplicativo não-compensável
DANO_K = 0.025

# desconto por comorbidade (somado, com teto). Magnitudes altas => efeito detectável pelo BFSS.
DESC_RENAL, DESC_CARDIO, DESC_RETINO, DESC_NEURO, DESC_TETO = 0.18, 0.15, 0.12, 0.10, 0.60

# fragilidade: traço fixo por paciente que desloca os hazards de comorbidade de forma
# INDEPENDENTE do dano -> as comorbidades carregam sinal próprio (decola da colinearidade com M2).
FRAG_W = 0.9

RUIDO_DHLY = 0.02  # desvio do ruído gaussiano em ΔHLY

# dinâmica da HbA1c
HBA1C_AJUSTE = 0.5       # fração do gap percorrida por período
HBA1C_RUIDO = 0.3        # ruído de medição
HBA1C_MIN, HBA1C_MAX = 4.5, 13.5
M3_SPREAD = 2.5          # quanto a baixa responsividade eleva o alvo alcançável


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


# ------------------------------------------------------------------ FATORES da fórmula de ΔHLY
def m1_saude(hba1c: float) -> float:
    """HbA1c atual -> saúde glicêmica em [0,1] (maior HbA1c => menor saúde)."""
    v = (HBA1C_RUIM - hba1c) / (HBA1C_RUIM - HBA1C_OTIMO)
    return float(np.clip(v, 0.0, 1.0))


def responsividade(hba1c: float, m3: float) -> float:
    return W_M1 * m1_saude(hba1c) + W_M3 * m3


def fator_idade(idade: float) -> float:
    return float(np.clip(1.0 - IDADE_SLOPE * (idade - IDADE_REF), IDADE_PISO, 1.0))


def fator_dano(dano: float) -> float:
    return math.exp(-DANO_K * dano)


def desconto_comorbidade(renal: int, cardio: int, retino: int, neuro: int) -> float:
    d = DESC_RENAL * renal + DESC_CARDIO * cardio + DESC_RETINO * retino + DESC_NEURO * neuro
    return float(np.clip(d, 0.0, DESC_TETO))


def delta_hly(nivel: int, hba1c: float, dano: float, m3: float, idade: float,
              renal: int, cardio: int, retino: int, neuro: int, rng: np.random.Generator) -> float:
    """ΔHLY do período — produto suave de fatores (forma fechada)."""
    valor = (
        POTENCIA_TRATAMENTO[nivel]
        * responsividade(hba1c, m3)
        * fator_idade(idade)
        * fator_dano(dano)
        * (1.0 - desconto_comorbidade(renal, cardio, retino, neuro))
    )
    valor += rng.normal(0.0, RUIDO_DHLY)
    return float(np.clip(valor, 0.0, 1.0))


# ------------------------------------------------------------------ DINÂMICA longitudinal
def proxima_hba1c(hba1c: float, nivel: int, m3: float, rng: np.random.Generator) -> float:
    alvo_alc = PISO_HBA1C[nivel] + (1.0 - m3) * M3_SPREAD
    nova = hba1c + HBA1C_AJUSTE * (alvo_alc - hba1c) + rng.normal(0.0, HBA1C_RUIDO)
    return float(np.clip(nova, HBA1C_MIN, HBA1C_MAX))


def incremento_dano(hba1c: float) -> float:
    return max(0.0, hba1c - ALVO_HBA1C)


def hazard_retinopatia(dano: float, idade: float, frag: float = 0.0) -> float:
    return _sigmoid(-3.5 + 0.035 * dano + 0.015 * (idade - 40) + FRAG_W * frag)


def hazard_renal(dano: float, idade: float, frag: float = 0.0) -> float:
    return _sigmoid(-4.3 + 0.035 * dano + 0.015 * (idade - 40) + FRAG_W * frag)


def hazard_neuropatia(dano: float, frag: float = 0.0) -> float:
    return _sigmoid(-3.8 + 0.035 * dano + FRAG_W * frag)


def hazard_cardiovascular(dano: float, idade: float, frag: float = 0.0) -> float:
    return _sigmoid(-5.2 + 0.03 * dano + 0.04 * (idade - 50) + FRAG_W * frag)


def regra_escalada(nivel: int, anos_acima_alvo: int, rng: np.random.Generator) -> int:
    """Escada de tratamento monótona: HbA1c alta por >=2 anos -> sobe um degrau (p=0.6)."""
    if nivel < 3 and anos_acima_alvo >= 2 and rng.random() < 0.6:
        return nivel + 1
    return nivel
