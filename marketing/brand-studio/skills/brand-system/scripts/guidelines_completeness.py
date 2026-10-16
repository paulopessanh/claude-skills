#!/usr/bin/env python3
"""guidelines_completeness.py — can a stranger apply this brand using only the guidelines?

Reads a structured guidelines spec and checks two things: is every section a team needs present,
and do the numbers agree with each other. Guidelines that look finished but contradict themselves
are worse than guidelines that are visibly incomplete, because people trust them.

Completeness (GAP, counted toward the score): logo versions (positive, negative, mono), protection area
defined relative to a part of the mark, minimum size in print and screen units, at least 6 misuse cases,
colour tokens with HEX, RGB and CMYK, usage proportion, declared contrast pairs, fonts with role + licence +
fallback, a type scale, a graphic-elements origin rule, voice traits with is / is-not, and applications.

Consistency (CONFLICT, BLOCK):
  HEX_RGB_MISMATCH   a token's RGB does not equal its HEX
  PAIR_FAILS         a contrast pair declared AA (4.5:1) or AA large (3:1) does not pass when recomputed
  DUPLICATE_TOKEN    two tokens share a name, or two names share a HEX
  UNKNOWN_PAIR_COLOUR a pair uses a HEX that is not a token or white/black
Warnings: CMYK_APPROX_ONLY when CMYK is marked approximate and no profile is named.

Exit codes: 0 COMPLETE | 1 input error | 2 GAPS or COMPLETE_WITH_WARNINGS | 4 INCONSISTENT
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import re
import sys


def hex_rgb(h):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", str(h).strip())
    if not m:
        raise ValueError(f"bad hex colour: {h!r}")
    v = m.group(1)
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def lum(rgb):
    lin = lambda c: (c / 255.0) / 12.92 if c / 255.0 <= 0.04045 else (((c / 255.0) + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(h1, h2):
    a, b = sorted((lum(hex_rgb(h1)), lum(hex_rgb(h2))), reverse=True)
    return (a + 0.05) / (b + 0.05)


def check(s):
    gaps, conflicts, warns = [], [], []
    logo = s.get("logo", {})
    pol = set(logo.get("polarities", []))
    if not {"positive", "negative", "mono"} <= pol:
        gaps.append(("LOGO_POLARITIES", "needs positive, negative and mono versions"))
    if not logo.get("versions"):
        gaps.append(("LOGO_VERSIONS", "list the versions (horizontal, vertical, symbol, wordmark)"))
    pa = logo.get("protection_area", {})
    if not pa.get("rule") or not pa.get("relative_to"):
        gaps.append(("PROTECTION_AREA", "define it relative to a part of the mark, not in loose millimetres"))
    ms = logo.get("min_size", {})
    if not (ms.get("print_mm") and ms.get("screen_px")):
        gaps.append(("MIN_SIZE", "needs print (mm) and screen (px)"))
    if len(logo.get("misuse", [])) < 6:
        gaps.append(("MISUSE", f"{len(logo.get('misuse', []))} misuse cases; at least 6 are expected"))
    col = s.get("colour", {})
    toks = col.get("tokens", [])
    if not toks:
        gaps.append(("COLOUR_TOKENS", "no colour tokens"))
    names, hexes, approx = {}, {}, []
    for t in toks:
        try:
            rgb = hex_rgb(t["hex"])
        except (ValueError, KeyError) as e:
            conflicts.append(("HEX_RGB_MISMATCH", f"{t.get('token')}: {e}"))
            continue
        if t.get("token") in names:
            conflicts.append(("DUPLICATE_TOKEN", f"token name {t['token']} appears twice"))
        names[t.get("token")] = t["hex"].upper()
        if t["hex"].upper() in hexes and hexes[t["hex"].upper()] != t.get("token"):
            conflicts.append(("DUPLICATE_TOKEN", f"{t['token']} and {hexes[t['hex'].upper()]} share {t['hex']}"))
        hexes[t["hex"].upper()] = t.get("token")
        if tuple(t.get("rgb", ())) != rgb:
            conflicts.append(("HEX_RGB_MISMATCH", f"{t.get('token')}: RGB {t.get('rgb')} is not {t['hex']} {rgb}"))
        if not t.get("cmyk"):
            gaps.append(("CMYK", f"{t.get('token')} has no CMYK"))
        elif t.get("cmyk_status") == "approx" and not col.get("icc_profile"):
            approx.append(t.get("token"))
    if approx:
        shown = ", ".join(approx[:3]) + (f" and {len(approx) - 3} more" if len(approx) > 3 else "")
        warns.append(("CMYK_APPROX_ONLY", f"{len(approx)} token(s) have approximate CMYK and no ICC profile is named ({shown}); print values need a profile and a proof"))
    if not col.get("ratio"):
        gaps.append(("COLOUR_RATIO", "state the proportion of use on light and on dark backgrounds"))
    pairs = col.get("pairs", [])
    if not pairs:
        gaps.append(("CONTRAST_PAIRS", "declare the text / background pairs and their level"))
    known = set(hexes) | {"#FFFFFF", "#000000"}
    for p in pairs:
        try:
            fg, bg = p["fg"].upper(), p["bg"].upper()
            if fg not in known or bg not in known:
                conflicts.append(("UNKNOWN_PAIR_COLOUR", f"pair {fg} on {bg} uses a colour that is not a token"))
                continue
            r = contrast(fg, bg)
            need = {"AA": 4.5, "AA_large": 3.0, "AAA": 7.0}.get(p.get("declared"))
            if need and r < need:
                conflicts.append(("PAIR_FAILS", f"{fg} on {bg} is {r:.2f}:1 but declared {p['declared']} (needs {need}:1)"))
        except (ValueError, KeyError) as e:
            conflicts.append(("PAIR_FAILS", f"bad pair {p}: {e}"))
    ty = s.get("typography", {})
    fonts = ty.get("fonts", [])
    if not fonts:
        gaps.append(("FONTS", "no fonts"))
    for f in fonts:
        missing = [k for k in ("role", "name", "license", "fallback") if not f.get(k)]
        if missing:
            gaps.append(("FONT_FIELDS", f"{f.get('name', '?')} lacks {', '.join(missing)}"))
    if not ty.get("scale"):
        gaps.append(("TYPE_SCALE", "no type scale (level, size, line height)"))
    if not s.get("graphic_elements", {}).get("origin_rule"):
        gaps.append(("ELEMENT_ORIGIN", "graphic elements need a rule that ties them to the mark's geometry"))
    traits = s.get("voice", {}).get("traits", [])
    if len(traits) < 3 or any(not (t.get("is") and t.get("is_not")) for t in traits):
        gaps.append(("VOICE", "3-4 traits, each with is and is-not"))
    if not s.get("applications"):
        gaps.append(("APPLICATIONS", "list the real applications and their rules"))
    return gaps, conflicts, warns


TOTAL_CHECKS = 17


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Check guidelines for completeness and internal consistency.")
    ap.add_argument("--input", help="guidelines spec JSON (see assets/example_guidelines.json)")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_guidelines.json") if a.sample else a.input
    if not path:
        ap.error("provide --input or --sample")
    try:
        with open(path, encoding="utf-8") as fh:
            spec = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    gaps, conflicts, warns = check(spec)
    score = max(0, round(100 * (1 - len(gaps) / TOTAL_CHECKS)))
    code = 4 if conflicts else (2 if gaps or warns else 0)
    verdict = {0: "COMPLETE", 2: "GAPS", 4: "INCONSISTENT"}[code]
    if code == 2 and not gaps:
        verdict = "COMPLETE_WITH_WARNINGS"
    res = {"verdict": verdict, "completeness_score": score, "conflicts": [{"code": c, "message": m} for c, m in conflicts],
           "gaps": [{"code": c, "message": m} for c, m in gaps], "warnings": [{"code": c, "message": m} for c, m in warns]}
    if a.output == "json":
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"Verdict: {verdict}   completeness {score}/100   conflicts {len(conflicts)}   gaps {len(gaps)}")
        for c, m in conflicts:
            print(f"  [CONFLICT] {c}: {m}")
        for c, m in gaps:
            print(f"  [GAP] {c}: {m}")
        for c, m in warns:
            print(f"  [WARN] {c}: {m}")
    sys.exit(code)


if __name__ == "__main__":
    main()
