# Tuning BFSS — grade rápida (subamostrada 2500/1200, 50 iters, 30 peixes, seed 42)

R² baseline (todas as 25 variáveis candidatas): **0.7496**

Objetivo: o recall já chega a 1.0; o tuning busca subir a **precisão** (menos
falsos positivos de ruído) sem perder marcadores relevantes. Parâmetro-chave:
`alpha` da Eq.(10) (parcimônia) + limiares adaptativos `thres_c`/`thres_v`.

## Grade completa (24 configs), ordenada por F1

| alpha | thres_c | thres_v | n_sel | P | R | F1 | R² |
| --: | --: | --: | --: | --: | --: | --: | --: |
| 0.8 | 0.6 | 0.4 | 8 | **1.00** | 0.89 | **0.94** | 0.922 |
| 0.9 | 0.6 | 0.4 | 9 | 0.89 | 0.89 | 0.89 | 0.914 |
| 0.7 | 0.6 | 0.4 | 7 | 1.00 | 0.78 | 0.88 | 0.905 |
| 0.9 | 0.4 | 0.4 | 10 | 0.80 | 0.89 | 0.84 | 0.869 |
| 0.6 | 0.6 | 0.4 | 7 | 0.86 | 0.67 | 0.75 | 0.892 |
| 0.9 | 0.6 | 0.2 | 15 | 0.60 | **1.00** | 0.75 | 0.856 |
| 0.8 | 0.6 | 0.2 | 13 | 0.62 | 0.89 | 0.73 | 0.843 |
| 0.8 | 0.4 | 0.4 | 9 | 0.67 | 0.67 | 0.67 | 0.860 |
| 0.9 | 0.2 | 0.4 | 18 | 0.50 | **1.00** | 0.67 | — |
| 0.7 | 0.2 | 0.2 | 16 | 0.50 | 0.89 | 0.64 | — |
| 0.7 | 0.2 | 0.4 | 16 | 0.50 | 0.89 | 0.64 | — |
| 0.6 | 0.4 | 0.2 | 16 | 0.50 | 0.89 | 0.64 | — |
| 0.6 | 0.6 | 0.2 | 10 | 0.60 | 0.67 | 0.63 | — |
| 0.9 | 0.2 | 0.2 | 17 | 0.47 | 0.89 | 0.62 | — |
| 0.7 | 0.4 | 0.2 | 14 | 0.50 | 0.78 | 0.61 | — |
| 0.7 | 0.4 | 0.4 | 14 | 0.50 | 0.78 | 0.61 | — |
| 0.8 | 0.4 | 0.2 | 14 | 0.50 | 0.78 | 0.61 | — |
| 0.9 | 0.4 | 0.2 | 14 | 0.50 | 0.78 | 0.61 | — |
| 0.7 | 0.6 | 0.2 | 11 | 0.55 | 0.67 | 0.60 | — |
| 0.6 | 0.2 | 0.2 | 13 | 0.46 | 0.67 | 0.55 | — |
| 0.6 | 0.2 | 0.4 | 13 | 0.46 | 0.67 | 0.55 | — |
| 0.6 | 0.4 | 0.4 | 13 | 0.46 | 0.67 | 0.55 | — |
| 0.8 | 0.2 | 0.2 | 15 | 0.40 | 0.67 | 0.50 | — |
| 0.8 | 0.2 | 0.4 | 15 | 0.40 | 0.67 | 0.50 | — |

(Fonte bruta: `tuning_console.log`. Configs com `thres_v=0.2` na metade de baixo;
`R²` preenchido só para o top-8 que o script imprimiu.)

## Leitura

- **`thres_v=0.4` é o fator dominante** para precisão alta: todas as melhores têm `tv=0.4`.
- **Melhor F1 (campeã):** `alpha=0.8, thres_c=0.6, thres_v=0.4` → P=1.00, R=0.89, 8 features.
- **Melhor para recall=1.0:** `alpha=0.9, thres_c=0.6, thres_v=0.2` → P=0.60, R=1.00, 15 features.
- Tradeoff esperado: apertar a parcimônia sobe precisão e custa recall.

> Estabilidade em múltiplos seeds: ver `estabilidade.md`.
