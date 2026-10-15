#!/usr/bin/env python3
"""evidence_ledger.py — gate every claim in a brand reverse-engineering case.

Reverse engineering a brand from the outside gives you outputs (logo, pack, site, posts)
and almost never the inputs (brief, budget, rejected routes, client politics). The most
common failure is writing an intent as if it were a fact: "the brief asked for X".
This tool separates three classes of claim and refuses the ones that cheat:

  observed    — you can point at an artifact that shows it.
  inferred    — the best explanation of artifacts; needs a rival explanation on record.
  hypothesis  — a guess about something unobservable; allowed, never promoted.

Rules (BLOCK = exit 4, WARN = exit 2):
  BAD_FIELD            BLOCK  unknown stage/class/confidence, or duplicate claim id
  UNKNOWN_EVIDENCE     BLOCK  claim cites an artifact id that is not in the case
  NO_EVIDENCE          BLOCK  observed/inferred claim cites nothing
  INTENT_AS_FACT       BLOCK  'observed' claim in briefing/research/strategy with no
                              interview, case study, guidelines or brief document behind it
  NO_RIVAL             BLOCK  inferred claim with no alternative explanation recorded
  THIN_INFERENCE       WARN   inferred claim resting on a single artifact
  SELF_REPORT_ONLY     WARN   every cited artifact is a self-report (post-hoc rationalisation risk)
  OVERCONFIDENT_INTENT WARN   inferred claim about intent stages marked high confidence
  HYPOTHESIS_CONFIDENT WARN   a hypothesis marked medium/high confidence

Exit codes: 0 SOUND | 1 input error | 2 CAUTION | 3 INSUFFICIENT (no artifacts) | 4 UNSOUND
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import sys

STAGES = ["briefing", "research", "strategy", "concept",
          "visual_direction", "system", "applications", "guidelines"]
INTENT_STAGES = {"briefing", "research", "strategy"}
INTENT_KINDS = {"interview", "case_study", "guidelines", "brief_document"}
CLASSES = {"observed", "inferred", "hypothesis"}
CONFIDENCE = {"high", "medium", "low"}


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def check(case):
    arts = {a.get("id"): a for a in case.get("artifacts", [])}
    findings, seen = [], set()

    def add(level, code, cid, msg):
        findings.append({"level": level, "code": code, "claim": cid, "message": msg})

    for c in case.get("claims", []):
        cid = c.get("id", "?")
        cls, stage = c.get("class"), c.get("stage")
        conf = c.get("confidence", "low")
        ev = c.get("evidence", []) or []
        if cid in seen:
            add("BLOCK", "BAD_FIELD", cid, "duplicate claim id")
        seen.add(cid)
        if stage not in STAGES or cls not in CLASSES or conf not in CONFIDENCE:
            add("BLOCK", "BAD_FIELD", cid, f"stage={stage!r} class={cls!r} confidence={conf!r} not allowed")
            continue
        missing = [e for e in ev if e not in arts]
        if missing:
            add("BLOCK", "UNKNOWN_EVIDENCE", cid, f"cites unknown artifact(s): {', '.join(missing)}")
        if cls in ("observed", "inferred") and not ev:
            add("BLOCK", "NO_EVIDENCE", cid, f"{cls} claim cites no artifact; reclassify as hypothesis")
        cited = [arts[e] for e in ev if e in arts]
        if cls == "observed" and stage in INTENT_STAGES and not any(a.get("kind") in INTENT_KINDS for a in cited):
            add("BLOCK", "INTENT_AS_FACT", cid,
                f"'{stage}' is intent, not output. Visual artifacts cannot show it. "
                "Cite an interview, case study, guidelines or brief document, or reclassify as inferred/hypothesis")
        if cls == "inferred":
            if not c.get("alternatives"):
                add("BLOCK", "NO_RIVAL", cid, "inferred claim needs at least one rival explanation")
            if len(set(ev)) < 2:
                add("WARN", "THIN_INFERENCE", cid, "inference rests on one artifact; find a second or lower the confidence")
            if stage in INTENT_STAGES and conf == "high":
                add("WARN", "OVERCONFIDENT_INTENT", cid, "intent inferred from outputs should not be high confidence")
        if cited and cls != "hypothesis" and all(a.get("source_type") == "self_report" for a in cited):
            add("WARN", "SELF_REPORT_ONLY", cid, "all evidence is self-reported by the makers; treat as their story, not as proof")
        if cls == "hypothesis" and conf in ("medium", "high"):
            add("WARN", "HYPOTHESIS_CONFIDENT", cid, "a hypothesis cannot be medium/high confidence; gather evidence and reclassify")
    return findings


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Gate the claims of a brand reverse-engineering case file.")
    ap.add_argument("--input", help="case file JSON (see assets/example_reference.json)")
    ap.add_argument("--sample", action="store_true", help="run on assets/example_reference.json")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    args = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_reference.json") if args.sample else args.input
    if not path:
        ap.error("provide --input or --sample")
    case = load(path)

    if not case.get("artifacts"):
        result = {"verdict": "INSUFFICIENT", "reason": "no artifacts in the case; collect observable material first"}
        print(json.dumps(result, indent=2) if args.output == "json" else "INSUFFICIENT: no artifacts. Collect observable material first.")
        sys.exit(3)

    findings = check(case)
    claims = case.get("claims", [])
    by_class = {k: sum(1 for c in claims if c.get("class") == k) for k in sorted(CLASSES)}
    blocks = [f for f in findings if f["level"] == "BLOCK"]
    warns = [f for f in findings if f["level"] == "WARN"]
    verdict, code = ("UNSOUND", 4) if blocks else (("CAUTION", 2) if warns else ("SOUND", 0))
    result = {"verdict": verdict, "claims_by_class": by_class, "blocks": len(blocks),
              "warnings": len(warns), "findings": findings}
    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Verdict: {verdict}   claims: {by_class}   blocks: {len(blocks)}   warnings: {len(warns)}")
        for f in findings:
            print(f"  [{f['level']}] {f['claim']} {f['code']}: {f['message']}")
        if code == 0:
            print("  No findings. Claims are separated and cited.")
    sys.exit(code)


if __name__ == "__main__":
    main()
