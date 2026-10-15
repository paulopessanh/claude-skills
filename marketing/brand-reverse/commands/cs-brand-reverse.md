---
name: "cs-brand-reverse"
description: "/cs:brand-reverse — Reverse engineer how a brand and its visual identity were made, rebuild the eight-stage creative process, and plan a new brand's process without copying marks."
argument-hint: "[reference brand name or link, plus what you want to build]"
---

# /cs:brand-reverse — From the finished identity back to the process

**Command:** `/cs:brand-reverse [reference brand, and the new brand you are working on]`

## When to run

- "Como essa identidade visual foi criada?" / "reconstruir o processo criativo desta marca"
- Before briefing a client, to learn what a reference brand actually decided
- To audit your own finished project and recover the rationale you never wrote down

## What you get

1. **A case file** of observable artifacts, each marked primary, secondary or self-report.
2. **Colour and type logic** with a rival explanation beside every reading.
3. **A gated claim list**: observed, inferred, hypothesis. Intent is never presented as fact.
4. **The eight-stage chain**, with LOST stages shown as LOST and one question per stage for
   someone who was there.
5. **A process plan for the new brand** and a distance check against the reference.

## Workflow

```bash
S=marketing/brand-reverse/skills/brand-reverse/scripts
python3 $S/palette_logic_analyzer.py --input case.json
python3 $S/evidence_ledger.py        --input case.json     # fix until not exit 4
python3 $S/process_reconstructor.py  --input case.json
python3 $S/process_reconstructor.py  --input case.json --plan
python3 $S/method_transfer_guard.py  --case case.json --new brief.json
# add --sample to any script to see it on the fictional Cafe Maru case
```

Uses the `cs-brand-reverse-analyst` agent and the `brand-reverse` skill.
