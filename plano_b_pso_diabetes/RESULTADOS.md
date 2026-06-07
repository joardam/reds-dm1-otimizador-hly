# Resultados — PSO sobre diabéticos (bimodal, n=357)

- Indivíduos: 357 (ideais=119, demais=238)
- AUC PSO: treino=0.820 | teste=0.664
- AUC sklearn (baseline): teste=0.664
- Validação PSO×sklearn (cosseno dos pesos): 1.000

## Características do indivíduo ideal (pesos do PSO)

| característica | peso | direção |
|---|---:|---|
| CP2h | +0.338 | mais = ideal |
| BMI | -0.304 | menos = ideal |
| BUN | +0.240 | mais = ideal |
| waist1 | -0.232 | menos = ideal |
| ISIGutt | -0.212 | menos = ideal |
| WHR | -0.193 | menos = ideal |
| hip | -0.167 | menos = ideal |
| SCRE | +0.162 | mais = ideal |
| ALT | -0.134 | menos = ideal |
| FatherDM | -0.119 | menos = ideal |
| HomaIR | -0.115 | menos = ideal |
| DMfamilyHistory | -0.105 | menos = ideal |
| MotherDM | -0.090 | menos = ideal |
| AST | +0.090 | mais = ideal |
| Gender | +0.068 | mais = ideal |
| GGT | +0.067 | mais = ideal |
| FCP | -0.059 | menos = ideal |
| ALB | -0.056 | menos = ideal |
| HR | -0.048 | menos = ideal |
| Smoking | -0.041 | menos = ideal |
| ALP | -0.035 | menos = ideal |
| INS2h | +0.023 | mais = ideal |
| Fat | +0.018 | mais = ideal |
| FINS | -0.016 | menos = ideal |
| Waist2 | +0.010 | mais = ideal |
| TP | -0.002 | menos = ideal |

## Perfil descritivo (média ideais vs demais)

| variável | ideais | demais | dif |
|---|---:|---:|---:|
| BMI | 21.42 | 24.83 | -3.41 |
| waist1 | 75.38 | 82.50 | -7.12 |
| Waist2 | 81.01 | 87.32 | -6.31 |
| hip | 88.34 | 93.59 | -5.25 |
| WHR | 0.85 | 0.88 | -0.03 |
| Fat | 21.00 | 25.74 | -4.74 |
| HR | 77.46 | 78.63 | -1.17 |
| FINS | 8.47 | 12.24 | -3.77 |
| FCP | 2.02 | 2.57 | -0.55 |
| INS2h | 55.14 | 68.67 | -13.53 |
| CP2h | 11.42 | 10.15 | +1.27 |
| HomaIR | 2.85 | 4.53 | -1.68 |
| ISIGutt | 57.26 | 104.76 | -47.50 |
| ALT | 33.35 | 45.69 | -12.34 |
| AST | 53.93 | 50.23 | +3.70 |
| GGT | 133.19 | 125.83 | +7.36 |
| ALP | 93.15 | 95.28 | -2.13 |
| BUN | 5.52 | 5.02 | +0.50 |
| SCRE | 73.61 | 68.81 | +4.80 |
| TP | 76.35 | 76.42 | -0.07 |
| ALB | 46.12 | 46.90 | -0.78 |
| Gender | 1.32 | 1.34 | -0.02 |
| Smoking | 2.29 | 2.18 | +0.11 |
| FatherDM | 0.00 | 0.01 | -0.01 |
| MotherDM | 0.00 | 0.01 | -0.01 |
| DMfamilyHistory | 0.01 | 0.06 | -0.05 |
