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

---

## BFSS — implementado (passo 4)

Reconstrução fiel ao **Sargo (2013)** ("Binary Fish School Search applied to Feature
Selection", IST Lisboa — PDF em `../docs/`), herdando a estrutura dos operadores da
implementação da colega (`FSS-dm1-otmization`) e **corrigindo os pontos problemáticos**.

### Estrutura

```
bfss/
  avaliador.py        wrapper KNN-REGRESSOR + fitness Eq.(10)
  fish.py             peixe: init Eq.(11), movimento individual Eq.(12)
  school.py           cardume: alimentação Eq.(3), instintivo Eq.(13/15/16), volitivo Eq.(6/17/18)
  preprocessamento.py base_bfss.csv -> X, y, nomes, grupos (encode texto, scaling, split por paciente)
  otimizador.py       laço Sargo + rastreio do melhor-global
  validacao.py        precisão/recall/F1 vs gabarito_marcadores.json
rodar_bfss.py         entrypoint: roda na base sintética e gera relatório auditável
resultados/           bfss_resultado.json + bfss_relatorio.md (gerados)
```

### Correções sobre o código herdado

1. **Regressão, não classificação.** O alvo `DELTA_HLY` é contínuo → `KNeighborsRegressor`
   + R² (a colega usava `KNeighborsClassifier` + acurácia, que não faz sentido para alvo contínuo).
2. **Padronização (StandardScaler)** ajustada no treino — o KNN depende de escala; estava ausente.
3. **Split por paciente** (GroupShuffleSplit) — evita vazamento longitudinal (mesmo paciente em
   treino e teste).
   - Nota de desempenho: no regime subamostrado o KNN é pequeno e `n_jobs=1` é ~1.6x mais rápido
     que `-1` (overhead de threads). Padrão `n_jobs=1`, configurável.
4. **Pré-processamento de texto/IDs** — encode label (1 coluna por variável, preserva o mapeamento
   bit↔variável↔gabarito); descarte de IDs/data/ano.
5. **Melhor-global rastreado** ao longo das iterações — movimentos coletivos não têm aceitação, então
   `max(fishes)` só no fim podia reportar solução pior.
6. **`W_scale`** (teto de peso, Sargo) e **alpha único** na Eq.(10) (em vez de dois pesos soltos).
7. **Sem código morto** — o `bfss_optimizer.py` da colega tinha assinaturas inconsistentes e quebrava.

### Como rodar

```bash
cd otimizadores
python rodar_bfss.py                       # padrões (fishes=30, iters=100, alpha=0.9, seed=42)
python rodar_bfss.py --iters 150 --alpha 0.95
```

Saída clara e **auditável**: console + `resultados/bfss_resultado.json` (parâmetros, seleção,
métricas, histórico) + `resultados/bfss_relatorio.md` (tabela VP/FP/FN/VN por variável).
