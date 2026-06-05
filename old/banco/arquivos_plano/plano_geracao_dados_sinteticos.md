# Plano de Geração de Dados Sintéticos Fidedignos (REDS-DM1)

Este documento especifica a estratégia, arquitetura e passos práticos necessários para que um agente autônomo de programação (ou desenvolvedor) construa e popule a base de dados sintética para a **REDS-DM1** (Rede Estadual de Dados em Saúde - Diabetes Mellitus Tipo 1) utilizando o contexto brasileiro (Pernambuco/SUS) e o dataset clínico de referência **Diabetes 130-US Hospitals** (UCI/Kaggle).

---

## 1. Arquitetura da Solução Híbrida

Para garantir a **consistência lógica** (evitar alucinações de dados da IA) e a **fidelidade clínica** (manter correlações biológicas reais), a geração deve seguir uma abordagem **híbrida**:

```
                  [ Dataset Base: Kaggle 130-US ]
                                │
                                ▼
                   [ Motor Clínico Estatístico ]
                   - Gaussian Copula (SDV) ou Regras
                   - Gera: Diagnósticos, Medicamentos, HbA1c
                                │
                                ▼
                 [ Motor de Regras e Localização ]
                 - Regras do SUS (Triagem Manchester)
                 - População do IBGE-PE (Municípios)
                 - Histórico de Vacinas (DATASUS)
                                │
                                ▼
                [ Validador de Integridade Relacional ]
                - Garante FKs consistentes e cronologia
                                │
                                ▼
                  [ Banco de Dados REDS-DM1 ]
```

---

## 2. Passos para Execução do Agente

### Passo 1: Preparação do Ambiente e Coleta de Fontes
O script gerador deve rodar em Python no notebook Lenovo, utilizando as seguintes bibliotecas:
*   `pandas` e `numpy` (Manipulação de dados rápida).
*   `requests` (Para consultar APIs públicas).
*   `sdv` (Synthetic Data Vault, se optar pelo Gaussian Copula para correlações avançadas).

#### Fontes de Dados Necessárias:
1.  **Dataset Clínico:** Baixar o dataset `brandao/diabetes` (Diabetes 130-US Hospitals) do Kaggle. O arquivo principal é o `diabetic_data.csv`.
2.  **Municípios de PE (IBGE):** Consultar a API do IBGE para obter os 184 municípios de Pernambuco.
    *   *Endpoint:* `https://servicodados.ibge.gov.br/api/v1/localidades/estados/PE/municipios`
3.  **População por Município:** Utilizar um dicionário de pesos demográficos baseado no censo para que a distribuição dos pacientes reflita a realidade populacional de Pernambuco.

---

### Passo 2: Limpeza e Preparação do Dataset Base (Kaggle)
Antes de mapear, o script deve tratar os dados originais:
*   **Identificação Única:** O dataset original possui múltiplos registros por paciente. Agrupar por `patient_nbr` para consolidar a tabela `PACIENTE` e separar as internações em `ATENDIMENTO` (relação de 1 para N).
*   **Missing Values:** Valores nulos representados por `?` nas colunas de raça, peso e diagnósticos devem ser normalizados ou imputados.

---

### Passo 3: Mapeamento e Tradução Clínica (Kaggle $\rightarrow$ REDS)

O agente deve implementar as seguintes lógicas de conversão no script:

#### A. Tradução de Diagnósticos (ICD-9 para CID-10)
O dataset do Kaggle usa ICD-9 (formato americano antigo) para os diagnósticos (`diag_1`, `diag_2`, `diag_3`). O SUS usa CID-10.
*   **Ação:** Criar um dicionário de tradução simples para as principais faixas de diabetes e complicações:
    *   Códigos 250.xx (Diabetes Mellitus no ICD-9) $\rightarrow$ Mapear para **E10** (Diabetes Mellitus Tipo 1) ou **E11** (Tipo 2) no CID-10.
    *   Códigos de doenças renais (580-589) $\rightarrow$ Mapear para **N18** (Insuficiência renal crônica).
    *   Códigos de doenças circulatórias (390-459) $\rightarrow$ Mapear para a faixa **I00-I99**.

#### B. Conversão de Exame HbA1c (Categórico para Numérico)
O exame de HbA1c no Kaggle (`A1Cresult`) é qualitativo: `None`, `Normal`, `>7`, `>8`. A tabela `RES_EXAME.DS_RESULTADO` precisa de valores numéricos realistas.
*   **Ação:** Usar amostragem de distribuição normal truncada (`scipy.stats.truncnorm`) para simular o resultado numérico:
    *   Se `A1Cresult == 'Normal'` $\rightarrow$ Gerar valor decimal entre `4.0` e `5.6` (Média = 5.0, DP = 0.4).
    *   Se `A1Cresult == '>7'` $\rightarrow$ Gerar valor decimal entre `7.1` e `8.0` (Média = 7.5, DP = 0.3).
    *   Se `A1Cresult == '>8'` $\rightarrow$ Gerar valor decimal entre `8.1` e `14.0` (Média = 9.8, DP = 1.5).
    *   Se `A1Cresult == 'None'` $\rightarrow$ Não gerar linha de exame ou gerar valor padrão de controle de rotina (`5.7` a `7.0`).

#### C. Medicamentos (Marca/EUA para RENAME/SUS)
Mapear as colunas de variação de medicamentos do Kaggle para medicamentos reais fornecidos pelo SUS:
*   `metformin` $\rightarrow$ **Cloridrato de Metformina (850mg)**
*   `insulin` $\rightarrow$ **Insulina Humana NPH** ou **Insulina Humana Regular**
*   `glipizide` / `glyburide` $\rightarrow$ **Glibenclamida (5mg)**
*   *Lógica:* Se a coluna do medicamento no Kaggle estiver marcada como `No`, o paciente não recebe a prescrição. Se estiver `Steady` (estável), `Up` (aumentou) ou `Down` (diminuiu), gerar o registro correspondente em `PRESCRICAO_MEDICAMENTO` com doses correspondentes.

---

### Passo 4: Geolocalização e Demografia Pernambucana

Para retirar a "identidade americana" da base, o script deve aplicar as distribuições brasileiras:

1.  **Faixa Etária:** O Kaggle fornece idades agrupadas em faixas (ex: `[10-20)`). O script deve sortear uma data de nascimento aleatória que caia nessa faixa de idade, compatível com o ano do atendimento (ex: se o atendimento foi em 2005 e a faixa é `[10-20)`, o ano de nascimento deve ser sorteado entre 1985 e 1995).
2.  **Municípios de Pernambuco:** Usar a lista de municípios obtida do IBGE.
    *   Criar um vetor de probabilidade baseado na população de cada município.
    *   Para cada paciente sintético, sortear o município de residência (`NM_MUNIC`).
    *   Mapear o código correspondente da Regional de Saúde do Estado de Pernambuco (GERES).

---

### Passo 5: Regras de Negócio do SUS (Triagem e Vacinas)

#### A. Classificação de Risco (Manchester) na tabela `ACOLHIMENTO`
Como o Kaggle possui a urgência da admissão (`admission_type_id`), mapear logicamente para as cores da triagem brasileira:
*   `Emergency` (ID 1) $\rightarrow$ **Vermelho** ou **Laranja** (Urgência máxima/risco de morte).
*   `Urgent` (ID 2) $\rightarrow$ **Amarelo** (Urgência moderada).
*   `Elective` (ID 3) $\rightarrow$ **Verde** ou **Azul** (Pouco urgente/eletivo).

#### B. Registro de Vacinação (`IMUNIZAÇÃO`)
Gerar de forma probabilística o histórico de vacinas com base na cobertura real em Pernambuco (DATASUS):
*   Se o paciente tem Diabetes Tipo 1 (grupo prioritário), aplicar taxas de vacinação de **Influenza (Gripe)** e **Pneumocócica 23-valente** específicas para esse grupo (ex: 80% de chance de ter tomado as doses nos anos corretos).

---

### Passo 6: Validação de Cronologia e Integridade Relacional

O script de geração deve possuir um validador lógico final para garantir as seguintes restrições:
1.  **Cronologia:** $\text{Data de Nascimento} < \text{Data de Vacinação} < \text{Data de Triagem (Acolhimento)} \le \text{Data de Admissão} \le \text{Data de Alta/Óbito}$.
2.  **Chaves Estrangeiras:** Todos os IDs em `ATENDIMENTO` devem referenciar um `ID_PACIENTE` existente. O mesmo vale para prescrições, exames e diagnósticos vinculados àquele atendimento.
3.  **Estado Civil e Sexo:** Mapear categorias nulas e traduzir termos (ex: `Female` $\rightarrow$ `Feminino`, `Male` $\rightarrow$ `Masculino`).

---

## 3. Desempenho e Execução no Notebook Lenovo

Para garantir que o agente gere o banco em **menos de 3 minutos** na CPU local:
*   **Evitar loops aninhados (`for`):** Utilizar operações vetorizadas do Pandas (`df.map()`, `np.select()`, `np.random.choice()`) para atribuir municípios e regras de triagem de uma vez só em todo o DataFrame.
*   **Exportação em Lotes:** Se o banco final for SQLite ou PostgreSQL, usar `to_sql` do Pandas com o argumento `chunksize=10000` para otimizar a escrita em disco.
*   **Limitação do Escopo:** Caso opte por utilizar o algoritmo `GaussianCopula` do SDV para capturar correlações clínicas profundas, treine o modelo em um subset de **10.000 a 20.000 linhas** representativas. Ele aprenderá o comportamento clínico em menos de 2 minutos e conseguirá gerar as 100.000 linhas finais sintéticas em segundos.
