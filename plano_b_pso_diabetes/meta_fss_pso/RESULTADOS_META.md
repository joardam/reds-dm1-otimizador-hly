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

O meta-FSS encontrou hiperparametros com AUC de teste marginalmente maior
(0.6779 vs 0.6640, +0.014). Esse ganho, porem, deve ser lido com cautela —
ver a secao de ressalvas abaixo.

## Ressalvas sobre robustez (overfitting e ruido da estimativa)

Esta observacao foi adicionada apos revisao do experimento e nao invalida o
resultado; apenas delimita o quanto se pode concluir dele.

- **Overfitting leve a moderado.** Ha um gap treino->teste de ~0.16 de AUC
  (0.84 -> 0.68). O modelo ajusta o treino visivelmente melhor do que
  generaliza. Note que o meta-FSS escolheu `lam = 0.0159` (abaixo do padrao
  0.05), ou seja, **reduziu a regularizacao L2** — o que sobe o AUC de treino
  e tende a aumentar o overfitting. Parte do "ganho" do meta-FSS vem desse
  afrouxamento, perseguido via CV de treino.

- **AUC de teste e uma estimativa ruidosa.** O 0.6779 foi medido em UM unico
  split de ~107 amostras (~36 positivos). O erro-padrao aproximado do AUC
  (Hanley-McNeil, `~sqrt(AUC*(1-AUC)/n_pos)`) fica em ~0.07, o que da um
  IC 95% de aproximadamente **0.68 +/- 0.15** (~[0.53, 0.83]). A diferenca de
  0.014 entre meta e padrao esta **dentro dessa faixa de ruido** — nao e um
  ganho estatisticamente robusto.

- **Sem data leakage relevante na busca.** A busca de hiperparametros so usa o
  conjunto de treino (CV-3 interno); o teste nunca e tocado durante o ajuste.
  O unico ponto a higienizar e benigno: o z-score das preditoras e o corte de
  quantil do rotulo sao computados sobre o dataset inteiro antes do split
  (leakage de normalizacao leve), o que nao infla os numeros observados.

- **Como confirmar o numero real.** Para saber se a AUC "segura" e se o ganho
  do meta-FSS sobrevive a variancia, usar repeated/k-fold CV sobre o dataset
  inteiro (media +/- desvio) em vez de um unico split de 107 amostras.

## Saidas geradas

- `resultados_metafss_convergencia.png` — convergencia do meta-FSS
- `resultados_comparacao_convergencia.png` — PSO padrao x PSO meta-otimizado
- `resultados_importancia_meta.png` — importancia das features (PSO meta)
