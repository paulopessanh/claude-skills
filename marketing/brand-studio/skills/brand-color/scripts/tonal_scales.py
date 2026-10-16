#!/usr/bin/env python3
"""tonal_scales.py — tints, tones and shades of each brand colour, each step with its token, values and use.

Definitions, so the team and the client use the same words:
  Tint   the colour plus white. Lighter, still clearly the colour. Chroma eases down but not below 30% of the base.
  Tone   the colour plus grey. Same family, quieter and more refined. Chroma falls to 25% of the base at the last step.
  Shade  the colour plus black. Deeper, hue held. Chroma eases down 25% so deep steps stay coloured and not muddy.
         The deepest shade stops at OKLCH lightness 0.17 or a third of the base, so it is a deep colour, never pure black.

Every scale is computed in OKLCH with the hue held and gamut-fitted, 7 steps per scale (the base is step 0).
Per step: token, HEX, RGB, HSL, OKLCH, approximate CMYK, contrast against white and ink, APCA, and whether it may
carry text. Token: {SIGLA}_{Family}_{Tint|Tone|Shade}{1..7}; the base is {SIGLA}_{Family}_Base.

Rules:
  NO_TEXT_SHADE   WARN  no shade of a family reaches 4.5:1 against white: the family cannot carry text on light
  NO_TEXT_TINT    WARN  no tint reaches 4.5:1 against the dark ink: the family cannot carry text on dark
  TWINS           WARN  two neighbouring steps are closer than 0.012 in OKLab: they will read as one
  GREY_TINT       WARN  a tint or a shade kept under 20% of the base chroma: it reads grey, not coloured

CMYK is approximate. PMS needs a printed match. Exit: 0 ok | 1 input error | 2 warnings.
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402

N = 7
WHITE, INK = "#FFFFFF", "#12161C"
USES = {
    "Tint": {"what": "Cor mais clara da mesma família.",
             "use": "Fundos de destaque, cartões, estado selecionado ou hover, etiquetas, ilustração leve, gráficos de apoio.",
             "when": "Quando a marca precisa aparecer com leveza, sem competir com o conteúdo.",
             "never": "Texto sobre fundo claro. Nunca como única diferença entre dois estados sem outra pista."},
    "Tone": {"what": "Cor misturada ao cinza. Mais calma.",
             "use": "Interface secundária, bordas, estados inativos, fotografia e ilustração de atmosfera, fundos de gráficos.",
             "when": "Quando a peça pede sofisticação ou o conteúdo é denso e a cor precisa recuar.",
             "never": "Como cor de ação, link ou botão. Uma cor apagada não chama o clique."},
    "Shade": {"what": "Cor misturada ao preto. Mais profunda.",
              "use": "Texto, títulos, fundos escuros e modo escuro, botão pressionado, sombras coloridas, sobreposições.",
              "when": "Quando a peça pede peso, contraste e leitura, ou quando a marca vira fundo.",
              "never": "Preto puro no lugar do shade. Em impressão offset, preto puro sai lavado."},
}


def step_hex(L0, C0, h, kind, i):
    t = i / (N + 1)
    if kind == "Tint":
        L, C = L0 + (0.975 - L0) * t, max(C0 * (1 - 0.6 * t ** 1.5), C0 * 0.30)
    elif kind == "Tone":
        L, C = L0 + (0.70 - L0) * 0.8 * t, C0 * (1 - 0.85 * t)
    else:
        floor = min(L0, max(0.17, L0 * 0.35))
        L, C = L0 + (floor - L0) * t / (N / (N + 1)), C0 * (1 - 0.25 * t)
    return cl.oklch_to_hex(L, C, h)


def row(token, hx):
    d = cl.describe(hx)
    cw, ci = cl.contrast(hx, WHITE), cl.contrast(hx, INK)
    d.update({"token": token, "contrast_white": round(cw, 2), "contrast_ink": round(ci, 2),
              "apca_on_white": cl.apca(hx, WHITE), "apca_on_ink": cl.apca(hx, INK),
              "carries_text": {"white_text_on_it": cw >= 4.5, "ink_text_on_it": ci >= 4.5,
                               "it_as_text_on_white": cw >= 4.5, "it_as_text_on_ink": ci >= 4.5}})
    return d


def build(data):
    sig = data["brand"]["sigla"]
    findings, fams = [], []
    for f in data["families"]:
        name = f.get("universe_name") or f["name"]
        base = cl.norm_hex(f["hex"])
        L0, C0, h = cl.oklch(base)
        fam = {"family": name, "base": row(f"{sig}_{name}_Base", base), "scales": {}}
        for kind in ("Tint", "Tone", "Shade"):
            steps = []
            for i in range(1, N + 1):
                hx = step_hex(L0, C0, h, kind, i)
                steps.append(row(f"{sig}_{name}_{kind}{i}", hx))
                if kind != "Tone" and C0 > 0.04 and cl.oklch(hx)[1] < 0.20 * C0:
                    findings.append(("WARN", "GREY_TINT", f"{name} {kind}{i} reads grey."))
            hexes = [base] + [s["hex"] for s in steps]
            for a, b in zip(hexes, hexes[1:]):
                if sum((x - y) ** 2 for x, y in zip(cl.oklab(a), cl.oklab(b))) ** 0.5 < 0.012:
                    findings.append(("WARN", "TWINS", f"{name} {kind}: two neighbouring steps are too close ({a}, {b})."))
            fam["scales"][kind] = {**USES[kind], "steps": steps}
        if not any(s["contrast_white"] >= 4.5 for s in fam["scales"]["Shade"]["steps"]) and cl.contrast(base, WHITE) < 4.5:
            findings.append(("WARN", "NO_TEXT_SHADE", f"{name}: no shade reaches 4.5:1 on white."))
        if not any(s["contrast_ink"] >= 4.5 for s in fam["scales"]["Tint"]["steps"]) and cl.contrast(base, INK) < 4.5:
            findings.append(("WARN", "NO_TEXT_TINT", f"{name}: no tint reaches 4.5:1 on the dark ink."))
        fams.append(fam)
    return {"brand": data["brand"], "ink": INK, "families": fams,
            "findings": [{"level": a, "code": b, "message": c} for a, b, c in findings],
            "verdict": "CAVEATS" if findings else "CLEAN",
            "note": "CMYK values are approximate. PMS needs a printed match."}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--input", required=True, help='JSON {"brand":{"sigla":"SFI"},"families":[{"universe_name":"Cume","hex":"#2B3A67"}]}')
    ap.add_argument("--out")
    args = ap.parse_args()
    try:
        with open(args.input, encoding="utf-8") as f:
            res = build(json.load(f))
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)
    return 2 if res["verdict"] == "CAVEATS" else 0


if __name__ == "__main__":
    sys.exit(main())
