# Script de Treinamento CTGAN - Baseline (REDS-DM1)
#
# ONDE RODA: Kaggle Notebooks (kaggle.com/code), NÃO Google Colab.
#
# Como usar no Kaggle:
# 1. Crie um Notebook novo no Kaggle.
# 2. Painel direito > Accelerator: ligue a GPU (ex.: T4 x2).
# 3. Painel direito > Internet: LIGADO (precisa baixar o CSV do GitHub e instalar a sdv).
# 4. Cole este script numa célula (ou cole por blocos separados pelos comentários "# === Bloco N ===").
# 5. Para rodar a noite toda sem ficar com a aba aberta: "Save Version" > "Save & Run All (Commit)".
#    O Kaggle roda em modo headless (limite ~12h por execução em lote) e guarda tudo que
#    estiver em /kaggle/working na versão salva.
# 6. Depois do commit, os arquivos de saída (.pkl e .csv) ficam na aba "Output" da versão,
#    de onde você faz o download para o PC.

# === Bloco 0: Instalação ===
# No Kaggle, descomente e rode UMA vez por sessão. O pandas já vem instalado; instalar a sdv
# por cima não tem problema.
# !pip install sdv

# === Bloco 1: Imports e Carregamento ===
import pandas as pd
from sdv.metadata import SingleTableMetadata
from sdv.single_table import CTGANSynthesizer
import warnings
warnings.filterwarnings('ignore')

print("1. Carregando dados (fonte: Diabetes 130-US, via GitHub)...")
# URL direta do dataset usado no projeto, para não precisar de upload manual no Kaggle.
csv_url = "https://raw.githubusercontent.com/Lfirenzeg/msds622/main/Final_Project/diabetic_data.csv"
df = pd.read_csv(csv_url)

# Colunas demográficas e clínicas que formam a "fotografia" (T0) do paciente.
# IMPORTANTE: diag_1/diag_2/diag_3 foram ADICIONADAS nesta versão. Sem elas, o sintético sai
# sem códigos de diagnóstico e o pipeline (generator.py) não consegue derivar as comorbidades
# IS_RENAL e IS_CARDIOVASCULAR, que o simulador de HLY precisa para descontar anos saudáveis.
colunas_interesse = [
    # Demografia e Internação
    'race', 'gender', 'age', 'admission_type_id', 'time_in_hospital',
    'num_lab_procedures', 'num_procedures', 'num_medications', 'number_outpatient',
    'number_emergency', 'number_inpatient', 'number_diagnoses',
    # Diagnósticos (ICD-9) -> geram comorbidades no pipeline (IS_RENAL / IS_CARDIOVASCULAR)
    'diag_1', 'diag_2', 'diag_3',
    # Exames e Desfechos
    'max_glu_serum', 'A1Cresult', 'readmitted', 'change', 'diabetesMed',
    # 23 Medicamentos (candidatos para o BFSS)
    'metformin', 'repaglinide', 'nateglinide', 'chlorpropamide', 'glimepiride',
    'acetohexamide', 'glipizide', 'glyburide', 'tolbutamide', 'pioglitazone',
    'rosiglitazone', 'acarbose', 'miglitol', 'troglitazone', 'tolazamide',
    'examide', 'citoglipton', 'insulin', 'glyburide-metformin',
    'glipizide-metformin', 'glimepiride-pioglitazone', 'metformin-rosiglitazone',
    'metformin-pioglitazone'
]
df_baseline = df[colunas_interesse].copy()

# Tratamento básico de valores nulos (o dataset usa '?' como ausente).
df_baseline = df_baseline.replace('?', pd.NA)

# === Bloco 2: Metadados ===
print("\n2. Detectando metadados (esquema da tabela)...")
metadata = SingleTableMetadata()
metadata.detect_from_dataframe(data=df_baseline)
# Força tipos que o SDV pode interpretar mal.
metadata.update_column(column_name='admission_type_id', sdtype='categorical')
# diag_1/2/3 são códigos ICD-9 (categóricos), não números a serem interpolados.
metadata.update_column(column_name='diag_1', sdtype='categorical')
metadata.update_column(column_name='diag_2', sdtype='categorical')
metadata.update_column(column_name='diag_3', sdtype='categorical')

# === Bloco 3: Treinamento do CTGAN ===
print("\n3. Configurando e treinando o CTGAN (isso leva tempo, ~1h com epochs=300 na T4)...")
# Dica: no primeiro teste, use epochs=5 só para ver se roda ponta a ponta.
# Para o treinamento real, 300 epochs. A rodada anterior (sem os diag) levou ~1h.
synthesizer = CTGANSynthesizer(
    metadata,
    epochs=300,
    verbose=True
)

synthesizer.fit(df_baseline)

# === Bloco 4: Salvamento do modelo ===
print("\n4. Salvando o modelo treinado em /kaggle/working ...")
# /kaggle/working é a pasta persistida na versão salva (aba Output).
synthesizer.save('/kaggle/working/ctgan_diabetic_baseline.pkl')
print("Modelo salvo: /kaggle/working/ctgan_diabetic_baseline.pkl")

# === Bloco 5: Geração do CSV sintético COMPLETO ===
# Antes este script só gerava 5 linhas de teste. Agora geramos a base sintética inteira,
# que é o que de fato será baixada e plugada no pipeline (data_loader.py).
print("\n5. Gerando base sintética completa (15.000 linhas)...")
synthetic_data = synthesizer.sample(num_rows=15000)
synthetic_data.to_csv('/kaggle/working/diabetic_sintetico_ctgan.csv', index=False)
print("CSV salvo: /kaggle/working/diabetic_sintetico_ctgan.csv")
print(f"Formato gerado: {synthetic_data.shape}")
print("\nPrévia das 5 primeiras linhas:")
print(synthetic_data.head())
