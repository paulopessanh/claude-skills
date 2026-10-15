#!/usr/bin/env python3
"""_ecoedit.py — the editing layer of the brandbook when it runs as an Artifact page.

A library for _ecobook.py. It returns CSS and JavaScript as plain strings. The layer adds, for the people who can write
the page, a bar to edit narrative text, save it, and download a clean client version. Everyone else sees the manual
with no editing interface at all, so the same link works as the client view.

Rules the layer enforces, because the package must not drift:
- Only narrative chapters are editable (story, purpose, concept, personality, name, photography, voice, FAQ, governance).
- Chapters generated from numbers (symbol, colour, type, tokens, applications) and the locked decisions (pétreos and
  vetados) are read only. Change them in the source file and build again, or the manual stops matching the logo.
- An edit stores the hash of the text it replaced. If the source text changes later, the edit is reported as left out
  instead of being applied over a different sentence.

Saved text lives in content.json beside the page. The page itself never changes. Running this file only prints this text.

Stdlib only. Deterministic.
"""

import sys

EDIT_CSS = """
.ed-bar{position:fixed;left:0;right:0;bottom:0;z-index:40;background:var(--surface);border-top:1px solid var(--line);
 padding:10px max(16px,env(safe-area-inset-right,0px)) calc(10px + env(safe-area-inset-bottom,0px)) max(16px,env(safe-area-inset-left,0px));
 display:flex;flex-wrap:wrap;gap:8px 10px;align-items:center;font:500 14px/1.3 var(--body)}
.ed-bar[hidden]{display:none}
.ed-bar .sp{flex:1;min-width:8px}
.ed-bar .st{color:var(--muted);min-width:0}
.ed-bar .btn.pri{background:var(--accent);color:var(--accent-fg);border-color:var(--accent)}
.ed-bar .btn[disabled]{opacity:.45;cursor:default}
.ed-bar .btn[aria-pressed="true"]{outline:2px solid var(--accent);outline-offset:2px}
body.has-edbar{padding-bottom:96px}
.ed-pop{position:fixed;right:max(16px,env(safe-area-inset-right,0px));bottom:calc(76px + env(safe-area-inset-bottom,0px));z-index:41;width:min(360px,calc(100vw - 32px));
 background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:0 12px 40px rgba(0,0,0,.18);font:400 14px/1.5 var(--body)}
.ed-pop[hidden]{display:none}
.ed-pop h4{margin:0 0 6px;font:600 15px var(--body)} .ed-pop p{margin:0 0 10px;color:var(--muted)} .ed-pop .btn{width:100%;justify-content:center}
.ed-toast{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(84px + env(safe-area-inset-bottom,0px));z-index:42;background:var(--fg);color:var(--bg);
 padding:10px 16px;border-radius:999px;font:500 14px var(--body);max-width:calc(100vw - 32px)}
.ed-toast[hidden]{display:none}
.ed-lock{display:none;margin:0 0 20px;padding:10px 14px;border:1px dashed var(--line);border-radius:10px;color:var(--muted);font:400 14px/1.5 var(--body)}
.editing .ed-lock{display:block}
.editing [data-ed]{outline:1px dashed var(--line);outline-offset:3px;border-radius:4px;cursor:text}
.editing [data-ed]:hover{outline-color:var(--muted)} .editing [data-ed]:focus{outline:2px solid var(--accent)}
.editing [data-ed].mod{background:var(--soft)}
.ed-dl{margin-top:16px}
@media print{.ed-bar,.ed-pop,.ed-toast,.ed-lock,.ed-dl{display:none!important}}
"""

EDIT_JS = r"""
(function(){
var EDITABLE=['historia','proposito','conceito','personalidade','nome','fotografia','voz','faq','governanca'];
var LOCKS={petreos:'Pétreos e vetados são decisões travadas com o cliente. Reabra a decisão no projeto, não aqui.',
 simbolo:'Este capítulo nasce da geometria da fonte. Para mudar o símbolo, mude a fonte e gere de novo.',versoes:'Gerado da fonte.',uso:'Gerado da fonte (medidas e erros de uso).',
 cor:'Cores, passos e contrastes vêm da fonte. Para mudar uma cor, mude a fonte e gere de novo, assim o logo e o manual continuam iguais.',
 tipografia:'Tipos e escala vêm da fonte.',elementos:'Gerado da fonte.',movimento:'Tempos e curvas vêm da fonte.',aplicacoes:'Gerado da fonte.',tokens:'Tokens e arquivos vêm da fonte.',historico:'Histórico gerado da fonte.'};
var SEL='p,dd,h3,li,td,summary,.quote,.lead';
var FNAME='__FNAME__';
var S={edits:{},saved:{},orphans:0,editing:false,ns:null,dl:null,can:false,F:[],draftKey:'bk-draft:'+FNAME};
function hash(s){var h=2166136261;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return (h>>>0).toString(36)}
function $(id){return document.getElementById(id)}
function fields(){var out=[];EDITABLE.forEach(function(cid){var ch=$(cid);if(!ch)return;var n=0;
 [].forEach.call(ch.querySelectorAll(SEL),function(el){if(el.children.length||el.closest('.eyebrow,.copy,.badge,[data-edit-ui]'))return;var t=el.textContent;if(!t.trim())return;
  out.push({id:cid+'.'+(n++),el:el,orig:t,h:hash(t)})})});return out}
S.F=fields();
function byId(id){for(var i=0;i<S.F.length;i++)if(S.F[i].id===id)return S.F[i];return null}
function same(a,b){return JSON.stringify(a)===JSON.stringify(b)}
function setText(f,t){f.el.textContent=t;f.el.classList.toggle('mod',t!==f.orig)}
function applyEdits(map){S.orphans=0;S.F.forEach(function(f){var e=map[f.id];if(e&&e.was===f.h){setText(f,e.text)}else{if(e)S.orphans++;setText(f,f.orig)}})}
function count(){var n=0;Object.keys(S.edits).forEach(function(k){if(!S.saved[k]||S.saved[k].text!==S.edits[k].text)n++});Object.keys(S.saved).forEach(function(k){if(!S.edits[k])n++});return n}
function toast(msg){var t=$('ed-toast');if(!t)return;t.textContent=msg;t.hidden=false;clearTimeout(toast.t);toast.t=setTimeout(function(){t.hidden=true},3200)}
function draft(){try{if(count())localStorage.setItem(S.draftKey,JSON.stringify(S.edits));else localStorage.removeItem(S.draftKey)}catch(e){}}
function ui(){var n=count(),st=$('ed-st'),sv=$('ed-save'),un=$('ed-undo');if(!st)return;
 st.textContent=(n?n+(n===1?' alteração não salva':' alterações não salvas'):(S.saved&&Object.keys(S.saved).length?'Tudo salvo':'Sem alterações'))+(S.orphans?'. '+S.orphans+' edição(ões) ficaram de fora porque o texto da fonte mudou':'');
 sv.disabled=!n;un.disabled=!n}
function setEditing(on){S.editing=on;document.documentElement.classList.toggle('editing',on);$('ed-toggle').setAttribute('aria-pressed',String(on));$('ed-toggle').textContent=on?'Concluir edição':'Editar texto';
 S.F.forEach(function(f){if(on){f.el.setAttribute('contenteditable','plaintext-only');if(f.el.contentEditable!=='plaintext-only')f.el.setAttribute('contenteditable','true');f.el.setAttribute('data-ed','')}else{f.el.removeAttribute('contenteditable');f.el.removeAttribute('data-ed')}});
 if(on)[].forEach.call(document.querySelectorAll('#faq details'),function(d){d.open=true})}
document.addEventListener('input',function(e){var el=e.target;if(!S.editing||!el.hasAttribute||!el.hasAttribute('data-ed'))return;
 var f=null;for(var i=0;i<S.F.length;i++)if(S.F[i].el===el){f=S.F[i];break}if(!f)return;
 var t=el.textContent.replace(/\s+/g,' ').trim();if(t===f.orig)delete S.edits[f.id];else S.edits[f.id]={was:f.h,text:t};el.classList.toggle('mod',t!==f.orig);draft();ui()});
document.addEventListener('keydown',function(e){if(S.editing&&e.key==='Enter'&&e.target.hasAttribute&&e.target.hasAttribute('data-ed')){e.preventDefault();e.target.blur()}});
document.addEventListener('click',function(e){if(S.editing&&e.target.closest&&e.target.closest('summary[data-ed]'))e.preventDefault()},true);
function save(){if(!S.ns||!count())return;var body=JSON.stringify({v:1,saved:new Date().toISOString(),edits:S.edits},null,1);$('ed-save').disabled=true;
 draft();
 S.ns.publish({'content.json':{content:body,contentType:'application/json'}}).then(function(){S.saved=JSON.parse(JSON.stringify(S.edits));try{localStorage.removeItem(S.draftKey)}catch(e){}ui();toast('Salvo. Quem abrir o link vê esta versão.')},
  function(err){var c=err&&err.code;ui();toast(c==='conflict'?'Outra pessoa salvou antes. A página vai recarregar e seu rascunho fica guardado.':c==='not_writer'||c==='not_granted'?'Você só pode ler esta página.':c==='capability_disabled'?'Salvar não está disponível neste modo de compartilhamento.':'Não foi possível salvar. Tente de novo.')})}
function undo(){S.edits=JSON.parse(JSON.stringify(S.saved));applyEdits(S.edits);draft();ui()}
function clientHtml(){var root=$('bk-root').cloneNode(true);
 [].forEach.call(root.querySelectorAll('[data-edit-ui]'),function(n){n.remove()});
 [].forEach.call(root.querySelectorAll('[contenteditable],[data-ed],.mod'),function(n){n.removeAttribute('contenteditable');n.removeAttribute('data-ed');n.classList.remove('mod')});
 var link=document.querySelector('link[href*="fonts.googleapis.com/css2"]');var css=$('bk-css'),js=$('bk-js');
 var lang=document.documentElement.getAttribute('lang')||'pt-BR';
 return '<!doctype html><html lang="'+lang+'"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>'+document.title.replace(/</g,'&lt;')+'</title>'
  +'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'+(link?link.outerHTML:'')+'<style>'+css.textContent+'</style></head><body>'+root.outerHTML+'<script>'+js.textContent+'<\/script></body></html>'}
function download(){if(!S.dl){toast('Download indisponível aqui.');return}
 S.dl.save({filename:FNAME,data:clientHtml()}).then(function(){toast('Arquivo do cliente salvo. Abra no navegador e use Imprimir para gerar o PDF.')},function(e){if(!e||e.code!=='declined')toast('Não foi possível baixar.')})}
function build(){if($('ed-bar'))return;
 var bar=document.createElement('div');bar.className='ed-bar';bar.id='ed-bar';bar.setAttribute('data-edit-ui','');bar.setAttribute('role','toolbar');bar.setAttribute('aria-label','Edição do manual');
 bar.innerHTML='<button type="button" class="btn" id="ed-toggle" aria-pressed="false">Editar texto</button><span class="st" id="ed-st" role="status"></span><span class="sp"></span>'
  +'<button type="button" class="btn" id="ed-undo" disabled>Descartar</button><button type="button" class="btn pri" id="ed-save" disabled>Salvar</button><button type="button" class="btn" id="ed-cli" aria-expanded="false">Versão do cliente</button>';
 var pop=document.createElement('div');pop.className='ed-pop';pop.id='ed-pop';pop.hidden=true;pop.setAttribute('data-edit-ui','');
 pop.innerHTML='<h4>Versão do cliente</h4><p>O link desta página mostra o texto salvo, sem os controles de edição. Compartilhe pelo menu Compartilhar do Claude.</p><p>Para enviar um arquivo, baixe o HTML. Ele abre em qualquer navegador e vira PDF pelo comando Imprimir.</p><button type="button" class="btn pri" id="ed-dl">Baixar HTML do cliente</button>';
 var tt=document.createElement('div');tt.className='ed-toast';tt.id='ed-toast';tt.hidden=true;tt.setAttribute('role','status');tt.setAttribute('data-edit-ui','');
 document.body.appendChild(bar);document.body.appendChild(pop);document.body.appendChild(tt);document.body.classList.add('has-edbar');
 Object.keys(LOCKS).forEach(function(cid){var ch=$(cid);if(!ch)return;var h=ch.querySelector('header');if(!h)return;var p=document.createElement('p');p.className='ed-lock';p.setAttribute('data-edit-ui','');p.textContent='Somente leitura. '+LOCKS[cid];h.insertAdjacentElement('afterend',p)});
 $('ed-toggle').addEventListener('click',function(){setEditing(!S.editing)});$('ed-save').addEventListener('click',save);$('ed-undo').addEventListener('click',undo);
 $('ed-cli').addEventListener('click',function(){var o=$('ed-pop').hidden;$('ed-pop').hidden=!o;$('ed-cli').setAttribute('aria-expanded',String(o))});$('ed-dl').addEventListener('click',download);
 window.addEventListener('beforeunload',function(e){if(count()){e.preventDefault();e.returnValue=''}});ui()}
function footer(){var f=document.querySelector('footer.col');if(!f||!S.dl||$('ed-dlf'))return;var b=document.createElement('button');b.type='button';b.className='btn ed-dl';b.id='ed-dlf';b.setAttribute('data-edit-ui','');b.textContent='Baixar este manual (HTML)';b.addEventListener('click',download);f.appendChild(b)}
function loadSaved(){return fetch('content.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():null}).then(function(j){if(j&&j.edits){S.saved=j.edits;S.edits=JSON.parse(JSON.stringify(j.edits));applyEdits(S.edits)}}).catch(function(){})}
function restoreDraft(){try{var d=localStorage.getItem(S.draftKey);if(!d)return;var m=JSON.parse(d);if(m&&typeof m==='object'&&!same(m,S.saved)){S.edits=m;applyEdits(m);if(S.can)toast('Rascunho recuperado. Salve para publicar.')}}catch(e){}}
loadSaved().then(function(){var c=window.claude;if(!c||!c.use)return;
 Promise.all([c.use('artifact'),c.use('user'),c.use('downloads')]).then(function(r){S.ns=r[0];S.dl=r[2];var u=r[1];S.can=!!(S.ns&&u&&u.canEdit&&u.canEdit());
  if(S.can){restoreDraft();build();ui()}footer()}).catch(function(){})});
})();
"""


def edit_css():
    return EDIT_CSS


def edit_js(file_name):
    return EDIT_JS.replace("__FNAME__", file_name)


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
