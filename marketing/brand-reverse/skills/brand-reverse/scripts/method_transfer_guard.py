#!/usr/bin/env python3
"""method_transfer_guard.py — transfer the method, never the mark.

Reverse engineering a reference brand is legitimate. Shipping its name, palette, mark or
phrase under a new client is not, and in the same sector it is also a confusion risk.
This guard sits between the reconstruction and your new brand and checks two things.

1. Patterns are value-free. Every `pattern` in the case file must carry method only. A
   pattern containing a hex code, the reference name, one of its typefaces or one of its
   distinctive assets is a leak.                                          VALUE_LEAK  BLOCK
2. The new brief keeps its distance from the reference.
   NAME_CLOSE        BLOCK  near-match name (similarity >= 0.80, containment, or the same distinctive word;
                            generic words like casa, cafe, studio, sul are ignored)
   NAME_NEAR         WARN   similarity 0.65-0.80
   PALETTE_CLONE     BLOCK  two or more new colours within CIE76 delta-E < 10 of reference colours
   COLOUR_NEAR       WARN   one new colour within delta-E < 10 (a single colour is often category convention)
                            Neutrals (near-white, near-black, grey) are skipped: they are category defaults.
   ASSET_OVERLAP     BLOCK  an asset idea shares >= 50% of its words with a reference distinctive asset
   ASSET_NEAR        WARN   33-50% overlap
   TYPE_SAME         WARN   same typeface name as a reference face (licensed and widely shared: not a block)
   SAME_SECTOR       WARN   same sector; every near-miss above matters more, run a trademark search

Not legal advice. A clean pass here does not clear a mark; a trademark search does.

Exit codes: 0 DISTANT | 1 input error | 2 NEAR | 4 TOO_CLOSE
Stdlib only. No network. Deterministic.
"""

import argparse
import colorsys
import difflib
import json
import os
import re
import sys
import unicodedata

GENERIC = {"casa", "cafe", "studio", "estudio", "atelier", "atelie", "house", "brand", "co", "company", "labs", "lab",
           "the", "de", "da", "do", "dos", "das", "and", "e", "sul", "norte", "leste", "oeste", "north", "south",
           "east", "west", "new", "nova", "novo", "original", "artesanal", "craft", "premium"}
STOP = {"the", "a", "an", "of", "on", "in", "and", "with", "for", "to", "de", "da", "do", "com", "uma", "um", "e", "o", "a"}
HEXRE = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def ascii_lower(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()


def norm(s):
    return re.sub(r"[^a-z0-9]", "", ascii_lower(s))


def distinctive(s):
    return [w for w in re.findall(r"[a-z0-9]+", ascii_lower(s)) if w not in GENERIC and len(w) >= 4]


def tokens(s):
    return {w for w in re.findall(r"[a-z0-9À-ÿ]+", str(s).lower()) if len(w) > 2 and w not in STOP}


def lab(hexv):
    v = hexv.lstrip("#")
    rgb = [int(v[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    x = 0.4124 * lin[0] + 0.3576 * lin[1] + 0.1805 * lin[2]
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    z = 0.0193 * lin[0] + 0.1192 * lin[1] + 0.9505 * lin[2]
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x / 0.95047), f(y), f(z / 1.08883)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def is_neutral(hexv):
    v = hexv.lstrip("#")
    h, s, val = colorsys.rgb_to_hsv(*(int(v[i:i + 2], 16) / 255.0 for i in (0, 2, 4)))
    return s < 0.15 or val < 0.12 or (s < 0.25 and val > 0.92)


def delta_e(a, b):
    return sum((p - q) ** 2 for p, q in zip(lab(a), lab(b))) ** 0.5


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def leaks(ref, claims):
    banned = [("reference name", ref.get("name")),
              *[("typeface", t.get("name")) for t in ref.get("typefaces", [])],
              *[("distinctive asset", a) for a in ref.get("distinctive_assets", [])]]
    out = []
    for c in claims:
        pat = c.get("pattern")
        if not pat:
            continue
        if HEXRE.search(pat):
            out.append(("BLOCK", "VALUE_LEAK", f"{c['id']}: pattern contains a hex code"))
        for kind, val in banned:
            if val and norm(val) and norm(val) in norm(pat):
                out.append(("BLOCK", "VALUE_LEAK", f"{c['id']}: pattern contains the {kind} '{val}'"))
    return out


def distance(ref, new):
    out = []
    refname = ref.get("name", "")
    for n in [new.get("name")] + list(new.get("naming_candidates", [])):
        if not n:
            continue
        a, b = norm(n), norm(refname)
        if not a or not b:
            continue
        ratio = difflib.SequenceMatcher(None, a, b).ratio()
        contained = min(len(a), len(b)) >= 4 and (a in b or b in a)
        shared = [(w, r) for w in distinctive(n) for r in distinctive(refname)
                  if difflib.SequenceMatcher(None, w, r).ratio() >= 0.80]
        if ratio >= 0.80 or contained:
            out.append(("BLOCK", "NAME_CLOSE", f"'{n}' vs '{refname}' (similarity {ratio:.2f})"))
        elif shared:
            out.append(("BLOCK", "NAME_CLOSE", f"'{n}' reuses the distinctive word '{shared[0][0]}' of '{refname}' "
                        f"(matches '{shared[0][1]}')"))
        elif ratio >= 0.65:
            out.append(("WARN", "NAME_NEAR", f"'{n}' vs '{refname}' (similarity {ratio:.2f})"))
    near = []
    for nc in new.get("palette", []):
        for rc in ref.get("palette", []):
            try:
                if is_neutral(nc["hex"]) or is_neutral(rc["hex"]):
                    continue
                d = delta_e(nc["hex"], rc["hex"])
            except (ValueError, KeyError):
                print(f"error: bad hex in palette: {nc!r} / {rc!r}", file=sys.stderr)
                sys.exit(1)
            if d < 10:
                near.append((nc["hex"], rc["hex"], d))
    if len({n[0] for n in near}) >= 2:
        out.append(("BLOCK", "PALETTE_CLONE", "; ".join(f"{a} ~ {b} (dE {d:.1f})" for a, b, d in near)))
    elif near:
        a, b, d = near[0]
        out.append(("WARN", "COLOUR_NEAR", f"{a} ~ {b} (dE {d:.1f})"))
    for idea in new.get("asset_ideas", []):
        ti = tokens(idea)
        for ra in ref.get("distinctive_assets", []):
            tr = tokens(ra)
            if not ti or not tr:
                continue
            j = len(ti & tr) / len(ti | tr)
            if j >= 0.5:
                out.append(("BLOCK", "ASSET_OVERLAP", f"'{idea}' vs '{ra}' (overlap {j:.0%})"))
            elif j >= 0.33:
                out.append(("WARN", "ASSET_NEAR", f"'{idea}' vs '{ra}' (overlap {j:.0%})"))
    ref_faces = {norm(t.get("name")) for t in ref.get("typefaces", [])}
    for t in new.get("typefaces", []):
        if norm(t.get("name")) in ref_faces:
            out.append(("WARN", "TYPE_SAME", f"'{t.get('name')}' is also a reference typeface"))
    if ref.get("sector") and norm(ref["sector"]) == norm(new.get("sector", "")):
        out.append(("WARN", "SAME_SECTOR", "same sector: confusion risk is higher, run a trademark search before presenting"))
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Check that a new brand takes the method of a reference, not its marks.")
    ap.add_argument("--case", help="reference case file JSON")
    ap.add_argument("--new", help="new-brand brief JSON (see assets/example_new_brief.json)")
    ap.add_argument("--sample", action="store_true", help="run on the two example assets")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    args = ap.parse_args()
    if args.sample:
        case = load(os.path.join(here, "..", "assets", "example_reference.json"))
        new = load(os.path.join(here, "..", "assets", "example_new_brief.json"))
    elif args.case and args.new:
        case, new = load(args.case), load(args.new)
    else:
        ap.error("provide --case and --new, or --sample")
    if not new.get("name"):
        print("error: the new brief needs a name", file=sys.stderr)
        sys.exit(1)
    ref = case.get("reference", {})
    findings = list(dict.fromkeys(leaks(ref, case.get("claims", [])) + distance(ref, new)))
    blocks = [f for f in findings if f[0] == "BLOCK"]
    verdict, code = ("TOO_CLOSE", 4) if blocks else (("NEAR", 2) if any(f[0] == "WARN" and f[1] != "SAME_SECTOR" for f in findings) else ("DISTANT", 0))
    res = {"verdict": verdict, "findings": [{"level": a, "code": b, "message": c} for a, b, c in findings]}
    if args.output == "json":
        print(json.dumps(res, indent=2))
    else:
        print(f"Verdict: {verdict}")
        for a, b, c in findings:
            print(f"  [{a}] {b}: {c}")
        if not findings:
            print("  No overlap found. This is not trademark clearance.")
    sys.exit(code)


if __name__ == "__main__":
    main()
