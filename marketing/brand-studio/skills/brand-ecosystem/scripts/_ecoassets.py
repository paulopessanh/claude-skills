#!/usr/bin/env python3
"""_ecoassets.py — draws every visual file of the ecosystem from brand-source.v1.

A library for ecosystem_builder.py. It returns SVG strings and never reads or writes files. Every colour it uses is a
token of the brand; every text carries data-bg (the colour behind it) and data-size so ecosystem_auditor.py can recompute
its contrast. The symbol is a geometric study generated from parameters, to be refined and finalised by the creative team.
Running this file only prints this text.

Stdlib only. Deterministic.
"""

import html
import math
import sys

from _ecolib import ridge_points, polyline, polyline_length

POL = {"positive": ("Cume_50", "Vale_50", "Neblina"), "negative": ("Cume_10", "Vale_30", "Cume_70"), "mono": ("Tinta", "Tinta", "Branco")}
K_WIDTH = {"headline": 0.47, "body": 0.54, "mono": 0.62}
# Lockup geometry. One set of numbers shared by the drawing, the modulation diagrams and the audit, so the manual cannot
# state a proportion the file does not have. Units are those of the symbol: the tallest peak is 100.
LH = {"gap": 40, "name": 100, "desc": 24, "desc_ls": 3.2, "rule": 0.45}
LV = {"scale": 1.3, "name": 90, "desc": 22, "desc_ls": 3.0, "rule": 0.45, "below": 22}


def esc(s):
    return html.escape(str(s), quote=True)


class Ctx:
    def __init__(self, b, flat, fams):
        self.b, self.flat, self.b_fams, self.sig = b, flat, fams, b["identity"]["sigla"]
        self.name, self.desc, self.tag = b["identity"]["name"], b["identity"]["descriptor"], b["identity"]["tagline"]
        self.fam = {f["role"]: f"'{f['name']}', {f['fallback']}" for f in b["typography"]["fonts"]}
        sy = b["symbol"]
        self.pts = ridge_points(sy["vertices"], sy["slope_deg"], 100.0)
        self.W, self.H, self.sw = self.pts[-1][0], 100.0, sy["stroke_ratio"] * 100.0
        self.sy = sy

    def t(self, name):
        return self.flat[f"{self.sig}_{name}"]

    def text(self, x, y, s, size, fill, bg, role="body", weight=400, anchor="start", tl=None, ls=None, italic=False, upper=False, logo=False):
        a = (f'x="{x:g}" y="{y:g}" font-family="{esc(self.fam[role])}" font-size="{size:g}" font-weight="{weight}" fill="{fill}" '
             f'data-bg="{bg}" data-size="{size:g}"')
        if anchor != "start":
            a += f' text-anchor="{anchor}"'
        if logo:
            a += ' data-exempt="logotype"'
        if italic:
            a += ' font-style="italic"'
        if ls is not None:
            a += f' letter-spacing="{ls:g}"'
        if tl:
            a += f' textLength="{tl:g}" lengthAdjust="spacing"'
        return f"<text {a}>{esc(s.upper() if upper else s)}</text>"

    def est(self, s, size, role="body", ls=0.0):
        return round(len(s) * (size * K_WIDTH[role] + ls), 1)


def svg(w, h, body, title, vb=None, extra=""):
    vb = vb or f"0 0 {w:g} {h:g}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w:g}" height="{h:g}" role="img" aria-label="{esc(title)}"{extra}>'
            f"<title>{esc(title)}</title>{body}</svg>")


def sym(c, color, ox=0.0, oy=0.0, sc=1.0, extra=""):
    return (f'<polyline points="{polyline(c.pts, c.H, ox, oy, sc)}" fill="none" stroke="{color}" stroke-width="{c.sw * sc:.2f}" '
            f'stroke-linecap="round" stroke-linejoin="round"{extra}/>')


def sym_box(c):
    p = c.sw
    return (-p, -p, c.W + 2 * p, c.H + 2 * p)


# ------------------------------------------------------------ logo files
def symbol_svg(c, pol):
    ink, _, bg = POL[pol]
    x, y, w, h = sym_box(c)
    return svg(w, h, sym(c, c.t(ink)), f"{c.name}, símbolo, versão {pol}", vb=f"{x:.2f} {y:.2f} {w:.2f} {h:.2f}")


def wordmark_g(c, pol, size=100, x=0, y=100, anchor="start"):
    ink, _, bg = POL[pol]
    return c.text(x, y, c.name, size, c.t(ink), c.t(bg), "headline", 500, anchor, tl=c.est(c.name, size, "headline"), logo=True)


def wordmark_svg(c, pol):
    size = 100
    w = c.est(c.name, size, "headline")
    return svg(w + 20, 150, wordmark_g(c, pol, size, 10, 110), f"{c.name}, nome, versão {pol}")


def lockup_h(c, pol):
    """Symbol, then the same line continues as a horizon: the name sits on it, the descriptor hangs under it."""
    ink, acc, bg = POL[pol]
    p, gap, size = c.sw, LH["gap"], LH["name"]
    tl = c.est(c.name, size, "headline")
    d_size = LH["desc"]
    d_tl = c.est(c.desc, d_size, "body", LH["desc_ls"])
    ox, oy = p, p + 10
    base = oy + c.H                      # baseline of the ridge and of the horizon rule
    tx = ox + c.W + gap
    x_end = tx + max(tl, d_tl) + 4
    rule = (f'<line x1="{ox + c.W:.2f}" y1="{base:.2f}" x2="{x_end:.2f}" y2="{base:.2f}" stroke="{c.t(ink)}" '
            f'stroke-width="{c.sw * LH["rule"]:.2f}" stroke-linecap="round"/>')
    body = (sym(c, c.t(ink), ox, oy) + rule + wordmark_g(c, pol, size, tx, base - 16)
            + c.text(tx + 4, base + 38, c.desc, d_size, c.t(acc if pol != "mono" else ink), c.t(bg), "body", 600, ls=LH["desc_ls"], tl=d_tl, upper=True, logo=True))
    return body, x_end + p, base + 38 + 14


def lockup_v(c, pol):
    ink, acc, bg = POL[pol]
    p, size = c.sw, LV["name"]
    tl = c.est(c.name, size, "headline")
    d_size = LV["desc"]
    d_tl = c.est(c.desc, d_size, "body", LV["desc_ls"])
    sc = LV["scale"]
    w = max(tl, c.W * sc) + 2 * p + 40
    cx = w / 2
    ox, oy = cx - c.W * sc / 2, p + 10
    base = oy + c.H * sc
    rule = (f'<line x1="{cx - tl / 2:.2f}" y1="{base:.2f}" x2="{cx + tl / 2:.2f}" y2="{base:.2f}" stroke="{c.t(ink)}" '
            f'stroke-width="{c.sw * LV["rule"] * sc:.2f}" stroke-linecap="round"/>')
    wy = base + LV["below"] + size * 0.78
    body = (rule + sym(c, c.t(ink), ox, oy, sc) + wordmark_g(c, pol, size, cx, wy, "middle")
            + c.text(cx, wy + 44, c.desc, d_size, c.t(acc if pol != "mono" else ink), c.t(bg), "body", 600, "middle", ls=LV["desc_ls"], tl=d_tl, upper=True, logo=True))
    return body, w, wy + 44 + 14


def lockup_svg(c, pol, kind):
    body, w, h = (lockup_h if kind == "horizontal" else lockup_v)(c, pol)
    return svg(round(w, 1), round(h, 1), body, f"{c.name}, assinatura {kind}, versão {pol}")


def ink_of(c, pol):
    """Token name (without the sigla) of the colour the mark is drawn in, for a polarity."""
    return POL[pol][0]


def lockup_dims(c, kind, pol="positive"):
    """Width and height of the lockup file, in symbol units (tallest peak = 100 in the symbol file)."""
    _, w, h = (lockup_h if kind == "horizontal" else lockup_v)(c, pol)
    return w, h


def symbol_dims(c):
    _, _, w, h = sym_box(c)
    return w, h


def width_ratio(c, kind):
    """How many times wider the lockup file is than the symbol file. Minimum sizes scale with it."""
    if kind == "symbol":
        return 1.0
    return lockup_dims(c, kind)[0] / symbol_dims(c)[0]


def modulation_svg(c, kind):
    """The lockup with its measures: u is the tallest peak as drawn in that lockup. Protection area is 1u on every side."""
    pol = "positive"
    ink = c.t(POL[pol][0])
    body, w, h = (lockup_h if kind == "horizontal" else lockup_v)(c, pol)
    p = c.sw
    if kind == "horizontal":
        u = c.H
        ox, oy = p, p + 10
        x_sym_end = ox + c.W
        tx = x_sym_end + LH["gap"]
        marks = [("u", ox - 14, oy, ox - 14, oy + u)]
        gap_mark = (f"{LH['gap'] / u:g}u", x_sym_end, tx, oy + u * 0.55)
    else:
        u = c.H * LV["scale"]
        cx = w / 2
        oy = p + 10
        marks = [("u", cx - c.W * LV["scale"] / 2 - 14, oy, cx - c.W * LV["scale"] / 2 - 14, oy + u)]
    lab = f'font-size="26" fill="var(--fg)" font-family="{esc(c.fam["mono"])}"'
    g = ""
    for t_, x1, y1, x2, y2 in marks:
        g += (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="var(--fg)" stroke-width="1.2"/>'
              f'<text x="{(x1 + x2) / 2 + (8 if x1 == x2 else 0):.1f}" y="{(y1 + y2) / 2 + (4 if x1 == x2 else -6):.1f}" {lab}>{esc(t_)}</text>')
    if kind == "horizontal":
        t_, gx1, gx2, gy = gap_mark
        g += (f'<line x1="{gx1:.1f}" y1="{gy:.1f}" x2="{gx2:.1f}" y2="{gy:.1f}" stroke="var(--fg)" stroke-width="1.2"/>'
              f'<text x="{gx1 - 62:.1f}" y="{gy - 8:.1f}" {lab}>{esc(t_)}</text>')
    pad = u
    vb = f"{-pad - 20:.0f} {-pad - 20:.0f} {w + 2 * pad + 40:.0f} {h + 2 * pad + 40:.0f}"
    prot = (f'<rect x="{-pad:.1f}" y="{-pad:.1f}" width="{w + 2 * pad:.1f}" height="{h + 2 * pad:.1f}" fill="none" stroke="var(--muted)" stroke-width="1.4" stroke-dasharray="6 6"/>'
            f'<rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="var(--line)" stroke-width="1"/>')
    return (f'<svg viewBox="{vb}" role="img" aria-label="Modulação da assinatura {kind}: u é a altura do pico, a área de proteção é 1u em todos os lados">'
            f'{prot}{body}{g}</svg>')


def modulation_notes(c, kind):
    """The measures of a lockup in fractions of u, as text for the caption."""
    if kind == "horizontal":
        u = c.H
        return (f"Símbolo e nome a {LH['gap'] / u:g}u. Nome {LH['name'] / u:g}u, descritor {LH['desc'] / u:.2f}u, linha {c.sw * LH['rule'] / u:.2f}u. Proteção 1u em todos os lados.")
    u = c.H * LV["scale"]
    return (f"Nome {LV['name'] / u:.2f}u, descritor {LV['desc'] / u:.2f}u, linha {c.sw * LV['rule'] * LV['scale'] / u:.2f}u. Proteção 1u em todos os lados.")


def wordmark_construction_svg(c):
    """The name with baseline, x-height and cap-height guides from the ratios the source declares."""
    wm = c.b["wordmark"]
    size, base = 100, 150
    w = c.est(c.name, size, "headline")
    ink = c.t(POL["positive"][0])
    cap, xh = wm["cap_height_ratio"], wm["x_height_ratio"]
    lab = f'font-size="12" fill="var(--muted)" font-family="{esc(c.fam["mono"])}"'
    guides = ""
    for yv, name in ((base, "linha de base"), (base - xh * size, f"altura do x {xh:g}"), (base - cap * size, f"altura da caixa alta {cap:g}")):
        guides += (f'<line x1="0" y1="{yv:.1f}" x2="{w + 30:.1f}" y2="{yv:.1f}" stroke="var(--muted)" stroke-width="1" stroke-dasharray="4 5"/>'
                   f'<text x="{w + 34:.1f}" y="{yv + 4:.1f}" {lab}>{esc(name)}</text>')
    txt = c.text(10, base, c.name, size, ink, c.t(POL["positive"][2]), "headline", 500, tl=w, logo=True)
    return (f'<svg viewBox="0 0 {w + 230:.0f} {base + 40}" role="img" aria-label="Construção do nome {esc(c.name)}: linha de base, altura do x e altura da caixa alta">'
            f'{guides}{txt}</svg>')


def matrix_cell(c, pol, bg_hex, w=64, h=40):
    """A small sample of the symbol in the ink of a polarity on a background."""
    sc = (w - 20) / c.W
    ink = c.t(POL[pol][0])
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Amostra de símbolo {pol}">'
            f'<rect width="{w}" height="{h}" rx="6" fill="{bg_hex}"/>' + sym(c, ink, 10, (h - c.H * sc) / 2, sc) + "</svg>")


def seal_g(c, pol, uid="a", size=300):
    ink, acc, bg = POL[pol]
    s = size / 300.0
    sc = 150.0 / c.W
    ox, oy = 75, 150 - c.H * sc * 0.45
    top = c.name.upper()
    d_top = "M 35,150 A 115,115 0 0 1 265,150"          # text sits outside this baseline, inside the band 103..137
    d_bot = "M 22,150 A 128,128 0 0 0 278,150"          # text hangs inside this baseline, same band
    ring = (f'<circle cx="150" cy="150" r="140" fill="none" stroke="{c.t(acc)}" stroke-width="5"/>'
            f'<circle cx="150" cy="150" r="102" fill="none" stroke="{c.t(ink)}" stroke-width="1.5"/>')
    fam = esc(c.fam["body"])
    txt = (f'<defs><path id="seal-top-{uid}" d="{d_top}"/><path id="seal-bot-{uid}" d="{d_bot}"/></defs>'
           f'<text font-family="{fam}" font-size="20" font-weight="600" letter-spacing="5" fill="{c.t(ink)}" data-bg="{c.t(bg)}" data-size="20" data-exempt="logotype">'
           f'<textPath href="#seal-top-{uid}" startOffset="50%" text-anchor="middle">{esc(top)}</textPath></text>'
           f'<text font-family="{fam}" font-size="16" font-weight="600" letter-spacing="3" fill="{c.t(ink)}" data-bg="{c.t(bg)}" data-size="16" data-exempt="logotype">'
           f'<textPath href="#seal-bot-{uid}" startOffset="50%" text-anchor="middle">{esc(c.desc.upper())}</textPath></text>')
    return f'<g transform="scale({s:.4f})">{ring}{txt}{sym(c, c.t(ink), ox, oy, sc)}</g>'


def seal_svg(c, pol):
    return svg(300, 300, seal_g(c, pol, pol), f"{c.name}, selo, versão {pol}")


def favicon_svg(c):
    sc = 44.0 / c.W
    return svg(64, 64, f'<rect width="64" height="64" rx="14" fill="{c.t("Cume_50")}"/>' + sym(c, c.t("Neblina"), 10, 32 - c.H * sc * 0.45, sc),
               f"{c.name}, ícone do site")


def animated_svg(c):
    ms = c.b["motion"]["logo_animation"]["duration_ms"]
    ease = c.b["motion"]["logo_animation"]["easing"]
    L = round(polyline_length(c.pts))
    x, y, w, h = sym_box(c)
    css = (f"@keyframes draw{{from{{stroke-dashoffset:{L}}}to{{stroke-dashoffset:0}}}}"
           f".ln{{stroke-dasharray:{L};stroke-dashoffset:0;animation:draw {ms}ms {ease} 1 both}}"
           f"@media (prefers-reduced-motion: reduce){{.ln{{animation:none}}}}")
    body = f"<style>{css}</style>" + sym(c, c.t("Cume_50"), extra=' class="ln"')
    return svg(w, h, body, f"{c.name}, símbolo animado", vb=f"{x:.2f} {y:.2f} {w:.2f} {h:.2f}")


# ------------------------------------------------------------ elements
def layers(c, w, h, top, lines, base_scale, stroke, fill, line_color, gap_ratio, width_ratio=1.0):
    """Layered contour lines: the symbol's own polyline, repeated, each layer hiding the part of the one behind it."""
    out = []
    gap = gap_ratio * c.H * base_scale
    for i in range(lines):
        sc = base_scale * (1 - 0.045 * i)
        yb = top + i * gap
        pts, x = [], -((i * 37) % max(1, int(c.W * sc)))
        while x < w + 20:
            for j, (px, py) in enumerate(c.pts):
                if j == 0 and pts:
                    continue
                pts.append((x + px * sc, yb - py * sc))
            x += c.W * sc
        d = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        out.append(f'<polygon points="{d} {w + 40},{h + 20} -40,{h + 20}" fill="{fill}" stroke="none"/>'
                   f'<polyline points="{d}" fill="none" stroke="{line_color}" stroke-width="{stroke * sc / base_scale:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')
    return "".join(out)


def pattern_svg(c, dark):
    w, h = 1200, 800
    bg, ln = ("Cume_70", "Cume_50") if dark else ("Neblina", "Cume_30")
    n = c.b["elements"]["pattern"]["lines"]
    gr = c.b["elements"]["pattern"]["gap_ratio"]
    body = f'<rect width="{w}" height="{h}" fill="{c.t(bg)}"/>' + layers(c, w, h, 250, n, 1.25, 2.2, c.t(bg), c.t(ln), gr)
    return svg(w, h, body, f"{c.name}, padrão de linhas de nível, {'escuro' if dark else 'claro'}")


def divider_svg(c):
    w, h = 800, 44
    return svg(w, h, f'<rect width="{w}" height="{h}" fill="{c.t("Neblina")}"/>' + layers(c, w, h, 38, 1, 0.26, 2.0, c.t("Neblina"), c.t("Cume_30"), 0), f"{c.name}, divisor")


def _ridge_picto(c, col):
    sc = 20.0 / c.W
    return f'<polyline points="{polyline(c.pts, c.H, 2.0, 12.0 - c.H * sc / 2, sc)}" stroke="{col}"/>'


PICTO = {
    "ridge": _ridge_picto,
    "lot": lambda c, col: f'<rect x="4" y="5" width="16" height="14" rx="2" stroke="{col}"/><path d="M8 10 H16 M8 14 H13" stroke="{col}"/>',
    "altitude": lambda c, col: f'<path d="M12 20 V6 M7.5 10.5 L12 6 L16.5 10.5 M5 20 H19" stroke="{col}"/>',
    "time": lambda c, col: f'<circle cx="12" cy="12" r="8" stroke="{col}"/><path d="M12 7 V12 L15.5 14" stroke="{col}"/>',
    "gift": lambda c, col: (f'<rect x="4" y="10" width="16" height="10" rx="1.5" stroke="{col}"/><rect x="3" y="7" width="18" height="3.5" rx="1" stroke="{col}"/>'
                            f'<path d="M12 7 V20 M12 7 C12 4 8 3.5 8 5.5 C8 7 10 7 12 7 M12 7 C12 4 16 3.5 16 5.5 C16 7 14 7 12 7" stroke="{col}"/>'),
    "origin": lambda c, col: (f'<path d="M12 21 C12 21 5 14.8 5 10 A7 7 0 0 1 19 10 C19 14.8 12 21 12 21 Z" stroke="{col}"/>'
                              f'<path d="M8.8 11.8 L10.6 9 L12 11 L13.4 9.6 L15.2 11.8" stroke="{col}"/>'),
}


def picto_svg(c, pid, name):
    col = c.t("Cume_50")
    body = f'<g fill="none" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">{PICTO[pid](c, col)}</g>'
    return svg(24, 24, body, f"{c.name}, pictograma {name}")


def palette_svg(c):
    fams = c.b_fams
    w, rowh = 1200, 190
    h = 120 + len(fams) * rowh + 220
    body = [f'<rect width="{w}" height="{h}" fill="{c.t("Neblina")}"/>',
            c.text(60, 80, f"Paleta {c.name}", 44, c.t("Tinta"), c.t("Neblina"), "headline", 400)]
    y = 130
    for f in fams:
        body.append(c.text(60, y + 24, f"{f['pt_name']} {f['universe']}", 24, c.t("Tinta"), c.t("Neblina"), "body", 600))
        for i, (s, d) in enumerate(f["steps"].items()):
            x = 60 + i * 152
            fg = c.t("Tinta") if _lum_pick(c, d["hex"]) else c.t("Branco")
            bgn = d["hex"]
            body.append(f'<rect x="{x}" y="{y + 40}" width="140" height="110" rx="10" fill="{d["hex"]}"/>')
            body.append(c.text(x + 12, y + 108, f"{s}", 26, fg, bgn, "body", 700))
            body.append(c.text(x + 12, y + 134, d["hex"], 17, fg, bgn, "mono", 500))
        y += rowh
    body.append(c.text(60, y + 24, "Neutros", 24, c.t("Tinta"), c.t("Neblina"), "body", 600))
    for i, n in enumerate(c.b["colour"]["neutrals"]):
        x = 60 + i * 152
        fg = c.t("Tinta") if _lum_pick(c, n["hex"]) else c.t("Branco")
        body.append(f'<rect x="{x}" y="{y + 40}" width="140" height="110" rx="10" fill="{n["hex"]}" stroke="{c.t("Cume_30")}" stroke-width="1"/>')
        body.append(c.text(x + 12, y + 100, n["name"], 24, fg, n["hex"].upper(), "body", 700))
        body.append(c.text(x + 12, y + 134, n["hex"].upper(), 17, fg, n["hex"].upper(), "mono", 500))
    return svg(w, h, "".join(body), f"{c.name}, folha de paleta")


def _lum_pick(c, hexv):
    from _ecolib import contrast
    return contrast(hexv, c.t("Tinta")) >= contrast(hexv, c.t("Branco"))


# ------------------------------------------------------------ applications
def nested(c, markup, x, y, s):
    return f'<g transform="translate({x:g},{y:g}) scale({s:g})">{markup}</g>'


def app_bag(c):
    w, h = 600, 900
    bg = c.t("Cume_50")
    body = [f'<rect width="{w}" height="{h}" fill="{bg}"/>', layers(c, w, h, 700, 5, 1.1, 2.0, bg, c.t("Cume_60"), c.b["elements"]["pattern"]["gap_ratio"])]
    body.append(nested(c, seal_g(c, "negative", "bag", 300), 190, 58, 0.73))
    body.append(c.text(300, 400, c.name, 86, c.t("Neblina"), bg, "headline", 500, "middle", tl=c.est(c.name, 86, "headline")))
    body.append(c.text(300, 448, c.desc, 22, c.t("Cume_10"), bg, "body", 600, "middle", ls=3.4, tl=c.est(c.desc, 22, "body", 3.4), upper=True))
    body.append(c.text(300, 520, c.tag, 30, c.t("Cume_10"), bg, "headline", 400, "middle", italic=True, tl=c.est(c.tag, 30, "headline")))
    body.append(f'<rect x="0" y="600" width="{w}" height="84" fill="{c.t("Vale_50")}"/>')
    body.append(c.text(300, 654, "Lote 12 · Mantiqueira", 26, c.t("Branco"), c.t("Vale_50"), "body", 600, "middle", ls=2.4, tl=c.est("Lote 12 · Mantiqueira", 26, "body", 2.4), upper=True))
    body.append(c.text(40, 850, "250 g", 44, c.t("Cume_10"), bg, "headline", 400))
    body.append(c.text(560, 846, "Feito em lotes pequenos", 22, c.t("Cume_10"), bg, "body", 400, "end"))
    return svg(w, h, "".join(body), f"{c.name}, etiqueta da embalagem de 250 gramas")


def app_card_front(c):
    w, h = 1050, 600
    bg = c.t("Neblina")
    m, lw, lh = lockup_h(c, "positive")
    s = 0.82
    body = (f'<rect width="{w}" height="{h}" fill="{bg}"/>' + nested(c, m, 90, (h - lh * s) / 2 - 20, s)
            + c.text(90, 540, "serrafina.example", 26, c.t("Cume_50"), bg, "body", 500))
    return svg(w, h, body, f"{c.name}, cartão de visita, frente")


def app_card_back(c):
    w, h = 1050, 600
    bg = c.t("Cume_50")
    body = (f'<rect width="{w}" height="{h}" fill="{bg}"/>' + layers(c, w, h, 470, 6, 1.5, 2.0, bg, c.t("Cume_60"), c.b["elements"]["pattern"]["gap_ratio"])
            + c.text(90, 220, "Ana", 70, c.t("Neblina"), bg, "headline", 400)
            + c.text(90, 270, "Fundadora", 28, c.t("Cume_10"), bg, "body", 500)
            + c.text(90, 400, "marca@serrafina.example", 26, c.t("Cume_10"), bg, "body", 400)
            + c.text(90, 442, "Serra da Mantiqueira", 26, c.t("Cume_10"), bg, "body", 400))
    return svg(w, h, body, f"{c.name}, cartão de visita, verso")


def app_social(c):
    w = h = 1080
    bg = c.t("Cume_70")
    m, lw, lh = lockup_h(c, "negative")
    body = (f'<rect width="{w}" height="{h}" fill="{bg}"/>' + layers(c, w, h, 640, 7, 2.0, 3.0, bg, c.t("Cume_60"), c.b["elements"]["pattern"]["gap_ratio"])
            + c.text(90, 330, "O tempo é", 118, c.t("Neblina"), bg, "headline", 300) + c.text(90, 460, "o ingrediente.", 118, c.t("Neblina"), bg, "headline", 300)
            + c.text(990, 112, "Lote 12", 28, c.t("Cume_10"), bg, "body", 600, "end", ls=2.0, upper=True)
            + nested(c, m, 90, 940, 0.42))
    return svg(w, h, body, f"{c.name}, post quadrado de rede social")


def app_site(c):
    w, h = 1440, 800
    bg = c.t("Neblina")
    m, lw, lh = lockup_h(c, "positive")
    b = [f'<rect width="{w}" height="{h}" fill="{bg}"/>', nested(c, m, 80, 34, 0.42)]
    for i, lk in enumerate(["Lotes", "Assinatura", "Presentes", "Origem"]):
        b.append(c.text(640 + i * 150, 78, lk, 22, c.t("Cume_50"), bg, "body", 500))
    b.append(f'<rect x="1190" y="44" width="170" height="56" rx="28" fill="{c.t("Vale_50")}"/>')
    b.append(c.text(1275, 80, "Entrar", 22, c.t("Branco"), c.t("Vale_50"), "body", 600, "middle"))
    b.append(c.text(80, 330, "Feito devagar,", 96, c.t("Tinta"), bg, "headline", 300))
    b.append(c.text(80, 436, "no alto da serra.", 96, c.t("Tinta"), bg, "headline", 300))
    b.append(c.text(80, 510, "Chocolate de altitude em lotes pequenos.", 26, c.t("Tinta"), bg, "body", 400))
    b.append(c.text(80, 548, "Cada barra diz de onde veio e quanto tempo levou.", 26, c.t("Tinta"), bg, "body", 400))
    b.append(f'<rect x="80" y="606" width="310" height="70" rx="35" fill="{c.t("Vale_50")}"/>')
    b.append(c.text(235, 650, "Ver o lote do mês", 26, c.t("Branco"), c.t("Vale_50"), "body", 600, "middle"))
    b.append(c.text(430, 650, "Como fazemos", 24, c.t("Cume_50"), bg, "body", 600))
    b.append(f'<defs><linearGradient id="duo-site" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="{c.t("Cume_70")}"/><stop offset="1" stop-color="{c.t("Cume_30")}"/></linearGradient>'
             f'<clipPath id="clip-site"><rect x="800" y="130" width="560" height="580" rx="24"/></clipPath></defs>')
    b.append(f'<rect x="800" y="130" width="560" height="580" rx="24" fill="url(#duo-site)"/>')
    b.append(f'<g clip-path="url(#clip-site)">' + layers(c, 1440, 760, 470, 4, 1.6, 2.5, c.t("Cume_70"), c.t("Cume_50"), c.b["elements"]["pattern"]["gap_ratio"])+ "</g>")
    b.append(c.text(830, 690, "Fotografia: lote, mãos e luz da manhã (ilustrativo)", 20, c.t("Cume_10"), c.t("Cume_70"), "body", 500))
    return svg(w, h, "".join(b), f"{c.name}, página inicial do site")


def app_box(c):
    w = h = 800
    bg = c.t("Neblina")
    body = (f'<rect width="{w}" height="{h}" fill="{bg}"/><defs><clipPath id="box-clip"><rect x="43" y="43" width="714" height="714"/></clipPath></defs>'
            + '<g clip-path="url(#box-clip)">' + layers(c, w, h, 770, 3, 0.7, 2.0, bg, c.t("Cume_30"), c.b["elements"]["pattern"]["gap_ratio"]) + "</g>"
            + f'<rect x="40" y="40" width="720" height="720" fill="none" stroke="{c.t("Cume_50")}" stroke-width="3"/>'
            + nested(c, seal_g(c, "positive", "box", 300), 220, 150, 1.2)
            + c.text(400, 560, "Lote 12", 30, c.t("Cume_50"), bg, "body", 600, "middle", ls=3.0, upper=True)
            + c.text(400, 612, c.tag, 32, c.t("Tinta"), bg, "headline", 400, "middle", italic=True, tl=c.est(c.tag, 32, "headline")))
    return svg(w, h, body, f"{c.name}, tampa da caixa de presente")


def app_letter(c):
    w, h = 794, 1123
    bg = c.t("Branco")
    m, lw, lh = lockup_h(c, "positive")
    lines = ["Segue o relatório do lote 12, que descansou por três semanas antes de ser embalado.",
             "O ponto de derretimento ficou em 34 graus e o final lembra amêndoa.",
             "Combinamos a entrega para a próxima semana, no endereço de sempre."]
    b = [f'<rect width="{w}" height="{h}" fill="{bg}"/>', nested(c, m, 60, 56, 0.4),
         c.text(734, 84, "marca@serrafina.example", 16, c.t("Cume_50"), bg, "body", 500, "end"),
         c.text(60, 300, "Prezada Ana,", 20, c.t("Tinta"), bg, "body", 500)]
    for i, ln in enumerate(lines):
        b.append(c.text(60, 348 + i * 34, ln, 18, c.t("Tinta"), bg, "body", 400))
    b.append(c.text(60, 500, "Com atenção,", 18, c.t("Tinta"), bg, "body", 400))
    b.append(c.text(60, 534, "Equipe Serra Fina", 18, c.t("Tinta"), bg, "body", 500))
    b.append(layers(c, w, h, 1060, 1, 0.45, 1.5, bg, c.t("Cume_30"), 0))
    b.append(c.text(60, 1096, f"{c.name} · {c.desc} · Serra da Mantiqueira", 14, c.t("Cume_50"), bg, "body", 500))
    return svg(w, h, "".join(b), f"{c.name}, papel timbrado")


APP_FILES = {
    "bag": [("App-Bag-Label", app_bag)],
    "card": [("App-Card-Front", app_card_front), ("App-Card-Back", app_card_back)],
    "social": [("App-Social-Post", app_social)],
    "site": [("App-Site-Hero", app_site)],
    "box": [("App-Gift-Box-Lid", app_box)],
    "letterhead": [("App-Letterhead", app_letter)],
}

if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
