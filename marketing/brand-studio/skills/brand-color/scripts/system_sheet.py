#!/usr/bin/env python3
"""system_sheet.py — one self-contained HTML sheet of the whole colour system.

Reads the consolidated system JSON written by color_system.py and renders it as a page a designer, a client and a
third-party team can all read: every palette with token, HEX, RGB, approximate CMYK and PMS status, the use of each,
light and dark specimens, and the prohibition cards with their examples.

The sheet follows the visitor's light or dark setting. Every colour shown comes from the data, so the sheet cannot
drift from the palette. Text on a swatch picks white or ink by contrast. No external fonts, scripts or images.
Exit: 0 ok | 1 input error. Stdlib only. No network. Deterministic.
"""

import argparse
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402

E = html.escape


def lab(hx):
    return "#FFFFFF" if cl.contrast("#FFFFFF", hx) >= cl.contrast("#12161C", hx) else "#12161C"


def meta(c, token=None):
    cm = " ".join(str(v) for v in c["cmyk_approx"])
    rgb = ", ".join(str(v) for v in c.get("rgb", cl.hex_rgb(c["hex"])))
    return (f'<span class="tk">{E(token or c.get("token", ""))}</span><span>{E(c["hex"])} · RGB {rgb}</span>'
            f'<span>CMYK≈ {cm} · PMS pendente</span>')


def sw(c, token=None, size=""):
    hx = c["hex"]
    return (f'<div class="sw {size}"><div class="chip" style="background:{hx};color:{lab(hx)}">Aa</div>'
            f'<div class="meta">{meta(c, token)}</div></div>')


def chipline(c, bg=None):
    bits = []
    if "contrast_white" in c:
        bits.append(f'branco {c["contrast_white"]}:1')
        bits.append(f'tinta {c["contrast_ink"]}:1')
    return f'<span class="ratio">{" · ".join(bits)}</span>' if bits else ""


def section(i, title, lead, body):
    return f'<section id="s{i}"><h2><span>{i:02d}</span>{E(title)}</h2><p class="lead">{E(lead)}</p>{body}</section>'


def s_principal(d):
    out = []
    paths = d.get("paths")
    if paths:
        for p in paths.get("paths", []):
            cols = "".join(f'<div class="pc" style="background:{p[k]["hex"]};color:{lab(p[k]["hex"])}"><b>{E(p[k]["name"])}</b><span>{E(p[k]["hex"])}</span></div>'
                           for k in ("primary", "secondary", "accent"))
            mj = p["majority_use"]["light_layout"]
            out.append(f'<div class="card"><h3>Caminho {E(p["id"])} · {E(p["label"])}</h3><div class="bar">{cols}</div>'
                       f'<p>{E(p["why"])}</p><p class="small">Uso majoritário no layout claro: neutro {mj["neutral"]}, principal {mj["primary"]}, acento {mj["accent"]}. Regra de partida a confirmar.</p></div>')
    ch = d["chosen"]
    base = {f["family"]: f["base"] for f in d["scales"]["families"]}
    out.append('<h3>Escolhida</h3><div class="grid">' + "".join(
        f'<div><p class="role">{E(r)}</p>{sw(base[ch[k]])}</div>' for k, r in (("primary", "Principal"), ("secondary", "Secundária"), ("accent", "Acento"))) + "</div>")
    return section(1, "Paleta principal", "As cores da marca, de onde saem todas as outras. Cada uma tem papel e proporção de uso.", "".join(out))


def s_secondary(d):
    out = []
    for f in d["scales"]["families"]:
        out.append(f'<h3>{E(f["family"])}</h3>')
        for kind, label in (("Tint", "Tints"), ("Tone", "Tones"), ("Shade", "Shades")):
            sc = f["scales"][kind]
            out.append(f'<div class="scale"><div class="sch"><b>{label}</b><span>{E(sc["what"])}</span></div>'
                       f'<div class="strip">' + sw(f["base"], size="mini") + "".join(
                           f'<div class="sw mini"><div class="chip" style="background:{s["hex"]};color:{lab(s["hex"])}">{i}</div>'
                           f'<div class="meta">{meta(s)}{chipline(s)}</div></div>' for i, s in enumerate(sc["steps"], 1)) + "</div>"
                       f'<p class="small"><b>Use:</b> {E(sc["use"])} <b>Quando:</b> {E(sc["when"])} <b>Nunca:</b> {E(sc["never"])}</p></div>')
    return section(2, "Paletas secundárias", "Tints, tones e shades de cada cor da marca. Cada escala tem uso próprio.", "".join(out))


def role_cell(r):
    if not r:
        return ""
    hx = r["hex"]
    extra = f'<span class="ratio">{r.get("contrast", r.get("label_contrast", r.get("text_contrast", "")))}:1</span>'
    return (f'<div class="rc"><div class="chip s" style="background:{hx};color:{lab(hx)}">Aa</div>'
            f'<div class="meta"><span class="tk">{E(r["token"])}</span><span>{E(hx)}</span>{extra}</div></div>')


def s_roles(d):
    rows = {}
    for r in d["roles"]["roles"]:
        rows.setdefault(r["role"], {})[r["mode"]] = r
    body = ['<table><thead><tr><th>Papel</th><th>Modo claro</th><th>Modo escuro</th><th>Regra</th><th>Nunca</th></tr></thead><tbody>']
    for role, m in rows.items():
        lt, dk = m.get("light"), m.get("dark")
        body.append(f'<tr><th scope="row">{E((lt or dk)["label"])}</th><td>{role_cell(lt)}</td><td>{role_cell(dk)}</td>'
                    f'<td>{E((lt or dk)["rule"])}</td><td>{E((lt or dk)["never"])}</td></tr>')
    body.append("</tbody></table>")
    mk = d["roles"]["mark_on_primary"]
    body.append(f'<p class="small"><b>Marca sobre a cor principal como fundo:</b> {E(mk["hex"])} ({mk["contrast"]}:1). {E(mk["rule"])}</p>')
    return section(3, "Paletas complementares", "Uma cor para cada trabalho: marca, título, subtítulo, tagline, ícone, linha fina, número-chave, link, botão, destaque e brilho.", "".join(body))


def s_supp(d):
    n = d["neutral"]
    strip = "".join(f'<div class="sw mini"><div class="chip" style="background:{s["hex"]};color:{lab(s["hex"])}">{s["step"]:02d}</div><div class="meta">{meta(s)}</div></div>' for s in n["steps"])
    rl = n["roles"]
    rtab = ['<table><thead><tr><th>Trabalho</th><th>Claro</th><th>Escuro</th></tr></thead><tbody>']
    for k in rl["light"]:
        rtab.append(f'<tr><th scope="row">{E(k)}</th><td>{role_cell({"token": rl["light"][k]["token"], "hex": rl["light"][k]["hex"], "contrast": rl["light"][k]["contrast_on_page"]})}</td>'
                    f'<td>{role_cell({"token": rl["dark"][k]["token"], "hex": rl["dark"][k]["hex"], "contrast": rl["dark"][k]["contrast_on_page"]})}</td></tr>')
    rtab.append("</tbody></table>")
    out = [f'<h3>Neutros da marca ({E(n["temperature"])})</h3><div class="strip">{strip}</div>', "".join(rtab)]
    out.append("<h3>Ambientes físicos</h3>")
    for sp in d["spaces"]["spaces"]:
        rows = "".join(
            f'<tr><th scope="row">{E(x["surface"])}</th><td>{role_cell({"token": x["token"], "hex": x["hex"]})}</td><td>{x["share_percent"]}%</td>'
            f'<td>{x["lrv_estimated"]}</td><td>{E(x["finish"])}</td><td>{E(x["note"])}</td></tr>' for x in sp["surfaces"])
        li = sp["lighting"]
        fl = "".join(f'<li class="warn">{E(f["message"])}</li>' for f in sp["findings"])
        out.append(f'<div class="card"><h3>{E(sp["label"])} · cor de marca em {sp["brand_share_percent"]}% das superfícies (limite {sp["brand_share_limit"]}%)</h3>'
                   f'<p class="small">Iluminação: {E(li["temperatura"])}, IRC {E(li["irc"])}. {E(li["nota"])}</p>'
                   f'<table><thead><tr><th>Superfície</th><th>Cor</th><th>Área</th><th>LRV≈</th><th>Acabamento</th><th>Nota</th></tr></thead><tbody>{rows}</tbody></table>'
                   f'{"<ul>" + fl + "</ul>" if fl else ""}</div>')
    out.append("<ul>" + "".join(f"<li>{E(r)}</li>" for r in d["spaces"]["rules"]) + "</ul>")
    return section(4, "Paletas suplementares", "A escala de neutros que pertence à marca, e as paletas de lojas, showrooms e escritórios.", "".join(out))


def s_status(d):
    st = d["status"]
    cards = []
    for k, v in st["statuses"].items():
        if k == "neutral":
            cards.append(f'<div class="card"><h3>{E(v["label"])}</h3>{sw(v["strong"])}<p class="small">{E(v["meaning"])}</p></div>')
            continue
        tl, td = v["text_on_light"], v["text_on_dark"]
        cards.append(
            f'<div class="card"><h3>{E(v["label"])} <span class="gl">{E(v["glyph"])}</span></h3>{sw(v["strong"])}'
            f'<div class="spec" style="background:{v["surface_light"]["hex"]};color:{tl["hex"]};border:1px solid {v["border_light"]["hex"]}">{E(v["glyph"])} {E(v["label"])} <small>{tl["contrast"]}:1</small></div>'
            f'<div class="spec" style="background:{v["surface_dark"]["hex"]};color:{td["hex"]};border:1px solid {v["border_dark"]["hex"]}">{E(v["glyph"])} {E(v["label"])} <small>{td["contrast"]}:1</small></div>'
            f'<p class="small">{E(v["meaning"])}</p></div>')
    r = st["rules"]
    body = (f'<div class="grid">{"".join(cards)}</div><h3>Use</h3><ul>{"".join(f"<li>{E(x)}</li>" for x in r["use"])}</ul>'
            f'<h3>Nunca</h3><ul>{"".join(f"<li>{E(x)}</li>" for x in r["never"])}</ul>'
            f'<p class="small">{E(r["meaning_not_direction"])} {E(r["icons"])} {E(r["print"])}</p>')
    fl = "".join(f'<li class="warn">{E(f["message"])}</li>' for f in st["findings"])
    return section(5, "Paletas restritas", "Cores de estado para dashboards e relatórios. Dizem uma coisa só e nunca são cor de marca.", body + (f"<ul>{fl}</ul>" if fl else ""))


def s_grad(d):
    out = []
    for g in d["gradients"]:
        stops = "".join(f'<tr><td>{E(s["role"])}</td><td>{s["pos"]}%</td><td>{E(s["hex"])}</td><td>{", ".join(str(v) for v in s["rgb"])}</td>'
                        f'<td>{", ".join(str(v) for v in s["hsl"])}</td><td>{" ".join(str(v) for v in s["cmyk_approx"])}</td></tr>' for s in g["stops"])
        fl = "".join(f'<li class="warn">{E(f["message"])}</li>' for f in g["findings"])
        css = g["css"]["universal_srgb"].replace("180deg", "90deg")
        bgs = g["checks"]["backgrounds"]
        panel = next(iter(bgs.values()))["bg"] if bgs else "#F6F7F9"
        hold = f' · Hold {E(g["hold_token"])}' if g.get("hold_token") else ""
        out.append(f'<div class="card"><h3>{E(g["name"])} · {E(g["verdict"])}<span class="small">{hold}</span></h3>'
                   f'<div class="gp" style="background:{panel}"><div class="gb" style="background:{css}"></div></div>'
                   f'<table><thead><tr><th>Parada</th><th>Pos.</th><th>HEX</th><th>RGB</th><th>HSL</th><th>CMYK≈</th></tr></thead><tbody>{stops}</tbody></table>'
                   f'<p class="small"><b>CSS moderno:</b> <code>{E(g["css"]["modern_oklch"])}</code></p>'
                   f'<p class="small"><b>CSS universal (Figma, Illustrator, Keynote, e-mail):</b> <code>{E(g["css"]["universal_srgb"])}</code></p>'
                   f'<p class="small">Croma mínimo: {g["checks"]["min_chroma_ratio"]} do extremo mais fraco'
                   + (f' (mistura RGB direta: {g["checks"]["naive_rgb_min_chroma_ratio"]})' if g["checks"].get("naive_rgb_min_chroma_ratio") is not None else "")
                   + f'.</p>{"<ul>" + fl + "</ul>" if fl else ""}</div>')
    return section(6, "Gradientes", "Quatro paradas por família: Light Source, Hold, Falloff e Anchor. Sem grey limbo, medido nas amostras reais.", "".join(out))


def s_rules(d):
    u = d["usage"]
    cards = []
    for r in u["backgrounds"]:
        bg = r["bg"]["hex"]

        def tx(k, text, extra=""):
            c = r.get(k)
            return f'<div style="color:{c["hex"]}{extra}">{text} <small>{c["contrast"]}:1</small></div>' if c else ""
        av = "".join(f'<li>{E(a["token"])} {E(a["hex"])}: {a["contrast"]}:1</li>' for a in r["avoid"])
        note = f'<p class="small warn">{E(r["text_note"])}</p>' if r.get("text_note") else ""
        cards.append(
            f'<div class="card"><h3>{E(r["background"])} <small>{E(r["mode"])}</small></h3>'
            f'<div class="specimen" style="background:{bg}">{tx("mark", "MARCA", ";font-weight:800;letter-spacing:.08em;font-size:1.3rem")}'
            f'{tx("brand_title", "Título da peça", ";font-weight:700;font-size:1.15rem")}{tx("text_body", "Texto corrido da peça, em tamanho de leitura.")}'
            f'{tx("text_muted", "Texto de apoio, legenda e data.", ";font-size:.9rem")}{tx("link", "Link sublinhado", ";text-decoration:underline")}'
            f'{tx("accent", "42%", ";font-weight:800;font-size:1.6rem")}</div>'
            f'<p class="small">{E(r["mark_rule"])}</p>{note}'
            f'{"<p class=small><b>Evitar neste fundo</b></p><ul>" + av + "</ul>" if av else ""}</div>')
    sw_rows = "".join(f'<tr><th scope="row">{E(x["label"])}</th><td>{E(x["light"]["token"])} {E(x["light"]["hex"])}</td><td>{E(x["dark"]["token"])} {E(x["dark"]["hex"])}</td></tr>' for x in u["mode_switch"])
    body = (f'<div class="grid wide">{"".join(cards)}</div><h3>Do claro para o escuro</h3>'
            f'<table><thead><tr><th>Papel</th><th>Claro</th><th>Escuro</th></tr></thead><tbody>{sw_rows}</tbody></table>'
            f'<h3>Regras</h3><ul>{"".join(f"<li>{E(x)}</li>" for x in u["rules"])}</ul>')
    return section(7, "Regras de uso", "Como a marca se comporta em fundo claro, fundo escuro e quando uma cor da marca vira o fundo.", body)


def ex_html(e):
    k = e["kind"]
    cap = f'<p class="small">{E(e["caption"])}</p>'
    if k == "pair":
        return f'<div class="ex"><div class="pairs" style="background:{e["bg"]};color:{e["fg"]}">Aa Texto <small>{e["ratio"]}:1</small></div>{cap}</div>'
    if k == "gradient":
        a, b = e["hexes"]
        return f'<div class="ex"><div class="gb" style="background:linear-gradient(90deg,{a},{b})"></div>{cap}</div>'
    hexes = e["hexes"]
    wrong = "errad" in e["caption"] and len(hexes) > 1
    sws = "".join(f'<div class="dot{" bad" if wrong and i == len(hexes) - 1 else ""}" style="background:{h}" title="{h}"><span>{"✕" if wrong and i == len(hexes) - 1 else ""}</span></div>' for i, h in enumerate(hexes))
    return f'<div class="ex"><div class="dots">{sws}</div>{cap}</div>'


def s_prohib(d):
    cards = []
    for it in d["prohib"]["items"]:
        cards.append(f'<div class="card pr {it["severity"].lower()}"><h3><span class="badge">{E(it["severity"])}</span> {E(it["id"])} · {E(it["title"])}</h3>'
                     f'<p><b>Regra.</b> {E(it["rule"])}</p><p class="small"><b>Por quê.</b> {E(it["why"])}</p>'
                     f'{"".join(ex_html(e) for e in it["examples"])}</div>')
    return section(8, "Paleta de proibições", "O que está fora do universo da marca, com exemplos reais para não deixar dúvida.", f'<div class="grid wide">{"".join(cards)}</div>')


CSS = """
:root{--bg:#F6F7F9;--fg:#14181E;--mut:#4A525C;--line:#D5DAE0;--card:#FFFFFF;--warn:#8A4B00;--bad:#B3261E}
@media (prefers-color-scheme:dark){:root{--bg:#10141A;--fg:#E8ECF1;--mut:#A7B0BC;--line:#2A323C;--card:#171C23;--warn:#F0B35A;--bad:#FF8A80}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header,main{max-width:1180px;margin:0 auto;padding:0 20px}
header{padding-top:36px}h1{font-size:2rem;margin:.2em 0}
nav{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);z-index:3}
nav ul{display:flex;gap:6px;flex-wrap:wrap;list-style:none;margin:0 auto;padding:10px 20px;max-width:1180px}
nav a{display:block;padding:6px 10px;border:1px solid var(--line);border-radius:999px;color:var(--fg);text-decoration:none;font-size:.85rem}
nav a:focus-visible,nav a:hover{outline:2px solid currentColor}
section{padding:42px 0 8px;border-top:1px solid var(--line)}
h2{font-size:1.5rem;margin:0 0 .2em;display:flex;gap:12px;align-items:baseline}h2 span{color:var(--mut);font-variant-numeric:tabular-nums}
h3{margin:1.4em 0 .5em;font-size:1.05rem}.lead{color:var(--mut);max-width:70ch;margin-top:0}.small{font-size:.86rem;color:var(--mut)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:6px 18px 16px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px}.grid.wide{grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
.grid .card{margin:0}
.sw{display:flex;gap:12px;align-items:center;margin:6px 0}.sw.mini{flex-direction:column;align-items:stretch;min-width:118px;margin:0}
.chip{width:56px;height:56px;border-radius:12px;display:grid;place-items:center;font-weight:700;flex:none;border:1px solid rgba(127,127,127,.35)}
.sw.mini .chip{width:100%;height:46px}.chip.s{width:34px;height:34px;border-radius:8px;font-size:.8rem}
.meta{display:flex;flex-direction:column;font-size:.74rem;color:var(--mut);line-height:1.35}.tk{font-weight:700;color:var(--fg);word-break:break-all}
.ratio{color:var(--fg);font-variant-numeric:tabular-nums}
.strip{display:flex;gap:8px;overflow-x:auto;padding:4px 0 8px}
.scale{margin:14px 0}.sch{display:flex;gap:10px;align-items:baseline}.sch span{color:var(--mut);font-size:.88rem}
table{width:100%;border-collapse:collapse;font-size:.88rem;margin:10px 0}th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line)}
thead th{color:var(--mut);font-weight:600;font-size:.78rem;text-transform:uppercase;letter-spacing:.04em}
.rc{display:flex;gap:8px;align-items:center}
.bar{display:flex;border-radius:10px;overflow:hidden;margin:8px 0}.pc{flex:1;padding:16px 12px;display:flex;flex-direction:column}
.pc span{font-size:.8rem}.role{margin:0;font-size:.8rem;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
.spec{margin:6px 0;padding:10px 12px;border-radius:10px;font-weight:600}.gl{font-weight:800}
.specimen{border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:6px;border:1px solid var(--line)}
.specimen small,.spec small{font-weight:400;opacity:.85;font-size:.72rem}
.gp{padding:10px;background:#F6F7F9;border-radius:10px;margin:8px 0}.gb{height:84px;border-radius:10px}
code{font-size:.78rem;word-break:break-all}
.warn,.small.warn{color:var(--warn)}
.badge{display:inline-block;font-size:.68rem;padding:2px 8px;border-radius:999px;border:1px solid currentColor;vertical-align:middle}
.pr.block .badge{color:var(--bad)}.pr.alert .badge{color:var(--warn)}.pr.guide .badge{color:var(--mut)}
.dots{display:flex;gap:10px;margin:8px 0}.dot{width:64px;height:64px;border-radius:12px;display:grid;place-items:center;border:1px solid rgba(127,127,127,.4);font-size:1.6rem;color:#fff;position:relative}
.dot.bad{outline:3px solid var(--bad);outline-offset:2px}.dot span{text-shadow:0 0 4px #000}
.pairs{padding:14px;border-radius:10px;font-weight:700;border:1px solid var(--line)}.ex{margin:10px 0}
footer{max-width:1180px;margin:40px auto;padding:20px;color:var(--mut);font-size:.82rem;border-top:1px solid var(--line)}
@media (max-width:640px){h1{font-size:1.5rem}table{display:block;overflow-x:auto}}
"""

NAV = ["Principal", "Secundárias", "Complementares", "Suplementares", "Restritas", "Gradientes", "Regras de uso", "Proibições"]


def render(d):
    brand = d["brand"]
    body = "".join((s_principal(d), s_secondary(d), s_roles(d), s_supp(d), s_status(d), s_grad(d), s_rules(d), s_prohib(d)))
    nav = "".join(f'<li><a href="#s{i}">{i:02d} {n}</a></li>' for i, n in enumerate(NAV, 1))
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="color-scheme" content="light dark"><title>Sistema de cores {E(brand.get("name", brand["sigla"]))}</title><style>{CSS}</style></head>'
            f'<body><header><p class="small">{E(brand["sigla"])} · sistema de cores</p><h1>{E(brand.get("name", brand["sigla"]))}: sistema de cores</h1>'
            f'<p class="lead">Principal, secundárias, complementares, suplementares, restritas, gradientes, regras de uso e proibições. '
            f'CMYK é aproximado e todo PMS está pendente de correspondência impressa.</p></header>'
            f'<nav aria-label="Seções"><ul>{nav}</ul></nav><main>{body}</main>'
            f'<footer>Gerado de uma fonte única pelo brand-color. Mude a fonte e gere de novo: não edite esta folha.</footer></body></html>')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--system", required=True, help="system.json written by color_system.py")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        with open(a.system, encoding="utf-8") as f:
            page = render(json.load(f))
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(page)
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
