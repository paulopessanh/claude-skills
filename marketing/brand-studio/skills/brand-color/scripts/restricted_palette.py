#!/usr/bin/env python3
"""restricted_palette.py — restricted palette: status colours for dashboards, reports and tables.

Restricted means fenced: these colours say one thing (good, bad, careful, information, no change) and are never
brand colours. The tool builds five statuses, each with a strong colour (chart, icon), a text colour for light and for
dark backgrounds, a surface and a border, all passing contrast, and checks them for colour-blind readers.

Hues are fixed by what people expect: green 145, red 27, amber 75, blue 250. A status colour that people
cannot read at a glance is worse than no colour. Lightness is set apart on purpose, so the palette still
works in grayscale print and for readers who confuse red and green.

Rules:
  CVD_CONFUSION  WARN  two statuses fall under 0.06 in OKLab after a simulated deuteranopia, protanopia or tritanopia.
                       They are never used alone: every status also carries an icon and a word (WCAG 1.4.1)
  GRAY_GAP       WARN  positive and negative differ by less than 0.10 in lightness: they merge in grayscale print
  BRAND_CLASH    WARN  a brand colour sits within 25 degrees of a status hue, has chroma above 0.08 and lightness of 0.45
                       or more: it may be read as that status. Do not use it as a data colour next to the status
  NO_TEXT        WARN  no text step of a status reaches 4.5:1 on its background

CMYK is approximate. PMS needs a printed match. Colour-blind simulation is an approximation for planning.
Exit: 0 ok | 1 input error | 2 warnings. Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402

# key: (label, token word, hue, strong lightness, glyph, meaning)
STATUS = {
    "positive": ("Positivo", "Positivo", 145.0, 0.66, "✓", "Meta atingida, resultado bom, concluído."),
    "negative": ("Negativo", "Negativo", 27.0, 0.52, "✕", "Meta perdida, erro, risco que exige ação."),
    "warning": ("Alerta", "Alerta", 75.0, 0.82, "!", "Atenção, perto do limite, revisar."),
    "info": ("Informação", "Info", 250.0, 0.58, "i", "Nota, dica, estado neutro de interesse."),
}
ICONS_RULE = "Todo status leva ícone e palavra. A cor sozinha nunca basta (WCAG 1.4.1) e some na impressão em preto e branco."


def tone(L, C, h):
    return cl.oklch_to_hex(L, C, h)


def text_for(hue, bg, other, margin=1.05):
    """The lightest-touch text colour that passes 4.5:1 on bg and on the surface 'other'. Walks away from bg."""
    dark_bg = cl.oklch(bg)[0] < 0.5
    rng = [i / 100 for i in range(30, 96)] if dark_bg else [i / 100 for i in range(66, 14, -1)]
    for L in rng:
        hx = tone(L, 0.15, hue)
        if min(cl.contrast(hx, bg), cl.contrast(hx, other)) >= 4.5 * margin:
            return hx
    return None


def build(primary, sigla, bg_light, bg_dark, extra, neutral_hex):
    findings = []
    rows = {}
    for key, (label, word, hue, Ls, glyph, meaning) in STATUS.items():
        strong = tone(Ls, 0.17, hue)
        s_light, s_dark = tone(0.965, 0.025, hue), tone(0.27, 0.05, hue)
        t_light, t_dark = text_for(hue, bg_light, s_light), text_for(hue, bg_dark, s_dark)
        for name, v in (("light", t_light), ("dark", t_dark)):
            if v is None:
                findings.append(("WARN", "NO_TEXT", f"{label}: no text colour passes 4.5:1 on the {name} background."))
        t_light = t_light or "#000000"
        t_dark = t_dark or "#FFFFFF"
        rows[key] = {
            "label": label, "glyph": glyph, "meaning": meaning,
            "strong": {**cl.describe(strong), "token": f"{sigla}_Status_{word}_Forte"},
            "text_on_light": {**cl.describe(t_light), "token": f"{sigla}_Status_{word}_TextoClaro",
                              "contrast": round(cl.contrast(t_light, bg_light), 2)},
            "text_on_dark": {**cl.describe(t_dark), "token": f"{sigla}_Status_{word}_TextoEscuro",
                             "contrast": round(cl.contrast(t_dark, bg_dark), 2)},
            "surface_light": {**cl.describe(s_light), "token": f"{sigla}_Status_{word}_FundoClaro"},
            "surface_dark": {**cl.describe(s_dark), "token": f"{sigla}_Status_{word}_FundoEscuro"},
            "border_light": {**cl.describe(tone(0.80, 0.07, hue)), "token": f"{sigla}_Status_{word}_BordaClara"},
            "border_dark": {**cl.describe(tone(0.42, 0.08, hue)), "token": f"{sigla}_Status_{word}_BordaEscura"},
            "text_contrast_on_surface_light": round(cl.contrast(t_light, s_light), 2),
            "text_contrast_on_surface_dark": round(cl.contrast(t_dark, s_dark), 2),
        }
    nL, nC, nh = cl.oklch(neutral_hex) if neutral_hex else (0.5, 0.01, cl.oklch(primary)[2])
    nstrong = tone(0.55, 0.012, nh)
    rows["neutral"] = {"label": "Sem variação", "glyph": "–", "meaning": "Estável, sem dado, sem mudança.",
                       "strong": {**cl.describe(nstrong), "token": f"{sigla}_Status_Neutro_Forte"}}
    keys = list(STATUS)
    sims = ("deuteranopia", "protanopia", "tritanopia")
    cvd = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            ha, hb = rows[a]["strong"]["hex"], rows[b]["strong"]["hex"]
            worst = min((cl.oklab_dist(cl.simulate_cvd(ha, s), cl.simulate_cvd(hb, s)), s) for s in sims)
            cvd.append({"pair": [a, b], "min_distance": round(worst[0], 3), "worst_case": worst[1]})
            if worst[0] < 0.06:
                findings.append(("WARN", "CVD_CONFUSION", f"{a} and {b} come close under {worst[1]} (distance {worst[0]:.3f}). Keep icon and word on both."))
    gap = abs(cl.oklch(rows["positive"]["strong"]["hex"])[0] - cl.oklch(rows["negative"]["strong"]["hex"])[0])
    if gap < 0.10:
        findings.append(("WARN", "GRAY_GAP", f"Positive and negative differ by {gap:.2f} in lightness: they merge in grayscale print."))
    for b in [primary] + list(extra):
        Lb, Cb, hb = cl.oklch(b)
        for key, (label, _, hue, *_r) in STATUS.items():
            if Cb > 0.08 and Lb >= 0.45 and cl.hue_gap(hb, hue) < 25:
                findings.append(("WARN", "BRAND_CLASH", f"Brand colour {b} is within 25 degrees of '{label}' and bright enough to be read as it. As a button or a link it may be taken for that status. Keep it out of data next to the status, and test it with the client."))
    return {"sigla": sigla, "statuses": rows, "colour_blind_check": cvd,
            "lightness_gap_positive_negative": round(gap, 3),
            "rules": {
                "use": ["Chips e etiquetas de estado", "Variação em indicadores (KPI)", "Células de tabela e semáforos de relatório",
                        "Avisos e banners de sistema", "Barras ou linhas que representam bom ou ruim"],
                "never": ["Como cor da marca, de botão primário ou de decoração", "Em gradiente", "Sozinha, sem ícone e palavra",
                          "Positivo e negativo lado a lado em verde e vermelho sem diferença de luminosidade",
                          "Mais de um status no mesmo elemento"],
                "meaning_not_direction": "Positivo é o que é bom para o negócio, não o que sobe. Custo que sobe é negativo, custo que cai é positivo.",
                "icons": ICONS_RULE,
                "print": "Em impressão, confirme em prova em escala de cinza que positivo e negativo ainda se distinguem."},
            "findings": [{"level": a, "code": b, "message": c} for a, b, c in findings],
            "verdict": "CAVEATS" if findings else "CLEAN",
            "note": "CMYK values are approximate. PMS needs a printed match. Colour-blind simulation is approximate."}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--primary", required=True)
    ap.add_argument("--sigla", required=True)
    ap.add_argument("--bg-light", default="#FFFFFF")
    ap.add_argument("--bg-dark", default="#12161C")
    ap.add_argument("--extra-brand", nargs="*", default=[], help="other brand colours to check against the status hues")
    ap.add_argument("--neutral", help="hex of a mid neutral for the no-change status")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        res = build(cl.norm_hex(a.primary), a.sigla, cl.norm_hex(a.bg_light), cl.norm_hex(a.bg_dark),
                    [cl.norm_hex(x) for x in a.extra_brand], a.neutral and cl.norm_hex(a.neutral))
    except ValueError as e:
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
