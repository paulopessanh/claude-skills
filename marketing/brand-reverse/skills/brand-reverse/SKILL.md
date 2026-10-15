---
name: brand-reverse
description: Use when someone wants to reverse engineer how a brand and its visual identity were made, rebuild the creative process behind a logo, palette, packaging or guidelines, or turn reference brands into a repeatable branding process for a new client. Triggers include "engenharia reversa de marca", "como essa identidade visual foi criada", "reconstruir o processo criativo", "brand teardown", "reverse engineer this brand identity", "what brief produced this". Separates observed, inferred and guessed claims, reads colour and type logic, rebuilds the eight-stage process from briefing to guidelines, and plans a new brand's process without copying marks. Not for naming from scratch, generating logos, or trademark clearance.
license: MIT
metadata:
  version: 1.0.0
  author: Alireza Rezvani
  category: marketing
  updated: 2026-10-15
---

# Brand Reverse: from the finished identity back to the process

You see a brand's outputs. You never see its inputs: the brief, the budget, the routes that
lost, the client's veto. Reverse engineering is inference, so the skill's job is to keep
inference honest, then turn what survives into a process you can run for a new brand.
Reply in the user's language.

## Workflow

**1. Frame.** Ask at most four questions: which reference brand(s), what the result is for
(learn, brief a client, audit your own past work), which artifacts you can actually look at,
and the sector of the new brand. Stop asking once you can start.

**2. Inventory artifacts.** Fill [`assets/reverse_worksheet.md`](assets/reverse_worksheet.md)
into a case file shaped like [`assets/example_reference.json`](assets/example_reference.json).
Only what the user shows you or is public. Mark each artifact `primary`, `secondary` or
`self_report` (a studio's case study is a self-report).

**3. Read the visual logic.**

```bash
python3 scripts/palette_logic_analyzer.py --input case.json --output human
```

Hue relation, roles, temperature, WCAG contrast, proportion pattern, type pairing. Every
design-intent reading comes back as an inference with its rival attached.

**4. Write claims, then gate them.** Each claim is `observed`, `inferred` or `hypothesis`.

```bash
python3 scripts/evidence_ledger.py --input case.json
```

Exit 0 SOUND, 2 CAUTION, 4 UNSOUND. Do not move on at 4. It blocks intent written as fact,
inference with no rival, and citations that do not exist.

**5. Rebuild the chain.**

```bash
python3 scripts/process_reconstructor.py --input case.json
```

Eight stages, each LOST, HYPOTHESIS_ONLY, INFERRED or RECOVERED, with the requirements the
outputs force upstream and one question per stage for someone who was in the room. Exit 3
means too little evidence to call it a process.

**6. Transfer the method.**

```bash
python3 scripts/process_reconstructor.py --input case.json --plan
python3 scripts/method_transfer_guard.py --case case.json --new brief.json
```

The plan lists each stage's decisions, a gate question, and value-free patterns. The guard
blocks hex codes, names and assets leaking into patterns, and a new brand sitting too close.

**7. Deliver two documents:** the reconstruction (stage table, claims by class, open questions)
and the process plan for the new brand. Say which stages are guesses.

## Rules

- **Intent is never fact.** Briefing, research and strategy are not visible in a logo.
- **Every inference names a rival.** Start with sector convention and template defaults.
- **A maker's story is a story.** Case studies and interviews are `self_report`.
- **Transfer method, never marks.** Patterns carry no hex, name, typeface or asset.
- **Not legal advice.** A DISTANT verdict is not trademark clearance.

## Example

`python3 scripts/process_reconstructor.py --sample` on the fictional Cafe Maru prints
`visual_direction RECOVERED`, `applications LOST`, and the line "implied upstream (C2,
hypothesis): Recognition from distance on a shelf mattered more than range of colour."
That sentence is the product: a testable guess about the brief, derived from a visible choice.

## Scripts and references

| File | Role |
|---|---|
| `scripts/evidence_ledger.py` | Claim gate: observed / inferred / hypothesis |
| `scripts/palette_logic_analyzer.py` | Colour and type logic with rivals |
| `scripts/process_reconstructor.py` | Eight-stage rebuild, back-propagation, `--plan` |
| `scripts/method_transfer_guard.py` | Value-leak and distance check |

- [`references/brand_process_canon.md`](references/brand_process_canon.md): the stage model and its sources
- [`references/inference_discipline.md`](references/inference_discipline.md): abduction, rivals, self-report bias
- [`references/distinctive_assets_and_law.md`](references/distinctive_assets_and_law.md): what may transfer

Distinct from `marketing-skill/brand-guidelines`, which documents a brand you already own.
