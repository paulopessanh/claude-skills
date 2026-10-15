# Briefing and extraction: know the client before thinking about form

Confidence key: 🟢 published primary source · 🟡 secondary or judgment · 🔴 folklore.

## What a good brief separates

Three columns, always: what we know (fact, with source and date), what we think (hypothesis, marked), what is missing (gap, ranked).
`brief_gap_analyzer.py` enforces the first two and computes the third. A brief that blends them contaminates every later step,
because a designer cannot tell which sentence to trust.

Required fields the script checks: contracted scope, ambition, audience, origin of the name (critical); company history,
services, differentiators, current brand, competitors (important); deadlines, clients and proof, territories (useful); and
who decides.

## Reading the inputs

- Classify each input by date relative to any extraction meeting. A form filled after a conversation that already worked as a
  kick-off is "already extracted": use the content and do not repeat the dynamic.
- Record disagreement between decisors as a finding, not a footnote. Two people who like and dislike the same thing is a
  decision you have to get made, not an average to take.
- Check timelines against each other: years of relationship cannot exceed the age of the company. The script blocks the impossible case.

## Running the kick-off

- Ask about what people did, not what they would do. "Tell me about the last time a customer chose you over a bigger competitor"
  yields facts; "would customers value X?" yields compliments.
- Let the client name the attributes in their own words. Convert them to a short list afterwards.
- Archetypes are a lens for the conversation, not a result. Use them to generate hypotheses ("this sounds like a Sage with a Creator streak"), then test with episodes.

## Sources

1. 🟢 Rob Fitzpatrick, *The Mom Test*, 2013. Ask about past behaviour and specifics; avoid hypotheticals and flattery.
2. 🟢 Steve Portigal, *Interviewing Users*, Rosenfeld Media, 2013. Interview structure, silence, probing for stories.
3. 🟢 Margaret Mark and Carol S. Pearson, *The Hero and the Outlaw*, McGraw-Hill, 2001. Twelve brand archetypes.
4. 🟢 Jean-Noël Kapferer, *The New Strategic Brand Management*, Kogan Page (several editions). The identity prism: physique, personality, culture, relationship, reflection, self-image.
5. 🟢 David A. Aaker, *Building Strong Brands*, Free Press, 1996. Core and extended identity.
6. 🟢 Richard Nisbett and Timothy Wilson, "Telling more than we can know", *Psychological Review* 84(3), 1977. People give plausible but unreliable accounts of their own reasons, a reason to prefer episodes over explanations.
7. 🟢 Alina Wheeler, *Designing Brand Identity*, 5th ed., 2017. The research and strategy phases.

## Claims to hold loosely

- 🟡 The twelve archetypes are a popular framework with limited empirical validation. Useful for conversation, weak as measurement.
- 🔴 "Archetype tests reliably classify a brand." Two analysts rarely agree; treat the result as one hypothesis.
- 🔴 "The client knows what they want." They know what bothers them; the want is often a fear. Translate before you design.
