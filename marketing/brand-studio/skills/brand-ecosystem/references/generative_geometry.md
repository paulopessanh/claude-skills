# Generative geometry and honest limits

How the symbol, patterns and pictograms come from parameters, and what that does and does not give you. Confidence: 🟢 established, 🟡 reasonable, 🔴 folklore.

## Construction from parameters

The ridge symbol is a polyline. Vertices are fractions of the tallest peak. Horizontal position follows from one constant
slope angle, so every flank shares an angle and the form reads as one gesture. 🟢 Constrained geometry is a standard
identity method (Wheeler, Müller-Brockmann grids). Because it is computed, the manual can print the construction exactly and
every derived element (pattern, divider, seal arc) reuses the same angle. 🟡

## What the generator cannot do

- It cannot judge distinctiveness. A computed mountain can still look like any mountain. The lockups add a continuing
  horizon rule to help, and a person must decide if it is enough. 🟡
- It cannot do optical correction. Designers adjust curves and joins by eye. The package labels the symbol a geometric study. 🟢
- It uses live fonts in logo text. Outlining needs a font file, and shipping one carries a licence question. 🟢

## Accessibility of generated files

SVG text carries `data-bg` and `data-size` attributes so the auditor can recompute contrast. Logotypes are exempt from WCAG
1.4.3, but the package still reports them. The animated symbol draws with stroke-dashoffset and stops under
prefers-reduced-motion. 🟢 WCAG 2.3.3.

## CMYK

The conversion is the naive formula. It ignores the black generation and ink limits of any real press. Use it as a hint
only. 🟢

## Sources

- Wheeler, Designing Brand Identity.
- Müller-Brockmann, Grid Systems in Graphic Design.
- W3C, WCAG 2.1 (1.4.3, 1.4.11, 2.3.3).
- MDN, SVG stroke-dasharray and stroke-dashoffset.
- Ottosson (2020), OKLab.
