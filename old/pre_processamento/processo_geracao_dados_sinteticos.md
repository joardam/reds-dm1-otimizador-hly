# Processo de Geração de Dados Clínicos Sintéticos (REDS-DM1)

Este documento detalha o funcionamento, as regras de negócio e a arquitetura do motor híbrido utilizado para gerar o banco de dados relacional sintético **`reds_dm1.db`**. A base foi gerada para simular a realidade epidemiológica e gerencial da Rede Estadual de Dados em Saúde de Pernambuco (REDS-PE) para pacientes com **Diabetes Mellitus Tipo 1 (DM1)**.

---

## 1. Arquitetura do Motor Híbrido

A geração de dados sintéticos fidedignos em saúde exige que os dados não sejam apenas aleatórios, mas que respeitem correlações biológicas reais (relação entre medicamentos, exames e comorbidades) e regras organizacionais do SUS. Por isso, adotou-se uma abordagem **híbrida**:

```
[ Dataset Clínico Base: Kaggle 130-US ] ───► Aprendizado Generativo de Padrões (CTGAN/SDV - Nuvem)
                                                        │
                                                        ▼
[ Pacientes Sintéticos (Perfil Baseline) ] ──► Fusão de Dados e Tradução Clínica (Máquina Local)
                                                        │
                                                        ▼
[ Regras e Pesos Demográficos (IBGE-PE) ] ──► Regionalização em Pernambuco (Cidades e GERES)
                                                        │
                                                        ▼
[ Protocolos de Saúde do SUS ] ─────────────► Triagem Manchester e ImunizaçõesDATAsus
                                                        │
                                                        ▼
[ Validador de Integridade e Cronologia ] ──► Consistência Temporal (Nascimento < Admissão)
                                                        │
                                                        ▼
[ Banco de Dados Relacional SQLite ] ────────► reds_dm1.db (Pronto para o BFSS)
```

---

## 2. Etapas de Processamento dos Dados

### Etapa 1: Consolidação da Relação 1:N
O dataset de referência original do Kaggle contêm registros de internações onde um mesmo paciente pode aparecer em várias linhas. 
* **Ação:** O script agrupa os dados por `patient_nbr` (ID único do paciente no Kaggle).
* **Estruturação:**
  * As informações demográficas estáticas (sexo, raça, faixa etária) geram um único registro na tabela **`PACIENTE`**.
  * Cada internação individual associada a esse paciente é desmembrada em uma linha na tabela **`ATENDIMENTO`**.
  * Chaves primárias e estrangeiras auto-incrementais são geradas para garantir a integridade referencial.

### Etapa 2: Localização e Demografia (IBGE-PE)
Para nacionalizar a base e simular Pernambuco:
* **Municípios:** O script consulta a API de Localidades do IBGE para coletar os 184 municípios do estado.
* **Pesos Populacionais:** Foi mapeado um dicionário com pesos demográficos para as cidades polo (Recife, Jaboatão, Olinda, Caruaru, Petrolina, Paulista, etc.). Cidades com maior população têm maior probabilidade de serem sorteadas como residência do paciente sintético (`NM_MUNIC`), refletindo a distribuição demográfica real de Pernambuco.

### Etapa 3: Tradução Clínica e Mapeamentos SUS

#### A. Diagnósticos (ICD-9 para CID-10)
O dataset do Kaggle utiliza códigos ICD-9 (formato norte-americano antigo) para os três principais diagnósticos registrados (`diag_1`, `diag_2`, `diag_3`). O SUS utiliza o padrão CID-10.
* **Diabetes (250.xx):** Mapeado para o código **`E10.9`** (Diabetes Mellitus Tipo 1 sem complicações) se a idade do paciente for $\le 30$ anos, aumentando a coerência fisiológica do DM1 infanto-juvenil. Para idades mais avançadas, mapeia-se para `E11.9` (DM Tipo 2).
* **Nefropatia e Insuficiência Renal (580-589):** Mapeados para o código **`N18.9`** (Insuficiência renal crônica).
* **Doenças Circulatórias (390-459):** Mapeados para códigos da faixa **`I00-I99`** (ex: `I21.9` para infarto, `I50.9` para insuficiência cardíaca e `I10` para hipertensão).

#### B. Resultados de HbA1c (Categórico para Numérico Decimal)
No Kaggle, a Hemoglobina Glicada (`A1Cresult`) é descrita apenas de forma qualitativa: `Normal`, `>7`, `>8` ou `None` (não realizado). Para a tabela `RES_EXAME.DS_RESULTADO` do SUS, precisamos de valores contínuos realistas.
* **Ação:** O gerador aplica amostragens baseadas em **distribuição normal truncada** para gerar valores decimais plausíveis:
  * Se `A1Cresult` for `Normal` $\rightarrow$ Gera valores entre `4.0%` e `5.6%` ($\mu = 5.0$, $\sigma = 0.4$).
  * Se `A1Cresult` for `>7` $\rightarrow$ Gera valores entre `7.1%` e `8.0%` ($\mu = 7.5$, $\sigma = 0.3$).
  * Se `A1Cresult` for `>8` $\rightarrow$ Gera valores entre `8.1%` e `15.0%` ($\mu = 9.8$, $\sigma = 1.5$).
  * Se `A1Cresult` for `None` $\rightarrow$ Simula exames de rotina regulares (entre `5.7%` e `7.0%`) em 20% dos casos ou deixa em branco.

#### C. Medicamentos (EUA para RENAME/SUS) - Expansão BFSS
Para evitar **Viés de Seleção (Selection Bias)** antes de rodar o modelo de feature selection (BFSS), as colunas de medicamentos do Kaggle foram **integralmente mapeadas** para a RENAME. Antes, o script restringia a geração a apenas 4 medicamentos clássicos, ocultando as demais opções do BFSS. Agora, a IA aprende e o script exporta **23 variações**, incluindo:
* `metformin` $\rightarrow$ **Cloridrato de Metformina (850mg)** (Via Oral).
* `insulin` $\rightarrow$ **Insulina Humana (NPH/Regular)** (Subcutânea).
* `glipizide` / `glyburide` $\rightarrow$ **Glibenclamida** e **Glipizida**.
* `pioglitazone`, `acarbose`, `repaglinide`, etc. $\rightarrow$ Mapeados para seus respectivos análogos RENAME.
* **Lógica:** Se a coluna no Kaggle/Modelo Sintético for `No`, nenhum registro de receita é criado. Se for `Steady`, `Up` ou `Down`, um registro em `PRESCRICAO_MEDICAMENTO` é criado com instruções de dose realistas do SUS (ex: *"Aplicar 10 UI pela manhã"*). Todos os 23 medicamentos são consolidados na tabela plana `MODEL_DATASET` para que o BFSS descubra matematicamente sua relevância.

#### D. Protocolo de Triagem de Manchester
Como o dataset do Kaggle possui a gravidade da admissão hospitalar (`admission_type_id`), o motor mapeia essas prioridades para as cores e descrições do Protocolo de Triagem de Manchester brasileiro na tabela `ACOLHIMENTO`:
* `Emergency` (ID 1) $\rightarrow$ Risco **Vermelho** ou **Laranja** (Urgência máxima/risco de morte).
* `Urgent` (ID 2) $\rightarrow$ Risco **Amarelo** (Urgência moderada).
* `Elective` (ID 3) $\rightarrow$ Risco **Verde** ou **Azul** (Pouco urgente/Não urgente).

#### E. Registro de Imunização DATASUS
Como pacientes com DM1 são considerados prioritários no calendário de vacinação do SUS, o gerador simula um histórico de imunizações na tabela `IMUNIZACAO` para cerca de 30% dos pacientes da base:
* São geradas aplicações realistas de **Vacina Influenza Triovalente** e **Vacina Pneumocócica 23-valente**, com datas epidemiologicamente corretas.

---

## 3. Validador de Integridade e Regras Temporais

Para impedir a ocorrência de dados inconsistentes que invalidem a simulação biológica, o gerador passa os dados por um módulo validador de restrições temporais e lógicas:

1. **Restrição Temporal:** Garante que a linha do tempo do paciente seja causalmente correta:
   $$\text{Data de Nascimento} < \text{Data de Vacinação} < \text{Data de Triagem (Manchester)} \le \text{Data de Admissão} \le \text{Data de Alta/Óbito}$$
2. **Consistência de Óbito:** Se um paciente tem a flag `FL_OBITO = 1`, o óbito deve ocorrer na data exata de fim da sua última internação (`DT_MOMENT_FIM` em `ATENDIMENTO`), e sua data de óbito (`DT_OBITO`) é registrada na tabela `PACIENTE`.
3. **Casamento de Chaves:** Chaves estrangeiras (`ID_PACIEN`, `ID_ATEND`, `ID_PROFIS`, `ID_UNID`) são validadas de forma estrita para evitar registros órfãos.

---

## 4. Otimização de Desempenho Local

Para que a base sintética com 15.000 linhas seja gerada em **segundos** em um computador pessoal, o código segue duas diretrizes:
* **Vetorização no Pandas:** Mapeamentos complexos (como faixas etárias para datas de nascimento ou cidades por pesos) são calculados em lote usando operações vetorizadas do Numpy e Pandas, evitando laços de repetição lentos.
* **Escrita com Executemany:** O banco de dados SQLite é populado utilizando inserções em lote (`executemany` do sqlite3) em vez de conexões individuais por linha, o que reduz o gargalo de escrita em disco (I/O).
