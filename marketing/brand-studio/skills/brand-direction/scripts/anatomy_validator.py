#!/usr/bin/env python3
"""anatomy_validator.py — check the anatomy of a brand: type, name, symbol, descriptor, tagline, slogan, hookline.

Anatomy (the working standard this skill uses):
  type        nominative (name only), figurative (symbol only), mixed (symbol + name), three_dimensional
  descriptor  REQUIRED  says what the company does, in plain words
  tagline     REQUIRED  carries the essence and the positioning
  slogan      optional  tied to a campaign or a product
  hookline    optional  a repeatable phrase made for buzz; needs a marketing strategy behind it

Rules:
  BAD_TYPE / MISSING_PART  BLOCK  unknown type, or the type needs a part that is missing (mixed needs symbol + name)
  NO_DESCRIPTOR            BLOCK  a descriptor is required in every type
  NO_TAGLINE               BLOCK  a tagline is required
  TAGLINE_IS_DESCRIPTOR    BLOCK  the tagline repeats the descriptor
  DESCRIPTOR_LENGTH        WARN   outside 2-6 words
  VAGUE_DESCRIPTOR         WARN   leans on words that say nothing (solutions, quality, excellence, leader ...)
  DESCRIPTOR_HAS_NAME      WARN   the descriptor repeats the brand name
  TAGLINE_LENGTH           WARN   outside 2-9 words
  TAGLINE_OVERLAP          WARN   more than half the tagline's words are in the descriptor
  TAGLINE_HAS_NAME         WARN   the tagline repeats the brand name
  UNDECIDED                WARN   slogan or hookline has no explicit include / exclude decision with a reason
  HOOKLINE_NO_STRATEGY     WARN   a hookline is included without a marketing strategy flag
  CANDIDATE_COUNT          WARN   with --stage candidates: 3-5 descriptor and 3-5 tagline candidates are expected

Exit codes: 0 OK | 1 input error | 2 WARNINGS | 4 BLOCKED
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

TYPES = ("nominative", "figurative", "mixed", "three_dimensional")
VAGUE = {"solutions", "solucoes", "quality", "qualidade", "excellence", "excelencia", "innovation", "inovacao", "leader", "lider",
         "best", "melhor", "premium", "world-class", "integrated", "integradas", "global", "inovadoras", "innovative"}


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s).lower()) if not unicodedata.combining(c))


def words(s):
    return re.findall(r"[a-z0-9]+", fold(s))


def check(d, stage):
    out = []
    add = lambda lvl, code, msg: out.append((lvl, code, msg))
    t, name = d.get("type"), (d.get("name") or "").strip()
    if t not in TYPES:
        add("BLOCK", "BAD_TYPE", f"type must be one of {', '.join(TYPES)}")
    else:
        if t in ("mixed", "nominative") and not name:
            add("BLOCK", "MISSING_PART", f"a {t} brand needs a name")
        if t in ("mixed", "figurative") and not d.get("symbol"):
            add("BLOCK", "MISSING_PART", f"a {t} brand needs a symbol")
    desc = d.get("descriptor_candidates") if stage == "candidates" else [d.get("descriptor")] if d.get("descriptor") else []
    tags = d.get("taglines", [])
    if stage == "candidates":
        desc = desc or []
        if not 3 <= len(desc) <= 5 or not 3 <= len(tags) <= 5:
            add("WARN", "CANDIDATE_COUNT", f"{len(desc)} descriptor and {len(tags)} tagline candidates; 3-5 of each are expected")
    if not desc:
        add("BLOCK", "NO_DESCRIPTOR", "a descriptor is required: what the company does, in plain words")
    if not tags:
        add("BLOCK", "NO_TAGLINE", "a tagline is required: the essence and the positioning")
    nw = set(words(name))
    for ds in desc:
        w = words(ds)
        if not 2 <= len(w) <= 6:
            add("WARN", "DESCRIPTOR_LENGTH", f"'{ds}' has {len(w)} words; 2-6 read as a descriptor")
        if set(w) & VAGUE:
            add("WARN", "VAGUE_DESCRIPTOR", f"'{ds}' uses a word that says nothing: {', '.join(sorted(set(w) & VAGUE))}")
        if nw and nw <= set(w):
            add("WARN", "DESCRIPTOR_HAS_NAME", f"'{ds}' repeats the brand name")
    for tg in tags:
        w = words(tg)
        if not 2 <= len(w) <= 9:
            add("WARN", "TAGLINE_LENGTH", f"'{tg}' has {len(w)} words; 2-9 read as a tagline")
        if nw and nw <= set(w):
            add("WARN", "TAGLINE_HAS_NAME", f"'{tg}' repeats the brand name")
        for ds in desc:
            dw = set(words(ds))
            if fold(tg).strip() == fold(ds).strip():
                add("BLOCK", "TAGLINE_IS_DESCRIPTOR", f"tagline '{tg}' repeats the descriptor")
            elif w and len(set(w) & dw) / len(set(w)) > 0.5:
                add("WARN", "TAGLINE_OVERLAP", f"tagline '{tg}' reuses most of the descriptor '{ds}'")
    for key in ("slogan", "hookline"):
        v = d.get(key)
        if not isinstance(v, dict) or v.get("decision") not in ("include", "exclude") or len(str(v.get("reason", "")).strip()) < 5:
            add("WARN", "UNDECIDED", f"{key}: record include or exclude, with the reason")
        elif v["decision"] == "include" and not v.get("text"):
            add("WARN", "UNDECIDED", f"{key} is included but has no text")
        if key == "hookline" and isinstance(v, dict) and v.get("decision") == "include" and not v.get("marketing_strategy"):
            add("WARN", "HOOKLINE_NO_STRATEGY", "a hookline works only with a marketing strategy behind it")
    return list(dict.fromkeys(out))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Validate the anatomy of a brand.")
    ap.add_argument("--input", help="anatomy JSON (see assets/example_anatomy.json)")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--stage", choices=["candidates", "final"], default="final")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_anatomy.json") if a.sample else a.input
    if not path:
        ap.error("provide --input or --sample")
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    f = check(d, a.stage)
    code = 4 if any(x[0] == "BLOCK" for x in f) else (2 if f else 0)
    verdict = {0: "OK", 2: "WARNINGS", 4: "BLOCKED"}[code]
    if a.output == "json":
        print(json.dumps({"verdict": verdict, "stage": a.stage, "findings": [{"level": l, "code": c, "message": m} for l, c, m in f]}, indent=2, ensure_ascii=False))
    else:
        print(f"Verdict: {verdict} (stage: {a.stage})")
        for l, c, m in f:
            print(f"  [{l}] {c}: {m}")
        if not f:
            print("  Anatomy is complete and decided.")
    sys.exit(code)


if __name__ == "__main__":
    main()
