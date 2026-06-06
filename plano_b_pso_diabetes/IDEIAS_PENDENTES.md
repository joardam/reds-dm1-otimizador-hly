# Ideias pendentes (backlog do Plano B)

> Lista de mudanças a aplicar **no final**, depois que o entendimento estiver consolidado.
> Nada aqui foi feito ainda — é só o registro para não perdermos as ideias.

## A fazer

- [ ] **Tooltips de característica no seletor de par.** Ao passar o mouse (ou ao trocar) no
  seletor "Par de características" da aba Simulação, mostrar uma descrição curta de cada variável
  (ex.: CP2h = peptídeo-C 2h, mede reserva do pâncreas; BMI = IMC; BUN = ureia/função renal;
  waist1 = cintura/gordura abdominal). Pode ser um balãozinho de ajuda por característica.

- [ ] **Tirar a menção a "não em cardumes"** no cartão 3 da Apresentação. A frase
  "inspirado no voo de bandos de pássaros — *não em cardumes*" ficou sem sentido para quem lê,
  porque não há contexto do porquê do contraste. Deixar só "inspirado no voo coordenado de bandos
  de pássaros (Kennedy & Eberhart, 1995)".

- [ ] **Consolidar/expandir a seção de Limitações.** Hoje há um cartão 9 na Apresentação e a
  "Atenção metodológica" no README, mas estão incompletos. Reunir TODAS as limitações num lugar
  claro (cartão da Apresentação + seção no relatório final), incluindo as levantadas durante o
  estudo (lista abaixo). Sempre que, ao explicar o código, surgir um "isso é bom colocar na
  limitação", registrar aqui na hora.

## Limitações levantadas durante o estudo (para incorporar)

> Lista corrente — vai crescendo conforme estudamos os pontos do ROTEIRO_DE_ESTUDO.md.

- **Rótulo "ideal" é uma escolha de projeto** (idade↑ + HbA1c↓ + comorbidades↓). Defensável, mas
  não é a única definição possível; outra equipe poderia pesar diferente. *(ponto 2.1)*
- **Corte do terço (33%) é arbitrário** e gera classes desbalanceadas (119 ideais × 238 demais).
  Não é problema grave (AUC lida bem), mas é uma decisão, não uma verdade. *(ponto 2.3)*
- **Lista de preditoras é curada à mão** (26 de 190 colunas), por conhecimento de domínio — não é
  varredura automática. Prós: interpretável, sem circularidade. Contra: posso ter deixado de fora
  alguma pista boa não pensada. *(ponto 3.1)*
- **Imputação pela mediana "achata" a variação** (preenche vários buracos com o mesmo valor).
  Aceitável com <25% de ausência, mas reduz um pouco a variabilidade real. *(ponto 3.3)*
- **Base não distingue T1D/T2D** → "diabetes tipo não especificado"; é testbed do otimizador.
- **Coorte única (China, 2012) e transversal** → fala de associação, não de causa; não generaliza
  para o Brasil/SUS.

