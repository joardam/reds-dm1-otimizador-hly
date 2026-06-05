"""
data_loader.py
Carrega o dataset clínico do Kaggle e a API de Municípios do IBGE-PE,
utilizando cache local para evitar requisições redundantes e otimizar a performance.
"""

import os
import requests
import json
import pandas as pd

CSV_URL = "https://raw.githubusercontent.com/Lfirenzeg/msds622/main/Final_Project/diabetic_data.csv"
IBGE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/PE/municipios"

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CSV_PATH = os.path.join(CACHE_DIR, "diabetic_data.csv")
JSON_PATH = os.path.join(CACHE_DIR, "municipios_pe.json")

def ensure_cache_dir():
    """Garante que a pasta cache exista."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"[data_loader] Pasta de cache criada em: {CACHE_DIR}")

def download_file(url: str, dest_path: str):
    """Baixa um arquivo da internet utilizando requests (trata compressão)."""
    ensure_cache_dir()
    print(f"[data_loader] Baixando de {url} ...")
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        with open(dest_path, 'wb') as out_file:
            out_file.write(r.content)
        print(f"[data_loader] Arquivo salvo em: {dest_path}")
    except Exception as e:
        print(f"[data_loader] Erro ao baixar {url}: {e}")
        raise


def load_clinical_data(limit_rows: int = None) -> pd.DataFrame:
    """Carrega o dataset clínico da UCI/Kaggle, baixando se necessário."""
    ensure_cache_dir()
    if not os.path.exists(CSV_PATH):
        download_file(CSV_URL, CSV_PATH)
    
    print("[data_loader] Carregando dataset clínico (diabetic_data.csv)...")
    df = pd.read_csv(CSV_PATH, nrows=limit_rows)
    print(f"[data_loader] Dataset carregado. Linhas: {len(df)}, Colunas: {len(df.columns)}")
    return df

def load_municipios() -> list:
    """Carrega os municípios de Pernambuco a partir da API do IBGE."""
    ensure_cache_dir()
    if not os.path.exists(JSON_PATH):
        download_file(IBGE_URL, JSON_PATH)
        
    print("[data_loader] Carregando municípios de Pernambuco...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        municipios_list = json.load(f)
    print(f"[data_loader] {len(municipios_list)} municípios carregados.")
    return municipios_list

if __name__ == "__main__":
    # Teste rápido de carregamento
    df = load_clinical_data(limit_rows=100)
    muns = load_municipios()
    print("Primeiro município:", muns[0] if muns else "Nenhum")
