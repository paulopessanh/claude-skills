#!/usr/bin/env python3
"""palette_logic_analyzer.py — read the colour and type logic out of a brand's visual system.

Input is what you can measure by eyedropper and by reading the specimen: a palette with
approximate surface shares, and the typefaces with their class and role. The tool computes
what is computable (roles, hue relation, temperature, WCAG contrast, proportion pattern,
type pairing) and then states each design-intent reading as an INFERENCE with the rival
explanation attached, because "why" is never in the pixels.

Hue relation (circular hue difference between chromatic colours, degrees):
  triadic              three hues each ~120 apart (+/-20)
  complementary        a pair 165-180 apart
  split-complementary  three or more hues, a pair 135-165 apart and no pair 165-180
  near-complementary   exactly two hues 135-165 apart (too few hues to call it split)
  analogous            all chromatic hues within 60 of each other
  irregular            none of the above
Neutral = saturation < 0.15, or value < 0.12, or (saturation < 0.25 and value > 0.92).

Exit codes: 0 OK | 1 input error | 2 FLAGS (contrast or type findings) | 3 INSUFFICIENT (< 2 colours)
Stdlib only. No network. Deterministic.
"""

import argparse
import colorsys
import json
import os
import re
import sys

HEX = re.compile(r"^#?([0-9a-fA-F]{6})$")


def parse_hex(h):
    m = HEX.match(str(h).strip())
    if not m:
        raise ValueError(f"bad hex colour: {h!r}")
    v = m.group(1)
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def luminance(rgb):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hsv(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in rgb))
    return h * 360.0, s, v


def is_neutral(s, v):
    return s < 0.15 or v < 0.12 or (s < 0.25 and v > 0.92)


def hue_gap(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def hue_relation(hues):
    if not hues:
        return "achromatic"
    if len(hues) < 2:
        return "single-hue"
    gaps = [hue_gap(a, b) for i, a in enumerate(hues) for b in hues[i + 1:]]
    if len(hues) >= 3:
        for i in range(len(hues)):
            for j in range(i + 1, len(hues)):
                for k in range(j + 1, len(hues)):
                    t = (hue_gap(hues[i], hues[j]), hue_gap(hues[j], hues[k]), hue_gap(hues[i], hues[k]))
                    if all(100 <= g <= 140 for g in t):
                        return "triadic"
    if any(165 <= g <= 180 for g in gaps):
        return "complementary"
    if any(135 <= g < 165 for g in gaps):
        return "split-complementary" if len(hues) >= 3 else "near-complementary"
    if max(gaps) <= 60:
        return "analogous"
    return "irregular"


def temperature(h):
    if h <= 70 or h >= 330:
        return "warm"
    if 170 <= h <= 270:
        return "cool"
    return "mixed"


def analyse_palette(palette):
    rows = []
    n = len(palette)
    shares = [p.get("share") for p in palette]
    if all(s is None for s in shares):
        shares = [1.0 / n] * n
    elif any(s is None for s in shares):
        raise ValueError("give a share for every colour or for none")
    total = sum(shares) or 1.0
    for p, s in zip(palette, shares):
        rgb = parse_hex(p["hex"])
        h, sat, val = hsv(rgb)
        rows.append({"hex": "#" + "".join(f"{c:02X}" for c in rgb), "share": round(s / total, 3),
                     "hue": round(h), "neutral": is_neutral(sat, val), "rgb": rgb})
    rows.sort(key=lambda r: -r["share"])
    for i, r in enumerate(rows):
        if r["neutral"]:
            r["role"] = "neutral"
        elif i == 0:
            r["role"] = "dominant"
        elif r["share"] <= 0.12:
            r["role"] = "accent"
        else:
            r["role"] = "secondary"
    chrom = [r for r in rows if not r["neutral"]]
    cw = sum(r["share"] for r in chrom) or 1.0
    temp = {"warm": 0.0, "cool": 0.0, "mixed": 0.0}
    for r in chrom:
        temp[temperature(r["hue"])] += r["share"] / cw
    contrast_rows = []
    for r in rows:
        best = max((contrast(r["rgb"], o["rgb"]), o["hex"]) for o in rows if o is not r)
        grade = "text-safe" if best[0] >= 4.5 else ("large-text-only" if best[0] >= 3 else "FAIL")
        contrast_rows.append({"hex": r["hex"], "best_ratio": round(best[0], 2), "against": best[1], "grade": grade})
    top = rows[0]["share"]
    proportion = "dominant-led" if top >= 0.5 else ("balanced" if top < 0.4 else "two-colour-led")
    for r in rows:
        r.pop("rgb")
    return {"colours": rows, "hue_relation": hue_relation([r["hue"] for r in chrom]),
            "temperature": {k: round(v, 2) for k, v in temp.items()},
            "proportion_pattern": "/".join(str(round(r["share"] * 100)) for r in rows), "proportion_class": proportion,
            "contrast": contrast_rows}


def analyse_type(faces):
    classes = sorted({f.get("class", "?") for f in faces})
    names = sorted({f.get("name", "?") for f in faces})
    roles = {f.get("role") for f in faces}
    flags = []
    if len(names) > 3:
        flags.append("TYPE_SPRAWL: more than three families; a system rarely needs them")
    if not ({"headline", "body"} <= roles):
        flags.append("ROLE_GAP: headline and body roles are not both covered")
    if len(names) == 1:
        pairing = "single family"
    elif "serif" in classes and "sans" in classes:
        pairing = "serif/sans contrast pairing"
    elif len(classes) == 1:
        pairing = f"same-class pairing ({classes[0]})"
    else:
        pairing = "mixed-class pairing: " + " + ".join(classes)
    return {"families": names, "classes": classes, "pairing": pairing, "flags": flags}


def readings(pal, typ):
    sector = "sector convention (check three or more category competitors before crediting intent)"
    out = []
    if pal["hue_relation"] not in ("achromatic", "single-hue"):
        out.append({"observation": f"Hue relation is {pal['hue_relation']}.",
                    "inference": f"The palette was built on a {pal['hue_relation']} scheme on purpose.",
                    "rival": sector, "class": "inferred"})
    out += [
        {"observation": f"Surface shares run {pal['proportion_pattern']} ({pal['proportion_class']}).",
         "inference": "A fixed proportion rule governs colour use across touchpoints.",
         "rival": "Colours were sampled from a single hero photograph or pack, not set as a rule", "class": "inferred"},
    ]
    if typ:
        out.append({"observation": f"Type is a {typ['pairing']}.",
                    "inference": "The pairing was chosen for the personality the strategy asked for.",
                    "rival": "Defaults of the tool or template the makers worked in", "class": "inferred"})
    return out


def render(res):
    p = res["palette"]
    lines = [f"Hue relation: {p['hue_relation']}   Proportion: {p['proportion_pattern']} ({p['proportion_class']})",
             "Temperature: " + (", ".join(f"{k} {v:.0%}" for k, v in p["temperature"].items() if v) or "none (no chromatic colour)")]
    for r in p["colours"]:
        lines.append(f"  {r['hex']}  {r['share']:.0%}  {r['role']}")
    lines.append("Contrast (best partner in palette):")
    for c in p["contrast"]:
        lines.append(f"  {c['hex']} {c['best_ratio']}:1 vs {c['against']}  {c['grade']}")
    if res.get("type"):
        lines.append(f"Type: {res['type']['pairing']} ({', '.join(res['type']['families'])})")
    for f in res["flags"]:
        lines.append(f"  [FLAG] {f}")
    lines.append("Readings (all INFERRED, record the rival in the ledger):")
    for r in res["readings"]:
        lines.append(f"  - {r['observation']} -> {r['inference']}  Rival: {r['rival']}")
    return "\n".join(lines)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Extract colour and type logic from a brand's palette and typefaces.")
    ap.add_argument("--input", help="case file or {palette, typefaces} JSON")
    ap.add_argument("--sample", action="store_true", help="run on assets/example_reference.json")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    args = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_reference.json") if args.sample else args.input
    if not path:
        ap.error("provide --input or --sample")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        data = data.get("reference", data)
        palette = data.get("palette", [])
        if len(palette) < 2:
            print("INSUFFICIENT: need at least two colours with hex values.")
            sys.exit(3)
        pal = analyse_palette(palette)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    typ = analyse_type(data["typefaces"]) if data.get("typefaces") else None
    flags = [f"COLOUR_UNUSABLE: {c['hex']} reaches only {c['best_ratio']}:1 against every other palette colour"
             for c in pal["contrast"] if c["grade"] == "FAIL"]
    if typ:
        flags += typ["flags"]
    res = {"palette": pal, "type": typ, "flags": flags, "readings": readings(pal, typ)}
    print(json.dumps(res, indent=2) if args.output == "json" else render(res))
    sys.exit(2 if flags else 0)


if __name__ == "__main__":
    main()
