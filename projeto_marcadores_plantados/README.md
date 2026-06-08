# Testbed de marcadores plantados

Plano principal: um **otimizador** (Computação Natural) validado por **marcadores plantados**
(verdade-base) sobre uma base sintética longitudinal de DM1. Inclui:

- **base sintética** longitudinal com marcadores plantados e gabarito (`dados_sinteticos/`);
- **simulador de HLY** (`simulador_hly/`);
- **BFSS** para seleção de variáveis (`otimizadores/`) — **implementado e validado**;
- a rota multiobjetivo (HLY × Custo × Equidade) e a discussão mFSS/MOFSS → PSO discreto.

## Como navegar

- **`RELATORIO_GERAL.md`** — relatório consolidado: passos tomados, resultados e explicações.
- **`ESTADO_ATUAL.md`** — documento canônico com todo o histórico de decisões (escada de
  tratamento, M1/M2/M3, dano acumulado, epistemologia do BFSS, §8 da rota mFSS→discreto).
- **`otimizadores/`** — o entregável avaliado (BFSS pronto; PSO multiobjetivo a seguir).
- **`dados_sinteticos/MODELO_NUMERICO.md`** — o modelo gerador da base (drivers, ruídos, efeitos).
