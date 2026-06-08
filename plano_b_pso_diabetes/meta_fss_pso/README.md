# meta_fss_pso — Meta-Otimização: FSS otimiza hiperparâmetros do PSO

> Semana #10 (PSO) x Semana #11 (FSS) da disciplina de Computação Natural.

## O que é este módulo

Usa o **FSS (Fish School Search)** para encontrar automaticamente os melhores hiperparâmetros
do **PSO**, que por sua vez otimiza os pesos da regressão logística para identificar o
"indivíduo ideal" entre 357 diabéticos.

```
FSS (meta-nível)  ->  otimiza  ->  PSO (nível 1)  ->  otimiza  ->  pesos da regressão
[w_in, c1, c2, L]              [pesos do modelo]              [classificação]
```

As funções de **Wellness** e **Fitness** são idênticas ao `pso_diabetes.py`.
O FSS apenas ajusta os hiperparâmetros `w_in, c1, c2, LAMBDA` do PSO.

## Arquitetura e Integração Visual

Este módulo foi refatorado para operar em conjunto com a raiz do projeto. Após gerar os resultados numéricos e visuais, as métricas e os vetores de hiperparâmetros são injetados diretamente na aba **Hiperparâmetros (FSS)** do arquivo `pso_visualizacao.html` gerado pelo `gerar_visualizacao.py` principal, que traz uma tabela comparativa (feature a feature) entre os pesos da execução padrão e os pesos meta-otimizados.

## Como rodar

```bash
cd plano_b_pso_diabetes/meta_fss_pso
python meta_fss_pso.py
```

Tempo estimado de execução: **6-12 minutos**.

*Nota: Após a execução, lembre-se de rodar o `gerar_visualizacao.py` na raiz para atualizar o dashboard HTML.*

## Saídas geradas na pasta

| Arquivo | Conteúdo |
|---|---|
| `RESULTADOS_META.md` | Tabelas estáticas de hiperparâmetros encontrados e a variação da AUC. |
| `resultados_metafss_convergencia.png` | Gráfico: Convergência do fitness (AUC) do meta-FSS por iteração. |
| `resultados_comparacao_convergencia.png` | Gráfico: Convergência do erro no PSO padrão x PSO meta-otimizado. |
| `resultados_importancia_meta.png` | Gráfico: Importância/Pesos das features obtidas com hiperparâmetros otimizados. |
| `ESTRATEGIAS_AUC.md` | Anotações contendo as estratégias arquiteturais (ex: BFSS) para evolução preditiva. |

## Hiperparâmetros otimizados pelo FSS

| Parâmetro | Intervalo de busca | Valor padrão (empírico) |
|---|---|---|
| `w_in` (inércia) | [0.30, 0.95] | 0.70 |
| `c1` (confiança pessoal) | [0.50, 2.50] | 1.50 |
| `c2` (confiança social) | [0.50, 2.50] | 1.50 |
| `LAMBDA` (regularização L2) | [0.001, 0.50] | 0.05 |

## Configuração do experimento

- **meta-FSS:** 15 peixes x 30 iterações
- **PSO interno:** 15 partículas x 80 iterações (leve, para viabilidade computacional)
- **Avaliação:** CV-3 fold no conjunto de treino (evita data leakage durante o ajuste fino)
- **Base:** mesma do `pso_diabetes.py` — coorte bimodal, diabéticos (n=357)
