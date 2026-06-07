# otimizadores/

Os algoritmos de Computação Natural — o **entregável avaliado**.

- **BFSS / wFSS** — seleção de variáveis (idealmente recupera os marcadores plantados — hipótese sob teste, medida por precisão/recall).
- **PSO discreto** — **núcleo multiobjetivo** do 2º estágio (Frente de Pareto: HLY × Custo × Equidade).
  Rota fechada em 2026-06-07: política **discretizada por design** → **mFSS descartado** (ver
  `../ESTADO_ATUAL.md` §8).
- ~~**MOFSS / mFSS**~~ — descartado (histórico em `../ESTADO_ATUAL.md` §8).
- **Baseline** (ex.: NSGA-II): **em aberto** — manter um ao lado do PSO ainda não foi decidido.

> A implementar após o testbed e o simulador estarem prontos. Pendências da rota: o **como** da camada
> de Pareto sobre o PSO (MOPSO c/ arquivo de não-dominados vs. escalarização) e a decisão do baseline.
