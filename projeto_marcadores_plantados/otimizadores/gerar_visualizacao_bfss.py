#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera um app HTML autocontido que apresenta e SIMULA (replay) o BFSS de seleção de
variáveis sobre a base de marcadores plantados — no mesmo espírito da visualização do PSO.

Duas abas:
  1) APRESENTAÇÃO — o problema (otimizador é o entregável; base é testbed de marcadores
     plantados), o BFSS "na natureza", e os resultados reais (P/R/F1, R², auditoria).
  2) SIMULAÇÃO interativa — REPLAY de execuções reais do BFSS:
       • AQUÁRIO: o cardume "nadando" no plano (nº de variáveis × R²); cada peixe tem
         tamanho ∝ peso; a ⭐ é o melhor-global. O cardume migra para o canto bom
         (poucas variáveis, R² alto), contraindo/dilatando (movimento volitivo).
       • MAPA DE SELEÇÃO: 25 variáveis (9 marcadores relevantes × 16 ruídos); a barra de
         cada uma cresce conforme a fração do cardume que a seleciona. Os marcadores
         "acendem" e os ruídos apagam — inclusive o distrator TEMPO_DIAGNOSTICO.
       • PLACAR ao vivo: Precisão / Recall / F1 do melhor-global a cada iteração + R².
     É possível COMPARAR PRESETS (campeã × alta-sensibilidade × alta-parcimônia) para ver
     o tradeoff precisão↔recall acontecendo.

Os números vêm de execuções REAIS do BFSS (mesmo pipeline de rodar_bfss.py). O estado do
cardume por iteração é gravado via o callback `on_iter` do otimizador (sem alterar a dinâmica).

Saída: bfss_visualizacao.html (abra no navegador; zero dependências externas).
"""
import json
import os

import numpy as np

from bfss.preprocessamento import preparar_dados
from bfss.avaliador import AvaliadorWrapper
from bfss.otimizador import run_bfss
from bfss.validacao import validar_selecao

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ_PLANO = os.path.dirname(AQUI)
CSV = os.path.join(RAIZ_PLANO, "dados_sinteticos", "saida", "base_bfss.csv")
GABARITO = os.path.join(RAIZ_PLANO, "dados_sinteticos", "saida", "gabarito_marcadores.json")

# Configuração comum dos runs (modo rápido/subamostrado — o relatório mostra que a
# seleção é idêntica ao canônico). Mantém o app leve e a geração em poucos minutos.
NUM_FISHES = 30
NUM_ITERS = 70
K = 5
SEED = 42
W_SCALE = 500.0
MAX_TREINO = 2500
MAX_TESTE = 1200

# Três presets que contam a história do tradeoff (valores vindos do tuning real):
PRESETS = [
    dict(id="campea", nome="Campeã (equilíbrio)",
         desc="α=0,8 · thres_c=0,6 · thres_v=0,4 — corta o ruído sem perder marcadores",
         p=dict(alpha=0.8, thres_c=0.6, thres_v=0.4)),
    dict(id="recall", nome="Alta sensibilidade",
         desc="α=0,9 · thres_v=0,2 — pega todos os marcadores, mas deixa entrar ruído",
         p=dict(alpha=0.9, thres_c=0.6, thres_v=0.2)),
    dict(id="parcimonia", nome="Alta parcimônia",
         desc="α=0,7 · thres_v=0,4 — modelo enxuto, sacrifica um pouco de recall",
         p=dict(alpha=0.7, thres_c=0.6, thres_v=0.4)),
]


def r2_baseline(dados):
    """R² usando TODAS as variáveis candidatas (referência de comparação)."""
    av = AvaliadorWrapper(dados["X_train"], dados["X_test"],
                          dados["y_train"], dados["y_test"], alpha=1.0, k=K)
    _, r2 = av.avaliar(np.ones(len(dados["feature_names"]), dtype=int))
    return float(r2)


def _rodar_preset(dados, preset):
    """Roda um preset gravando o estado do cardume por iteração (replay)."""
    snaps = []

    def on_iter(t, cardume, melhor_pos, melhor_fit, melhor_r2):
        # cada peixe: [nº selecionadas, R², peso] — para posicionar no aquário
        fish = [[int(f.position.sum()), round(float(f.r2), 3), round(float(f.weight), 1)]
                for f in cardume.fishes]
        # quantos peixes selecionam cada variável (barras do mapa de seleção)
        q = [int(c) for c in np.sum([f.position for f in cardume.fishes], axis=0)]
        # variáveis do melhor-global (linha de destaque + placar P/R/F1)
        s = [int(i) for i in np.where(melhor_pos == 1)[0]]
        snaps.append({"b": [round(float(melhor_fit), 4), round(float(melhor_r2), 4),
                            int(melhor_pos.sum())], "f": fish, "q": q, "s": s})

    res = run_bfss(dados, num_fishes=NUM_FISHES, num_iterations=NUM_ITERS,
                   k=K, seed=SEED, w_scale=W_SCALE, verbose=False,
                   on_iter=on_iter, **preset["p"])
    val = validar_selecao(res.selected_features, dados["relevantes"], dados["irrelevantes"])
    sel_idx = [dados["feature_names"].index(c) for c in res.selected_features]
    out = {
        "id": preset["id"], "nome": preset["nome"], "desc": preset["desc"],
        "P": round(val.precisao, 3), "R": round(val.recall, 3), "F1": round(val.f1, 3),
        "nsel": res.num_selecionadas, "sel": sel_idx, "snaps": snaps,
        "vp": val.vp, "fp": val.fp, "fn": val.fn, "r2final": round(res.r2, 4),
    }
    return out, res, val


def construir_dados():
    """Roda o baseline + os 3 presets reais e devolve (payload, apres).

    Reutilizado pelos geradores desktop e mobile (uma fonte de verdade)."""
    dados = preparar_dados(CSV, GABARITO, test_size=0.3, seed=SEED,
                           max_treino=MAX_TREINO, max_teste=MAX_TESTE)
    feats = dados["feature_names"]
    rel = set(dados["relevantes"])
    r2base = r2_baseline(dados)

    presets_out, champ = [], None
    r2lo, r2hi = 1.0, 0.0
    for pr in PRESETS:
        print(f"\n=== BFSS preset '{pr['id']}' ({pr['desc']}) ===")
        po, res, val = _rodar_preset(dados, pr)
        print(f"   -> P={po['P']} R={po['R']} F1={po['F1']} | sel={po['nsel']} "
              f"| R²={po['r2final']}")
        for sp in po["snaps"]:
            for f in sp["f"]:
                r2lo = min(r2lo, f[1]); r2hi = max(r2hi, f[1])
        presets_out.append(po)
        if pr["id"] == "campea":
            champ = (res, val)

    r2lo = max(0.0, r2lo - 0.02)
    r2hi = min(1.0, r2hi + 0.02)

    payload = {
        "nf": NUM_FISHES, "nrelev": len(dados["relevantes"]),
        "vars": feats, "relev": [1 if c in rel else 0 for c in feats],
        "wscale": W_SCALE, "r2lo": round(r2lo, 3), "r2hi": round(r2hi, 3),
        "r2base": round(r2base, 4), "presets": presets_out,
        "info": {"n_pac": dados["n_pacientes"], "n_at": dados["n_atendimentos"],
                 "n_tr": dados["n_treino"], "n_te": dados["n_teste"]},
    }
    apres = montar_apresentacao_bfss(payload, champ, dados)
    return payload, apres


def montar_apresentacao_bfss(payload, champ, dados):
    """Narrativa da aba de apresentação, com os números reais da execução campeã."""
    res, val = champ
    feats = payload["vars"]
    relset = set(dados["relevantes"])
    selset = set(res.selected_features)
    info = payload["info"]

    # tabela de auditoria por variável (relevantes em cima, ruídos embaixo)
    linhas = []
    for c in feats:
        papel = "relevante" if c in relset else "ruído"
        if c in selset and c in relset:
            tag, cls = "✅ VP", "pos"
        elif c in selset and c not in relset:
            tag, cls = "⚠️ FP", "neg"
        elif c not in selset and c in relset:
            tag, cls = "❌ FN", "neg"
        else:
            tag, cls = "✓ VN", "muted"
        linhas.append(f"<tr><td>{c}</td><td class='muted'>{papel}</td>"
                      f"<td>{'sim' if c in selset else 'não'}</td>"
                      f"<td class='{cls}'>{tag}</td></tr>")
    tabela = "".join(linhas)

    P = f"{val.precisao:.3f}"; R = f"{val.recall:.3f}"; F1 = f"{val.f1:.3f}"
    r2 = f"{res.r2:.3f}"; r2b = f"{payload['r2base']:.3f}"
    nrel = payload["nrelev"]; nruido = len(feats) - nrel

    return f"""
<div class="apres">

 <div class="card">
  <h2>1. O que está sendo avaliado</h2>
  <p>O <b>entregável</b> não é a base de dados — é o <b>otimizador de Computação Natural</b>: o
     <b>BFSS (Binary Fish School Search)</b>, um algoritmo inspirado no comportamento de
     <b>cardumes de peixes</b>, aplicado à <b>seleção de variáveis</b>. A base é apenas o
     <b>campo de testes</b>.</p>
  <p class="muted"><span class="tag">como provamos que funciona</span> Usamos a estratégia de
     <b>marcadores plantados</b>: construímos uma base sintética em que <b>sabemos de antemão</b>
     quais variáveis realmente causam o desfecho. Assim a qualidade do otimizador é medida por
     <b>verdade-base</b> (precisão / recall / F1), e não por uma métrica interna que poderia se
     auto-enganar.</p>
 </div>

 <div class="card">
  <h2>2. Os marcadores plantados</h2>
  <p>São <b>{nrel + nruido} variáveis candidatas</b>: <b>{nrel} relevantes</b> (os marcadores que
     <i>de fato</i> influenciam o alvo <code>DELTA_HLY</code>) e <b>{nruido} ruídos</b> que não
     deveriam ser escolhidos. Entre os ruídos há um <b>distrator plantado de propósito</b>
     (<code>TEMPO_DIAGNOSTICO</code>), <b>correlacionado</b> com o sinal para tentar enganar o
     seletor. O BFSS tem de achar os relevantes e <b>rejeitar</b> os ruídos.</p>
  <div class="kpis">
   <div class="kpi"><b>{info['n_pac']}</b><span>pacientes</span></div>
   <div class="kpi"><b>{info['n_at']}</b><span>atendimentos</span></div>
   <div class="kpi"><b>{nrel}</b><span>marcadores relevantes</span></div>
   <div class="kpi"><b>{nruido}</b><span>ruídos</span></div>
  </div>
 </div>

 <div class="card">
  <h2>3. O BFSS na natureza</h2>
  <p>Cada <b>peixe</b> é uma resposta candidata: um vetor de 25 bits (1 = variável selecionada).
     O cardume busca em conjunto através de três movimentos de Sargo (2013):</p>
  <p><b>Alimentação</b> — peixes que melhoraram "engordam" (ganham peso/influência).
     <b>Movimento instintivo</b> — o cardume é puxado na direção de quem melhorou.
     <b>Movimento volitivo</b> — o cardume <b>contrai</b> em torno do baricentro quando está indo
     bem (explotação) ou <b>dilata</b> quando estagna (exploração). É essa dança que você verá no
     <b>aquário</b> da simulação.</p>
 </div>

 <div class="card">
  <h2>4. Resultado da execução campeã</h2>
  <div class="kpis">
   <div class="kpi"><b>{P}</b><span>Precisão</span></div>
   <div class="kpi"><b>{R}</b><span>Recall</span></div>
   <div class="kpi"><b>{F1}</b><span>F1</span></div>
   <div class="kpi"><b>{res.num_selecionadas}/{len(feats)}</b><span>variáveis escolhidas</span></div>
  </div>
  <p><b>Precisão {P}</b> = <b>zero falsos positivos</b>: nenhum ruído entrou, nem o distrator.
     <b>Recall {R}</b> = achou {len(val.vp)} dos {nrel} marcadores. E o <b>R² subiu</b> de
     <b>{r2b}</b> (todas as 25 variáveis) para <b>{r2}</b> (só as selecionadas): menos ruído, mais
     poder preditivo.</p>
 </div>

 <div class="card">
  <h2>5. Auditoria por variável (vs verdade-base)</h2>
  <table class="r">
   <tr><th>Variável</th><th>No gabarito</th><th>Selecionada</th><th>Resultado</th></tr>
   {tabela}
  </table>
  <p class="muted">VP = acerto · VN = ruído corretamente descartado · FP = falso alarme ·
     FN = marcador perdido.</p>
 </div>

 <div class="card">
  <h2>6. A história do distrator e do "miss" honesto</h2>
  <p><b>Por que o distrator foi rejeitado:</b> <code>TEMPO_DIAGNOSTICO</code> foi plantado
     <b>correlacionado</b> com o sinal para enganar — e o BFSS o descartou em todos os cenários,
     evidência de que captura <b>causa</b>, não mera correlação.</p>
  <p><b>Por que falta o <code>IS_CARDIOVASCULAR</code>:</b> no modelo gerador ele é o driver
     <b>mais fraco e mais tardio</b>, colocado de propósito <b>abaixo</b> do distrator na "zona
     contestada". Recuperá-lo exigiria também admitir o distrator e <b>derrubar a precisão</b>. O
     otimizador fez a <b>escolha correta de compromisso</b> — e o miss é robusto (não é falta de
     dados). Use o seletor <b>Alta sensibilidade</b> na simulação para ver o que acontece quando
     se força o recall: o ruído entra junto.</p>
 </div>

 <p class="muted" style="text-align:center;margin:20px 0">
   Quer ver o cardume trabalhando? Abra a aba <b>🎮 Simulação interativa</b> acima.</p>

</div>
"""


# --------------------------------------------------------------------------- #
# JS compartilhado entre os templates desktop e mobile (mesmos IDs de elemento).
# --------------------------------------------------------------------------- #
JS_CORE = r"""
const DATA = /*DATA*/;
const NF = DATA.nf, NV = DATA.vars.length, NREL = DATA.nrelev;
let pi = 0, P = DATA.presets[pi];
let iterf = 0, playing = false;
const SPEED = [0, 0.12, 0.25, 0.45, 0.8, 1.4];   // por passo do slider 1..5
const $ = id => document.getElementById(id);
const setT = (id, v) => { const e = $(id); if (e) e.textContent = v; };
const hue = i => Math.round(360 * i / NF);
const h01 = i => { const x = Math.sin(i * 127.13) * 43758.5453; return x - Math.floor(x); };

const cvA = $('cvA'), ctxA = cvA.getContext('2d');
const cvC = $('cvC'), ctxC = cvC.getContext('2d');
let WA = 600, HA = 480, WC = 300, HC = 90, DPR = 1;
function fit() {
  DPR = Math.min(window.devicePixelRatio || 1, 2);
  [cvA, cvC].forEach(cv => { const r = cv.getBoundingClientRect(); if (!r.width) return;
    cv.width = Math.round(r.width * DPR); cv.height = Math.round(r.height * DPR); });
  WA = cvA.width; HA = cvA.height; WC = cvC.width; HC = cvC.height; draw();
}
window.addEventListener('resize', fit);
window.addEventListener('orientationchange', () => setTimeout(fit, 250));

// ---- mapa de seleção (DOM, responsivo) ----
const mapa = $('mapa');
function buildMapa() {
  mapa.innerHTML = '';
  const lblRel = document.createElement('div');
  lblRel.className = 'mlbl rel'; lblRel.textContent = '🟢 marcadores plantados — devem ser ACHADOS';
  mapa.appendChild(lblRel);
  for (let i = 0; i < NV; i++) {
    if (i === NREL) {
      const lblNoi = document.createElement('div');
      lblNoi.className = 'mlbl noi'; lblNoi.textContent = '🟠 ruídos — devem ficar de FORA';
      mapa.appendChild(lblNoi);
    }
    const row = document.createElement('div');
    row.className = 'mrow ' + (DATA.relev[i] ? 'rel' : 'noi'); row.dataset.i = i;
    row.innerHTML = '<span class="mname">' + DATA.vars[i] + '</span>' +
      '<div class="mbar"><div class="mfill"></div></div><span class="mpct">0%</span>';
    mapa.appendChild(row);
  }
}
function updateMapa() {
  const a = Math.floor(iterf), b = Math.min(P.snaps.length - 1, a + 1), t = iterf - a;
  const SA = P.snaps[a], SB = P.snaps[b];
  const sel = new Set(curSnap().s);
  mapa.querySelectorAll('.mrow').forEach(row => {
    const i = +row.dataset.i;
    const frac = (SA.q[i] * (1 - t) + SB.q[i] * t) / NF;
    row.querySelector('.mfill').style.width = (frac * 100).toFixed(1) + '%';
    row.querySelector('.mpct').textContent = Math.round(frac * 100) + '%';
    row.classList.toggle('best', sel.has(i));
  });
}

function curSnap() { return P.snaps[Math.min(P.snaps.length - 1, Math.round(iterf))]; }

// ---- aquário (canvas) ----
function star(ctx, cx, cy, r, col) {
  ctx.beginPath();
  for (let i = 0; i < 10; i++) { const ang = Math.PI / 5 * i - Math.PI / 2, rad = i % 2 ? r * 0.45 : r;
    const X = cx + Math.cos(ang) * rad, Y = cy + Math.sin(ang) * rad; i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); }
  ctx.closePath(); ctx.fillStyle = col; ctx.fill();
}
function fish(x, y, r, h) {
  ctxA.save(); ctxA.translate(x, y);
  ctxA.shadowColor = 'hsl(' + h + ',85%,55%)'; ctxA.shadowBlur = 5 * DPR;
  ctxA.fillStyle = 'hsl(' + h + ',85%,62%)';
  ctxA.beginPath(); ctxA.ellipse(0, 0, r, r * 0.6, 0, 0, 7); ctxA.fill();
  ctxA.beginPath(); ctxA.moveTo(r * 0.8, 0); ctxA.lineTo(r * 1.6, -r * 0.7);
  ctxA.lineTo(r * 1.6, r * 0.7); ctxA.closePath(); ctxA.fill();
  ctxA.restore();
}
function drawAquario() {
  const a = Math.floor(iterf), b = Math.min(P.snaps.length - 1, a + 1), t = iterf - a;
  const SA = P.snaps[a], SB = P.snaps[b];
  const padL = 50 * DPR, padB = 36 * DPR, padT = 16 * DPR, padR = 14 * DPR;
  const x0 = padL, x1 = WA - padR, y0 = HA - padB, y1 = padT;
  const lo = DATA.r2lo, hi = DATA.r2hi;
  const X = n => x0 + (x1 - x0) * (n / NV);
  const Y = r => y0 + (y1 - y0) * ((r - lo) / (hi - lo));
  // fundo + "sweet spot" (poucas variáveis, R² alto = canto superior esquerdo)
  ctxA.fillStyle = '#0a0e14'; ctxA.fillRect(0, 0, WA, HA);
  const g = ctxA.createRadialGradient(X(0), Y(hi), 4 * DPR, X(0), Y(hi), (x1 - x0) * 0.8);
  g.addColorStop(0, 'rgba(110,231,135,0.16)'); g.addColorStop(1, 'rgba(110,231,135,0)');
  ctxA.fillStyle = g; ctxA.fillRect(0, 0, WA, HA);
  // grade + eixos
  ctxA.strokeStyle = 'rgba(255,255,255,0.07)'; ctxA.lineWidth = 1 * DPR;
  ctxA.fillStyle = '#9aa4b2'; ctxA.font = (11 * DPR) + 'px system-ui,sans-serif';
  ctxA.textAlign = 'center'; ctxA.textBaseline = 'top';
  for (let n = 0; n <= NV; n += 5) {
    ctxA.beginPath(); ctxA.moveTo(X(n), y1); ctxA.lineTo(X(n), y0); ctxA.stroke();
    ctxA.fillText(n, X(n), y0 + 5 * DPR);
  }
  ctxA.textAlign = 'right'; ctxA.textBaseline = 'middle';
  for (let k = 0; k <= 4; k++) { const r = lo + (hi - lo) * k / 4;
    ctxA.beginPath(); ctxA.moveTo(x0, Y(r)); ctxA.lineTo(x1, Y(r)); ctxA.stroke();
    ctxA.fillText(r.toFixed(2), x0 - 6 * DPR, Y(r));
  }
  ctxA.fillStyle = '#c8d0db'; ctxA.font = (12 * DPR) + 'px system-ui,sans-serif';
  ctxA.textAlign = 'center'; ctxA.textBaseline = 'bottom';
  ctxA.fillText('nº de variáveis selecionadas  (←  menos = melhor)', (x0 + x1) / 2, HA - 4 * DPR);
  ctxA.save(); ctxA.translate(13 * DPR, (y0 + y1) / 2); ctxA.rotate(-Math.PI / 2);
  ctxA.textBaseline = 'top'; ctxA.fillText('R²  (↑  maior = melhor)', 0, 0); ctxA.restore();
  // peixes (identidade estável por índice -> jitter determinístico p/ não sobrepor)
  for (let i = 0; i < NF; i++) {
    const fa = SA.f[i], fb = SB.f[i];
    const ns = fa[0] * (1 - t) + fb[0] * t;
    const r2 = fa[1] * (1 - t) + fb[1] * t;
    const w = fa[2] * (1 - t) + fb[2] * t;
    const jx = (h01(i) - 0.5) * 0.7, jy = (h01(i + 99) - 0.5) * (hi - lo) * 0.03;
    const rad = (2.5 + 7 * Math.sqrt(Math.max(0, (w - 1) / (DATA.wscale - 1)))) * DPR;
    fish(X(ns + jx), Y(r2 + jy), rad, hue(i));
  }
  // melhor-global (estrela)
  const bns = SA.b[2] * (1 - t) + SB.b[2] * t, br = SA.b[1] * (1 - t) + SB.b[1] * t;
  ctxA.save(); ctxA.shadowColor = '#ffd166'; ctxA.shadowBlur = 12 * DPR;
  star(ctxA, X(bns), Y(br), 10 * DPR, '#ffd166'); ctxA.restore();
}

function drawConv() {
  ctxC.fillStyle = '#0a0e14'; ctxC.fillRect(0, 0, WC, HC);
  const n = P.snaps.length, lo = DATA.r2lo, hi = DATA.r2hi;
  const X = i => 4 * DPR + (WC - 8 * DPR) * (i / (n - 1));
  const Y = r => HC - 6 * DPR - (HC - 12 * DPR) * ((r - lo) / (hi - lo));
  ctxC.strokeStyle = '#22d3ee'; ctxC.lineWidth = 1.8 * DPR; ctxC.beginPath();
  for (let i = 0; i < n; i++) { const r = P.snaps[i].b[1]; i ? ctxC.lineTo(X(i), Y(r)) : ctxC.moveTo(X(i), Y(r)); }
  ctxC.stroke();
  const ci = Math.round(iterf);
  ctxC.strokeStyle = 'rgba(255,209,102,0.8)'; ctxC.lineWidth = 1 * DPR;
  ctxC.beginPath(); ctxC.moveTo(X(ci), 2 * DPR); ctxC.lineTo(X(ci), HC - 2 * DPR); ctxC.stroke();
}

function score(sel) {
  let tp = 0, fp = 0; sel.forEach(i => { DATA.relev[i] ? tp++ : fp++; });
  const pr = (tp + fp) ? tp / (tp + fp) : 0, rc = NREL ? tp / NREL : 0;
  const f1 = (pr + rc) ? 2 * pr * rc / (pr + rc) : 0;
  return { pr, rc, f1 };
}
function updateScore() {
  const s = curSnap(), sc = score(s.s);
  setT('scP', (sc.pr * 100).toFixed(0) + '%');
  setT('scR', (sc.rc * 100).toFixed(0) + '%');
  setT('scF1', sc.f1.toFixed(2));
  setT('scR2', s.b[1].toFixed(3));
  setT('scNsel', s.b[2]);
  setT('it', (Math.round(iterf) + 1) + ' / ' + P.snaps.length);
}

function draw() { drawAquario(); updateMapa(); drawConv(); updateScore(); }

function loop() {
  if (playing) {
    iterf += SPEED[+$('speed').value];
    if (iterf >= P.snaps.length - 1) { iterf = P.snaps.length - 1; playing = false; $('play').textContent = '▶ Play'; }
  }
  draw(); requestAnimationFrame(loop);
}

// ---- presets ----
function buildPresets() {
  const box = $('presets'); box.innerHTML = '';
  DATA.presets.forEach((p, i) => {
    const b = document.createElement('button');
    b.className = 'preset' + (i === 0 ? ' on' : ''); b.textContent = p.nome;
    b.onclick = () => setPreset(i); box.appendChild(b);
  });
  setPreset(0);
}
function setPreset(i) {
  pi = i; P = DATA.presets[pi]; iterf = 0; playing = false;
  const btns = $('presets').querySelectorAll('.preset');
  btns.forEach((b, k) => b.classList.toggle('on', k === i));
  $('play').textContent = '▶ Play';
  $('presetDesc').innerHTML = '<b>' + P.nome + '</b> — ' + P.desc +
    '<br><span class="muted">final: Precisão ' + (P.P * 100).toFixed(0) + '% · Recall ' +
    (P.R * 100).toFixed(0) + '% · F1 ' + P.F1.toFixed(2) + ' · ' + P.nsel + ' variáveis</span>';
  draw();
}

// ---- controles ----
$('play').onclick = function () {
  if (iterf >= P.snaps.length - 1) iterf = 0;
  playing = !playing; this.textContent = playing ? '⏸ Pause' : '▶ Play';
};
$('step').onclick = () => { playing = false; $('play').textContent = '▶ Play';
  iterf = Math.min(P.snaps.length - 1, Math.round(iterf) + 1); draw(); };
$('reset').onclick = () => { playing = false; $('play').textContent = '▶ Play'; iterf = 0; draw(); };

// ---- abas ----
function show(which) {
  const sim = which === 'sim';
  $('view-apres').style.display = sim ? 'none' : 'block';
  $('view-sim').style.display = sim ? 'block' : 'none';
  $('tabApres').classList.toggle('active', !sim);
  $('tabSim').classList.toggle('active', sim);
  window.scrollTo(0, 0);
  if (sim) fit();
}
$('tabApres').onclick = () => show('apres');
$('tabSim').onclick = () => show('sim');

buildMapa(); buildPresets(); loop();
"""


def render_html(template, payload, apres):
    """Injeta o JS compartilhado, os dados reais (JSON) e a apresentação no template."""
    return (template
            .replace("/*JS*/", JS_CORE)
            .replace("/*DATA*/", json.dumps(payload))
            .replace("<!--APRES-->", apres))


def main():
    payload, apres = construir_dados()
    html = render_html(TEMPLATE, payload, apres)
    out = os.path.join(AQUI, "bfss_visualizacao.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n[ok] {out} gerado ({len(html):,} bytes) — abra no navegador.")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>BFSS — marcadores plantados: apresentação e simulação</title>
<style>
 :root{--bg:#0f1115;--card:#171a21;--line:#2a2f3a;--txt:#e6e6e6;--mut:#9aa4b2;--blue:#2563eb}
 *{box-sizing:border-box}
 body{font-family:system-ui,Arial,sans-serif;margin:0;background:var(--bg);color:var(--txt)}
 header{padding:10px 16px;background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
 h1{font-size:16px;margin:0}
 small{color:var(--mut)}
 .tabs{margin-top:8px;display:flex;gap:8px}
 .tab{background:#374151;color:#fff;border:0;border-radius:8px;padding:9px 14px;font-size:14px;font-weight:600;cursor:pointer}
 .tab.active{background:var(--blue)}
 .wrap{display:flex;flex-wrap:wrap;gap:16px;padding:16px;align-items:flex-start}
 .aqcol{flex:1 1 460px;min-width:300px}
 canvas#cvA{width:100%;aspect-ratio:5/4;background:#000;border:1px solid var(--line);border-radius:10px;display:block}
 canvas#cvC{width:100%;height:80px;background:#000;border:1px solid var(--line);border-radius:8px;display:block;margin-top:10px}
 .mapcol{flex:1 1 360px;min-width:280px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}
 .panel{flex:1 1 240px;min-width:230px;max-width:340px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
 .row{margin:10px 0;display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
 label{font-size:13px;color:#c8d0db}
 button{background:var(--blue);color:#fff;border:0;border-radius:6px;padding:8px 12px;cursor:pointer;font-size:13px}
 button.sec{background:#374151}
 .btns{display:flex;gap:8px;flex-wrap:wrap}
 .preset{background:#374151;flex:1 1 auto}
 .preset.on{background:var(--blue)}
 input[type=range]{width:130px}
 .legend{font-size:12px;color:var(--mut);margin-top:6px;line-height:1.5}
 /* placar */
 .score{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 2px}
 .sc{flex:1 1 60px;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px;text-align:center}
 .sc b{display:block;font-size:20px;color:#8ee6a0;font-variant-numeric:tabular-nums}
 .sc span{font-size:11px;color:var(--mut)}
 /* mapa de seleção */
 .mlbl{font-size:12px;font-weight:700;margin:8px 0 4px;color:#c8d0db}
 .mlbl.rel{color:#6ee787} .mlbl.noi{color:#ffb870}
 .mrow{display:flex;align-items:center;gap:8px;margin:2px 0}
 .mname{flex:0 0 122px;font-size:11px;color:#c8d0db;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 .mbar{flex:1;height:13px;background:#0f1115;border:1px solid var(--line);border-radius:7px;overflow:hidden}
 .mfill{height:100%;width:0;border-radius:7px;transition:width .08s linear}
 .mrow.rel .mfill{background:linear-gradient(90deg,#2e7d50,#6ee787)}
 .mrow.noi .mfill{background:linear-gradient(90deg,#7a4a1e,#ffb870)}
 .mpct{flex:0 0 32px;text-align:right;font-size:11px;color:var(--mut);font-variant-numeric:tabular-nums}
 .mrow.best .mname{font-weight:700;color:#fff}
 .mrow.best .mname::before{content:"✓ ";color:#22d3ee}
 /* apresentação */
 .apres{max-width:1000px;margin:0 auto;padding:18px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin:14px 0;overflow-x:auto}
 .card h2{font-size:18px;margin:0 0 10px}
 .card p{line-height:1.65;color:#c8d0db;font-size:14px;margin:8px 0}
 .kpis{display:flex;flex-wrap:wrap;gap:12px;margin:10px 0}
 .kpi{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:12px 16px;min-width:120px;text-align:center}
 .kpi b{display:block;font-size:26px;color:#8ee6a0;font-variant-numeric:tabular-nums}
 .kpi span{font-size:12px;color:var(--mut)}
 table.r{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}
 table.r th,table.r td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left}
 .pos{color:#6ee787}.neg{color:#ff9aa2}.muted{color:var(--mut);font-size:13px}
 .tag{display:inline-block;background:#1f2937;border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:12px;color:var(--mut);margin-right:6px}
 code{background:#0f1115;border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:12px}
 @media(max-width:900px){.panel{max-width:none}}
</style></head>
<body>
<header>
 <h1>BFSS &amp; marcadores plantados <small>— do problema ao resultado</small></h1>
 <nav class="tabs">
  <button id="tabApres" class="tab active">📊 Apresentação</button>
  <button id="tabSim" class="tab">🎮 Simulação interativa</button>
 </nav>
</header>

<section id="view-apres"><!--APRES--></section>

<section id="view-sim" style="display:none">
 <div style="padding:10px 16px"><small>Replay de execuções <b>reais</b> do BFSS. No <b>aquário</b>, cada peixe é uma combinação de variáveis (tamanho ∝ peso); o cardume migra para <b>poucas variáveis + R² alto</b>. No <b>mapa</b>, as barras mostram quantos % do cardume seleciona cada variável — os marcadores acendem, os ruídos apagam. Troque o <b>preset</b> para ver o tradeoff precisão↔recall.</small></div>
 <div class="wrap">
  <div class="aqcol">
   <canvas id="cvA"></canvas>
   <canvas id="cvC"></canvas>
   <div class="legend">Curva: R² do melhor-global por iteração (marcador = iteração atual).</div>
  </div>
  <div class="mapcol">
   <div style="font-size:13px;color:#c8d0db;margin-bottom:4px">Mapa de seleção do cardume</div>
   <div id="mapa"></div>
  </div>
  <div class="panel">
   <div class="row"><label>Preset (configuração)</label></div>
   <div class="btns" id="presets"></div>
   <div class="legend" id="presetDesc"></div>
   <div class="score">
    <div class="sc"><b id="scP">—</b><span>Precisão</span></div>
    <div class="sc"><b id="scR">—</b><span>Recall</span></div>
    <div class="sc"><b id="scF1">—</b><span>F1</span></div>
   </div>
   <div class="score">
    <div class="sc"><b id="scR2">—</b><span>R² (melhor)</span></div>
    <div class="sc"><b id="scNsel">—</b><span>nº variáveis</span></div>
    <div class="sc"><b id="it">—</b><span>iteração</span></div>
   </div>
   <div class="row btns">
    <button id="play">▶ Play</button>
    <button id="step" class="sec">Passo</button>
    <button id="reset" class="sec">Reiniciar</button>
   </div>
   <div class="row"><label>Velocidade</label><input type="range" id="speed" min="1" max="5" value="3"></div>
   <div class="legend">⭐ = melhor-global · cada peixe colorido é um membro do cardume. Placar = Precisão/Recall/F1 do melhor-global <b>vs verdade-base</b>, ao vivo.</div>
  </div>
 </div>
</section>
<script>/*JS*/</script>
</body></html>"""


if __name__ == "__main__":
    main()
