# Relatório do Projeto: Otimização PSO e Meta-FSS (Diabetes)

Este relatório resume a arquitetura, lógica e histórico de desenvolvimento contidos na pasta `plano_b_pso_diabetes`.

## 1. Visão Geral e Objetivo
O objetivo do projeto é utilizar algoritmos de Inteligência de Enxames (Swarm Intelligence) para criar um **perfil interpretável do indivíduo ideal** (saudável) a partir de um banco de dados clínico de pacientes diabéticos. 

A abordagem escolhida foge das tradicionais "caixas-pretas": utilizamos a otimização matemática para ajustar os pesos de uma Regressão Logística. Com isso, os pesos finais indicam diretamente a importância e a direção clínica (positivo/negativo) de cada uma das 26 características biológicas selecionadas.

---

## 2. O Contexto do "Plano B" e Dados
A pasta `plano_b_pso_diabetes` nasceu como uma alternativa (Plano B) ao uso de bibliotecas fechadas de Machine Learning (como Scikit-Learn) ou algoritmos tradicionais de otimização (L-BFGS). Em vez de usar gradientes descendentes matematicamente exatos, o projeto propõe implementar um **algoritmo populacional (PSO)** construído "do zero" em Numpy para buscar os pesos ideais.
* **Dados Utilizados:** Os dados são lidos diretamente do arquivo `DM1_dados_processados.csv`. Antes de iniciar a modelagem, as variáveis sofrem normalização rigorosa (z-score) para garantir que variáveis com escalas diferentes (ex: Idade vs Função Hepática) não enviesem os pesos do PSO durante a regularização.

---

## 3. Lógica e Arquitetura Principal

### O Alvo (A "Função de Wellness")
Como o banco de dados original não possui um rótulo binário perfeito de "saudável vs doente", o projeto cria um proxy numérico chamado **Wellness** (bem-estar).
* É calculado agregando variáveis indicadoras de desfechos negativos: `zscore(Idade) - zscore(HbA1c) - zscore(Comorbidades)`.
* Pacientes no terço superior desta métrica são rotulados como a classe alvo (indivíduos "ideais").

### Nível Base: PSO (Particle Swarm Optimization)
Arquivo: `pso_diabetes.py`
* **Partículas:** Representam um vetor de pesos para a regressão logística (um peso por variável clínica + viés).
* **Função Objetivo (Fitness):** Minimizar a **perda logarítmica (logloss)** da regressão penalizada por uma regularização **L2** (para evitar pesos gigantescos).
* **Saída:** O melhor vetor de pesos global (gbest), que dita o modelo de classificação e o perfil de "importância" das features.

### Meta-Nível: FSS (Fish School Search)
Arquivo: `meta_fss_pso/meta_fss_pso.py`
Para garantir que o PSO não estava preso em parâmetros arbitrários, implementamos uma meta-heurística. O FSS foi escolhido para procurar os melhores **hiperparâmetros** para o PSO base.
* **Peixes:** Cada peixe é um vetor 4D contendo os hiperparâmetros `[w_in (inércia), c1 (atração cognitiva), c2 (atração social), lam (taxa de regularização)]`.
* **Avaliação:** Um peixe é avaliado rodando um PSO interno leve com *Cross-Validation* de 3 folds. O *fitness* do peixe é a métrica AUC média no conjunto de validação.
* **Resultado:** O FSS revelou que hiperparâmetros mais conservadores (menor atração, menor regularização) mantinham estabilidade semelhante ao empirismo inicial.

---

## 4. O Módulo de Visualização Interativa

Arquivo: `gerar_visualizacao.py`
Para comunicar os resultados de forma clara, o projeto conta com um gerador dinâmico de HTML independente de frameworks web. Ele executa os algoritmos, gera os gráficos via `matplotlib`, converte-os para base64 e os injeta num único arquivo portável: **`pso_visualizacao.html`**.

A interface é dividida em 3 abas:
1. **📊 Apresentação:** Exibe o painel estático, os gráficos de convergência da perda e um gráfico de barras com a importância final das variáveis calculadas pelo PSO padrão.
2. **🎮 Simulação Interativa:** Permite navegar por uma superfície de erro 3D usando mapas de calor e ver, na prática, como o "enxame" (representado por pequenas bolinhas) busca o mínimo da função numa projeção em duas variáveis por vez.
3. **⚙️ Hiperparâmetros (FSS):** Integra as saídas visuais geradas pelo script `meta_fss_pso.py`, mostrando a convergência do cardume e validando os resultados originais.
4. **Comparação Direta:** Uma tabela foi programada para parear as 26 variáveis e ranqueá-las, evidenciando se a otimização dos hiperparâmetros alterou a "direção" das features (ex: GGT passou a ser indicativo positivo ou continuou negativo?).

---

## 5. Próximos Passos e Oportunidades

Apesar de robusto na interpretação, a métrica de *AUC (Área Sob a Curva ROC)* no teste possui espaço para crescimento (~0.67). Um documento de registro (`meta_fss_pso/ESTRATEGIAS_AUC.md`) foi criado listando os caminhos técnicos para alavancar essa taxa de acerto. O roteiro priorizado é:
1. **(Prioridade) Tratamento de Classes Desbalanceadas:** Impor *focal loss* ou penalidades logarítmicas assimétricas para corrigir o viés majoritário.
2. **Seleção de Variáveis (BFSS):** Adicionar uma nova camada onde um *Binary Fish School Search* desliga as features irrelevantes do dataset antes do PSO rodar.
3. **Engenharia de Variáveis:** Inserir transformações e interações entre os atributos clínicos.
