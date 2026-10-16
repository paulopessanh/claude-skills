#!/usr/bin/env python3
"""palette_paths.py — turn colour candidates found in the briefing and research into 3 defensible paths to vote on.

The reading of briefing, kick-off, meeting transcripts, market research and references is done by a person or by Claude.
Each colour found goes in as a candidate with its evidence and a weight from 0 to 1. This tool does the part that must
be repeatable: it drops vetoed hues, scores every primary/secondary/accent triple and returns three paths that differ on
purpose, each with its majority use.

Score of a triple (0 to 1): 0.45 evidence + 0.30 differentiation + 0.25 function.
  evidence         the weights of its three colours, primary counts double
  differentiation  OKLab distance of the primary to the closest competitor colour, capped at 0.25
  function         the primary carries text on a light and on a dark background; the accent reads on the primary;
                   the three sit more than 25 degrees apart in hue (a pair of near twins reads as one colour)

The three paths are the best triple by evidence, the best by differentiation and the best by function, kept distinct
by primary where possible. Each path states its reason, so the vote is about meaning and not about taste alone.

Rules:
  VETOED_HUE   a candidate within 25 degrees of a vetoed hex (and with chroma above 0.04) is dropped and listed
  FEW_CANDS    BLOCK  fewer than 3 usable candidates: go back to research before proposing
  WEAK_EVIDENCE WARN  a colour in the best path has weight under 0.4: the choice rests on taste, say so to the client
  SAME_PATHS   WARN   fewer than 3 distinct paths exist: the research did not open real alternatives

Majority use is a starting rule, not a law: neutral 60, primary 30, accent 10 on a light layout. A primary dark
enough to carry white text (OKLCH lightness under 0.5) leads the dark layout at 60.
The vote is decided by a person or the client. Exit: 0 ok | 1 input error | 2 warnings | 4 blocked.
Stdlib only. No network. Deterministic.
"""

import argparse
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402

WHITE, INK = "#FFFFFF", "#12161C"


def dist(a, b):
    la, lb = cl.oklab(a), cl.oklab(b)
    return sum((x - y) ** 2 for x, y in zip(la, lb)) ** 0.5


def score_triple(p, s, a, comps):
    ev = (2 * p["weight"] + s["weight"] + a["weight"]) / 4
    diff = min(min((dist(p["hex"], c) for c in comps), default=0.25), 0.25) / 0.25
    carries = (cl.contrast(WHITE, p["hex"]) >= 4.5 or cl.contrast(INK, p["hex"]) >= 4.5)
    both = cl.contrast(WHITE, p["hex"]) >= 4.5 and cl.contrast(INK, p["hex"]) >= 3.0
    acc_on_p = max(cl.contrast(a["hex"], p["hex"]), cl.contrast(a["hex"], WHITE), cl.contrast(a["hex"], INK)) >= 3.0
    hp, hs, ha = (cl.oklch(x["hex"])[2] for x in (p, s, a))
    apart = min(cl.hue_gap(hp, hs), cl.hue_gap(hp, ha), cl.hue_gap(hs, ha)) > 25
    fn = (0.4 if carries else 0) + (0.2 if both else 0) + (0.2 if acc_on_p else 0) + (0.2 if apart else 0)
    return {"evidence": ev, "differentiation": diff, "function": fn,
            "total": 0.45 * ev + 0.30 * diff + 0.25 * fn}


def majority(p):
    dark = cl.oklch(p["hex"])[0] < 0.5
    return {"light_layout": {"neutral": 60, "primary": 30, "accent": 10},
            "dark_layout": {"primary": 60, "neutral_light": 30, "accent": 10} if dark else {"neutral_dark": 60, "primary": 30, "accent": 10},
            "note": "Starting rule. Validate it on the first three applications before it becomes law."}


def run(data):
    findings, dropped = [], []
    comps = [cl.norm_hex(c) for c in data.get("competitors", [])]
    vet = [cl.norm_hex(v) for v in data.get("vetoed_hexes", [])]
    cands = []
    for c in data["candidates"]:
        c = dict(c, hex=cl.norm_hex(c["hex"]), weight=float(c.get("weight", 0.5)))
        L, C, h = cl.oklch(c["hex"])
        near = [v for v in vet if C > 0.04 and cl.oklch(v)[1] > 0.04 and cl.hue_gap(h, cl.oklch(v)[2]) < 25]
        hit = [v for v in near if dist(c["hex"], v) < 0.18]
        if hit:
            dropped.append({"name": c["name"], "hex": c["hex"], "vetoed_by": hit})
            findings.append(("INFO", "VETOED_HUE", f"{c['name']} {c['hex']} dropped: same hue and close to vetoed {hit[0]}."))
        else:
            if near:
                findings.append(("WARN", "NEAR_VETO", f"{c['name']} {c['hex']} shares a hue with vetoed {near[0]} but is visibly different. Confirm with the client that it is not read as the vetoed colour."))
            cands.append(c)
    if len(cands) < 3:
        findings.append(("BLOCK", "FEW_CANDS", "Fewer than 3 usable candidates. Go back to research before proposing a palette."))
        return {"paths": [], "dropped": dropped,
                "findings": [{"level": a, "code": b, "message": c} for a, b, c in findings], "verdict": "BLOCKED"}
    scored = []
    for p, s, a in itertools.permutations(cands, 3):
        scored.append((p, s, a, score_triple(p, s, a, comps)))
    picks, used = [], set()
    for key, label, why in (("evidence", "Fiel às evidências", "Parte das cores mais citadas no briefing, no kick-off e nas referências."),
                            ("differentiation", "Diferente do mercado", "Afasta a cor principal dos concorrentes e das cores da categoria."),
                            ("function", "Mais funcional", "Garante texto legível em fundo claro e escuro e um destaque que se lê sobre a principal.")):
        order = sorted(scored, key=lambda x: (-x[3][key], -x[3]["total"], x[0]["name"]))
        pick = next((x for x in order if x[0]["name"] not in used), order[0])
        used.add(pick[0]["name"])
        picks.append((key, label, why, pick))
    keys = {(x[3][0]["name"], x[3][1]["name"], x[3][2]["name"]) for x in picks}
    if len(keys) < 3:
        findings.append(("WARN", "SAME_PATHS", "Fewer than 3 distinct paths: the research did not open real alternatives."))
    paths = []
    for i, (key, label, why, (p, s, a, sc)) in enumerate(picks):
        weak = [c["name"] for c in (p, s, a) if c["weight"] < 0.4]
        if weak and i == 0:
            findings.append(("WARN", "WEAK_EVIDENCE", f"In the evidence path, {', '.join(weak)} has weight under 0.4: the choice rests on taste. Say so to the client."))
        paths.append({"id": "ABC"[i], "label": label, "lead_criterion": key, "why": why,
                      "primary": {"name": p["name"], "hex": p["hex"], "evidence": p.get("evidence", [])},
                      "secondary": {"name": s["name"], "hex": s["hex"], "evidence": s.get("evidence", [])},
                      "accent": {"name": a["name"], "hex": a["hex"], "evidence": a.get("evidence", [])},
                      "scores": {k: round(v, 2) for k, v in sc.items()},
                      "majority_use": majority(p),
                      "swatch": [cl.describe(x["hex"]) for x in (p, s, a)]})
    verdict = "CAVEATS" if any(f[0] == "WARN" for f in findings) else "CLEAN"
    return {"brand": data.get("brand", {}), "paths": paths, "dropped": dropped,
            "vote": {"question": "Qual caminho a marca assume?", "options": [{"id": p["id"], "label": p["label"]} for p in paths],
                     "rule": "A pessoa responsável ou o cliente decide. A ferramenta não vota."},
            "findings": [{"level": a, "code": b, "message": c} for a, b, c in findings], "verdict": verdict}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--input", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    try:
        with open(args.input, encoding="utf-8") as f:
            res = run(json.load(f))
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)
    return {"BLOCKED": 4, "CAVEATS": 2, "CLEAN": 0}[res["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
