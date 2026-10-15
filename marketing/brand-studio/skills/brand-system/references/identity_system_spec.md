# The identity system spec: what it holds and how its numbers stay honest

Confidence key: 🟢 published primary source · 🟡 secondary, draft standard, or judgment · 🔴 folklore.

## What a spec holds

A spec is the structured form of the guidelines, so a script can check it and a team can build from it.

1. **Concept** in a paragraph and in a sentence.
2. **Anatomy**: type, structure, descriptor, tagline, name origin, registry status.
3. **Construction**: grid, proportions, angles, and the reason for each detail, so a redraw does not drift.
4. **Versions**: horizontal, vertical, symbol, wordmark, signatures with descriptor and with tagline.
5. **Use**: protection area defined against a part of the mark (not loose millimetres), minimum size in print units and screen
   units, positive, negative, mono, backgrounds including photography, and at least six misuse cases.
6. **Colour**: tokens with HEX, RGB, CMYK, proportion on light and dark, declared contrast pairs.
7. **Type**: hierarchy, sizes, line height, licence, fallback.
8. **Graphic elements**: each derived from the mark's geometry (angle, direction, weight), with right and wrong examples.
9. **Photography, motion, voice** (traits with is and is-not), **applications**, **before and after**.

## Why internal consistency matters more than length

A manual that looks complete but contradicts itself (a colour whose RGB is not its HEX, a pair declared accessible that is not)
sends different teams to different results while everyone believes they follow the same document. `guidelines_completeness.py`
therefore treats a conflict as a block and a gap as a score.

## Tokens

Name colours and sizes as tokens, and let the document, the website and the files all reference the tokens. Declare the
semantic role of a token (text, background, accent), not only its value.

## Sources

1. 🟢 Alina Wheeler, *Designing Brand Identity*, 5th ed., Wiley, 2017. The identity standards and the guidelines that carry them.
2. 🟢 Richard Danne and Bruce Blackburn, *NASA Graphics Standards Manual*, 1975. A standards manual as a system with reasons and rules.
3. 🟢 Brad Frost, *Atomic Design*, 2016. Systems built from small, reusable parts.
4. 🟡 W3C Design Tokens Community Group, *Design Tokens Format Module* (draft). A shared format for tokens; still evolving, check the current draft.
5. 🟢 W3C, WCAG 2.1, SC 1.4.3 and SC 1.4.11. Contrast minimums for text and non-text parts.
6. 🟢 ICC, *Specification ICC.1:2010*, and the ISO 12647 series. Print colour needs a profile and a proof.

## Claims to hold loosely

- 🔴 "More pages make a better manual." Rules a team can find and apply beat pages nobody reads.
- 🟡 The six-misuse minimum and the completeness weights are this skill's working defaults. Raise them for complex marks.
- 🟡 Protection area "relative to a part of the mark" is a convention that survives scaling; absolute millimetres do not.
