"""
BFSS — Binary Fish School Search (single-objective) para seleção de variáveis.

Reconstrução fiel ao algoritmo de Sargo (2013), "Binary Fish School Search
applied to Feature Selection" (IST Lisboa), adaptada ao nosso problema:
alvo CONTÍNUO `DELTA_HLY` (wrapper de REGRESSÃO, não classificação).

Herda a estrutura de operadores da implementação da colega
(FSS-dm1-otmization), corrigindo os pontos problemáticos. Ver README.md.
"""

from .otimizador import run_bfss, ResultadoBFSS
from .avaliador import AvaliadorWrapper

__all__ = ["run_bfss", "ResultadoBFSS", "AvaliadorWrapper"]
