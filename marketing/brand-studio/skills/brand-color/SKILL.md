---
name: brand-color
description: Use when a brand needs its complete colour system, from the main palette to gradients and prohibitions. Triggers include "sistema de cores", "paleta da marca", "tints tones shades", "paletas complementares", "paleta neutra", "paleta restrita", "dashboard positivo negativo alerta", "gradiente", "degradê", "grey limbo", "light mode dark mode", "paleta de proibições", "CMYK RGB HEX PMS", "brand colour system", "gradient without muddy middle". Builds gradients in the Light Source, Hold, Falloff, Anchor method and measures them for grey limbo, with HEX, RGB, HSL, OKLCH and approximate CMYK for every stop.
license: MIT
metadata:
  version: 0.2.0
  author: Alireza Rezvani
  category: marketing
  updated: 2026-10-16
---

# Brand Color: one system, every use named

A colour list is not a system. A system says which colour does which job, on which background, in which medium,
and what is never allowed. This skill is built in phases. **Phase 1 shipped the colour engine and the gradient
builder. Phase 2 adds the principal, secondary and complementary palettes.** The phases marked Phase 3 below are
planned and not yet in this package; do not claim them as done. Reply in the user's language.

## The eight deliverables (target scope)

| # | Palette | Job | Status |
|---|---|---|---|
| 1 | Principal | The colours of the brand, ranked by share of use, picked from briefing, kick-off, research and references | **Phase 2, this package** |
| 2 | Secundárias | Tints, tones and shades of the principal, each with a stated use | **Phase 2, this package** |
| 3 | Complementares | Title, tagline, subtitle, icons, hairlines, button, key number, link, highlight and sheen, digital and print | **Phase 2, this package** |
| 4 | Suplementares | Tinted neutral scale, and physical spaces (store, showroom, office) | Phase 3 |
| 5 | Restritas | Positive, negative, warning, info for dashboards and reports, never used as brand colour | Phase 3 |
| 6 | **Gradientes** | Clean gradients for light and dark backgrounds | **Phase 1, this package** |
| 7 | Regras de uso | Light mode and dark mode behaviour, and what the logo does when the brand colour becomes the background | Phase 3 |
| 8 | Proibições | What is outside the brand, with examples | Phase 3 |

## Workflow, palettes 1 to 3

**1. Principal palette: three paths, then a vote.** Read the briefing, kick-off, meeting transcripts, market research and
references. For every colour they point to, write a candidate with its evidence quoted and a weight from 0 to 1
([`assets/example_candidates.json`](assets/example_candidates.json)). Add the competitor colours and the client's vetoes.

```bash
python3 scripts/palette_paths.py --input candidates.json --out paths.json
```

It drops a candidate that shares a hue with a veto and sits close to it. It returns three paths that differ on purpose:
faithful to the evidence, different from the market, and most functional (text reads on light and dark). Each path
has a stated reason and a majority use (neutral 60, primary 30, accent 10, a starting rule to confirm on the first
three applications). **A person or the client decides the vote.** The tool never votes. Exit 4 means fewer than 3
usable candidates: go back to research.

**2. Secondary palettes: tints, tones and shades.** Write the three chosen families and run:

```bash
python3 scripts/tonal_scales.py --input families.json --out scales.json
```

Each family gets 7 steps per scale, token `{SIGLA}_{Family}_{Tint|Tone|Shade}{1..7}`, with HEX, RGB, HSL, OKLCH, approximate CMYK,
contrast on white and ink, APCA, and what each scale is for. Use: **tints** for highlight backgrounds, cards and
states; **tones** to make the colour recede, for secondary interface, borders and atmosphere; **shades** for text,
dark backgrounds and pressed states. The deepest shade is a deep colour, never pure black.

**3. Complementary palette: one colour per job.**

```bash
python3 scripts/role_map.py --scales scales.json --primary Cume --secondary Vale --accent Brasa \
  --bg-light "#EDF0F2" --bg-dark "#12161C" --out roles.json
```

For brand mark, title, subtitle, tagline, icon, hairline, key number, link, button, highlight bar and sheen, in light and
dark mode, it picks the step closest to the brand colour that passes the contrast the role needs (4.5:1 for text
with a 5% margin, 3:1 for graphics and large type). Each row carries its rule, what never to do and a print note. It
also gives `mark_on_primary`, the colour of the mark when the primary becomes the background. In dark mode the
title is the lightest of the pair and in light mode the deepest. Exit 2 lists what had to fall back.

## Gradients without grey limbo

Grey limbo is the dull, dirty band that appears in the middle of a gradient. A straight RGB mix of two saturated
colours passes through a low-chroma middle. The method here removes it in three moves.

1. **Four named stops, one family.** Light Source 0%, Hold 42% (the brand colour itself), Falloff 62%, Anchor 100%.
   Hue and chroma are held. Only lightness steps down. The Hold stop makes the brand colour the anchor of the
   look, so the gradient never drifts away from it.
2. **Interpolate in OKLCH, not RGB.** Lightness and chroma stay perceptually even, so no step goes grey.
3. **Measure the real samples.** The tool samples 33 points, quantises them to hex and compares the chroma of the
   weakest sample with the weaker end. Under 60% is limbo and the tool blocks. It prints the same figure for a
   naive RGB mix so the difference is visible.

```bash
# One family, with the two background checks
python3 scripts/gradient_builder.py --mono "#2B3A67" --bg-light "#EDF0F2" --bg-dark "#12161C" \
  --name Cume --svg cume.svg --out cume.gradient.json

# Two families. A bridge stop is added when needed; BLOCKED when the gamut cannot carry it
python3 scripts/gradient_builder.py --duo "#2B3A67" "#2F7F86" --svg cume-vale.svg
```

Exit 0 clean, 2 caveats, 4 blocked, 1 input error.

Each stop is written with HEX, RGB, HSL, OKLCH and approximate CMYK. The output has two CSS strings:
`modern_oklch` for browsers and `universal_srgb` with sampled stops for Figma, Illustrator, Keynote and email.
A team that cannot use OKLCH copies `universal_srgb` and gets the same look.

## Rules

- **Never mix two families by a straight RGB blend.** Use the builder.
- **Never use pure black or pure white as a gradient end.** Use a tinted neutral of the family hue, or the Anchor.
- **A gradient goes from the main colour to one other family, in one angle.** More than a 90 degree hue arc reads as a rainbow.
- **One gradient lives on the background it was checked on.** Light and dark are checked separately. A stop under 3:1 against its
  background cannot carry an edge or a shape there.
- **CMYK is approximate.** Print needs an ICC profile and a proof.
- **PMS (Pantone) is never computed.** It needs the licensed library and a printed match. Carry it as `pending_match`.
- **A BLOCKED verdict stops delivery.** Add a third family between the two, or move the ends closer in hue.

## Forcing questions

1. Which colour is the Hold, and who approved it as the brand colour?
2. What sits on the gradient: text, logo or nothing? Text needs 4.5:1 on the stop it sits on.
3. Is the gradient for screen, print, or both? Print needs a spot-colour fallback.
4. Does the client's veto list include a hue the gradient passes through?

See [`references/gradient_method.md`](references/gradient_method.md).
