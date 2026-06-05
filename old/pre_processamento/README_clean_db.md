# Processo de Limpeza e Preparação de Dados (REDS-DM1)

Este diretório contém os scripts e documentos de documentação para realizar o pré-processamento e a limpeza da base de dados original do projeto (`banco/reds_dm1.db`), resultando em uma base otimizada (`banco/reds_dm1_clean.db`) pronta para o algoritmo de seleção de variáveis **BFSS** e modelagem do simulador.

---

## 1. Arquivos Contidos neste Diretório

*   **`clean_database.py`**: O script Python responsável por realizar a limpeza, remover variáveis ruidosas, e gerar a base de modelagem final com caminhos relativos robustos.
*   **`count_columns.py`**: Um utilitário de suporte para contar colunas e inspecionar a estrutura física do banco limpo resultante.
*   **`criterios_limpeza.md`**: O documento teórico detalhado explicando quais colunas foram excluídas (administrativas, TI, privacidade, chaves técnicas) e quais foram mantidas (clínicas, demográficas) e sua respectiva justificativa.
*   **`README_clean_db.md`**: Este arquivo de visão geral.

---

## 2. Estrutura do Conjunto de Dados de Modelagem (`MODEL_DATASET`)

A tabela final consolidada de modelagem (`MODEL_DATASET`) possui cerca de **40 colunas** (dinâmico baseado nas extrações de medicações) e reúne dados demográficos, clínicos, de exames e medicamentos por atendimento (internação):

| Coluna | Descrição |
| :--- | :--- |
| `ID_ATEND` | Identificador único da internação (chave primária da linha). |
| `ID_PACIEN` | Identificador do paciente associado. |
| `NU_IDADE` | Idade do paciente no momento do atendimento. |
| `IN_SEXO` | Gênero (`M` ou `F`). |
| `NM_MUNIC` | Município de residência em Pernambuco (para equidade/distribuição). |
| `DS_RACA` | Etnia autoidentificada (padrão SUS). |
| `DS_TIPO_ATEND` | Tipo de admissão (`E` para Emergência, `I` para Internação, `APS` para Atenção Primária). |
| `DS_ESPECI` | Especialidade médica responsável. |
| `TEMPO_INTERNACAO_DIAS` | Tempo total de internação (em dias). Representa o custo e complexidade do caso. |
| `DS_COR_RISCO` | Cor de prioridade de urgência Manchester. |
| `DS_CLASSIF_RISCO` | Grau de gravidade clínico. |
| `EXAME_HBA1C` | Resultado da HbA1c em valor numérico real. |
| `MED_[NOME_DO_FARMACO]` | Múltiplas colunas binárias (0 ou 1) representando os **23 medicamentos** mapeados da base (ex: MED_METFORMINA, MED_ACARBOSE, MED_PIOGLITAZONA) para uso pelo BFSS sem viés. |
| `IS_RENAL` | Flag binária (0 ou 1): Diagnóstico associado a doença renal crônica (`N18`). |
| `IS_CARDIOVASCULAR` | Flag binária (0 ou 1): Diagnóstico de cardiopatias/hipertensão (`I21`, `I50`, `I10`, `I64`). |
| `FL_OBITO` | Flag binária (0 ou 1): Atendimento encerrou em óbito (target / gravidade máxima). |

---

## 3. Como Executar

Os scripts de pré-processamento resolvem os caminhos relativos ao projeto de forma automática. 

Para limpar a base de dados original e gerar o novo banco SQLite:
```powershell
python pre_processamento/clean_database.py
```

Para listar a quantidade de colunas e campos de cada tabela gerada:
```powershell
python pre_processamento/count_columns.py
```
