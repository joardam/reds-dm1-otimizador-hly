# Critérios de Seleção e Limpeza de Variáveis (REDS-DM1)

Este documento descreve detalhadamente os critérios científicos, clínicos e estatísticos utilizados para filtrar o banco de dados original `reds_dm1.db` (160 colunas brutas) e gerar a base consolidada de modelagem `reds_dm1_clean.db` (com **cerca de 40 colunas**), ideal para a execução do algoritmo **BFSS (sem Selection Bias)** e do simulador de **HLY**.

---

## 1. Critérios de Exclusão (O que foi removido e por quê?)

A eliminação de colunas seguiu critérios rigorosos para evitar **overfitting (sobreajuste)**, violação de privacidade (LGPD) e ineficiência computacional.

### A. Dados Pessoais Identificáveis (Privacidade)
*   **Campos:** `NM_PACIEN` (Nome), `NM_MAE` (Mãe), `NM_SOCIAL` (Nome Social), `CD_CPF` (CPF), `DS_CNS` (CNS/Cartão SUS), `NU_TEL1/2/3` (Telefones), `DS_EMAIL` (E-mail).
*   **Critério:** Não possuem relevância biológica ou epidemiológica. O nome ou e-mail de um paciente não altera sua resposta glicêmica ou complicações do diabetes. Mantê-los faria o modelo de machine learning tentar associar strings de identificação ao prognóstico de óbito.

### B. Metadados e Campos de Auditoria de TI
*   **Campos:** `DT_ATUALZ` (Data de Atualização), `DT_ATUALZ_ORIGEM`, `FL_ANONIMIZADO` (Flag de anonimização), `ID_SISTEM_ORIGEM` (Código do sistema de origem), `IN_SISTEM_ORIGEM`.
*   **Critério:** São variáveis gerenciais do banco de dados relacional para auditoria de sincronização de prontuários do estado. Não trazem nenhuma informação sobre a saúde ou diagnóstico clínico do paciente.

### C. Endereço Físico (Granularidade Excessiva)
*   **Campos:** `DS_TP_LOGRD` (Tipo de rua), `DS_LOGRD` (Rua), `NU_LOGRD` (Número), `DS_COMPL` (Complemento), `NM_BAIRRO` (Bairro), `CD_CEP` (CEP), `SG_UF` (Estado - sempre "PE").
*   **Critério:** Enquanto a cidade de residência (`NM_MUNIC`) é vital para avaliar a equidade na saúde e regionalização do SUS, a rua ou o CEP adicionam um nível de detalhe (dimensionalidade) que apenas gera dados esparsos e ruído estatístico.

### D. Chaves Estrangeiras e IDs Organizacionais
*   **Campos:** `ID_UNID` (Código da Unidade), `ID_PROFIS` (Código do médico/profissional), `CD_CNES` (Código de registro do hospital), `CNPJ_RESPONSAVEL`, `ID_CBO` (Ocupação médica), `TP_FICHA` (Tipo de prontuário), `CD_SOLICITACAO` (Código sequencial do exame).
*   **Critério:** A resposta clínica de um paciente à insulina ou o risco de desenvolver nefropatia depende de parâmetros biológicos e terapêuticos, e não do ID interno do médico que o atendeu ou do CNPJ do hospital no sistema SQL.

### E. Textos Livres e Descrições Redundantes
*   **Campos:** `DS_DIAG` (Texto descrevendo o CID-10), `DS_EXAME` (Texto descrevendo o exame realizado).
*   **Critério:** Já mantemos os códigos padronizados (ex: `CD_DIAG` = `N18.9`). As descrições em formato de texto livre em português geram redundância cognitiva e consomem memória desnecessária para modelos matemáticos.

---

## 2. Critérios de Inclusão (O que foi mantido e por quê?)

Foram preservadas e sintetizadas as variáveis que descrevem a jornada clínica do paciente e influenciam o cálculo de Anos de Vida Saudáveis (HLY):

1.  **Epidemiologia Básica:** 
    *   `NU_IDADE` e `IN_SEXO`: Fatores cruciais na progressão de complicações crônicas do diabetes.
    *   `DS_RACA`: Importante para controle de vulnerabilidades sociais e demográficas no SUS.
    *   `NM_MUNIC`: Garante que o otimizador distribua insumos de forma equitativa geograficamente.
2.  **Gravidade da Admissão (Triagem Manchester):**
    *   `DS_COR_RISCO` e `DS_CLASSIF_RISCO`: Medem o quão agudo/grave era o estado do paciente no acolhimento (Manchester).
3.  **Controle Glicêmico:**
    *   `EXAME_HBA1C`: O principal marcador clínico. O HLY é calibrado diretamente pelas âncoras de HbA1c (T1D Index).
4.  **Terapêutica (Inclusão Completa para Mitigação de Viés):**
    *   **23 Colunas de Medicamentos** (ex: `MED_METFORMINA`, `MED_ACARBOSE`, `MED_PIOGLITAZONA`): Foram mantidas de forma abrangente e dinâmica. Anteriormente, o banco era filtrado para apenas 4 drogas clássicas. A inclusão integral foi uma decisão metodológica para garantir que o **BFSS (Feature Selection)** possua todas as variáveis matemáticas disponíveis para avaliar eficácia (HLY) sem a interferência do viés de seleção humano (Selection Bias).
5.  **Comorbidades / Complicações Agudas:**
    *   `IS_RENAL` (Doença renal baseada no CID-10 `N18`) e `IS_CARDIOVASCULAR` (Cardiopatias baseadas nos CIDs `I21`, `I50`, `I10`, `I64`). O simulador precisa dessas flags para descontar os anos de vida saudáveis por incapacidades.
6.  **Custo/Tempo e Severidade:**
    *   `TEMPO_INTERNACAO_DIAS`: Proxy para custo operacional de internação.
    *   `FL_OBITO`: Desfecho clínico definitivo.
