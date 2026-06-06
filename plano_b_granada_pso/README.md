# Plano B — T1DiabetesGranada + PSO (entrega de curto prazo)

> **Status: INÍCIO — 2026-06-06.** Plano B de **fácil implementação**, escolhido após conversa com o
> orientador (o plano ambicioso ficou em `../projeto_pausado_marcadores_plantados/`). Meta: algo
> **minimamente apresentável dentro do prazo**.

## Ideia (como o usuário descreveu)

1. Usar a base real **T1DiabetesGranada** (736 pacientes, 100% DM1, idade 12–81, ~4 anos, HbA1c,
   ICD-9, CGM; **sem medicamentos** — acesso via Zenodo).
2. Aplicar **PSO** (Particle Swarm Optimization) — o algoritmo de Computação Natural exigido.
3. **Identificar o(s) melhor(es) indivíduo(s)** e depois **correlacionar**: com base nesses indivíduos
   ótimos, **quais características eles têm em comum**.
4. Critério provisório de "melhor indivíduo": **idade**, **poucas comorbidades** e **hemoglobina (HbA1c)
   ideal**.

## ⚠️ Pontos a resolver antes de codar (conversa honesta — ver chat)

- **Acesso aos dados:** T1DiabetesGranada exige solicitação no Zenodo (termo de uso). Precisamos
  **confirmar que conseguimos baixar** (ou o usuário sobe o arquivo no repo). É o caminho crítico.
- **Papel real do PSO:** "achar o melhor indivíduo" numa base fixa com um score fixo é só **ordenar**
  (argmax) — PSO não faria trabalho de verdade. Precisamos de um enquadramento onde o PSO **otimize
  algo contínuo**. Duas opções fáceis e defensáveis (a decidir):
  - **(A) Perfil ideal sintético:** PSO busca no espaço de características o perfil que maximiza o score
    de saúde; depois caracterizamos esse perfil e achamos os pacientes reais mais próximos.
  - **(B) Modelo otimizado por PSO (recomendado):** define-se um rótulo de "bom desfecho"; o PSO otimiza
    os **pesos de um modelo** (ex.: regressão/classificador) que prevê esse rótulo a partir das *outras*
    características → os pesos altos = "quais características o indivíduo ótimo tem". Responde direto à
    pergunta 3, é PSO de verdade, e é simples.

## Próximos passos

1. Confirmar acesso/posse da base (crítico).
2. Escolher o enquadramento do PSO (A ou B).
3. Definir o score/rótulo de "melhor indivíduo" (idade ↑, comorbidades ↓, HbA1c ~7%).
4. Implementar (Python: pandas + um PSO simples) e interpretar os resultados.
