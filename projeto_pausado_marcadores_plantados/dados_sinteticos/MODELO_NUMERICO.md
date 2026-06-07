# Modelo numérico do testbed de marcadores plantados — DECIDIDO

> **Status: DECIDIDO e implementado em 2026-06-07.** Este documento fecha a "proposta numérica"
> que estava pendente (`docs/desenho_marcadores.md` §8 e `ESTADO_ATUAL.md` §5). As decisões abaixo
> foram tomadas com autonomia delegada pelo usuário, ancoradas em evidência (DCCT/EDIC, ADA, T1D Index).
> O código que materializa tudo isto está em `simulador_hly/modelo_hly.py` e `dados_sinteticos/gerar_base.py`.

## 0. Princípio

A base é um **testbed controlado**: nós **plantamos** relações conhecidas (verdade-base) e a função
ΔHLY é **forma fechada e determinística** (a menos de ruído pequeno). Assim o **gabarito** de "quais
variáveis têm efeito" é fato da base — e o BFSS pode ser medido por precisão/recall ao recuperá-lo.
Não é evidência clínica; é validação algorítmica.

## 1. Marcadores (decisão M1, M2, M3)

| Marcador | Significado | Natureza | Onde entra |
| :-- | :-- | :-- | :-- |
| **M1** | `EXAME_HBA1C` — HbA1c **atual** (controle glicêmico do período) | temporal (muda a cada visita) | responsividade (estado atual) |
| **M2** | `DANO_ACUMULADO` — **dano acumulado** (memória metabólica) | temporal (acumulador) | modulador próprio `fator_dano` |
| **M3** | `MARCADOR_RESPOSTA` — traço **fixo** de responsividade do paciente | estático (no PACIENTE) | responsividade + dinâmica da HbA1c |

- **M1 × M2 são distintos de propósito** (efeito legado / metabolic memory, DCCT-EDIC): quem foi mal por
  anos e *agora* controlou tem **M1 baixo, M2 alto**. São colunas separadas → sinais separáveis pelo BFSS.
- **M2 = acumulador**, não duração crua: `dano(t) = dano(t−1) + max(0, HbA1c(t) − ALVO)`, com `ALVO = 7.0%`
  (alvo ADA para adultos). `TEMPO_DIAGNOSTICO` cru entra como **distrator correlacionado** (o driver real é o dano).

## 2. Fórmula de ΔHLY (por período/ano) — forma fechada

```
ΔHLY = potência_tratamento(L)            # ↑ com o nível da escada
     × responsividade                     # 0.6·M1_saúde + 0.4·M3
     × fator_idade(idade)                 # jovem ganha mais (relógio do corpo)
     × fator_dano(M2)                      # dano alto → menos ganho (relógio da doença), NÃO compensável
     × (1 − desconto_comorbidade)          # renal/cardio/retino/neuro reduzem o teto
     + ruído_pequeno
ΔHLY ∈ [0,1]  (utilidade/qualidade do ano);   HLY_total = Σ ΔHLY ao longo do acompanhamento
```

### Parâmetros decididos (valores fechados — o "gabarito")

| Componente | Fórmula / valores | Âncora de evidência |
| :-- | :-- | :-- |
| `potência_tratamento(L)` | L0→0.55, L1→0.70, L2→0.85, L3→1.00 | escada MDI-humana→MDI-análogo→bomba→bomba+CGM; cada degrau melhora controle e custa mais. **Degraus largos de propósito** para o NIVEL ter efeito DIRETO identificável (não só mediado pela HbA1c) |
| `M1_saúde` | `clip((10.5 − HbA1c)/(10.5 − 5.5), 0, 1)` | HbA1c 5.5%→ótimo (1.0), 10.5%→ruim (0.0) |
| `responsividade` | `0.6·M1_saúde + 0.4·M3` | combinação contínua decidida no design |
| `fator_idade(idade)` | `clip(1.0 − 0.008·(idade − 12), 0.45, 1.0)` | jovem ganha mais anos saudáveis marginais |
| `fator_dano(dano)` | `exp(−0.025·dano)` | multiplicativo = teto não-compensável; dano≈20→0.61, 40→0.37, 60→0.22 |
| `desconto_comorbidade` | `clip(0.18·renal + 0.15·cardio + 0.12·retino + 0.10·neuro, 0, 0.6)` | complicações micro/macrovasculares reduzem qualidade de vida. Magnitudes **altas** para o efeito ser detectável pelo BFSS acima do ruído |
| `ruído` | `N(0, 0.02)` | pequeno → sinal recuperável |

**Fragilidade (decisão de identificabilidade):** cada paciente tem um traço fixo `fragilidade ~ N(0,1)`
que desloca os *hazards* de comorbidade (peso `FRAG_W = 0.9`) de forma **independente do dano**. Sem isso,
as comorbidades seriam quase uma função do `DANO_ACUMULADO` (colineares) e o BFSS não as distinguiria do
ruído — com a fragilidade, elas carregam **sinal próprio** e ficam recuperáveis. A fragilidade em si **não
é exposta como feature** (é causa latente das comorbidades, que são as features observadas).

## 3. Dinâmica longitudinal (como os valores evoluem no tempo)

- **HbA1c (M1):** caminha para um alvo alcançável dependente de tratamento e responsividade:
  `alvo_alc = piso(L) + (1 − M3)·2.5`, com `piso = {0:8.5, 1:7.8, 2:7.2, 3:6.8}`;
  `HbA1c(t) = HbA1c(t−1) + 0.5·(alvo_alc − HbA1c(t−1)) + N(0,0.3)`, clip `[4.5, 13.5]`.
  Efeito: melhor tecnologia (L↑) e maior responsividade (M3↑) → HbA1c menor ao longo do tempo.
- **Tratamento (L):** baseline categórico (P(0,1,2,3)=0.40/0.30/0.20/0.10); **escalada** monótona por regra
  simples (se HbA1c>8.0 por 2 anos seguidos e L<3 → sobe um degrau, p=0.6). Não-decrescente (clínico).
- **Comorbidades (surgem e ficam):** hazard anual logístico crescente com dano/idade/fragilidade, com
  janelas de latência fundamentadas (retinopatia ≥3 anos; nefropatia/neuropatia ≥5 anos; cardio ≥40 anos):
  - retino: `σ(−3.5 + 0.035·dano + 0.015·(idade−40) + 0.9·frag)` se dx≥3
  - renal:  `σ(−4.3 + 0.035·dano + 0.015·(idade−40) + 0.9·frag)` se dx≥5
  - neuro:  `σ(−3.8 + 0.035·dano + 0.9·frag)` se dx≥5
  - cardio: `σ(−5.2 + 0.03·dano + 0.04·(idade−50) + 0.9·frag)` se idade≥40

## 4. Coorte

- **N = 500 pacientes**, acompanhamento **15–25 anos** (anual) → ~10 mil atendimentos (1 linha BFSS = 1 visita).
- Idade baseline ~ `N(35,15)` clip `[12,70]`; HbA1c baseline ~ `N(8.5,1.5)` clip `[5.5,13]`;
  M3 ~ `Beta(2,2)`; duração-dx baseline aleatória (≤ idade−5).
- Entrada do paciente espalhada em ~1995–2005 para o horizonte caber até ~2025 (cronologia válida).

## 5. Gabarito do BFSS (o alvo da validação)

**Alvo de regressão = `DELTA_HLY` por atendimento.**

**✅ Variáveis RELEVANTES (BFSS idealmente seleciona):**
`NU_IDADE`, `EXAME_HBA1C` (M1), `DANO_ACUMULADO` (M2), `MARCADOR_RESPOSTA` (M3), `NIVEL_TRATAMENTO`,
`IS_RENAL`, `IS_CARDIOVASCULAR`, `IS_RETINOPATIA`, `IS_NEUROPATIA`.

**❌ Variáveis IRRELEVANTES (BFSS idealmente descarta):**
`TEMPO_DIAGNOSTICO` (**distrator correlacionado** — o driver é o dano, §7 do design), `IN_SEXO`,
`DS_RACA`, `NM_MUNIC` (dimensão de **equidade** do MOFSS, não preditor de HLY), `INSULINA_MARCA`
(marca dentro do mesmo nível = ruído), `PRESSAO_ARTERIAL` (distrator plausível), `RUIDO_01..RUIDO_10`
(ruído puro gaussiano).

**Métrica:** precisão/recall (relevantes selecionadas vs. ruído). A `TEMPO_DIAGNOSTICO` é o teste de
"pega o driver causal (dano) ou cai no proxy?".

## 6. Artefatos gerados (`dados_sinteticos/saida/`)

- **`base_bfss.csv`** — tabela plana, 1 linha por atendimento, features + alvo `DELTA_HLY`. **É o que o BFSS consome.**
- **`reds_dm1_sintetico.db`** — banco **relacional REDS íntegro** (PACIENTE→ATENDIMENTO→EXAME/RES_EXAME/
  PRESCRICAO/ATEND_DIAGNOS), FKs e cronologia válidas; marcadores plantados guardados como resultados de
  exame / JSON em `COMPLEMENTAR` (atributos legítimos do schema). Satisfaz a restrição inegociável de fidelidade relacional.
- **`gabarito_marcadores.json`** — manifesto-máquina do gabarito (relevantes × ruído, parâmetros).
- **`pacientes_resumo.csv`** — HLY total por paciente (apoio à etapa 2 da política).

## 7. Resultado da geração + validação (seed=42, executado 2026-06-07)

**Coorte:** 500 pacientes, **9.991 atendimentos** (linhas BFSS). HbA1c média global **8,30%** (faixa
5,5–12,1 — plausível para DM1). HLY total médio/paciente 4,04 (0,38–14,04 — boa dispersão dirigida pelos
marcadores). Prevalência final de complicações: renal 44%, retinopatia 63%, neuropatia 55%, cardio 18%
(coerente com DM1 de longa duração e controle heterogêneo).

**Validação A — integridade relacional:** **PASSOU** (0 violações de FK; cronologia nascimento<atendimento,
exame≤resultado, início≤fim; HbA1c em faixa; CPF=11, CNS=15; sexo∈{F,M}).

**Validação B — recuperabilidade do sinal (sanidade pré-BFSS, RandomForest, R²=0,984):** as **9 variáveis
relevantes do gabarito ocupam exatamente o top-9** por importância (recall **100%**). A menor relevante
(`IS_CARDIOVASCULAR` ≈ 0,0048) fica **acima** do maior ruído (`TEMPO_DIAGNOSTICO` ≈ 0,0038 — o distrator
correlacionado, por design), que por sua vez fica acima do ruído puro (`RUIDO_*` ≈ 0,0024). Ordem de
importância: M3 > HbA1c > dano > idade > renal > nível > retino ≈ neuro > cardio ≫ ruído.

**Conclusão:** a base separa **limpa** sinal de ruído e está **pronta para o BFSS** (alvo `DELTA_HLY`). A
métrica de avaliação do BFSS será precisão/recall contra `gabarito_marcadores.json`.

## 8. Como reproduzir

```bash
pip install numpy pandas scikit-learn
python3 dados_sinteticos/gerar_base.py     # gera saida/
python3 validacao/validar_base.py          # valida banco + sinal
```
Determinístico (seed=42). Parâmetros do gabarito vivem em `simulador_hly/modelo_hly.py`.
