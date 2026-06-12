# Estrutura da Apresentação — Equipe 4 (versão reequilibrada para o Plano B)

> Documento de **planejamento** (não é a apresentação construída). Define o roteiro
> slide a slide, o design e o que muda em relação à versão anterior.
> Premissa do orientador: **mostrar a trajetória, focar no Plano B e passar de
> relance no BFSS.** Tom acadêmico, sóbrio, sem excessos.

---

## 1. Diagnóstico da versão atual (o que corrigir)

A versão anterior tem 18 telas e é tecnicamente correta, mas o **peso narrativo está
no Plano A** (objetivo ambicioso, MOPSO/NSGA-II, BFSS com slide de resultados completo).
A correção é de **ênfase**, não de conteúdo:

| Problema na versão atual | Correção nesta estrutura |
|---|---|
| Plano A aparece como protagonista (objetivo, pipeline, Pareto) | Plano A vira **contexto de origem**; só explica o "de onde viemos" |
| BFSS tem slide próprio com métricas em destaque (P=1.0, R=0.889…) | BFSS vira **um slide "de relance"**: existe, foi validado, está em curso |
| As 3 fases ocupam 3 slides separados | Trajetória condensada em **1 slide-linha-do-tempo** |
| O "ganho" fica diluído entre validação e perfil | **Ganho explícito** em slide próprio: o perfil do indivíduo ideal |
| A validação (cosseno 1.000) aparece de passagem | Vira **o argumento central** do Plano B: "o otimizador acha o ótimo conhecido" |

**Regra de ouro do reequilíbrio:** ~70% do tempo no Plano B (objetivo adaptado →
Wellness → passo a passo → por que PSO → validação → ganho → limitações), ~15% na
trajetória/redução de escopo, ~15% em BFSS + próximos passos.

---

## 2. Mensagem central (uma frase)

> "Reduzimos o escopo de forma honesta e **entregamos um otimizador de enxame (PSO)
> validado**: num problema convexo e contínuo, o PSO encontra **exatamente** o ótimo
> analítico conhecido (cosseno = 1,000) e **revela o perfil do diabético ideal** de
> forma interpretável."

O AUC ≈ 0,66 **não** é a vitória. A vitória é dupla: (1) **validação** — o otimizador
acha o ótimo conhecido; (2) **interpretação** — o vetor de pesos é o perfil clínico.

---

## 3. Roteiro slide a slide (13 telas + capa)

Cada slide traz: **Mensagem** (a frase que o slide tem que cravar), **Conteúdo**,
**Visual** e **Responde a** (qual pedido do orientador é coberto).

### Capa
- **Mensagem:** identidade do projeto, sem promessas exageradas.
- **Conteúdo:** Projeto REDS-DM1 · Otimizador Bioinspirado · Computação Natural · Equipe 4.
  Subtítulo honesto: *"Entrega: PSO validado sobre coorte de diabéticos (Plano B)"*.
- **Visual:** título + filete fino; sem ícones decorativos.

### Slide 1 — Agenda
- **Mensagem:** o caminho da conversa em uma olhada.
- **Conteúdo:** 5 blocos: (i) De onde viemos — trajetória; (ii) O Plano B e seu objetivo;
  (iii) Como funciona — passo a passo; (iv) Validação e ganho; (v) Limitações e próximos passos.
- **Visual:** lista numerada simples; destacar visualmente o bloco "Plano B" como o miolo.

### Slide 2 — Síntese executiva
- **Mensagem:** em 30 s, o que é, qual problema e onde chegamos.
- **Conteúdo:** contexto (Computação Natural; REDS-PE; alvo DM em PE; SUS) +
  uma linha de resultado: *"PSO implementado do zero, validado contra a solução
  analítica (cosseno = 1,000)."*
- **Visual:** 3 colunas curtas (Contexto · Proposta · Resultado).

### Slide 3 — Trajetória em 3 fases (linha do tempo)  ← *substitui 3 slides por 1*
- **Mensagem:** o projeto amadureceu; a redução de escopo foi decisão técnica, não recuo.
- **Conteúdo (linha do tempo horizontal):**
  - **Fase 1 — 130-US + CTGAN** → *abandonada* (população errada, sem eixo temporal, sem gabarito).
  - **Fase 2 — Marcadores plantados** → *pausada, não abandonada* (gabarito sintético; BFSS validado aqui).
  - **Fase 3 — Plano B / PSO sobre coorte bimodal** → *entregue* (o foco de hoje).
- **Visual:** timeline com 3 nós e status colorido (cinza/âmbar/verde). Sem texto longo.
- **Responde a:** *documentar a trajetória; redução de escopo*.

### Slide 4 — Redução de escopo (status de cada componente)
- **Mensagem:** transparência total — o que caiu, o que ficou, o que está planejado.
- **Conteúdo (tabela enxuta):**
  | Componente | Status |
  |---|---|
  | 130-US + CTGAN | Abandonado |
  | PSO sobre coorte bimodal (Plano B) | **Entregue** |
  | Meta-FSS (hiperparâmetros do PSO) | Entregue |
  | Visualização HTML do PSO | Entregue |
  | Banco sintético de marcadores | Concluído |
  | BFSS (seleção de variáveis) | Validado |
  | MOPSO + NSGA-II (frente de Pareto) | Planejado |
- **Visual:** tabela de 2 colunas, badges de status. **Negrito só no Plano B.**
- **Responde a:** *redução de escopo; limitações*.

### Slide 5 — Objetivo: original → adaptado
- **Mensagem:** o objetivo foi **adaptado** com o orientador, mantendo a espinha de enxame.
- **Conteúdo (lado a lado):**
  - *Original (Plano A):* otimizador multiobjetivo (HLY × Custo × Equidade), frente de Pareto.
  - *Adaptado (Plano B):* usar **PSO** para achar o perfil do "indivíduo ideal" entre
    diabéticos, otimizando os **pesos de uma regressão logística** sobre a variável
    **Wellness** (proxy de HLY), e **validar** contra a solução analítica do scikit-learn.
- **Visual:** duas colunas "Antes / Agora"; seta de transição. Nota de rodapé de honestidade:
  *"A base é testbed; o entregável é o otimizador."*
- **Responde a:** *objetivo adaptado*.

### Slide 6 — A variável dependente: Wellness
- **Mensagem:** por que **Wellness** e não um rótulo clínico direto.
- **Conteúdo:**
  - A base é um **snapshot transversal**, sem rótulo "saudável vs. doente" e sem trajetória longitudinal.
  - **Wellness** = terço superior de `z(idade) − z(HbA1c) − z(nº comorbidades)`.
  - **Conexão com HLY:** ausência de complicações + controle metabólico = pilares dos Anos de Vida Saudáveis.
  - Tabela de grupos: ideais = 119 · demais = 238 · total (DM==1) = 357.
- **Visual:** a fórmula em destaque (tipografia matemática), + mini-tabela dos 3 grupos.
- **Responde a:** *explicar que a variável dependente é Wellness*.

### Slide 7 — Passo a passo da solução (Plano B)
- **Mensagem:** da base bruta ao perfil do ideal, em 9 passos reprodutíveis.
- **Conteúdo (fluxo numerado):**
  1. Carregar & filtrar (CSV 5.922×190 → DM==1 → 357)
  2. Construir Wellness (rótulo 0/1)
  3. Selecionar 26 features (proxies; imputar mediana; z-score)
  4. Função de fitness = −(log-loss + L2)
  5. Executar PSO (27D; w=0,7; c1=c2=1,5; gbest = ótimo)
  6. Validar (70/30; cosseno PSO×sklearn = 1,000)
  7. Meta-FSS (hiperparâmetros; AUC cross-val 3 folds)
  8. Perfil do ideal (rank por |peso|; sinal = direção clínica)
  9. Visualizar (HTML, 3 abas, enxame animado)
- **Visual:** fluxograma horizontal em 9 caixas, agrupadas em 3 blocos
  (Preparação · Otimização · Interpretação). Sem ícones cartunescos.
- **Responde a:** *documentar passo a passo; passo a passo até o resultado final*.

### Slide 8 — Por que PSO (enxame) e não algoritmo evolucionário
- **Mensagem:** PSO é a escolha **natural** para este problema, não conveniência.
- **Conteúdo (argumento técnico — o ponto-chave):**
  - **Terreno do problema:** os pesos da logística vivem em **espaço contínuo de alta
    dimensão (27D)** e a perda é **convexa**. Esse é o terreno natural do PSO: ele
    **desliza no contínuo com momento** e converge rápido para o ótimo. GAs exigem
    crossover/mutação, menos intuitivos para pesos reais.
  - **Alinhamento com o enunciado:** a disciplina avalia Inteligência de Enxames;
    PSO é o algoritmo canônico, e a família FSS é o fio condutor do projeto.
  - **Interpretabilidade:** PSO entrega direto um **vetor de pesos** (magnitude =
    importância, sinal = direção clínica); genoma binário de GA obscureceria isso.
  - **Validação elegante:** num problema convexo, existe **ótimo conhecido** → dá para
    provar que o otimizador chegou nele (cosseno = 1,000). Demonstração limpa e didática.
- **Visual:** 4 quadrantes (Terreno · Enunciado · Interpretabilidade · Validação).
- **Responde a:** *por que swarm em vez de evolucionária*.

### Slide 9 — Validação: o otimizador acha o ótimo conhecido  ← *o argumento central*
- **Mensagem:** a prova de que o PSO funciona — não é "deu 0,66", é "achou o ótimo".
- **Conteúdo:**
  - Métricas honestas: AUC treino = 0,820 · AUC teste = 0,664 · **AUC sklearn = 0,664**.
  - **Cosseno(pesos PSO, pesos sklearn) = 1,000** → o PSO encontrou **exatamente** a
    mesma solução do otimizador analítico. Diferença treino/teste controlada por L2.
  - Enquadramento: *"Para uma demonstração de validação, PSO num problema convexo é
    limpo e didático — o otimizador acha o ótimo conhecido."*
- **Visual:** curva de convergência do PSO (`resultados_convergencia_pso.png`) +
  o número **1,000** em destaque. Deixar claro: AUC = qualidade do problema; cosseno = prova do otimizador.
- **Responde a:** *deixar mais explícito o ganho (parte 1: validação)*.

### Slide 10 — Ganho: o perfil do indivíduo ideal  ← *ganho explícito*
- **Mensagem:** o que **descobrimos** — um conjunto de características conhecidas do diabético ideal.
- **Conteúdo:**
  - Top features por |peso| (do `RESULTADOS.md`): CP2h +0,338 · BMI −0,304 · BUN +0,240 ·
    waist1 −0,232 · ISIGutt −0,212 · WHR −0,193 · SCRE +0,162 · ALT −0,134 · HomaIR −0,115 · FatherDM −0,119.
  - **Perfil-síntese:** diabético mais **magro**, com **menor resistência à insulina**,
    **função hepática preservada** (ALT↓) e **sem histórico familiar** de DM.
  - Médias comparativas (ideais vs demais) confirmam: BMI 21,4 vs 24,8; ISIGutt 57,3 vs 104,8; ALT 33,4 vs 45,7.
- **Visual:** barra horizontal divergente (pesos +/−, ordenada por magnitude) +
  caixa "Perfil-síntese". Usar `resultados_importancia.png` como base.
- **Responde a:** *deixar mais explícito o ganho; conjunto de características ideais conhecidas*.

### Slide 11 — BFSS, de relance (plano principal, em andamento)
- **Mensagem:** o plano principal segue vivo; valida o otimizador por marcadores plantados.
- **Conteúdo (um slide, sem aprofundar):**
  - Ideia: base sintética com **gabarito** (verdade-base plantada) → prova **algorítmica**
    de que o otimizador recupera o sinal (não é alegação clínica).
  - Status: **BFSS validado** (recuperou 8 de 9 marcadores; R² subiu com as variáveis selecionadas).
  - Próximo: MOPSO discreto + NSGA-II para a frente de Pareto.
- **Visual:** um único bloco compacto; **sem** painel de métricas grande. É contexto, não resultado do dia.
- **Responde a:** *passar de relance no BFSS (orientador)*.

### Slide 12 — Limitações declaradas
- **Mensagem:** sabemos exatamente onde a entrega não vai — e dizemos.
- **Conteúdo (lista honesta):**
  - Base **não distingue T1D/T2D** → "diabetes tipo não especificado"; é **testbed**, não evidência clínica.
  - Coorte **única e transversal** (China, 2012) → fala de **associação, não causalidade**.
  - Rótulo "ideal" é **escolha de projeto** defensável, não a única.
  - 26 preditoras **curadas à mão** → podem ter omitido pistas.
  - Imputação pela mediana **achata** a variação; corte do terço (33%) é limiar arbitrário.
  - L2 (λ=0,05) calibrado empiricamente, não por cross-validation formal.
- **Visual:** lista de duas colunas, sóbria. Sem ícones de alerta dramáticos.
- **Responde a:** *limitações*.

### Slide 13 — Próximos passos e conclusão
- **Mensagem:** trajetória coerente; entrega sólida; caminho claro à frente.
- **Conteúdo:**
  - Próximo: frente de Pareto (MOPSO discreto + NSGA-II), ~540 políticas com gabarito por enumeração.
  - Fecho: *"PSO validado (cosseno 1,000) + perfil interpretável = otimizador funciona.
    Plano A continua como horizonte multiobjetivo."*
  - Conexão Plano B → BFSS → Simulador HLY → MOPSO.
- **Visual:** mini-pipeline integrado de uma linha + frase de fecho.

---

## 4. Mapa: pedidos do orientador → onde são respondidos

| Pedido | Slide(s) |
|---|---|
| Passo a passo até o resultado final | 7 |
| Limitações | 12 |
| Redução de escopo | 3, 4 |
| Deixar mais explícito o ganho | 9 (validação) + 10 (perfil) |
| Por que swarm em vez de evolucionária | 8 |
| Objetivo adaptado | 5 |
| Documentar passo a passo | 7 |
| Conjunto de características ideais conhecidas | 10 |
| Explicar que a variável dependente é Wellness | 6 |
| PSO em problema convexo = validação limpa | 8 + 9 |
| Mostrar trajetória, focar no Plano B, BFSS de relance | 3 (trajetória) · 5–10 (foco Plano B) · 11 (BFSS de relance) |

---

## 5. Sistema de design (sóbrio, acadêmico, sem AI slop)

**Princípio:** parecer um artigo/seminário bem produzido, não um deck de marketing.
Menos é mais — espaço em branco, hierarquia clara, um dado por slide.

- **Paleta:** base neutra (branco/cinza-grafite #2B2B2B para texto) + **uma** cor de
  acento institucional (azul-petróleo ~#1F4E5F ou verde-escuro). Status: cinza
  (abandonado), âmbar (em curso), verde sóbrio (entregue). Nada de gradientes vibrantes.
- **Tipografia:** uma serifada para títulos (ex.: *Source Serif / Lora*) + uma
  sem-serifa para corpo e dados (ex.: *Inter / Source Sans*). Números em fonte tabular.
  Máx. 2 famílias. Tamanho de corpo ≥ 18 pt.
- **Layout:** grid de 12 colunas, margens generosas, um filete fino sob o título.
  Numeração de slide discreta no rodapé. Logo/disciplina pequenos e fixos.
- **Gráficos:** matplotlib limpo — sem fundo cinza, sem 3D decorativo, sem legendas
  redundantes. Reaproveitar `resultados_convergencia_pso.png` e `resultados_importancia.png`,
  reestilizados para a paleta. Barras divergentes para pesos +/−.
- **Densidade:** ≤ 5 bullets por slide; uma ideia-âncora por tela. Evitar parágrafos.
- **Proibido (AI slop):** ícones genéricos coloridos em excesso, emojis, sombras
  pesadas, clip-art, gradientes arco-íris, "🚀/✨", títulos sensacionalistas.
- **Ferramenta sugerida:** LaTeX Beamer (tema metropolis sóbrio) ou PowerPoint/Google
  Slides com master único. Consistência de master > criatividade por slide.

---

## 6. Contagem e ritmo

- **14 telas** (capa + 13). Alvo: ~12–15 min + perguntas.
- Tempo por bloco: trajetória/escopo ~3 min · Plano B (5–10) ~7 min ·
  BFSS de relance ~1 min · limitações/futuro ~2 min.
- Slides 8 e 9 são o **clímax técnico** — ensaiar bem a fala do "ótimo conhecido / cosseno 1,000".
