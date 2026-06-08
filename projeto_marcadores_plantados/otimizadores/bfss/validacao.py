"""
Validação por verdade-base: a seleção do BFSS recupera os marcadores plantados?

Compara as variáveis selecionadas contra `gabarito_marcadores.json`:
  - VP (acerto)      = selecionada E relevante
  - FP (falso alarme)= selecionada E irrelevante  (ruído/distrator escolhido por engano)
  - FN (perdida)     = relevante E NÃO selecionada
  - VN               = irrelevante E NÃO selecionada

Métricas: precisão, recall, F1 — a "espinha dorsal" da avaliação (ver
ESTADO_ATUAL.md). Não recuperar tudo é resultado VÁLIDO, não defeito do código.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ResultadoValidacao:
    precisao: float
    recall: float
    f1: float
    vp: List[str] = field(default_factory=list)
    fp: List[str] = field(default_factory=list)
    fn: List[str] = field(default_factory=list)
    vn: List[str] = field(default_factory=list)


def validar_selecao(selecionadas, relevantes, irrelevantes):
    sel = set(selecionadas)
    rel = set(relevantes)
    irr = set(irrelevantes)

    vp = sorted(sel & rel)
    fp = sorted(sel & irr)
    fn = sorted(rel - sel)
    vn = sorted(irr - sel)

    precisao = len(vp) / (len(vp) + len(fp)) if (len(vp) + len(fp)) else 0.0
    recall = len(vp) / (len(vp) + len(fn)) if (len(vp) + len(fn)) else 0.0
    f1 = (2 * precisao * recall / (precisao + recall)) if (precisao + recall) else 0.0

    return ResultadoValidacao(
        precisao=precisao, recall=recall, f1=f1,
        vp=vp, fp=fp, fn=fn, vn=vn,
    )
