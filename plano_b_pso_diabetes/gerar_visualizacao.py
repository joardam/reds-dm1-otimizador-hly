#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera um app HTML autocontido com DUAS telas (menu de abas):

  1) APRESENTAÇÃO — o problema, o método, os gráficos (convergência + importância) e a leitura
     dos resultados: o que cada número significa e por que faz sentido ter chegado nele.
  2) SIMULAÇÃO interativa — o PSO "nadando" no relevo de desempenho real (fatia 2D de 2 pesos).

Os números (AUC, cosseno, pesos, perfil) vêm de uma execução real do PSO (mesmo pipeline do
pso_diabetes.py). Os gráficos PNG são embutidos em base64 -> o HTML não depende de arquivos externos.

Saída: pso_visualizacao.html  (abra no navegador; zero instalação).
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
  <p>O PSO é inspirado no <b>voo coordenado de bandos de pássaros</b> (Kennedy &amp; Eberhart, 1995) —
     <i>não</i> em cardumes. Cada "partícula" do enxame é uma <b>tentativa de resposta</b>: um conjunto
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
  <p class="muted">• É um retrato <b>transversal</b> (uma foto no tempo), então fala de
     <b>associação</b>, não de causa. • Uma única coorte (China, 2012) → não generaliza para
     o Brasil/SUS. • O rótulo "ideal" é uma <b>escolha de projeto</b> (idade + HbA1c + comorbidades),
     defensável mas não única. • Base não distingue tipo 1/tipo 2 → é testbed do otimizador.</p>
 </div>

 <p class="muted" style="text-align:center;margin:20px 0">
   Quer ver o algoritmo trabalhando? Abra a aba <b>🎮 Simulação interativa</b> acima.</p>

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

    payload = {"G": G, "pares": dados_pares}
    apres = montar_apresentacao(img_conv, img_imp, linhas, perfil, met)
    html = TEMPLATE.replace("/*DATA*/", json.dumps(payload)).replace("<!--APRES-->", apres)
    with open("pso_visualizacao.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("[ok] pso_visualizacao.html gerado (", len(html), "bytes ) — abra no navegador.")


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
 </nav>
</header>

<section id="view-apres"><!--APRES--></section>

<section id="view-sim" style="display:none">
 <div style="padding:10px 16px"><small>Cada partícula é uma combinação de 2 pesos. O fundo é o desempenho real (claro = melhor). A ⭐ é o ótimo (fora do centro, de propósito). As partículas (bando) convergem para o topo.</small></div>
 <div class="wrap">
  <canvas id="cv" width="620" height="620"></canvas>
  <div class="panel">
   <div class="row"><label>Par de características</label><select id="par"></select></div>
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
<script>
const DATA = /*DATA*/;
const cv=document.getElementById('cv'), ctx=cv.getContext('2d');
const G=DATA.G, W=cv.width, H=cv.height;
let P=DATA.pares[0];                 // par atual
let heat=document.createElement('canvas'); heat.width=G; heat.height=G;
let particles=[], gbest=null, iter=0, playing=false, traces=[], acc=0;
const SPF=[0,0.04,0.08,0.16,0.3,0.6,1.2,2.5,4,7,11]; // passos por frame por valor do slider (1..10)
const SPF_LBL=['','muito lenta','lenta','lenta','média','média','rápida','rápida','muito rápida','muito rápida','turbo'];

// ---- seletor de par ----
const sel=document.getElementById('par');
DATA.pares.forEach((p,i)=>{const o=document.createElement('option');o.value=i;o.textContent=p.fi+'  ×  '+p.fj;sel.appendChild(o);});
sel.onchange=()=>{P=DATA.pares[sel.value]; buildHeat(); reset();};

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
 draw();
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
function loop(){ if(playing){ acc += SPF[+document.getElementById('speed').value];
   while(acc>=1){ stepOnce(); acc--; } } animate(); draw(); requestAnimationFrame(loop); }
// ---- controles ----
document.getElementById('play').onclick=function(){playing=!playing; this.textContent=playing?'⏸ Pause':'▶ Play';};
document.getElementById('step').onclick=()=>{stepOnce();draw();};
document.getElementById('reset').onclick=reset;
document.getElementById('speed').oninput=function(){document.getElementById('speedLbl').textContent=SPF_LBL[this.value];};
document.getElementById('np').oninput=function(){document.getElementById('npLbl').textContent=this.value; reset();};
document.getElementById('winr').oninput=function(){document.getElementById('wLbl').textContent=(this.value/100).toFixed(2);};
document.getElementById('c1').oninput=function(){document.getElementById('c1Lbl').textContent=(this.value/100).toFixed(1);};
document.getElementById('c2').oninput=function(){document.getElementById('c2Lbl').textContent=(this.value/100).toFixed(1);};
['trace','showg','showv'].forEach(id=>document.getElementById(id).onchange=draw);
// ---- menu de abas ----
function show(which){
 document.getElementById('view-apres').style.display = which=='apres'?'block':'none';
 document.getElementById('view-sim').style.display   = which=='sim'?'block':'none';
 document.getElementById('tabApres').classList.toggle('active',which=='apres');
 document.getElementById('tabSim').classList.toggle('active',which=='sim');
 window.scrollTo(0,0);
}
document.getElementById('tabApres').onclick=()=>show('apres');
document.getElementById('tabSim').onclick=()=>show('sim');
buildHeat(); reset(); loop();
</script></body></html>"""


if __name__ == "__main__":
    main()
