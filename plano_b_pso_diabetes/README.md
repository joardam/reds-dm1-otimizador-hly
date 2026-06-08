# Plano B — PSO sobre coorte de diabéticos (entrega de curto prazo)

> **Status: em andamento — 2026-06-06.** Plano B de **fácil implementação**, escolhido após conversa
> com o orientador (o plano principal está em `../projeto_marcadores_plantados/`).
> Meta: algo **minimamente apresentável dentro do prazo**.

## Decisões fechadas

- **Base de dados: "A bimodal dataset for diabetes research"** (Nature Scientific Data, 2026;
  Zenodo DOI `10.5281/zenodo.18270337`). Arquivo em `data/Dataset for diabetes research.csv`
  (5.922 indivíduos × 190 variáveis; dicionário em `data/Supplementary Information.docx`).
  Coorte de **rastreio metabólico adulto (China, 2012)** — snapshot transversal.
- **Universo do estudo: apenas os DIABÉTICOS** → filtro `DM == 1` → **n = 357**.
- **Algoritmo: PSO** (Particle Swarm Optimization) — algoritmo de Computação Natural exigido.
- **Honestidade declarada:** a base **NÃO distingue tipo 1 vs tipo 2** (sem autoanticorpos, adultos
  18–91, contexto de síndrome metabólica → na prática T2D). Não existe base aberta de T1D usável
  (ver histórico no chat). Logo, isto é **"diabetes (tipo não especificado)"**, não T1D. O entregável
  é o **otimizador**; a base é testbed.

## Objetivo

Identificar o(s) **"melhor(es) indivíduo(s)"** entre os diabéticos e **caracterizar** o que eles têm em
comum (PSO + correlação/interpretação).

## Campos disponíveis para o score (confirmados na base)

- **Idade:** `Age` (18–91).
- **Glicemia/controle:** `HbA1c` (+ flag `A1cover6575`), `FPG`, `PG2h`, `GA`, `FINS`, `FCP`, `HomaIR`.
- **Comorbidades:** `HypertenHis`, `DyslipideHis`, pressão `Bpsys`/`Bpdia`, lipídios.
- **Critério provisório de "melhor indivíduo":** idade, **poucas comorbidades**, **HbA1c ideal** (~7%).

## Implementação (Opção B) — `pso_diabetes.py`

- **Rótulo "indivíduo ideal"** = terço superior de `wellness = z(idade) − z(HbA1c) − z(nº comorbidades)`
  (comorbidades = hipertensão `WHO1999hbp` + dislipidemia `TGdis`/`DysHDLIDFNCEP`). Idade↑ = melhor.
- **PSO** otimiza os pesos de uma **regressão logística** que prevê o rótulo a partir de 26
  características que **não** entram no rótulo (antropometria, insulina/peptídeo-C/HOMA, enzimas
  hepáticas, renais, estilo de vida, histórico familiar). Fitness = −(log-loss + L2).
- **Validação:** o ótimo do PSO é comparado à logística analítica do sklearn (mesma regularização).

### Como rodar

```bash
pip install numpy pandas scikit-learn matplotlib
cd plano_b_pso_diabetes
python3 pso_diabetes.py
```

Gera: `RESULTADOS.md`, `resultados_convergencia_pso.png`, `resultados_importancia.png`.

### Resultados (n=357; 119 ideais vs 238 demais)

- **PSO:** AUC treino ≈ 0.82 | teste ≈ 0.66 — **sklearn** teste ≈ 0.66.
- **Validação:** similaridade (cosseno) dos pesos PSO×sklearn = **1.000** → o PSO resolveu a mesma
  otimização (prova que funciona).
- **Perfil do indivíduo ideal:** mais **magro** (BMI/cintura/gordura↓), menos **resistência à insulina**
  (HOMA-IR/insulina jejum↓), **ALT↓** (menos fígado gorduroso) e **menos histórico familiar** de DM.

## Atenção metodológica

- Não fatiar os 357 em sub-recortes pequenos (ex.: "top 10%" = ~36 → fraco).
- Coorte única (China, 2012) → não generaliza; declarar como testbed.
- O rótulo é construído de {idade, HbA1c, comorbidades}; por isso essas variáveis (e proxies de
  glicose/lipídio/PA) ficam **fora** dos preditores, pra a descoberta não ser circular.
