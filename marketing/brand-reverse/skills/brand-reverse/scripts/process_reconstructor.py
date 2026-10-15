#!/usr/bin/env python3
"""process_reconstructor.py — rebuild the creative process behind a brand, then plan yours.

A brand identity is the last link of a chain: brief -> research -> strategy -> concept ->
visual direction -> system -> applications -> guidelines. From outside you see the tail.
This tool works the chain both ways.

  reconstruct (default)
    Per stage: LOST / HYPOTHESIS_ONLY / INFERRED / RECOVERED, decision coverage against the
    decisions that stage must have made, back-propagated requirements (what the visible
    outputs force to have been true upstream, always labelled hypothesis), and the question
    to put to someone who was in the room for every stage that outsiders cannot see.

  --plan
    The creative process for YOUR brand: every stage with its decisions, a gate question,
    and the value-free `pattern` lessons the reference supplied for those decisions.
    Patterns are method, not content. Run method_transfer_guard.py before using them.

Refusals:
  exit 4  claim cites an unknown artifact, uses an unknown stage/decision, or `implies` a
          requirement at a stage that is not upstream of the claim
  exit 3  fewer than three stages are INFERRED or RECOVERED: there is no process to speak of,
          only a few isolated outputs

Exit codes: 0 OK | 1 input error | 2 HOLES (an output stage is LOST) | 3 INSUFFICIENT | 4 INVALID
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import sys

STAGES = ["briefing", "research", "strategy", "concept",
          "visual_direction", "system", "applications", "guidelines"]
OUTPUT_STAGES = {"visual_direction", "system", "applications", "guidelines"}
DECISIONS = {
    "briefing": ["objectives", "audience_scope", "constraints"],
    "research": ["market_audit", "audience_insight", "competitor_map"],
    "strategy": ["positioning", "personality", "promise", "audience"],
    "concept": ["big_idea", "naming_logic", "voice"],
    "visual_direction": ["logo_concept", "color_logic", "type_logic", "imagery_style"],
    "system": ["grid_layout", "lockups", "tokens", "motion"],
    "applications": ["key_touchpoints", "packaging_signage", "digital"],
    "guidelines": ["clear_space_misuse", "usage_rules", "governance"],
}
GATE = {
    "briefing": "Can the client state, in one sentence, what must be different in the market after this project?",
    "research": "Can you name one audience truth and one category convention that you will break on purpose?",
    "strategy": "Can positioning, personality and promise each be tested against a competitor's version?",
    "concept": "Does the idea survive being said aloud without any image?",
    "visual_direction": "Can each visual choice be traced to a strategy line, with no choice left to taste?",
    "system": "Could a stranger extend the identity to an unseen touchpoint using only the tokens and rules?",
    "applications": "Does the identity still read on the hardest touchpoint (smallest, cheapest, most cluttered)?",
    "guidelines": "Do the rules say what to do when two rules conflict, and who decides?",
}
ASK = {
    "briefing": "What did the brief ask for, what was the budget and timeline, and what was off the table?",
    "research": "What research was done, and which finding changed the direction?",
    "strategy": "Which positioning routes were considered and why were they rejected?",
    "concept": "How many ideas reached the client, and what made this one win?",
    "visual_direction": "Which visual routes were presented, and what did the client change?",
    "system": "Which rules were set before the first application, and which came from applications?",
    "applications": "Which touchpoint broke the system first, and what changed because of it?",
    "guidelines": "What is policed in practice, and what did the client ignore?",
}
RANK = {"LOST": 0, "HYPOTHESIS_ONLY": 1, "INFERRED": 2, "RECOVERED": 3}


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def validate(case):
    arts = {a.get("id") for a in case.get("artifacts", [])}
    errs = []
    for c in case.get("claims", []):
        cid, st = c.get("id", "?"), c.get("stage")
        if st not in STAGES:
            errs.append(f"{cid}: unknown stage {st!r}")
            continue
        dec = c.get("decision")
        if dec and dec not in DECISIONS[st]:
            errs.append(f"{cid}: decision {dec!r} is not a {st} decision ({', '.join(DECISIONS[st])})")
        for e in c.get("evidence", []) or []:
            if e not in arts:
                errs.append(f"{cid}: cites unknown artifact {e}")
        for imp in c.get("implies", []) or []:
            tgt = imp.get("stage")
            if tgt not in STAGES or STAGES.index(tgt) >= STAGES.index(st):
                errs.append(f"{cid}: implies a requirement at {tgt!r}, which is not upstream of {st}")
    return errs


def reconstruct(case):
    claims = case.get("claims", [])
    stages, back = [], {s: [] for s in STAGES}
    for c in claims:
        for imp in c.get("implies", []) or []:
            back[imp["stage"]].append({"requirement": imp["requirement"], "derived_from": c["id"],
                                       "class": "hypothesis"})
    for s in STAGES:
        cs = [c for c in claims if c["stage"] == s]
        classes = {c["class"] for c in cs}
        status = ("RECOVERED" if "observed" in classes else "INFERRED" if "inferred" in classes
                  else "HYPOTHESIS_ONLY" if cs else "LOST")
        covered = sorted({c.get("decision") for c in cs if c.get("decision") and c["class"] != "hypothesis"})
        row = {"stage": s, "status": status, "output_stage": s in OUTPUT_STAGES,
               "claims": [c["id"] for c in cs],
               "decisions_covered": covered,
               "decisions_open": [d for d in DECISIONS[s] if d not in covered],
               "back_propagated": back[s]}
        if status in ("LOST", "HYPOTHESIS_ONLY") or row["decisions_open"]:
            row["ask_someone_who_was_there"] = ASK[s]
        stages.append(row)
    return stages


def plan(case, stages):
    claims = case.get("claims", [])
    out = []
    for row in stages:
        s = row["stage"]
        pats = [{"decision": c.get("decision"), "pattern": c["pattern"], "source_claim": c["id"],
                 "class": c["class"]} for c in claims if c["stage"] == s and c.get("pattern")]
        out.append({"stage": s, "decisions_to_make": DECISIONS[s], "gate": GATE[s], "borrowed_patterns": pats})
    return out


def render(stages, plan_rows, plan_mode):
    lines = []
    if not plan_mode:
        for r in stages:
            lines.append(f"{r['stage']:<17} {r['status']:<16} decisions {len(r['decisions_covered'])}/{len(r['decisions_covered']) + len(r['decisions_open'])}"
                         + (f"   open: {', '.join(r['decisions_open'])}" if r["decisions_open"] else ""))
            for b in r["back_propagated"]:
                lines.append(f"    implied upstream ({b['derived_from']}, hypothesis): {b['requirement']}")
            if "ask_someone_who_was_there" in r:
                lines.append(f"    ask: {r['ask_someone_who_was_there']}")
    else:
        for p in plan_rows:
            lines.append(f"{p['stage'].upper()}")
            lines.append(f"    decide: {', '.join(p['decisions_to_make'])}")
            lines.append(f"    gate:   {p['gate']}")
            for b in p["borrowed_patterns"]:
                lines.append(f"    pattern [{b['class']}] {b['decision']}: {b['pattern']}")
    return "\n".join(lines)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Reconstruct a brand's creative process, or plan yours from it.")
    ap.add_argument("--input", help="case file JSON (see assets/example_reference.json)")
    ap.add_argument("--sample", action="store_true", help="run on assets/example_reference.json")
    ap.add_argument("--plan", action="store_true", help="emit the process plan for the new brand")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    args = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_reference.json") if args.sample else args.input
    if not path:
        ap.error("provide --input or --sample")
    case = load(path)
    errs = validate(case)
    if errs:
        print("INVALID case file:\n  " + "\n  ".join(errs), file=sys.stderr)
        sys.exit(4)
    stages = reconstruct(case)
    usable = sum(1 for r in stages if RANK[r["status"]] >= RANK["INFERRED"])
    if usable < 3:
        print(f"INSUFFICIENT: only {usable} stage(s) are inferred or recovered. "
              "Three or more are needed before a process can be claimed. Collect more artifacts.")
        sys.exit(3)
    holes = [r["stage"] for r in stages if r["output_stage"] and r["status"] == "LOST"]
    summary = {k: sum(1 for r in stages if r["status"] == k) for k in RANK}
    summary["decisions_covered"] = sum(len(r["decisions_covered"]) for r in stages)
    summary["decisions_total"] = sum(len(DECISIONS[r["stage"]]) for r in stages)
    plan_rows = plan(case, stages) if args.plan else None
    if args.output == "json":
        print(json.dumps({"summary": summary, "stages": stages, "plan": plan_rows, "output_holes": holes}, indent=2))
    else:
        print(render(stages, plan_rows, args.plan))
        if not args.plan:
            print(f"\nSummary: {summary['RECOVERED']} recovered, {summary['INFERRED']} inferred, {summary['HYPOTHESIS_ONLY']} hypothesis only, "
                  f"{summary['LOST']} lost. Decisions covered {summary['decisions_covered']}/{summary['decisions_total']}.")
        if holes:
            print(f"\nHOLES in output stages: {', '.join(holes)}. These are observable; collect more artifacts.")
    sys.exit(2 if holes else 0)


if __name__ == "__main__":
    main()
