# ESTADO ATUAL DO PROJETO — REDS-DM1

> Arquivo de contexto canônico. Leia isto **primeiro** para entender o estado real do projeto
> antes de confiar nos demais documentos. Última atualização: **2026-06-01**.
>
> Por que este arquivo existe: os documentos de plano (`*.md` em `projeto/`, `banco/arquivos_plano/`
> e `pre_processamento/`) descrevem o estado **pretendido/idealizado**, que diverge do estado **real**
> em vários pontos (listados na seção 5). Em caso de conflito, **este arquivo tem prioridade**.

---

## 1. Objetivo do projeto (o que é avaliado)

Disciplina de **Computação Natural**. O entregável avaliado é um **otimizador** que **maximiza os
Anos de Vida Saudáveis (HLY — Healthy Life Years)** de pacientes com Diabetes Mellitus Tipo 1 (DM1)
em Pernambuco, gerando uma **Frente de Pareto** entre três objetivos: **HLY × Custo × Equidade**.

Algoritmos previstos:
- **BFSS / wFSS** (Binary/weighted Fish School Search) — seleção de variáveis.
- **MOFSS / mFSS** (Multi-Objective/Mixed-Variable Fish School Search) — núcleo da otimização.
- **NSGA-II** e **PSO** — baselines de comparação.

**O banco de dados sintético é um SUBSTRATO/testbed, não o artefato avaliado.** Não é objetivo
buscar realismo epidemiológico perfeito da coorte; é objetivo ter um substrato plausível e
estruturalmente íntegro sobre o qual o simulador e os otimizadores rodam.

---

## 2. Decisões de escopo já tomadas (vigentes)

1. **Deliverable = otimizador.** Base = substrato. Não investir em "fidelidade clínica DM1" da base.
2. **HbA1c basal fica no SIMULADOR**, não nos dados. O simulador (a ser construído) define o estado
   glicêmico inicial de cada perfil a partir das âncoras do **T1D Index**. A coluna `EXAME_HBA1C`
   da base é esparsa (~16% preenchida) e serve só como conferência de plausibilidade.
3. **Equidade é medida por MUNICÍPIO** (`NM_MUNIC`). O dicionário REDS **não tem GERES / região de
   saúde** — o campo mais granular disponível é a cidade. GERES seria informação externa opcional.
4. **Fora de escopo** (não corrigir, não afeta o otimizador):
   - Rótulo DM1 vs DM2 — nem chega ao `MODEL_DATASET`.
   - `FL_OBITO` fabricado — HLY vem das âncoras, não de sobrevivência.
   - Largura de medicamentos (4 vs 23) — afeta só a abrangência do BFSS, não o HLY.
5. **Idade** (coorte enviesada para idosos, média ~63) é o único atributo que mexe no resultado
   (HLY depende de idade). Se incomodar, resolve-se com um **filtro na carga do simulador**
   (selecionar pacientes mais jovens), **não** mexendo na base.

---

## 3. Estado real dos artefatos (verificado em 2026-05-31)

### Bancos de dados
- **`banco/reds_dm1.db`** → **500 atendimentos** (gerado pelo default `limit_rows=500` do
  `if __name__` em `generator.py`). **Desatualizado.**
- **`banco/reds_dm1_clean.db`** → **15.000 atendimentos**, construído de uma rodada antiga de 15k.
  - `MODEL_DATASET`: **15 colunas, apenas 4 medicamentos** (Metformina, Insulina NPH, Insulina
    Regular, Glibenclamida). **Não tem as 23 colunas** que os docs afirmam.
- **Os dois bancos estão DESSINCRONIZADOS** (500 vs 15.000).

### Distribuições reais no `reds_dm1_clean.db`
- Diabetes: **DM1 (E10/E10.9) = 606** vs **DM2 (E11.9) = 17.526** → só ~3,3% é Tipo 1.
- Idade: média **62,9 anos**; só **4,6%** têm ≤30 anos (min 0, max 99).
- Óbito: **94 / 11.886 = 0,79%** (fabricado por regra arbitrária no `generator.py`).
- HbA1c: preenchida em **16,1%** dos atendimentos (2.409 de 15.000).

### Esquema (schema)
- 13 tabelas REDS, modelagem relacional correta (PKs autoincrementais, FKs íntegras).
- `PACIENTE` tem `NM_MUNIC`, `SG_UF`, `NM_BAIRRO`, `CD_CEP` — **não há campo de GERES/região**.

### Como o pipeline funciona HOJE
- `banco/generator.py` lê o **CSV real do Kaggle 130-US** (via `data_loader.py`, URL no GitHub),
  traduz linha-a-linha (ICD-9→CID-10, HbA1c categórica→numérica, medicamentos→RENAME, triagem
  Manchester, etc.) e popula o SQLite. **NÃO usa CTGAN/SDV atualmente.**
- `banco/validator.py` valida integridade relacional, cronologia e consistência semântica.
- `pre_processamento/clean_database.py` gera o `reds_dm1_clean.db` e o `MODEL_DATASET` plano.

---

## 4. Em andamento e próximos passos

### Concluído
- **CTGAN/SDV — retreino (Opção A) concluído e validado.** O CSV sintético final está na **raiz do
  projeto**: `diabetic_sintetico_ctgan.csv`, **(15.000, 43)**. Treinado com
  `pre_processamento/treinamento_sdv_baseline.py` (epochs=300, GPU, Kaggle).
  - ✅ `diag_1` (14.998/15.000), `diag_2` (14.963), `diag_3` (14.844) **presentes e preenchidos**.
  - ✅ Comorbidades vão nascer de verdade (cruzando os códigos com as regras do `translator.py`:
    renal 580–589→N18.9; cardio 410–414/428/401–405→I21.9/I50.9/I10):
    **984** pacientes renais, **6.299** cardiovasculares, **6.934 (~46%)** com ≥1 comorbidade.
  - ✅ Conteúdo coerente: medicamentos em No/Steady/Up/Down; idade enviesada para idosos; HbA1c
    esparsa (~7% preenchida — esperado, a basal vem do simulador).
  - `patient_nbr` **continua ausente, e está correto** — será reconstruído como ID sequencial no
    pipeline (nunca foi para entrar no treino).
- ⚠️ Lembrete: **CTGAN reproduz a distribuição da fonte.** O sintético é ~97% DM2 idoso, como o
  130-US. Isso é aceitável (substrato); a lógica DM1 vive no simulador (âncoras T1D Index).
- Histórico: a 1ª rodada (anterior) saiu com **(15.000, 40)**, **sem** os `diag_*` — daí a decisão
  pela Opção A (retreinar incluindo os diagnósticos), agora cumprida.

### Pendentes (ordem sugerida)
1. Integrar o CSV sintético (`diabetic_sintetico_ctgan.csv`) ao `data_loader.py` (hoje ele lê o CSV
   real do Kaggle) e reconstruir `patient_nbr` como ID sequencial no pipeline.
2. Regerar `reds_dm1.db` com 15.000 **e** rodar `clean_database.py` em seguida (sincronizar +
   atualizar para as 23 colunas de medicamento previstas).
3. **Construir o simulador de HLY** (ainda não existe): lê `MODEL_DATASET`, define HbA1c basal
   pelas âncoras T1D Index, mapeia perfil → HLY com descontos por comorbidade (`IS_RENAL`,
   `IS_CARDIOVASCULAR`).
4. Construir os otimizadores (BFSS, depois MOFSS, depois NSGA-II/PSO) e a Frente de Pareto.

---

## 5. Divergências conhecidas: documentos × realidade

| O documento afirma | Realidade atual |
| :--- | :--- |
| Geração usa motor CTGAN/SDV/Gaussian Copula | `generator.py` faz tradução direta; CTGAN já treinou (retreino c/ `diag_*` concluído, CSV validado na raiz) mas **ainda não integrado ao `data_loader.py`** |
| `MODEL_DATASET` tem 23 medicamentos / ~40 colunas | Real: 4 medicamentos / 15 colunas (versão antiga) |
| Base de 15.000 registros | `reds_dm1.db` tem 500; só o `_clean.db` tem 15.000 |
| Script CTGAN: "use o Google Colab" | Está rodando no **Kaggle** (persistência via *Save Version/Commit*, saída em `/kaggle/working`) |
| Base "fidedigna de DM1" | É ~97% DM2 / idosa — aceitável como substrato, não declarado como limitação |
| Gantt (Otimizacao...md): BFSS ativo, simulador iniciando | CTGAN concluído; próximo passo é integrar o CSV e construir o simulador (ainda não começou) |
| Script CTGAN gera base completa | Versão anterior salvava só 5 linhas; **versão atual já gera/salva o CSV de 15.000** |

---

## 6. Mapa de arquivos

- **`banco/`** — pipeline de geração: `data_loader.py`, `db_schema.py`, `seeder.py`,
  `translator.py`, `generator.py`, `validator.py`, `main.py`. Bancos `.db` e cache.
- **`pre_processamento/`** — limpeza/modelagem: `clean_database.py`, `count_columns.py`,
  `treinamento_sdv_baseline.py` (CTGAN) e docs (`criterios_limpeza.md`,
  `processo_geracao_dados_sinteticos.md`, `README_clean_db.md`).
- **`projeto/`** — `Otimizacao_HLY_DM1_REDS_Atualizado.md` (visão do projeto) e dicionário REDS.
- **`banco/arquivos_plano/`** — `plano_geracao_dados_sinteticos.md` e dicionário REDS (`.xlsx`).
