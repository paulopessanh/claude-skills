# Process architecture: the step graph, the gates, and change propagation

Confidence key: 🟢 published primary source · 🟡 secondary, or this suite's own synthesis · 🔴 folklore.

## The graph

`1 Briefing -> 2 Kick-off -> 3 Research -> 4 Direction -> 5 Shapes dynamic -> 6 Brand and identity -> 6.5 Team guidelines -> 7 Pieces -> 8 Manual -> 9 Ecosystem`

Not a list but a dependency graph: step 4 needs 1, 2 and 3; step 6 needs 4 and 5; step 8 needs everything. `brand_state.py`
encodes it, so "can we start this?" is computed, not remembered.

🟡 The ten steps are this suite's working model. They split the five practitioner phases in Wheeler (research, strategy,
identity design, touchpoints, asset management) so that each step has one set of decisions and one gate. Do not present
the count as a standard.

## Why gates

A gate is a checklist of things that, if wrong, every later step inherits. Each item asks for evidence you can point to.

| Step | The error a gate item prevents |
|---|---|
| 1 | a guess written as a fact; scope that drifts from the contract; years that do not add up |
| 3 | a competitor with no source; a colour map guessed by eye; registries without a date |
| 4 | a pétreo with no origin (a preference); a font with no licence; a palette that fails contrast |
| 5 | a vote read without quorum; a market reference mistaken for a proposal |
| 6 | guidelines that contradict themselves; an element not derived from the mark |
| 8 | a manual that disagrees with the team guidelines; two versions that drifted |

## Change propagation

Reopening step X marks every approved or in-flight downstream step stale, transitively. A stale step returns by rework or by
`revalidate` with a reason. This is the same idea as a build system rebuilding only what depends on a changed file.

## Narrative: the Sparkline

Every presentation alternates what is (today's reality, in the client's words) and what could be (the possible future), in
four acts: Diagnosis (the world as it is, closing on the question the brand answers), Revelation (the big idea, with one
moment people remember), Proof (resistance and evidence alternating, with the likely objections answered), Close (the new
world with the brand and a clear request for a decision). Build the map before any slide: slide, act, is or could be,
what the client should feel. Guidelines are not a presentation and do not use it.

## Sources

1. 🟢 Alina Wheeler, *Designing Brand Identity*, 5th ed., Wiley, 2017. Five phases of an identity process.
2. 🟢 Marty Neumeier, *The Brand Gap*, New Riders, 2003 (revised 2006). The gap between strategy and design is where identities fail.
3. 🟢 Robert G. Cooper, "Stage-Gate Systems: A New Tool for Managing New Products", *Business Horizons* 33(3), 1990. Gates as go/kill checkpoints with defined deliverables.
4. 🟢 Stuart I. Feldman, "Make: A program for maintaining computer programs", *Software: Practice and Experience* 9(4), 1979. Rebuild only what depends on what changed.
5. 🟢 Nancy Duarte, *Resonate*, Wiley, 2010. The Sparkline: what is against what could be.
6. 🟢 Daniel Kahneman, Olivier Sibony and Cass Sunstein, *Noise*, Little, Brown, 2021. Independent judgments before discussion.

## Claims to hold loosely

- 🟡 "Gates reduce rework." Cooper's evidence is largely survey-based; gates help when they check real evidence and hurt when they become paperwork. That is why every item needs evidence you can point to.
- 🔴 "More steps means a better process." A step earns its place by guarding against a named error.
