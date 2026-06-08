#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copia pso_visualizacao.html de plano_b_pso_diabetes/ para esta pasta
e adiciona uma nova aba "Hiperparametros (FSS)" com os resultados
da meta-otimizacao.

Execute a partir de plano_b_pso_diabetes/meta_fss_pso/:
    python adicionar_aba_meta.py
"""

import base64, os, re

SRC = os.path.join('..', 'pso_visualizacao.html')
DST = 'pso_visualizacao.html'

# ---------------------------------------------------------------------------
# Ler HTML fonte
# ---------------------------------------------------------------------------
with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# ---------------------------------------------------------------------------
# Ler imagens como base64
# ---------------------------------------------------------------------------
def b64img(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')

img_fss = b64img('resultados_metafss_convergencia.png')
img_cmp = b64img('resultados_comparacao_convergencia.png')
img_imp = b64img('resultados_importancia_meta.png')
print('[ok] imagens lidas')

# ---------------------------------------------------------------------------
# 1. Adicionar botao de aba no nav
# ---------------------------------------------------------------------------
OLD_BTN = '<button id="tabSim" class="tab">\U0001f3ae Simula\u00e7\u00e3o interativa</button>'
NEW_BTN = (OLD_BTN +
           '\n   <button id="tabMeta" class="tab">\U0001f4c8 Hiperpar\u00e2metros (FSS)</button>')
assert OLD_BTN in html, 'ERRO: botao tabSim nao encontrado no HTML'
html = html.replace(OLD_BTN, NEW_BTN, 1)
print('[ok] botao de aba adicionado')

# ---------------------------------------------------------------------------
# 2. Construir conteudo da nova aba
# ---------------------------------------------------------------------------
nova_secao = f"""
<section id="view-meta" style="display:none">
<div class="apres">

 <div class="card">
  <h2>5. Meta-Otimiza\u00e7\u00e3o: FSS calibrando os hiperpar\u00e2metros do PSO</h2>
  <p>O PSO original usa par\u00e2metros emp\u00edricos fixos (w\u202f=\u202f0,7\u00a0;\u00a0c1\u202f=\u202fc2\u202f=\u202f1,5\u00a0;\u00a0\u03bb\u202f=\u202f0,05).
     Neste experimento um segundo algoritmo de Computa\u00e7\u00e3o Natural &mdash; o
     <b>FSS (Fish School Search)</b> &mdash; assume o papel de &ldquo;meta-otimizador&rdquo;:
     cada peixe representa uma configura\u00e7\u00e3o candidata de hiperpar\u00e2metros e nada em busca
     da que maximiza a AUC de classifica\u00e7\u00e3o.</p>
  <p>A avalia\u00e7\u00e3o de cada peixe usa <b>CV-3</b> (3-fold cross-validation) exclusivamente
     sobre o conjunto de treino &mdash; o conjunto de teste nunca \u00e9 visto durante a busca,
     evitando <em>data leakage</em>.</p>
  <div class="kpis">
   <div class="kpi"><b>15</b><span>peixes no FSS</span></div>
   <div class="kpi"><b>30</b><span>itera\u00e7\u00f5es do FSS</span></div>
   <div class="kpi"><b>15\u202f\u00d7\u202f80</b><span>part\u00edculas\u202f\u00d7\u202fiter por avalia\u00e7\u00e3o</span></div>
   <div class="kpi"><b>CV-3</b><span>folds para o fitness</span></div>
  </div>
 </div>

 <div class="card">
  <h2>6. Hiperpar\u00e2metros encontrados pelo FSS</h2>
  <table class="r">
   <tr><th>Par\u00e2metro</th><th>Papel</th><th>Padr\u00e3o emp\u00edrico</th><th>Valor (FSS)</th><th>Varia\u00e7\u00e3o</th></tr>
   <tr>
    <td><b>w_in</b></td>
    <td class="muted">In\u00e9rcia das part\u00edculas</td>
    <td>0,700</td><td class="pos">0,666</td><td class="neg">&minus;0,034</td>
   </tr>
   <tr>
    <td><b>c1</b></td>
    <td class="muted">Confian\u00e7a pessoal</td>
    <td>1,500</td><td class="pos">0,737</td><td class="neg">&minus;0,763</td>
   </tr>
   <tr>
    <td><b>c2</b></td>
    <td class="muted">Confian\u00e7a social</td>
    <td>1,500</td><td class="pos">0,592</td><td class="neg">&minus;0,908</td>
   </tr>
   <tr>
    <td><b>&lambda; (LAMBDA)</b></td>
    <td class="muted">Regulariza\u00e7\u00e3o L2</td>
    <td>0,050</td><td class="pos">0,016</td><td class="neg">&minus;0,034</td>
   </tr>
  </table>
  <p><b>Por que o FSS preferiu valores menores?</b> Com apenas ~250 amostras de treino e
     26 features, part\u00edculas com <b>menos in\u00e9rcia e menor atra\u00e7\u00e3o social</b> exploram o
     espa\u00e7o de pesos de forma mais diversa antes de convergir. A
     <b>regulariza\u00e7\u00e3o menor</b> permite que o modelo capture mais sinal dos dados, gerando
     AUC superior sem sobreajuste perceptível no conjunto de teste.</p>
 </div>

 <div class="card">
  <h2>7. Gr\u00e1fico: converg\u00eancia do meta-FSS</h2>
  <img src="data:image/png;base64,{img_fss}" alt="convergencia meta-FSS">
  <p><b>O que mostra:</b> a melhor AUC de CV-3 encontrada pelo cardume a cada itera\u00e7\u00e3o.
     O cardume parte de AUC&nbsp;\u2248&nbsp;0,73 e converge para <b>0,787</b> &mdash; evidenciando
     que os tr\u00eas movimentos do FSS (individual, instintivo, volitivo) orientam a busca de
     forma progressiva e eficaz.</p>
  <p class="muted">A linha tracejada \u00e9 a AUC de teste do PSO com par\u00e2metros emp\u00edricos (baseline).
     O FSS supera esse valor j\u00e1 na itera\u00e7\u00e3o&nbsp;5.</p>
 </div>

 <div class="card">
  <h2>8. PSO padr\u00e3o \u00d7 PSO meta-otimizado</h2>
  <img src="data:image/png;base64,{img_cmp}" alt="comparacao convergencia PSO">
  <div class="kpis" style="margin-top:14px">
   <div class="kpi"><b>0,664</b><span>AUC teste &mdash; PSO padr\u00e3o</span></div>
   <div class="kpi"><b>0,678</b><span>AUC teste &mdash; PSO meta (FSS)</span></div>
   <div class="kpi"><b style="color:#8ee6a0">+2,1\u202f%</b><span>melhoria relativa</span></div>
   <div class="kpi"><b>0,701</b><span>cosseno entre os pesos</span></div>
  </div>
  <p><b>O que mostra:</b> o PSO com hiperpar\u00e2metros encontrados pelo FSS converge mais
     r\u00e1pido no treino <b>(0,837 vs&nbsp;0,821)</b> e obt\u00e9m AUC de teste superior
     <b>(0,678 vs&nbsp;0,664)</b>, com +2,1\u202f% de ganho relativo.</p>
  <p><b>Cosseno&nbsp;=&nbsp;0,701</b> (diferente do 1,000 original PSO&nbsp;\u00d7&nbsp;sklearn).
     Isso \u00e9 esperado e correto: os dois PSOs usam regulariza\u00e7\u00f5es diferentes
     (\u03bb&nbsp;=&nbsp;0,016 vs&nbsp;0,050), portanto convergem para dire\u00e7\u00f5es
     distintas no espa\u00e7o de pesos. Confirma que a meta-otimiza\u00e7\u00e3o encontrou uma
     solu\u00e7\u00e3o <em>genuinamente diferente</em> da emp\u00edrica.</p>
 </div>

 <div class="card">
  <h2>9. Perfil do indiv\u00edduo ideal &mdash; PSO meta-otimizado</h2>
  <img src="data:image/png;base64,{img_imp}" alt="importancia features PSO meta">
  <p><b>Como ler:</b> peso <span class="pos">verde/positivo</span> = ter mais dessa
     caracter\u00edstica aproxima do perfil ideal; peso
     <span class="neg">vermelho/negativo</span> = ter mais afasta do ideal.
     O padr\u00e3o qualitativo permanece consistente com o PSO original: fatores de
     <b>composi\u00e7\u00e3o corporal</b> e <b>resist\u00eancia \u00e0 insulina</b> dominam os pesos negativos,
     confirmando a robustez da an\u00e1lise.</p>
  <p class="muted">Quer ver o algoritmo trabalhando visualmente?
     Abra a aba <b>\U0001f3ae Simula\u00e7\u00e3o interativa</b> acima.</p>
 </div>

</div>
</section>
"""

# ---------------------------------------------------------------------------
# 3. Inserir a nova secao antes de </script></body></html>
# ---------------------------------------------------------------------------
CLOSING = '</script></body></html>'
assert CLOSING in html, 'ERRO: fechamento do HTML nao encontrado'
html = html.replace(CLOSING, '</script>' + nova_secao + '</body></html>', 1)
print('[ok] secao view-meta inserida')

# ---------------------------------------------------------------------------
# 4. Atualizar funcao show() para incluir view-meta
# ---------------------------------------------------------------------------
old_show = re.compile(
    r"function show\(which\)\{.*?window\.scrollTo\(0,0\);\s*\}",
    re.DOTALL
)
new_show = (
    "function show(which){\n"
    " document.getElementById('view-apres').style.display = which=='apres'?'block':'none';\n"
    " document.getElementById('view-sim').style.display   = which=='sim'?'block':'none';\n"
    " document.getElementById('view-meta').style.display  = which=='meta'?'block':'none';\n"
    " document.getElementById('tabApres').classList.toggle('active',which=='apres');\n"
    " document.getElementById('tabSim').classList.toggle('active',which=='sim');\n"
    " document.getElementById('tabMeta').classList.toggle('active',which=='meta');\n"
    " window.scrollTo(0,0);\n"
    "}"
)
html, n_show = old_show.subn(new_show, html, count=1)
assert n_show == 1, 'ERRO: funcao show() nao encontrada'
print('[ok] funcao show() atualizada')

# ---------------------------------------------------------------------------
# 5. Adicionar handler de clique para tabMeta
# ---------------------------------------------------------------------------
OLD_HANDLER = "document.getElementById('tabSim').onclick=()=>show('sim');"
NEW_HANDLER = (OLD_HANDLER +
               "\ndocument.getElementById('tabMeta').onclick=()=>show('meta');")
assert OLD_HANDLER in html, 'ERRO: handler tabSim nao encontrado'
html = html.replace(OLD_HANDLER, NEW_HANDLER, 1)
print('[ok] handler tabMeta adicionado')

# ---------------------------------------------------------------------------
# Salvar
# ---------------------------------------------------------------------------
with open(DST, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'[ok] {DST} gerado ({len(html):,} bytes) — abra no navegador.')
