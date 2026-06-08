# Estratégias para Aumento de AUC

Este documento registra os três principais caminhos identificados para melhorar a AUC (poder preditivo) do modelo de regressão logística otimizado por PSO, mantendo a interpretabilidade do perfil clínico.

## 1. Seleção de Features via BFSS (O caminho mais promissor)
O modelo atual utiliza todas as 26 features candidatas. Em regressões logísticas, features irrelevantes ou altamente correlacionadas adicionam ruído, confundindo o hiperplano de separação e causando overfitting (reduzindo a AUC de teste).

* **Ação:** Implementar uma camada de seleção de atributos utilizando o algoritmo **BFSS (Binary Fish School Search)**.
* **Mecânica:** Cada "peixe" no BFSS representaria um vetor de 26 bits (1 = inclui a feature, 0 = exclui). O fitness do peixe seria a AUC obtida treinando o PSO apenas com aquele subset de features.
* **Impacto:** Alto. Reduzir o ruído é historicamente a técnica que mais traz ganhos diretos em dados de saúde, além de adicionar um forte diferencial acadêmico (uso de BFSS no domínio correto).

## 2. Tratamento do Desbalanceamento de Classes
O dataset é desbalanceado (proporção aproximada de 1:2 entre classe "ideal" e "demais"). A função atual de *fitness* (logloss padrão) pune os erros igualmente, o que estatisticamente puxa o modelo para focar em prever a classe majoritária, prejudicando a sensibilidade para os indivíduos ideais.

* **Ação:** Alterar a função `fitness_pso` para equilibrar a punição.
* **Mecânica:** 
  * Utilizar um **Logloss Ponderado**, onde os erros ao classificar um "indivíduo ideal" recebem um peso maior (ex: peso 2).
  * Alternativamente, adotar o **Focal Loss**, que foca o treinamento nos exemplos difíceis de classificar.
* **Impacto:** Médio/Alto. O modelo passará a errar menos na classe minoritária, melhorando as métricas de sensibilidade e a curva ROC/AUC global.

## 3. Engenharia de Features (Feature Engineering)
A Regressão Logística baseia-se num hiperplano linear. Se a relação biológica entre uma variável (ex: IMC) e o status de saúde não for linear, o modelo não consegue capturá-la.

* **Ação:** Criar novas features a partir da base existente para ajudar o modelo a encontrar as relações ocultas.
* **Mecânica:**
  * **Features polinomiais:** Utilizar a versão ao quadrado de certas variáveis contínuas.
  * **Interações:** Criar produtos entre features fortemente correlacionadas (ex: `Gordura * Idade`).
  * **Agrupamentos/Binarização:** Basear-se em limites clínicos reais para criar flags categóricas (ex: IMC > 30 = 1).
* **Impacto:** Médio. Ajuda o modelo linear a emular fronteiras de decisão não-lineares.
