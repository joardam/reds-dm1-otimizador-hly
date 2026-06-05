# Desenho dos marcadores plantados — RASCUNHO

> Status: **rascunho** (estrutura decidida; faltam os números exatos).
> Documento de trabalho. O canônico de estado é o `ESTADO_ATUAL.md` na raiz.
> Última atualização: 2026-06-04.

## 0. Decisões de base
- Base **100% DM1** (sem diabetes tipo 2). Tratamento por **insulina + bomba/CGM**, NÃO
  metformina/sulfonilureia (que eram drogas de DM2 herdadas do dataset antigo).
- **Tudo deve encaixar no REDS clean** (reaproveitar schema/validador de `old/banco/`).
- Base **longitudinal**: o **mesmo paciente repetido em vários tempos**, cronologicamente correto,
  com melhora/piora plantada (ver seção 2).
- Plano em **duas fases**: (1) montar a mecânica temporal reaproveitando as **faixas de valores** do
  reds_clean; (2) depois **reformular os valores específicos** para a indicação do problema.

## 1. Fórmula de HLY (efeito contínuo e condicional, NÃO binário)

Ganho de Anos de Vida Saudáveis é um **produto suave de fatores** (forma fechada, conhecida →
preserva o gabarito), aplicado **ao longo da trajetória** (acumula no tempo):

```
ΔHLY(período) = potência_do_tratamento
              × responsividade_do_paciente   (combinação contínua de M1,M2,M3)
              × fator_idade                   (jovem ganha mais; curva monótona)
              × (1 − desconto_comorbidade)    (renal/cardio/retino/neuro reduzem o teto)
              + ruído_pequeno
HLY_total = soma dos períodos ponderados pela qualidade ao longo do acompanhamento
```

- `responsividade` = ex.: `0.5·M1 + 0.3·M2 + 0.2·M3` (cada marcador 0..1). Espectro contínuo.
- **Freios de complexidade:** 3 marcadores + 2 moduladores + **1 interação** (tratamento×responsividade).
  Forma fechada → ótimo teórico calculável. Ruído pequeno → sinal recuperável.

## 2. Estrutura temporal (longitudinal) — paciente repetido no tempo

Encaixa direto no REDS: **um `PACIENTE` (1) → vários `ATENDIMENTO` (N)**, cada um com data crescente.
A **fidelidade relacional / cronologia** já é verificável pelo `validator.py` do `old/`.

**Ganho elegante:** como **nós plantamos a trajetória**, a melhora/piora ao longo do tempo é
**verdade-base conhecida** — temos o "delta T" real na base, mas ainda como gabarito (sem precisar de
base real longitudinal e seus problemas de acesso/validação).

**Campos estáticos (no `PACIENTE`, não mudam):**
`ID_PACIEN`, `NU_IDADE` (baseline; cresce no tempo), `IN_SEXO`, `DS_RACA`, `NM_MUNIC`,
`MARCADOR_RESPOSTA` (M3, traço fixo que define COMO o paciente evolui).

**Campos temporais (em cada `ATENDIMENTO`, evoluem):**
`DT_ATENDIMENTO` (datas crescentes), `EXAME_HBA1C` (M1; melhora/piora conforme tratamento×responsividade),
`TEMPO_DIAGNOSTICO` (M2; aumenta), `MODALIDADE_TRATAMENTO` (MDI/bomba/CGM; a decisão),
`IS_RENAL`/`IS_CARDIOVASCULAR`/`IS_RETINOPATIA`/`IS_NEUROPATIA` (comorbidades que **aparecem** se o
controle for ruim por tempo suficiente).

## 3. Horizonte e cadência (fundamentado em diretrizes)

DM1 é doença crônica; **2 anos é curto demais**. Complicações levam **≥10 anos** para surgir, e é só
no horizonte longo que a diferença entre bom e mau controle aparece (senão o otimizador não tem o
que distinguir). Parâmetros realistas (ADA / DCCT-EDIC):

- **Horizonte de acompanhamento:** **~15–30 anos** (progressivo, de longo prazo). Default sugerido
  a calibrar: ~20 anos a partir do baseline (ou do diagnóstico até uma idade-horizonte).
- **HbA1c:** a cada **3–6 meses** (trimestral se mudando terapia; semestral se estável).
- **Rastreio de complicações:** **retinopatia** a partir de 3–5 anos do diagnóstico (anual/bienal);
  **nefropatia** anual a partir de 5 anos de duração.
- **Cadência prática de atendimentos no testbed (a decidir):** atendimento **anual** (revisão padrão)
  ao longo de 15–30 anos, com HbA1c podendo ser trimestral dentro do ano. Mantém volume gerenciável.
- Âncora de efeito: controle apertado (HbA1c ≤7%) → **35–76% menos** complicações microvasculares.

## 4. Campos REDS: manter / ruído / trocar-remover / adicionar
(base de partida = 19 campos do `old/banco/reds_dm1_clean.db` MODEL_DATASET)

**✅ MANTER (encaixam no desenho):**
`ID_ATEND`, `ID_PACIEN` (chaves); `NU_IDADE` (modulador); `EXAME_HBA1C` (M1);
`IS_RENAL`, `IS_CARDIOVASCULAR` (moduladores); `NM_MUNIC` (equidade);
`MED_INSULINA_NPH`, `MED_INSULINA_REGULAR` (insulina faz sentido no DM1).

**🟡 MANTER como RUÍDO (distrator de peso zero — útil pro BFSS):**
`IN_SEXO`, `DS_RACA`.

**❌ TROCAR/REMOVER (herança DM2 + pronto-socorro agudo, não condiz com DM1 crônico):**
`MED_METFORMINA`, `MED_GLIBENCLAMIDA` (drogas de DM2); `DS_COR_RISCO`, `DS_CLASSIF_RISCO`
(triagem Manchester aguda); `TEMPO_INTERNACAO_DIAS` (custo agora vem do nível de cuidado);
`DS_TIPO_ATEND`, `DS_ESPECI` (administrativos); `FL_OBITO` (mortalidade — saímos desse caminho).

**➕ ADICIONAR (fidelidade, ancorado em literatura):**
`TEMPO_DIAGNOSTICO` (duração — M2); `MODALIDADE_TRATAMENTO` (MDI/bomba/CGM — decisão+custo;
intensidade atual = modulador); `MARCADOR_RESPOSTA` (M3 sintético);
`IS_RETINOPATIA`, `IS_NEUROPATIA` (camada de qualidade de vida/incapacidade);
`PRESSAO_ARTERIAL` *(opcional)* (preditor de nefropatia — modulador ou distrator plausível).

## 5. Variáveis do BFSS (gabarito da seleção)

**✅ Esperadas (selecionar):** `NU_IDADE`, `IS_RENAL`, `IS_CARDIOVASCULAR`, `EXAME_HBA1C` (M1),
`TEMPO_DIAGNOSTICO` (M2), `MARCADOR_RESPOSTA` (M3), `INTENSIDADE_TRATAMENTO_ATUAL` (modulador).
(+ opcionalmente `IS_RETINOPATIA`/`IS_NEUROPATIA` se entrarem na fórmula.)

**❌ Ignoradas (descartar):** `IN_SEXO`, `DS_RACA`, exame extra plantado sem efeito,
IDs/administrativos, `RUIDO_01..15`, e **os remédios individuais** (o BFSS deve provar que a droga
isolada não importa, só o controle/intensidade geral).

**Métrica:** precisão/recall (selecionou as esperadas vs. caiu em ruído).

## 5b. Problema de otimização: POLÍTICA DINÂMICA POR REGRAS (decisão escolhida)

Decisão de design: a otimização é **dinâmica por regras** (meio-termo entre estático e dinâmico
completo). O otimizador **não** escolhe tratamento paciente-a-paciente; ele otimiza os **parâmetros
de uma política** (conjunto de regras) aplicada à população inteira ao longo do horizonte.

- **Regras (exemplos):** gatilho de escalada ("se HbA1c > L por D períodos → sobe nível de
  tratamento"); priorização do recurso escasso (bomba+CGM) por critério; teto de orçamento B/período.
- **O que o MOFSS/PSO/NSGA-II otimizam:** os parâmetros das regras (L, D, B, critérios).
- **Papel do BFSS:** escolher **em quais features as regras se apoiam** → é aqui que ele deve
  recuperar os marcadores plantados e descartar o ruído.
- **Avaliação de uma política:** aplicar à população + simular o horizonte (regras disparam conforme
  os pacientes evoluem) → HLY total, custo total, equidade (os 3 objetivos da Frente de Pareto).

**Por que assim:** (1) o **orçamento acopla os pacientes** e a política é **compartilhada** → o
problema vira não-separável, genuinamente difícil → as metaheurísticas têm o que disputar (evita o
risco de "todos empatam no ótimo"); (2) o longitudinal passa a **valer de verdade**, pois a decisão
acontece dentro do tempo; (3) tratável de construir (não explode como o dinâmico livre por ano).

### Fundamento metodológico do mFSS contínuo-discreto (verificado no código-fonte)
Referência: **PALLAS** (yukuntan92/PALLAS, Python) — `PALLAS/fss.py`. Clone de leitura em
`docs/PALLAS_ref/` (só referência, não é nosso código). Lido linha a linha em 2026-06-04.

Como o mFSS trata **contínuo × discreto** (no `fss.py`):
- **Operadores unificados** (`individual_movement`, `feeding`, `collective_instinctive_movement`,
  `collective_volitive_movement`), separando tipos por índice no vetor do peixe.
- **Contínuo:** passo escalado por parâmetro adaptativo que **encolhe** por iteração (`update_step`).
- **Discreto:** passo `uniform(-1,1)` **limiarizado** para {-1,0,+1}, com limiar `thresh=j/num_iterations`
  que **cresce** → exploração no início, explotação no fim. É limiarização integrada (NÃO operador
  discreto separado; NÃO arredondamento só no fim — há passo discreto real toda iteração).
- **Fitness é plugável** (PALLAS usa verossimilhança de rede gênica via `abcsmc`/`apf`; trocamos pela
  nossa avaliação de política → HLY/custo/equidade).

> 🔀 **2026-06-05 — Este achado abriu uma POSSÍVEL MUDANÇA DE ROTA (não decidida).** Se a política for
> tratada como **discreta por design**, a necessidade do mFSS **desaparece** (o motivo dele é o domínio
> misto). Decisão em aberto, aguardando a equipe. **Ver `ESTADO_ATUAL.md` §8** (registro canônico da
> ideia inicial × possível mudança).

⚠️ **ACHADO QUE MUDA O PLANO:** o `fss.py` do PALLAS é **SINGLE-OBJECTIVE** (maximiza um escalar; sem
dominância nem arquivo de não-dominados). "Misto" e "multiobjetivo" são **camadas separadas**. Logo:
- Reaproveitamos do PALLAS a **maquinaria mista (contínuo+discreto)**.
- Teremos que **acoplar por cima a camada multiobjetivo** (dominância + arquivo externo, estilo MOFSS)
  para a Frente de Pareto (HLY × custo × equidade).
- E adaptar o discreto de {-1,0,+1} (arestas de rede) para nossos domínios (inteiro/categórico/binário).

## 6. Papéis especiais (fora do pool do BFSS)
- `NM_MUNIC`: não é preditor de HLY (BFSS ignora), mas é dimensão de **equidade** do MOFSS.
- **Nível de cuidado a aplicar**: variável de **decisão do MOFSS** + fonte do **CUSTO** (2º objetivo).
- Tripla natureza do medicamento: tratamento decidido (decisão+custo) / intensidade atual (feature) /
  remédios individuais (ruído).

## 7. Botão de dificuldade (opcional, 2ª rodada)
Plantar 1 distrator **correlacionado** com um marcador verdadeiro (ex.: exame que "anda junto" com a
HbA1c mas sem efeito causal) — testa se o BFSS pega o driver real ou cai no decoy.

## 8. Pendente (próximo passo)
Proposta **numérica** final: pesos M1/M2/M3; curvas dos moduladores; regras de progressão temporal
(quanto a HbA1c melhora/piora por período conforme tratamento×responsividade; quando surge cada
comorbidade); custos por nível de cuidado; horizonte/cadência exatos; faixa de ruído; e um
**exemplo de paciente ponta a ponta** (trajetória completa → HLY) para aprovação antes de codar.
