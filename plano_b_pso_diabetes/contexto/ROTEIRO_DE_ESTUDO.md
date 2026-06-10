# Roteiro de estudo — entender o projeto ponto a ponto

> Objetivo: dominar a pipeline inteira, do dado cru até a animação no navegador.
> Marque `[x]` cada ponto conforme entender. Cada item aponta o **arquivo:linha** pra você
> acompanhar no código, e o que se espera entender ali. Vá perguntando — a gente discute item a item.

São **dois arquivos**:
- `pso_diabetes.py` → o trabalho científico de verdade (o "treino").
- `gerar_visualizacao.py` → monta o HTML (apresentação + simulação visual).

---

## PARTE A — O treino de verdade (`pso_diabetes.py`)

### Fase 1 — Os dados
- [ ] **1.1** Carregar a base e ficar só com diabéticos. `carregar_diabeticos()` — linhas 42–49.
      (lê o CSV, filtra `DM==1` → 357 pessoas, converte tudo pra número.)
- [ ] **1.2** Por que `encoding="latin-1"` e por que vazios viram `NaN`. — linhas 43, 46–47.

### Fase 2 — O rótulo: o que é "indivíduo ideal"
- [ ] **2.1** A nota de "bem-estar" = `z(idade) − z(HbA1c) − z(nº comorbidades)`. `construir_rotulo()` — linhas 57–71.
- [ ] **2.2** O que é o z-score (padronização) e por que usar. `zscore()` — linhas 52–54.
- [ ] **2.3** Por que o corte é o **terço superior** (`quantile(2/3)`) → vira rótulo 0/1. — linhas 65–66.
- [ ] **2.4** Quais variáveis formam o rótulo (idade, HbA1c, hipertensão, dislipidemia). `LABEL_COLS` — linha 30.

### Fase 3 — As características preditoras (o que o PSO pode usar)
- [ ] **3.1** A lista de candidatas (antropometria, insulina, enzimas, histórico…). `CANDIDATAS` — linhas 36–39.
- [ ] **3.2** Por que tirar fora os "proxies" de glicose/lipídio/PA (evitar circularidade). `PROXY_EXCLUDE` — linhas 32–34.
- [ ] **3.3** Limpeza: descartar coluna com >25% de vazios, imputar mediana, padronizar. `selecionar_preditoras()` — linhas 74–83.

### Fase 4 — A "nota" de uma resposta (função de fitness)
- [ ] **4.1** A sigmoide: transforma um número em probabilidade 0–1. `sigmoid()` — linhas 89–90.
- [ ] **4.2** O fitness = `−(log-loss + L2)`. O que é log-loss (erro) e por que o sinal de menos. `fitness()` — linhas 98–103.
- [ ] **4.3** O que é a regularização L2 (`LAMBDA`) e por que ela segura os pesos. — linhas 86, 103.
- [ ] **4.4** O que é AUC e como medimos. `auc_pesos()` — linhas 93–95.

### Fase 5 — O PSO (o enxame procurando os pesos)
- [ ] **5.1** Cada partícula = um vetor de pesos (posição); 27 dimensões (26 + bias). `pso()` início — linhas 106–115.
- [ ] **5.2** A regra de atualização: inércia + puxão pessoal (pbest) + puxão social (gbest). — linhas 118–121.
- [ ] **5.3** Atualizar pbest e gbest a cada iteração. — linhas 123–126.
- [ ] **5.4** Os parâmetros `w_in=0.7, c1=1.5, c2=1.5` e o limite `[-4,4]`. — linhas 109, 116.
- [ ] **5.5** O histórico de AUC por iteração (vira o gráfico de convergência). — linha 127.

### Fase 6 — Treino × teste e validação
- [ ] **6.1** Separar 70% treino / 30% teste (e por quê). `train_test_split` — linha 138.
- [ ] **6.2** Rodar o PSO só no treino; medir AUC no treino e no teste. — linhas 141–144.
- [ ] **6.3** Baseline analítico do sklearn (a "resposta certa" conhecida). — linhas 146–152.
- [ ] **6.4** O cosseno entre pesos PSO × sklearn (≈1,000 = mesma direção = PSO validado). — linha 151.

### Fase 7 — Saídas (o que o treino produz)
- [ ] **7.1** Ranking dos pesos = o perfil do indivíduo ideal. — linhas 156–163.
- [ ] **7.2** Perfil descritivo: média ideais × demais. — linhas 165–171.
- [ ] **7.3** Os 2 gráficos (convergência e importância) e o `../RESULTADOS.md`. `salvar_saidas()` — linhas 177–215.

---

## PARTE B — O visualizador (`gerar_visualizacao.py`)

### Fase 8 — O relevo de fundo da simulação
- [ ] **8.1** Por que o relevo só pode ter 2 eixos: congelamos 25 pesos e variamos só 2. (no `main()`, o laço que monta `Z` a partir de `w2 = wstar.copy()`).
- [ ] **8.2** `fitness_full()` = a mesma nota de antes, mas no formato contínuo da fatia. — função no topo.
- [ ] **8.3** Como escolho **quais 2 características** mostrar (as 4 de maior peso). `ordem = argsort(-|wstar|)`.
- [ ] **8.4** A "descentralização": a moldura é deslocada pra ⭐ não ficar no centro. `fracs` + `linspace`.
- [ ] **8.5** O grid `Z[a][b]`: varro uma malha 60×60 de pesos e calculo a nota de cada ponto.

### Fase 9 — Montagem do HTML
- [ ] **9.1** Rodar o PSO real aqui também só pra pegar os números exatos da apresentação. `main()`.
- [ ] **9.2** Embutir os 2 PNGs em base64 (HTML autocontido, sem arquivos soltos). `b64()`.
- [ ] **9.3** Como a aba Apresentação é montada a partir dos resultados. `montar_apresentacao()`.
- [ ] **9.4** Os placeholders `/*DATA*/` e `<!--APRES-->` sendo substituídos no `TEMPLATE`.

### Fase 10 — A simulação no navegador (o JavaScript dentro do `TEMPLATE`)
- [ ] **10.1** O `DATA` injetado: o grid `Z`, limites, posição da ⭐. (início do `<script>`)
- [ ] **10.2** Desenhar o relevo: `buildHeat()` pinta cada célula do grid com uma cor por nota.
- [ ] **10.3** `fit(x,y)`: como a partícula descobre a nota num ponto qualquer (interpolação bilinear).
- [ ] **10.4** `reset()`: nascer N partículas aleatórias, dar cor (hue) a cada uma, achar o 1º gbest.
- [ ] **10.5** `stepOnce()`: o passo do PSO no navegador (mesma fórmula da Fase 5) + limite `vmax`.
- [ ] **10.6** `animate()` + `draw()`: suavização do movimento (easing), rastros que desbotam, brilho.
- [ ] **10.7** `loop()` + o acumulador de velocidade (`SPF`): como controlar passos-por-frame.
- [ ] **10.8** O menu de abas: `show('apres'|'sim')` alternando as duas `<section>`.

---

## Como usar este roteiro

Escolha um item (ex.: "me explica o 5.2") e a gente destrincha. Quando sentir que dominou,
marque `[x]`. No fim, você consegue explicar o projeto inteiro do zero.
