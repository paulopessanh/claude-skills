#!/usr/bin/env python3
"""_ecostrat.py — the strategic chapters of the brandbook and the platform on a page.

A library for ecosystem_builder.py. It reads the optional `strategy` block of a brand-source.v2 file, plus the strategic
fields that live in other blocks (personas, archetype, scales, voice principles). A source without `strategy` builds the
same package as before. The platform summary is derived here and is never a field of the source, so a cell cannot say
something that the chapters do not say. The auditor re-derives the cells on its own and compares them with the page.
Running this file only prints this text.

Stdlib only. Deterministic.
"""

import html
import sys

esc = html.escape

CHAPTER_IDS = ["metodo", "diagnostico", "viradas", "direcao", "tom", "plataforma"]
COPY_L = {"conduct": "Não. É conduta", "effort": "Só com esforço"}

CSS = """
.bars{display:grid;gap:10px;margin:14px 0}.pb{display:grid;grid-template-columns:minmax(120px,220px) 1fr auto;gap:12px;align-items:center}
.pb .tr{height:14px;border-radius:7px;background:var(--soft);overflow:hidden}.pb .tr i{display:block;height:100%;background:var(--accent)}
.pb b{font-variant-numeric:tabular-nums}
.rl{display:grid;grid-template-columns:minmax(90px,1fr) minmax(120px,2fr) minmax(90px,1fr);gap:12px;align-items:center;margin:8px 0}
.rl .tk{position:relative;height:2px;background:var(--line)}.rl .tk i{position:absolute;top:-6px;width:14px;height:14px;border-radius:50%;background:var(--fg);transform:translateX(-50%)}
.rl .r{text-align:right}.rl small{grid-column:1/-1;text-align:center;color:var(--muted);font-weight:600}
.m2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}.m2 .card.own{background:var(--hero);color:var(--hero-fg);border-color:var(--hero)}
.m2 .card.own h3,.m2 .card.own p{color:var(--hero-fg)}
.dk{background:var(--hero);color:var(--hero-fg);border-radius:14px;padding:18px 20px}.dk h3,.dk p,.dk .eyebrow{color:var(--hero-fg)}
.plat{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:2px solid var(--fg)}
.plat>div{padding:14px 12px 14px 0;border-bottom:1px solid var(--line)}.plat dt{font:700 11px var(--body);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.plat dd{margin:4px 0 0;font-weight:600}
.gloss{border-top:1px solid var(--line);margin-top:18px;padding-top:10px;color:var(--muted)}
@media (max-width:720px){.pb{grid-template-columns:1fr auto}.pb .tr{grid-column:1/-1}.rl{grid-template-columns:1fr 1fr}.rl .tk{grid-column:1/-1;order:3}.m2,.plat{grid-template-columns:1fr}}
"""


def has(b):
    return bool(b.get("strategy"))


def _t(x):
    return esc(str(x))


def _p(t, cls=""):
    return f'<p{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>{_t(t)}</p>'


def _tbl(head, rows):
    return ('<div class="tw"><table><thead><tr>' + "".join(f"<th>{_t(h)}</th>" for h in head) + "</tr></thead><tbody>"
            + "".join("<tr>" + "".join(f"<td>{_t(x)}</td>" for x in r) + "</tr>" for r in rows) + "</tbody></table></div>")


def _cards(items, grid="g3"):
    return f'<div class="grid {grid}">' + "".join(f"<div class='card'><h3>{_t(a)}</h3>{_p(t)}</div>" for a, t in items) + "</div>"


def _bars(rows, unit=""):
    """rows: (label, count or share). Width is the share of the largest value."""
    top = max((v for _, v in rows), default=1) or 1
    return '<div class="bars">' + "".join(
        f'<div class="pb"><span>{_t(l)}</span><span class="tr"><i style="width:{round(100 * v / top)}%"></i></span><b>{_t(v)}{unit}</b></div>' for l, v in rows) + "</div>"


def _gloss(b, *terms):
    notes = {n["term"]: n["plain"] for n in b["strategy"].get("term_notes", [])}
    rows = [(t, notes[t]) for t in terms if t in notes]
    if not rows:
        return ""
    return '<p class="gloss"><b>Por trás do termo.</b> ' + " ".join(f"<b>{_t(t)}</b>: {_t(x)}" for t, x in rows) + "</p>"


def scale_label(left, right, pos):
    return {0: f"100% {left}", 1: f"75% {left}", 2: "Equilíbrio", 3: f"75% {right}", 4: f"100% {right}"}[pos]


def platform_cells(b):
    """The 12 cells of the platform page, each one a text that already exists elsewhere in the source."""
    s = b["strategy"]
    names = ", ".join(v["name"] for v in s.get("values", []))
    traits = ", ".join(t["name"] for t in b["voice"]["traits"])
    return [("Ideia central", b["concept"]["big_idea"]), ("Frase da marca", b["identity"]["tagline"]), ("Essência", b["purpose"]["essence"]),
            ("Propósito", b["purpose"]["reason_to_exist"]), ("Promessa", b["purpose"]["promise"]), ("Categoria", s["category"]),
            ("Posicionamento", b["purpose"]["positioning"]), ("Valores", names), ("Arquétipo", b["personality"]["archetype"]["intersection_name"]),
            ("Tom de voz", traits), ("Para quem", b["audience"]["summary"]), ("Percepção desejada", s["synthesis"]["desired_perception"])]


def chapters(b):
    """Return [(id, title, body_html, lead)] for the six strategic chapters, in reading order."""
    s = b["strategy"]
    out = []
    # ---- método
    w = s.get("welcome", {})
    m = s["method"]
    body = ""
    if w:
        body += f'<div class="card"><h3>Para {_t(w["addressee"])}</h3>{_p(w["text"])}{_p(w["signed_by"])}</div>'
    body += f'<p class="quote">{_t(s["guiding_question"])}</p>'
    body += f'<h3>O método: {_t(m["name"])}</h3>' + _p(m["rule"]) + _cards([(f'{p["letter"]}  {p["name"]}' if p.get("letter") else p["name"], p["question"]) for p in m["pillars"]], "g2")
    body += "<h3>A base de evidências</h3>" + _tbl(("Tipo", "Quantidade", "Nota"), [(e["kind"], e["count"], e["note"]) for e in s["evidence_base"]])
    body += "<h3>Leitura por lente</h3>" + _tbl(("Lente", "O que encontramos", "O que isso significa"), [(r["pillar"], r["found"], r["meaning"]) for r in s["reading"]])
    out.append(("metodo", "Método e evidências", body + _gloss(b, "Posicionamento", "Território"), "Como a investigação foi feita e quanto material a sustenta."))
    # ---- diagnóstico
    d = ""
    if s.get("market_data"):
        d += "<h3>Dados de mercado</h3>" + _tbl(("Dado", "Número", "Fonte"), [(x["label"], x["figure"], x["source"]) for x in s["market_data"]])
    if s.get("market_shifts"):
        d += "<h3>O mercado mudou de lugar</h3>" + _tbl(("Quando", "O que mudou", "O efeito na marca", "Fonte"), [(x["date"], x["fact"], x["effect"], x["source"]) for x in s["market_shifts"]])
    if s.get("market_implications"):
        d += "<h3>O que isso significa para a marca</h3>" + _cards([(x["title"], x["text"]) for x in s["market_implications"]])
    if s.get("premises"):
        d += "<h3>Premissas do negócio</h3>" + _cards([(x["title"], x["text"]) for x in s["premises"]])
    d += "<h3>Metas por horizonte e papel da marca</h3>" + _tbl(("Prazo", "Meta do negócio", "Papel da marca"), [(g["horizon"], g["business_goal"], g["brand_role"]) for g in s["goals"]])
    d += f'<div class="dk"><p class="eyebrow">Nosso olhar crítico</p>{_p(s["critical_view"])}</div>'
    d += "<h3>Pontos de tensão e a decisão de cada um</h3>" + _tbl(("Um lado", "Outro lado", "Decisão"), [(t["side_a"], t["side_b"], t["decision"]) for t in s["tensions"]])
    for c_ in s.get("owner_corrections", []):
        d += f'<div class="card"><h3>Onde a evidência corrige a leitura da marca</h3>{_p("Antes: " + c_["belief"])}{_p("Evidência: " + c_["evidence"])}{_p("Decisão: " + c_["decision"])}</div>'
    d += f'<h3>Quem mais combina com a marca</h3>{_p(s["icp"])}<div class="dk"><p class="eyebrow">O achado que muda o jogo</p>{_p(s["icp_insight"])}</div>'
    pe = b["audience"]["personas"]
    d += "<h3>Personas</h3>" + _tbl(("Pessoa", "Quer", "O que trava", "O que precisa ouvir"), [(x["name"], x["needs"], x["blocker"], x["needs_to_hear"]) for x in pe])
    d += "<h3>Quem não é cliente</h3><ul>" + "".join(f"<li>{_t(x)}</li>" for x in s["non_clients"]) + "</ul>" + _p(s.get("non_client_rule", "")) if s.get("non_clients") else ""
    if s.get("value_premises"):
        d += "<h3>Premissas de valor</h3>" + _cards([(x["title"], x["text"]) for x in s["value_premises"]], "g2")
    ve = s.get("value_equation")
    if ve:
        d += ("<h3>Equação de valor percebido</h3>" + _p("O cliente soma: " + ", ".join(ve["gains"]) + ". O cliente subtrai: " + ", ".join(ve["costs"]) + ".")
              + _bars([(x["factor"], x["score"]) for x in ve["reading"]], " de 5") + _tbl(("Fator", "Leitura", "Ação"), [(x["factor"], x["reading"], x["action"]) for x in ve["reading"]]))
    d += "<h3>Concorrência por tipo</h3>" + _tbl(("Tipo", "Faz bem", "Falha em", "A marca faz diferente"), [(x["type"], x["does_well"], x["fails_at"], x["we_differ"]) for x in s["competition"]])
    tm = s.get("territory_map")
    if tm:
        d += (f'<h3>Mapa de território</h3>{_p("Eixos: " + tm["y_axis"] + " e " + tm["x_axis"] + ".")}<div class="m2">'
              + "".join(f'<div class="card{" own" if q["name"] == tm["own"] else ""}"><h3>{_t(q["name"])}</h3>{_p(", ".join(q["brands"]))}</div>' for q in tm["quadrants"]) + "</div>")
    u = s.get("universe")
    if u:
        d += "<h3>Universo da marca</h3>" + _cards([("Atmosfera", u["atmosphere"]), ("Linguagem", u["language"]), ("Postura", u["posture"]), ("Estética visual", u["aesthetics"]), ("Presença digital", u["digital"]), ("O que não cabe", u["not_fit"])])
    a = b["personality"]["archetype"]
    d += ("<h3>Arquétipo: " + _t(a["primary"]) + " e " + _t(a["secondary"]) + f", {_t(a['intersection_name'])}</h3>"
          + _tbl(("", "Principal: " + a["primary"], "Secundário: " + a["secondary"]), [("De onde veio", a["origin"], ""), ("O que traz", a["brings"], ""), ("A sombra", a["shadow"], ""), ("Quem equilibra", a["balanced_by"], "")])
          + f'<div class="card"><h3>Entra como tempero</h3>{_p(a["seasoning"])}</div>')
    pc = s.get("perception")
    if pc:
        d += ("<h3>Pesquisa de percepção</h3>" + _p(f"Respostas válidas: {pc['n']}. {pc['sample_note']}") + "<h4>Para que a marca existe, nas respostas</h4>" + _bars([(x["label"], x["count"]) for x in pc["purpose_answers"]])
              + "<h4>Como a veem hoje</h4>" + _bars([(x["trait"], x["count"]) for x in pc["traits_today"]]) + "<h4>O que pedem ao futuro</h4>" + _bars([(x["trait"], x["count"]) for x in pc["traits_future"]])
              + f'<div class="dk"><p class="eyebrow">Leitura</p>{_p(pc["reading"])}</div>')
    out.append(("diagnostico", "Diagnóstico", d + _gloss(b, "Arquétipo", "Sombra"), "O que é verdade hoje sobre o negócio, o público, o valor, a concorrência e a percepção."))
    # ---- viradas
    v = ""
    for i, t in enumerate(s["turns"], 1):
        v += f'<div class="card"><p class="eyebrow">{i} de {len(s["turns"])}</p><h3>{_t(t["title"])}</h3>{_p(t["text"])}</div>'
    sy = s["synthesis"]
    v += ("<h3>Síntese estratégica</h3>" + _cards([("Cenário", sy["scenario"]), ("Problema", sy["problem"]), ("Oportunidade", sy["opportunity"]), ("Território", sy["territory"])], "g2")
          + f'<p class="eyebrow">Percepção desejada</p><p class="quote">{_t(sy["desired_perception"])}</p>')
    out.append(("viradas", "Viradas de chave e síntese", v, "Leituras que nascem de cruzar o que a marca diz com o que as evidências mostram."))
    # ---- direção
    pu = b["purpose"]
    r = f'<p class="quote">{_t(pu["positioning"])}</p>' + _cards([("Categoria", s["category"]), ("Não é", ", ".join(s["not_category"]))], "g2")
    sp = s["spectrum"]
    r += _p(f"No espectro de mercado: {sp['from']} a {sp['to']}. {scale_label(sp['from'], sp['to'], sp['position'])}. {sp.get('note', '')}")
    r += f'<div class="dk"><p class="eyebrow">O que o cliente leva para casa</p>{_p(s["value_proposition"])}<p class="eyebrow">Promessa</p>{_p(pu["promise"])}</div><ul>' + "".join(f"<li>{_t(x)}</li>" for x in s["promise_guarantees"]) + "</ul>"
    if s.get("differentials"):
        r += "<h3>Diferenciais e o teste de cópia</h3>" + _tbl(("Diferencial", "Prova", "Dá para copiar?"), [(x["name"], x["proof"], COPY_L[x["copyability"]]) for x in s["differentials"]])
    r += ("<h3>Essência, propósito, missão e visão</h3>" + _cards([("Essência", pu["essence"]), ("Propósito", pu["reason_to_exist"]), ("Missão", pu["mission"]), ("Visão", pu["vision"])], "g2"))
    r += "<h3>Valores</h3>" + _tbl(("Valor", "Origem", "No comportamento"), [(x["name"], x["definition"], x["behavior"]) for x in s["values"]])
    if s.get("principles"):
        r += "<h3>O que a marca nunca negocia</h3><ol>" + "".join(f"<li>{_t(x)}</li>" for x in s["principles"]) + "</ol>"
    cn = b["concept"]
    ss = s.get("slogan_system")
    if ss:
        r += (f'<h3>Slogan em dois tempos ({_t("proposta" if ss["status"] == "proposed" else "aprovado")})</h3>' + _cards([("Primeiro tempo", ss["first_beat"]), ("Segundo tempo", ss["second_beat"])], "g2")
              + _tbl(("Uso", "Frase"), [(x["context"], x["line"]) for x in ss["usage"]]) + _p("Frases de apoio: " + " ".join(ss["support_lines"])) + (_p(ss["note"]) if ss.get("note") else ""))
    r += f'<h3>Big idea</h3><p class="quote">{_t(cn["big_idea"])}</p>' + _cards([(x["title"], x["text"]) for x in cn["reasons"]], "g2")
    r += "<h3>Narrativa em etapas</h3>" + _tbl(("Etapa", "O que conta"), [(x["stage"], x["text"]) for x in b["history"]["arc"]])
    if s.get("narrative_rules"):
        r += "<h3>Como contar a história</h3>" + _cards([(x["title"], x["text"]) for x in s["narrative_rules"]], "g2")
    if s.get("tone_by_situation"):
        r += "<h3>A mesma voz em cada situação</h3>" + _tbl(("Situação", "Tom"), [(x["situation"], x["tone"]) for x in s["tone_by_situation"]]) + '<ul class="chips">' + "".join(f"<li>{_t(x)}</li>" for x in s.get("themes", [])) + "</ul>"
    r += f'<p class="quote">{_t(s["manifesto_close"])}</p>'
    out.append(("direcao", "Direção estratégica", r + _gloss(b, "Big idea"), "O que a marca decide ser, dizer e fazer daqui para frente."))
    # ---- tom
    t = "<h3>Personalidade em réguas</h3>" + _p("Meio é equilíbrio. Uma casa para o lado é 75% e a ponta é 100%.")
    for x in b["personality"]["scales"]:
        t += (f'<div class="rl"><span>{_t(x["left"])}</span><span class="tk"><i style="left:{x["position"] * 25}%"></i></span><span class="r">{_t(x["right"])}</span>'
              f'<small>{_t(scale_label(x["left"], x["right"], x["position"]))}</small></div>')
    t += "<h3>Princípios de tom de voz</h3>" + _tbl(("Princípio", "Na prática"), [(x["rule"], x["application"]) for x in b["voice"]["principles"]])
    t += "<h3>O mesmo recado, na voz da marca</h3>" + _tbl(("Antes", "Na voz da marca"), [(x["before"], x["after"]) for x in b["voice"]["before_after"]])
    if b["voice"].get("dictionary"):
        t += "<h3>Dicionário</h3>" + _tbl(("Termo", "Em palavras simples"), [(x["term"], x["plain"]) for x in b["voice"]["dictionary"]])
    if s.get("content_pillars"):
        t += "<h3>Pilares de conteúdo</h3>" + _bars([(x["name"], x["share"]) for x in s["content_pillars"]], "%") + _tbl(("Pilar", "Assuntos", "Exemplos de pauta"), [(x["name"], x["topics"], ", ".join(x["examples"])) for x in s["content_pillars"]])
        t += ('<div class="grid g2"><div class="card"><h3>Sempre</h3><ul>' + "".join(f"<li>{_t(x)}</li>" for x in s["content_always"]) + '</ul></div><div class="card"><h3>Nunca</h3><ul>'
              + "".join(f"<li>{_t(x)}</li>" for x in s["content_never"]) + "</ul></div></div>")
    if s.get("communication_rules"):
        t += "<h3>Direção de comunicação</h3>" + _cards([(x["title"], x["text"]) for x in s["communication_rules"]], "g3") + f'<div class="dk"><p class="eyebrow">Bio sugerida</p>{_p(s["bio"])}</div>'
    if s.get("touchpoints"):
        t += "<h3>Pontos de contato</h3>" + _tbl(("Ponto de contato", "O que muda"), [(x["name"], x["change"]) for x in s["touchpoints"]])
    ba = s.get("brand_architecture")
    if ba:
        t += (f'<h3>Arquitetura de marca: {_t(ba["model"].lower())}</h3><div class="dk"><p class="eyebrow">Marca mãe</p><h3>{_t(ba["parent"])}</h3></div>'
              + _cards([("Linha", x) for x in ba["children"]], "g3") + _p(ba["rule"]))
    out.append(("tom", "Personalidade, voz e conteúdo", t + _gloss(b, "Pilares de conteúdo"), "Como a marca soa, o que publica e onde aparece."))
    # ---- plataforma
    cells = platform_cells(b)
    pl = '<dl class="plat">' + "".join(f"<div><dt>{_t(k)}</dt><dd>{_t(v)}</dd></div>" for k, v in cells) + "</dl>"
    cl = s.get("closing")
    if cl:
        pl += f'<div class="dk"><p class="eyebrow">Encerramento</p><h3>{_t(cl["reframe"])}</h3>{_p("Próximo passo: " + cl["next_step"])}</div>'
    pl += "<h3>Fontes</h3>" + _tbl(("Fonte", "O que sustenta"), [(x["outlet"], x["supports"]) for x in s["sources"]]) + _p(s["primary_research_note"], "gloss")
    out.append(("plataforma", "Plataforma da marca", pl, "A marca em uma página. Nenhuma célula é texto novo."))
    return out


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
