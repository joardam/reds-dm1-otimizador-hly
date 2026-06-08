# simulador_hly/

Simulador que transforma **perfil + tratamento → Anos de Vida Saudáveis (HLY)**, respeitando os
marcadores plantados.

HLY = **quantidade de vida** (sobrevivência) **×** **qualidade de vida** (sem incapacidade;
estabilidade glicêmica: tempo no alvo, hipoglicemias, variabilidade). A métrica exata de qualidade
ainda será definida (ver `ESTADO_ATUAL.md`, seção 5, item 1).

Arcabouço conceitual: T1D Index (estrutura de anos-saudáveis-perdidos) + relação HbA1c→desfecho do
DCCT/EDIC. **Não** é cópia do T1D Index (que é populacional); é um simulador individual ancorado.

> ✅ **IMPLEMENTADO em 2026-06-07: `modelo_hly.py`.** Forma fechada e determinística (a menos de ruído):
> `ΔHLY = potência(L)·responsividade(M1,M3)·fator_idade·fator_dano(M2)·(1−desconto_comorbidade) + ruído`.
> Inclui a dinâmica longitudinal da HbA1c, o acumulador de dano (M2) e os *hazards* de comorbidade.
> Os números (o "gabarito") estão aqui e em `../dados_sinteticos/MODELO_NUMERICO.md`.
