#!/usr/bin/env python3
"""color_system.py — from candidates and a chosen path to the whole colour system, in one command.

Runs, in order: palette_paths (the three paths), tonal_scales, neutral_scale, role_map, restricted_palette,
physical_spaces, usage_rules, prohibitions and the gradients, then writes every result, one consolidated system.json
and the HTML sheet. The path is chosen by a person or by the client: --path A, B or C is required, the tool never votes.

  python3 color_system.py --candidates candidates.json --path A --out ./cor
      [--light-hex "#EDF0F2"] [--dark-hex "#12161C"] [--allow-white]

Output folder:
  system.json            everything, the source for the manual and the sheet
  json/                  one file per palette
  sistema-de-cores.html  the sheet to read, share and print
Exit: 0 clean | 1 input error | 2 caveats listed in the summary | 4 blocked (a stage refused). Stdlib only. No network.
"""

import argparse
import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402
import gradient_builder as gb  # noqa: E402
import neutral_scale as ns  # noqa: E402
import palette_paths as pp  # noqa: E402
import physical_spaces as ps  # noqa: E402
import prohibitions as pr  # noqa: E402
import restricted_palette as rp  # noqa: E402
import role_map as rm  # noqa: E402
import system_sheet as sheet  # noqa: E402
import tonal_scales as ts  # noqa: E402
import usage_rules as ur  # noqa: E402


def _build(name, bg_light, bg_dark, mono=None, duo=None):
    args = SimpleNamespace(angle=180, hue_drift=0.0, bg_light=bg_light, bg_dark=bg_dark, name=name, mono=mono, duo=duo)
    return gb.build(args)[0]


def fit_hold(fam, bg, dark):
    """The Hold for a background: the family step closest to the brand colour whose whole mono gradient keeps 3:1 on bg.
    On a dark background the candidates are the base and then its tints; on a light one, the base and then its shades."""
    kind = "Tint" if dark else "Shade"
    cands = [fam["base"]] + fam["scales"][kind]["steps"]
    for c in cands:
        res = _build("probe", bg if not dark else None, bg if dark else None, mono=c["hex"])
        bgs = res["checks"]["backgrounds"]
        if bgs["dark" if dark else "light"]["min_ratio"] >= 3.0:
            return c
    return cands[-1]


def gradients(scales, prim, sec, bg_light, bg_dark):
    """For each family and for the main pair: one gradient for light backgrounds and one for dark backgrounds."""
    fams = {f["family"]: f for f in scales["families"]}
    out = []
    for dark, mode, bg in ((False, "fundo claro", bg_light), (True, "fundo escuro", bg_dark)):
        hold = {n: fit_hold(fams[n], bg, dark) for n in (prim["name"], sec["name"])}
        for n in (prim["name"], sec["name"]):
            res = _build(f"{n} · {mode}", bg_light if not dark else None, bg_dark if dark else None, mono=hold[n]["hex"])
            res["hold_token"], res["for_background"] = hold[n]["token"], mode
            out.append(res)
        # The pair runs from the Light Source of the first family to the Anchor of the second, so the light changes too.
        a_light = cl.oklch_to_hex(*gb.mono_stops(hold[prim["name"]]["hex"])[0][1])
        b_anchor = cl.oklch_to_hex(*gb.mono_stops(hold[sec["name"]]["hex"])[-1][1])
        res = _build(f"{prim['name']} para {sec['name']} · {mode}", bg_light if not dark else None, bg_dark if dark else None,
                     duo=[a_light, b_anchor])
        res["hold_token"] = f"{hold[prim['name']]['token']} + {hold[sec['name']]['token']}"
        res["for_background"] = mode
        out.append(res)
    return out


def run(cands, path, light_hex, dark_hex, allow_white):
    stages = {}
    paths = pp.run(cands)
    stages["paths"] = paths
    if paths["verdict"] == "BLOCKED":
        return {"stages": stages, "blocked": "paths"}
    ch = next((p for p in paths["paths"] if p["id"] == path), None)
    if ch is None:
        raise KeyError(f"path {path!r} not among {[p['id'] for p in paths['paths']]}")
    prim, sec, acc = ch["primary"], ch["secondary"], ch["accent"]
    sigla = cands["brand"]["sigla"]
    fams = {"brand": cands["brand"], "families": [{"universe_name": x["name"], "hex": x["hex"]} for x in (prim, sec, acc)]}
    scales = ts.build(fams)
    neutral = ns.run(prim["hex"], sigla, light_hex, dark_hex)
    bgl = neutral["roles"]["light"]["page"]["hex"]
    bgd = neutral["roles"]["dark"]["page"]["hex"]
    roles = rm.build(scales, prim["name"], sec["name"], acc["name"], bgl, bgd)
    status = rp.build(prim["hex"], sigla, bgl, bgd, [sec["hex"], acc["hex"]], neutral["steps"][6]["hex"])
    spaces = ps.build(scales, neutral, prim["name"], sec["name"], acc["name"])
    usage = ur.build(scales, neutral, prim["name"], sec["name"], acc["name"], roles)
    prohib = pr.build(scales, neutral, status, cands.get("vetoed_hexes", []), sigla, allow_white)
    grads = gradients(scales, prim, sec, bgl, bgd)
    stages.update(scales=scales, neutral=neutral, roles=roles, status=status, spaces=spaces, usage=usage,
                  prohib=prohib, gradients=grads)
    system = {"brand": cands["brand"], "chosen": {"path": path, "primary": prim["name"], "secondary": sec["name"], "accent": acc["name"]},
              "paths": paths, "scales": scales, "neutral": neutral, "roles": roles, "status": status, "spaces": spaces,
              "usage": usage, "prohib": prohib, "gradients": grads, "note": "CMYK is approximate. PMS needs a printed match."}
    return {"stages": stages, "system": system}


def verdicts(stages):
    rows = []
    for k, v in stages.items():
        if k == "gradients":
            for g in v:
                rows.append((f"gradient {g['name']}", g["verdict"]))
        elif isinstance(v, dict) and "verdict" in v:
            rows.append((k, v["verdict"]))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--path", required=True, choices=["A", "B", "C"], help="the path chosen in the vote")
    ap.add_argument("--out", required=True)
    ap.add_argument("--light-hex")
    ap.add_argument("--dark-hex")
    ap.add_argument("--allow-white", action="store_true")
    a = ap.parse_args()
    try:
        with open(a.candidates, encoding="utf-8") as f:
            cands = json.load(f)
        res = run(cands, a.path, a.light_hex and cl.norm_hex(a.light_hex), a.dark_hex and cl.norm_hex(a.dark_hex), a.allow_white)
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e!r}", file=sys.stderr)
        return 1
    os.makedirs(os.path.join(a.out, "json"), exist_ok=True)
    for name, v in res["stages"].items():
        with open(os.path.join(a.out, "json", f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(v, f, ensure_ascii=False, indent=2)
    if "blocked" in res:
        print(f"BLOCKED at stage: {res['blocked']}")
        for f in res["stages"]["paths"]["findings"]:
            print(f"  {f['level']} {f['code']}: {f['message']}")
        return 4
    with open(os.path.join(a.out, "system.json"), "w", encoding="utf-8") as f:
        json.dump(res["system"], f, ensure_ascii=False, indent=2)
    with open(os.path.join(a.out, "sistema-de-cores.html"), "w", encoding="utf-8") as f:
        f.write(sheet.render(res["system"]))
    rows = verdicts(res["stages"])
    for k, v in rows:
        print(f"{v:8} {k}")
    ch = res["system"]["chosen"]
    print(f"path {ch['path']}: {ch['primary']} / {ch['secondary']} / {ch['accent']}  ->  {a.out}")
    return 4 if any(v == "BLOCKED" for _, v in rows) else (2 if any(v == "CAVEATS" for _, v in rows) else 0)


if __name__ == "__main__":
    sys.exit(main())
