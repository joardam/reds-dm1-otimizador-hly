# Estado do projeto (âncora de retomada)

> Resumo curto para retomar rápido após compactar a conversa. Última atualização: 2026-06-06.

## Duas trilhas no repositório

1. **`plano_b_pso_diabetes/` — TRILHA ATIVA (entrega de curto prazo).**
   - Base: "A bimodal dataset for diabetes research" (Zenodo `10.5281/zenodo.18270337`), em `data/`.
     Coorte de rastreio adulto (China, 2012). **Não distingue T1D/T2D** → "diabetes tipo não
     especificado" (não T1D). O entregável é o **otimizador**, a base é testbed.
   - Universo: **diabéticos** (`DM==1`, **n=357**).
   - Método (PSO, Opção B): rótulo "indivíduo ideal" = terço superior de
     `z(idade) − z(HbA1c) − z(comorbidades)`; o **PSO otimiza pesos de uma logística** que prevê esse
     rótulo a partir das *outras* características. `pso_diabetes.py` → `RESULTADOS.md` + 2 PNGs.
   - Resultado: PSO AUC teste ≈ 0,66 = sklearn 0,66; cosseno dos pesos = **1,000** (PSO validado).
     Perfil ideal: mais magro, menos resistência à insulina, ALT menor, menos histórico familiar.
   - Visualizador: `gerar_visualizacao.py` → `pso_visualizacao.html` (PSO 2D interativo no navegador;
     cores por partícula, rastros, controles). É uma **fatia 2D didática** (2 pesos), não as 27D.
   - Como rodar: `pip install numpy pandas scikit-learn matplotlib` e `python3 pso_diabetes.py`.

2. **`projeto_pausado_marcadores_plantados/` — PAUSADO (não abandonado).**
   - Projeto ambicioso original: otimizador multiobjetivo HLY × Custo × Equidade validado por
     marcadores plantados. Canônico: `ESTADO_ATUAL.md` lá dentro (tem todo o histórico de decisões).
   - Pausado em 2026-06-06 por prazo/escopo, após conversa com o orientador.

3. **`old/`** — 1ª tentativa (130-US/CTGAN), arquivada.

## Próximo passo sugerido

Relatório final da entrega (Plano B), e opcionalmente deixar o PSO com seleção de features (L1) para
ter um diferencial sobre a logística analítica.

## Branch

Desenvolvimento em `claude/system-overview-bhZsF`.
