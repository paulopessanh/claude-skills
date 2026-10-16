#!/usr/bin/env python3
"""usage_rules.py — rules of use for light mode, dark mode and brand colour as background.

A brand has one or two main colours. When one of them becomes the background, the mark and the text cannot stay as
they were: the mark turns white or a light version of the brand, and text takes a colour that reads. This tool turns
that behaviour into a table that anyone can follow, computed from the palette and not from taste.

It takes the tonal scales, the neutral scale and the three families. For each background it settles:
  mark         the colour of the logo and of the main symbol
  title        brand-coloured text (primary family), when it passes
  text         strong, body and muted text, the softest neutral that still passes
  link         the secondary family, when it passes
  accent       the accent family as a graphic or a key number, when it passes 3:1
  avoid        the brand colours that fail on this background, with their ratio
and writes the approved fg/bg pairs in the shape of brand-source.v2 (fg, bg, declared).

Backgrounds:
  light   page, card (a white with a trace of the brand hue), soft highlight (a light tint of the primary)
  dark    page, surface, brand deep (a deep shade of the primary)
  colour  the primary, the secondary and the accent as full backgrounds

Contrast: text 4.5:1 with a 5% margin, body 7:1, graphics 3:1, mark 3:1 (4.5:1 when it is a brand step on a dark page).
Rules:
  NO_MARK    BLOCK  no colour reaches 3:1 for the mark on a background that the table offers
  NO_TEXT    WARN   no neutral reaches 4.5:1 for muted text on a background
  ACCENT_OUT WARN   the accent family fails 3:1 on a background: it may not appear there
Exit: 0 ok | 1 input error | 2 warnings | 4 blocked. Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402


def fam(scales, name):
    return next(f for f in scales["families"] if f["family"] == name)


def pool(f, kinds=("base", "Tint", "Tone", "Shade")):
    out = []
    for k in kinds:
        out += [f["base"]] if k == "base" else f["scales"][k]["steps"]
    return out


def closest(cands, base_hex, bg, minc):
    ok = [c for c in cands if cl.contrast(c["hex"], bg) >= minc]
    return min(ok, key=lambda c: cl.oklab_dist(c["hex"], base_hex)) if ok else None


def softest(cands, bg, minc):
    ok = [c for c in cands if cl.contrast(c["hex"], bg) >= minc]
    return min(ok, key=lambda c: cl.contrast(c["hex"], bg)) if ok else None


def brief(c, bg):
    return {"token": c["token"], "hex": c["hex"], "contrast": round(cl.contrast(c["hex"], bg), 2),
            "cmyk_approx": c["cmyk_approx"]} if c else None


def backgrounds(scales, neutral, P, S, A):
    nl, nd = neutral["roles"]["light"], neutral["roles"]["dark"]
    steps = {s["token"]: s for s in neutral["steps"]}
    ink = steps[nl["text_strong"]["token"]]
    tints = P["scales"]["Tint"]["steps"]
    soft = next((t for t in tints if cl.contrast(ink["hex"], t["hex"]) >= 7.0), tints[-1])
    deep = P["scales"]["Shade"]["steps"][2]
    return [
        ("light", "Fundo claro padrão", {"token": nl["page"]["token"], "hex": nl["page"]["hex"], **{"cmyk_approx": nl["page"]["cmyk_approx"]}}),
        ("light", "Cartão sobre o fundo claro", {"token": nl["surface"]["token"], "hex": nl["surface"]["hex"], "cmyk_approx": nl["surface"]["cmyk_approx"]}),
        ("light", "Destaque suave", soft),
        ("dark", "Fundo escuro padrão", {"token": nd["page"]["token"], "hex": nd["page"]["hex"], "cmyk_approx": nd["page"]["cmyk_approx"]}),
        ("dark", "Superfície escura", {"token": nd["surface"]["token"], "hex": nd["surface"]["hex"], "cmyk_approx": nd["surface"]["cmyk_approx"]}),
        ("dark", "Escuro de marca", deep),
        ("colour", f"{P['family']} como fundo", P["base"]),
        ("colour", f"{S['family']} como fundo", S["base"]),
        ("colour", f"{A['family']} como fundo", A["base"]),
    ]


def build(scales, neutral, p, s, a, roles):
    P, S, A = fam(scales, p), fam(scales, s), fam(scales, a)
    white = {"token": neutral["roles"]["light"]["surface"]["token"], "hex": neutral["roles"]["light"]["surface"]["hex"],
             "cmyk_approx": neutral["roles"]["light"]["surface"]["cmyk_approx"]}
    nsteps = [white] + [{"token": x["token"], "hex": x["hex"], "cmyk_approx": x["cmyk_approx"]} for x in neutral["steps"]]
    findings, rows, pairs = [], [], []
    for mode, label, bgc in backgrounds(scales, neutral, P, S, A):
        bg = bgc["hex"]
        dark_like = cl.oklch(bg)[0] < 0.5
        if mode == "light":
            mark = closest([P["base"]] + P["scales"]["Shade"]["steps"] + P["scales"]["Tint"]["steps"], P["base"]["hex"], bg, 3.0)
            mark_note = "Marca na cor base da principal."
        elif mode == "dark":
            mark = closest([P["base"]] + P["scales"]["Tint"]["steps"], P["base"]["hex"], bg, 4.5)
            mark_note = "Marca na versão clara da principal. A cor base some neste fundo."
        else:
            mark = closest([white], P["base"]["hex"], bg, 4.5) or closest(P["scales"]["Tint"]["steps"][::-1], white["hex"], bg, 4.5)
            mark_note = "A cor virou fundo: a marca passa para branco tingido, ou para o tint mais claro."
        if mark is None:
            findings.append(("BLOCK", "NO_MARK", f"{label}: no colour reaches the mark contrast. Do not offer this background."))
        title = closest(pool(P, ("base", "Shade", "Tint", "Tone")), P["base"]["hex"], bg, 4.5 * 1.05)
        text_pool = nsteps
        strong = max((c for c in text_pool), key=lambda c: cl.contrast(c["hex"], bg))
        body = softest(text_pool, bg, 7.0)
        muted = softest(text_pool, bg, 4.5 * 1.05)
        if muted is None:
            findings.append(("WARN", "NO_TEXT", f"{label}: no neutral reaches 4.5:1 for muted text."))
        link = closest(pool(S, ("base", "Shade", "Tint", "Tone")), S["base"]["hex"], bg, 4.5 * 1.05)
        acc = closest(pool(A, ("base", "Shade", "Tint")), A["base"]["hex"], bg, 3.0)
        if acc is None:
            findings.append(("WARN", "ACCENT_OUT", f"{label}: the {A['family']} family fails 3:1 here, so the accent may not appear on this background."))
        text_note = None
        if body is None:
            r = cl.contrast(strong["hex"], bg)
            text_note = (f"Sem texto corrido neste fundo: o melhor par é {strong['token']} com {int(r * 100) / 100}:1. "
                         "Use só título grande (24 px, ou 19 px em negrito, ou 18 pt) e rótulo curto, nunca parágrafo."
                         if r >= 3.0 else "Nenhum texto passa neste fundo. Não ofereça este fundo para texto.")
        avoid = []
        for f in (P, S, A):
            r = cl.contrast(f["base"]["hex"], bg)
            if r < 3.0:
                avoid.append({"token": f["base"]["token"], "hex": f["base"]["hex"], "contrast": round(r, 2),
                              "why": "Abaixo de 3:1. Não serve de texto, ícone ou traço neste fundo."})
        row = {"mode": mode, "background": label, "bg": {"token": bgc["token"], "hex": bg, "cmyk_approx": bgc["cmyk_approx"]},
               "mark": brief(mark, bg), "mark_rule": mark_note, "brand_title": brief(title, bg),
               "text_strong": brief(strong, bg), "text_body": brief(body, bg), "text_muted": brief(muted, bg),
               "link": brief(link, bg), "accent": brief(acc, bg), "text_note": text_note, "avoid": avoid,
               "leans": "escuro" if dark_like else "claro"}
        rows.append(row)
        for role, c in (("mark", mark), ("brand_title", title), ("text_body", body), ("text_muted", muted), ("link", link)):
            if c:
                r = cl.contrast(c["hex"], bg)
                pairs.append({"fg": c["token"], "bg": bgc["token"], "role": role, "ratio": int(r * 100) / 100,
                              "declared": "AAA" if r >= 7 else ("AA" if r >= 4.5 else "AA-large")})
    switch = []
    if roles:
        by = {}
        for r in roles["roles"]:
            by.setdefault(r["role"], {})[r["mode"]] = r
        for role, m in by.items():
            if "light" in m and "dark" in m:
                switch.append({"role": role, "label": m["light"]["label"],
                               "light": {"token": m["light"]["token"], "hex": m["light"]["hex"]},
                               "dark": {"token": m["dark"]["token"], "hex": m["dark"]["hex"]}})
    verdict = "BLOCKED" if any(f[0] == "BLOCK" for f in findings) else ("CAVEATS" if findings else "CLEAN")
    return {"sigla": neutral["sigla"], "families": {"primary": p, "secondary": s, "accent": a},
            "backgrounds": rows, "approved_pairs": pairs, "mode_switch": switch,
            "rules": [
                "Fundo claro: a marca usa a cor base da principal. Texto em neutro escuro. O acento aparece pequeno e raro.",
                "Fundo escuro: a marca usa a versão clara da principal, nunca a cor base. Superfícies sobem em claridade (superfície, depois elevada) em vez de usar sombra.",
                "Cor da marca como fundo: a marca passa para branco tingido. O texto é branco tingido ou o neutro mais claro que passa. A mesma cor não carrega texto e fundo ao mesmo tempo.",
                "Dark mode não é inverter. Reconfira cada par na tabela: os pares aprovados são os únicos garantidos.",
                "Cada fundo lista o que evitar. Se uma cor da paleta está em 'avoid' para aquele fundo, ela não entra como texto, ícone ou traço lá.",
                "Em impressão, o fundo escuro de marca é cor chapada com prova. Texto claro abaixo de 8 pt sobre cor chapada engrossa e fecha: use corpo maior ou peso maior."],
            "findings": [{"level": x, "code": y, "message": z} for x, y, z in findings],
            "verdict": verdict, "note": "CMYK values are approximate. PMS needs a printed match."}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scales", required=True)
    ap.add_argument("--neutral", required=True)
    ap.add_argument("--primary", required=True)
    ap.add_argument("--secondary", required=True)
    ap.add_argument("--accent", required=True)
    ap.add_argument("--roles", help="output of role_map.py, for the light to dark switch table")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        with open(a.scales, encoding="utf-8") as f:
            scales = json.load(f)
        with open(a.neutral, encoding="utf-8") as f:
            neutral = json.load(f)
        roles = None
        if a.roles:
            with open(a.roles, encoding="utf-8") as f:
                roles = json.load(f)
        res = build(scales, neutral, a.primary, a.secondary, a.accent, roles)
    except (OSError, ValueError, KeyError, StopIteration) as e:
        print(f"error: {e!r}", file=sys.stderr)
        return 1
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)
    return {"BLOCKED": 4, "CAVEATS": 2, "CLEAN": 0}[res["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
