#!/usr/bin/env python3
"""brief_gap_analyzer.py — find what a branding brief does not yet know, before anyone designs anything.

A confusing brief contaminates every later step. This tool reads a structured brief and reports:

  GAP           a required field is empty (priority: critical / important / useful)
  UNSOURCED     BLOCK  a field marked `fact` has no usable source
  BAD_FIELD     BLOCK  a field has no valid class (`fact` or `hypothesis`)
  FUTURE_DATE   BLOCK  a source dated after the as-of date
  STALE_SOURCE  WARN   a source older than 180 days
  DIVERGENCE    WARN   one decisor likes what another dislikes
  TIME_IMPOSSIBLE BLOCK  a relationship that began before the company existed, or longer than it existed
  TIME_INCOHERENT WARN   stated years do not match the start year (more than 1 year apart)

It also lists the client's dislikes as `vetoes` (they become hard constraints for colour and
shape work) and writes a kick-off agenda: critical gaps first, then divergences, then every
hypothesis to validate, then stale sources to refresh. Nothing is invented: a gap stays a gap.

Exit codes: 0 READY | 1 input error | 2 GAPS (warnings or gaps, no blocks) | 3 INSUFFICIENT (under 50% of required fields) | 4 BLOCKED
Stdlib only. No network. Deterministic.
"""

import argparse
import datetime
import json
import os
import re
import sys

REQUIRED = {
    "scope_contracted": "critical", "ambition": "critical", "audience": "critical", "name_origin": "critical",
    "company_history": "important", "services": "important", "differentiators": "important", "current_brand": "important",
    "competitors": "important", "deadlines": "useful", "clients_and_proof": "useful", "territories": "useful",
}
BAD_SOURCES = {"", "assumed", "unknown", "none", "n/a", "tbd"}


def toks(items):
    return {w for x in items for w in re.findall(r"[a-z0-9à-ÿ]+", str(x).lower()) if len(w) >= 4}


def parse_date(s):
    try:
        return datetime.date.fromisoformat(str(s))
    except ValueError:
        return None


def analyse(b, as_of):
    findings, agenda = [], []

    def add(level, code, where, msg):
        findings.append({"level": level, "code": code, "where": where, "message": msg})

    fields = b.get("fields", {})
    filled = 0
    for key, prio in REQUIRED.items():
        f = fields.get(key)
        if not f or not str(f.get("value", "")).strip():
            add("GAP", "GAP", key, f"{prio} field is empty")
            continue
        filled += 1
    dec = b.get("decisors", [])
    if dec:
        filled += 1
    else:
        add("GAP", "GAP", "decisors", "critical field is empty: who approves?")
    total = len(REQUIRED) + 1
    for key, f in fields.items():
        cls, src = f.get("class"), str(f.get("source", "")).strip().lower()
        if cls not in ("fact", "hypothesis"):
            add("BLOCK", "BAD_FIELD", key, f"class must be fact or hypothesis, got {cls!r}")
            continue
        if cls == "fact" and src in BAD_SOURCES:
            add("BLOCK", "UNSOURCED", key, "a fact needs a source; give one or mark it hypothesis")
        if cls == "hypothesis":
            agenda.append((3, f"Validate hypothesis: {key} = {str(f.get('value', ''))[:80]}"))
        d = parse_date(f.get("date")) if f.get("date") else None
        if f.get("date") and d is None:
            add("BLOCK", "BAD_FIELD", key, f"date {f.get('date')!r} is not YYYY-MM-DD")
        elif d and d > as_of:
            add("BLOCK", "FUTURE_DATE", key, f"source dated {d}, after {as_of}")
        elif d and (as_of - d).days > 180:
            add("WARN", "STALE_SOURCE", key, f"source is {(as_of - d).days} days old")
            agenda.append((4, f"Refresh stale source: {key}"))
    for i, a in enumerate(dec):
        for c in dec[i + 1:]:
            for x, y in ((a, c), (c, a)):
                shared = toks(x.get("likes", [])) & toks(y.get("dislikes", []))
                if shared:
                    add("WARN", "DIVERGENCE", f"{x.get('name')} vs {y.get('name')}",
                        f"{x.get('name')} likes what {y.get('name')} dislikes: {', '.join(sorted(shared))}")
                    agenda.append((2, f"Resolve divergence: {x.get('name')} vs {y.get('name')} on {', '.join(sorted(shared))}"))
    founded = b.get("founded_year")
    for t in b.get("timeline", []):
        since, yrs = t.get("since_year"), t.get("years")
        if since is None or yrs is None:
            continue
        if founded is not None and since < founded:
            add("BLOCK", "TIME_IMPOSSIBLE", t.get("label"), f"starts in {since}, before the company was founded in {founded}")
        elif founded is not None and yrs > as_of.year - founded + 1:
            add("BLOCK", "TIME_IMPOSSIBLE", t.get("label"), f"{yrs} years is longer than the company has existed ({as_of.year - founded + 1} at most)")
        elif abs(yrs - (as_of.year - since)) > 1:
            add("WARN", "TIME_INCOHERENT", t.get("label"), f"{yrs} years stated, but since {since} gives {as_of.year - since}")
            agenda.append((2, f"Fix the number of years: {t.get('label')}"))
    for g in [f for f in findings if f["code"] == "GAP"]:
        prio = REQUIRED.get(g["where"], "critical")
        agenda.append(({"critical": 0, "important": 1}.get(prio, 5), f"Ask: {g['where']} ({prio})"))
    vetoes = sorted({d for x in dec for d in x.get("dislikes", [])})
    agenda.sort(key=lambda t: t[0])
    return findings, [a for _, a in agenda], filled, total, vetoes


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Find the gaps, contradictions and unsourced facts in a branding brief.")
    ap.add_argument("--input", help="brief JSON (see assets/example_brief.json)")
    ap.add_argument("--sample", action="store_true", help="run on assets/example_brief.json")
    ap.add_argument("--as-of", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_brief.json") if a.sample else a.input
    if not path:
        ap.error("provide --input or --sample")
    try:
        with open(path, encoding="utf-8") as fh:
            brief = json.load(fh)
        as_of = datetime.date.fromisoformat(a.as_of or brief.get("as_of") or datetime.date.today().isoformat())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    findings, agenda, filled, total, vetoes = analyse(brief, as_of)
    blocks = [f for f in findings if f["level"] == "BLOCK"]
    if filled / total < 0.5:
        verdict, code = "INSUFFICIENT", 3
    elif blocks:
        verdict, code = "BLOCKED", 4
    elif findings:
        verdict, code = "GAPS", 2
    else:
        verdict, code = "READY", 0
    res = {"verdict": verdict, "required_coverage": f"{filled}/{total}", "findings": findings, "vetoes": vetoes, "kickoff_agenda": agenda}
    if a.output == "json":
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"Verdict: {verdict}   required fields filled: {filled}/{total}   as of {as_of}")
        for f in findings:
            print(f"  [{f['level']}] {f['code']} {f['where']}: {f['message']}")
        if vetoes:
            print("  Client dislikes (hard constraints for colour and shape): " + "; ".join(vetoes))
        if agenda:
            print("Kick-off agenda:")
            for i, x in enumerate(agenda, 1):
                print(f"  {i}. {x}")
    sys.exit(code)


if __name__ == "__main__":
    main()
