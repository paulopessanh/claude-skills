# The category and its colour: read before you draw

Confidence key: 🟢 published primary source · 🟡 tool heuristic or secondary · 🔴 folklore.

## Why read the category first

If most competitors in a sector share a palette family, a symbol type or a tone, a new brand that does the same is
not wrong, it is invisible. If none does, the empty space may be an opportunity or a place the category rejects. The
matrix measures; a person decides which.

## What `competitor_matrix.py` measures

- **Hue map.** Competitors' colours in OKLCH, 12 bins of 30 degrees, share of competitors per bin. Chromatic colours only
  (OKLab chroma 0.04 or more), because a grey has no hue to compare.
- **Clichés.** Anything 40% or more of competitors use: a hue bin, a symbol type, an anatomy type, a tone word. 🟡 The 40% line is a working threshold, not a law.
- **White space.** Hue bins nobody uses and the client did not veto, ranked by the gap to the nearest used bin. Always paired with the caveat that empty can mean rejected.
- **Candidate check.** Your palette against each competitor's, with distance in OKLab. 🟡 Roughly 0.02 is commonly treated as a just-noticeable difference; the script warns below 0.06 and blocks a palette that is within 0.04 on two colours of one competitor.

## Why OKLCH and not hex or HSL

Hex cannot tell you whether two blues look alike; HSL hue and lightness do not match perception (a yellow and a blue of equal
HSL lightness differ strongly in brightness). OKLab was designed so that distance and lightness track what the eye sees.

## Doing the research honestly

- Every competitor has a source and a date; otherwise it is a rumour (the script blocks it).
- 5 to 12 competitors. Under 5 is not a category; over 12 dilutes the reading.
- Look beyond the sector too: out-of-category references and artistic lineage feed the direction step.
- Registries (trademark, domains, handles) are recorded with the date of the consultation. They age.

## Sources

1. 🟢 Björn Ottosson, "A perceptual color space for image processing" (OKLab), 2020, bottosson.github.io/posts/oklab. Matrices and rationale.
2. 🟢 CIE 15:2004, *Colorimetry*. The reference for CIE Lab and colour difference concepts.
3. 🟢 W. Chan Kim and Renée Mauborgne, *Blue Ocean Strategy*, Harvard Business School Press, 2005. The strategy canvas: plot competitors on shared factors to find uncontested space.
4. 🟢 Al Ries and Jack Trout, *Positioning: The Battle for Your Mind*, 1981. Positioning is relative to competitors.
5. 🟢 Byron Sharp, *How Brands Grow*, Oxford University Press, 2010, and Jenni Romaniuk, *Building Distinctive Brand Assets*, Oxford University Press, 2018. Distinctiveness as recognition without the name.
6. 🟢 Andrew Elliot and Markus Maier, "Color psychology: Effects of perceiving color on psychological functioning in humans", *Annual Review of Psychology* 65, 2014. Colour effects are context dependent and less settled than popular claims.
7. 🟢 Josef Albers, *Interaction of Color*, Yale University Press, 1963. A colour is read against its neighbours.

## Claims to hold loosely

- 🔴 "Blue means trust, red means urgency." Meaning comes from context and category.
- 🔴 "An empty hue is an opportunity." It is a question. Link it to a client attribute or drop it.
- 🟡 Category conventions can be a safe signal (a buyer recognises "chocolate" by brown). Break a convention on purpose and for a reason, not by accident.
