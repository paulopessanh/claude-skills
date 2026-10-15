---
name: brand-direction
description: Use when a branding project must turn research into creative rules and a convergence, steps 4 and 5. Triggers include "direção criativa", "pétreos e vetados", "naming", "avaliar nomes", "anatomia da marca", "descriptor e tagline", "caminhos de símbolo", "sistema de cores", "paleta com contraste", "dinâmica das formas", "votação do cliente", "briefing de finalização", "brand direction", "name screening", "colour system". Builds pétreos and vetados with origin, screens names, validates anatomy, generates accessible colour families, and tallies the client's vote into a verdict that refuses to over-read noise.
license: MIT
metadata:
  version: 1.0.0
  author: Alireza Rezvani
  category: marketing
  updated: 2026-10-15
---

# Brand Direction: rules before forms

After this step any designer knows what to draw and what not to draw, and the client knows why. Every choice
traces to a pétreo (a truth that cannot move) or it is taste, and taste is not a reason. Reply in the user's language.

## Workflow

1. **Pétreos (3) and vetados (3).** Each is a sentence, a traceable origin and a visual translation. Lock them with
   `brand_state.py lock`. A vetado is a tempting path you will not take, with the reason.
2. **Semantic formula.** Decide which parts of the mark are icon (resembles), index (points to) and symbol (convention).
3. **Naming read.** Names usually arrive closed. Screen the candidates, then add the checks only a person can do:

   ```bash
   python3 scripts/naming_screener.py --input naming.json     # exit 0 clear, 2 caution, 4 all blocked
   ```

4. **Anatomy.** `anatomy_validator.py --stage candidates` for 3 to 5 descriptors and taglines, then `--stage final`.
   A descriptor and a tagline are required; slogan and hookline need an explicit include or exclude with a reason.
5. **Symbol paths (4 or 5).** For each: logic, references, risks. The client's stated taste becomes one path, not the answer.
6. **Colour.** Base colours in, families out, with the vetoed hues from discovery:

   ```bash
   python3 scripts/color_system_builder.py --input colours.json
   ```

   Step 50 is the base. Tokens, HEX, RGB, approximate CMYK, contrast against white and near-black. Exit 4 on a vetoed hue.
7. **Type, graphic elements, lineage, mood.** Test type with the client's own words. Check licence and fallback.
8. **Shapes dynamic (step 5).** Give each item a visible type (rough, draft, market reference, inspiration). Collect votes
   independently before any discussion, so one voice does not set the others. Then:

   ```bash
   python3 scripts/vote_tally.py --input votes.json    # exit 3 no quorum, 4 blocked
   ```

   Output: a verdict (green light, adjust, new direction) and the finalisation brief: keep, add, eliminate, must convey.

## Rules

- **A market reference is never a proposal.** If one wins the vote, translate what the client liked in it; do not copy it.
- **No quorum, no verdict.** Do not read a vote that too few decisors cast.
- **No colour, shape or word that the client vetoed.** The scripts block it; do not argue around the block.
- **Mark every inference as an inference.** A pétreo with no origin is a preference.
- **Names are screened, not cleared.** The trademark office and the language checks stay with a person.

## Use a reference brand

To borrow method from a brand you admire, run `brand-reverse` first, take only its `pattern` lines (they hold no
values), and pass the new brief through its `method_transfer_guard.py` before presenting.

## Example

`python3 scripts/vote_tally.py --sample` prints GREEN_LIGHT for item F02, flags F04 as CONTESTED by one decisor, and
lists the words the client used for the winning shapes.

## References

- [`references/naming_anatomy_and_signs.md`](references/naming_anatomy_and_signs.md): naming tests, anatomy, icon, index, symbol
- [`references/colour_type_and_convergence.md`](references/colour_type_and_convergence.md): OKLCH ramps, WCAG, CMYK limits, voting and noise
