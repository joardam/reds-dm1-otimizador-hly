# Estabilidade do BFSS (seeds [42, 7, 123, 2024])

Subamostra 2500/1200, 50 iters, 30 peixes.

## Resumo (media +- desvio)

| config | alpha | tc | tv | P | R | F1 | n_sel |
| :-- | --: | --: | --: | --: | --: | --: | --: |
| CAMPEA (F1) | 0.8 | 0.6 | 0.4 | 1.000+-0.000 | 0.889+-0.000 | 0.941+-0.000 | 8.0+-0.0 |
| RECALL_TOTAL | 0.9 | 0.6 | 0.2 | 0.614+-0.030 | 0.972+-0.048 | 0.753+-0.036 | 14.2+-0.4 |

## CAMPEA (F1) - frequencia de selecao por variavel (4 seeds)

| variavel | papel | selecionada (de N seeds) |
| :-- | :-- | --: |
| NU_IDADE | relevante | 4/4 |
| EXAME_HBA1C | relevante | 4/4 |
| DANO_ACUMULADO | relevante | 4/4 |
| MARCADOR_RESPOSTA | relevante | 4/4 |
| NIVEL_TRATAMENTO | relevante | 4/4 |
| IS_RENAL | relevante | 4/4 |
| IS_CARDIOVASCULAR | relevante | 0/4 |
| IS_RETINOPATIA | relevante | 4/4 |
| IS_NEUROPATIA | relevante | 4/4 |
| TEMPO_DIAGNOSTICO | ruido | 0/4 |
| IN_SEXO | ruido | 0/4 |
| DS_RACA | ruido | 0/4 |
| NM_MUNIC | ruido | 0/4 |
| INSULINA_MARCA | ruido | 0/4 |
| PRESSAO_ARTERIAL | ruido | 0/4 |
| RUIDO_01 | ruido | 0/4 |
| RUIDO_02 | ruido | 0/4 |
| RUIDO_03 | ruido | 0/4 |
| RUIDO_04 | ruido | 0/4 |
| RUIDO_05 | ruido | 0/4 |
| RUIDO_06 | ruido | 0/4 |
| RUIDO_07 | ruido | 0/4 |
| RUIDO_08 | ruido | 0/4 |
| RUIDO_09 | ruido | 0/4 |
| RUIDO_10 | ruido | 0/4 |

## RECALL_TOTAL - frequencia de selecao por variavel (4 seeds)

| variavel | papel | selecionada (de N seeds) |
| :-- | :-- | --: |
| NU_IDADE | relevante | 4/4 |
| EXAME_HBA1C | relevante | 4/4 |
| DANO_ACUMULADO | relevante | 4/4 |
| MARCADOR_RESPOSTA | relevante | 4/4 |
| NIVEL_TRATAMENTO | relevante | 4/4 |
| IS_RENAL | relevante | 4/4 |
| IS_CARDIOVASCULAR | relevante | 3/4 |
| IS_RETINOPATIA | relevante | 4/4 |
| IS_NEUROPATIA | relevante | 4/4 |
| TEMPO_DIAGNOSTICO | ruido | 1/4 |
| IN_SEXO | ruido | 1/4 |
| DS_RACA | ruido | 0/4 |
| NM_MUNIC | ruido | 0/4 |
| INSULINA_MARCA | ruido | 1/4 |
| PRESSAO_ARTERIAL | ruido | 1/4 |
| RUIDO_01 | ruido | 2/4 |
| RUIDO_02 | ruido | 3/4 |
| RUIDO_03 | ruido | 4/4 |
| RUIDO_04 | ruido | 1/4 |
| RUIDO_05 | ruido | 1/4 |
| RUIDO_06 | ruido | 1/4 |
| RUIDO_07 | ruido | 3/4 |
| RUIDO_08 | ruido | 2/4 |
| RUIDO_09 | ruido | 0/4 |
| RUIDO_10 | ruido | 1/4 |
