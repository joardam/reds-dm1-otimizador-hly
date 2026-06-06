#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera um visualizador interativo (HTML autocontido) do PSO no espaço dos PESOS.

Como são 27 pesos, mostramos uma FATIA 2D: variam-se 2 pesos (de 2 características) enquanto os
demais ficam fixos no ótimo. O "relevo" (fitness) é calculado a partir dos DADOS REAIS (mesma
função do pso_diabetes.py: -(log-loss + L2)). As partículas do PSO nadam até o topo do relevo
(= melhor combinação de pesos = melhor identificação do 'indivíduo ideal').

Saída: pso_visualizacao.html  (abra no navegador; zero instalação).
"""
import json
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from pso_diabetes import (carregar_diabeticos, construir_rotulo, selecionar_preditoras,
                          sigmoid, LAMBDA)

G = 60                       # resolução do grid do relevo
R = 1.2                      # meia-largura em torno do ótimo (em unidades de peso)


def fitness_full(w, X, y, b):
    p = np.clip(sigmoid(X @ w + b), 1e-9, 1 - 1e-9)
    logloss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return -(logloss + LAMBDA * np.sum(w ** 2))


def main():
    df = carregar_diabeticos()
    y = construir_rotulo(df)
    X, cols = selecionar_preditoras(df)
    Xtr, _, ytr, _ = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    C = 0.5 / (len(ytr) * LAMBDA)
    lr = LogisticRegression(max_iter=2000, C=C).fit(Xtr, ytr)
    wstar = lr.coef_[0].astype(float)
    bstar = float(lr.intercept_[0])

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
        w = wstar.copy()
        for a, yv in enumerate(ys):
            for b_ in range(G):
                w[fi] = xs[b_]; w[fj] = yv
                Z[a][b_] = fitness_full(w, Xtr, ytr, bstar)
        w[fi] = wstar[fi]; w[fj] = wstar[fj]
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
    html = TEMPLATE.replace("/*DATA*/", json.dumps(payload))
    with open("pso_visualizacao.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("[ok] pso_visualizacao.html gerado (", len(html), "bytes ) — abra no navegador.")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-br"><head><meta charset="utf-8">
<title>PSO — buscando os melhores pesos</title>
<style>
 body{font-family:system-ui,Arial,sans-serif;margin:0;background:#0f1115;color:#e6e6e6}
 header{padding:10px 16px;background:#171a21;border-bottom:1px solid #2a2f3a}
 h1{font-size:16px;margin:0}
 small{color:#9aa4b2}
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
</style></head>
<body>
<header>
 <h1>PSO — partículas buscando os melhores pesos (relevo de desempenho real)</h1>
 <small>Cada partícula é uma combinação de 2 pesos. O fundo é o desempenho real (claro = melhor). A ⭐ é o ótimo (fora do centro, de propósito). As partículas (bando) convergem para o topo.</small>
</header>
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
buildHeat(); reset(); loop();
</script></body></html>"""


if __name__ == "__main__":
    main()
