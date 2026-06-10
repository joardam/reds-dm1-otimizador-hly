#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versão **mobile-first** da visualização do BFSS (apresentação + simulação/replay).

Mesmo conteúdo e mesmos dados reais do gerador desktop (`gerar_visualizacao_bfss.py`) —
reaproveita `construir_dados()`, `render_html()` e o `JS_CORE` (mesmos IDs de elemento),
trocando apenas o layout/CSS para celular:

  * <meta viewport> + uma coluna (aquário, mapa de seleção e painel empilham);
  * canvas do aquário responsivo (preenche a largura, nítido em telas retina);
  * alvos de toque maiores (botões/presets/sliders) e tipografia legível no telefone;
  * mapa de seleção com nomes de variável que se adaptam à largura.

Saída: bfss_visualizacao_mobile.html (abra no celular; autocontido, zero instalação).
"""
import os

from gerar_visualizacao_bfss import construir_dados, render_html, AQUI


TEMPLATE_MOBILE = r"""<!DOCTYPE html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>BFSS — marcadores plantados (mobile)</title>
<style>
 :root{--bg:#0f1115;--card:#171a21;--line:#2a2f3a;--txt:#e6e6e6;--mut:#9aa4b2;--blue:#2563eb}
 *{box-sizing:border-box}
 html{-webkit-text-size-adjust:100%}
 body{font-family:system-ui,-apple-system,Arial,sans-serif;margin:0;background:var(--bg);color:var(--txt);-webkit-tap-highlight-color:transparent}
 header{padding:10px 12px;background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
 h1{font-size:15px;margin:0;line-height:1.3}
 small{color:var(--mut);font-size:12px}
 .tabs{margin-top:8px;display:flex;gap:8px}
 .tab{flex:1;background:#374151;color:#fff;border:0;border-radius:8px;padding:11px 8px;font-size:14px;font-weight:600;cursor:pointer;min-height:44px}
 .tab.active{background:var(--blue)}
 .simhint{padding:8px 12px;color:var(--mut);font-size:12.5px;line-height:1.5}
 .wrap{display:flex;flex-direction:column;gap:14px;padding:0 12px 28px}
 canvas#cvA{width:100%;aspect-ratio:1/1;max-height:78vh;background:#000;border:1px solid var(--line);border-radius:12px;display:block}
 canvas#cvC{width:100%;height:70px;background:#000;border:1px solid var(--line);border-radius:8px;display:block}
 .mapcol{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px}
 .panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
 .row{margin:12px 0;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
 label{font-size:14px;color:#c8d0db}
 button{background:var(--blue);color:#fff;border:0;border-radius:8px;padding:11px 14px;cursor:pointer;font-size:14px;min-height:44px}
 button.sec{background:#374151}
 .btns{display:flex;gap:8px;flex-wrap:wrap}
 .btns button{flex:1 1 auto}
 .preset{background:#374151;flex:1 1 30%}
 .preset.on{background:var(--blue)}
 input[type=range]{width:100%;height:30px;accent-color:var(--blue)}
 .field{display:flex;flex-direction:column;gap:6px;width:100%}
 .legend{font-size:12.5px;color:var(--mut);margin-top:4px;line-height:1.55}
 .score{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 2px}
 .sc{flex:1 1 28%;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:10px;text-align:center}
 .sc b{display:block;font-size:22px;color:#8ee6a0;font-variant-numeric:tabular-nums}
 .sc span{font-size:11px;color:var(--mut)}
 .mlbl{font-size:12.5px;font-weight:700;margin:8px 0 4px;color:#c8d0db}
 .mlbl.rel{color:#6ee787} .mlbl.noi{color:#ffb870}
 .mrow{display:flex;align-items:center;gap:8px;margin:3px 0}
 .mname{flex:0 0 38%;font-size:11.5px;color:#c8d0db;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 .mbar{flex:1;height:15px;background:#0f1115;border:1px solid var(--line);border-radius:8px;overflow:hidden}
 .mfill{height:100%;width:0;border-radius:8px;transition:width .08s linear}
 .mrow.rel .mfill{background:linear-gradient(90deg,#2e7d50,#6ee787)}
 .mrow.noi .mfill{background:linear-gradient(90deg,#7a4a1e,#ffb870)}
 .mpct{flex:0 0 34px;text-align:right;font-size:11px;color:var(--mut);font-variant-numeric:tabular-nums}
 .mrow.best .mname{font-weight:700;color:#fff}
 .mrow.best .mname::before{content:"✓ ";color:#22d3ee}
 .apres{max-width:1000px;margin:0 auto;padding:14px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:12px 0;overflow-x:auto}
 .card h2{font-size:17px;margin:0 0 10px}
 .card p{line-height:1.65;color:#c8d0db;font-size:14.5px;margin:8px 0}
 .kpis{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0}
 .kpi{flex:1 1 130px;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px;text-align:center}
 .kpi b{display:block;font-size:24px;color:#8ee6a0;font-variant-numeric:tabular-nums}
 .kpi span{font-size:12px;color:var(--mut)}
 table.r{width:100%;border-collapse:collapse;margin-top:8px;font-size:13.5px}
 table.r th,table.r td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left}
 .pos{color:#6ee787}.neg{color:#ff9aa2}.muted{color:var(--mut);font-size:13px}
 .tag{display:inline-block;background:#1f2937;border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:12px;color:var(--mut);margin-right:6px}
 code{background:#0f1115;border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:12px}
</style></head>
<body>
<header>
 <h1>BFSS &amp; marcadores plantados <small>— versão para celular</small></h1>
 <nav class="tabs">
  <button id="tabApres" class="tab active">📊 Apresentação</button>
  <button id="tabSim" class="tab">🎮 Simulação</button>
 </nav>
</header>

<section id="view-apres"><!--APRES--></section>

<section id="view-sim" style="display:none">
 <div class="simhint">Replay de execuções <b>reais</b> do BFSS. No <b>aquário</b>, o cardume migra para <b>poucas variáveis + R² alto</b>; no <b>mapa</b>, os marcadores acendem e os ruídos apagam. Troque o <b>preset</b> para ver o tradeoff precisão↔recall.</div>
 <div class="wrap">
  <canvas id="cvA"></canvas>
  <canvas id="cvC"></canvas>
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
   <div class="field"><label>Velocidade</label><input type="range" id="speed" min="1" max="5" value="3"></div>
  </div>
  <div class="mapcol">
   <div style="font-size:13px;color:#c8d0db;margin-bottom:4px">Mapa de seleção do cardume</div>
   <div id="mapa"></div>
  </div>
 </div>
</section>
<script>/*JS*/</script>
</body></html>"""


def main():
    payload, apres = construir_dados()
    html = render_html(TEMPLATE_MOBILE, payload, apres)
    out = os.path.join(AQUI, "bfss_visualizacao_mobile.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n[ok] {out} gerado ({len(html):,} bytes) — abra no celular.")


if __name__ == "__main__":
    main()
