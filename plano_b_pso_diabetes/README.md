# Plano B — PSO sobre coorte de diabéticos (entrega de curto prazo)

> **Status: em andamento — 2026-06-06.** Plano B de **fácil implementação**, escolhido após conversa
> com o orientador (o plano ambicioso ficou em `../projeto_pausado_marcadores_plantados/`).
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

## A definir (próximos passos)

1. **Score de "melhor indivíduo"** — quais colunas exatas, pesos e o alvo de HbA1c.
2. **Enquadramento do PSO** (com n=357, a Opção B é viável):
   - **(A) Perfil ideal:** PSO busca no espaço de características o perfil que maximiza o score; depois
     achamos os pacientes reais mais próximos.
   - **(B) Modelo otimizado por PSO (recomendado):** PSO otimiza os **pesos de um modelo** que prevê um
     rótulo de "bom desfecho" a partir das *outras* características → pesos altos = "quais
     características o indivíduo ótimo tem".
3. **Implementar** (Python: pandas + PSO simples) e interpretar.

## Atenção metodológica

- Não fatiar os 357 em sub-recortes pequenos (ex.: "top 10%" = ~36 → fraco).
- Coorte única (China, 2012) → não generaliza; declarar como testbed.
