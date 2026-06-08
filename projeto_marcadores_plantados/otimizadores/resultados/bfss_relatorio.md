# Relatório BFSS — seleção de variáveis (base de marcadores plantados)

## Entradas

- Base: `dados_sinteticos\saida\base_bfss.csv`
- Gabarito: `dados_sinteticos\saida\gabarito_marcadores.json`
- Pacientes: 500 | Atendimentos: 10031 (treino 6977 / teste 3054)

## Parâmetros

| parâmetro | valor |
| :-- | :-- |
| num_fishes | 30 |
| num_iterations | 100 |
| alpha | 0.8 |
| k | 5 |
| thres_c | 0.6 |
| thres_v | 0.4 |
| s_ind_start | 0.1 |
| s_ind_end | 0.001 |
| w_scale | 500.0 |
| seed | 42 |

## Resultado

- **Selecionadas:** 8 de 25
- **Fitness (Eq.10):** 0.8802
- **R² subconjunto:** 0.9303 (baseline todas as variáveis: 0.7858)
- **Avaliações do wrapper:** 3163

## Validação por verdade-base

- **Precisão:** 1.000
- **Recall:** 0.889
- **F1:** 0.941

### Auditoria por variável

| variável | no gabarito | selecionada | resultado |
| :-- | :-- | :-- | :-- |
| NU_IDADE | relevante | sim | ✅ VP |
| EXAME_HBA1C | relevante | sim | ✅ VP |
| DANO_ACUMULADO | relevante | sim | ✅ VP |
| MARCADOR_RESPOSTA | relevante | sim | ✅ VP |
| NIVEL_TRATAMENTO | relevante | sim | ✅ VP |
| IS_RENAL | relevante | sim | ✅ VP |
| IS_CARDIOVASCULAR | relevante | não | ❌ FN |
| IS_RETINOPATIA | relevante | sim | ✅ VP |
| IS_NEUROPATIA | relevante | sim | ✅ VP |
| TEMPO_DIAGNOSTICO | irrelevante | não | ✓ VN |
| IN_SEXO | irrelevante | não | ✓ VN |
| DS_RACA | irrelevante | não | ✓ VN |
| NM_MUNIC | irrelevante | não | ✓ VN |
| INSULINA_MARCA | irrelevante | não | ✓ VN |
| PRESSAO_ARTERIAL | irrelevante | não | ✓ VN |
| RUIDO_01 | irrelevante | não | ✓ VN |
| RUIDO_02 | irrelevante | não | ✓ VN |
| RUIDO_03 | irrelevante | não | ✓ VN |
| RUIDO_04 | irrelevante | não | ✓ VN |
| RUIDO_05 | irrelevante | não | ✓ VN |
| RUIDO_06 | irrelevante | não | ✓ VN |
| RUIDO_07 | irrelevante | não | ✓ VN |
| RUIDO_08 | irrelevante | não | ✓ VN |
| RUIDO_09 | irrelevante | não | ✓ VN |
| RUIDO_10 | irrelevante | não | ✓ VN |
