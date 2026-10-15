#!/usr/bin/env python3
"""color_system_builder.py — turn a few base colours into a documented, accessible colour system.

From each base colour it builds a family of steps (default 10..70, step 50 = the base itself)
by moving lightness in OKLCH while keeping the hue, and pulling chroma back inside the sRGB
gamut so no step is clipped. For every step it prints a token name, HEX, RGB, an approximate CMYK,
and WCAG contrast against white and near-black. It then reports which steps carry text.

Rules:
  VETOED_HUE   BLOCK  a family's hue is within 25 degrees of a vetoed colour's hue (client veto)
  DUPLICATE    WARN   two base colours are closer than 0.05 in OKLab: they will read as one
  NO_TEXT_STEP WARN   a family has no step that carries white text at 4.5:1
  LOW_RANGE    WARN   the family's steps span less than 0.5 of lightness (a ramp that does not ramp)

CMYK here is a naive conversion from sRGB. Real print values come from an ICC profile and a printed
proof (ISO 12647 workflows); the tool says APPROX so nobody ships it as a spec.

Token name: {SIGLA}_{Universe}_{step}, for example SFI_Cume_50. The colour is named in two parts,
the colour word and a name from the brand's own world ("Azul Cume").

Exit codes: 0 OK | 1 input error | 2 WARNINGS | 4 BLOCKED (veto)
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import math
import os
import re
import sys

CHROMA_MIN = 0.04
VETO_TOL = 25      # degrees of OKLCH hue; the same tolerance in competitor_matrix.py and deliverable_linter.py


def hex_rgb(h):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", str(h).strip())
    if not m:
        raise ValueError(f"bad hex colour: {h!r}")
    v = m.group(1)
    return tuple(int(v[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def delin(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def to_oklab(rgb):
    r, g, b = (lin(c) for c in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def from_oklab(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def in_gamut(lrgb):
    return all(-1e-6 <= c <= 1 + 1e-6 for c in lrgb)


def oklch_to_hex(L, C, h):
    lo, hi = 0.0, C
    a, b = math.cos(math.radians(h)), math.sin(math.radians(h))
    if not in_gamut(from_oklab(L, C * a, C * b)):
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if in_gamut(from_oklab(L, mid * a, mid * b)) else (lo, mid)
        C = lo
    rgb = [min(1, max(0, delin(min(1, max(0, c))))) for c in from_oklab(L, C * a, C * b)]
    return "#" + "".join(f"{round(c * 255):02X}" for c in rgb), C


def lum(hexv):
    r, g, b = (lin(c) for c in hex_rgb(hexv))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(h1, h2):
    a, b = sorted((lum(h1), lum(h2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def cmyk_approx(hexv):
    r, g, b = hex_rgb(hexv)
    k = 1 - max(r, g, b)
    if k >= 1:
        return (0, 0, 0, 100)
    return tuple(round(100 * v) for v in ((1 - r - k) / (1 - k), (1 - g - k) / (1 - k), (1 - b - k) / (1 - k), k))


def hue_of(hexv):
    L, a, b = to_oklab(hex_rgb(hexv))
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def hue_gap(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def build_family(base_hex, steps):
    L0, C0, h = hue_of(base_hex)
    rows = []
    for s in steps:
        if s == 50:
            hx = "#" + base_hex.lstrip("#").upper()
        elif s < 50:
            t = (50 - s) / 40.0
            hx, _ = oklch_to_hex(L0 + (0.97 - L0) * t, C0 * (0.15 + 0.85 * (1 - t)), h)
        else:
            frac = min(1.0, (s - 50) / 25.0)          # 60 -> 0.4, 70 -> 0.8 of the way to L 0.18
            hx, _ = oklch_to_hex(L0 - (L0 - 0.18) * frac if L0 > 0.18 else L0, C0 * (1 - 0.35 * frac), h)
        rows.append({"step": s, "hex": hx, "rgb": [round(c * 255) for c in hex_rgb(hx)], "cmyk_approx": list(cmyk_approx(hx)),
                     "on_white": round(contrast(hx, "#FFFFFF"), 2), "on_near_black": round(contrast(hx, "#111111"), 2)})
    return rows


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Build accessible colour families from base colours.")
    ap.add_argument("--input", help="colour JSON (see assets/example_colours.json)")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_colours.json") if a.sample else a.input
    if not path:
        ap.error("provide --input or --sample")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        sigla, fams = data["sigla"].upper(), data["families"]
        steps = data.get("steps", [10, 20, 30, 40, 50, 60, 70])
        if 50 not in steps:
            raise ValueError("steps must include 50, the base")
        veto_h = [hue_of(v)[2] for v in data.get("vetoed_hexes", []) if hue_of(v)[1] >= CHROMA_MIN]
        out, findings = [], []
        for f in fams:
            rows = build_family(f["hex"], steps)
            name = f"{f['pt_name']} {f['universe_name']}"
            L0, C0, h0 = hue_of(f["hex"])
            if C0 >= CHROMA_MIN and any(hue_gap(h0, vh) <= VETO_TOL for vh in veto_h):
                findings.append(("BLOCK", "VETOED_HUE", f"{name} ({f['hex']}) is within {VETO_TOL} degrees of a vetoed hue"))
            text_steps = [r["step"] for r in rows if r["on_white"] >= 4.5]
            if not text_steps:
                findings.append(("WARN", "NO_TEXT_STEP", f"{name} has no step that carries white text at 4.5:1"))
            span = max(hue_of(r["hex"])[0] for r in rows) - min(hue_of(r["hex"])[0] for r in rows)
            if span < 0.5:
                findings.append(("WARN", "LOW_RANGE", f"{name} spans only {span:.2f} of lightness"))
            for r in rows:
                r["token"] = f"{sigla}_{f['universe_name']}_{r['step']}"
            out.append({"name": name, "base": f["hex"], "text_on_white_from_step": min(text_steps) if text_steps else None, "steps": rows})
        for i, f1 in enumerate(fams):
            for f2 in fams[i + 1:]:
                d = math.dist(to_oklab(hex_rgb(f1["hex"])), to_oklab(hex_rgb(f2["hex"])))
                if d < 0.05:
                    findings.append(("WARN", "DUPLICATE", f"{f1['universe_name']} and {f2['universe_name']} are {d:.3f} apart in OKLab"))
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    code = 4 if any(x[0] == "BLOCK" for x in findings) else (2 if findings else 0)
    if a.output == "json":
        print(json.dumps({"verdict": {0: "OK", 2: "WARNINGS", 4: "BLOCKED"}[code], "families": out,
                          "findings": [{"level": l, "code": c, "message": m} for l, c, m in findings]}, indent=2, ensure_ascii=False))
    else:
        for fam in out:
            print(f"{fam['name']}  base {fam['base']}  white text from step {fam['text_on_white_from_step']}")
            for r in fam["steps"]:
                aa = "AA" if r["on_white"] >= 4.5 else ("AA large" if r["on_white"] >= 3 else "fail")
                print(f"  {r['token']:<14} {r['hex']}  rgb {tuple(r['rgb'])}  cmyk~ {tuple(r['cmyk_approx'])}  white {r['on_white']:>5} ({aa})  black {r['on_near_black']:>5}")
        for l, c, m in findings:
            print(f"  [{l}] {c}: {m}")
        print("CMYK is APPROX (naive from sRGB). Get print values from a profile and a printed proof.")
    sys.exit(code)


if __name__ == "__main__":
    main()
