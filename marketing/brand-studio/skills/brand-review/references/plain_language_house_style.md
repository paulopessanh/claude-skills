# Plain-language house style, and when to change it

Confidence key: 🟢 published primary source · 🟡 house preference or heuristic · 🔴 folklore.

## What the default profile enforces

`deliverable_linter.py` ships with `plain-ptbr-direct`: direct, human, active voice. It blocks em dashes, en dashes and
semicolons, emoji, unfinished markers and vetoed colours, and warns on clichés, hedges, likely passive voice, headings that end
with a period, figures with no source, term variants and implausible years.

🟡 These are **house preferences**. Banning a punctuation mark does not make text clear; the rules are a cheap, consistent way to
push writers toward short sentences and plain verbs, and they make drafts uniform across a team. Change them when your house
style differs: copy [`../assets/house_style_plain_ptbr.json`](../assets/house_style_plain_ptbr.json), edit it, pass `--profile`.

## What a profile can change

`banned_chars` (character to name), `cliches`, `hedges`, `placeholders`, `preferred_terms` (preferred term to its variants,
for example logo against logotipo), and a name. Add your own terms of art there and your own list of phrases your clients dislike.

## Why plain language

- Clear text is read faster and trusted more, especially by people who did not sit in the meeting.
- A term of art is explained on first use. A reference only designers recognise is explained or dropped.
- Active voice names who does what; passive hides the actor, which is a risk in a document that records decisions.

## Limits of the linter

It cannot judge facts, logic, tone or whether a metaphor works. The passive-voice rule is a heuristic and will flag legitimate
cases; read the line before changing it. Hedges are flagged because "might" often hides a decision you could state, but
honest uncertainty is allowed when you mark it as an assumption.

## Sources

1. 🟢 ISO 24495-1:2023, *Plain language, Part 1: Governing principles and guidelines*. Relevant, understandable, findable, usable.
2. 🟢 George Orwell, "Politics and the English Language", *Horizon*, 1946. Prefer the short word, the active verb, the concrete image.
3. 🟢 Steven Pinker, *The Sense of Style*, Viking, 2014. Writing as showing the reader something; the curse of knowledge.
4. 🟢 United States, Plain Writing Act of 2010 (Public Law 111-274). Government documents in clear writing.
5. 🟢 W3C, WCAG 2.1, SC 3.1.5 Reading Level (AAA). Supplementary content for lower reading levels.

## Claims to hold loosely

- 🟡 "Banning semicolons and dashes improves clarity." It encourages shorter sentences; it is not evidence of clarity.
- 🔴 "Passive voice is always wrong." It has uses (the actor is unknown or irrelevant). Flag it and decide.
- 🔴 "Never use a technical term." Use it, and explain it the first time.
