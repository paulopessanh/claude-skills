# Colour systems, type, and how a vote becomes a decision

Confidence key: 🟢 published primary source · 🟡 tool heuristic or secondary · 🔴 folklore.

## A colour system

- A family is a ramp of steps around a base. In `color_system_builder.py` step 50 is the base itself; lighter steps raise OKLab
  lightness toward 0.97 with chroma eased down, darker steps move toward 0.18, hue held constant. Chroma is pulled back until
  the colour fits the sRGB gamut, so no step is silently clipped.
- Name colours in two parts: the colour word and a name from the brand's world ("Azul Cume"). Token: `{SIGLA}_{Name}_{step}`.
- Contrast is computed, not judged. Body text needs 4.5:1 and large text or interface parts 3:1 (WCAG). The script reports which
  step first carries white text.
- 🟡 CMYK from the script is a naive conversion and is labelled approximate. Print values come from a colour-managed workflow
  with an ICC profile and a printed proof.
- Gradients: from the main colour to one other family, at one defined angle. Proportion of use is stated for light and dark backgrounds.

## Type

Principal, support, mono. Test with the client's own words, not lorem ipsum. Record licence, fallback and who will edit later.
A static font with one weight renders every weight as that one; prefer a variable font or the weight you use most.

## From votes to a verdict

A shapes dynamic produces opinions; `vote_tally.py` keeps them from being over-read.

- Collect votes independently before discussion, so the loudest voice does not set the others. 🟢 Noise research recommends independent judgments first.
- One favorite per voter. A scale of no (−1), maybe (0), yes (+1), favorite (+3). 🟡 The weights are tool defaults; change with `--scale` in code if your process differs.
- Count twice by two independent routes (voter by voter, item by item); a mismatch blocks.
- No quorum, no verdict: if fewer than the required decisors cast votes on 80% of items, nothing is declared.
- Plurality is not agreement. Different counting rules can crown different winners from the same ballots. Report the split between decisors (yes against no) instead of hiding it.
- A market reference that wins is a signal about language, not a proposal. Translate it.

## Sources

1. 🟢 W3C, *Web Content Accessibility Guidelines (WCAG) 2.1*, SC 1.4.3 Contrast (Minimum) and SC 1.4.11 Non-text Contrast.
2. 🟢 Björn Ottosson, OKLab, 2020 (matrices, lightness model).
3. 🟢 ICC, *Specification ICC.1:2010*; ISO 12647 series (process control for print production). Why print colour needs a profile.
4. 🟢 Robert Bringhurst, *The Elements of Typographic Style*, 4th ed., Hartley and Marks, 2012; Ellen Lupton, *Thinking with Type*, 2nd ed., 2010.
5. 🟢 Daniel Kahneman, Olivier Sibony and Cass Sunstein, *Noise*, 2021. Independent assessments, then aggregation.
6. 🟢 Donald Saari, "Chaotic Elections! A Mathematician Looks at Voting", American Mathematical Society, 2001; Kenneth Arrow, *Social Choice and Individual Values*, 1951. No counting rule is neutral in every case.
7. 🟢 Norman Dalkey and Olaf Helmer, "An Experimental Application of the Delphi Method to the Use of Experts", *Management Science* 9(3), 1963. Structured, anonymous rounds.

## Claims to hold loosely

- 🔴 "The client voted, so the client decided." A vote informs. The decision is a verdict with its reasons and a named owner.
- 🟡 Fixed lightness anchors (0.97 and 0.18) are choices that suit most brands; a very pale or very dark base may need hand tuning.
