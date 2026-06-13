# Roteiro de fala — Slides 9, 10 e 11 + Simulador PSO

> Fala em primeira pessoa, tom acadêmico mas natural. Tempo-alvo: ~1 a 1,5 min por slide.
> `[ação]` = o que fazer; **negrito** = onde dar ênfase; (…) = pausa.

---

## SLIDE 9 — "O otimizador acha o ótimo conhecido"  (~1 min 20 s)

**Objetivo da fala:** deslocar a atenção do AUC (modesto) para a *prova* de que o
otimizador funciona — o cosseno 1,000.

> "Aqui está a pergunta mais importante de qualquer otimizador: **ele realmente acha a
> resposta certa?** (…)
>
> Olhem os números. O AUC de teste deu **0,664** — e o scikit-learn, que resolve o mesmo
> problema de forma analítica, deu **exatamente o mesmo 0,664**. Ou seja: esse 0,664 não
> é fraqueza do nosso PSO, é o **teto do problema** — é até onde esses dados deixam chegar.
>
> [apontar o número 1,000] Agora o que prova o otimizador é isto: o **cosseno entre os
> pesos que o PSO encontrou e os pesos da solução analítica é 1,000**. Não 0,99 — **um
> inteiro**. Os dois vetores apontam exatamente para a mesma direção. (…) O PSO,
> partindo do zero, chegou na **mesma solução** que a matemática fechada.
>
> [apontar a curva] E a convergência mostra o caminho: sobe rápido no começo, depois
> **estabiliza num platô**. É o comportamento de um enxame saudável — ele encontra a
> região boa e assenta nela.
>
> A frase pra levar daqui é: **o AUC mede a dificuldade do problema; o cosseno prova o
> otimizador.** Como o problema é convexo, existe um ótimo conhecido — e nós provamos que
> o PSO chegou nele."

**Transição:** "E se o otimizador chegou na resposta certa… o que essa resposta nos
**conta** sobre o paciente? É o próximo slide."

**Se perguntarem "por que o AUC não é mais alto?"** → "Porque tiramos de propósito as
variáveis que definem o rótulo (idade, HbA1c, comorbidades). O que sobra é o perfil
metabólico *secundário* — mais sutil. Um AUC perto de 1 aqui seria sinal de
circularidade, não de mérito."

---

## SLIDE 10 — "O ganho: o perfil do indivíduo ideal"  (~1 min 20 s)

**Objetivo da fala:** mostrar que o entregável não é um número, é um **perfil clínico
interpretável** — e que ele faz sentido médico.

> "Esse é o **ganho** do trabalho. O PSO não devolve só uma nota: ele devolve um **vetor
> de pesos**, e cada peso tem leitura clínica direta — a **magnitude** diz o quanto a
> característica importa, e o **sinal** diz a direção.
>
> [apontar o gráfico] As mais fortes: **IMC, cintura, gordura corporal** puxando pra
> baixo; **resistência à insulina — o HOMA-IR — também pra baixo**; a **ALT, enzima do
> fígado, mais baixa**; e **sem histórico familiar** de diabetes.
>
> Juntando tudo, o perfil do diabético 'ideal' nesta coorte é: (…) **mais magro, com
> menos resistência à insulina, fígado mais saudável e sem histórico familiar**.
>
> E isso não é invenção do algoritmo — as **médias comparativas** confirmam: o IMC médio
> dos ideais é **21,4 contra 24,8**; o índice de sensibilidade à insulina é quase o
> **dobro**; a ALT é bem mais baixa. (…) O otimizador **redescobriu**, sozinho, um perfil
> que é clinicamente coerente. Esse é o valor: não é só achar o ótimo, é **conseguir
> explicar** o ótimo."

**Transição:** "Esses hiperparâmetros do PSO — quanta inércia, quanta atração — nós não
chutamos. Deixamos **outro algoritmo de enxame** descobrir os melhores. É o slide do
Meta-FSS."

**Se perguntarem "esse perfil vale pro SUS / pra Pernambuco?"** → honestidade:
"Não diretamente — é uma coorte de rastreio da China, 2012, e transversal. Vale como
**associação e como prova de que o otimizador acha um perfil coerente**, não como
recomendação clínica. A base é testbed."

---

## SLIDE 11 — "Meta-FSS: o enxame que ajusta o enxame"  (~1 min 30 s)

**Objetivo da fala:** mostrar sofisticação (otimização em dois níveis) **e** maturidade
(ler o ganho com honestidade). É também onde o **FSS** — a família que dá nome ao
projeto — aparece de fato.

> "Todo PSO tem 'botões' de ajuste: inércia, atração pessoal, atração social,
> regularização. Em vez de calibrar isso na mão, nós usamos **outro algoritmo de enxame,
> o FSS — Fish School Search — para ajustar os botões do PSO**. É uma **otimização em
> dois níveis**: [apontar o fluxo] o FSS otimiza o PSO, que otimiza os pesos da
> regressão. Um enxame governando o outro.
>
> [apontar o gráfico] O FSS encontrou hiperparâmetros um pouco diferentes, e o AUC de
> teste subiu de **0,664 para 0,678**. (…)
>
> Mas aqui vem a parte que eu faço questão de dizer — a **leitura honesta**: esse ganho
> de **+0,014 está dentro da margem de ruído** da estimativa. Com uma amostra de teste
> pequena, o intervalo de confiança é da ordem de **0,68 mais ou menos 0,15**. E parte do
> ganho vem do FSS ter **afrouxado a regularização**, o que ajuda no treino mas tende a
> dar um leve overfitting.
>
> Então o ponto deste slide **não é o número** — é demonstrar que dominamos a **família
> de enxames além do PSO**, e que sabemos exatamente **quanto** podemos concluir de um
> resultado. Para mim, mostrar a margem de ruído vale mais do que vender o 0,678."

**Transição (fecho do bloco):** "Esses três slides respondem à pergunta central: o
otimizador funciona, ele se explica, e nós sabemos seus limites. Se quiserem, dá pra
**ver o enxame trabalhando ao vivo** — é o simulador."

**Se perguntarem "o que é FSS, em uma frase?"** → "É um algoritmo de enxame inspirado em
**cardumes de peixes**: cada peixe se move, ganha ou perde 'peso' conforme melhora, e o
cardume todo migra para a região mais promissora. Mesma ideia do PSO, metáfora diferente."

---

# Como apresentar o SIMULADOR PSO de forma contextual

> Use isto ao abrir a aba **Simulação interativa** do HTML (idealmente logo após o
> slide 9 ou no fim do bloco). A meta é conectar o simulador ao **problema**, não mostrar
> "um gráfico bonito".

## A ponte (a primeira frase, a mais importante)

> "Até agora eu **afirmei** que o PSO acha o ótimo. Agora vocês vão **ver** isso
> acontecer."

## O que é cada elemento (traduzindo a tela para o problema)

- **O relevo / a superfície 3D** é a **paisagem de desempenho real** do problema. Cada
  ponto do chão é uma combinação de pesos; a **altura é o quão bem aquela combinação
  separa o 'indivíduo ideal' dos demais** (o AUC). Pico alto = combinação melhor.
- **Os dois eixos** são os **pesos de duas características clínicas** de verdade — por
  exemplo, o peso do IMC contra o peso da ALT. (O problema real tem 27 eixos; aqui a
  gente corta uma **fatia 2D** pra conseguir enxergar — é uma janela didática, não a
  busca inteira.)
- **A ⭐ no topo** é o **ótimo analítico — o gabarito**. É a resposta que o scikit-learn
  dá. É exatamente o ponto que, lá no slide 9, deu cosseno 1,000.
- **Os pontinhos (o bando)** são as **partículas**: cada uma é uma tentativa de resposta,
  um conjunto de pesos. Os **rastros** mostram o caminho que cada uma percorreu.
- **O movimento** é o PSO de verdade: cada partícula combina **inércia** (segue em
  frente), **memória pessoal** (volta pro melhor lugar que ela já viu) e **influência
  social** (é puxada pro melhor que o bando achou). É essa receita que faz o bando
  **subir o morro e se juntar na estrela**.

## A frase que fecha o sentido

> "Repare: ninguém disse pras partículas onde está o topo. Elas **descobrem** sozinhas,
> só trocando informação entre si. Quando o bando inteiro se junta na estrela, é a versão
> **visual** do nosso cosseno 1,000 — o enxame achou o ótimo conhecido. E cada eixo é uma
> característica clínica real, então o que vocês estão vendo é o método **descobrindo
> quais variáveis importam** para o perfil do paciente ideal."

## Gancho com o horizonte do projeto (opcional, se sobrar tempo)

> "E essa é exatamente a intuição que escala pro Plano A: troquem 'pesos de
> características' por 'políticas de alocação de recursos', e a altura do relevo por
> **Anos de Vida Saudáveis versus custo versus equidade**. O mesmo enxame que sobe esse
> morro é o que vai, no futuro, procurar a melhor política de saúde."

## Dicas de operação (pra não travar ao vivo)

- Comece em **2D** (mais legível), aperte **Play**, deixe convergir, e **só então** vire
  pra **3D** e gire devagar — o "uau" do 3D funciona melhor depois que entenderam o 2D.
- Tenha **um par de características já escolhido** e testado (ex.: IMC × ALT), pra não
  procurar no seletor na hora.
- Se perguntarem por que nem sempre converge perfeito: "com poucas partículas ou um par
  'plano', o relevo tem menos sinal — é honesto, mostra que o método depende da
  informação que existe nos dados."
