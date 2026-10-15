---
name: brand-system
description: Use when an approved brand must become a complete identity system and a living manual, steps 6 to 8. Triggers include "apresentação da marca", "sistema de identidade visual", "guidelines para o time", "área de proteção e redução mínima", "tokens de cor", "usos proibidos", "peças gráficas", "manual da marca", "brandbook", "nomenclatura de arquivos", "brand guidelines spec", "brand manual". Builds the identity spec, checks guidelines for missing sections and for numbers that contradict each other, keeps the manual and the team guidelines on one source, and checks file names and what may be delivered.
license: MIT
metadata:
  version: 1.0.0
  author: Alireza Rezvani
  category: marketing
  updated: 2026-10-15
---

# Brand System: one source of numbers

Guidelines that look finished but contradict themselves are worse than visibly incomplete ones, because people trust
them. This skill makes the identity complete, makes the numbers agree, and keeps three documents from drifting apart:
the reveal, the team guidelines and the manual. Reply in the user's language.

## Workflow

**Step 6, brand and identity.** Write the spec as one structured file ([`assets/example_guidelines.json`](assets/example_guidelines.json)):
concept in a paragraph and in a sentence · anatomy (type, structure, descriptor, tagline, name origin, registry status) ·
construction (grid, proportions, angles, the reason for each detail) · versions · use (protection area tied to a part of
the mark, minimum size in print and screen units, positive, negative, mono, backgrounds, misuse) · colour tokens and
pairs · type hierarchy with fallback and licence · graphic elements derived from the mark's geometry · photography ·
motion · voice (traits with is and is-not) · real applications · before and after.

```bash
python3 scripts/guidelines_completeness.py --input spec.json     # exit 0 complete, 2 gaps, 4 inconsistent
```

It checks that every token's RGB equals its HEX, that each contrast pair declared AA passes when recomputed, that no
token name or colour is duplicated, and that nothing a team needs is missing. Fix conflicts before gaps.

To see what a complete manual still asks of the source, run the coverage check. It compares the source with 34 needs
reverse engineered from a real corporate manual and names the field to add for each gap (exit 2 on an essential gap):

```bash
python3 scripts/manual_coverage_check.py --source brand-source.json

For the strategic half (platform, personas, archetype, voice), add `--blueprint assets/strategic_blueprint.v1.json`. It lists 16 needs in layer S and never changes the visual essentials.
```

**Step 6.5, team guidelines.** Technical rules only: signatures, colour, grid, type, elements, pictograms, components,
pieces. No story, no concept. Publish by version for the lead's review with a visible status, then a final version
with no status, always at the same address. A change to colour, type, element or mark changes this document first.

**Step 7, pieces.** Direct the team on real uses (card, letterhead, signature, deck, social, uniform, sign). Each piece
gets a technical sheet: size, bleed, safe area, colour mode, resolution.

**Step 8, manual.** Born in step 1 and grown at every approval, so nothing is rebuilt from memory. Two versions, one source:
an internal one (decisions with date and author, client changes with the opinion, discarded alternatives, registries,
links) and the client one (published, searchable, copyable colour codes, downloads). The team guidelines are the technical
base of the manual with the same numbers and names; if they diverge, the latest approved wins and the other is corrected.

```bash
python3 scripts/asset_name_checker.py --input manifest.json --sigla SFI
```

Default name `{SIGLA}_{Name}_V{NN}_{DDMMAA}`; final `{SIGLA}_{Name}_Final_{DDMMAA}`. Exit 4 if a file in an `Exportados`
folder is not approved. Warns on bad names, bad dates, duplicate versions, gaps and temporary-looking files.

## Rules

- **Print values come from a profile and a proof.** The script's CMYK is approximate and says so.
- **Only approved work goes to the delivery folder.** A superseded final moves to `Old`.
- **A change to the mark means checking every element derived from it.**
- **State the reason of each rule.** A rule with no reason is ignored or argued.
- **Never invent a number to fill a gap.** Leave the gap visible and ask.

## Example

`python3 scripts/guidelines_completeness.py --sample` returns INCONSISTENT: one token's RGB is `[178, 74, 40]` while its HEX
`#B24A2F` is `(178, 74, 47)`, and a pair declared AA scores 2.06:1. It also lists eight gaps.

## References

- [`references/identity_system_spec.md`](references/identity_system_spec.md): what a spec holds, standards manuals, tokens
- [`references/manual_as_living_document.md`](references/manual_as_living_document.md): versions, one source, drift
- [`references/manual_anatomy_reference.md`](references/manual_anatomy_reference.md): the reverse engineered manual structure, 7 layers, 34 needs
- [`references/strategic_manual_reference.md`](references/strategic_manual_reference.md): the strategic platform half (16 needs, layer S), the page grammar and how a reel presents it
