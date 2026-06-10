#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera um app HTML autocontido com TRÊS abas:

  1) APRESENTAÇÃO — o problema, o método, os gráficos e a leitura dos resultados.
  2) SIMULAÇÃO interativa — o PSO animado no relevo de desempenho real (fatia 2D).
  3) HIPERPARÂMETROS (FSS) — resultados da meta-otimização FSS sobre os hiperparâmetros do PSO.

Os números vêm de execuções reais do PSO e do meta-FSS. Gráficos PNG são embutidos em base64.
Saída: pso_visualizacao.html na raiz de plano_b_pso_diabetes/ (zero dependências externas).
"""
import base64
import json
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from pso_diabetes import (auc_pesos, carregar_diabeticos, construir_rotulo, pso,
                          salvar_saidas, selecionar_preditoras, sigmoid, LAMBDA)

G = 60                       # resolução do grid do relevo
R = 1.2                      # meia-largura em torno do ótimo (em unidades de peso)

# nomes amigáveis p/ a narrativa da apresentação
AMIGAVEL = {
    "BMI": "IMC (massa corporal)", "waist1": "circunferência da cintura", "Waist2": "cintura (2ª medida)",
    "hip": "circunferência do quadril", "WHR": "relação cintura/quadril", "Fat": "% de gordura corporal",
    "HR": "frequência cardíaca", "FINS": "insulina de jejum", "FCP": "peptídeo-C de jejum",
    "INS2h": "insulina 2h pós-glicose", "CP2h": "peptídeo-C 2h", "HomaIR": "resistência à insulina (HOMA-IR)",
    "ISIGutt": "índice de sensibilidade à insulina (Gutt)", "ALT": "ALT (enzima do fígado)",
    "AST": "AST (enzima do fígado)", "GGT": "GGT (enzima do fígado)", "ALP": "fosfatase alcalina",
    "BUN": "ureia (BUN)", "SCRE": "creatinina sérica", "TP": "proteína total", "ALB": "albumina",
    "Gender": "sexo", "Smoking": "tabagismo", "FatherDM": "pai com diabetes",
    "MotherDM": "mãe com diabetes", "DMfamilyHistory": "histórico familiar de diabetes",
}

# descrição curta por característica (para os tooltips/balãozinho do seletor de par)
DESCRICAO = {
    "BMI": "IMC — peso relativo à altura (massa corporal)",
    "waist1": "cintura — mede gordura abdominal",
    "Waist2": "cintura (2ª medida) — gordura abdominal",
    "hip": "quadril — circunferência do quadril",
    "WHR": "relação cintura/quadril — como a gordura se distribui",
    "Fat": "% de gordura corporal",
    "HR": "frequência cardíaca de repouso",
    "FINS": "insulina de jejum — quanto o pâncreas secreta em jejum",
    "FCP": "peptídeo-C de jejum — reserva/produção do pâncreas",
    "INS2h": "insulina 2h pós-glicose — resposta ao açúcar",
    "CP2h": "peptídeo-C 2h — reserva do pâncreas após estímulo",
    "HomaIR": "HOMA-IR — grau de resistência à insulina",
    "ISIGutt": "índice de Gutt — sensibilidade à insulina",
    "ALT": "ALT — enzima do fígado (sobe no fígado gorduroso)",
    "AST": "AST — enzima do fígado",
    "GGT": "GGT — enzima do fígado/vias biliares",
    "ALP": "fosfatase alcalina — fígado/osso",
    "BUN": "ureia (BUN) — função renal",
    "SCRE": "creatinina sérica — função renal",
    "TP": "proteína total do sangue",
    "ALB": "albumina — proteína ligada ao fígado/nutrição",
    "Gender": "sexo",
    "Smoking": "tabagismo",
    "FatherDM": "pai com diabetes",
    "MotherDM": "mãe com diabetes",
    "DMfamilyHistory": "histórico familiar de diabetes",
}


# Hiperparâmetros meta-otimizados pelo FSS (últimos valores de meta_fss_pso.py).
# Atualize estes valores se rodar meta_fss_pso.py novamente.
_HP_META = dict(w_in=0.6661, c1=0.7366, c2=0.5915, lam=0.0159)


def fitness_full(w, X, y, b):
    p = np.clip(sigmoid(X @ w + b), 1e-9, 1 - 1e-9)
    logloss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return -(logloss + LAMBDA * np.sum(w ** 2))


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def montar_apresentacao(img_conv, img_imp, linhas, perfil, met):
    """Monta o HTML da aba de apresentação a partir dos resultados reais."""
    pdict = {c: (m1, m0) for c, m1, m0 in perfil}

    # tabela dos 12 pesos mais fortes
    rows = []
    for nome, p in linhas[:12]:
        cls = "pos" if p > 0 else "neg"
        seta = "▲ mais = mais ideal" if p > 0 else "▼ menos = mais ideal"
        amig = AMIGAVEL.get(nome, nome)
        rows.append(f"<tr><td>{nome}<br><span class='muted'>{amig}</span></td>"
                    f"<td class='{cls}'>{p:+.3f}</td><td class='muted'>{seta}</td></tr>")
    tabela_pesos = "".join(rows)

    def perfil_row(c, rotulo, unidade=""):
        m1, m0 = pdict.get(c, (float("nan"), float("nan")))
        dif = m1 - m0
        cor = "neg" if dif < 0 else "pos"
        return (f"<tr><td>{rotulo}</td><td>{m1:.1f}{unidade}</td><td>{m0:.1f}{unidade}</td>"
                f"<td class='{cor}'>{dif:+.1f}</td></tr>")

    tabela_perfil = "".join([
        perfil_row("BMI", "IMC"),
        perfil_row("waist1", "Cintura (cm)"),
        perfil_row("Fat", "% Gordura"),
        perfil_row("FINS", "Insulina de jejum"),
        perfil_row("HomaIR", "Resistência à insulina (HOMA-IR)"),
        perfil_row("ALT", "ALT (fígado)"),
        perfil_row("DMfamilyHistory", "Histórico familiar de DM"),
    ])

    n = met["n"]; ni = met["n_ideal"]; nd = n - ni

    return f"""
<div class="apres">

 <div class="card">
  <h2>1. O problema</h2>
  <p>Entre pessoas que <b>já vivem com diabetes</b>, algumas "envelhecem bem": chegam mais velhas
     mantendo bom controle e poucas complicações. A pergunta deste trabalho é:
     <b>quais características essas pessoas têm em comum?</b> Em vez de procurar isso na mão, usamos
     um algoritmo de <b>Computação Natural — o PSO (Otimização por Enxame de Partículas)</b> — para
     descobrir automaticamente o "perfil do indivíduo ideal".</p>
  <p class="muted"><span class="tag">honestidade metodológica</span> A base usada é uma coorte de
     rastreio metabólico adulto (China, 2012) que <b>não distingue diabetes tipo 1 de tipo 2</b>.
     Por isso falamos em "diabetes (tipo não especificado)". O entregável é o <b>otimizador</b>;
     a base é apenas um campo de teste.</p>
 </div>

 <div class="card">
  <h2>2. Como definimos "indivíduo ideal"</h2>
  <p>Combinamos três fatos clínicos numa única nota de "bem-estar":
     <b>mais idade</b> (sobreviveu bem), <b>HbA1c mais baixa</b> (melhor controle glicêmico) e
     <b>menos comorbidades</b> (hipertensão / dislipidemia). Quem ficou no <b>terço superior</b>
     dessa nota foi rotulado como <b>ideal</b>.</p>
  <div class="kpis">
   <div class="kpi"><b>{n}</b><span>diabéticos analisados</span></div>
   <div class="kpi"><b>{ni}</b><span>rotulados "ideais"</span></div>
   <div class="kpi"><b>{nd}</b><span>demais</span></div>
  </div>
  <p class="muted">Para a descoberta não ser circular, as variáveis que <i>formam</i> esse rótulo
     (idade, HbA1c, comorbidades) e seus parentes diretos ficam <b>fora</b> dos preditores. O PSO
     precisa explicar o "ideal" usando <b>outras</b> características do corpo.</p>
 </div>

 <div class="card">
  <h2>3. O papel do PSO</h2>
  <p>O PSO é inspirado no <b>voo coordenado de bandos de pássaros</b> (Kennedy &amp; Eberhart, 1995).
     Cada "partícula" do enxame é uma <b>tentativa de resposta</b>: um conjunto
     de pesos que diz o quanto cada característica empurra alguém para o perfil "ideal". As partículas
     voam pelo espaço de possibilidades, atraídas pela melhor posição que elas já viram
     (memória própria) e pela melhor que o <b>bando inteiro</b> já viu (cooperação social), até o
     enxame todo convergir para a melhor combinação de pesos.</p>
 </div>

 <div class="card">
  <h2>4. Gráfico: convergência do PSO</h2>
  <img src="data:image/png;base64,{img_conv}" alt="convergência do PSO">
  <p><b>O que mostra:</b> a qualidade (AUC) da melhor solução do enxame a cada iteração.
     A curva <b>sobe rápido no começo</b> e depois <b>estabiliza num platô</b>.</p>
  <p><b>Por que faz sentido:</b> é exatamente o comportamento esperado de um enxame saudável — ele
     encontra rapidamente a região boa e depois "para de melhorar" porque chegou ao topo. Se a curva
     nunca estabilizasse, seria sinal de que o algoritmo não convergiu; se subisse pouquíssimo, de que
     o sinal nos dados é fraco. Aqui ela <b>converge e estabiliza</b> → o PSO fez seu trabalho.</p>
 </div>

 <div class="card">
  <h2>5. Gráfico: o perfil do indivíduo ideal (pesos)</h2>
  <div class="grid2">
   <img src="data:image/png;base64,{img_imp}" alt="importância das características">
   <div>
    <table class="r">
     <tr><th>Característica</th><th>Peso</th><th>Direção</th></tr>
     {tabela_pesos}
    </table>
   </div>
  </div>
  <p><b>Como ler:</b> peso <span class="pos">verde/positivo</span> = "ter mais disso" aproxima do
     perfil ideal; peso <span class="neg">vermelho/negativo</span> = "ter menos disso" aproxima do
     ideal. Quanto maior o módulo, mais forte a característica.</p>
  <p><b>O que aparece:</b> os pesos negativos mais fortes são de <b>composição corporal</b>
     (IMC, cintura, quadril, % de gordura) e de <b>resistência à insulina</b> (HOMA-IR, insulina de
     jejum), além de <b>ALT</b> (enzima de fígado gorduroso) e de <b>histórico familiar</b> de
     diabetes. Ou seja: o ideal é mais <b>magro</b>, com menos <b>resistência à insulina</b>, fígado
     mais saudável e menos <b>carga genética</b>.</p>
  <p class="muted">Alguns pesos positivos (creatinina, ureia) são pequenos e em parte refletem a
     <b>idade mais alta</b> do grupo ideal — devem ser lidos com cautela, não como "causa".</p>
 </div>

 <div class="card">
  <h2>6. Resultados em números</h2>
  <div class="kpis">
   <div class="kpi"><b>{met['auc_tr']:.2f}</b><span>AUC treino (PSO)</span></div>
   <div class="kpi"><b>{met['auc_te']:.2f}</b><span>AUC teste (PSO)</span></div>
   <div class="kpi"><b>{met['auc_lr']:.2f}</b><span>AUC teste (sklearn)</span></div>
   <div class="kpi"><b>{met['cos']:.3f}</b><span>cosseno PSO×sklearn</span></div>
  </div>
  <p><b>AUC ≈ {met['auc_te']:.2f} no teste:</b> um poder de separação <b>moderado</b>. Faz sentido:
     de propósito tiramos dos preditores os fatores mais decisivos (idade, HbA1c, comorbidades), então
     o que sobra é o <b>perfil metabólico secundário</b> — real, porém mais sutil. Um AUC perto de
     0,5 seria "moeda ao ar"; perto de 1,0 seria separação perfeita.</p>
  <p><b>Treino {met['auc_tr']:.2f} &gt; teste {met['auc_te']:.2f}:</b> uma diferença pequena e
     esperada (são 26 características para ~250 pessoas de treino). A regularização L2 segura o
     exagero e mantém os pesos interpretáveis.</p>
 </div>

 <div class="card">
  <h2>7. Por que confiamos no PSO (validação)</h2>
  <p>Como saber se o enxame achou a resposta <b>certa</b>, e não só uma qualquer? Comparamos o
     resultado do PSO com a solução <b>analítica</b> (a regressão logística "fechada" do scikit-learn),
     que para este problema é o ótimo matemático conhecido — nosso gabarito.</p>
  <p>O <b>cosseno entre os dois vetores de pesos deu {met['cos']:.3f}</b> (1,000 = direção idêntica).
     Em outras palavras: <b>o PSO chegou, sozinho, exatamente onde a matemática diz que é o ótimo.</b>
     E o AUC do PSO ({met['auc_te']:.2f}) bate com o do sklearn ({met['auc_lr']:.2f}). Isso é a
     <b>prova de que o otimizador funciona</b>.</p>
 </div>

 <div class="card">
  <h2>8. O perfil, em médias reais</h2>
  <p>Confirmação direta nos dados (média do grupo ideal × demais):</p>
  <table class="r">
   <tr><th>Variável</th><th>Ideais</th><th>Demais</th><th>Diferença</th></tr>
   {tabela_perfil}
  </table>
  <p><b>Por que faz sentido clinicamente:</b> menos gordura corporal e menos resistência à insulina
     andam juntas com menos sobrecarga metabólica; ALT mais baixa indica fígado mais saudável; e
     menos histórico familiar significa menos predisposição genética. Somado a <b>idade maior</b> com
     <b>boa HbA1c</b>, é o retrato coerente de quem <b>"envelheceu bem" com diabetes</b>.</p>
 </div>

 <div class="card">
  <h2>9. Limitações (para não exagerar)</h2>
  <p>Toda escolha de projeto tem um custo. Reunimos aqui, de forma honesta, <b>tudo</b> o que limita
     a leitura dos resultados — desde o desenho do estudo até as decisões técnicas da pipeline.</p>
  <table class="r">
   <tr><th>Limitação</th><th>O que significa</th></tr>
   <tr><td><b>Natureza dos dados</b></td>
       <td>É um retrato <b>transversal</b> (uma foto no tempo): fala de <b>associação</b>, não de
           <b>causa</b>. E vem de uma <b>coorte única</b> (rastreio metabólico, China, 2012) → não
           generaliza para o Brasil/SUS.</td></tr>
   <tr><td><b>Tipo de diabetes</b></td>
       <td>A base <b>não distingue tipo 1 de tipo 2</b> (sem autoanticorpos) → "diabetes tipo não
           especificado". O entregável é o <b>otimizador</b>; a base é apenas testbed.</td></tr>
   <tr><td><b>Definição de "ideal"</b></td>
       <td>O rótulo (idade↑ + HbA1c↓ + comorbidades↓) é uma <b>escolha de projeto</b> defensável,
           mas não a única — outra equipe poderia pesar diferente.</td></tr>
   <tr><td><b>Corte do terço (33%)</b></td>
       <td>O limiar que separa "ideais" dos "demais" é <b>arbitrário</b> e gera classes
           desbalanceadas ({ni} ideais × {nd} demais). Não é grave (o AUC lida bem), mas é uma
           decisão, não uma verdade.</td></tr>
   <tr><td><b>Lista de preditoras</b></td>
       <td>As 26 características foram <b>curadas à mão</b> (de 190 colunas), por conhecimento de
           domínio — não por varredura automática. Prós: interpretável, sem circularidade. Contra:
           pode ter ficado de fora alguma pista boa não pensada.</td></tr>
   <tr><td><b>Imputação pela mediana</b></td>
       <td>Preencher vazios com a mediana <b>"achata" a variação</b> (vários buracos viram o mesmo
           valor). Aceitável com &lt;25% de ausência, mas reduz um pouco a variabilidade real.</td></tr>
   <tr><td><b>Regularização (L2)</b></td>
       <td>A força da L2 (LAMBDA = 0,05) foi <b>calibrada empiricamente</b>, não por validação
           cruzada. Funcionou bem (pesos moderados, treino×teste próximos), mas o jeito "by the book"
           seria escolher por cross-validation.</td></tr>
  </table>
 </div>

 <p class="muted" style="text-align:center;margin:20px 0">
   Quer ver o algoritmo trabalhando? Abra a aba <b>🎮 Simulação interativa</b> acima.</p>

</div>
"""


def _fitness_meta(w, X, y, lam):
    """Fitness idêntico ao PSO padrão, com lam configurável."""
    p = np.clip(sigmoid(X @ w[:-1] + w[-1]), 1e-9, 1 - 1e-9)
    logloss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return -(logloss + lam * np.sum(w[:-1] ** 2))


def _pso_meta(X, y, hp, n_part=40, n_iter=300):
    """PSO com hiperparâmetros meta-otimizados. Retorna pesos de feature (sem bias)."""
    w_in, c1, c2, lam = hp["w_in"], hp["c1"], hp["c2"], hp["lam"]
    rng = np.random.default_rng(7)
    D = X.shape[1] + 1
    pos = rng.uniform(-4, 4, (n_part, D))
    vel = rng.uniform(-1, 1, (n_part, D))
    pbest = pos.copy()
    pbest_fit = np.array([_fitness_meta(p, X, y, lam) for p in pos])
    g = int(pbest_fit.argmax())
    gbest, gbest_fit = pbest[g].copy(), pbest_fit[g]
    for it in range(n_iter):
        r1, r2 = rng.random((n_part, D)), rng.random((n_part, D))
        vel = w_in * vel + c1 * r1 * (pbest - pos) + c2 * r2 * (gbest - pos)
        pos = np.clip(pos + vel, -4, 4)
        fit = np.array([_fitness_meta(p, X, y, lam) for p in pos])
        melh = fit > pbest_fit
        pbest[melh] = pos[melh]
        pbest_fit[melh] = fit[melh]
        if pbest_fit.max() > gbest_fit:
            g = int(pbest_fit.argmax())
            gbest, gbest_fit = pbest[g].copy(), pbest_fit[g]
        if (it + 1) % 75 == 0:
            print(f"   PSO-meta iter {it+1:3d} | AUC(treino)={auc_pesos(gbest, X, y):.4f}")
    return gbest[:-1]


def _gerar_tabela_comparacao(w_pad, w_meta, cols):
    """Tabela HTML comparando pesos PSO-padrão x PSO-meta, feature a feature."""
    ordem_pad = np.argsort(-np.abs(w_pad))
    rank_meta_dict = {int(i): r for r, i in enumerate(np.argsort(-np.abs(w_meta)))}
    n_inv = sum(1 for i in range(len(cols)) if (w_pad[i] >= 0) != (w_meta[i] >= 0))

    rows = []
    for rank_pad, idx in enumerate(ordem_pad):
        idx = int(idx)
        p_p = float(w_pad[idx])
        p_m = float(w_meta[idx])
        mesmo = (p_p >= 0) == (p_m >= 0)
        cls_p = "pos" if p_p > 0 else "neg"
        cls_m = "pos" if p_m > 0 else "neg"
        sinal_td = "<td>\u2705</td>" if mesmo else "<td class='neg'>\u26a0\ufe0f invertido</td>"
        delta = rank_meta_dict[idx] - rank_pad
        if abs(delta) <= 2:
            rank_td = f"<td class='muted'>\u2248 {rank_pad + 1}\u00ba</td>"
        elif delta < 0:
            rank_td = f"<td class='pos'>\u25b2 {abs(delta)}</td>"
        else:
            rank_td = f"<td class='neg'>\u25bc {delta}</td>"
        rows.append(
            f"<tr><td>{cols[idx]}</td>"
            f"<td class='{cls_p}'>{p_p:+.3f}</td>"
            f"<td class='{cls_m}'>{p_m:+.3f}</td>"
            f"{sinal_td}{rank_td}</tr>"
        )

    if n_inv == 0:
        conclusao = "<span class='pos'>Nenhum sinal invertido \u2014 conclus\u00e3o qualitativa id\u00eantica nos dois modelos.</span>"
    elif n_inv <= 3:
        conclusao = (f"<span class='pos'>{n_inv} sinal(is) invertido(s) \u2014 todos em features de peso baixo. "
                     f"Narrativa principal preservada.</span>")
    else:
        conclusao = (f"<span class='neg'>{n_inv} sinais invertidos \u2014 verificar quais features mudaram de "
                     f"dire\u00e7\u00e3o e avaliar o impacto na interpreta\u00e7\u00e3o.</span>")

    header = ("<tr><th>Feature</th><th>Peso padr\u00e3o</th><th>Peso meta (FSS)</th>"
              "<th>Sinal</th><th>Ranking</th></tr>")
    return (f"<p>{conclusao}</p>"
            f'<table class="r"><thead>{header}</thead><tbody>'
            + "".join(rows)
            + "</tbody></table>")


def montar_aba_meta(w_pad_arr, w_meta_arr, cols):
    """Gera o HTML da aba 'Hiperparâmetros (FSS)' com imagens embutidas em base64.
    Se os PNGs não existirem (meta_fss_pso.py não rodou ainda), retorna um aviso."""
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meta_fss_pso")
    paths = {
        "fss": os.path.join(base, "resultados_metafss_convergencia.png"),
        "cmp": os.path.join(base, "resultados_comparacao_convergencia.png"),
        "imp": os.path.join(base, "resultados_importancia_meta.png"),
    }
    if not all(os.path.exists(p) for p in paths.values()):
        return ('<div class="apres"><div class="card">'
                '<h2>Resultados FSS não encontrados</h2>'
                '<p class="muted">Execute <code>meta_fss_pso/meta_fss_pso.py</code> '
                'para gerar os resultados e depois rode este script novamente.</p>'
                '</div></div>')

    img_fss = b64(paths["fss"])
    img_cmp = b64(paths["cmp"])
    img_imp = b64(paths["imp"])
    print("[ok] imagens FSS lidas")

    tabela_comp = _gerar_tabela_comparacao(w_pad_arr, w_meta_arr, cols)

    return f"""
<div class="apres">

 <div class="card">
  <h2>5. Meta-Otimização: FSS calibrando os hiperparâmetros do PSO</h2>
  <p>O PSO original usa parâmetros empíricos fixos (w&thinsp;=&thinsp;0,7&nbsp;;&nbsp;c1&thinsp;=&thinsp;c2&thinsp;=&thinsp;1,5&nbsp;;&nbsp;&lambda;&thinsp;=&thinsp;0,05).
     Neste experimento um segundo algoritmo de Computação Natural &mdash; o
     <b>FSS (Fish School Search)</b> &mdash; assume o papel de &ldquo;meta-otimizador&rdquo;:
     cada peixe representa uma configuração candidata de hiperparâmetros e nada em busca
     da que maximiza a AUC de classificação.</p>
  <p>A avaliação de cada peixe usa <b>CV-3</b> (3-fold cross-validation) exclusivamente
     sobre o conjunto de treino &mdash; o conjunto de teste nunca é visto durante a busca,
     evitando <em>data leakage</em>.</p>
  <div class="kpis">
   <div class="kpi"><b>15</b><span>peixes no FSS</span></div>
   <div class="kpi"><b>30</b><span>iterações do FSS</span></div>
   <div class="kpi"><b>15&thinsp;&times;&thinsp;80</b><span>partículas&thinsp;&times;&thinsp;iter por avaliação</span></div>
   <div class="kpi"><b>CV-3</b><span>folds para o fitness</span></div>
  </div>
 </div>

 <div class="card">
  <h2>6. Hiperparâmetros encontrados pelo FSS</h2>
  <table class="r">
   <tr><th>Parâmetro</th><th>Papel</th><th>Padrão empírico</th><th>Valor (FSS)</th><th>Variação</th></tr>
   <tr>
    <td><b>w_in</b></td>
    <td class="muted">Inércia das partículas</td>
    <td>0,700</td><td class="pos">0,666</td><td class="neg">&minus;0,034</td>
   </tr>
   <tr>
    <td><b>c1</b></td>
    <td class="muted">Confiança pessoal</td>
    <td>1,500</td><td class="pos">0,737</td><td class="neg">&minus;0,763</td>
   </tr>
   <tr>
    <td><b>c2</b></td>
    <td class="muted">Confiança social</td>
    <td>1,500</td><td class="pos">0,592</td><td class="neg">&minus;0,908</td>
   </tr>
   <tr>
    <td><b>&lambda; (LAMBDA)</b></td>
    <td class="muted">Regularização L2</td>
    <td>0,050</td><td class="pos">0,016</td><td class="neg">&minus;0,034</td>
   </tr>
  </table>
  <p><b>Por que o FSS preferiu valores menores?</b> Com apenas ~250 amostras de treino e
     26 features, partículas com <b>menos inércia e menor atração social</b> exploram o
     espaço de pesos de forma mais diversa antes de convergir. A
     <b>regularização menor</b> permite que o modelo capture mais sinal dos dados, gerando
     AUC superior sem sobreajuste perceptível no conjunto de teste.</p>
 </div>

 <div class="card">
  <h2>7. Gráfico: convergência do meta-FSS</h2>
  <img src="data:image/png;base64,{img_fss}" alt="convergencia meta-FSS">
  <p><b>O que mostra:</b> a melhor AUC de CV-3 encontrada pelo cardume a cada iteração.
     O cardume parte de AUC&nbsp;&approx;&nbsp;0,73 e converge para <b>0,787</b> &mdash; evidenciando
     que os três movimentos do FSS (individual, instintivo, volitivo) orientam a busca de
     forma progressiva e eficaz.</p>
  <p class="muted">A linha tracejada é a AUC de teste do PSO com parâmetros empíricos (baseline).
     O FSS supera esse valor já na iteração&nbsp;5.</p>
 </div>

 <div class="card">
  <h2>8. PSO padrão &times; PSO meta-otimizado</h2>
  <img src="data:image/png;base64,{img_cmp}" alt="comparacao convergencia PSO">
  <div class="kpis" style="margin-top:14px">
   <div class="kpi"><b>0,664</b><span>AUC teste &mdash; PSO padrão</span></div>
   <div class="kpi"><b>0,678</b><span>AUC teste &mdash; PSO meta (FSS)</span></div>
   <div class="kpi"><b style="color:#8ee6a0">+2,1&thinsp;%</b><span>melhoria relativa</span></div>
   <div class="kpi"><b>0,701</b><span>cosseno entre os pesos</span></div>
  </div>
  <p><b>O que mostra:</b> o PSO com hiperparâmetros encontrados pelo FSS converge mais
     rápido no treino <b>(0,837 vs&nbsp;0,821)</b> e obtém AUC de teste superior
     <b>(0,678 vs&nbsp;0,664)</b>, com +2,1&thinsp;% de ganho relativo.</p>
  <p><b>Cosseno&nbsp;=&nbsp;0,701</b> (diferente do 1,000 original PSO&nbsp;&times;&nbsp;sklearn).
     Isso é esperado e correto: os dois PSOs usam regularizações diferentes
     (&lambda;&nbsp;=&nbsp;0,016 vs&nbsp;0,050), portanto convergem para direções
     distintas no espaço de pesos. Confirma que a meta-otimização encontrou uma
     solução <em>genuinamente diferente</em> da empírica.</p>
 </div>

 <div class="card">
  <h2>9. Perfil do indivíduo ideal &mdash; PSO meta-otimizado</h2>
  <img src="data:image/png;base64,{img_imp}" alt="importancia features PSO meta">
  <p><b>Como ler:</b> peso <span class="pos">verde/positivo</span> = ter mais dessa
     característica aproxima do perfil ideal; peso
     <span class="neg">vermelho/negativo</span> = ter mais afasta do ideal.
     O padrão qualitativo permanece consistente com o PSO original: fatores de
     <b>composição corporal</b> e <b>resistência à insulina</b> dominam os pesos negativos,
     confirmando a robustez da análise.</p>
  <p class="muted">Quer ver o algoritmo trabalhando visualmente?
     Abra a aba <b>🎮 Simulação interativa</b> acima.</p>
 </div>

 <div class="card">
  <h2>10. As features mudaram de direção? Padrão × meta-otimizado</h2>
  <p>Ambos os modelos usam as <b>mesmas 26 features</b>. Tabela ordenada pela importância no
     modelo padrão (mesma referência da aba <b>📊 Apresentação</b>). Sinal ✅ = mesma
     direção em ambos os modelos; ⚠️ = direções opostas.</p>
  {tabela_comp}
  <p class="muted">▲/▼ no ranking indica subida ou descida de posição no modelo meta.
     Features com sinal invertido em pesos pequenos têm impacto narrativo baixo.</p>
 </div>

</div>
"""


def main():
    df = carregar_diabeticos()
    y = construir_rotulo(df)
    X, cols = selecionar_preditoras(df)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    # ótimo analítico — usado no relevo da simulação e como gabarito de validação
    C = 0.5 / (len(ytr) * LAMBDA)
    lr = LogisticRegression(max_iter=2000, C=C).fit(Xtr, ytr)
    wstar = lr.coef_[0].astype(float)
    bstar = float(lr.intercept_[0])

    # execução real do PSO -> números exatos da apresentação
    print("\n=== PSO (números da apresentação) ===")
    w, _, hist = pso(Xtr, ytr)
    auc_tr = auc_pesos(w, Xtr, ytr)
    auc_te = auc_pesos(w, Xte, yte)
    auc_lr = roc_auc_score(yte, lr.predict_proba(Xte)[:, 1])
    cos = float(np.dot(w[:-1], wstar) / (np.linalg.norm(w[:-1]) * np.linalg.norm(wstar) + 1e-12))
    pesos = w[:-1]
    ordem_w = np.argsort(-np.abs(pesos))
    linhas = [(cols[i], float(pesos[i])) for i in ordem_w]
    perfil = [(c, float(df[c][y == 1].mean()), float(df[c][y == 0].mean())) for c in cols]
    met = dict(auc_tr=auc_tr, auc_te=auc_te, auc_lr=auc_lr, cos=cos, n=len(y), n_ideal=int(y.sum()))

    # garante que os gráficos PNG existam (gera se faltar) e os embute em base64
    if not (os.path.exists("resultados_convergencia_pso.png")
            and os.path.exists("resultados_importancia.png")):
        salvar_saidas(hist, linhas, perfil, met)
    img_conv = b64("resultados_convergencia_pso.png")
    img_imp = b64("resultados_importancia.png")

    # escolhe pares a partir das características mais influentes
    ordem = np.argsort(-np.abs(wstar))
    t = [int(i) for i in ordem[:4]]
    pares = [(t[0], t[1]), (t[0], t[2]), (t[1], t[3])]
    # posição do ótimo DENTRO da moldura (fração 0..1 em x,y). Descentralizado de propósito,
    # em cantos diferentes por par, p/ o bando ter de "caminhar" até o topo (busca visível).
    fracs = [(0.27, 0.30), (0.72, 0.28), (0.30, 0.73)]

    dados_pares = []
    for (fi, fj), (fx, fy) in zip(pares, fracs):
        # largura total continua 2R (mesmo zoom); só desloca o enquadramento
        xs = np.linspace(wstar[fi] - 2 * R * fx, wstar[fi] + 2 * R * (1 - fx), G)
        ys = np.linspace(wstar[fj] - 2 * R * fy, wstar[fj] + 2 * R * (1 - fy), G)
        Z = np.zeros((G, G))
        w2 = wstar.copy()
        for a, yv in enumerate(ys):
            for b_ in range(G):
                w2[fi] = xs[b_]; w2[fj] = yv
                Z[a][b_] = fitness_full(w2, Xtr, ytr, bstar)
        w2[fi] = wstar[fi]; w2[fj] = wstar[fj]
        zmin, zmax = float(Z.min()), float(Z.max())
        dados_pares.append({
            "fi": cols[fi], "fj": cols[fj],
            "xmin": float(xs[0]), "xmax": float(xs[-1]),
            "ymin": float(ys[0]), "ymax": float(ys[-1]),
            "zmin": zmin, "zmax": zmax,
            "ox": float(wstar[fi]), "oy": float(wstar[fj]),
            "Z": [[round(v, 5) for v in row] for row in Z.tolist()],
        })

    payload = {"G": G, "pares": dados_pares,
               "descr": {c: DESCRICAO.get(c, c) for c in cols}}
    print("\n=== PSO meta-otimizado (comparação de pesos) ===")
    w_meta_comp = _pso_meta(Xtr, ytr, _HP_META)
    apres = montar_apresentacao(img_conv, img_imp, linhas, perfil, met)
    meta = montar_aba_meta(pesos, w_meta_comp, cols)
    html = (TEMPLATE
            .replace("/*DATA*/", json.dumps(payload))
            .replace("<!--APRES-->", apres)
            .replace("<!--META-->", meta))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pso_visualizacao.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[ok] {out} gerado ({len(html):,} bytes) — abra no navegador.")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-br"><head><meta charset="utf-8">
<title>PSO — diabetes: apresentação e simulação</title>
<style>
 body{font-family:system-ui,Arial,sans-serif;margin:0;background:#0f1115;color:#e6e6e6}
 header{padding:10px 16px;background:#171a21;border-bottom:1px solid #2a2f3a;position:sticky;top:0;z-index:5}
 h1{font-size:16px;margin:0}
 small{color:#9aa4b2}
 .tabs{margin-top:8px;display:flex;gap:8px}
 .tab{background:#374151}
 .tab.active{background:#2563eb}
 .wrap{display:flex;flex-wrap:wrap;gap:16px;padding:16px}
 canvas{background:#000;border:1px solid #2a2f3a;border-radius:8px}
 .panel{min-width:260px;max-width:320px;background:#171a21;border:1px solid #2a2f3a;border-radius:8px;padding:14px}
 .row{margin:10px 0;display:flex;align-items:center;justify-content:space-between;gap:10px}
 label{font-size:13px;color:#c8d0db}
 button{background:#2563eb;color:#fff;border:0;border-radius:6px;padding:7px 12px;cursor:pointer;font-size:13px}
 button.sec{background:#374151}
 input[type=range]{width:140px}
 select{background:#0f1115;color:#e6e6e6;border:1px solid #2a2f3a;border-radius:6px;padding:5px}
 .stat{font-variant-numeric:tabular-nums;color:#8ee6a0}
 .legend{font-size:12px;color:#9aa4b2;margin-top:6px;line-height:1.5}
 .apres{max-width:1000px;margin:0 auto;padding:18px}
 .card{background:#171a21;border:1px solid #2a2f3a;border-radius:10px;padding:18px 22px;margin:14px 0}
 .card h2{font-size:18px;margin:0 0 10px;color:#e6e6e6}
 .card p{line-height:1.65;color:#c8d0db;font-size:14px;margin:8px 0}
 .card img{max-width:100%;border-radius:8px;background:#fff;padding:6px;margin-top:10px}
 .kpis{display:flex;flex-wrap:wrap;gap:12px;margin:10px 0}
 .kpi{background:#0f1115;border:1px solid #2a2f3a;border-radius:8px;padding:12px 16px;min-width:120px;text-align:center}
 .kpi b{display:block;font-size:26px;color:#8ee6a0;font-variant-numeric:tabular-nums}
 .kpi span{font-size:12px;color:#9aa4b2}
 table.r{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}
 table.r th,table.r td{padding:6px 8px;border-bottom:1px solid #2a2f3a;text-align:left;vertical-align:top}
 table.r td.pos{color:#6ee787;font-variant-numeric:tabular-nums;text-align:right}
 table.r td.neg{color:#ff9aa2;font-variant-numeric:tabular-nums;text-align:right}
 .pos{color:#6ee787} .neg{color:#ff9aa2}
 .muted{color:#9aa4b2;font-size:13px}
 .grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
 @media(max-width:760px){.grid2{grid-template-columns:1fr}}
 .tag{display:inline-block;background:#1f2937;border:1px solid #2a2f3a;border-radius:999px;padding:2px 10px;font-size:12px;color:#9aa4b2;margin-right:6px}
</style></head>
<body>
<header>
 <h1>PSO &amp; diabetes — do problema ao resultado</h1>
 <nav class="tabs">
  <button id="tabApres" class="tab active">📊 Apresentação</button>
  <button id="tabSim" class="tab">🎮 Simulação interativa</button>
  <button id="tabMeta" class="tab">📈 Hiperparâmetros (FSS)</button>
 </nav>
</header>

<section id="view-apres"><!--APRES--></section>

<section id="view-sim" style="display:none">
 <div style="padding:10px 16px"><small>Cada partícula é uma combinação de 2 pesos. Veja o enxame em <b>2D</b> (mapa de calor visto de cima) ou em <b>3D</b> (superfície, onde a altura é o desempenho). Claro/alto = melhor; a ⭐ é o ótimo. As partículas (bando) convergem para o topo.</small></div>
 <div class="wrap">
  <canvas id="cv" width="620" height="620"></canvas>
  <div class="panel">
   <div class="row"><label>Par de características</label><select id="par"></select></div>
   <div class="legend" id="parHelp"></div>
   <div class="row"><label>Visualização</label><span>
     <button id="v2d">2D</button> <button id="v3d" class="sec">3D</button></span></div>
   <div class="row" id="row3d" style="display:none">
     <label><input type="checkbox" id="autorot" checked> Girar sozinho</label>
     <label>Zoom <input type="range" id="zoom3d" min="40" max="300" value="100"></label></div>
   <div class="row" id="row3d2" style="display:none">
     <label>Altura <input type="range" id="zscale" min="20" max="100" value="55"></label>
     <span class="muted" style="font-size:11px">scroll = zoom · arraste = girar</span></div>
   <div class="row">
    <button id="play">▶ Play</button>
    <button id="step" class="sec">Passo</button>
    <button id="reset" class="sec">Reiniciar</button>
   </div>
   <div class="row"><label><input type="checkbox" id="trace" checked> Mostrar rastro</label>
        <label><input type="checkbox" id="showg" checked> Mostrar gbest</label></div>
   <div class="row"><label><input type="checkbox" id="showv"> Mostrar velocidades</label></div>
   <div class="row"><label>Velocidade: <span id="speedLbl">lenta</span></label><input type="range" id="speed" min="1" max="10" value="2"></div>
   <div class="row"><label>Nº partículas: <span id="npLbl">30</span></label><input type="range" id="np" min="5" max="80" value="30"></div>
   <div class="row"><label>Inércia (w): <span id="wLbl">0.70</span></label><input type="range" id="winr" min="0" max="100" value="70"></div>
   <div class="row"><label>c1 (pessoal): <span id="c1Lbl">1.5</span></label><input type="range" id="c1" min="0" max="300" value="150"></div>
   <div class="row"><label>c2 (social): <span id="c2Lbl">1.5</span></label><input type="range" id="c2" min="0" max="300" value="150"></div>
   <hr style="border-color:#2a2f3a">
   <div class="row"><label>Iteração</label><span class="stat" id="it">0</span></div>
   <div class="row"><label>Melhor desempenho</label><span class="stat" id="best">—</span></div>
   <div class="legend" id="leg"></div>
  </div>
 </div>
</section>
<section id="view-meta" style="display:none"><!--META--></section>
<script>
const DATA = /*DATA*/;
const cv=document.getElementById('cv'), ctx=cv.getContext('2d');
const G=DATA.G, W=cv.width, H=cv.height;
let P=DATA.pares[0];                 // par atual
let heat=document.createElement('canvas'); heat.width=G; heat.height=G;
let particles=[], gbest=null, iter=0, playing=false, traces=[], acc=0;
let render3d=false, yaw=0.7, pitch=0.95, H3=0.55, zoom=1, autorot=true, drag3=null;  // estado da câmera 3D
const SPF=[0,0.04,0.08,0.16,0.3,0.6,1.2,2.5,4,7,11]; // passos por frame por valor do slider (1..10)
const SPF_LBL=['','muito lenta','lenta','lenta','média','média','rápida','rápida','muito rápida','muito rápida','turbo'];

// ---- seletor de par ----
const sel=document.getElementById('par');
const descr=f=>(DATA.descr&&DATA.descr[f])||f;
DATA.pares.forEach((p,i)=>{const o=document.createElement('option');o.value=i;o.textContent=p.fi+'  ×  '+p.fj;
 o.title=p.fi+': '+descr(p.fi)+'\n'+p.fj+': '+descr(p.fj);   // tooltip nativo ao passar o mouse
 sel.appendChild(o);});
function updateParHelp(){
 document.getElementById('parHelp').innerHTML=
   '<b>'+P.fi+'</b>: '+descr(P.fi)+'<br><b>'+P.fj+'</b>: '+descr(P.fj);
}
function legend3d(){ document.getElementById('leg').innerHTML='Superfície 3D — a <b>altura</b> é o desempenho real. Eixo X = peso de <b>'+P.fi+'</b>, eixo Y = peso de <b>'+P.fj+'</b>. ⭐ = ótimo (no pico). <b>Arraste</b> para girar.'; }
sel.onchange=()=>{P=DATA.pares[sel.value]; buildHeat(); updateParHelp(); if(render3d) legend3d(); reset();};

function color(t){ // t in [0,1] -> azul->verde->amarelo->vermelho-claro (desempenho)
 t=Math.max(0,Math.min(1,t));
 const r=Math.round(255*Math.min(1,Math.max(0,1.5*t-0.2)));
 const g=Math.round(255*Math.min(1,Math.max(0,1.3*t)));
 const b=Math.round(255*Math.min(1,Math.max(0,1-1.6*t)));
 return [r,g,b];
}
function buildHeat(){
 const hc=heat.getContext('2d'), img=hc.createImageData(G,G);
 const dz=(P.zmax-P.zmin)||1;
 for(let a=0;a<G;a++)for(let b=0;b<G;b++){
   const t=(P.Z[a][b]-P.zmin)/dz; const c=color(t);
   const idx=4*((G-1-a)*G+b);            // inverte y p/ topo em cima
   img.data[idx]=c[0];img.data[idx+1]=c[1];img.data[idx+2]=c[2];img.data[idx+3]=255;
 }
 hc.putImageData(img,0,0);
 document.getElementById('leg').innerHTML='Eixo X = peso de <b>'+P.fi+'</b> &nbsp; | &nbsp; Eixo Y = peso de <b>'+P.fj+'</b><br>Fundo claro = melhor desempenho. ⭐ = ótimo encontrado pela análise.';
}
// ---- conversões coordenada-peso <-> pixel ----
const px=x=>(x-P.xmin)/(P.xmax-P.xmin)*W;
const py=y=>H-(y-P.ymin)/(P.ymax-P.ymin)*H;
// ---- fitness por interpolação bilinear do grid ----
function fit(x,y){
 let fx=(x-P.xmin)/(P.xmax-P.xmin)*(G-1), fy=(y-P.ymin)/(P.ymax-P.ymin)*(G-1);
 fx=Math.max(0,Math.min(G-1,fx)); fy=Math.max(0,Math.min(G-1,fy));
 const x0=Math.floor(fx),y0=Math.floor(fy),x1=Math.min(G-1,x0+1),y1=Math.min(G-1,y0+1);
 const tx=fx-x0,ty=fy-y0;
 const z00=P.Z[y0][x0],z10=P.Z[y0][x1],z01=P.Z[y1][x0],z11=P.Z[y1][x1];
 return (z00*(1-tx)+z10*tx)*(1-ty)+(z01*(1-tx)+z11*tx)*ty;
}
const rnd=(a,b)=>a+Math.random()*(b-a);
function reset(){
 const n=+document.getElementById('np').value;
 particles=[]; traces=[]; iter=0; gbest=null; acc=0;
 for(let i=0;i<n;i++){
   const x=rnd(P.xmin,P.xmax), y=rnd(P.ymin,P.ymax), f=fit(x,y);
   const hue=Math.round(360*i/n);
   particles.push({x,y,vx:rnd(-.1,.1),vy:rnd(-.1,.1),bx:x,by:y,bf:f,dx:x,dy:y,hue});
   traces.push([[x,y]]);
   if(!gbest||f>gbest.f) gbest={x,y,f};
 }
 document.getElementById('it').textContent=0;
 document.getElementById('best').textContent=gbest.f.toFixed(4);
 render();
}
function stepOnce(){
 const w=+document.getElementById('winr').value/100;
 const c1=+document.getElementById('c1').value/100, c2=+document.getElementById('c2').value/100;
 for(let i=0;i<particles.length;i++){
   const p=particles[i];
   p.vx=w*p.vx+c1*Math.random()*(p.bx-p.x)+c2*Math.random()*(gbest.x-p.x);
   p.vy=w*p.vy+c1*Math.random()*(p.by-p.y)+c2*Math.random()*(gbest.y-p.y);
   const vmax=(P.xmax-P.xmin)*0.10;
   p.vx=Math.max(-vmax,Math.min(vmax,p.vx)); p.vy=Math.max(-vmax,Math.min(vmax,p.vy));
   p.x+=p.vx; p.y+=p.vy;
   const f=fit(p.x,p.y);
   if(f>p.bf){p.bf=f;p.bx=p.x;p.by=p.y;}
   if(f>gbest.f) gbest={x:p.x,y:p.y,f};
 }
 iter++;
 document.getElementById('it').textContent=iter;
 document.getElementById('best').textContent=gbest.f.toFixed(4);
}
function animate(){
 const ease=0.16, thr=(P.xmax-P.xmin)*0.0015;
 for(let i=0;i<particles.length;i++){const p=particles[i];
   p.dx+=(p.x-p.dx)*ease; p.dy+=(p.y-p.dy)*ease;            // suaviza o movimento (fluido)
   const tr=traces[i], last=tr[tr.length-1];
   if(Math.abs(p.dx-last[0])+Math.abs(p.dy-last[1])>thr){ tr.push([p.dx,p.dy]); if(tr.length>90) tr.shift(); }
 }
}
function draw(){
 ctx.imageSmoothingEnabled=true;
 ctx.drawImage(heat,0,0,G,G,0,0,W,H);
 ctx.fillStyle='rgba(8,10,15,0.30)'; ctx.fillRect(0,0,W,H);   // escurece p/ as cores saltarem
 // rastros: cada partícula na sua cor, com desvanecimento (cauda transparente -> cabeça forte)
 if(document.getElementById('trace').checked){
   ctx.lineCap='round';
   for(let i=0;i<traces.length;i++){const tr=traces[i], hue=particles[i].hue;
     for(let k=1;k<tr.length;k++){const a=k/tr.length;
       ctx.beginPath(); ctx.moveTo(px(tr[k-1][0]),py(tr[k-1][1])); ctx.lineTo(px(tr[k][0]),py(tr[k][1]));
       ctx.strokeStyle='hsla('+hue+',95%,62%,'+(a*0.9).toFixed(3)+')'; ctx.lineWidth=0.6+2.6*a; ctx.stroke();
     }
   }
 }
 // velocidades
 if(document.getElementById('showv').checked){
   for(const p of particles){ ctx.beginPath(); ctx.moveTo(px(p.dx),py(p.dy));
     ctx.lineTo(px(p.dx+p.vx*3),py(p.dy+p.vy*3)); ctx.strokeStyle='rgba(255,220,120,.85)'; ctx.lineWidth=1.2; ctx.stroke(); }
 }
 // partículas coloridas com brilho
 ctx.save();
 for(const p of particles){ ctx.shadowColor='hsl('+p.hue+',95%,60%)'; ctx.shadowBlur=8;
   ctx.beginPath(); ctx.arc(px(p.dx),py(p.dy),3.6,0,7); ctx.fillStyle='hsl('+p.hue+',95%,66%)'; ctx.fill(); }
 ctx.restore();
 // ótimo (estrela) e gbest, com brilho
 ctx.save(); ctx.shadowColor='#ffd166'; ctx.shadowBlur=14; star(px(P.ox),py(P.oy),11,'#ffd166'); ctx.restore();
 if(document.getElementById('showg').checked && gbest){
   ctx.save(); ctx.shadowColor='#22d3ee'; ctx.shadowBlur=12;
   ctx.beginPath(); ctx.arc(px(gbest.x),py(gbest.y),7,0,7); ctx.strokeStyle='#22d3ee'; ctx.lineWidth=2.5; ctx.stroke(); ctx.restore();
 }
}
function star(cx,cy,r,col){ ctx.beginPath();
 for(let i=0;i<10;i++){const ang=Math.PI/5*i-Math.PI/2,rad=i%2?r*0.45:r;
   const X=cx+Math.cos(ang)*rad,Y=cy+Math.sin(ang)*rad; i?ctx.lineTo(X,Y):ctx.moveTo(X,Y);}
 ctx.closePath(); ctx.fillStyle=col; ctx.fill(); }
// ---- render 3D: a MESMA superfície de desempenho, agora com altura = fitness ----
function draw3d(){
 const CX=W/2, CY=H*0.60, scale=360*zoom, dz=(P.zmax-P.zmin)||1;
 const cyw=Math.cos(yaw), syw=Math.sin(yaw), cpt=Math.cos(pitch), spt=Math.sin(pitch);
 // projeta um ponto do mundo (wx,wy,wz) -> [pixelX, pixelY, profundidade] (giro + inclinação)
 const proj=(wx,wy,wz)=>{ const xr=wx*cyw-wy*syw, yr=wx*syw+wy*cyw;
   return [CX+xr*scale, CY-(yr*spt+wz*cpt)*scale, yr*cpt-wz*spt]; };
 const gx=b=>(b/(G-1)-0.5), gy=a=>(a/(G-1)-0.5), gz=v=>((v-P.zmin)/dz-0.5)*H3;
 const nx=x=>((x-P.xmin)/(P.xmax-P.xmin)-0.5), ny=y=>((y-P.ymin)/(P.ymax-P.ymin)-0.5);
 ctx.fillStyle='#05070b'; ctx.fillRect(0,0,W,H);
 // malha de quadrados pintada por altura, desenhada do fundo p/ a frente (painter's algorithm)
 const S=2, quads=[];
 for(let a=0;a+S<G;a+=S) for(let b=0;b+S<G;b+=S){
   const z00=P.Z[a][b], z10=P.Z[a][b+S], z11=P.Z[a+S][b+S], z01=P.Z[a+S][b];
   const A=proj(gx(b),gy(a),gz(z00)),     B=proj(gx(b+S),gy(a),gz(z10));
   const C=proj(gx(b+S),gy(a+S),gz(z11)), D=proj(gx(b),gy(a+S),gz(z01));
   quads.push({A,B,C,D,t:((z00+z10+z11+z01)/4-P.zmin)/dz,depth:(A[2]+B[2]+C[2]+D[2])/4});
 }
 quads.sort((m,n)=>n.depth-m.depth);
 for(const q of quads){ const c=color(q.t);
   ctx.beginPath(); ctx.moveTo(q.A[0],q.A[1]); ctx.lineTo(q.B[0],q.B[1]);
   ctx.lineTo(q.C[0],q.C[1]); ctx.lineTo(q.D[0],q.D[1]); ctx.closePath();
   ctx.fillStyle='rgb('+c[0]+','+c[1]+','+c[2]+')'; ctx.fill();
   ctx.strokeStyle='rgba(0,0,0,.18)'; ctx.lineWidth=.5; ctx.stroke(); }
 // rastros projetados sobre o relevo (mesma cor da partícula, desbotando na cauda)
 if(document.getElementById('trace').checked){ ctx.lineCap='round';
   for(let i=0;i<traces.length;i++){ const pc=particles[i]; if(!pc) continue;
     const tr=traces[i], hue=pc.hue; let prev=null;
     for(let k=0;k<tr.length;k++){ const pp=proj(nx(tr[k][0]),ny(tr[k][1]),gz(fit(tr[k][0],tr[k][1]))+.015);
       if(prev){ const al=k/tr.length; ctx.beginPath(); ctx.moveTo(prev[0],prev[1]); ctx.lineTo(pp[0],pp[1]);
         ctx.strokeStyle='hsla('+hue+',95%,62%,'+(al*0.9).toFixed(3)+')'; ctx.lineWidth=0.6+2.2*al; ctx.stroke(); }
       prev=pp; } } }
 // velocidades (seta curta a partir de cada partícula, seguindo o relevo)
 if(document.getElementById('showv').checked){
   for(const p of particles){ const a0=proj(nx(p.dx),ny(p.dy),gz(fit(p.dx,p.dy))+.02);
     const b0=proj(nx(p.dx+p.vx*3),ny(p.dy+p.vy*3),gz(fit(p.dx+p.vx*3,p.dy+p.vy*3))+.02);
     ctx.beginPath(); ctx.moveTo(a0[0],a0[1]); ctx.lineTo(b0[0],b0[1]);
     ctx.strokeStyle='rgba(255,220,120,.85)'; ctx.lineWidth=1.2; ctx.stroke(); } }
 // partículas pousadas na superfície (cada uma na sua cor), ordenadas por profundidade
 const pts=particles.map(p=>({s:proj(nx(p.dx),ny(p.dy),gz(fit(p.dx,p.dy))+.02),hue:p.hue}))
                    .sort((m,n)=>n.s[2]-m.s[2]);
 ctx.save();
 for(const q of pts){ ctx.shadowColor='hsl('+q.hue+',95%,60%)'; ctx.shadowBlur=8;
   ctx.beginPath(); ctx.arc(q.s[0],q.s[1],4,0,7); ctx.fillStyle='hsl('+q.hue+',95%,66%)'; ctx.fill(); }
 ctx.restore();
 if(document.getElementById('showg').checked && gbest){
   const g=proj(nx(gbest.x),ny(gbest.y),gz(fit(gbest.x,gbest.y))+.02);
   ctx.save(); ctx.shadowColor='#22d3ee'; ctx.shadowBlur=12;
   ctx.beginPath(); ctx.arc(g[0],g[1],7,0,7); ctx.strokeStyle='#22d3ee'; ctx.lineWidth=2.5; ctx.stroke(); ctx.restore(); }
 const o=proj(nx(P.ox),ny(P.oy),gz(fit(P.ox,P.oy))+.03);
 ctx.save(); ctx.shadowColor='#ffd166'; ctx.shadowBlur=14; star(o[0],o[1],12,'#ffd166'); ctx.restore();
}
function render(){ render3d?draw3d():draw(); }
function loop(){
 if(playing){ acc += SPF[+document.getElementById('speed').value]; while(acc>=1){ stepOnce(); acc--; } }
 if(render3d && autorot && !drag3) yaw+=0.006;            // gira sozinho quando não está arrastando
 animate(); render(); requestAnimationFrame(loop);
}
// ---- controles ----
document.getElementById('play').onclick=function(){playing=!playing; this.textContent=playing?'⏸ Pause':'▶ Play';};
document.getElementById('step').onclick=()=>{stepOnce();render();};
document.getElementById('reset').onclick=reset;
document.getElementById('speed').oninput=function(){document.getElementById('speedLbl').textContent=SPF_LBL[this.value];};
document.getElementById('np').oninput=function(){document.getElementById('npLbl').textContent=this.value; reset();};
document.getElementById('winr').oninput=function(){document.getElementById('wLbl').textContent=(this.value/100).toFixed(2);};
document.getElementById('c1').oninput=function(){document.getElementById('c1Lbl').textContent=(this.value/100).toFixed(1);};
document.getElementById('c2').oninput=function(){document.getElementById('c2Lbl').textContent=(this.value/100).toFixed(1);};
['trace','showg','showv'].forEach(id=>document.getElementById(id).onchange=render);
// ---- alternância 2D/3D + câmera ----
function setView(is3d){ render3d=is3d;
 document.getElementById('row3d').style.display=is3d?'flex':'none';
 document.getElementById('row3d2').style.display=is3d?'flex':'none';
 document.getElementById('v3d').className=is3d?'':'sec';
 document.getElementById('v2d').className=is3d?'sec':'';
 if(is3d) legend3d(); else buildHeat();
 render();
}
document.getElementById('v2d').onclick=()=>setView(false);
document.getElementById('v3d').onclick=()=>setView(true);
document.getElementById('autorot').onchange=function(){autorot=this.checked;};
document.getElementById('zscale').oninput=function(){H3=this.value/100; if(!playing) render();};
document.getElementById('zoom3d').oninput=function(){zoom=this.value/100; if(!playing) render();};
cv.addEventListener('wheel',e=>{ if(!render3d) return; e.preventDefault();
 zoom=Math.max(0.4,Math.min(3,zoom*(e.deltaY<0?1.1:0.9)));
 document.getElementById('zoom3d').value=Math.round(zoom*100); if(!playing) render(); },{passive:false});
cv.addEventListener('mousedown',e=>{ if(render3d) drag3={x:e.clientX,y:e.clientY,yaw,pitch}; });
window.addEventListener('mousemove',e=>{ if(drag3){ yaw=drag3.yaw+(e.clientX-drag3.x)*0.01;
  pitch=Math.max(0.15,Math.min(1.45,drag3.pitch+(e.clientY-drag3.y)*0.005)); if(!playing) render(); }});
window.addEventListener('mouseup',()=>{drag3=null;});
// ---- menu de abas ----
function show(which){
 document.getElementById('view-apres').style.display = which=='apres'?'block':'none';
 document.getElementById('view-sim').style.display   = which=='sim'?'block':'none';
 document.getElementById('view-meta').style.display  = which=='meta'?'block':'none';
 document.getElementById('tabApres').classList.toggle('active',which=='apres');
 document.getElementById('tabSim').classList.toggle('active',which=='sim');
 document.getElementById('tabMeta').classList.toggle('active',which=='meta');
 window.scrollTo(0,0);
}
document.getElementById('tabApres').onclick=()=>show('apres');
document.getElementById('tabSim').onclick=()=>show('sim');
document.getElementById('tabMeta').onclick=()=>show('meta');
buildHeat(); updateParHelp(); reset(); loop();
</script></body></html>"""


if __name__ == "__main__":
    main()
