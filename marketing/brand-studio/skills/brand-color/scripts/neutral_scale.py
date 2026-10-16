#!/usr/bin/env python3
"""neutral_scale.py — the supplementary neutral palette: a grey scale that belongs to the brand.

An untinted grey sits next to a coloured brand like a stranger. This tool builds 11 neutrals (N00 light to N10 deep)
that carry a trace of the brand hue, so every grey in a layout looks chosen. The hue comes from the primary, the
chroma stays between 0.004 and 0.03 (a tint, never a colour), and lightness steps are even in OKLCH.

If the brand already fixed its light and dark neutrals (for example a fog white and an ink), pass them with
--light-hex and --dark-hex: they become N00 and N10 and the scale is built between them.

From the scale it assigns jobs, in light mode and in dark mode:
  page, surface, sunken (backgrounds) | border_subtle (1.3:1), border_ui (3:1) | text_muted (4.5:1 on page and surface)
  text_body (9:1) | text_strong (the deepest or the lightest)
Every job picks the softest step that still passes, so text is readable and never harsher than needed.

Rules:
  TWINS        WARN  two neighbouring steps are closer than 0.03 in OKLab
  CHROMA_RANGE WARN  a step has chroma outside 0.004 to 0.03 (grey, or too coloured to be a neutral)
  NO_STEP      WARN  a job has no step that passes its contrast
  LIGHT_END    WARN  N00 is darker than OKLCH lightness 0.94: there is no real light background

CMYK is approximate. PMS needs a printed match. A neutral in print is four-colour with a trace of the brand ink,
never black alone: a black-only grey shifts warm or cool with the paper.
Exit: 0 ok | 1 input error | 2 warnings. Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402

# Share of the way from the deep end (0) to the light end (1), for N00 (lightest) down to N10 (deepest).
FRAC = [1.0, 0.93, 0.85, 0.76, 0.65, 0.52, 0.40, 0.28, 0.17, 0.07, 0.0]
DEFAULT_LIGHT, DEFAULT_DARK = (0.985, 0.008), (0.20, 0.016)


def temperature(h):
    if 20 <= h < 110:
        return "quente"
    if 110 <= h < 190:
        return "verde-neutra"
    if 190 <= h < 300:
        return "fria"
    return "rosada"


def build(primary, sigla, light_hex=None, dark_hex=None):
    Lp, Cp, hp = cl.oklch(primary)
    hue = hp if Cp >= 0.03 else 260.0
    if light_hex:
        Ll, Cl, hl = cl.oklch(light_hex)
    else:
        (Ll, Cl), hl = DEFAULT_LIGHT, hue
    if dark_hex:
        Ld, Cd, hd = cl.oklch(dark_hex)
    else:
        (Ld, Cd), hd = DEFAULT_DARK, hue
    steps = []
    for i, f in enumerate(FRAC):  # i = 0 is the lightest, f = 1 is the light end
        L = Ld + (Ll - Ld) * f
        C = Cd + (Cl - Cd) * f
        h = cl.hue_lerp(hd, hl, f)
        hx = cl.oklch_to_hex(L, C, h)
        d = cl.describe(hx)
        d.update({"token": f"{sigla}_Neutro_N{i:02d}", "step": i, "lrv": cl.lrv(hx)})
        steps.append(d)
    if light_hex:
        steps[0].update(cl.describe(light_hex))
        steps[0]["hex"] = cl.norm_hex(light_hex)
    if dark_hex:
        steps[-1].update(cl.describe(dark_hex))
        steps[-1]["hex"] = cl.norm_hex(dark_hex)
    return steps, hue


def pick(steps, ok, order):
    seq = steps if order == "light_first" else list(reversed(steps))
    return next((s for s in seq if ok(s)), None)


def jobs(steps, mode, findings):
    c = cl.contrast
    if mode == "light":
        # Cards sit lighter than the page: a white with a trace of the brand hue.
        hue_c = cl.oklch(steps[0]["hex"])
        lift = cl.oklch_to_hex(0.995, 0.004, hue_c[2])
        d = cl.describe(lift)
        d.update({"token": steps[0]["token"].replace("N00", "Branco"), "step": -1, "lrv": cl.lrv(lift)})
        page, surface, sunken = steps[0], d, steps[1]
    else:
        page, surface, sunken = steps[-1], steps[-2], steps[-3]
    out = {"page": page, "surface": surface, "sunken": sunken}
    seq = steps if mode == "light" else list(reversed(steps))
    # light mode walks from light to dark; dark mode walks from dark to light. The first passing step is the softest.
    specs = {
        "border_subtle": lambda s: c(s["hex"], page["hex"]) >= 1.3,
        "border_ui": lambda s: c(s["hex"], page["hex"]) >= 3.0,
        "text_muted": lambda s: min(c(s["hex"], page["hex"]), c(s["hex"], surface["hex"])) >= 4.5 * 1.05,
        "text_body": lambda s: min(c(s["hex"], page["hex"]), c(s["hex"], surface["hex"])) >= 9.0,
    }
    for name, ok in specs.items():
        s = next((x for x in seq if ok(x)), None)
        if s is None:
            findings.append(("WARN", "NO_STEP", f"{mode} mode: no neutral passes for {name}."))
            s = seq[-1]
        out[name] = s
    out["text_strong"] = steps[-1] if mode == "light" else steps[0]
    res = {}
    for k, s in out.items():
        res[k] = {"token": s["token"], "hex": s["hex"], "contrast_on_page": round(c(s["hex"], page["hex"]), 2),
                  "cmyk_approx": s["cmyk_approx"]}
    return res


def run(primary, sigla, light_hex, dark_hex):
    findings = []
    steps, hue = build(primary, sigla, light_hex, dark_hex)
    for a, b in zip(steps, steps[1:]):
        if cl.oklab_dist(a["hex"], b["hex"]) < 0.03:
            findings.append(("WARN", "TWINS", f"{a['token']} and {b['token']} are too close."))
    for s in steps:
        C = s["oklch"][1]
        if not 0.004 <= C <= 0.03:
            findings.append(("WARN", "CHROMA_RANGE", f"{s['token']} has chroma {C}: a neutral needs 0.004 to 0.03."))
    if steps[0]["oklch"][0] < 0.94:
        findings.append(("WARN", "LIGHT_END", "N00 is darker than OKLCH lightness 0.94: there is no real light background."))
    mid = steps[5]
    grey = cl.oklch_to_hex(mid["oklch"][0], 0.0, hue)
    return {"sigla": sigla, "hue": round(hue, 1), "temperature": temperature(hue), "steps": steps,
            "roles": {"light": jobs(steps, "light", findings), "dark": jobs(steps, "dark", findings)},
            "untinted_example": {"hex": grey, "replaces": mid["token"],
                                 "note": "A grey of the same lightness with no hue. It is the stranger in the layout: never use it."},
            "findings": [{"level": a, "code": b, "message": c} for a, b, c in findings],
            "verdict": "CAVEATS" if findings else "CLEAN",
            "note": "CMYK values are approximate. PMS needs a printed match."}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--primary", required=True, help="the primary brand colour, its hue tints the neutrals")
    ap.add_argument("--sigla", required=True)
    ap.add_argument("--light-hex")
    ap.add_argument("--dark-hex")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        res = run(cl.norm_hex(a.primary), a.sigla, a.light_hex and cl.norm_hex(a.light_hex), a.dark_hex and cl.norm_hex(a.dark_hex))
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
