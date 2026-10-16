# Inference discipline: how to guess without fooling yourself

Confidence key: 🟢 published primary source · 🟡 secondary or applied here by analogy · 🔴 folklore.

## The three classes

| Class | Test | Example |
|---|---|---|
| observed | You can point at an artifact that shows it | "A terracotta field covers about half the front." |
| inferred | Best explanation of artifacts, with a rival on record | "Origin is the promise." Rival: generic nature cue |
| hypothesis | About something unobservable | "The budget allowed one print run." |

A hypothesis can be useful. It is never promoted to a fact by repetition.

## Why the rules exist

1. 🟢 Charles S. Peirce, lectures on pragmatism (1903), *Collected Papers* vol. 5. Abduction is
   reasoning from a surprising observation to a hypothesis that would explain it. It produces
   candidates, not conclusions. Back-propagation in the reconstructor is abduction.
2. 🟢 Peter Lipton, *Inference to the Best Explanation*, 2nd ed., Routledge, 2004. An
   explanation is only "best" against named rivals. That is why `evidence_ledger.py` blocks an
   inferred claim with no alternative (NO_RIVAL).
3. 🟢 Kees Dorst, *Frame Innovation*, MIT Press, 2015. Design reasoning runs from a desired
   outcome and a guessed frame to a "how". Reversing it means guessing the frame, so the
   guess must be marked.
4. 🟢 Nigel Cross, *Designerly Ways of Knowing*, Birkhauser, 2006, and 🟢 Donald Schon, *The
   Reflective Practitioner*, Basic Books, 1983. Designers often cannot state their reasons
   in advance; rationale is reconstructed after the work. Treat any rationale as a reconstruction.
5. 🟢 Richard Nisbett and Timothy Wilson, "Telling more than we can know", *Psychological
   Review* 84(3), 1977. People report plausible causes for their behaviour that do not match
   the real ones. This is the basis for SELF_REPORT_ONLY: a studio's case study is a
   plausible story from the people with the most reason to tell it well.
6. 🟢 Marc Mangel and Francisco Samaniego, "Abraham Wald's work on aircraft survivability",
   *Journal of the American Statistical Association* 79(386), 1984. You see the survivors.
   Famous identities are survivors; the routes that failed, and the identities that followed
   the same method and failed, are invisible.
7. 🟢 Andrew Elliot and Markus Maier, "Color psychology", *Annual Review of Psychology* 65,
   2014. Effects of colour on behaviour are context dependent and less settled than popular
   claims. Do not credit a palette with a universal emotional meaning.

## Habits that follow

- 🟡 Always check sector convention first. If three competitors share the palette family, the
  colour is category, not insight.
- 🟡 Check tool and template defaults before crediting a typographic choice to strategy.
- 🟡 Give a high-observability stage (visual_direction) high confidence only when two or more
  artifacts agree. Give intent stages low confidence whatever the evidence.
- 🟡 Convert every claim you cannot defend into a question for someone who was there. The
  reconstructor prints one per stage.

## Folklore to refuse

- 🔴 "The geometry proves the designer used the golden ratio." Overlays fit almost anything.
- 🔴 "Red means urgency, blue means trust." Context and category decide.
