# meta_fss_pso — Meta-Otimizacao: FSS otimiza hiperparametros do PSO

> Semana #10 (PSO) x Semana #11 (FSS) da disciplina de Computacao Natural.

## O que e este modulo

Usa o **FSS (Fish School Search)** para encontrar automaticamente os melhores hiperparametros
do **PSO**, que por sua vez otimiza os pesos da regressao logistica para identificar o
"individuo ideal" entre 357 diabeticos.

```
FSS (meta-nivel)  ->  otimiza  ->  PSO (nivel 1)  ->  otimiza  ->  pesos da logistica
[w_in, c1, c2, L]              [pesos do modelo]              [classificacao]
```

As funcoes de **Wellness** e **Fitness** sao identicas ao `pso_diabetes.py`.
O FSS apenas ajusta os hiperparametros `w_in, c1, c2, LAMBDA` do PSO.

## Como rodar

```bash
cd plano_b_pso_diabetes/meta_fss_pso
python meta_fss_pso.py
```

Tempo estimado: **6-12 minutos**.

## Saidas geradas

| Arquivo | Conteudo |
|---|---|
| `RESULTADOS_META.md` | Tabelas de hiperparametros e AUC |
| `resultados_metafss_convergencia.png` | Convergencia do meta-FSS por iteracao |
| `resultados_comparacao_convergencia.png` | PSO padrao x PSO meta-otimizado |
| `resultados_importancia_meta.png` | Importancia das features (PSO meta) |

## Hiperparametros otimizados pelo FSS

| Parametro | Intervalo de busca | Valor padrao (empirico) |
|---|---|---|
| `w_in` (inércia) | [0.30, 0.95] | 0.70 |
| `c1` (confianca pessoal) | [0.50, 2.50] | 1.50 |
| `c2` (confianca social) | [0.50, 2.50] | 1.50 |
| `LAMBDA` (regularizacao L2) | [0.001, 0.50] | 0.05 |

## Configuracao do experimento

- **meta-FSS:** 15 peixes x 30 iteracoes
- **PSO interno:** 15 particulas x 80 iteracoes (leve, para viabilidade computacional)
- **Avaliacao:** CV-3 fold no conjunto de treino (evita data leakage)
- **Base:** mesma do `pso_diabetes.py` — coorte bimodal, diabeticos (n=357)
