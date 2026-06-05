"""
translator.py
Implementa as regras de negócio, traduções clínicas (ICD-9 para CID-10, medicamentos, exames)
e geodemográficas (municípios de PE, idades para datas de nascimento, CPFs/CNSs).
"""

import re
import random
from datetime import datetime, timedelta
import numpy as np

# Cidades principais de Pernambuco e seus pesos populacionais aproximados
MAJOR_PE_CITIES_WEIGHTS = {
    "Recife": 100,
    "Jaboatão dos Guararapes": 50,
    "Olinda": 30,
    "Caruaru": 25,
    "Petrolina": 25,
    "Paulista": 20,
    "Cabo de Santo Agostinho": 15,
    "Camaragibe: Camaragibe": 12,
    "Garanhuns": 10,
    "Vitória de Santo Antão": 10,
}

def generate_valid_cpf() -> str:
    """Gera um número de CPF válido com dígitos verificadores corretos."""
    digits = [random.randint(0, 9) for _ in range(9)]
    
    # Primeiro dígito verificador
    s1 = sum(digits[i] * (10 - i) for i in range(9))
    d1 = 11 - (s1 % 11)
    d1 = 0 if d1 >= 10 else d1
    digits.append(d1)
    
    # Segundo dígito verificador
    s2 = sum(digits[i] * (11 - i) for i in range(10))
    d2 = 11 - (s2 % 11)
    d2 = 0 if d2 >= 10 else d2
    digits.append(d2)
    
    return "".join(map(str, digits))

def generate_valid_cns() -> str:
    """Gera um número de CNS (Cadastro Nacional de Saúde) com formato válido de 15 dígitos."""
    # CNS válidos começam com 1, 2, 7, 8 ou 9
    start_digit = random.choice([1, 2, 7, 8])
    random_digits = [random.randint(0, 9) for _ in range(10)]
    cns_base = str(start_digit) + "".join(map(str, random_digits))
    
    # Calcula dígito verificador para CNS
    s = sum(int(cns_base[i]) * (15 - i) for i in range(11))
    resto = s % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    
    if dv == 10:
        # Se dv for 10, a regra do CNS manda somar 2 ao resto e recalcular ou usar um sufixo
        # Para simplificar mantendo a validação, geramos de novo recursivamente se dv for 10
        return generate_valid_cns()
        
    cns_final = cns_base + "000" + str(dv)
    return cns_final

def generate_phone_number() -> str:
    """Gera um numero de celular formatado no padrao (81) 9xxxx-xxxx."""
    prefix = random.choice(["99", "98", "97", "96", "91"])
    rest = "".join(str(random.randint(0, 9)) for _ in range(6))
    return f"(81) {prefix}{rest[:2]}-{rest[2:]}"

def generate_email(name: str) -> str:
    """Gera um email valido baseado no nome do paciente."""
    clean_name = name.lower()
    clean_name = re.sub(r'[áàâãä]', 'a', clean_name)
    clean_name = re.sub(r'[éèêë]', 'e', clean_name)
    clean_name = re.sub(r'[íìîï]', 'i', clean_name)
    clean_name = re.sub(r'[óòôõö]', 'o', clean_name)
    clean_name = re.sub(r'[úùûü]', 'u', clean_name)
    clean_name = re.sub(r'[ç]', 'c', clean_name)
    parts = clean_name.split()
    if len(parts) >= 2:
        username = f"{parts[0]}.{parts[-1]}"
    else:
        username = parts[0]
    domain = random.choice(["gmail.com", "outlook.com", "yahoo.com.br", "hotmail.com"])
    return f"{username}@{domain}"

def generate_address() -> tuple:
    """Gera um endereco brasileiro aleatorio (tipo_logradouro, logradouro, numero, bairro, cep)."""
    tp_logradouro = random.choice(["Rua", "Avenida", "Travessa", "Praca", "Alameda"])
    nomes_logradouros = [
        "Floriano Peixoto", "Agamenon Magalhaes", "Dantas Barreto", "Conde da Boa Vista",
        "Rosa e Silva", "Sebastiao Lacerda", "Imperial", "Domingos Ferreira", "Conselheiro Aguiar",
        "da Aurora", "Sete de Setembro", "Boa Viagem", "Imaculada Conceicao", "do Futuro"
    ]
    logradouro = random.choice(nomes_logradouros)
    numero = str(random.randint(10, 2500)) if random.random() < 0.9 else "S/N"
    bairros = ["Boa Viagem", "Madalena", "Casa Forte", "Derby", "Gracas", "Espinheiro", 
               "Cordeiro", "Afogados", "San Martin", "Varzea", "Pina", "Boa Vista", "Santo Amaro"]
    bairro = random.choice(bairros)
    
    cep_prefix = random.randint(50000, 56999)
    cep_suffix = random.randint(100, 999)
    cep = f"{cep_prefix}-{cep_suffix:03d}"
    
    return tp_logradouro, logradouro, numero, bairro, cep

def translate_gender(gender_str: str) -> str:
    """Traduz o gênero do dataset original para português."""
    gender = str(gender_str).strip().lower()
    if "female" in gender:
        return "Feminino"
    elif "male" in gender:
        return "Masculino"
    else:
        return random.choice(["Feminino", "Masculino"])

def translate_race(race_str: str) -> str:
    """Traduz a raça do dataset original para o padrão brasileiro do SUS."""
    race = str(race_str).strip().lower()
    if race == "caucasian":
        return "Branca"
    elif race == "africanamerican":
        return "Preta"
    elif race == "asian":
        return "Amarela"
    elif race == "hispanic":
        return "Parda"
    elif race == "other" or race == "?":
        return random.choice(["Parda", "Indígena", "Sem Informação"])
    return "Sem Informação"

def translate_diagnosis(icd9_code: str, age_years: int) -> str:
    """
    Traduz códigos ICD-9 para CID-10 correspondentes.
    Foca nos principais diagnósticos de Diabetes, Renal e Circulatório.
    """
    icd = str(icd9_code).strip()
    
    # 1. Diabetes (250.xx)
    if icd.startswith("250"):
        # Se for jovem, maior probabilidade de ser DM Tipo 1 (E10.9)
        if age_years <= 30:
            return "E10.9" # DM Tipo 1 sem complicações
        else:
            return "E11.9" # DM Tipo 2 sem complicações
            
    # 2. Doenças Renais (580-589)
    # Tenta converter o código para número
    try:
        val = float(icd)
        if 580 <= val <= 589:
            return "N18.9" # Insuficiência renal crônica
    except ValueError:
        pass
        
    # 3. Doenças Circulatórias (390-459)
    try:
        val = float(icd)
        if 390 <= val <= 459:
            if 410 <= val <= 414:
                return "I21.9" # Infarto agudo do miocárdio
            elif val == 428:
                return "I50.9" # Insuficiência cardíaca
            elif 401 <= val <= 405:
                return "I10" # Hipertensão
            elif 430 <= val <= 438:
                return "I64" # AVC
            return "I10" # Hipertensão padrão
    except ValueError:
        pass
        
    # Padrão para códigos não mapeados: associar à diabetes geral ou hipertensão
    return random.choice(["E11.9", "I10"])

def get_truncated_normal(mean: float, sd: float, low: float, high: float) -> float:
    """Gera um valor com distribuição normal truncada."""
    while True:
        val = np.random.normal(mean, sd)
        if low <= val <= high:
            return round(val, 2)

def translate_hba1c(a1c_result: str) -> float:
    """Converte HbA1c qualitativa do Kaggle em resultado numérico realista (%)."""
    res = str(a1c_result).strip()
    if res == "Normal":
        return get_truncated_normal(5.0, 0.4, 4.0, 5.6)
    elif res == ">7":
        return get_truncated_normal(7.5, 0.3, 7.1, 8.0)
    elif res == ">8":
        return get_truncated_normal(9.8, 1.5, 8.1, 15.0)
    else:
        # Para "None", gera controle de rotina (20% de chance) ou retorna None
        if random.random() < 0.2:
            return get_truncated_normal(6.3, 0.4, 5.7, 7.0)
        return None

def get_symptoms(diag_1: str, adm_type_id: int) -> tuple:
    """
    Gera sintomas baseados no diagnóstico principal (Kaggle diag_1) e tipo de admissão.
    Isso preserva a distribuição clínica original do dataset.
    """
    icd = str(diag_1).strip()
    
    # Doenças Circulatórias (390-459)
    if icd.startswith('4') or icd.startswith('39'):
        if adm_type_id == 1:
            return "Dor torácica, falta de ar", "Possível infarto/isquemia"
        return "Tontura, palpitações", "Hipertensão/Alteração cardíaca"
        
    # Diabetes e Endócrinas (250.xx)
    elif icd.startswith('250'):
        if adm_type_id == 1:
            return "Poliúria, hálito cetônico, confusão", "Descompensação diabética aguda"
        return "Polidipsia, fadiga", "Diabetes descompensada"
        
    # Respiratórias (460-519)
    elif icd.startswith('46') or icd.startswith('47') or icd.startswith('48') or icd.startswith('49') or icd.startswith('50') or icd.startswith('51'):
        if adm_type_id == 1:
            return "Dispneia severa, tosse produtiva", "Insuficiência respiratória aguda"
        return "Tosse, cansaço", "Problema respiratório"
        
    # Renais / Geniturinário (580-629)
    elif icd.startswith('58') or icd.startswith('59') or icd.startswith('6'):
        return "Edema, diminuição do volume urinário", "Problema renal/urinário"
        
    # Gastrointestinais (520-579)
    elif icd.startswith('52') or icd.startswith('53') or icd.startswith('54') or icd.startswith('55') or icd.startswith('56') or icd.startswith('57'):
        return "Dor abdominal, náuseas", "Sintomas gastrointestinais"
        
    # Default fallback preservando a distribuição de severidade (adm_type_id)
    if adm_type_id == 1:
        return "Dor aguda, mal-estar súbito", "Emergência não especificada"
    elif adm_type_id == 2:
        return "Dor moderada, febre", "Urgência médica"
    else:
        return "Mal-estar geral, acompanhamento", "Acompanhamento ambulatorial"


def translate_medicines(row) -> list:
    """
    Analisa colunas de medicamentos do Kaggle e traduz para prescrições RENAME/SUS.
    Retorna lista de dicionários com prescrições, mapeando as 23 colunas do Kaggle originais.
    """
    prescriptions = []
    
    # Mapeamentos de medicamentos refletindo as colunas exatas do Kaggle
    med_mappings = {
        "metformin": ("Cloridrato de Metformina (850mg)", 1, "Via Oral", "Tomar 1 comprimido 2 vezes ao dia"),
        "insulin": ("Insulina Humana (NPH/Regular)", 2, "Subcutânea", "Aplicar conforme prescrição médica"),
        "glipizide": ("Glipizida (5mg)", 3, "Via Oral", "Tomar 1 comprimido pela manhã"),
        "glyburide": ("Glibenclamida (5mg)", 4, "Via Oral", "Tomar 1 comprimido pela manhã"),
        "repaglinide": ("Repaglinida (2mg)", 5, "Via Oral", "Tomar antes das refeições"),
        "nateglinide": ("Nateglinida (120mg)", 6, "Via Oral", "Tomar antes das refeições"),
        "chlorpropamide": ("Clorpropamida (250mg)", 7, "Via Oral", "Tomar pela manhã"),
        "glimepiride": ("Glimepirida (2mg)", 8, "Via Oral", "Tomar pela manhã"),
        "acetohexamide": ("Aceto-hexamida", 9, "Via Oral", "Tomar conforme prescrição"),
        "tolbutamide": ("Tolbutamida", 10, "Via Oral", "Tomar conforme prescrição"),
        "pioglitazone": ("Pioglitazona (30mg)", 11, "Via Oral", "Tomar 1 comprimido ao dia"),
        "rosiglitazone": ("Rosiglitazona (4mg)", 12, "Via Oral", "Tomar 1 comprimido ao dia"),
        "acarbose": ("Acarbose (50mg)", 13, "Via Oral", "Tomar junto às refeições"),
        "miglitol": ("Miglitol (50mg)", 14, "Via Oral", "Tomar com a primeira porção das refeições"),
        "troglitazone": ("Troglitazona", 15, "Via Oral", "Tomar conforme prescrição"),
        "tolazamide": ("Tolazamida", 16, "Via Oral", "Tomar conforme prescrição"),
        "examide": ("Exameida", 17, "Via Oral", "Tomar conforme prescrição"),
        "citoglipton": ("Citogliptina", 18, "Via Oral", "Tomar conforme prescrição"),
        "glyburide-metformin": ("Glibenclamida + Metformina", 19, "Via Oral", "Tomar conforme prescrição"),
        "glipizide-metformin": ("Glipizida + Metformina", 20, "Via Oral", "Tomar conforme prescrição"),
        "glimepiride-pioglitazone": ("Glimepirida + Pioglitazona", 21, "Via Oral", "Tomar conforme prescrição"),
        "metformin-rosiglitazone": ("Metformina + Rosiglitazona", 22, "Via Oral", "Tomar conforme prescrição"),
        "metformin-pioglitazone": ("Metformina + Pioglitazona", 23, "Via Oral", "Tomar conforme prescrição")
    }
    
    for kaggle_col, sus_info in med_mappings.items():
        if kaggle_col in row:
            val = str(row[kaggle_col]).strip()
            # Se o paciente toma o medicamento (Up, Down, Steady)
            if val in ["Up", "Down", "Steady"]:
                name, code, via, dose = sus_info
                
                prescriptions.append({
                    "NM_MEDTO": name,
                    "CD_MEDTO": code,
                    "DS_TIPO": "principal",
                    "DS_VIA_ADMIN_MEDTO": via,
                    "DS_DOSE_MEDTO": dose,
                    "DS_OBSERV_MEDTO": f"Ajuste clínico para medicamento original marcado como {val}."
                })
                
    return prescriptions

def get_municipio_weights(municipios: list) -> list:
    """Calcula pesos de probabilidade populacional para sorteio de municípios."""
    weights = []
    for m in municipios:
        name = m.get("nome", "")
        # Busca peso na lista de cidades principais ou usa padrão
        w = MAJOR_PE_CITIES_WEIGHTS.get(name, 2)
        weights.append(w)
        
    total = sum(weights)
    return [w / total for w in weights]

def generate_birth_date(age_str: str) -> tuple:
    """Gera uma data de nascimento consistente com a faixa etaria e retorna (data, idade_anos)."""
    match = re.findall(r'\d+', age_str)
    if len(match) >= 2:
        age_low, age_high = int(match[0]), int(match[1])
        age = random.randint(age_low, age_high - 1)
    else:
        age = random.randint(10, 80)
        
    reference_year = 2024
    birth_year = reference_year - age
    birth_date = datetime(birth_year, random.randint(1, 12), random.randint(1, 28))
    return birth_date, age

def generate_encounter_dates(birth_date: datetime, age: int, time_in_hospital_days: int) -> dict:
    """
    Gera datas consistentes de atendimento baseadas na data de nascimento estatica do paciente,
    respeitando a sua idade no momento do atendimento.
    """
    # O atendimento inicia em uma data aleatoria no ano em que o paciente tem 'age' anos de idade
    encounter_start = birth_date + timedelta(days=age * 365 + random.randint(1, 360))
    encounter_start = encounter_start.replace(hour=random.randint(7, 22), minute=random.randint(0, 59))
    
    # Data de alta (fim)
    encounter_end = encounter_start + timedelta(days=max(1, time_in_hospital_days), hours=random.randint(1, 6))
    
    # Acolhimento/Triagem (acontece cerca de 15 a 45 minutos antes da admissão)
    triage_start = encounter_start - timedelta(minutes=random.randint(15, 45))
    triage_end = triage_start + timedelta(minutes=random.randint(5, 15))
    
    # Exame e resultado (realizado durante a internação)
    max_exam_hours = max(2, time_in_hospital_days * 24)
    exam_time = encounter_start + timedelta(hours=random.randint(1, max(2, max_exam_hours - 2)))
    exam_result_time = exam_time + timedelta(hours=random.randint(2, 12))
    
    # Vacinação (imunização) - ocorreu em alguma data anterior, mas obrigatoriamente APOS o nascimento
    age_in_days = (encounter_start - birth_date).days
    if age_in_days <= 30:
        vaccine_time = birth_date + timedelta(days=random.randint(1, max(2, age_in_days - 1)))
    else:
        max_vaccine_days = min(365, age_in_days - 1)
        vaccine_time = encounter_start - timedelta(days=random.randint(30, max_vaccine_days))
    
    # Prescrição (criada durante o atendimento)
    prescription_time = encounter_start + timedelta(hours=random.randint(1, 3))
    
    return {
        "birth_date": birth_date.strftime("%Y-%m-%d"),
        "triage_start": triage_start.strftime("%Y-%m-%d %H:%M:%S"),
        "triage_end": triage_end.strftime("%Y-%m-%d %H:%M:%S"),
        "encounter_start": encounter_start.strftime("%Y-%m-%d %H:%M:%S"),
        "encounter_end": encounter_end.strftime("%Y-%m-%d %H:%M:%S"),
        "exam_time": exam_time.strftime("%Y-%m-%d %H:%M:%S"),
        "exam_result_time": exam_result_time.strftime("%Y-%m-%d %H:%M:%S"),
        "vaccine_time": vaccine_time.strftime("%Y-%m-%d %H:%M:%S"),
        "prescription_time": prescription_time.strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    # Teste rápido
    print("CPF:", generate_valid_cpf())
    print("CNS:", generate_valid_cns())
    print("HbA1c Normal:", translate_hba1c("Normal"))
    print("HbA1c >8:", translate_hba1c(">8"))
    bd, age = generate_birth_date("[30-40)")
    print("Cronologia:", generate_encounter_dates(bd, age, 5))
