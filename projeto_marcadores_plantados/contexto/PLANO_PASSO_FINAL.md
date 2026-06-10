# Plano do passo final — 2º estágio: Frente de Pareto HLY × Custo × Equidade

> **Status: PLANO APROVADO (em detalhamento), 2026-06-10.** Branch: `final-implementation`.
> Decisões tomadas em conversa com o usuário. Implementação ainda **não iniciada** (aguarda OK).
> A §6 (atuação das políticas) está em **detalhamento** — pode ajustar antes de codar.

---

## 0. Objetivo

Otimizar os **parâmetros de uma política dinâmica de tratamento** aplicada à coorte sintética de
marcadores plantados, gerando a **Frente de Pareto** entre três objetivos —
**HLY (↑) × Custo (↓) × Equidade (↑)** — com **MOPSO discreto**, e **provar** que o otimizador
funciona comparando a frente encontrada com a **frente verdadeira conhecida** (por enumeração do grid).

O entregável avaliado é o **otimizador**; a base é **testbed** de validação algorítmica (não evidência
clínica). É o análogo, no 2º estágio, dos marcadores plantados do BFSS: lá provamos que o algoritmo
recupera os marcadores conhecidos; aqui, que recupera a **frente de Pareto conhecida**.

## 1. Decisões consolidadas

| Item | Decisão |
| :-- | :-- |
| Motor de avaliação | **Oráculo** — re-simula a coorte com `simulador_hly/modelo_hly.py` (exato, determinístico) |
| Conexão com o BFSS | A regra de **prioridade** usa apenas marcadores que o BFSS validou (dano, idade, HbA1c) |
| Equidade | **1 − Gini** das HLY médias por município |
| Camada de Pareto | **MOPSO** discreto + **arquivo externo** de não-dominados |
| Baseline | **NSGA-II** (pymoo), ao lado do PSO |
| Validação | **Frente exata por enumeração** = gabarito; métricas hypervolume / IGD / cobertura |
| Custos | **Reais (R$)**, valores redondos ilustrativos ancorados em CMED/SUS |
| Visualização | Frente de Pareto **3D interativa** (desktop + mobile) |

## 2. Variáveis de decisão (a política, em grid discreto)

| Parâmetro | Significado | Grid |
| :-- | :-- | :-- |
| `L` | limiar de HbA1c que dispara escalada | {7,0 · 7,25 · 7,5 · 7,75 · 8,0 · 8,5} |
| `D` | anos acima do limiar antes de escalar (paciência) | {1 · 2 · 3} |
| `B` | orçamento anual (teto de gasto da coorte) — **acopla os pacientes** | 6 níveis (baixo → ilimitado) |
| `prioridade` | quem escala primeiro sob orçamento | {dano↑ · idade↓ · HbA1c↑ · custo-benefício · equânime-por-município} |

≈ **6×3×6×5 = 540 políticas** (tamanho ajustável). Grande o bastante para a força bruta custar (540
simulações da coorte) e o MOPSO ganhar achando a frente com **muito menos** avaliações; pequeno o
bastante para ainda conhecermos a **frente exata** (gabarito). Dimensionar o grid é a resposta à
crítica "por que não só força bruta".

## 3. Modelo de custos (R$ — ilustrativos, ancorados em CMED/SUS)

| Nível | Tratamento | Custo anual recorrente | Aquisição única |
| :-- | :-- | --: | --: |
| **L0** | MDI + insulina humana (NPH/regular) | R$ 600 | — |
| **L1** | MDI + insulina análoga (glargina/lispro) | R$ 3.000 | — |
| **L2** | Bomba de infusão | R$ 6.000 (insumos) | R$ 18.000 (1ª vez na bomba) |
| **L3** | Bomba + CGM | R$ 15.000 (insumos + sensores) | R$ 18.000 (se ainda não tinha bomba) |

Monótono e com degraus largos. Fonte anotada em `custos.py`; explicitamente ilustrativos.

## 4. Os três objetivos

- **HLY** (maximizar): `Σ_pacientes Σ_anos ΔHLY` (também reporta a média por paciente).
- **Custo** (minimizar): `Σ custo_anual(nível) + Σ aquisições`, em R$.
- **Equidade** (maximizar): `1 − Gini( {HLY média de cada município} )`.

Tensões que geram a frente: o **orçamento** cria Custo×HLY; a **prioridade** cria HLY×Equidade.

## 5. Pipeline e algoritmos

- **Avaliação (oráculo):** cada política → re-simula a coorte → (HLY, Custo, Equidade). O MOPSO é
  **caixa-preta**: só vê política → 3 números (nunca a fórmula).
- **MOPSO discreto + arquivo externo** de não-dominados (líderes sorteados do arquivo guiam o enxame;
  posições projetadas ao grid).
- **Baseline NSGA-II** (pymoo) no mesmo problema.
- **Frente exata** por enumeração das 540 políticas (conjunto não-dominado = gabarito).
- **Métricas:** hypervolume, IGD (distância à frente verdadeira), cobertura (% de pontos ótimos
  recuperados), nº de avaliações.

## 6. Atuação das políticas (EM DETALHAMENTO — discutir antes de codar)

Uma política é um conjunto **fixo** de parâmetros `(L, D, B, prioridade)`; eles **não mudam** durante a
simulação. A simulação roda ano a ano sobre a **mesma coorte** (traços fixos: responsividade M3,
fragilidade, idade de diagnóstico, HbA1c inicial, município). A cada ano:

1. **Dinâmica** (igual ao `modelo_hly.py`): HbA1c evolui rumo ao alvo do nível atual, o dano acumula,
   hazards podem disparar comorbidades, e computa-se o ΔHLY do ano.
2. **Candidatos a escalar:** para cada paciente, conta-se há quantos anos seguidos `HbA1c > L`. Se
   `≥ D` anos **e** nível < 3 → o paciente é **candidato** a subir um degrau.
3. **Acoplamento pelo orçamento (não-separável):** junta-se **todos** os candidatos do ano, ordena-se
   por `prioridade`, e escala-se descendo a lista **até o orçamento `B` do ano acabar** (a escalada custa
   o degrau novo + eventual aquisição da bomba). Quem não coube **espera** e tenta de novo no ano seguinte.
4. **Custo do ano** = soma dos custos de nível de todos os pacientes + aquisições do ano.

Ao final do horizonte: HLY = Σ ΔHLY; Custo = Σ custos; Equidade = 1 − Gini das HLY médias por município.

**Critérios de prioridade (usam só features observáveis):** `dano↑` (maior dano primeiro), `idade↓`
(mais jovem primeiro), `HbA1c↑` (pior controle primeiro), `custo-benefício` (maior ganho esperado por
R$, estimado por marcadores observáveis como M3+HbA1c), `equânime-por-município` (prioriza pacientes de
municípios com menor HLY média acumulada → empurra o Gini para baixo).

**Determinismo (números aleatórios comuns):** todas as políticas são avaliadas sobre a **mesma coorte
com a mesma semente** de ruído → diferenças de resultado vêm **só** da política. Isso torna o objetivo
bem-definido e a frente reprodutível.

**Diferença para a base atual:** a base foi gerada com uma regra de escalada fixa e estocástica
(`regra_escalada`: HbA1c>8 por 2 anos, p=0,6). A política **generaliza** essa regra (`L`, `D` ajustáveis,
escalada determinística) e **acrescenta** a camada de orçamento + prioridade — que é o que torna o
problema multiobjetivo e não-separável.

## 7. Estrutura de arquivos

```
otimizadores/politica/
  custos.py                 # CUSTO_NIVEL (R$) + agregação + orçamento
  simulador_politica.py     # simular_coorte(politica, traços) -> (HLY, Custo, Equidade)
  equidade.py               # 1 - Gini por município
  mopso.py                  # PSO discreto multiobjetivo + arquivo de não-dominados
  baseline_nsga.py          # NSGA-II (pymoo)
  frente_exata.py           # enumeração do grid -> frente exata (gabarito)
  metricas_pareto.py        # hypervolume, IGD, cobertura
  rodar_politica.py         # entrypoint: MOPSO + NSGA-II + validação -> JSON + MD
  gerar_visualizacao_pareto.py [+ _mobile]
```

## 8. Ordem de implementação + checkpoints

| # | Etapa | Checkpoint |
| :-- | :-- | :-- |
| 1 | `custos.py` | custo de uma trajetória conhecida confere |
| 2 | Expor traços + `simular_coorte(politica)` | política-base reproduz a base atual (determinismo) |
| 3 | `equidade.py` (Gini) | casos `[10,10,10]`→1 e `[30,0,0]`→baixo |
| 4 | `simulador_politica.py` | política → 3 números coerentes |
| 5 | `frente_exata.py` | frente verdadeira existe, com tradeoff nos 3 eixos |
| 6 | `mopso.py` + `metricas_pareto.py` | MOPSO recupera a frente com « avaliações |
| 7 | `baseline_nsga.py` | NSGA-II comparável ao MOPSO |
| 8 | `rodar_politica.py` + relatório | resultados auditáveis salvos (JSON + MD) |
| 9 | Visualização 3D (desktop + mobile) | frente navegável |

## 9. Honestidade declarada (vai no relatório)

Testbed controlado de **validação algorítmica**, não evidência clínica. Custos ilustrativos. O mérito é
o **otimizador recuperar a frente verdadeira** — não o realismo do diabetes. O otimizador nunca usa a
fórmula (caixa-preta); a fórmula serve só para montar o gabarito.
