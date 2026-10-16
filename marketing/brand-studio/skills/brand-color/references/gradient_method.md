# Gradient method: Light Source, Hold, Falloff, Anchor

Source: a design tutorial by the channel aevyvideoschool, shown to the team as screenshots. The numbers below are
the example in that tutorial, kept as a worked example. They are not rules for every brand.

## The four stops

| Stop | Position | Job |
|---|---|---|
| Light Source | 0% | Where the light hits. The lightest and least dense stop. |
| Hold | 40 to 45% | Holds the brand colour. The gradient rests here before it falls. |
| Falloff | 60 to 65% | Where the colour starts to lose light. |
| Anchor | 100% | The deepest stop. Grounds the shape. |

Worked example, hue 235 held, in HSL (hue, saturation, lightness):

| Stop | S | L |
|---|---|---|
| Light Source | 90 | 80 |
| Hold | 80 | 70 |
| Falloff | 70 | 60 |
| Anchor | 60 | 50 |

Hue stays fixed. Saturation and lightness step by 10. That is the whole recipe, and it is why the middle does not go grey.

## Grey limbo

The tutorial shows a lighter stop, a darker stop and the band between them as a flat, greyish zone. That band is
grey limbo. It appears when two saturated colours are mixed straight in RGB: the channels average toward a middle
grey, and chroma collapses in the centre.

Measured here, with the builder, as the lowest chroma of 33 samples divided by the chroma of the weaker end:

| Pair | Straight RGB mix | brand-color (OKLCH) |
|---|---|---|
| Blue #2B3A67 to teal #2F7F86 | 0.86 | 1.00 |
| Blue #1F4FD8 to orange #F28C28 | 0.26 | 1.00 |
| Blue #2B3A67 to yellow #E8C547 | 0.06 | 1.00 |

Below 0.60 the builder reports GREY_LIMBO and blocks.

## Why OKLCH and not HSL

HSL is easy to hand-edit and is what the tutorial uses, so the builder prints HSL for every stop and a designer can
reproduce the ramp in any tool. HSL lightness is not perceptual: 50% lightness in yellow is far brighter than in
blue. OKLCH lightness is perceptual, so the steps look even across hues. The engine computes in OKLCH and shows HSL.

## Light and dark backgrounds

Check the gradient on each background separately. WCAG 2.2 non-text contrast asks 3:1 for shapes and edges. Text on
a stop asks 4.5:1 (normal) or 3:1 (large). The builder reports the minimum and maximum ratio of the 33 samples and
the worst APCA Lc against each background it receives.

## Reproducing the gradient in other tools

- Browsers: `modern_oklch`.
- Figma, Illustrator, Keynote, email: `universal_srgb`. It carries sampled stops from the clean OKLCH path.
- Print: CMYK is approximate. Ask the printer for a proof, and for a spot-colour fallback in the Hold.
