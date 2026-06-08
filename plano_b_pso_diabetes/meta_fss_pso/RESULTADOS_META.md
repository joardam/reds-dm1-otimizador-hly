# Resultados — Meta-Otimizacao: FSS -> PSO -> Logistica

## Configuracao do experimento

- **meta-FSS:** 15 peixes x 30 iteracoes
- **PSO interno:** 15 particulas x 80 iteracoes
- **Avaliacao:** CV-3 fold no conjunto de treino

## Hiperparametros encontrados pelo meta-FSS

| hiperparametro | valor (FSS) | valor padrao | variacao |
|---|---:|---:|---:|
| w_in | 0.6661 | 0.7000 | -0.0339 |
| c1 | 0.7366 | 1.5000 | -0.7634 |
| c2 | 0.5915 | 1.5000 | -0.9085 |
| lam | 0.0159 | 0.0500 | -0.0341 |

## Comparacao de AUC

| configuracao | AUC treino | AUC teste |
|---|---:|---:|
| PSO meta-otimizado (FSS) | 0.8368 | 0.6779 |
| PSO padrao (empirico)    | 0.8207 | 0.6640 |

## Validacao

- **Cosseno pesos PSO-meta x PSO-padrao:** 0.701
  (proximo de 1.0 -> ambos convergem na mesma direcao)

## Interpretacao

O meta-FSS encontrou hiperparametros que melhoraram a AUC de teste.

## Saidas geradas

- `resultados_metafss_convergencia.png` — convergencia do meta-FSS
- `resultados_comparacao_convergencia.png` — PSO padrao x PSO meta-otimizado
- `resultados_importancia_meta.png` — importancia das features (PSO meta)
