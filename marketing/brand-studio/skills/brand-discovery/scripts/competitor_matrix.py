#!/usr/bin/env python3
"""competitor_matrix.py — see the category before drawing in it: clichés, crowded hues, white space.

A brand that ignores its category is born looking like it. This tool reads 5 to 12 competitors
and measures what they have in common, in OKLCH (a perceptual colour space, Ottosson 2020),
so "empty hue" means empty to the eye and not just to the hex code.

Measured:
  hue map        12 bins of 30 degrees; share of competitors using each (chromatic colours only)
  cliches        any hue bin, symbol type, anatomy type or tone word used by 40% or more of competitors
  white space    hue bins no competitor uses, ranked by distance to the nearest occupied bin, minus vetoed hues
  candidate      optional: your palette, checked for distance to each competitor and for sitting in a crowded hue

Hard rules:
  every competitor needs a source and a date (UNSOURCED, exit 4): an unsourced competitor is a rumour
  fewer than 5 competitors is not a category (exit 3); more than 12 dilutes the reading (warning)
  a candidate colour within 25 degrees of a vetoed hue is a VETOED_HUE (exit 4): the client's veto is not up for negotiation here
  a candidate whose colours are near-identical (OKLab distance < 0.04) to two colours of one competitor
  is a PALETTE_CLONE (exit 4)
An empty hue can be empty for a reason (the category may reject it). The tool says so; a person judges.

Exit codes: 0 OK | 1 input error | 2 WARNINGS | 3 INSUFFICIENT | 4 BLOCKED
Stdlib only. No network. Deterministic.
"""

import argparse
import collections
import json
import math
import os
import re
import sys

CHROMA_MIN = 0.04     # below this a colour reads as neutral in OKLab
CLICHE_SHARE = 0.40
CLONE_DIST = 0.04     # OKLab distance, roughly 2 JND
NEAR_DIST = 0.06
VETO_TOL = 25         # degrees of OKLCH hue; the same tolerance in color_system_builder.py and deliverable_linter.py


def hex_rgb(h):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", str(h).strip())
    if not m:
        raise ValueError(f"bad hex colour: {h!r}")
    v = m.group(1)
    return tuple(int(v[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def oklab(h):
    r, g, b = (lin(c) for c in hex_rgb(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def oklch(h):
    L, a, b = oklab(h)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def dist(h1, h2):
    return math.dist(oklab(h1), oklab(h2))


def hue_bin(hue):
    return int(hue // 30) % 12


def bin_label(i):
    return f"{i * 30}-{i * 30 + 30}"


def circ_gap(i, j):
    d = abs(i - j) % 12
    return min(d, 12 - d)


def analyse(data):
    comps = data["competitors"]
    findings = []
    res = {"n": len(comps)}
    use = collections.defaultdict(set)
    for c in comps:
        for hx in c.get("palette", []):
            L, C, H = oklch(hx)
            if C >= CHROMA_MIN:
                use[hue_bin(H)].add(c["name"])
    n = len(comps)
    res["hue_map"] = {bin_label(i): round(len(use[i]) / n, 2) for i in range(12) if use[i]}
    res["cliches"] = {"hue": [bin_label(i) for i in range(12) if len(use[i]) / n >= CLICHE_SHARE]}
    for key in ("symbol_type", "anatomy"):
        cnt = collections.Counter(c.get(key) for c in comps if c.get(key))
        res["cliches"][key] = [f"{k} ({v}/{n})" for k, v in cnt.items() if v / n >= CLICHE_SHARE]
    tones = collections.Counter(w for c in comps for w in set(c.get("tone", [])))
    res["cliches"]["tone"] = [f"{k} ({v}/{n})" for k, v in tones.most_common() if v / n >= CLICHE_SHARE]
    vet, veto_hues = set(), []
    for hx in data.get("vetoed_hexes", []):
        L, C, H = oklch(hx)
        if C >= CHROMA_MIN:
            vet.add(hue_bin(H))
            veto_hues.append(H)
    occupied = [i for i in range(12) if use[i]]
    free = [i for i in range(12) if not use[i] and i not in vet]
    res["white_space"] = sorted(
        ({"hue": bin_label(i), "gap_to_nearest_used_bins": min((circ_gap(i, j) for j in occupied), default=6)} for i in free),
        key=lambda d: -d["gap_to_nearest_used_bins"])[:5]
    res["white_space_caveat"] = ("An empty hue may be empty because the category rejects it (taste, regulation, product cues). "
                                 "Check each against the client's attributes before using it.")
    cand = data.get("candidate")
    if cand:
        out = []
        crowded = {bin_label(i) for i in range(12) if len(use[i]) / n >= CLICHE_SHARE}
        for hx in cand.get("palette", []):
            L, C, H = oklch(hx)
            nearest = min(((dist(hx, p), c["name"], p) for c in comps for p in c.get("palette", [])), key=lambda t: t[0])
            row = {"hex": hx, "hue": bin_label(hue_bin(H)) if C >= CHROMA_MIN else "neutral",
                   "nearest_competitor": nearest[1], "distance": round(nearest[0], 3)}
            out.append(row)
            if C >= CHROMA_MIN and any(min(abs(H - v), 360 - abs(H - v)) <= VETO_TOL for v in veto_hues):
                findings.append(("BLOCK", "VETOED_HUE", f"{hx} (hue {H:.0f}) is within {VETO_TOL} degrees of a vetoed hue"))
            if C >= CHROMA_MIN and row["hue"] in crowded:
                findings.append(("WARN", "CROWDED_HUE", f"{hx} sits in hue {row['hue']}, used by {len(use[hue_bin(H)])}/{n} competitors"))
            if C >= CHROMA_MIN and nearest[0] < NEAR_DIST:
                findings.append(("WARN", "NEAR_COMPETITOR", f"{hx} is {nearest[0]:.3f} from {nearest[1]}'s {nearest[2]}"))
        for c in comps:
            close = [hx for hx in cand.get("palette", []) if any(dist(hx, p) < CLONE_DIST for p in c.get("palette", []))]
            if len(close) >= 2:
                findings.append(("BLOCK", "PALETTE_CLONE", f"{len(close)} candidate colours are near-identical to {c['name']}'s palette"))
        res["candidate"] = out
    return res, findings


def render(res, findings, verdict):
    L = [f"Verdict: {verdict}   competitors: {res['n']}", "Hue map (share of competitors): " +
         (", ".join(f"{k}: {v:.0%}" for k, v in sorted(res["hue_map"].items(), key=lambda kv: int(kv[0].split('-')[0]))) or "none")]
    for k, v in res["cliches"].items():
        L.append(f"Clichés ({k}): " + (", ".join(v) if v else "none at 40% or more"))
    L.append("White space (hue degrees, widest gap first): " + (", ".join(f"{w['hue']} (gap {w['gap_to_nearest_used_bins']})" for w in res["white_space"]) or "none"))
    L.append("  " + res["white_space_caveat"])
    for r in res.get("candidate", []):
        L.append(f"Candidate {r['hex']}: hue {r['hue']}, nearest {r['nearest_competitor']} at {r['distance']}")
    for lvl, code, msg in findings:
        L.append(f"  [{lvl}] {code}: {msg}")
    return "\n".join(L)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Competitor matrix: clichés, crowded hues and white space, in OKLCH.")
    ap.add_argument("--input", help="competitors JSON (see assets/example_competitors.json)")
    ap.add_argument("--sample", action="store_true", help="run on assets/example_competitors.json")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_competitors.json") if a.sample else a.input
    if not path:
        ap.error("provide --input or --sample")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        comps = data["competitors"]
        findings = []
        for c in comps:
            if not str(c.get("source", "")).strip() or not str(c.get("date", "")).strip():
                findings.append(("BLOCK", "UNSOURCED", f"{c.get('name')}: a competitor needs a source and a date"))
        if len(comps) < 5:
            msg = f"INSUFFICIENT: {len(comps)} competitor(s). Five or more make a category."
            print(msg if a.output == "human" else json.dumps({"verdict": "INSUFFICIENT", "message": msg}))
            sys.exit(3)
        if len(comps) > 12:
            findings.append(("WARN", "TOO_MANY", f"{len(comps)} competitors dilute the reading; keep the 12 that matter"))
        res, more = analyse(data)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    findings += more
    code = 4 if any(f[0] == "BLOCK" for f in findings) else (2 if findings else 0)
    verdict = {0: "OK", 2: "WARNINGS", 4: "BLOCKED"}[code]
    if a.output == "json":
        print(json.dumps({"verdict": verdict, **res, "findings": [{"level": l, "code": c, "message": m} for l, c, m in findings]}, indent=2, ensure_ascii=False))
    else:
        print(render(res, findings, verdict))
    sys.exit(code)


if __name__ == "__main__":
    main()
