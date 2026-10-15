#!/usr/bin/env python3
"""manual_coverage_check.py — does this brand's source answer what a complete identity manual must answer?

The blueprint (assets/manual_blueprint.v1.json) was reverse engineered from a real corporate manual: 34 needs in
7 layers, each with the question it answers, a value-free pattern and the source fields that would answer it. This
script reads a brand source file (the brand-source.v1 shape used by the ecosystem builder, or any JSON with the same
dotted paths) and reports, per need, COVERED, PARTIAL or MISSING, and names the field to add for each gap.

A check is a dotted path: "a.b" must be present and non-empty, "a.b>=N" must be a list of at least N items,
"a[].k" must be present in every item of a non-empty list.

Priorities: essential (every brand), recommended (most brands), conditional (only when its condition holds; a gap is
informational). A COVERED need means the source holds the data, not that the data is good. Review decides quality.

Exit codes: 0 every essential need covered | 1 input error | 2 essential gaps (or partial) found.
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BLUEPRINT = os.path.join(HERE, "..", "assets", "manual_blueprint.v1.json")

SAMPLE = {
    "identity": {"owner": "Founder", "tagline": "A line"},
    "history": {"paragraphs": ["One."]},
    "purpose": {"promise": "A promise"},
    "concept": {"big_idea": "An idea"},
    "personality": {"attributes": ["a", "b", "c"]},
    "petreos": [{"text": "x"}],
    "colour": {"families": [{"hex": "#112233", "meaning": "m"}], "ratio": {"light_bg": []}},
    "symbol": {"vertices": [0, 1], "slope_deg": 45, "rationale": "r", "min_size": {"print_mm": 10},
               "protection_rule": "p", "misuse": ["1", "2", "3", "4", "5", "6"]},
    "typography": {"fonts": [{"fallback": "serif", "license": "OFL"}, {"fallback": "sans", "license": "OFL"}]},
    "governance": {"owner": "Founder", "approval_flow": "Written request"},
    "applications": [{"spec": "s"}],
}


def get(node, parts):
    """Resolve a path. Returns (found, value) where value may be a list for [] segments."""
    cur = node
    for i, p in enumerate(parts):
        if p.endswith("[]"):
            key = p[:-2]
            cur = cur.get(key) if isinstance(cur, dict) else None
            if not isinstance(cur, list) or not cur:
                return False, None
            rest = parts[i + 1:]
            vals = []
            for it in cur:
                ok, v = get(it, rest) if rest else (True, it)
                if not ok:
                    return False, None
                vals.append(v)
            return True, vals
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return False, None
    return True, cur


def present(v):
    if v is None:
        return False
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return True
    if isinstance(v, (str, list, dict)):
        return bool(v if not isinstance(v, str) else v.strip())
    return bool(v)


def check(src, expr):
    m = re.fullmatch(r"(.+?)>=(\d+)", expr)
    n = int(m.group(2)) if m else None
    path = m.group(1) if m else expr
    ok, v = get(src, path.split("."))
    if not ok:
        return False
    if n is not None:
        return isinstance(v, list) and len(v) >= n
    if isinstance(v, list):
        return bool(v) and all(present(x) for x in v)
    return present(v)


def evaluate(src, bp):
    rows = []
    for nd in bp["needs"]:
        res = [(c, check(src, c)) for c in nd["checks"]]
        hit = sum(1 for _, ok in res if ok)
        status = "COVERED" if hit == len(res) else ("PARTIAL" if hit else "MISSING")
        rows.append({"id": nd["id"], "layer": nd["layer"], "need": nd["need"], "priority": nd["priority"],
                     "condition": nd.get("condition"), "status": status, "found": [c for c, ok in res if ok],
                     "absent": [c for c, ok in res if not ok], "proposed_field": nd.get("proposed_field"),
                     "answers": nd["answers"], "pages": nd.get("pages")})
    return rows


def summarize(rows, bp):
    layers = {l["id"]: {"name": l["name"], "covered": 0, "total": 0} for l in bp["layers"]}
    for r in rows:
        layers[r["layer"]]["total"] += 1
        layers[r["layer"]]["covered"] += r["status"] == "COVERED"
    ess = [r for r in rows if r["priority"] == "essential"]
    return {"layers": layers, "essential_total": len(ess), "essential_covered": sum(r["status"] == "COVERED" for r in ess),
            "essential_gaps": [r["id"] for r in ess if r["status"] != "COVERED"]}


def render(rows, s):
    out = ["MANUAL COVERAGE", ""]
    for lid, l in s["layers"].items():
        out.append(f"  {lid} {l['name']:<28} {l['covered']}/{l['total']} covered")
    out.append("")
    out.append(f"  Essential needs covered: {s['essential_covered']}/{s['essential_total']}")
    for pri, title in (("essential", "ESSENTIAL GAPS"), ("recommended", "RECOMMENDED GAPS"), ("conditional", "CONDITIONAL (informational)")):
        gaps = [r for r in rows if r["priority"] == pri and r["status"] != "COVERED"]
        if not gaps:
            continue
        out += ["", title]
        for r in gaps:
            cond = f" [{r['condition']}]" if r["condition"] else ""
            out.append(f"  {r['id']} {r['status']:<7} {r['need']}{cond}")
            out.append(f"        asks: {r['answers']}")
            if r["proposed_field"]:
                out.append(f"        add:  {r['proposed_field']}")
            else:
                out.append(f"        absent: {', '.join(r['absent'])}")
    out += ["", "Covered means the source holds the data. Review decides whether it is good."]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Check a brand source against the reverse engineered manual blueprint.")
    ap.add_argument("--source", help="brand source JSON (brand-source.v1 shape)")
    ap.add_argument("--blueprint", default=DEFAULT_BLUEPRINT, help="manual-blueprint.v1 JSON")
    ap.add_argument("--sample", action="store_true", help="run on a small built-in source")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    try:
        bp = json.load(open(a.blueprint, encoding="utf-8"))
        src = SAMPLE if a.sample else json.load(open(a.source, encoding="utf-8"))
    except (OSError, ValueError, TypeError) as e:
        print(f"input error: {e}", file=sys.stderr)
        return 1
    if not a.sample and not a.source:
        print("input error: give --source or --sample", file=sys.stderr)
        return 1
    rows = evaluate(src, bp)
    s = summarize(rows, bp)
    if a.output == "json":
        print(json.dumps({"summary": s, "needs": rows}, ensure_ascii=False, indent=2))
    else:
        print(render(rows, s))
    return 2 if s["essential_gaps"] else 0


if __name__ == "__main__":
    sys.exit(main())
