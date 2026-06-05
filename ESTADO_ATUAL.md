# ESTADO ATUAL DO PROJETO — REDS-DM1 (RECOMEÇO)

> Arquivo de contexto canônico. Leia isto **primeiro**. Em caso de conflito com qualquer
> outro documento, **este arquivo tem prioridade**. Última atualização: **2026-06-05**.
>
> **Houve um recomeço (reset) do projeto nesta data.** A tentativa anterior foi inteira
> preservada na pasta `old/` (nada foi apagado). Os motivos do reset e o que mudou estão
> na seção 2. Este arquivo descreve o **novo** plano.

---

## 1. Objetivo do projeto (o que é avaliado)

Disciplina de **Computação Natural**. O entregável avaliado é um **otimizador** que **maximiza os
Anos de Vida Saudáveis (HLY — Healthy Life Years)** de pacientes com Diabetes Mellitus Tipo 1 (DM1)
em Pernambuco, gerando uma **Frente de Pareto** entre três objetivos: **HLY × Custo × Equidade**.

Algoritmos previstos:
- **BFSS / wFSS** (Binary/weighted Fish School Search) — seleção de variáveis.
- **MOFSS / mFSS** (Multi-Objective/Mixed-Variable Fish School Search) — núcleo da otimização.
  ⚠️ **Pode mudar — ver §8 (POSSÍVEL MUDANÇA DE ROTA).**
- **NSGA-II** e **PSO** — baselines de comparação. ⚠️ Status de "obrigatório" **não confirmado**
  pelo usuário (o pipeline mental dele era só BFSS→mFSS); ver §8.

**Forma do problema de otimização (decidido 2026-06-04): POLÍTICA DINÂMICA POR REGRAS.** O otimizador
não aloca paciente-a-paciente; ele otimiza os **parâmetros de uma política** (regras de escalada de
tratamento, priorização e orçamento) aplicada à população ao longo do horizonte longitudinal. O BFSS
escolhe as features que as regras usam; MOFSS/NSGA-II/PSO otimizam os parâmetros. O **orçamento acopla
os pacientes** → problema não-separável (evita o risco de ser fácil demais). Detalhes em
`docs/desenho_marcadores.md` §5b.

**Referência do mFSS contínuo-discreto:** PALLAS (`yukuntan92/PALLAS`, `PALLAS/fss.py`), lido linha a
linha e clonado em `docs/PALLAS_ref/` (só referência). Trata contínuo×discreto por **limiarização
integrada** (discreto vira {-1,0,+1} via limiar crescente; contínuo via passo que encolhe). ⚠️ Esse
código é **single-objective**: "misto" e "multiobjetivo" são camadas separadas → reaproveitamos a
maquinaria mista, mas teremos que **acoplar a camada Pareto (dominância + arquivo externo)** nós mesmos.

**O entregável é o OTIMIZADOR, não o realismo clínico dos dados.** Os dados são substrato/testbed.

---

## 2. Por que recomeçamos (o que aprendemos na tentativa anterior, em `old/`)

A tentativa anterior usava o dataset **Diabetes 130-US (Kaggle)** + **CTGAN** para gerar a base.
Discutindo a fundo, identificamos problemas de fundamentação que motivaram o reset:

1. **População errada.** O 130-US é ~97% **DM2 idoso**; o CTGAN só reproduz a fonte, então o
   sintético também era DM2 idoso. Pouquíssimo DM1 de verdade (~1.024 por código ICD-9).
2. **Sem eixo temporal e sem foco em qualidade de vida.** A base era uma "fotografia" transversal,
   sem trajetória. E a modelagem caminhava para **mortalidade** (HbA1c→SMR→sobrevivência), que é o
   **inverso** do objetivo: *Anos de Vida **Saudáveis*** é sobre **qualidade de vida**, não só sobre
   não morrer. HLY = quantidade de vida (sobrevivência) **×** qualidade de vida (sem incapacidade,
   estabilidade glicêmica diária: tempo no alvo, hipoglicemias, variabilidade).
3. **Sem verdade-base.** Com dados "realistas" porém sem rótulo de verdade, é impossível **provar**
   que o BFSS selecionou as variáveis certas ou que o MOFSS achou a frente ótima — e provar isso é
   justamente o que a disciplina avalia.

### Pesquisa de fundamentação (registrada para não repetir)
- **T1D Index** (Lancet, Gregory et al. 2022): é um modelo de Markov **populacional/por país**
  (ciclos anuais), não individual. Liga nível de cuidado → HbA1c → SMR → mortalidade; validado a
  ±6% **no agregado**, não em previsão individual de HLY. Bom como *arcabouço conceitual*, não como
  função paciente-a-paciente.
- A relação **HbA1c → desfecho** com evidência individual real vem do **DCCT/EDIC** (HR 1,56 de
  mortalidade por +10% relativo de HbA1c; 30% menos doença cardiovascular por 30 anos).
- Bases reais de DM1 longitudinais existem (ver seção 4), mas têm trade-offs de acesso e de
  tradução para o REDS.

---

## 3. Decisão atual (a abordagem escolhida)

**Validação por MARCADORES PLANTADOS (verdade-base / planted ground truth) como ESPINHA DORSAL.**

A ideia:
1. Construir uma base sintética onde se **planta deliberadamente** relações conhecidas
   ("marcadores" — ex.: "perfil com marcador X responde mais ao tratamento Y em HLY").
2. Rodar **BFSS** (seleção de variáveis) e **MOFSS/mFSS** (otimização).
3. **Validar que os algoritmos recuperam o que foi plantado:**
   - BFSS: medir **precisão/recall** na seleção dos marcadores relevantes vs. ruído.
   - MOFSS: a **Frente de Pareto** encontrada bate com a frente **analiticamente conhecida**.

Por que esta é a abordagem certa para o entregável:
- Com verdade-base, dá para **provar** que o otimizador funciona (recupera o ótimo conhecido) —
  impossível com dados reais sem gabarito.
- Driblá toda a discussão de fidelidade clínica: a afirmação passa a ser **algorítmica**
  ("BFSS/MOFSS funcionam e recuperam o sinal"), não clínica.
- Alinhado ao escopo: base = testbed; nota = otimizador.

**Honestidade declarada:** é um **testbed controlado para validação algorítmica**, NÃO evidência
clínica sobre diabetes. Documentar isso explicitamente.

### Camadas do plano (escala de risco)
| Camada | Papel | Risco |
| :-- | :-- | :-- |
| **Marcadores plantados** | **Espinha dorsal** — prova que BFSS/MOFSS recuperam o sinal conhecido | Baixo |
| **Base realista DM1** (ex.: T1DiabetesGranada via casamento estatístico) | 2ª camada — "aplicabilidade" em substrato plausível | Médio |
| **Fusão generativa (PAR/TimeGAN)** | **Evitar** como peça principal | Alto |

### Restrições inegociáveis
- **Fidelidade relacional no final é obrigatória.** A base sintética deve sair como um banco
  relacional REDS íntegro (FKs, cronologia, faixas válidas). Marcadores são injetados como
  atributos/relações legítimas do schema; um validador garante a integridade.
- Equidade é medida por **MUNICÍPIO** (o dicionário REDS não tem GERES/região).

---

## 4. Bases reais de DM1 pesquisadas (para a 2ª camada, se/quando formos usar)

| Base | Pontos fortes | Pontos fracos |
| :-- | :-- | :-- |
| **T1DiabetesGranada** (736 pac., 100% DM1, idade 12–81, 4 anos, CGM 15min, ICD-9, HbA1c) | Melhor encaixe no REDS (Patient/Diagnostics/Biochemical), variedade etária, temporal | **Sem medicamentos**; acesso via solicitação no Zenodo (termo de uso) |
| **T1D Exchange Registry** (dezenas de milhares, todas idades) | Variedade real de tratamentos (bomba/CGM/MDI), idade, HbA1c | Acesso por aplicação; mais "visitas" do que traço temporal fino |
| **MetaboNet** (consolidado DM1, GitHub aberto) | Aberto, longitudinal, tratamento+CGM+HbA1c | Centrado em CGM → **difícil traduzir pro REDS**; idade mais estreita |

Decisão sobre estas: **pendente** — só entram na 2ª camada. Começaremos pelo testbed plantado, que
não depende de baixar nada nem resolver acesso.

---

## 5. Próximos passos (ordem sugerida — NADA implementado ainda)

1. **Desenhar o testbed de marcadores plantados** (discutir antes de codar):
   - 🟡 **EM RASCUNHO** — estrutura desenhada em **`docs/desenho_marcadores.md`**. Decisões já fixadas:
     - Base **100% DM1** (sem DM2); fora: metformina/sulfonilureia.
     - **Tratamento = escada ordenada `NIVEL_TRATAMENTO` (0→3)** atravessando modalidade + tier de
       insulina, monótona em eficácia e custo (L0 MDI+humana → L1 MDI+análogo → L2 bomba → L3
       bomba+CGM). **Decidido 2026-06-05:** o **nível** é o sinal (decisão + custo + alvo da escalada);
       a **droga específica dentro do nível** é ruído. Escada ordinal → consistente com o "discreto
       por design" da §8.
     - **Longitudinal:** mesmo paciente repetido em vários tempos (REDS `PACIENTE` 1→N `ATENDIMENTO`),
       cronologia correta, com melhora/piora **plantada** = "delta T" como verdade-base.
     - **Horizonte longo (~15–30 anos)**, não 2 — complicações DM1 levam ≥10 anos a surgir; cadência
       ~anual com HbA1c trimestral/semestral, rastreio de complicações conforme diretrizes.
     - Campos dos 19 do reds_clean: manter (idade, HbA1c, IS_RENAL/CARDIO, insulina, município),
       virar ruído (sexo/raça), remover (drogas DM2, triagem Manchester, internação, óbito), e
       adicionar (tempo de diagnóstico, nível de tratamento, marcador de resposta, retino/neuro).
     - **Epistemologia do BFSS (decidido 2026-06-05):** o gabarito (quais variáveis têm efeito) é fato
       da base; que o BFSS o **recupere** é **hipótese sob teste** (idealmente sim, medido por
       precisão/recall) — não um "deve". Não selecionar é resultado válido, não defeito de spec.
     - **Seleção = BFSS single-objective (decidido 2026-06-05).** **MOBFSS descartado** (nem como
       opcional): o alvo é um valor único → um objetivo só basta; vários marcadores são *features*
       (entrada), não objetivos, e um objetivo já recupera todos. Multiobjetivo de verdade fica só na
       etapa 2 (política: HLY × Custo × Equidade).
     - **Alvo da seleção (decidido 2026-06-05, importante): `ΔHLY` por atendimento.** Cada linha = uma
       visita; alvo = ganho de HLY do período; features = valores daquele período. Casa com a fórmula
       `ΔHLY(período) = f(features do período)` → o BFSS recupera exatamente as variáveis da fórmula.
   - Plano em **2 fases**: (1) mecânica temporal reusando faixas do reds_clean; (2) reformular valores.
   - Falta a **proposta numérica** (pesos M1/M2/M3, curvas, regras de progressão temporal, custos por
     nível, horizonte/cadência exatos, ruído, exemplo de paciente ponta a ponta).
   - Definir o schema REDS mínimo (reaproveitar de `old/banco/db_schema.py` e `validator.py`).
2. **Construir o gerador sintético com marcadores** + validador de integridade relacional.
3. **Construir o simulador de HLY** (transforma perfil+tratamento em HLY, respeitando os marcadores).
4. **Implementar BFSS** e validar recuperação dos marcadores (precisão/recall).
5. **Implementar MOFSS/mFSS** e validar a Frente de Pareto vs. frente conhecida.
6. **Baselines NSGA-II e PSO** para comparação.
7. (Opcional) 2ª camada: aplicar em base realista DM1.

---

## 6. Mapa de arquivos (estado do recomeço)

- **`ESTADO_ATUAL.md`** — este arquivo (canônico).
- **`old/`** — tentativa anterior preservada (pipeline 130-US/CTGAN, `banco/`, `pre_processamento/`,
  `projeto/`, CSV sintético, ESTADO_ATUAL antigo). Consultar para reaproveitar schema/validador.
- Estrutura nova: a definir conforme avançarmos (ver `docs/` se criado).

---

## 7. Princípios de trabalho (do usuário)

- **Discutir antes de implementar.** Alinhar escopo/abordagem antes de codar.
- **Linguagem simples** — o usuário é estudante de Computação Natural, não técnico clínico.
- **Fidelidade relacional** do banco no final é requisito firme.

---

## 8. POSSÍVEL MUDANÇA DE ROTA (NÃO DECIDIDO) — domínio discreto por design vs. mFSS misto

> **Status: discutido em 2026-06-05, NÃO decidido.** Aguarda decisão do usuário **com a equipe dele**.
> Registrado deliberadamente como **rota possível e reversível** — o usuário quer poder voltar atrás.
> Esta seção **não** sobrescreve o plano vigente; ela documenta a ideia inicial e a alternativa em aberto.

### 8.1 Ideia INICIAL (registro definitivo do que era o plano)
Pipeline enxuto, na cabeça do usuário desde o começo:

```
Banco → BFSS → mFSS (o próprio mFSS constrói a Frente de Pareto)
```

- O **mFSS misto (contínuo × discreto)** era o **núcleo/protagonista** do 2º estágio.
- Parâmetros de política tratados como **mistos** — alguns contínuos (limiar `L`, orçamento `B`),
  outros discretos (`D` = nº de períodos, critério de prioridade).
- **NSGA-II / PSO:** a doc os listava como "baselines de comparação", mas o usuário **não** os
  considerava obrigatórios — o pipeline mental dele era só **BFSS → mFSS**. (Se são exigência do
  enunciado/professor, ainda é **a confirmar** — provavelmente sim, em disciplina de metaheurística,
  mas isso é decisão da equipe.)

### 8.2 Por que pode mudar (o que descobrimos na discussão)
- O mFSS contínuo×discreto só está implementado no **PALLAS** (nichado), e o `fss.py` é
  **SINGLE-OBJECTIVE** — **NÃO tem Frente de Pareto** (sem dominância, sem arquivo de não-dominados).
  ⚠️ O clone `docs/PALLAS_ref/` está no `.gitignore` e **não vem no repo** — o que sabemos do PALLAS
  vem das anotações em `docs/desenho_marcadores.md` §5b, não de código reverificável aqui.
- São **DUAS dificuldades independentes:** **(A)** a camada de Pareto e **(B)** o contínuo×discreto.
  PALLAS resolve **B sem A**. MOFSS de prateleira costuma ter **A sem B**. Precisamos de **A+B**.
- A **única razão de ser do mFSS** é lidar com os **dois domínios**. E o usuário esclareceu que o misto
  era **meio, não fim**: foi escolhido porque **parecia melhor implementação que discretizar**, e
  **não** porque tratar variável mista fosse a "graça"/contribuição do trabalho.
- **Inversão da intuição:** para **single-objective**, o misto do PALLAS é a implementação **mais
  fácil** (era essa a intuição original). Mas para **multiobjetivo** (nosso caso), o misto vira a
  **MAIS difícil** — porque a parte mista do PALLAS não tem Pareto e teríamos que **acoplar à mão** a
  dominância + arquivo externo sobre a maquinaria contínua-discreta. A intuição não estava errada; foi
  formada num cenário (single-objective) que não é o nosso.

### 8.3 A possível mudança de rota (chamada de "Mundo B — discreto por design")
- Decidir, **por design**, que **todos** os parâmetros da política vivem em **grid (discretos)**:
  `L` ∈ {7.0, 7.5, 8.0, ...}, `D` inteiro pequeno, `B` em níveis, critério categórico.
- São **poucos parâmetros e todos toleram grid** → perda de resolução desprezível, custo baixíssimo.
- **Consequência lógica (ponto do usuário):** isso **ELIMINA a necessidade do mFSS**, porque o motivo
  dele (o domínio misto) **deixa de existir**. O 2º estágio passa a ser um **otimizador multiobjetivo
  DISCRETO**.
- **É um OU-EXCLUSIVO:** não dá pra "discretizar **e** manter o mFSS". Discretizar **custa** o mFSS.
  (Foi uma contradição corrigida na discussão.)
- **Mata o maior risco** (o contínuo×discreto acoplado ao Pareto). Sobra ainda a camada de Pareto
  (dificuldade A), que continua de pé com qualquer algoritmo — mas é **território padrão** e bem mais
  domável quando o espaço já é discreto.

### 8.4 Sub-decisão em aberto SE formos pro Mundo B
Quem ocupa a vaga do 2º estágio (a camada Pareto é necessária em qualquer caso):
- **FSS discreto + camada Pareto construída por nós** → fica na família dos peixes; nós escrevemos a
  dominância + arquivo externo.
- **NSGA-II pronto** (ex.: `pymoo`) → Pareto e variável discreta **de graça**, mas **não é FSS**.

Depende de **uma pergunta ainda não respondida:** *o entregável exige ser FSS especificamente, ou
aceita outro otimizador de Computação Natural?* — a confirmar com a equipe/enunciado.

### 8.5 Como REVERTER (se a equipe decidir manter o mFSS — "Mundo A")
- Manter **pelo menos uma** variável genuinamente **contínua** (ex.: `L` ou `B`) → aí o mFSS se
  justifica de novo.
- Encarar o acoplamento **contínuo×discreto + Pareto** de frente.
- Plano B de emergência nesse mundo: **MOFSS** (continua peixe, Pareto na literatura) ou **NSGA-II**
  (menor risco). Estratégia de isolar risco: construir a **camada Pareto agnóstica** primeiro e ter um
  baseline multiobjetivo funcionando como rede de segurança antes de apostar tudo no mFSS.
