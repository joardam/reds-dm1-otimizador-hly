#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera a MESMA visualização (apresentação + simulação do PSO), porém num app HTML
**otimizado para celular**:

  * <meta viewport> + layout mobile-first (uma coluna, controles que empilham);
  * canvas responsivo (preenche a largura da tela, nítido em telas retina);
  * o gráfico **3D é controlado pelo toque**: 1 dedo gira (yaw/pitch) e
    **pinça (2 dedos) dá zoom** — zoom pensado para celular, sem depender de scroll;
  * alvos de toque maiores (botões/sliders) e tipografia legível no telefone;
  * malha 3D adaptativa (mais leve quando o ponteiro é "grosso"/touch) para rodar liso.

Reaproveita TODO o pipeline real (PSO + gabarito sklearn + relevo de desempenho) de
`gerar_visualizacao.py` via `construir_dados()` — nada de rodar o PSO duas vezes nem
duplicar a apresentação.

Saída: pso_visualizacao_mobile.html  (abra no celular; autocontido, zero instalação).
"""
from gerar_visualizacao import construir_dados, render_html


TEMPLATE_MOBILE = r"""<!DOCTYPE html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>PSO — diabetes (mobile)</title>
<style>
 :root{ --bg:#0f1115; --card:#171a21; --line:#2a2f3a; --txt:#e6e6e6; --mut:#9aa4b2; --blue:#2563eb; }
 *{box-sizing:border-box}
 html{-webkit-text-size-adjust:100%}
 body{font-family:system-ui,-apple-system,Arial,sans-serif;margin:0;background:var(--bg);color:var(--txt);
      -webkit-tap-highlight-color:transparent}
 header{padding:10px 12px calc(10px + env(safe-area-inset-bottom,0));background:var(--card);
        border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
 h1{font-size:15px;margin:0;line-height:1.3}
 small{color:var(--mut);font-size:12px}
 .tabs{margin-top:8px;display:flex;gap:8px}
 .tab{flex:1;background:#374151;color:#fff;border:0;border-radius:8px;padding:11px 8px;font-size:14px;
      font-weight:600;cursor:pointer;min-height:44px}
 .tab.active{background:var(--blue)}

 /* ---------- simulação: layout mobile-first (uma coluna) ---------- */
 .simhint{padding:8px 12px;color:var(--mut);font-size:12.5px;line-height:1.5}
 .simwrap{display:flex;flex-direction:column;gap:14px;padding:0 12px 28px;align-items:stretch}
 .stage{width:100%;display:flex;justify-content:center}
 canvas{width:100%;max-width:min(620px,94vw);aspect-ratio:1/1;background:#000;
        border:1px solid var(--line);border-radius:12px;touch-action:none;display:block}
 .panel{width:100%;max-width:620px;margin:0 auto;background:var(--card);border:1px solid var(--line);
        border-radius:12px;padding:14px}
 .row{margin:12px 0;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
 .row.col{flex-direction:column;align-items:stretch}
 label{font-size:14px;color:#c8d0db}
 button{background:var(--blue);color:#fff;border:0;border-radius:8px;padding:11px 14px;cursor:pointer;
        font-size:14px;min-height:44px;flex:0 0 auto}
 button.sec{background:#374151}
 .btns{display:flex;gap:8px;flex-wrap:wrap}
 .btns button{flex:1 1 auto}
 .seg button{flex:1}
 input[type=range]{width:100%;height:30px;accent-color:var(--blue)}
 input[type=checkbox]{width:20px;height:20px;vertical-align:middle;accent-color:var(--blue)}
 select{background:var(--bg);color:var(--txt);border:1px solid var(--line);border-radius:8px;
        padding:10px;font-size:15px;min-height:44px;width:100%}
 .field{display:flex;flex-direction:column;gap:6px;width:100%}
 .field .lbl{display:flex;justify-content:space-between;align-items:baseline}
 .stat{font-variant-numeric:tabular-nums;color:#8ee6a0;font-size:15px}
 .legend{font-size:12.5px;color:var(--mut);margin-top:4px;line-height:1.55}
 .touchpill{display:inline-block;background:#13233b;border:1px solid #1e3a5f;color:#9cc4ff;
            border-radius:999px;padding:4px 10px;font-size:12px;margin-top:6px}

 /* ---------- apresentação ---------- */
 .apres{max-width:1000px;margin:0 auto;padding:14px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:12px 0;
       overflow-x:auto}
 .card h2{font-size:17px;margin:0 0 10px}
 .card p{line-height:1.65;color:#c8d0db;font-size:14.5px;margin:8px 0}
 .card img{max-width:100%;height:auto;border-radius:8px;background:#fff;padding:6px;margin-top:10px}
 .kpis{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0}
 .kpi{flex:1 1 130px;background:var(--bg);border:1px solid var(--line);border-radius:10px;
      padding:12px;text-align:center}
 .kpi b{display:block;font-size:24px;color:#8ee6a0;font-variant-numeric:tabular-nums}
 .kpi span{font-size:12px;color:var(--mut)}
 table.r{width:100%;border-collapse:collapse;margin-top:8px;font-size:13.5px}
 table.r th,table.r td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
 table.r td.pos{color:#6ee787;font-variant-numeric:tabular-nums;text-align:right}
 table.r td.neg{color:#ff9aa2;font-variant-numeric:tabular-nums;text-align:right}
 .pos{color:#6ee787} .neg{color:#ff9aa2}
 .muted{color:var(--mut);font-size:13px}
 .grid2{display:grid;grid-template-columns:1fr;gap:14px;align-items:start}
 .tag{display:inline-block;background:#1f2937;border:1px solid var(--line);border-radius:999px;
      padding:2px 10px;font-size:12px;color:var(--mut);margin-right:6px}

 /* ---------- telas largas (tablet/desktop): painel ao lado ---------- */
 @media(min-width:900px){
   h1{font-size:17px}
   .simwrap{flex-direction:row;justify-content:center;align-items:flex-start;gap:18px}
   .stage{flex:0 0 auto;width:auto}
   .panel{width:340px;margin:0}
   .grid2{grid-template-columns:1fr 1fr}
 }
</style></head>
<body>
<header>
 <h1>PSO &amp; diabetes <small>— versão para celular</small></h1>
 <nav class="tabs">
  <button id="tabApres" class="tab active">📊 Apresentação</button>
  <button id="tabSim" class="tab">🎮 Simulação</button>
 </nav>
</header>

<section id="view-apres"><!--APRES--></section>

<section id="view-sim" style="display:none">
 <div class="simhint">Cada partícula é uma combinação de 2 pesos. No <b>3D</b> a altura é o desempenho real
  (claro/alto = melhor; ⭐ = ótimo). <span class="touchpill">👆 1 dedo gira · 🤏 pinça dá zoom</span></div>
 <div class="simwrap">
  <div class="stage"><canvas id="cv"></canvas></div>
  <div class="panel">
   <div class="field">
    <label>Par de características</label>
    <select id="par"></select>
   </div>
   <div class="legend" id="parHelp"></div>

   <div class="row seg"><span class="btns" style="width:100%">
     <button id="v2d" class="sec">2D (mapa)</button>
     <button id="v3d">3D (relevo)</button></span></div>

   <div id="row3d">
     <div class="row"><label><input type="checkbox" id="autorot" checked> Girar sozinho</label></div>
     <div class="field"><div class="lbl"><label>Zoom 3D</label></div>
        <input type="range" id="zoom3d" min="40" max="300" value="100"></div>
     <div class="field"><div class="lbl"><label>Altura do relevo</label></div>
        <input type="range" id="zscale" min="20" max="100" value="55"></div>
   </div>

   <div class="row btns">
    <button id="play">▶ Play</button>
    <button id="step" class="sec">Passo</button>
    <button id="reset" class="sec">Reiniciar</button>
   </div>

   <div class="row"><label><input type="checkbox" id="trace" checked> Rastro</label>
        <label><input type="checkbox" id="showg" checked> gbest</label>
        <label><input type="checkbox" id="showv"> Velocidades</label></div>

   <div class="field"><div class="lbl"><label>Velocidade</label><span class="muted" id="speedLbl">lenta</span></div>
        <input type="range" id="speed" min="1" max="10" value="2"></div>
   <div class="field"><div class="lbl"><label>Nº de partículas</label><span class="muted" id="npLbl">30</span></div>
        <input type="range" id="np" min="5" max="80" value="30"></div>
   <div class="field"><div class="lbl"><label>Inércia (w)</label><span class="muted" id="wLbl">0.70</span></div>
        <input type="range" id="winr" min="0" max="100" value="70"></div>
   <div class="field"><div class="lbl"><label>c1 (pessoal)</label><span class="muted" id="c1Lbl">1.5</span></div>
        <input type="range" id="c1" min="0" max="300" value="150"></div>
   <div class="field"><div class="lbl"><label>c2 (social)</label><span class="muted" id="c2Lbl">1.5</span></div>
        <input type="range" id="c2" min="0" max="300" value="150"></div>

   <hr style="border-color:var(--line)">
   <div class="row"><label>Iteração</label><span class="stat" id="it">0</span></div>
   <div class="row"><label>Melhor desempenho</label><span class="stat" id="best">—</span></div>
   <div class="legend" id="leg"></div>
  </div>
 </div>
</section>
<script>
const DATA = /*DATA*/;
const cv=document.getElementById('cv'), ctx=cv.getContext('2d');
const G=DATA.G;
let W=620, H=620, SC=1;                // dimensões do canvas (device px) e fator de escala visual
const COARSE = window.matchMedia('(pointer:coarse)').matches;   // celular/tablet (toque)
const STEP3D = COARSE ? 3 : 2;        // malha 3D mais leve no celular -> roda liso
let P=DATA.pares[0];                   // par atual
let heat=document.createElement('canvas'); heat.width=G; heat.height=G;
let particles=[], gbest=null, iter=0, playing=false, traces=[], acc=0;
let render3d=false, yaw=0.7, pitch=0.95, H3=0.55, zoom=1, autorot=true, drag3=null;  // câmera 3D
const SPF=[0,0.04,0.08,0.16,0.3,0.6,1.2,2.5,4,7,11];
const SPF_LBL=['','muito lenta','lenta','lenta','média','média','rápida','rápida','muito rápida','muito rápida','turbo'];

// ---- canvas responsivo + nítido em telas retina ----
function fitCanvas(){
 const dpr=Math.min(window.devicePixelRatio||1,2);
 const rect=cv.getBoundingClientRect();
 if(!rect.width){ return; }            // ainda escondido (aba apresentação)
 cv.width=Math.round(rect.width*dpr); cv.height=Math.round(rect.height*dpr);
 W=cv.width; H=cv.height; SC=Math.min(W,H)/620;
 render();
}
window.addEventListener('resize',fitCanvas);
window.addEventListener('orientationchange',()=>setTimeout(fitCanvas,250));

// ---- seletor de par ----
const sel=document.getElementById('par');
const descr=f=>(DATA.descr&&DATA.descr[f])||f;
DATA.pares.forEach((p,i)=>{const o=document.createElement('option');o.value=i;o.textContent=p.fi+'  ×  '+p.fj;
 sel.appendChild(o);});
function updateParHelp(){
 document.getElementById('parHelp').innerHTML=
   '<b>'+P.fi+'</b>: '+descr(P.fi)+'<br><b>'+P.fj+'</b>: '+descr(P.fj);
}
function legend3d(){ document.getElementById('leg').innerHTML='Superfície 3D — a <b>altura</b> é o desempenho real. Eixo X = peso de <b>'+P.fi+'</b>, eixo Y = peso de <b>'+P.fj+'</b>. ⭐ = ótimo (no pico). <b>1 dedo gira · pinça dá zoom.</b>'; }
sel.onchange=()=>{P=DATA.pares[sel.value]; buildHeat(); updateParHelp(); if(render3d) legend3d(); reset();};

function color(t){
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
   const idx=4*((G-1-a)*G+b);
   img.data[idx]=c[0];img.data[idx+1]=c[1];img.data[idx+2]=c[2];img.data[idx+3]=255;
 }
 hc.putImageData(img,0,0);
 document.getElementById('leg').innerHTML='Eixo X = peso de <b>'+P.fi+'</b> &nbsp;|&nbsp; Eixo Y = peso de <b>'+P.fj+'</b><br>Fundo claro = melhor desempenho. ⭐ = ótimo encontrado pela análise.';
}
const px=x=>(x-P.xmin)/(P.xmax-P.xmin)*W;
const py=y=>H-(y-P.ymin)/(P.ymax-P.ymin)*H;
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
   p.dx+=(p.x-p.dx)*ease; p.dy+=(p.y-p.dy)*ease;
   const tr=traces[i], last=tr[tr.length-1];
   if(Math.abs(p.dx-last[0])+Math.abs(p.dy-last[1])>thr){ tr.push([p.dx,p.dy]); if(tr.length>90) tr.shift(); }
 }
}
function draw(){
 ctx.imageSmoothingEnabled=true;
 ctx.drawImage(heat,0,0,G,G,0,0,W,H);
 ctx.fillStyle='rgba(8,10,15,0.30)'; ctx.fillRect(0,0,W,H);
 if(document.getElementById('trace').checked){
   ctx.lineCap='round';
   for(let i=0;i<traces.length;i++){const tr=traces[i], hue=particles[i].hue;
     for(let k=1;k<tr.length;k++){const a=k/tr.length;
       ctx.beginPath(); ctx.moveTo(px(tr[k-1][0]),py(tr[k-1][1])); ctx.lineTo(px(tr[k][0]),py(tr[k][1]));
       ctx.strokeStyle='hsla('+hue+',95%,62%,'+(a*0.9).toFixed(3)+')'; ctx.lineWidth=(0.6+2.6*a)*SC; ctx.stroke();
     }
   }
 }
 if(document.getElementById('showv').checked){
   for(const p of particles){ ctx.beginPath(); ctx.moveTo(px(p.dx),py(p.dy));
     ctx.lineTo(px(p.dx+p.vx*3),py(p.dy+p.vy*3)); ctx.strokeStyle='rgba(255,220,120,.85)'; ctx.lineWidth=1.2*SC; ctx.stroke(); }
 }
 ctx.save();
 for(const p of particles){ ctx.shadowColor='hsl('+p.hue+',95%,60%)'; ctx.shadowBlur=8*SC;
   ctx.beginPath(); ctx.arc(px(p.dx),py(p.dy),3.6*SC,0,7); ctx.fillStyle='hsl('+p.hue+',95%,66%)'; ctx.fill(); }
 ctx.restore();
 ctx.save(); ctx.shadowColor='#ffd166'; ctx.shadowBlur=14*SC; star(px(P.ox),py(P.oy),11*SC,'#ffd166'); ctx.restore();
 if(document.getElementById('showg').checked && gbest){
   ctx.save(); ctx.shadowColor='#22d3ee'; ctx.shadowBlur=12*SC;
   ctx.beginPath(); ctx.arc(px(gbest.x),py(gbest.y),7*SC,0,7); ctx.strokeStyle='#22d3ee'; ctx.lineWidth=2.5*SC; ctx.stroke(); ctx.restore();
 }
}
function star(cx,cy,r,col){ ctx.beginPath();
 for(let i=0;i<10;i++){const ang=Math.PI/5*i-Math.PI/2,rad=i%2?r*0.45:r;
   const X=cx+Math.cos(ang)*rad,Y=cy+Math.sin(ang)*rad; i?ctx.lineTo(X,Y):ctx.moveTo(X,Y);}
 ctx.closePath(); ctx.fillStyle=col; ctx.fill(); }
// ---- render 3D ----
function draw3d(){
 const CX=W/2, CY=H*0.60, scale=Math.min(W,H)*0.58*zoom, dz=(P.zmax-P.zmin)||1;
 const cyw=Math.cos(yaw), syw=Math.sin(yaw), cpt=Math.cos(pitch), spt=Math.sin(pitch);
 const proj=(wx,wy,wz)=>{ const xr=wx*cyw-wy*syw, yr=wx*syw+wy*cyw;
   return [CX+xr*scale, CY-(yr*spt+wz*cpt)*scale, yr*cpt-wz*spt]; };
 const gx=b=>(b/(G-1)-0.5), gy=a=>(a/(G-1)-0.5), gz=v=>((v-P.zmin)/dz-0.5)*H3;
 const nx=x=>((x-P.xmin)/(P.xmax-P.xmin)-0.5), ny=y=>((y-P.ymin)/(P.ymax-P.ymin)-0.5);
 ctx.fillStyle='#05070b'; ctx.fillRect(0,0,W,H);
 const S=STEP3D, quads=[];
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
   ctx.strokeStyle='rgba(0,0,0,.18)'; ctx.lineWidth=.5*SC; ctx.stroke(); }
 if(document.getElementById('trace').checked){ ctx.lineCap='round';
   for(let i=0;i<traces.length;i++){ const pc=particles[i]; if(!pc) continue;
     const tr=traces[i], hue=pc.hue; let prev=null;
     for(let k=0;k<tr.length;k++){ const pp=proj(nx(tr[k][0]),ny(tr[k][1]),gz(fit(tr[k][0],tr[k][1]))+.015);
       if(prev){ const al=k/tr.length; ctx.beginPath(); ctx.moveTo(prev[0],prev[1]); ctx.lineTo(pp[0],pp[1]);
         ctx.strokeStyle='hsla('+hue+',95%,62%,'+(al*0.9).toFixed(3)+')'; ctx.lineWidth=(0.6+2.2*al)*SC; ctx.stroke(); }
       prev=pp; } } }
 if(document.getElementById('showv').checked){
   for(const p of particles){ const a0=proj(nx(p.dx),ny(p.dy),gz(fit(p.dx,p.dy))+.02);
     const b0=proj(nx(p.dx+p.vx*3),ny(p.dy+p.vy*3),gz(fit(p.dx+p.vx*3,p.dy+p.vy*3))+.02);
     ctx.beginPath(); ctx.moveTo(a0[0],a0[1]); ctx.lineTo(b0[0],b0[1]);
     ctx.strokeStyle='rgba(255,220,120,.85)'; ctx.lineWidth=1.2*SC; ctx.stroke(); } }
 const pts=particles.map(p=>({s:proj(nx(p.dx),ny(p.dy),gz(fit(p.dx,p.dy))+.02),hue:p.hue}))
                    .sort((m,n)=>n.s[2]-m.s[2]);
 ctx.save();
 for(const q of pts){ ctx.shadowColor='hsl('+q.hue+',95%,60%)'; ctx.shadowBlur=8*SC;
   ctx.beginPath(); ctx.arc(q.s[0],q.s[1],4*SC,0,7); ctx.fillStyle='hsl('+q.hue+',95%,66%)'; ctx.fill(); }
 ctx.restore();
 if(document.getElementById('showg').checked && gbest){
   const g=proj(nx(gbest.x),ny(gbest.y),gz(fit(gbest.x,gbest.y))+.02);
   ctx.save(); ctx.shadowColor='#22d3ee'; ctx.shadowBlur=12*SC;
   ctx.beginPath(); ctx.arc(g[0],g[1],7*SC,0,7); ctx.strokeStyle='#22d3ee'; ctx.lineWidth=2.5*SC; ctx.stroke(); ctx.restore(); }
 const o=proj(nx(P.ox),ny(P.oy),gz(fit(P.ox,P.oy))+.03);
 ctx.save(); ctx.shadowColor='#ffd166'; ctx.shadowBlur=14*SC; star(o[0],o[1],12*SC,'#ffd166'); ctx.restore();
}
function render(){ render3d?draw3d():draw(); }
function loop(){
 if(playing){ acc += SPF[+document.getElementById('speed').value]; while(acc>=1){ stepOnce(); acc--; } }
 if(render3d && autorot && !drag3 && !touchMode) yaw+=0.006;
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
 document.getElementById('row3d').style.display=is3d?'block':'none';
 document.getElementById('v3d').className=is3d?'':'sec';
 document.getElementById('v2d').className=is3d?'sec':'';
 cv.style.touchAction=is3d?'none':'auto';   // 2D: deixa rolar a página; 3D: gestos no canvas
 if(is3d) legend3d(); else buildHeat();
 render();
}
document.getElementById('v2d').onclick=()=>setView(false);
document.getElementById('v3d').onclick=()=>setView(true);
document.getElementById('autorot').onchange=function(){autorot=this.checked;};
document.getElementById('zscale').oninput=function(){H3=this.value/100; if(!playing) render();};
document.getElementById('zoom3d').oninput=function(){zoom=this.value/100; if(!playing) render();};

// ---- mouse (desktop) ----
cv.addEventListener('wheel',e=>{ if(!render3d) return; e.preventDefault();
 zoom=Math.max(0.4,Math.min(3,zoom*(e.deltaY<0?1.1:0.9)));
 document.getElementById('zoom3d').value=Math.round(zoom*100); if(!playing) render(); },{passive:false});
cv.addEventListener('mousedown',e=>{ if(render3d) drag3={x:e.clientX,y:e.clientY,yaw,pitch}; });
window.addEventListener('mousemove',e=>{ if(drag3&&!touchMode){ yaw=drag3.yaw+(e.clientX-drag3.x)*0.01;
  pitch=Math.max(0.15,Math.min(1.45,drag3.pitch+(e.clientY-drag3.y)*0.005)); if(!playing) render(); }});
window.addEventListener('mouseup',()=>{ if(!touchMode) drag3=null; });

// ---- TOUCH (celular): 1 dedo gira, 2 dedos (pinça) dão zoom ----
let touchMode=null, pinch0=null;
function tdist(t){ const dx=t[0].clientX-t[1].clientX, dy=t[0].clientY-t[1].clientY; return Math.hypot(dx,dy); }
cv.addEventListener('touchstart',e=>{
 if(!render3d) return;                 // 2D: gesto nativo (rolar a página)
 e.preventDefault();
 if(e.touches.length>=2){ touchMode='pinch'; pinch0={d:tdist(e.touches),zoom}; drag3=null; }
 else { touchMode='rot'; const t=e.touches[0]; drag3={x:t.clientX,y:t.clientY,yaw,pitch}; }
},{passive:false});
cv.addEventListener('touchmove',e=>{
 if(!render3d) return; e.preventDefault();
 if(touchMode==='pinch' && e.touches.length>=2 && pinch0){
   const r=tdist(e.touches)/(pinch0.d||1);
   zoom=Math.max(0.4,Math.min(3,pinch0.zoom*r));
   document.getElementById('zoom3d').value=Math.round(zoom*100);
   if(!playing) render();
 } else if(touchMode==='rot' && drag3 && e.touches.length===1){
   const t=e.touches[0];
   yaw=drag3.yaw+(t.clientX-drag3.x)*0.01;
   pitch=Math.max(0.15,Math.min(1.45,drag3.pitch+(t.clientY-drag3.y)*0.005));
   if(!playing) render();
 }
},{passive:false});
function touchEnd(e){
 if(e.touches.length===0){ touchMode=null; drag3=null; pinch0=null; }
 else if(e.touches.length===1){ touchMode='rot'; const t=e.touches[0];
   drag3={x:t.clientX,y:t.clientY,yaw,pitch}; pinch0=null; }
}
cv.addEventListener('touchend',touchEnd);
cv.addEventListener('touchcancel',touchEnd);

// ---- menu de abas ----
function show(which){
 const sim=which=='sim';
 document.getElementById('view-apres').style.display = sim?'none':'block';
 document.getElementById('view-sim').style.display   = sim?'block':'none';
 document.getElementById('tabApres').classList.toggle('active',!sim);
 document.getElementById('tabSim').classList.toggle('active',sim);
 window.scrollTo(0,0);
 if(sim) fitCanvas();                  // canvas só tem tamanho quando a aba está visível
}
document.getElementById('tabApres').onclick=()=>show('apres');
document.getElementById('tabSim').onclick=()=>show('sim');
buildHeat(); updateParHelp(); setView(true); reset(); loop();
</script></body></html>"""


def main():
    payload, apres = construir_dados()
    html = render_html(TEMPLATE_MOBILE, payload, apres)
    with open("pso_visualizacao_mobile.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("[ok] pso_visualizacao_mobile.html gerado (", len(html),
          "bytes ) — abra no celular.")


if __name__ == "__main__":
    main()
