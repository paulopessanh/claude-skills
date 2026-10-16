#!/usr/bin/env python3
"""gradient_builder.py — gradients without grey limbo, in the Light Source / Hold / Falloff / Anchor method.

Two modes:
  --mono HEX         one family. Four stops in OKLCH, hue held, chroma held, lightness stepping down:
                     Light Source 0%, Hold 42%, Falloff 62%, Anchor 100%. Hold is the brand colour itself.
  --duo HEX HEX      two families. Interpolated in OKLCH on the shortest hue arc; when the middle
                     loses chroma, a bridge stop restores it. If the gamut cannot carry the bridge, it BLOCKS.

Why limbo happens: a straight RGB mix of two saturated colours passes through a low-chroma middle.
The gradient looks dirty there. OKLCH keeps chroma and lightness perceptually even, so the middle stays clean.
The tool measures the real, quantised hex samples, not the maths, and compares them with a naive RGB mix.

Rules:
  GREY_LIMBO     BLOCK  a sample's chroma falls under 60% of the weaker endpoint (and above 0.03)
  BRIDGE_FAILED  BLOCK  no bridge keeps chroma above that line: add a third family between the two
  HUE_SWING      WARN   the arc crosses more than 90 degrees: it reads as a rainbow
  NEUTRAL_END    WARN   an endpoint is near neutral: use a tinted neutral of the family hue, never pure black or white
  EDGE_CONTRAST  WARN   a stop is under 3:1 against a background it sits on (WCAG 1.4.11, shapes)
  FLAT_RANGE     WARN   lightness spans less than 0.12: the gradient will not read

CMYK is approximate. PMS needs a printed match. Exit: 0 ok | 1 input error | 2 warnings | 4 blocked.
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402

POS = {"light": 0.0, "hold": 0.42, "falloff": 0.62, "anchor": 1.0}
ROLE = {"light": "Light Source", "hold": "Hold", "falloff": "Falloff", "anchor": "Anchor"}
SAMPLES = 33
LIMBO_RATIO = 0.60
NEUTRAL_C = 0.03


def mono_stops(base, hue_drift=0.0):
    """Light Source, Hold (the base), Falloff, Anchor as OKLCH triples. Hold is exactly the base."""
    L0, C0, h0 = cl.oklch(base)
    hold = (L0, C0, h0)
    light = (min(0.95, L0 + 0.15), C0 * 0.95, (h0 - hue_drift) % 360)
    falloff = (max(0.12, L0 - 0.06), C0 * 1.0, (h0 + hue_drift * 0.5) % 360)
    anchor = (max(0.10, L0 - 0.14), C0 * 0.95, (h0 + hue_drift) % 360)
    return [("light", light), ("hold", hold), ("falloff", falloff), ("anchor", anchor)]


def sample(stops, n=SAMPLES):
    """Piecewise OKLCH interpolation across stops [(pos, (L,C,h))]. Returns n hex samples."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        for (p1, c1), (p2, c2) in zip(stops, stops[1:]):
            if p1 <= t <= p2:
                u = 0 if p2 == p1 else (t - p1) / (p2 - p1)
                L, C, h = cl.lerp_oklch(c1, c2, u)
                out.append(cl.oklch_to_hex(L, C, h))
                break
    return out


def chroma_of(hexes):
    return [cl.oklch(x)[1] for x in hexes]


def duo_stops(a, b):
    """Return (stops, bridged). Adds a bridge when the straight OKLCH path dips under the limbo line."""
    ca, cb = cl.oklch(a), cl.oklch(b)
    base = [(0.0, ca), (1.0, cb)]
    floor = LIMBO_RATIO * min(ca[1], cb[1])
    if min(chroma_of(sample(base))) >= floor or min(ca[1], cb[1]) < NEUTRAL_C:
        return base, False
    mid = cl.lerp_oklch(ca, cb, 0.5)
    for boost in (0.85, 1.0, 1.15):
        C = min(ca[1], cb[1]) * boost
        c = (mid[0], cl.fit_chroma(mid[0], C, mid[2]), mid[2])
        trial = [(0.0, ca), (0.5, c), (1.0, cb)]
        if min(chroma_of(sample(trial))) >= floor:
            return trial, True
    return [(0.0, ca), (0.5, (mid[0], cl.fit_chroma(mid[0], min(ca[1], cb[1]), mid[2]), mid[2])), (1.0, cb)], True


def naive_rgb(a, b):
    return [cl.lerp_srgb(a, b, i / (SAMPLES - 1)) for i in range(SAMPLES)]


def build(args):
    findings = []
    if args.mono:
        base = cl.norm_hex(args.mono)
        named = mono_stops(base, args.hue_drift)
        stops = [(POS[r], c) for r, c in named]
        roles = [r for r, _ in named]
        mode = "mono"
        if cl.oklch(base)[1] < NEUTRAL_C:
            findings.append(("WARN", "NEUTRAL_END", "The base is near neutral: tint it with the brand hue so the ramp does not read grey."))
        ref = None
    else:
        a, b = cl.norm_hex(args.duo[0]), cl.norm_hex(args.duo[1])
        stops, bridged = duo_stops(a, b)
        roles = ["light", "bridge", "anchor"] if bridged else ["light", "anchor"]
        mode = "duo"
        ca, cb = cl.oklch(a), cl.oklch(b)
        ref = naive_rgb(a, b)
        if cl.hue_gap(ca[2], cb[2]) > 90 and min(ca[1], cb[1]) >= NEUTRAL_C:
            findings.append(("WARN", "HUE_SWING", f"Hue arc is {cl.hue_gap(ca[2], cb[2]):.0f} degrees: it will read as a rainbow. Prefer families within 60 degrees."))
        for n, c in (("first", ca), ("second", cb)):
            if c[1] < NEUTRAL_C:
                findings.append(("WARN", "NEUTRAL_END", f"The {n} colour is near neutral: use a tinted neutral of the other family's hue, not pure black or white."))
        if bridged:
            findings.append(("WARN", "BRIDGE_ADDED", "A bridge stop was added at 50% to restore chroma. Document it as part of the gradient."))
    samples = sample(stops)
    ch = chroma_of(samples)
    weak = min(stops[0][1][1], stops[-1][1][1])
    ratio = min(ch) / weak if weak else 1.0
    if mode == "duo" and weak >= NEUTRAL_C and ratio < LIMBO_RATIO:
        code = "BRIDGE_FAILED" if len(stops) == 3 else "GREY_LIMBO"
        findings.append(("BLOCK", code, f"Chroma falls to {ratio:.0%} of the weaker end. Add a third family between the two, or move the ends closer in hue."))
    Ls = [cl.oklch(x)[0] for x in samples]
    if max(Ls) - min(Ls) < 0.12:
        findings.append(("WARN", "FLAT_RANGE", "Lightness range is under 0.12: the gradient will not read. Move the ends apart."))
    stop_rows = []
    for (p, c), role in zip(stops, roles):
        hx = cl.oklch_to_hex(*c)
        row = {"role": ROLE.get(role, "Bridge"), "pos": round(p * 100), "hex": hx}
        row.update({k: v for k, v in cl.describe(hx).items() if k != "hex"})
        stop_rows.append(row)
    bgs = {}
    for name, bg in (("light", args.bg_light), ("dark", args.bg_dark)):
        if bg:
            bg = cl.norm_hex(bg)
            ratios = [round(cl.contrast(s, bg), 2) for s in samples]
            bgs[name] = {"bg": bg, "min_ratio": min(ratios), "max_ratio": max(ratios),
                         "worst_apca_lc": min(abs(cl.apca(s, bg)) for s in samples)}
            if min(ratios) < 3.0:
                findings.append(("WARN", "EDGE_CONTRAST", f"On the {name} background some stops are under 3:1 (min {min(ratios)}). Do not use this as a shape edge there; place the gradient on the other background or move text to the end that passes."))
    naive_ratio = None
    if ref and weak >= NEUTRAL_C:
        naive_ratio = round(min(chroma_of(ref)) / weak, 2)
    idx = list(range(0, SAMPLES, 4))
    if idx[-1] != SAMPLES - 1:
        idx.append(SAMPLES - 1)
    css_oklch = "linear-gradient(in oklch {a}deg, {s})".format(
        a=args.angle, s=", ".join(f"{r['hex']} {r['pos']}%" for r in stop_rows))
    css_srgb = "linear-gradient({a}deg, {s})".format(
        a=args.angle, s=", ".join(f"{samples[i]} {round(i / (SAMPLES - 1) * 100)}%" for i in idx))
    verdict = "BLOCKED" if any(f[0] == "BLOCK" for f in findings) else (
        "CAVEATS" if any(f[0] == "WARN" and f[1] != "BRIDGE_ADDED" for f in findings) else "CLEAN")
    return {
        "name": args.name or ("grad-" + (args.mono or "-".join(args.duo)).replace("#", "")),
        "mode": mode, "angle": args.angle, "stops": stop_rows,
        "css": {"modern_oklch": css_oklch, "universal_srgb": css_srgb,
                "use": "Use universal_srgb in tools without OKLCH (Figma, Illustrator, Keynote, email). It is sampled from the clean OKLCH path, so it keeps the same look."},
        "checks": {"min_chroma_ratio": round(ratio, 2), "naive_rgb_min_chroma_ratio": naive_ratio,
                   "lightness_range": round(max(Ls) - min(Ls), 3), "backgrounds": bgs, "limbo_line": LIMBO_RATIO},
        "findings": [{"level": a, "code": b, "message": c} for a, b, c in findings],
        "verdict": verdict,
        "note": "CMYK values are approximate. PMS needs a printed match.",
    }, samples, ref


def svg(res, samples, ref):
    def grad(i, colors):
        stops = "".join(f'<stop offset="{j / (len(colors) - 1):.3f}" stop-color="{c}"/>' for j, c in enumerate(colors))
        return f'<linearGradient id="g{i}" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>'
    defs = grad(0, samples) + (grad(1, ref) if ref else "")
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="520" height="340" viewBox="0 0 520 340" font-family="Helvetica,Arial,sans-serif" font-size="12">',
             f"<defs>{defs}</defs>", '<rect width="100%" height="100%" fill="#FFFFFF"/>',
             '<rect x="20" y="20" width="220" height="240" rx="14" fill="url(#g0)"/>',
             '<text x="20" y="282" fill="#222">brand-color (OKLCH)</text>']
    if ref:
        parts += ['<rect x="280" y="20" width="220" height="240" rx="14" fill="url(#g1)"/>',
                  '<text x="280" y="282" fill="#222">naive RGB (compare)</text>']
    parts.append('<text x="20" y="308" fill="#555" font-size="11">' +
                 "  ".join(f'{r["role"]} {r["pos"]}% {r["hex"]}' for r in res["stops"]) + "</text></svg>")
    return "".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mono", metavar="HEX")
    g.add_argument("--duo", nargs=2, metavar=("HEX_A", "HEX_B"))
    ap.add_argument("--angle", type=int, default=180)
    ap.add_argument("--hue-drift", type=float, default=0.0, help="degrees of hue shift across a mono ramp, 0 to 12")
    ap.add_argument("--bg-light")
    ap.add_argument("--bg-dark")
    ap.add_argument("--name")
    ap.add_argument("--svg")
    ap.add_argument("--out")
    args = ap.parse_args()
    if not 0 <= args.hue_drift <= 12:
        print("error: --hue-drift must be between 0 and 12", file=sys.stderr)
        return 1
    try:
        res, samples, ref = build(args)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)
    if args.svg:
        with open(args.svg, "w", encoding="utf-8") as f:
            f.write(svg(res, samples, ref))
    return {"BLOCKED": 4, "CAVEATS": 2, "CLEAN": 0}[res["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
