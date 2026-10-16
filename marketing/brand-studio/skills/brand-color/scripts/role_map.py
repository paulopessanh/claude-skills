#!/usr/bin/env python3
"""role_map.py — complementary palette: which colour does which job, in light mode and dark mode.

Input is the output of tonal_scales.py (every family with its base, tints, tones and shades) and three names:
the primary, the secondary and the accent family. Plus the light and the dark background of the brand.
For every role the tool picks, from the right pool, the step closest to the brand colour that still passes the
contrast the role needs. Closest to the brand colour keeps identity; the contrast limit keeps it readable.

Roles and the contrast each one needs against the background it sits on:
  brand_mark        primary fill                          3.0  (graphic object, WCAG 1.4.11)
  title             primary, base or shade                4.5
  subtitle          primary, tone or shade                4.5
  tagline           secondary, base, tone or shade        4.5
  icon              primary, any step                     3.0
  hairline          primary, tone or tint                 3.0  (a hairline that carries meaning); decorative lines may be lighter
  key_number        accent, base or shade                 3.0  large type only (24 px, or 19 px bold, or 18 pt print)
  link              secondary, base or shade              4.5  always underlined, never colour alone
  button            accent fill, label white or ink       4.5  label on fill; the fill itself needs 3.0 on the background or an edge
  highlight_bar     primary tint fill, text on it         4.5
  sheen             lightest tint                         decorative, never carries text
Also: mark_on_primary, the colour of the mark when the primary becomes the background (white or the lightest tint).

Rules:
  NO_STEP    WARN  no step of the pool passes: the tool fell back to white or ink and says so
  SAME_ROLE  WARN  title and link resolve to the same hex: they will not read as different jobs

CMYK is approximate. PMS needs a printed match. Exit: 0 ok | 1 input error | 2 warnings.
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402

WHITE = "#FFFFFF"

ROLES = [
    # id, label, family key, pools, min contrast, rule, never, print note
    ("brand_mark", "Marca e assinatura", "primary", ("base",), 3.0,
     "Cor base da família principal. Em fundo escuro a marca troca para a versão clara.",
     "Recolorir a marca fora da paleta. Usar sobre fundo com menos de 3:1.", "Spot da principal ou quadricromia aprovada em prova."),
    ("title", "Títulos", "primary", ("base", "Shade"), 4.5,
     "Principal ou um shade dela.", "Cor de acento em título longo. Tint ou tone em título.", "Texto abaixo de 8 pt precisa de 100% de densidade."),
    ("subtitle", "Subtítulos", "primary", ("Tone", "Shade"), 4.5,
     "Um tone ou shade da principal, mais calmo que o título.", "Mesma cor do título (perde a hierarquia). Tint.", "Sem densidade parcial em corpo pequeno."),
    ("tagline", "Tagline", "secondary", ("base", "Tone", "Shade"), 4.5,
     "Família secundária. Separa a tagline do título e do subtítulo.", "Acento. Tint. Fundo com menos de 4,5:1.", "Em impressão sobre cor, testar em prova."),
    ("icon", "Ícones", "primary", ("base", "Shade", "Tone", "Tint"), 3.0,
     "Principal. Um único tom por ícone.", "Gradiente em ícone. Dois tons que se confundem.", "Traço mínimo de 0,5 pt."),
    ("hairline", "Linhas finas", "primary", ("Tone", "Tint", "Shade"), 3.0,
     "Tone ou tint da principal quando a linha tem sentido (separa, indica). Linha só decorativa pode ser mais clara.",
     "Preto puro. Tint com menos de 3:1 quando a linha carrega informação.", "Espessura mínima de 0,25 pt e sem tint abaixo de 40% de densidade."),
    ("key_number", "Número-chave", "accent", ("base", "Shade"), 3.0,
     "Acento. Só em tipo grande: 24 px, ou 19 px em negrito, ou 18 pt na impressão.", "Corpo de texto. Mais de um número-chave por tela sem hierarquia.", "Acima de 18 pt."),
    ("link", "Link", "secondary", ("base", "Shade"), 4.5,
     "Secundária, sempre sublinhado. A cor sozinha não basta.", "Link sem sublinhado. Mesma cor do título.", "Em impressão, sublinhado e URL visível."),
]


def pools(fam):
    out = {"base": [fam["base"]]}
    for k, s in fam["scales"].items():
        out[k] = s["steps"]
    return out


def choose(fam, kinds, bg, minc, base_hex):
    cand = []
    pl = pools(fam)
    for k in kinds:
        cand += pl.get(k, [])
    ok = [c for c in cand if cl.contrast(c["hex"], bg) >= minc]
    if not ok:
        return None
    return min(ok, key=lambda c: sum((x - y) ** 2 for x, y in zip(cl.oklab(c["hex"]), cl.oklab(base_hex))))


def row(role, label, mode, c, bg, rule, never, pnote, minc):
    return {"role": role, "label": label, "mode": mode, "token": c["token"], "hex": c["hex"],
            "cmyk_approx": c["cmyk_approx"], "on_background": bg,
            "contrast": round(cl.contrast(c["hex"], bg), 2), "needs": minc, "apca_lc": cl.apca(c["hex"], bg),
            "rule": rule, "never": never, "print_note": pnote}


def build(data, prim, sec, acc, bgl, bgd):
    fams = {f["family"]: f for f in data["families"]}
    for n in (prim, sec, acc):
        if n not in fams:
            raise KeyError(f"family not in scales: {n}")
    ink = data.get("ink", "#12161C")
    key = {"primary": fams[prim], "secondary": fams[sec], "accent": fams[acc]}
    findings, rows = [], []
    for mode, bg in (("light", bgl), ("dark", bgd)):
        for rid, label, fk, kinds, minc, rule, never, pnote in ROLES:
            fam = key[fk]
            # On a dark background a shade cannot carry colour: the pool swaps shades for tints.
            kk = tuple(dict.fromkeys("Tint" if (mode == "dark" and k == "Shade") else k for k in kinds))
            if rid == "brand_mark" and mode == "dark":
                kk, minc = ("base", "Tint"), 4.5
            # Text gets a 5% margin over the limit, so a screen or a print shift does not push it under.
            c = choose(fam, kk, bg, minc * 1.05 if minc >= 4.5 else minc, fam["base"]["hex"])
            if c is None:
                fb = WHITE if cl.contrast(WHITE, bg) >= minc else ink
                c = {"token": "fallback", "hex": fb, "cmyk_approx": cl.cmyk_approx(fb)}
                findings.append(("WARN", "NO_STEP", f"{label} in {mode} mode: no {fk} step reaches {minc}:1 on {bg}. Fell back to {fb}."))
            rows.append(row(rid, label, mode, c, bg, rule, never, pnote, minc))
        fill = key["accent"]["base"]
        lab = WHITE if cl.contrast(WHITE, fill["hex"]) >= cl.contrast(ink, fill["hex"]) else ink
        if cl.contrast(lab, fill["hex"]) < 4.5:
            findings.append(("WARN", "NO_STEP", f"Button label on {fill['hex']} stays under 4.5:1. Use a shade of the accent as the fill."))
        edge = cl.contrast(fill["hex"], bg)
        rows.append({"role": "button", "label": "Botão", "mode": mode, "token": fill["token"], "hex": fill["hex"],
                     "cmyk_approx": fill["cmyk_approx"], "on_background": bg, "label_color": lab,
                     "label_contrast": round(cl.contrast(lab, fill["hex"]), 2), "needs": 4.5,
                     "fill_vs_background": round(edge, 2), "edge_needed": edge < 3.0,
                     "rule": "Preenchimento com a cor de acento. Rótulo em branco ou tinta, com 4,5:1. Hover: um passo mais fundo no modo claro, um passo mais claro no modo escuro."
                             + (" O preenchimento não chega a 3:1 sobre este fundo: adicione contorno." if edge < 3.0 else ""),
                     "never": "Dois botões primários lado a lado. Rótulo sem contraste.", "print_note": "Botão é digital. Em impressão vira etiqueta ou selo."})
        pf = key["primary"]
        if mode == "light":
            lights = [s for s in pf["scales"]["Tint"]["steps"] if cl.contrast(ink, s["hex"]) >= 7.0]
            use = lights[0] if lights else pf["scales"]["Tint"]["steps"][-1]
            tl = ink
        else:
            use = pf["base"]
            tl = WHITE
        if cl.contrast(tl, use["hex"]) < 4.5:
            findings.append(("WARN", "NO_STEP", f"Highlight background {use['hex']} stays under 4.5:1 for its text in {mode} mode."))
        rows.append({"role": "highlight_bar", "label": "Barras e fundos de destaque", "mode": mode,
                     "token": use["token"], "hex": use["hex"], "cmyk_approx": use["cmyk_approx"],
                     "on_background": bg, "text_on_it": tl, "text_contrast": round(cl.contrast(tl, use["hex"]), 2),
                     "rule": "No modo claro, o tint mais próximo da principal em que o texto em tinta passa de 7:1. No modo escuro, a principal com texto branco.",
                     "never": "Tint com texto da mesma família. Mais de um fundo de destaque por área.", "print_note": "Sobre papel claro, 15 a 25% de densidade."})
        light = pf["scales"]["Tint"]["steps"][-1]
        rows.append({"role": "sheen", "label": "Brilho, reflexo e ponto de luz", "mode": mode,
                     "token": light["token"], "hex": light["hex"] if mode == "dark" else WHITE,
                     "cmyk_approx": light["cmyk_approx"], "on_background": bg,
                     "rule": "O tint mais claro da principal, como brilho. Decorativo, nunca carrega texto. No modo claro, branco com 60 a 90% de opacidade.",
                     "never": "Branco puro em fundo escuro grande. Brilho sobre texto.", "print_note": "Verniz localizado ou branco opaco, nunca meio-tom."})
    # Hierarchy: the title must stand apart from the subtitle, lighter on dark and deeper on light.
    pf = key["primary"]
    allp = [pf["base"]] + [s for k in ("Tint", "Tone", "Shade") for s in pf["scales"][k]["steps"]]
    allp.sort(key=lambda c: cl.oklch(c["hex"])[0])
    for mode, bg in (("light", bgl), ("dark", bgd)):
        t = next(r for r in rows if r["role"] == "title" and r["mode"] == mode)
        s = next(r for r in rows if r["role"] == "subtitle" and r["mode"] == mode)
        lt, lsub = cl.oklch(t["hex"])[0], cl.oklch(s["hex"])[0]
        if t["hex"] != s["hex"]:
            if (mode == "light" and lt > lsub) or (mode == "dark" and lt < lsub):
                keys = ("token", "hex", "cmyk_approx", "contrast", "apca_lc")
                for k in keys:
                    t[k], s[k] = s[k], t[k]
            continue
        ls = [cl.oklch(c["hex"])[0] for c in allp]
        i = next(j for j, c in enumerate(allp) if c["hex"] == s["hex"]) if any(c["hex"] == s["hex"] for c in allp) else None
        order = range(i + 1, len(allp)) if mode == "dark" else range(i - 1, -1, -1)
        alt = next((allp[j] for j in order if cl.contrast(allp[j]["hex"], bg) >= 4.5 * 1.05
                    and abs(ls[j] - ls[i]) >= 0.04), None) if i is not None else None
        if alt:
            t.update({"token": alt["token"], "hex": alt["hex"], "cmyk_approx": alt["cmyk_approx"],
                      "contrast": round(cl.contrast(alt["hex"], bg), 2), "apca_lc": cl.apca(alt["hex"], bg)})
        else:
            findings.append(("WARN", "SAME_ROLE", f"In {mode} mode title and subtitle resolve to the same colour and no neighbour step passes. Differ them by size and weight."))
    markc = [WHITE] + [s["hex"] for s in reversed(key["primary"]["scales"]["Tint"]["steps"])]
    mk = next((c for c in markc if cl.contrast(c, key["primary"]["base"]["hex"]) >= 3.0), WHITE)
    by = {(r["role"], r["mode"]): r["hex"] for r in rows}
    for mode in ("light", "dark"):
        if by.get(("title", mode)) == by.get(("link", mode)):
            findings.append(("WARN", "SAME_ROLE", f"In {mode} mode title and link resolve to the same colour. Change the secondary family or its step."))
    return {"brand": data["brand"], "families": {"primary": prim, "secondary": sec, "accent": acc},
            "backgrounds": {"light": bgl, "dark": bgd}, "roles": rows,
            "mark_on_primary": {"hex": mk, "contrast": round(cl.contrast(mk, key["primary"]["base"]["hex"]), 2),
                                "rule": "Quando a principal vira fundo, a marca passa para esta cor."},
            "findings": [{"level": a, "code": b, "message": c} for a, b, c in findings],
            "verdict": "CAVEATS" if findings else "CLEAN",
            "note": "CMYK values are approximate. PMS needs a printed match."}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scales", required=True, help="output of tonal_scales.py")
    ap.add_argument("--primary", required=True)
    ap.add_argument("--secondary", required=True)
    ap.add_argument("--accent", required=True)
    ap.add_argument("--bg-light", default="#FFFFFF")
    ap.add_argument("--bg-dark", default="#12161C")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        with open(a.scales, encoding="utf-8") as f:
            res = build(json.load(f), a.primary, a.secondary, a.accent, cl.norm_hex(a.bg_light), cl.norm_hex(a.bg_dark))
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)
    return 2 if res["verdict"] == "CAVEATS" else 0


if __name__ == "__main__":
    sys.exit(main())
