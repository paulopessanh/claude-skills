#!/usr/bin/env python3
"""_ecodeck.py — the strategic deck, a 16:9 slide deck generated from the same source as the manual.

A library for ecosystem_builder.py. The page grammar follows the strategic manual studied in
brand-system/references/strategic_page_grammar.md: a running header, a tracked eyebrow, a title in two weights, one dark
module per slide, a 'Por trás do termo' footnote, and a running footer with the author, the year and a page number.
Page numbers are unique and in order. The contents slide points to the real page of each part. The year is one value for
the whole deck. The platform slide is derived from the source and never written by hand. A source without `strategy`
builds no deck. Running this file only prints this text.

Stdlib only. Deterministic.
"""

import html
import sys

import _ecostrat as ST

esc = html.escape

CSS = """
#deck{position:fixed;inset:0;z-index:60;background:var(--fg);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:12px;color:var(--bg)}
#deck[hidden]{display:none}
body.dk-open{overflow:hidden}
#deck .dk-stage{width:min(100%,calc((100vh - 96px) * 16 / 9));flex:none}
#deck .dk-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:center;font:500 14px var(--body)}
#deck .dk-bar .btn{background:var(--surface);color:var(--fg)}
#deck .dk-bar .btn[hidden]{display:none}
#deck .dk-bar .btn[aria-pressed="true"]{outline:2px solid var(--accent);outline-offset:2px}
#deck .dk-bar .dk-c{min-width:64px;text-align:center;color:var(--bg)}
.sl{aspect-ratio:16/9;container-type:inline-size;background:var(--surface);color:var(--fg);border-radius:8px;overflow:hidden;position:relative;display:flex;flex-direction:column;padding:4cqw 5cqw 3cqw;font:400 1.75cqw/1.4 var(--body)}
.sl[hidden]{display:none}
.sl.dkl{background:var(--hero);color:var(--hero-fg)}
.sl header,.sl footer{display:flex;justify-content:space-between;gap:2cqw;font:600 .95cqw var(--body);letter-spacing:.14em;text-transform:uppercase;opacity:.75}
.sl footer{margin-top:auto;padding-top:1.4cqw}
.sl .wm{position:absolute;right:4cqw;top:5cqw;font:700 11cqw/1 var(--display);opacity:.06;pointer-events:none}
.sl .eb{margin:2.4cqw 0 .4cqw;font:700 1cqw var(--body);letter-spacing:.18em;text-transform:uppercase;opacity:.8}
.sl h2{margin:0 0 1.6cqw;font:400 3.5cqw/1.12 var(--display);letter-spacing:-.01em}
.sl h2 b{font-weight:700}
.sl .bd{flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column;gap:1.2cqw;justify-content:flex-start}
.sl .bd p{margin:0 0 .8cqw}
.sl .cols{display:grid;gap:2cqw;border-top:.2cqw solid currentColor;padding-top:1.4cqw}
.sl .c2{grid-template-columns:repeat(2,1fr)}.sl .c3{grid-template-columns:repeat(3,1fr)}.sl .c4{grid-template-columns:repeat(4,1fr)}.sl .c5{grid-template-columns:repeat(5,1fr)}.sl .c6{grid-template-columns:repeat(6,1fr)}
.sl .cols h3,.sl .bd h3{margin:0 0 .4cqw;font:700 1.9cqw/1.25 var(--body)}
.sl .cols small,.sl .lb{display:block;font:700 .9cqw var(--body);letter-spacing:.14em;text-transform:uppercase;opacity:.65;margin:.8cqw 0 .2cqw}
.sl .dm{background:var(--hero);color:var(--hero-fg);border-radius:.8cqw;padding:1.4cqw 1.6cqw}
.sl.dkl .dm{background:var(--surface);color:var(--fg)}
.sl .dm .lb,.sl .dm h3,.sl .dm p{color:inherit}
.sl table{width:100%;border-collapse:collapse;font-size:1.55cqw}
.sl th{font:700 .9cqw var(--body);letter-spacing:.14em;text-transform:uppercase;text-align:left;opacity:.65;padding:.5cqw .8cqw;border-bottom:.15cqw solid currentColor}
.sl td{padding:.6cqw .8cqw;border-bottom:1px solid var(--line);vertical-align:top}
.sl.dkl td{border-color:var(--hero-line)}
.sl .big{font:700 7cqw/1.02 var(--display);letter-spacing:-.02em;margin:3cqw 0 1.4cqw}
.sl .lead{font:300 2.2cqw/1.4 var(--body);max-width:60cqw;color:inherit}
.sl .q{font:700 2.6cqw/1.3 var(--body);border-left:.5cqw solid currentColor;padding-left:2cqw;margin:1cqw 0}
.sl .tn{margin:1.2cqw 0 0;padding-top:.8cqw;border-top:.15cqw solid currentColor;font-size:1.4cqw;opacity:.85}
.sl .m2{display:grid;grid-template-columns:1fr 1fr;gap:1cqw}.sl .m2>div{border:.15cqw solid currentColor;border-radius:.6cqw;padding:1cqw 1.2cqw}
.sl .m2>div.own{background:var(--hero);color:var(--hero-fg)}
.sl .pb{display:grid;grid-template-columns:20cqw 1fr 4cqw;gap:1cqw;align-items:center;margin:.5cqw 0}
.sl .pb .tr{height:1.2cqw;background:var(--soft);border-radius:.6cqw;overflow:hidden}.sl .pb .tr i{display:block;height:100%;background:var(--accent)}
.sl.dkl .pb .tr{background:var(--hero-line)}
.sl .rl{display:grid;grid-template-columns:11cqw 1fr 11cqw;gap:1cqw;align-items:center;margin:.2cqw 0;font-size:1.5cqw}
.sl .rl .tk{position:relative;height:.15cqw;background:currentColor;opacity:.5}.sl .rl .tk i{position:absolute;top:-.55cqw;width:1.2cqw;height:1.2cqw;border-radius:50%;background:currentColor;transform:translateX(-50%)}
.sl .rl .r{text-align:right}.sl .rl small{grid-column:1/-1;text-align:center;font-size:1.1cqw;margin-top:-.4cqw}
.sl .plat{display:grid;grid-template-columns:repeat(3,1fr);gap:0 2cqw;border-top:.2cqw solid currentColor;margin:0}
.sl .plat>div{padding:.8cqw 0}.sl .plat dt{font:700 .85cqw var(--body);letter-spacing:.14em;text-transform:uppercase;opacity:.65}.sl .plat dd{margin:.2cqw 0 0;font-weight:600;font-size:1.55cqw}
.sl .dsw{display:flex;gap:1cqw;flex-wrap:wrap}.sl .dsw div{width:11cqw;border-radius:.6cqw;padding:.8cqw;font:600 1cqw var(--body);min-height:8cqw;display:flex;flex-direction:column;justify-content:flex-end}
.sl .sig{display:flex;gap:2cqw;align-items:center}.sl .sig svg{height:12cqw;width:auto;max-width:44cqw}
.sl .tc{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0 3cqw;font-size:1.3cqw}.sl .tc h3{font:700 1.5cqw var(--body);margin:1cqw 0 .3cqw;border-bottom:.15cqw solid currentColor}
.sl .tc a{display:flex;justify-content:space-between;gap:1cqw;padding:.25cqw 0;color:inherit;text-decoration:none;cursor:pointer}
.sl .tc a b{font-variant-numeric:tabular-nums}
.sl .num{font:700 12cqw/1 var(--display)}.sl .of{border-top:.15cqw solid currentColor;display:inline-block;padding-top:.5cqw;font:700 1cqw var(--body);letter-spacing:.14em;text-transform:uppercase}
.sl .ol{list-style:none;margin:0;padding:0;font-size:1.8cqw}.sl .ol li{padding:.5cqw 0;border-bottom:1px solid var(--hero-line)}
.editing-deck .sl [data-dk]{outline:1px dashed currentColor;outline-offset:2px;cursor:text}
.editing-deck .sl [data-dk]:focus{outline:2px solid var(--accent)}
.editing-deck .sl [data-dk].mod{background:var(--soft);color:var(--fg)}
@media print{
 @page{size:1280px 720px;margin:0}
 body.dk-print #bk-root>*:not(#deck),body.dk-print .ed-bar,body.dk-print .ed-pop,body.dk-print .ed-toast{display:none!important}
 body.dk-print #deck{position:static;background:none;padding:0;display:block}
 body.dk-print #deck .dk-bar{display:none}
 body.dk-print #deck .dk-stage{width:1280px}
 body.dk-print .sl,body.dk-print .sl[hidden]{display:flex;width:1280px;height:720px;aspect-ratio:auto;border-radius:0;break-after:page;font-size:25px;-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
"""

VIEW_JS = """
(function(){
var dk=document.getElementById('deck');if(!dk)return;
var sl=[].slice.call(dk.querySelectorAll('.sl')),i=0,cnt=document.getElementById('dk-c');
function fit(s){var bd=s.querySelector('.bd');if(!bd)return;bd.style.zoom='';var z=1;while(bd.scrollHeight>bd.clientHeight+1&&z>0.55){z-=0.05;bd.style.zoom=String(z.toFixed(2))}}
function show(n){i=Math.max(0,Math.min(sl.length-1,n));sl.forEach(function(s,k){s.hidden=k!==i});fit(sl[i]);if(cnt)cnt.textContent=(i+1)+' / '+sl.length;try{sessionStorage.setItem('dk-i',String(i))}catch(e){}}
function open(){dk.hidden=false;document.body.classList.add('dk-open');var v=0;try{v=parseInt(sessionStorage.getItem('dk-i')||'0',10)||0}catch(e){}show(v);var b=document.getElementById('dk-next');if(b)b.focus()}
function close(){dk.hidden=true;document.body.classList.remove('dk-open');var o=document.getElementById('deck-open');if(o)o.focus()}
function print(){document.body.classList.add('dk-print');sl.forEach(function(s){s.hidden=false;fit(s)});setTimeout(function(){window.print()},80)}
window.addEventListener('afterprint',function(){document.body.classList.remove('dk-print');show(i)});
function on(id,fn){var e=document.getElementById(id);if(e)e.addEventListener('click',fn)}
on('deck-open',open);on('dk-close',close);on('dk-prev',function(){show(i-1)});on('dk-next',function(){show(i+1)});on('dk-print',print);
dk.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('[data-to]');if(a){e.preventDefault();var t=document.getElementById(a.getAttribute('data-to'));if(t)show(sl.indexOf(t))}});
document.addEventListener('keydown',function(e){if(dk.hidden)return;if(document.documentElement.classList.contains('editing-deck')&&e.target.hasAttribute&&e.target.hasAttribute('data-dk'))return;
 var k=e.key;if(k==='ArrowRight'||k==='PageDown'||k===' '){e.preventDefault();show(i+1)}else if(k==='ArrowLeft'||k==='PageUp'){e.preventDefault();show(i-1)}else if(k==='Home'){show(0)}else if(k==='End'){show(sl.length-1)}else if(k==='Escape'&&document.getElementById('dk-close')){close()}});
if(document.body.classList.contains('dk-standalone')){dk.hidden=false;document.body.classList.add('dk-open');show(0)}else{show(0);dk.hidden=true}
})();
"""

EDIT_JS = r"""
(function(){
var FNAME='__FNAME__',SEL='h2 .lt,h2 b,.bd p,.bd li,.bd td,.bd h3,.bd small,.q,.lead,.big',D={edits:{},saved:{},ns:null,dl:null,can:false,editing:false,F:[],key:'dk-draft:'+FNAME};
var dk=document.getElementById('deck');if(!dk)return;
function hash(s){var h=2166136261;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return (h>>>0).toString(36)}
function $(id){return document.getElementById(id)}
function fields(){var out=[];[].forEach.call(dk.querySelectorAll('.sl'),function(s){if(s.hasAttribute('data-lock'))return;var n=0;[].forEach.call(s.querySelectorAll(SEL),function(el){if(el.children.length||el.closest('.tc,.plat,.dsw'))return;var t=el.textContent;if(!t.trim())return;out.push({id:s.id+'.'+(n++),el:el,orig:t,h:hash(t)})})});return out}
D.F=fields();
function setText(f,t){f.el.textContent=t;f.el.classList.toggle('mod',t!==f.orig)}
function apply(m){D.F.forEach(function(f){var e=m[f.id];if(e&&e.was===f.h)setText(f,e.text);else setText(f,f.orig)})}
function count(){var n=0;Object.keys(D.edits).forEach(function(k){if(!D.saved[k]||D.saved[k].text!==D.edits[k].text)n++});Object.keys(D.saved).forEach(function(k){if(!D.edits[k])n++});return n}
function toast(m){var t=$('ed-toast');if(!t){t=document.createElement('div');t.className='ed-toast';t.id='ed-toast';t.setAttribute('role','status');t.setAttribute('data-edit-ui','');document.body.appendChild(t)}t.textContent=m;t.hidden=false;clearTimeout(toast.t);toast.t=setTimeout(function(){t.hidden=true},3200)}
function ui(){var n=count(),s=$('dk-save'),st=$('dk-st');if(s)s.disabled=!n;if(st)st.textContent=n?n+(n===1?' alteração não salva':' alterações não salvas'):(Object.keys(D.saved).length?'Tudo salvo':'')}
function setEditing(on){D.editing=on;document.documentElement.classList.toggle('editing-deck',on);var b=$('dk-edit');b.setAttribute('aria-pressed',String(on));b.textContent=on?'Concluir edição':'Editar slides';
 D.F.forEach(function(f){if(on){f.el.setAttribute('contenteditable','plaintext-only');if(f.el.contentEditable!=='plaintext-only')f.el.setAttribute('contenteditable','true');f.el.setAttribute('data-dk','')}else{f.el.removeAttribute('contenteditable');f.el.removeAttribute('data-dk')}})}
document.addEventListener('input',function(e){var el=e.target;if(!D.editing||!el.hasAttribute||!el.hasAttribute('data-dk'))return;var f=null;for(var i=0;i<D.F.length;i++)if(D.F[i].el===el){f=D.F[i];break}if(!f)return;
 var t=el.textContent.replace(/\s+/g,' ').trim();if(t===f.orig)delete D.edits[f.id];else D.edits[f.id]={was:f.h,text:t};el.classList.toggle('mod',t!==f.orig);try{if(count())localStorage.setItem(D.key,JSON.stringify(D.edits));else localStorage.removeItem(D.key)}catch(x){}ui()});
document.addEventListener('keydown',function(e){if(D.editing&&e.key==='Enter'&&e.target.hasAttribute&&e.target.hasAttribute('data-dk')){e.preventDefault();e.target.blur()}});
function save(){if(!D.ns||!count())return;var body=JSON.stringify({v:1,saved:new Date().toISOString(),edits:D.edits},null,1);$('dk-save').disabled=true;
 D.ns.publish({'deck.json':{content:body,contentType:'application/json'}}).then(function(){D.saved=JSON.parse(JSON.stringify(D.edits));try{localStorage.removeItem(D.key)}catch(e){}ui();toast('Deck salvo. Quem abrir o link vê esta versão.')},
  function(err){var c=err&&err.code;ui();toast(c==='conflict'?'Outra pessoa salvou antes. A página vai recarregar e seu rascunho fica guardado.':c==='not_writer'||c==='not_granted'?'Você só pode ler esta página.':'Não foi possível salvar. Tente de novo.')})}
function deckHtml(){var root=dk.cloneNode(true);root.removeAttribute('hidden');
 [].forEach.call(root.querySelectorAll('[data-edit-ui],.dk-bar'),function(n){n.remove()});
 [].forEach.call(root.querySelectorAll('[contenteditable],[data-dk],.mod'),function(n){n.removeAttribute('contenteditable');n.removeAttribute('data-dk');n.classList.remove('mod')});
 [].forEach.call(root.querySelectorAll('.sl'),function(n,k){if(k)n.setAttribute('hidden','')});
 var bar='<div class="dk-bar"><button type="button" class="btn" id="dk-prev">Anterior</button><span class="dk-c" id="dk-c"></span><button type="button" class="btn" id="dk-next">Próximo</button><button type="button" class="btn" id="dk-print">Imprimir ou PDF</button></div>';
 var st=root.querySelector('.dk-stage');if(st)st.insertAdjacentHTML('afterend',bar);
 var link=document.querySelector('link[href*="fonts.googleapis.com/css2"]');var css=$('bk-css'),js=$('dk-js');var lang=document.documentElement.getAttribute('lang')||'pt-BR';
 return '<!doctype html><html lang="'+lang+'"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>'+document.title.replace(/</g,'&lt;')+' Deck</title>'
  +'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'+(link?link.outerHTML:'')+'<style id="bk-css">'+css.textContent+'</style></head><body class="dk-standalone"><div id="bk-root">'+root.outerHTML+'</div><script id="dk-js">'+js.textContent+'<\/script></body></html>'}
function download(){if(!D.dl){toast('Download indisponível aqui.');return}D.dl.save({filename:FNAME,data:deckHtml()}).then(function(){toast('Deck salvo no seu computador. Abra no navegador, avance com as setas e use Imprimir para o PDF.')},function(e){if(!e||e.code!=='declined')toast('Não foi possível baixar.')})}
function wire(){var e=$('dk-edit'),s=$('dk-save'),d=$('dk-dl');
 if(D.dl&&d){d.hidden=false;d.addEventListener('click',download)}
 if(D.can&&e){e.hidden=false;s.hidden=false;e.addEventListener('click',function(){setEditing(!D.editing)});s.addEventListener('click',save);var n=$('dk-note');if(n)n.hidden=false;ui()}}
function loadSaved(){return fetch('deck.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():null}).then(function(j){if(j&&j.edits){D.saved=j.edits;D.edits=JSON.parse(JSON.stringify(j.edits));apply(D.edits)}}).catch(function(){})}
loadSaved().then(function(){var c=window.claude;if(!c||!c.use)return;
 Promise.all([c.use('artifact'),c.use('user'),c.use('downloads')]).then(function(r){D.ns=r[0];D.dl=r[2];var u=r[1];D.can=!!(D.ns&&u&&u.canEdit&&u.canEdit());
  if(D.can){try{var d=localStorage.getItem(D.key);if(d){var m=JSON.parse(d);if(m&&typeof m==='object'){D.edits=m;apply(m)}}}catch(e){}}
  wire()}).catch(function(){})});
})();
"""


def edit_js(file_name):
    return EDIT_JS.replace("__FNAME__", file_name)


def _t(x):
    return esc(str(x))


def _two(light, bold):
    return f'<span class="lt">{_t(light)} </span><b>{_t(bold)}</b>'


def _cols(items, n):
    return f'<div class="cols c{n}">' + "".join(f"<div><h3>{_t(a)}</h3><p>{_t(t)}</p></div>" for a, t in items) + "</div>"


def _tbl(head, rows):
    return ("<table><thead><tr>" + "".join(f"<th>{_t(h)}</th>" for h in head) + "</tr></thead><tbody>"
            + "".join("<tr>" + "".join(f"<td>{_t(x)}</td>" for x in r) + "</tr>" for r in rows) + "</tbody></table>")


def _bars(rows, unit=""):
    top = max((v for _, v in rows), default=1) or 1
    return "".join(f'<div class="pb"><span>{_t(l)}</span><span class="tr"><i style="width:{round(100 * v / top)}%"></i></span><b>{_t(v)}{unit}</b></div>' for l, v in rows)


def _note(b, *terms):
    notes = {n["term"]: n["plain"] for n in b["strategy"].get("term_notes", [])}
    rows = [(t, notes[t]) for t in terms if t in notes]
    return "" if not rows else '<p class="tn"><b>Por trás do termo.</b> ' + " ".join(f"<b>{_t(t)}</b>: {_t(x)}" for t, x in rows) + "</p>"


def year_of(b):
    return str(b["identity"]["date"])[:4]


def slide_list(b, c, svgs, uniq):
    """Return the slides as dicts, in order: kind, ch (0 opening, 1 to 4 chapters, 5 closing), eyebrow, title, body, dark, lock, toc, note."""
    s = b["strategy"]
    pu, cn, ps = b["purpose"], b["concept"], b["personality"]
    out = []

    def add(ch, eyebrow, title, body, dark=False, lock=False, toc=None, note="", kind="s", wm=""):
        out.append({"kind": kind, "ch": ch, "eb": eyebrow, "title": title, "body": body, "dark": dark, "lock": lock, "toc": toc, "note": note, "wm": wm})

    w = s.get("welcome", {})
    ident = b["identity"]
    # ---- abertura
    out.append({"kind": "cover", "ch": 0, "eb": "Manual da marca", "title": ident["name"], "dark": True, "lock": True, "toc": None, "note": "", "wm": "",
                "body": (f'<p class="lead">{_t(ident["tagline"])}</p><div class="cols c3"><div><small>Preparado para</small><p>{_t(w.get("addressee", ident["owner"]))}</p></div>'
                         f'<div><small>Estratégia</small><p>{_t(w.get("signed_by", ident["name"]))}</p></div><div><small>Data</small><p>{_t(ident["date"])}</p></div></div>')})
    if w:
        add(0, "Contracapa", _two("Bem-vindo", "a este guia."), f'<p class="lead">{_t(w["text"])}</p><p><b>{_t(w["signed_by"])}</b></p>', toc="Boas-vindas")
    out.append({"kind": "toc", "ch": 0, "eb": "Sumário", "title": _two("O que você vai", "encontrar aqui."), "body": "", "dark": False, "lock": True, "toc": None, "note": "", "wm": ""})
    add(0, "Introdução", _two("Uma pergunta guiou", "todo o trabalho."), f'<p class="q">{_t(s["guiding_question"])}</p>', toc="Uma pergunta que guiou tudo", note=_note(b, "Posicionamento"))
    m = s["method"]
    ev = "".join(f'<div><h3>{_t(e["count"])}</h3><p>{_t(e["kind"])}: {_t(e["note"])}</p></div>' for e in s["evidence_base"])
    add(0, "Como o material foi construído", _two("O método", m["name"] + "."), _cols([(p["name"], p["question"]) for p in m["pillars"]], min(4, len(m["pillars"]))) + f'<p>{_t(m["rule"])}</p><div class="cols c{min(4, len(s["evidence_base"]))}">{ev}</div>', toc="Como o material foi construído")
    # ---- 1 diagnóstico
    opener = lambda n, name, sub, items: out.append({"kind": "open", "ch": n, "eb": sub, "title": name, "dark": True, "lock": True, "toc": None, "note": "", "wm": "",
                                                       "body": '<ol class="ol">' + "".join(f"<li>{_t(x)}</li>" for x in items) + "</ol>", "num": f"{n:02d}"})
    d_items = ["Leitura por lente", "Metas e papel da marca", "Pontos de tensão", "Consumidor ideal e personas", "Concorrência e território", "Arquétipo e universo"] + (["Pesquisa de percepção"] if s.get("perception") else [])
    opener(1, "Diagnóstico", "O que é verdade hoje", d_items)
    add(1, "Leitura por lente", _two("O que achamos e", "o que significa."), _cols([(r["pillar"], r["found"] + " " + r["meaning"]) for r in s["reading"]], 2), toc="Leitura por lente")
    if s.get("premises"):
        add(1, "Premissas do negócio", _two("As verdades que a marca", "não pode contrariar."), _cols([(x["title"], x["text"]) for x in s["premises"][:6]], 3), toc="Premissas")
    g = s["goals"]
    add(1, "Metas e papel da marca", _two("O que o negócio quer e", "o papel da marca."), _cols([(f'{x["horizon"]}: {x["business_goal"]}', "Papel da marca: " + x["brand_role"]) for x in g], min(4, len(g)))
        + f'<div class="dm"><span class="lb">Nosso olhar crítico</span><p>{_t(s["critical_view"])}</p></div>', toc="Metas e papel da marca")
    add(1, "Pontos de tensão", _two("Cada tensão fecha com", "uma decisão."), _tbl(("Um lado", "Outro lado", "Decisão"), [(t["side_a"], t["side_b"], t["decision"]) for t in s["tensions"]]), toc="Pontos de tensão")
    for oc in s.get("owner_corrections", [])[:1]:
        add(1, "Onde a evidência corrige", _two("A leitura da marca", "e a evidência."), _cols([("Antes", oc["belief"]), ("Evidência", oc["evidence"]), ("Decisão", oc["decision"])], 3))
    add(1, "Consumidor ideal", _two("Quem mais", "combina com a marca."), f'<p class="lead">{_t(s["icp"])}</p><div class="dm"><span class="lb">O achado que muda o jogo</span><p>{_t(s["icp_insight"])}</p></div>', toc="Consumidor ideal", note=_note(b))
    pe = b["audience"]["personas"]
    pc = "".join(f'<div{" class=dm" if x.get("highest_value") else ""}><h3>{_t(x["name"])}</h3><p>{_t(x["who"])}</p><span class="lb">Quer</span><p>{_t(x["needs"])}</p><span class="lb">O que trava</span><p>{_t(x["blocker"])}</p><span class="lb">O que precisa ouvir</span><p><b>{_t(x["needs_to_hear"])}</b></p></div>' for x in pe)
    add(1, "Personas", _two(f"{len(pe)} rostos,", "uma mesma jornada."), f'<div class="cols c{min(4, len(pe))}">{pc}</div>', toc="Personas")
    if s.get("non_clients"):
        add(1, "Quem não é cliente", _two("O filtro é de comportamento,", "nunca de origem."), '<div class="cols c3">' + "".join(f"<div><p><b>Não: {_t(x)}</b></p></div>" for x in s["non_clients"][:3]) + f'</div><p>{_t(s.get("non_client_rule", ""))}</p>')
    add(1, "Concorrência", _two("Ninguém ocupa o lugar de", "quem faz e explica."), _tbl(("Tipo", "Faz bem", "Falha em", "A marca faz diferente"), [(x["type"], x["does_well"], x["fails_at"], x["we_differ"]) for x in s["competition"]]), toc="Concorrência e território")
    tm = s.get("territory_map")
    if tm:
        add(1, "Mapa de território", _two("O quadrante vazio", "é o da marca."), f'<p>Eixos: {_t(tm["y_axis"])} e {_t(tm["x_axis"])}.</p><div class="m2">' + "".join(
            f'<div{" class=own" if q["name"] == tm["own"] else ""}><h3>{_t(q["name"])}</h3><p>{_t(", ".join(q["brands"]))}</p></div>' for q in tm["quadrants"]) + "</div>")
    u = s.get("universe")
    if u:
        add(1, "Universo da marca", _two("Sentir a marca antes de", "entender o que ela vende."), _cols([("Atmosfera", u["atmosphere"]), ("Linguagem", u["language"]), ("Postura", u["posture"]), ("Estética visual", u["aesthetics"]), ("Presença digital", u["digital"]), ("O que não cabe", u["not_fit"])], 3), toc="Universo da marca")
    a = ps["archetype"]
    add(1, "Arquétipo", _two(f'{a["primary"]} e {a["secondary"]}', f'formam {a["intersection_name"].lower()}.'), _tbl(("", f'Principal: {a["primary"]}', f'Secundário: {a["secondary"]}'), [("De onde veio", a["origin"], ""), ("O que traz", a["brings"], ""), ("A sombra", a["shadow"], ""), ("Quem equilibra", a["balanced_by"], "")])
        + f'<p><b>Entra como tempero.</b> {_t(a["seasoning"])}</p>', toc="Arquétipo", note=_note(b, "Arquétipo", "Sombra"))
    pcn = s.get("perception")
    if pcn:
        add(1, "Pesquisa de percepção", _two("O propósito", "já chegou nas pessoas."), _bars([(x["label"], x["count"]) for x in pcn["purpose_answers"]]) + f'<p>Respostas válidas: {_t(pcn["n"])}. {_t(pcn["sample_note"])}</p>', toc="Pesquisa de percepção")
        add(1, "Pesquisa de percepção", _two("Como a veem hoje,", "o que pedem ao futuro."), '<div class="cols c2"><div><span class="lb">Hoje</span>' + _bars([(x["trait"], x["count"]) for x in pcn["traits_today"]]) + '</div><div><span class="lb">No futuro</span>'
            + _bars([(x["trait"], x["count"]) for x in pcn["traits_future"]]) + f'</div></div><div class="dm"><span class="lb">Leitura</span><p>{_t(pcn["reading"])}</p></div>')
    # ---- 2 viradas
    opener(2, "Viradas de chave", "Leituras que cruzam o que a marca diz com o que as evidências mostram", [t["title"] for t in s["turns"]] + ["Síntese estratégica"])
    n = len(s["turns"])
    for k, t in enumerate(s["turns"], 1):
        out.append({"kind": "turn", "ch": 2, "eb": "", "title": f'<span class="lt">{_t(t["title"])}</span>', "body": f'<p class="lead">{_t(t["text"])}</p>', "dark": k % 2 == 1, "lock": False,
                    "toc": (f"As {n} viradas de chave" if k == 1 else None), "note": "", "wm": "", "num": f"{k:02d}", "of": f"{k} de {n}"})
    sy = s["synthesis"]
    add(2, "Síntese estratégica", _two("Todo o estudo chega", "a uma conclusão."), _cols([("Cenário", sy["scenario"]), ("Problema", sy["problem"]), ("Oportunidade", sy["opportunity"]), ("Território", sy["territory"])], 4)
        + f'<span class="lb">Percepção desejada</span><p class="q">{_t(sy["desired_perception"])}</p>', toc="Síntese estratégica", note=_note(b, "Território"))
    # ---- 3 direção
    opener(3, "Direção estratégica", "O que a marca decide ser a partir de agora", ["Posicionamento e promessa", "Essência, propósito, missão e visão", "Valores e princípios", "Big idea", "Narrativa e manifesto", "Personalidade e tom de voz", "Pilares de conteúdo", "Comunicação", "Plataforma da marca"])
    sp = s["spectrum"]
    add(3, "Posicionamento", _two("O lugar que a marca", "escolhe ocupar."), f'<p class="lead">{_t(pu["positioning"])}</p><div class="cols c2"><div><small>Categoria</small><p>{_t(s["category"])}. {_t(" ".join(s["not_category"]))}</p></div>'
        f'<div><small>No espectro de mercado</small><p>{_t(sp["from"])} a {_t(sp["to"])}. {_t(ST.scale_label(sp["from"], sp["to"], sp["position"]))}. {_t(sp.get("note", ""))}</p></div></div>', toc="Posicionamento e promessa", note=_note(b, "Posicionamento"))
    add(3, "Proposta de valor e promessa", _two("O que o cliente", "leva para casa."), f'<p class="lead">{_t(s["value_proposition"])}</p><span class="lb">Promessa da marca</span><p class="big" style="font-size:4cqw">{_t(pu["promise"])}</p><p>'
        + _t(" ".join(s["promise_guarantees"])) + "</p>", dark=True)
    if s.get("differentials"):
        add(3, "Diferenciais", _two("Os motivos concretos para", "escolher a marca."), _tbl(("Diferencial", "Prova", "Dá para copiar?"), [(x["name"], x["proof"], ST.COPY_L[x["copyability"]]) for x in s["differentials"]])
            + "<p>Conduta é o que depende de caráter e de escolha, e por isso ninguém copia.</p>")
    add(3, "Essência, propósito, missão e visão", _two("A marca em", "quatro frases."), f'<div class="dm"><span class="lb">Essência</span><p class="big" style="font-size:5cqw;margin:.5cqw 0">{_t(pu["essence"])}</p></div>'
        + _cols([("Propósito: por que existe", pu["reason_to_exist"]), ("Missão: o que faz todo dia", pu["mission"]), ("Visão: onde quer chegar", pu["vision"])], 3), toc="Essência, propósito, missão e visão")
    add(3, "Valores", _two("Valores que aparecem", "no comportamento."), _cols([(v["name"], v["definition"] + " " + v["behavior"]) for v in s["values"]], min(4, len(s["values"]))), toc="Valores e princípios", note=_note(b))
    if s.get("principles"):
        add(3, "Princípios inegociáveis", _two("O que a marca", "nunca negocia."), "<ol>" + "".join(f"<li><b>{_t(x)}</b></li>" for x in s["principles"]) + "</ol>")
    add(3, "Big idea", _two("", cn["big_idea"]), f'<p class="lead">{_t(pu["reason_to_exist"])}</p>', dark=True, toc="Big idea", note=_note(b, "Big idea"), kind="big")
    add(3, "Por que a ideia sustenta a marca", _two("Uma ideia,", "várias razões."), _cols([(x["title"], x["text"]) for x in cn["reasons"]], min(5, len(cn["reasons"]))))
    add(3, "Narrativa", _two("A história que ninguém", "mais pode contar."), '<div class="cols c' + str(min(6, len(b["history"]["arc"]))) + '">' + "".join(f'<div><h3>{i} {_t(x["stage"])}</h3><p>{_t(x["text"])}</p></div>' for i, x in enumerate(b["history"]["arc"], 1)) + "</div>", toc="Narrativa e manifesto")
    if s.get("narrative_rules"):
        add(3, "Diretrizes de narrativa", _two("Como contar", "essa história."), _cols([(x["title"], x["text"]) for x in s["narrative_rules"]], 2) + ("" if not s.get("tone_by_situation") else _tbl(("Situação", "Tom"), [(x["situation"], x["tone"]) for x in s["tone_by_situation"]])))
    add(3, "Manifesto", _two("", " ".join(cn["manifesto"][:1])), "".join(f"<p>{_t(x)}</p>" for x in cn["manifesto"][1:]) + f'<p class="q">{_t(s["manifesto_close"])}</p>', dark=True)
    rl = "".join(f'<div class="rl"><span>{_t(x["left"])}</span><span class="tk"><i style="left:{x["position"] * 25}%"></i></span><span class="r">{_t(x["right"])}</span><small>{_t(ST.scale_label(x["left"], x["right"], x["position"]))}</small></div>' for x in ps["scales"])
    add(3, "Personalidade", _two("Se a marca fosse", "uma pessoa."), '<div class="cols c2" style="border:0">' + rl + '</div>' + "<p>Meio é equilíbrio. Uma casa para o lado é 75% e a ponta é 100%.</p>", toc="Personalidade e tom de voz")
    add(3, "A marca é, a marca não é", _two("Onde a qualidade vira", "defeito."), _tbl(("É", "Não é"), [(x["is"], x["is_not"]) for x in b["voice"]["traits"]]), note=_note(b))
    add(3, "Tom de voz", _two("Princípios,", "um jeito de falar."), _tbl(("Princípio", "Na prática"), [(x["rule"], x["application"]) for x in b["voice"]["principles"]]))
    add(3, "Antes e depois", _two("O mesmo recado,", "na voz da marca."), _tbl(("Antes", "Na voz da marca"), [(x["before"], x["after"]) for x in b["voice"]["before_after"]]))
    if b["voice"].get("dictionary"):
        add(3, "Dicionário", _two("Para a equipe usar", "no atendimento e no conteúdo."), _tbl(("Termo", "Em palavras simples"), [(x["term"], x["plain"]) for x in b["voice"]["dictionary"]]))
    if s.get("content_pillars"):
        cp = s["content_pillars"]
        add(3, "Pilares de conteúdo", _two(f"{len(cp)} assuntos,", "um perfil só."), _bars([(x["name"], x["share"]) for x in cp], "%") + _tbl(("Pilar", "Assuntos", "Exemplos de pauta"), [(x["name"], x["topics"], ", ".join(x["examples"])) for x in cp]), toc="Pilares de conteúdo", note=_note(b, "Pilares de conteúdo"))
        add(3, "Diretrizes de conteúdo", _two("O que sempre fazer e", "o que nunca fazer."), '<div class="cols c2"><div><span class="lb">Sempre</span><ul>' + "".join(f"<li>{_t(x)}</li>" for x in s["content_always"]) + '</ul></div><div><span class="lb">Nunca</span><ul>'
            + "".join(f"<li>{_t(x)}</li>" for x in s["content_never"]) + "</ul></div></div>")
    if s.get("communication_rules"):
        add(3, "Direção de comunicação", _two("Em 5 segundos,", "entender e confiar."), _cols([(x["title"], x["text"]) for x in s["communication_rules"]], min(4, len(s["communication_rules"]))) + f'<div class="dm"><span class="lb">Bio sugerida</span><p>{_t(s["bio"])}</p></div>', toc="Comunicação")
    if s.get("touchpoints"):
        add(3, "Pontos de contato", _two("Em cada lugar,", "a mesma marca."), _tbl(("Ponto de contato", "O que muda"), [(x["name"], x["change"]) for x in s["touchpoints"]]))
    cells = ST.platform_cells(b)
    add(3, "Plataforma da marca", _two("A marca", "em uma página."), '<dl class="plat">' + "".join(f"<div><dt>{_t(k)}</dt><dd>{_t(v)}</dd></div>" for k, v in cells) + "</dl>", lock=True, toc="Plataforma da marca",
        note='<p class="tn"><b>Por trás do termo.</b> A plataforma é o resumo de tudo e é derivada dos outros slides. Nenhuma célula é texto novo.</p>')
    # ---- 4 identidade visual
    opener(4, "Identidade visual", "Como a marca se mostra", ["Assinaturas", "Cor", "Tipografia"])
    add(4, "Assinaturas", _two("O símbolo e o nome,", "sempre juntos."), f'<div class="sig">{uniq(svgs["Horizontal-Positive"], "dkh")}{uniq(svgs["Symbol-Positive"], "dks")}</div><p>{_t(b["symbol"]["protection_rule"])}</p>', lock=True, toc="Assinaturas")
    sw = "".join(f'<div style="background:{c.t(f["universe_name"] + "_50")};color:{c.t("Branco")}"><span>{_t(f["universe_name"])}</span><span>{_t(c.t(f["universe_name"] + "_50"))}</span></div>' for f in b["colour"]["families"])
    sw += "".join(f'<div style="background:{n["hex"]};color:{c.t("Tinta") if n["name"] != "Tinta" else c.t("Branco")}"><span>{_t(n["name"])}</span><span>{_t(n["hex"])}</span></div>' for n in b["colour"]["neutrals"])
    add(4, "Cor", _two("Cores com", "um papel cada."), f'<div class="dsw">{sw}</div><p>{_t(b["colour"]["large_area_rule"])}</p>', lock=True, toc="Cor")
    add(4, "Tipografia", _two("Duas vozes,", "uma família de leitura."), "".join(f'<p style="font-family:{_t(f["name"])},{_t(f["fallback"])};font-size:2.6cqw"><b>{_t(f["name"])}</b> {_t(b["typography"]["specimen_text"])}</p>' for f in b["typography"]["fonts"][:2]), lock=True, toc="Tipografia")
    # ---- fecho
    cl = s["closing"]
    out.append({"kind": "close", "ch": 5, "eb": "Encerramento", "title": _two("", cl["reframe"]), "dark": True, "lock": False, "toc": "Encerramento e fontes", "note": "", "wm": "",
                "body": f'<p class="lead">Próximo passo: <b>{_t(cl["next_step"])}</b></p>'})
    add(5, "Fontes", _two("De onde vieram", "os dados."), _tbl(("Fonte", "O que sustenta"), [(x["outlet"], x["supports"]) for x in s["sources"]]) + f'<p>{_t(s["primary_research_note"])}</p>')
    return out


CH_NAMES = {0: "Abertura", 1: "01 · Diagnóstico", 2: "02 · Viradas de chave", 3: "03 · Direção estratégica", 4: "04 · Identidade visual", 5: "Encerramento"}


def deck_markup(b, c, svgs, uniq, standalone=False):
    """The #deck element: all slides, numbered 1 to N, with a contents slide that points to real pages."""
    sl = slide_list(b, c, svgs, uniq)
    year = year_of(b)
    ident = b["identity"]
    author = b["strategy"].get("welcome", {}).get("signed_by", ident["name"])
    # first slide of each toc entry, with its page number
    toc = []
    for k, x in enumerate(sl):
        if x.get("toc"):
            toc.append((x["ch"], x["toc"], k + 1))
    parts = []
    for k, x in enumerate(sl):
        n = k + 1
        sid = f"dk-{n}"
        cls = "sl" + (" dkl" if x["dark"] else "")
        lock = " data-lock" if x.get("lock") else ""
        if x["kind"] == "cover":
            parts.append(f'<article class="{cls}" id="{sid}" data-n="{n}"{lock}><header><span>{_t(ident["name"])}</span><span>Plataforma da marca</span></header><p class="eb">{_t(x["eb"])}</p><div class="big">{_t(x["title"])}</div><div class="bd">{x["body"]}</div></article>')
            continue
        if x["kind"] == "toc":
            by = {}
            for ch, label, pg in toc:
                by.setdefault(ch, []).append((label, pg))
            blocks = ""
            for ch in (0, 1, 2, 3, 4, 5):
                if ch not in by:
                    continue
                blocks += f"<div><h3>{_t(CH_NAMES[ch])}</h3>" + "".join(f'<a data-to="dk-{pg}"><span>{_t(label)}</span><b>{pg}</b></a>' for label, pg in by[ch]) + "</div>"
            body = f'<div class="tc">{blocks}</div>'
        elif x["kind"] in ("open", "turn", "close"):
            body = x["body"]
        else:
            body = x["body"]
        head = f'<header><span>{_t(CH_NAMES[x["ch"]])}</span><span>{_t(ident["name"])} · Plataforma da marca</span></header>'
        foot = f'<footer><span>{_t(author)}</span><span>{_t(ident["descriptor"])} · {year}</span><span class="pg">{n}</span></footer>'
        if x["kind"] == "open":
            inner = f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:4cqw;flex:1;align-items:center"><div><div class="num">{_t(x["num"])}</div><h2 style="margin-top:1cqw"><b>{_t(x["title"])}</b></h2><p class="lead">{_t(x["eb"])}</p></div><div><span class="lb">Neste capítulo</span>{body}</div></div>'
            parts.append(f'<article class="{cls}" id="{sid}" data-n="{n}" data-ch="{x["ch"]}"{lock}>{head}{inner}{foot}</article>')
            continue
        if x["kind"] == "turn":
            inner = f'<div style="display:grid;grid-template-columns:18cqw 1fr;gap:4cqw;flex:1;align-items:center"><div><div class="num">{_t(x["num"])}</div><span class="of">{_t(x["of"])}</span></div><div><h2 style="font-size:4cqw">{x["title"]}</h2>{body}</div></div>'
            parts.append(f'<article class="{cls}" id="{sid}" data-n="{n}" data-ch="{x["ch"]}"{lock}>{head}{inner}{foot}</article>')
            continue
        if x["kind"] == "close":
            inner = f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center"><p class="eb">{_t(x["eb"])}</p><h2 style="font-size:4.4cqw">{x["title"]}</h2>{body}</div>'
            parts.append(f'<article class="{cls}" id="{sid}" data-n="{n}" data-ch="{x["ch"]}"{lock}>{head}{inner}{foot}</article>')
            continue
        ttl = x["title"]
        inner = f'<p class="eb">{_t(x["eb"])}</p><h2>{ttl}</h2><div class="bd">{body}</div>{x["note"]}'
        wm = f'<span class="wm" aria-hidden="true">{x["ch"]:02d}</span>' if 1 <= x["ch"] <= 4 else ""
        parts.append(f'<article class="{cls}" id="{sid}" data-n="{n}" data-ch="{x["ch"]}"{lock}>{wm}{head}{inner}{foot}</article>')
    bar = ('<div class="dk-bar" data-nav><button type="button" class="btn" id="dk-prev">Anterior</button><span class="dk-c" id="dk-c" role="status"></span><button type="button" class="btn" id="dk-next">Próximo</button>'
           '<button type="button" class="btn" id="dk-print">Imprimir ou PDF</button>'
           + ('' if standalone else '<button type="button" class="btn" id="dk-edit" aria-pressed="false" hidden data-edit-ui>Editar slides</button><button type="button" class="btn" id="dk-save" hidden disabled data-edit-ui>Salvar</button>'
              '<button type="button" class="btn" id="dk-dl" hidden data-edit-ui>Baixar deck (HTML)</button><span id="dk-st" role="status" data-edit-ui></span>'
              '<button type="button" class="btn" id="dk-close">Fechar</button>')
           + '</div>')
    note = '' if standalone else '<p class="dk-c" id="dk-note" hidden data-edit-ui style="margin:0;font-size:13px">Edições valem só para o deck. Para mudar a marca, mude a fonte e gere de novo.</p>'
    return f'<div id="deck" aria-label="Deck da marca" hidden><div class="dk-stage">{"".join(parts)}</div>{bar}{note}</div>', len(sl)


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
