---
name: brand-color
description: Use when a brand needs its complete colour system, from the main palette to gradients and prohibitions. Triggers include "sistema de cores", "paleta da marca", "tints tones shades", "paletas complementares", "paleta neutra", "paleta restrita", "dashboard positivo negativo alerta", "gradiente", "degradê", "grey limbo", "light mode dark mode", "paleta de proibições", "CMYK RGB HEX PMS", "brand colour system", "gradient without muddy middle". Builds gradients in the Light Source, Hold, Falloff, Anchor method and measures them for grey limbo, with HEX, RGB, HSL, OKLCH and approximate CMYK for every stop.
license: MIT
metadata:
  version: 0.3.0
  author: Alireza Rezvani
  category: marketing
  updated: 2026-10-16
---

# Brand Color: one system, every use named

A colour list is not a system. A system says which colour does which job, on which background, in which medium,
and what is never allowed. All eight palettes below are in this package. One command builds them from the colour
candidates and the chosen path; each step also runs alone. Reply in the user's language.

**Two limits to say aloud.** CMYK is computed, so it is approximate: print needs an ICC profile and a proof. PMS
(Pantone) is never computed: it needs the licensed library and a printed match, so every colour carries
`pms.status = pending_match`.

## The eight deliverables (target scope)

| # | Palette | Job | Status |
|---|---|---|---|
| 1 | Principal | The colours of the brand, ranked by share of use, picked from briefing, kick-off, research and references | **Phase 2, this package** |
| 2 | Secundárias | Tints, tones and shades of the principal, each with a stated use | **Phase 2, this package** |
| 3 | Complementares | Title, tagline, subtitle, icons, hairlines, button, key number, link, highlight and sheen, digital and print | **Phase 2, this package** |
| 4 | Suplementares | Tinted neutral scale, and physical spaces (store, showroom, office) | **Phase 3, this package** |
| 5 | Restritas | Positive, negative, warning, info for dashboards and reports, never used as brand colour | **Phase 3, this package** |
| 6 | **Gradientes** | Clean gradients for light and dark backgrounds | **Phase 1, this package** |
| 7 | Regras de uso | Light mode and dark mode behaviour, and what the logo does when the brand colour becomes the background | **Phase 3, this package** |
| 8 | Proibições | What is outside the brand, with examples | **Phase 3, this package** |

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

## Workflow, palettes 4 to 8

**4. Supplementary palettes: the brand's own neutrals, and physical spaces.**

```bash
python3 scripts/neutral_scale.py --primary "#2B3A67" --sigla SFI --light-hex "#EDF0F2" --dark-hex "#12161C" --out neutral.json
python3 scripts/physical_spaces.py --scales scales.json --neutral neutral.json --primary Cume --secondary Vale --accent Brasa --out spaces.json
```

Eleven neutrals carry a trace of the primary hue, so no grey is a stranger. The tool assigns page, surface, sunken,
border, muted, body and strong text for light and dark. Spaces (store, showroom, office) get a surface plan with
share, finish, estimated LRV, lighting and checks: floor against wall by at least 30 LRV points, ceiling at 80 or
more, brand colour inside its limit (store 35%, showroom 20%, office 25%), and a warning for a very dark brand
wall. LRV from a hex is a planning figure: every surface stays `pending_match` until a physical sample is approved on site.

**5. Restricted palettes: status for dashboards and reports.**

```bash
python3 scripts/restricted_palette.py --primary "#2B3A67" --sigla SFI --bg-light "#EDF0F2" --bg-dark "#12161C" \
  --extra-brand "#2F7F86" "#C8452D" --out status.json
```

Positive, negative, warning, info and no-change, each with a strong colour, text for light and dark, surface and
border. They are fenced: never brand colour, never alone (icon and word always), and checked for colour-blind
readers and for grayscale print. It warns when a bright brand colour sits near a status hue: an accent in
red-orange can be read as an error.

**6. Gradients** come with a light and a dark variant for each family. For the Hold, the tool picks the step closest
to the brand colour that keeps every stop above 3:1 on that background. The pair runs from the Light Source of the first
family to the Anchor of the second, so the light changes as well as the hue.

**7. Rules of use.**

```bash
python3 scripts/usage_rules.py --scales scales.json --neutral neutral.json --primary Cume --secondary Vale \
  --accent Brasa --roles roles.json --out usage.json
```

For nine backgrounds (light page, card, soft highlight; dark page, surface, brand deep; each family as a full
background) it settles the mark, brand-coloured title, strong, body and muted text, link, accent and what to avoid,
with ratios. When a brand colour becomes the background the mark turns white or the lightest tint. A background that
cannot carry body text says so: it takes a large title and a short label only. It also writes the approved fg and bg
pairs in the shape of brand-source.v2.

**8. The prohibition palette.**

```bash
python3 scripts/prohibitions.py --scales scales.json --neutral neutral.json --status status.json \
  --vetoed "#C9A227" "#5A3A22" --out prohibitions.json
```

Thirteen cards, each with the rule, the reason and real examples made from the palette: near-miss colours, client
vetoes, pairs under 3:1 that look fine, vibrating pairs, muddy gradients, pure black and white, grey without a hue,
status as brand, colour alone, too many colours, a recoloured mark, rainbow gradients and black shadows. Severity is
BLOCK, ALERT or GUIDE.

## One command

```bash
python3 scripts/color_system.py --candidates candidates.json --path A --out ./cor \
  --light-hex "#EDF0F2" --dark-hex "#12161C"
```

`--path` is required: a person or the client votes, and the tool never does. It writes `system.json` (the source for
the manual), one file per palette in `json/`, and `sistema-de-cores.html`, a sheet that follows light and dark and
shows every token with HEX, RGB, approximate CMYK and PMS status. **Do not edit the sheet.** Change the candidates or
the path and generate again.

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
