# simulador_hly/

Simulador que transforma **perfil + tratamento → Anos de Vida Saudáveis (HLY)**, respeitando os
marcadores plantados.

HLY = **quantidade de vida** (sobrevivência) **×** **qualidade de vida** (sem incapacidade;
estabilidade glicêmica: tempo no alvo, hipoglicemias, variabilidade). A métrica exata de qualidade
ainda será definida (ver `ESTADO_ATUAL.md`, seção 5, item 1).

Arcabouço conceitual: T1D Index (estrutura de anos-saudáveis-perdidos) + relação HbA1c→desfecho do
DCCT/EDIC. **Não** é cópia do T1D Index (que é populacional); é um simulador individual ancorado.

> A definir/discutir antes de implementar.
