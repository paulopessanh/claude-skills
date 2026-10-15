#!/usr/bin/env python3
"""_ecobook.py — composes the brandbook, a single HTML page that holds every chapter of the brand.

A library for ecosystem_builder.py. The page is generated from the same source and the same SVG files as the rest of the
package, so a colour, a name or a sentence cannot differ between the brandbook and a file. Every colour in its own
interface is a token of the brand. It runs without a server: the only external request is the Google Fonts stylesheet.
Running this file only prints this text.

Stdlib only. Deterministic.
"""

import html
import re
import sys

from _ecolib import contrast, hex_rgb, cmyk_approx, ridge_points, file_stem
import _ecoassets as A
import _ecoedit as E
import _ecostrat as ST
import _ecodeck as DK

esc = html.escape


def uniq(svg_str, uid):
    """Make ids unique when the same SVG is inlined more than once, and let CSS size it."""
    s = re.sub(r'id="([^"]+)"', lambda m: f'id="{uid}-{m.group(1)}"', svg_str)
    s = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{uid}-{m.group(1)}"', s)
    s = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{uid}-{m.group(1)})", s)
    s = re.sub(r'(<svg [^>]*?) width="[^"]*" height="[^"]*"', r"\1", s, count=1)
    return s


def p_(t, cls=""):
    return f'<p{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>{esc(t)}</p>'


LK_L = {"symbol": "Símbolo", "horizontal": "Horizontal", "vertical": "Vertical"}
POL_L = {"positive": "positiva", "negative": "negativa", "mono": "uma cor"}
ST_L = {"preferred": "Preferida", "allowed": "Permitida", "forbidden": "Proibida"}


def kv_table(rows, head=("Item", "Regra")):
    return ('<div class="tw"><table><thead><tr>' + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr></thead><tbody>"
            + "".join("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in r) + "</tr>" for r in rows) + "</tbody></table></div>")


def chapter(n, cid, title, body, lead=""):
    return (f'<section id="{cid}" class="ch"><header><p class="eyebrow">Capítulo {n}</p><h2>{esc(title)}</h2>'
            f'{f"<p class={chr(34)}lead{chr(34)}>{esc(lead)}</p>" if lead else ""}</header>{body}</section>')


def copy_btn(text, label="Copiar"):
    return f'<button type="button" class="copy" data-copy="{esc(text, quote=True)}" aria-label="{esc(label)} {esc(text)}">{esc(label)}</button>'


def css(b, flat, c):
    t = c.t
    f = c.fam
    return f"""
:root{{--bg:{t('Neblina')};--surface:{t('Branco')};--fg:{t('Tinta')};--muted:{t('Cume_40')};--line:{t('Cume_20')};--link:{t('Cume_50')};
--accent:{t('Vale_50')};--accent-fg:{t('Branco')};--hero:{t('Cume_70')};--hero-fg:{t('Neblina')};--hero-line:{t('Cume_50')};--soft:{t('Cume_10')};
--display:{f['headline']};--body:{f['body']};--mono:{f['mono']};}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:{t('Cume_70')};--surface:{t('Cume_60')};--fg:{t('Cume_10')};--muted:{t('Cume_30')};--line:{t('Cume_50')};--link:{t('Vale_30')};--soft:{t('Cume_60')};color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:{t('Cume_70')};--surface:{t('Cume_60')};--fg:{t('Cume_10')};--muted:{t('Cume_30')};--line:{t('Cume_50')};--link:{t('Vale_30')};--soft:{t('Cume_60')};color-scheme:dark}}
@media print{{.top,.toc,.skip,.btn,.copy{{display:none!important}} body{{font-size:12pt}} .shell{{display:block}} .ch{{break-before:page}} .hero{{break-after:page;-webkit-print-color-adjust:exact;print-color-adjust:exact}} *{{animation:none!important}} .ln{{stroke-dashoffset:0!important}}}}
table.mx th,table.mx td{{padding:6px 8px;text-align:center;font-size:13px}} table.mx th[scope=row]{{text-align:left;white-space:nowrap}} .mxc svg{{display:block;margin:0 auto 4px;max-width:64px}} .mxs{{display:block;color:var(--muted)}} .st-preferred .mxs{{color:var(--accent);font-weight:600}} .st-forbidden{{opacity:.55}}\n*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--fg);font-family:var(--body);font-size:18px;line-height:1.6;padding-block:0}}
a{{color:var(--link)}} a:focus-visible,button:focus-visible,summary:focus-visible{{outline:3px solid var(--accent);outline-offset:3px}}
.skip{{position:absolute;left:-999px}} .skip:focus{{left:16px;top:16px;background:var(--surface);padding:8px 12px;z-index:50}}
.gut{{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
.top{{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:var(--bg);border-bottom:1px solid var(--line)}}
.top .in{{max-width:1280px;margin:0 auto;display:flex;align-items:center;gap:12px;min-height:60px;padding-block:8px}}
.top .logo{{width:190px;max-width:42vw;line-height:0}} .top .sp{{flex:1}}
.btn,.copy{{font:600 14px/1 var(--body);border:1px solid var(--line);background:var(--surface);color:var(--fg);padding:9px 14px;border-radius:999px;cursor:pointer}}
.btn:hover,.copy:hover{{border-color:var(--link)}} .copy{{padding:6px 10px;font-size:13px}} .copy.ok{{background:var(--accent);color:var(--accent-fg);border-color:var(--accent)}}
.only-dark{{display:none}} :root[data-theme="dark"] .only-dark{{display:block}} :root[data-theme="dark"] .only-light{{display:none}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]) .only-dark{{display:block}} :root:not([data-theme="light"]) .only-light{{display:none}}}}
.shell{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:240px minmax(0,1fr);gap:40px}}
nav.toc{{position:sticky;top:calc(61px + env(safe-area-inset-top,0px));align-self:start;max-height:calc(100vh - 80px);overflow:auto;padding:24px 0;font-size:15px}}
nav.toc a{{display:block;padding:5px 10px;text-decoration:none;color:var(--muted);border-left:2px solid var(--line)}} nav.toc a:hover{{color:var(--fg)}}
nav.toc a[aria-current="true"]{{color:var(--fg);border-left-color:var(--accent);font-weight:600}}
@media (max-width:1000px){{.shell{{display:block}} nav.toc{{position:static;max-height:none;border-bottom:1px solid var(--line);padding:12px 0}}}}
main{{min-width:0;padding-block:24px 80px}}
.hero{{background:var(--hero);color:var(--hero-fg);border-radius:20px;padding:clamp(28px,6vw,72px);display:grid;gap:24px;overflow:hidden}}
.hero h1{{font:300 clamp(48px,9vw,112px)/1 var(--display);margin:0;letter-spacing:-.01em;text-wrap:balance}}
.hero .sym{{max-width:360px;width:100%}} .hero p{{margin:0;max-width:56ch}} .hero .tag{{font:italic 400 clamp(22px,3vw,34px)/1.25 var(--display)}}
.meta{{display:flex;flex-wrap:wrap;gap:8px 20px;font:500 14px var(--mono);color:var(--hero-fg)}} .badge{{border:1px solid var(--hero-line);border-radius:999px;padding:4px 12px}}
section.ch{{padding-block:64px 8px;border-top:1px solid var(--line);margin-top:48px;scroll-margin-top:80px}} section.ch:first-of-type{{border-top:0;margin-top:0}}
.eyebrow{{font:600 12px/1 var(--body);letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 12px}}
h2{{font:400 clamp(32px,5vw,52px)/1.1 var(--display);margin:0 0 12px;text-wrap:balance}} h3{{font:500 24px/1.25 var(--display);margin:32px 0 8px}}
.lead{{font:400 clamp(20px,2.4vw,26px)/1.4 var(--display);max-width:44ch;margin:0 0 24px;color:var(--fg)}}
p{{max-width:68ch;margin:0 0 14px}}
.grid{{display:grid;gap:16px}} .g2{{grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr))}} .g3{{grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr))}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px;min-width:0}} .card h3{{margin-top:0}}
.stage{{border-radius:14px;padding:20px;display:flex;align-items:center;justify-content:center;min-height:160px;min-width:0}} .stage svg{{max-width:100%;height:auto;max-height:200px}}
.s-pos{{background:{t('Neblina')}}} .s-neg{{background:{t('Cume_70')}}} .s-mono{{background:{t('Branco')};border:1px solid var(--line)}}
figure{{margin:0}} figcaption{{font-size:14px;color:var(--muted);margin-top:8px}}
.fig{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px}} .fig svg{{width:100%;height:auto;display:block;border-radius:8px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;padding:0;margin:0;list-style:none}} .chips li{{border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:4px 14px;font-size:15px}}
.quote{{font:300 clamp(24px,3.4vw,40px)/1.25 var(--display);max-width:26ch;margin:0 0 10px}}
.defs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:16px}} .defs dt{{font:600 12px var(--body);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}} .defs dd{{margin:0;font:400 22px/1.35 var(--display)}}
.tl{{list-style:none;margin:0;padding:0;border-left:2px solid var(--line)}} .tl li{{padding:0 0 18px 20px;position:relative}} .tl li::before{{content:"";position:absolute;left:-7px;top:9px;width:12px;height:12px;border-radius:50%;background:var(--accent)}} .tl b{{font:500 22px var(--display)}}
table{{border-collapse:collapse;width:100%;font-size:15px}} th,td{{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}} th{{font:600 12px var(--body);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.tw{{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:14px}}
.ramp{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:8px}}
.sw{{border-radius:10px;padding:12px;min-height:128px;display:flex;flex-direction:column;justify-content:space-between;font:500 13px/1.35 var(--mono);border:1px solid var(--line);min-width:0}}
.sw b{{font:700 22px var(--body)}} .sw .copy{{align-self:flex-start;margin-top:6px}}
.bar{{display:flex;height:56px;border-radius:10px;overflow:hidden;border:1px solid var(--line)}} .bar span{{display:flex;align-items:flex-end;padding:4px 8px;font:600 12px var(--mono)}}
.grad{{height:96px;border-radius:12px;border:1px solid var(--line)}}
pre{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px;overflow-x:auto;font:400 13.5px/1.55 var(--mono);margin:0 0 12px}}
.spec{{font-size:22px}} .spec .d{{font:300 56px/1.05 var(--display)}}
.pi{{display:flex;gap:14px;align-items:center}} .pi svg{{width:48px;height:48px;flex:none}}
.do li,.dont li{{margin-bottom:6px}} .do{{padding-left:20px}} .dont{{padding-left:20px}}
details{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin-bottom:10px}} summary{{cursor:pointer;font:500 20px var(--display)}}
.demo{{background:var(--hero);border-radius:14px;padding:28px;display:flex;flex-wrap:wrap;gap:20px;align-items:center;justify-content:space-between}} .demo svg{{max-width:340px;width:100%;height:auto}} .demo polyline{{stroke:var(--hero-fg)}}
.drawn .ln{{animation:none}} .replay .ln{{animation:draw var(--dur) var(--ease) 1 both}}
@keyframes draw{{from{{stroke-dashoffset:var(--len)}}to{{stroke-dashoffset:0}}}}
@media (prefers-reduced-motion: reduce){{.replay .ln{{animation:none}}}}
footer.col{{border-top:1px solid var(--line);padding-block:32px;font-size:14px;color:var(--muted)}}
{(ST.CSS + DK.CSS) if ST.has(b) else ""}
"""


JS = """
(function(){
var root=document.documentElement;
function get(k){try{return localStorage.getItem(k)}catch(e){return null}} function set(k,v){try{localStorage.setItem(k,v)}catch(e){}}
var saved=get('sfi-theme'); if(saved==='light'||saved==='dark'){root.setAttribute('data-theme',saved)}
var tb=document.getElementById('theme');
if(tb){tb.addEventListener('click',function(){var cur=root.getAttribute('data-theme');
 var dark=cur?cur==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches; var next=dark?'light':'dark'; root.setAttribute('data-theme',next); set('sfi-theme',next); tb.textContent=next==='dark'?'Tema claro':'Tema escuro';});}
var mb=document.getElementById('menu'), nv=document.getElementById('toc');
if(mb&&nv){mb.addEventListener('click',function(){nv.hidden=!nv.hidden; mb.setAttribute('aria-expanded',String(!nv.hidden));}); function fit(){ if(window.matchMedia('(min-width:1001px)').matches){nv.hidden=false;mb.hidden=true}else{mb.hidden=false;if(!nv.dataset.u){nv.hidden=true}} } fit(); window.addEventListener('resize',fit); nv.addEventListener('click',function(e){if(e.target.tagName==='A'&&!window.matchMedia('(min-width:1001px)').matches){nv.hidden=true;mb.setAttribute('aria-expanded','false')}});}
document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('.copy'); if(!b)return; var t=b.getAttribute('data-copy');
 function done(){var o=b.textContent;b.textContent='Copiado';b.classList.add('ok');setTimeout(function(){b.textContent=o;b.classList.remove('ok')},1400)}
 function fallback(){var r=document.createRange();var n=b.closest('.sw,pre,div')||b;try{var ta=document.createElement('textarea');ta.value=t;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();var ok=document.execCommand('copy');document.body.removeChild(ta);if(ok)done()}catch(x){}}
 if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,fallback)}else{fallback()}});
var links=[].slice.call(document.querySelectorAll('nav.toc a'));
if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){links.forEach(function(a){a.removeAttribute('aria-current')});var a=document.querySelector('nav.toc a[href="#'+en.target.id+'"]');if(a)a.setAttribute('aria-current','true')}})},{rootMargin:'-20% 0px -70% 0px'});
 [].forEach.call(document.querySelectorAll('section.ch'),function(s){io.observe(s)});}
window.addEventListener('beforeprint',function(){[].forEach.call(document.querySelectorAll('details'),function(d){d.open=true})});
var rp=document.getElementById('replay'), dm=document.getElementById('demo');
if(rp&&dm){rp.addEventListener('click',function(){dm.classList.remove('replay');void dm.getBoundingClientRect();dm.classList.add('replay')});}
})();
"""


def build(b, flat, fams, c, svgs, files, standalone=True):
    ident = b["identity"]
    name, sig = ident["name"], ident["sigla"]
    t = c.t
    pal = lambda n: c.t(n)
    chs = []

    def add(cid, title, body, lead=""):
        chs.append((cid, title, body, lead))

    # --- história
    h = b["history"]
    ms = "".join(f"<li><b>{m['year']}</b><br>{esc(m['text'])}</li>" for m in h.get("milestones", []))
    add("historia", "História", "".join(p_(x) for x in h["paragraphs"]) + f'<div class="card"><h3>De onde vem o nome</h3>{p_(h["name_origin"])}</div>'
        + (f'<h3>Linha do tempo</h3><ul class="tl">{ms}</ul>' if ms else "")
        + f'<p class="eyebrow">Fontes desta história</p>{p_(", ".join(h["sources"]))}', lead=h["title"])

    # --- propósito
    pu = b["purpose"]
    add("proposito", "Propósito e posicionamento", '<dl class="defs">' + "".join(f"<div class='card'><dt>{esc(k)}</dt><dd>{esc(pu[key])}</dd></div>" for k, key in
        (("Missão", "mission"), ("Visão", "vision"), ("Posicionamento", "positioning"), ("Promessa", "promise"))) + "</dl>")

    # --- pétreos e vetados
    pet = "".join(f"<div class='card'><h3>{esc(p['text'])}</h3>{p_('Origem: ' + p['origin'])}{p_('No desenho: ' + p['visual_translation'])}</div>" for p in b["petreos"])
    vet = "".join(f"<li><b>{esc(v['text'])}.</b> {esc(v['reason'])}</li>" for v in b["vetados"])
    add("petreos", "Pétreos e vetados", f'<p>Pétreos são as verdades que não mudam. Cada decisão visual desta marca nasce de um deles.</p><div class="grid g3">{pet}</div>'
        f'<h3>O que a marca não faz</h3><ul class="dont">{vet}</ul>')

    # --- conceito
    cn = b["concept"]
    fm = cn["formula"]
    add("conceito", "Conceito", f'<p class="quote">{esc(cn["big_idea"])}</p><div class="grid g3">'
        f'<div class="card"><h3>Ícone</h3>{p_(fm["icon"])}</div><div class="card"><h3>Índice</h3>{p_(fm["index"])}</div><div class="card"><h3>Símbolo</h3>{p_(fm["symbol"])}</div></div>'
        f'<h3>Manifesto</h3>' + "".join(f'<p class="quote" style="font-size:clamp(22px,3vw,34px)">{esc(x)}</p>' for x in cn["manifesto"]))

    # --- personalidade e público
    ps, au = b["personality"], b["audience"]
    pers = "".join(f"<div class='card'><h3>{esc(x['name'])}</h3>{p_(x['who'])}{p_('Pensa: ' + x['thinks'])}{p_('Precisa: ' + x['needs'])}</div>" for x in au["personas"])
    add("personalidade", "Personalidade e público", f'<ul class="chips">' + "".join(f"<li>{esc(a)}</li>" for a in ps["attributes"]) + "</ul>"
        + p_("A marca não é: " + ", ".join(ps["is_not"]) + ".") + p_("Arquétipo (hipótese): " + ps["archetype_hypothesis"]) + f'<h3>Para quem</h3>{p_(au["summary"])}<div class="grid g2">{pers}</div>'
        + "<h3>Promessas emocionais</h3><ul>" + "".join(f"<li>{esc(x)}</li>" for x in au["emotional_promises"]) + "</ul>")

    if ST.has(b):
        for _ch in ST.chapters(b):
            add(*_ch)

    # --- nome e anatomia
    ids = ident
    add("nome", "Nome e anatomia", p_(h["name_origin"]) + f'<div class="stage s-pos fig">{uniq(svgs["Horizontal-Positive"], "an")}</div>'
        '<div class="tw"><table><thead><tr><th>Parte</th><th>Texto</th><th>Regra</th></tr></thead><tbody>'
        f'<tr><td>Tipo</td><td>Marca mista</td><td>Símbolo e nome, sempre juntos nas assinaturas.</td></tr>'
        f'<tr><td>Descritor</td><td>{esc(ids["descriptor"])}</td><td>Obrigatório. Diz o que a empresa faz.</td></tr>'
        f'<tr><td>Tagline</td><td>{esc(ids["tagline"])}</td><td>Obrigatória. Carrega a essência e o posicionamento.</td></tr>'
        f'<tr><td>Slogan</td><td>Fora desta versão</td><td>{esc(ids["slogan"]["reason"])}</td></tr>'
        f'<tr><td>Hookline</td><td>Fora desta versão</td><td>{esc(ids["hookline"]["reason"])}</td></tr></tbody></table></div>'
        + _name_in_text(b))

    # --- símbolo (construção)
    sy = b["symbol"]
    W, H = c.W, c.H
    pts = c.pts
    poly = " ".join(f"{x:.1f},{H - y + 0:.1f}" for x, y in pts)
    first = pts[1]
    import math
    ang = sy["slope_deg"]
    ar = 52
    ex, ey = ar * math.cos(math.radians(ang)), H - ar * math.sin(math.radians(ang))
    lab = f'font-size="9" fill="var(--fg)" font-family="{esc(c.fam["mono"])}"'
    cons = (f'<svg viewBox="{-H - 20} {-H - 30} {W + 2 * H + 40} {H * 3 + 60}" role="img" aria-label="Construção do símbolo: ângulo de {ang} graus e área de proteção">'
            f'<rect x="{-H}" y="{-H}" width="{W + 2 * H}" height="{3 * H}" fill="none" stroke="var(--muted)" stroke-width="1.2" stroke-dasharray="5 5"/>'
            f'<line x1="{-H}" y1="{H}" x2="{W + H}" y2="{H}" stroke="var(--muted)" stroke-width="0.8"/>'
            f'<polyline points="{poly}" fill="none" stroke="{t("Vale_50")}" stroke-width="{c.sw}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M {ar} {H} A {ar} {ar} 0 0 0 {ex:.1f} {ey:.1f}" fill="none" stroke="var(--fg)" stroke-width="1.2"/>'
            f'<text x="{ar + 6}" y="{H - 8}" {lab}>{ang}°</text>'
            f'<line x1="{first[0]:.1f}" y1="{-H}" x2="{first[0]:.1f}" y2="{H}" stroke="var(--muted)" stroke-width="0.8" stroke-dasharray="2 4"/>'
            f'<text x="{first[0] + 6:.1f}" y="{-H + 14}" {lab}>pico = 100, a medida de proteção</text>'
            f'<text x="{-H + 6}" y="{H + 13}" {lab}>linha de base</text></svg>')
    add("simbolo", "Símbolo", p_(sy["rationale"]) + f'<div class="fig">{cons}<figcaption>Construção. Todos os trechos sobem e descem em {ang}°. As alturas dos vértices, em relação ao pico mais alto: '
        + ", ".join(f"{v:g}" for v in sy["vertices"]) + ".</figcaption></div>"
        + f'<div class="card"><h3>Estudo geométrico</h3>{p_(sy["geometric_study_note"])}</div>', lead=sy["name"])

    # --- logotipo e assinaturas
    wm, lk = b["wordmark"], b["lockups"]
    lock_cards = ""
    for kind in ("horizontal", "vertical"):
        lock_cards += (f'<div class="card"><h3>Assinatura {kind}</h3>{p_(lk[kind]["when"])}<div class="fig">{A.modulation_svg(c, kind)}'
                       f'<figcaption>u é a altura do pico mais alto nesta assinatura. {esc(A.modulation_notes(c, kind))}</figcaption></div></div>')
    add("logotipo", "Logotipo e assinaturas", p_(wm["lettering"]) + f'<div class="fig">{A.wordmark_construction_svg(c)}<figcaption>Construção do nome. {esc(wm["construction_note"])}</figcaption></div>'
        + '<h3>Assinaturas</h3><div class="grid g2" style="align-items:start">' + lock_cards + "</div>")

    # --- versões
    ver = ""
    for kind, label in (("Symbol", "Símbolo"), ("Horizontal", "Horizontal"), ("Vertical", "Vertical"), ("Seal", "Selo"), ("Wordmark", "Nome")):
        cells = "".join(f'<figure><div class="stage s-{cls}">{uniq(svgs[f"{kind}-{pol.capitalize()}"], f"v{kind[:2]}{cls}")}</div><figcaption>{label}, {pol_l}</figcaption></figure>'
                        for pol, cls, pol_l in (("positive", "pos", "positiva"), ("negative", "neg", "negativa"), ("mono", "mono", "uma cor")))
        ver += f'<h3>{label}</h3><div class="grid g3">{cells}</div>'
    add("versoes", "Versões", p_("Cada assinatura existe em três polaridades. Use a positiva sobre fundo claro, a negativa sobre fundo escuro e a de uma cor quando só houver uma tinta.") + ver
        + f'<h3>Ícone do site</h3><div class="stage s-pos" style="max-width:200px">{uniq(svgs["Favicon"], "fav")}</div>'
        + "<h3>Quando usar cada versão</h3>" + kv_table([(LK_L[r["lockup"]], POL_L[r["polarity"]], r["use_when"]) for r in b["versions"]["matrix"]], ("Assinatura", "Versão", "Quando usar")))

    # --- aplicação sobre fundos
    us = b["usage"]
    bgs = []
    for r in us["background_matrix"]:
        if r["background"] not in bgs:
            bgs.append(r["background"])
    cell = {(r["version"], r["background"]): r for r in us["background_matrix"]}
    head = "<tr><th>Versão</th>" + "".join(f"<th>{esc(x)}</th>" for x in bgs) + "</tr>"
    body_rows = ""
    for k in ("symbol", "horizontal", "vertical"):
        for pol in ("positive", "negative", "mono"):
            vkey = f"{k}.{pol}"
            tds = ""
            for bg in bgs:
                r = cell.get((vkey, bg))
                if r is None:
                    tds += '<td class="mxc"><span class="mxs">Não indicada</span></td>'
                    continue
                st = r["status"]
                if bg == "foto":
                    tds += f'<td class="mxc st-{st}"><span class="mxs">{ST_L[st]}</span></td>'
                else:
                    tds += f'<td class="mxc st-{st}">{A.matrix_cell(c, pol, flat[sig + "_" + bg])}<span class="mxs">{ST_L[st]}</span></td>'
            body_rows += f'<tr><th scope="row">{LK_L[k]}, {POL_L[pol]}</th>{tds}</tr>'
    photo = "".join(f"<li>{esc(LK_L[r['version'].split('.')[0]])}, {esc(POL_L[r['version'].split('.')[1]])}: {esc(r['note'])}</li>" for r in us["background_matrix"] if r["background"] == "foto")
    add("fundos", "Aplicação sobre fundos", p_("A matriz diz qual versão vai sobre cada fundo. Preferida é a escolha padrão. Permitida passa de 3 para 1 de contraste. Proibida não deve ser usada.")
        + f'<div class="tw"><table class="mx"><thead>{head}</thead><tbody>{body_rows}</tbody></table></div>'
        + f"<h3>Sobre foto</h3><ul>{photo}</ul><div class=\"card\"><h3>Fundo que atrapalha</h3>{p_(us['conflicting_background_rule'])}</div>")

    # --- uso
    mu = sy["misuse"]
    ms_fig = _misuse_figs(c, mu)
    mm, px = sy["min_size"]["print_mm"], sy["min_size"]["screen_px"]
    min_txt = p_("Impressão: " + str(mm) + " mm de largura. Tela: " + str(px) + " px de largura.")
    sym_small = uniq(svgs["Symbol-Positive"], "ms")
    add("uso", "Uso", '<div class="grid g2"><div class="card"><h3>Área de proteção</h3>' + p_(sy["protection_rule"]) + "</div>"
        '<div class="card"><h3>Tamanho mínimo</h3>' + min_txt
        + '<div style="width:' + str(px) + 'px;max-width:100%">' + sym_small + "</div>" + p_("Tamanho real em tela.") + "</div></div>"
        '<h3>Tamanho mínimo e proteção por versão</h3>'
        + p_("O mínimo de cada assinatura é o mínimo do símbolo multiplicado pela razão entre a largura do arquivo e a do símbolo. Abaixo do limite, use a versão de uma cor.")
        + kv_table([(LK_L[r["lockup"]], f"{r['print_mm']} mm", f"{r['screen_px']} px", f"{next(x['peak_heights'] for x in us['protection_by_version'] if x['lockup'] == r['lockup']):g} pico") for r in us["min_size_by_version"]],
                   ("Assinatura", "Impressão", "Tela", "Proteção")) + f'<div class="card"><h3>Texto ao lado da marca</h3>{p_(us["text_alignment"])}</div>'
        '<h3>Usos proibidos</h3><div class="grid g3">' + ms_fig + "</div>")

    # --- cor
    add("cor", "Cor", _colour(b, flat, fams, c))

    # --- tipografia
    add("tipografia", "Tipografia", _type(b, c))

    # --- elementos
    el = b["elements"]
    pic = ""
    for pc in el["pictograms"]:
        key = "Pictogram-" + pc["id"].capitalize()
        pic += '<div class="pi card">' + uniq(svgs[key], "pc" + pc["id"]) + "<div><b>" + esc(pc["name"]) + "</b><br>" + esc(pc["use"]) + "</div></div>"
    add("elementos", "Elementos gráficos", p_(el["origin_rule"]) + f'<div class="grid g2"><figure class="fig">{uniq(svgs["Pattern-Light"], "pl")}<figcaption>Padrão de linhas de nível, claro.</figcaption></figure>'
        f'<figure class="fig">{uniq(svgs["Pattern-Dark"], "pd")}<figcaption>Padrão de linhas de nível, escuro.</figcaption></figure></div>'
        f'<h3>Divisor</h3><div class="fig">{uniq(svgs["Divider"], "dv")}</div><h3>Pictogramas</h3><div class="grid g3">{pic}</div>'
        + _support(b))

    # --- fotografia
    ph = b["photography"]
    duo = "".join(f'<div class="stage" style="background:linear-gradient(160deg,{t("Cume_70")},{t("Cume_30")});min-height:140px;color:{t("Neblina")};font:500 14px var(--mono)">duotone {i}</div>' for i in (1, 2, 3))
    add("fotografia", "Fotografia", "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in ph["principles"]) + f"</ul><h3>Tratamento</h3>{p_(ph['treatment'])}"
        f'<div class="grid g3">{duo}</div><div class="grid g2"><div class="card"><h3>Faça</h3><ul class="do">' + "".join(f"<li>{esc(x)}</li>" for x in ph["do"]) +
        '</ul></div><div class="card"><h3>Evite</h3><ul class="dont">' + "".join(f"<li>{esc(x)}</li>" for x in ph["dont"]) + "</ul></div></div>")

    # --- movimento
    mo = b["motion"]
    dur, ease = mo["logo_animation"]["duration_ms"], mo["logo_animation"]["easing"]
    anim = uniq(svgs["Symbol-Animated"].replace("animation:draw", "animation-name:draw;x:"), "an2")
    add("movimento", "Movimento", "<ul>" + "".join("<li>" + esc(x) + "</li>" for x in mo["principles"]) + "</ul>"
        '<div class="demo drawn" id="demo" style="--len:' + str(round(A.polyline_length(c.pts))) + ";--dur:" + str(dur) + "ms;--ease:" + ease + '">'
        + anim + '<button type="button" class="btn" id="replay">Reproduzir</button></div>'
        + p_("Duração: " + str(dur) + " ms. " + mo["logo_animation"]["note"]))

    # --- voz
    vo = b["voice"]
    tr = "".join(f"<div class='card'><h3>{esc(x['name'])}</h3>{p_('É: ' + x['is'])}{p_('Não é: ' + x['is_not'])}{p_('Assim: ' + x['example_do'])}{p_('Assim não: ' + x['example_dont'])}</div>" for x in vo["traits"])
    msg = "".join(f"<tr><td>{esc(m['territory'])}</td><td>{esc(m['message'])}</td><td>{esc(m['proof'])}</td></tr>" for m in vo["messaging"])
    tone = "".join(f"<tr><td>{esc(m['channel'])}</td><td>{esc(m['tone'])}</td></tr>" for m in vo["tone_by_channel"])
    add("voz", "Voz e mensagens", f'<div class="grid g3">{tr}</div><h3>Mensagens por território</h3><div class="tw"><table><thead><tr><th>Território</th><th>Mensagem</th><th>Prova</th></tr></thead><tbody>{msg}</tbody></table></div>'
        f'<h3>Vocabulário</h3><div class="grid g2"><div class="card"><h3>Use</h3><ul class="chips">' + "".join(f"<li>{esc(x)}</li>" for x in vo["vocabulary"]["use"]) +
        '</ul></div><div class="card"><h3>Evite</h3><ul class="chips">' + "".join(f"<li>{esc(x)}</li>" for x in vo["vocabulary"]["avoid"]) + f'</ul></div></div><h3>Tom por canal</h3><div class="tw"><table><thead><tr><th>Canal</th><th>Tom</th></tr></thead><tbody>{tone}</tbody></table></div>')

    # --- aplicações
    apps = ""
    for ap in b["applications"]:
        figs = "".join(f'<figure class="fig">{uniq(svgs[n], "ap" + n[-6:].replace("-", ""))}</figure>' for n, _ in A.APP_FILES[ap["id"]])
        apps += (f'<h3>{esc(ap["name"])}</h3><div class="grid g2" style="align-items:start"><div class="grid">{figs}</div><div class="card">{p_(ap["spec"])}<ul>'
                 + "".join(f"<li>{esc(r)}</li>" for r in ap["rules"]) + "</ul></div></div>"
                 + kv_table([("Formato", ap["production"]["format"]), ("Cores", ap["production"]["colour_mode"]), ("Processo", ap["production"]["process"]),
                             ("Material", ap["production"]["material"]), ("Acabamento", ap["production"]["finishing"]), ("Escala", ap["production"]["scale"])], ("Ficha técnica", "Valor")))
    add("aplicacoes", "Aplicações", p_("Cada aplicação mostra a regra aplicada. As imagens são ilustrativas e não substituem a prova de impressão.") + apps)

    # --- tokens e arquivos
    css_tokens = "\n".join(f"  --{k.lower().replace('_', '-')}: {v};" for k, v in flat.items())
    flist = "".join(f"<tr><td><code>{esc(p)}</code></td><td>{esc(r)}</td></tr>" for p, r in files)
    add("tokens", "Tokens e arquivos", p_("Os tokens abaixo são a fonte das cores. O arquivo de tokens do pacote traz o mesmo conteúdo em CSS e JSON.")
        + f'<pre id="tk">:root {{\n{esc(css_tokens)}\n}}</pre>{copy_btn(chr(58) + "root {" + chr(10) + css_tokens + chr(10) + "}", "Copiar tokens")}'
        + p_(f"Nome dos arquivos: {sig}_Nome_V01_DDMMAA.extensão, com versão de dois dígitos e data em dia, mês e ano.")
        + f'<h3>Conteúdo do pacote</h3><div class="tw"><table><thead><tr><th>Arquivo</th><th>Função</th></tr></thead><tbody>{flist}</tbody></table></div>')

    # --- entrega
    dl = b["delivery"]
    add("entrega", "Entrega e arquivos", p_("Reproduza a marca pelos arquivos do pacote e nunca a redesenhe a partir de uma impressão.")
        + kv_table([("Formatos", ", ".join(dl["formats"])), ("Sistemas de cor", ", ".join(dl["colour_systems"])), ("Texto em curvas", dl["outlined_and_editable"]),
                    ("Área de proteção", dl["protection_marker"])], ("Item", "Situação")))

    # --- governança, faq, histórico
    g = b["governance"]
    add("governanca", "Governança", f'<dl class="defs"><div class="card"><dt>Quem aprova</dt><dd>{esc(g["owner"])}</dd></div><div class="card"><dt>Fluxo</dt><dd>{esc(g["approval_flow"])}</dd></div>'
        f'<div class="card"><dt>Revisão</dt><dd>{esc(g["review_cycle"])}</dd></div><div class="card"><dt>Contato</dt><dd>{esc(g["contact"])}</dd></div>'
        f'<div class="card"><dt>Escopo</dt><dd>{esc(g["scope"])}</dd></div><div class="card"><dt>Propriedade</dt><dd>{esc(g["ip_notice"])}</dd></div></dl>')
    add("faq", "Perguntas frequentes", "".join(f"<details><summary>{esc(x['q'])}</summary>{p_(x['a'])}</details>" for x in b["faq"]))
    cl = "".join(f"<tr><td>{esc(x['version'])}</td><td>{esc(x['date'])}</td><td>{esc(x['change'])}</td><td>{esc(x['approved_by'])}</td></tr>" for x in b["changelog"])
    add("historico", "Histórico de versões", f'<div class="tw"><table><thead><tr><th>Versão</th><th>Data</th><th>Mudança</th><th>Aprovada por</th></tr></thead><tbody>{cl}</tbody></table></div>')

    nav = "".join(f'<a href="#{cid}">{esc(title)}</a>' for cid, title, _, _ in chs)
    body_ch = "".join(chapter(i + 1, cid, title, bd, ld) for i, (cid, title, bd, ld) in enumerate(chs))
    note = ' Marca fictícia criada para o teste do processo.' if b.get("fictional") else ""
    hero = (f'<header class="hero" id="capa"><div class="sym">{uniq(svgs["Symbol-Negative"], "hero")}</div><h1>{esc(name)}</h1><p class="tag">{esc(ident["tagline"])}</p>'
            f'<p>{esc(ident["descriptor"])}. Manual da marca, versão {esc(ident["version"])}.{note}</p>'
            f'<div class="meta"><span class="badge">V{esc(ident["version"])}</span><span class="badge">{esc(ident["date"])}</span><span class="badge">Símbolo: estudo geométrico</span></div></header>')
    deck_html, _n_slides = DK.deck_markup(b, c, svgs, uniq) if ST.has(b) else ("", 0)
    deck_btn = '<button type="button" class="btn" id="deck-open">Deck</button>' if deck_html else ""
    topb = (f'<header class="top gut"><div class="in"><a class="logo" href="#capa" aria-label="{esc(name)}, início"><span class="only-light">{uniq(svgs["Horizontal-Positive"], "tl")}</span>'
            f'<span class="only-dark">{uniq(svgs["Horizontal-Negative"], "td")}</span></a><span class="sp"></span>{deck_btn}<button type="button" class="btn" id="menu" aria-expanded="false" aria-controls="toc" hidden>Capítulos</button>'
            f'<button type="button" class="btn" id="theme">Tema</button></div></header>')
    page = (f'<a class="skip" href="#conteudo">Ir para o conteúdo</a>{topb}<div class="shell gut"><nav class="toc" id="toc" aria-label="Capítulos">{nav}</nav>'
            f'<main id="conteudo">{hero}{body_ch}<footer class="col">{esc(name)} · {esc(ident["descriptor"])} · V{esc(ident["version"])} · {esc(ident["date"])}. Gerado de uma fonte única (brand-source.v1).{note}</footer></main></div>')
    fonts = "&family=".join(f["google_family"] for f in b["typography"]["fonts"])
    link = f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={fonts}&display=swap">'
    title = f"{name} Manual da Marca"
    style = '<style id="bk-css">' + css(b, flat, c) + "</style>"
    root = f'<div id="bk-root">{page}{deck_html}</div>'
    dkjs = f'<script id="dk-js">{DK.VIEW_JS}</script>' if deck_html else ""
    dked = f'<script id="dk-ed-js" data-edit-ui>{DK.edit_js(file_stem(b, "Deck-Cliente") + ".html")}</script>' if deck_html else ""
    if standalone:
        return (f'<!doctype html><html lang="{esc(ident["language"])}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{esc(title)}</title>{link}{style}</head><body>{root}<script id="bk-js">{JS}</script>{dkjs}</body></html>')
    return (f'<title>{esc(title)}</title><meta name="claude:viewport-fit-sides" content="cover">{link}{style}{root}<script id="bk-js">{JS}</script>{dkjs}<style id="ed-css" data-edit-ui>{E.edit_css()}</style><script id="ed-js" data-edit-ui>{E.edit_js(file_stem(b, "Manual-Cliente") + ".html")}</script>{dked}')


def _misuse_figs(c, misuse):
    t = c.t
    W, H = c.W, c.H
    out = []
    for i, txt in enumerate(misuse):
        k = i % 7
        base = lambda extra="", color=t("Cume_50"): (f'<polyline points="{A.polyline(c.pts, H)}" fill="none" stroke="{color}" stroke-width="{c.sw}" stroke-linecap="round" stroke-linejoin="round"{extra}/>')
        vb = f"{-30} {-60} {W + 60:.0f} {H + 120}"
        if k == 0:
            inner = f'<g transform="translate({W / 2:.1f} 50) scale(0.6 1.6) translate({-W / 2:.1f} -50)">{base()}</g>'
        elif k == 1:
            inner = f'<g transform="rotate(-24 {W / 2:.1f} 50)">{base()}</g>'
        elif k == 2:
            inner = (f'<defs><linearGradient id="mg{i}" x1="0" x2="1"><stop offset="0" stop-color="{t("Vale_50")}"/><stop offset="0.5" stop-color="{t("Cume_30")}"/><stop offset="1" stop-color="{t("Cume_70")}"/></linearGradient></defs>'
                     + base(color=f"url(#mg{i})"))
        elif k == 3:
            inner = base(color=t("Cume_50")) + base(color=t("Neblina"), extra=' transform="translate(0 0)"').replace(f'stroke-width="{c.sw}"', f'stroke-width="{c.sw * 0.55:.2f}"')
        elif k == 4:
            inner = f'<g transform="translate(9 9)">{base(color=t("Cume_30"))}</g>{base()}'
        elif k == 5:
            inner = (f'<rect x="-30" y="-60" width="{W + 60}" height="{H + 120}" fill="{t("Cume_10")}"/>'
                     f'<g transform="translate(-30 -60)">' + A.layers(c, W + 60, H + 120, 96, 6, 0.55, 1.6, t("Cume_10"), t("Cume_30"), 0.55) + "</g>"
                     + base(color=t("Cume_50")))
        else:
            inner = f'<polygon points="{A.polyline(c.pts, H)}" fill="{t("Cume_50")}" stroke="{t("Cume_50")}" stroke-width="{c.sw}" stroke-linejoin="round"/>'
        strike = f'<line x1="-24" y1="{H + 52}" x2="{W + 24}" y2="-52" stroke="var(--fg)" stroke-width="5" stroke-linecap="round"/>'
        out.append(f'<figure><div class="stage s-pos" style="min-height:130px"><svg viewBox="{vb}" role="img" aria-label="Uso proibido: {esc(txt)}" style="max-height:130px">{inner}{strike}</svg></div><figcaption>{esc(txt)}</figcaption></figure>')
    return "".join(out)


def _name_in_text(b):
    nt = b["voice"]["name_in_text"]
    return (f'<div class="card"><h3>Como escrever o nome em texto</h3>{p_("Classe: " + nt["class"] + ".")}{p_(nt["case"])}<ul class="dont">'
            + "".join(f"<li>{esc(x)}</li>" for x in nt["never"]) + "</ul></div>")


def _support(b):
    sr, sg = b["elements"]["support_rules"], b["elements"]["symbol_as_graphic"]
    return ("<h3>Regras de apoio gráfico</h3>" + kv_table([("Cores permitidas", ", ".join(sr["colours_allowed"])), ("Como máscara de foto", sr["as_mask"]),
            ("Como gabarito de corte", sr["as_cut_template"]), ("Exceção à área de proteção", sr["protection_exception"])], ("Regra", "Valor"))
            + "<h3>Símbolo como grafismo</h3>" + kv_table([("Posições", ", ".join(sg["positions"])), ("Cores", ", ".join(sg["colour_options"])), ("Onde", sg["where"])], ("Regra", "Valor")))


def _colour(b, flat, fams, c):
    t = c.t
    col = b["colour"]
    sig = b["identity"]["sigla"]
    out = []
    for f in fams:
        cells = ""
        for s, d in f["steps"].items():
            hx = d["hex"]
            fg = t("Tinta") if contrast(hx, t("Tinta")) >= contrast(hx, t("Branco")) else t("Branco")
            rgb = hex_rgb(hx)
            cells += (f'<div class="sw" style="background:{hx};color:{fg}"><div><b>{s}</b><br>{d["token"]}<br>{hx}<br>RGB {rgb[0]}, {rgb[1]}, {rgb[2]}<br>CMYK≈ {", ".join(map(str, cmyk_approx(hx)))}'
                      f'<br>Branco {contrast(hx, t("Branco")):.1f}:1</div>{copy_btn(hx)}</div>')
        out.append(f'<h3>{esc(f["pt_name"])} {esc(f["universe"])}</h3>{p_(f["role"] + " " + f["meaning"])}<div class="ramp">{cells}</div>')
    neu = ""
    for n in col["neutrals"]:
        fg = t("Tinta") if contrast(n["hex"], t("Tinta")) >= contrast(n["hex"], t("Branco")) else t("Branco")
        neu += f'<div class="sw" style="background:{n["hex"]};color:{fg}"><div><b>{esc(n["name"])}</b><br>{n["token"]}<br>{n["hex"].upper()}<br>{esc(n["role"])}</div>{copy_btn(n["hex"].upper())}</div>'
    out.append(f'<h3>Neutros</h3><div class="ramp">{neu}</div>')
    for side, lab in (("light_bg", "Fundo claro"), ("dark_bg", "Fundo escuro")):
        segs = "".join(
            f'<span style="width:{pc}%;background:{flat[tk]};color:{t("Tinta") if contrast(flat[tk], t("Tinta")) >= contrast(flat[tk], t("Branco")) else t("Branco")}">{pc}%</span>'
            for tk, pc in col["ratio"][side])
        legend = ", ".join(f"{tk} {pc}%" for tk, pc in col["ratio"][side])
        out.append(f'<h3>Proporção, {lab.lower()}</h3><div class="bar" role="img" aria-label="Proporção de uso em {lab.lower()}: {esc(legend)}">{segs}</div>{p_(legend)}')
    rows = ""
    for pr in col["pairs"]:
        r = contrast(flat[pr["fg"]], flat[pr["bg"]])
        need = {"AA": 4.5, "AA_large": 3.0, "AAA": 7.0}[pr["declared"]]
        rows += (f'<tr><td>{pr["fg"]}</td><td>{pr["bg"]}</td><td>{r:.2f} : 1</td><td>{pr["declared"].replace("_", " ")}</td><td>{"Passa" if r >= need else "Falha"}</td></tr>')
    gd = col["gradient"]
    out.append(f'<h3>Pares de contraste</h3><div class="tw"><table><thead><tr><th>Texto</th><th>Fundo</th><th>Razão</th><th>Nível declarado</th><th>Resultado</th></tr></thead><tbody>{rows}</tbody></table></div>'
               f'<h3>Gradiente</h3><div class="grad" role="img" aria-label="Gradiente de {gd["from"]} para {gd["to"]} a {gd["angle"]} graus" style="background:linear-gradient({gd["angle"]}deg,{flat[gd["from"]]},{flat[gd["to"]]})"></div>'
               f'{p_(gd["rule"])}<div class="card"><h3>Impressão</h3>{p_(col["print_note"])}{p_("Tons de marrom, dourado e folha metálica ficam fora da marca.")}{p_(col["large_area_rule"])}</div>'
               + "<h3>Cor especial</h3>" + kv_table([(r["family"], r["system"], r["code"] if r["status"] == "matched" else "pendente de prova na gráfica") for r in col["spot_refs"]], ("Família", "Sistema", "Código")))
    return "".join(out)


def _type(b, c):
    ty = b["typography"]
    cards = ""
    for f in ty["fonts"]:
        fam = f"'{f['name']}', {f['fallback']}"
        cards += (f'<div class="card"><p class="eyebrow">{esc(f["role"])}</p><div style="font:400 64px/1.05 {esc(fam)};word-break:break-word">Aa</div><h3>{esc(f["name"])}</h3>'
                  f'{p_(f["usage"])}{p_("Licença: " + f["license"])}{p_("Substituto: " + f["fallback"])}'
                  f'<div style="font:400 17px/1.45 {esc(fam)};overflow-wrap:anywhere">ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>abcdefghijklmnopqrstuvwxyz<br>0123456789</div></div>')
    roles = {f["role"]: f for f in ty["fonts"]}
    rows = ""
    for s in ty["scale"]:
        f = roles[s["font_role"]]
        fam = f"'{f['name']}', {f['fallback']}"
        label = s["level"]
        sample = ty["specimen_text"] if s["size_px"] >= 28 else "Chocolate de altitude em lotes pequenos."
        rows += (f'<tr><td>{esc(label)}</td><td>{s["size_px"]} px, {s["line_height"]}, {s["weight"]}</td><td><div style="font:{s["weight"]} min({s["size_px"]}px,7vw)/{s["line_height"]} {esc(fam)};letter-spacing:{s["tracking"]}">{esc(sample)}</div></td></tr>')
    return (f'<div class="grid g3">{cards}</div><h3>Escala</h3><div class="tw"><table><thead><tr><th>Nível</th><th>Tamanho, entrelinha, peso</th><th>Amostra</th></tr></thead><tbody>{rows}</tbody></table></div>'
            + p_(ty["note"]) + "<h3>Onde cada fonte não entra</h3>" + kv_table([(r["font_role"], r["rule"]) for r in ty["restrictions"]], ("Papel", "Restrição")))


def build_deck(b, flat, fams, c, svgs):
    """A single-file deck: the same slides as the manual's deck, open at once, with arrow keys and print to PDF."""
    ident = b["identity"]
    deck, _ = DK.deck_markup(b, c, svgs, uniq, standalone=True)
    fonts = "&family=".join(f["google_family"] for f in b["typography"]["fonts"])
    link = f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={fonts}&display=swap">'
    style = '<style id="bk-css">' + css(b, flat, c) + "</style>"
    return (f'<!doctype html><html lang="{esc(ident["language"])}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(ident["name"])} Deck</title>{link}{style}</head><body class="dk-standalone"><div id="bk-root">{deck}</div><script id="dk-js">{DK.VIEW_JS}</script></body></html>')


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
