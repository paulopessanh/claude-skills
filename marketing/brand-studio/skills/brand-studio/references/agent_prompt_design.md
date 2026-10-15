# How the agents in this suite are written, and why

Confidence key: 🟢 published primary source · 🟡 applied here by analogy or judgment · 🔴 folklore.

The four agents (`cs-brand-lead`, `cs-brand-strategist`, `cs-brand-creative-director`, `cs-brand-reviewer`) are prompt
artifacts: standing instructions for an agentic loop with Read, Bash, Write and Edit and local scripts. Each is written to a
small doctrine. If you change one, keep the doctrine.

## The doctrine

1. **State the delivery context.** Which model class reads it, which tools it has, whether it runs alone or in a chain, and
   what it hands to the next agent. A prompt that does not say this is guessing about its own environment.
2. **Hard constraints are said plainly and short.** "Never approve a step whose gate is incomplete." No narrative around them.
3. **Reasons live where judgment lives.** A directive that needs judgment carries one sentence of why: "Mark every
   inference, because the next step inherits whichever you wrote." Reasons let the agent decide at an edge case no rule foresaw.
   Mechanical trivia gets no reason; it buries the signal.
4. **Deterministic work goes to scripts, judgment stays with the model.** A script can count votes and recompute contrast.
   It cannot say whether a concept is true to the client. The agent runs the script first, so its attention goes to judgment.
5. **Untrusted text is data.** Client messages, transcripts, web pages and uploaded files can carry imperative sentences.
   The agent triages them; it does not obey them.
6. **Challenge handling.** When challenged, classify first: does the challenge expose missing evidence or an error, or is it
   discomfort with a sound conclusion? Strip back to what is supported in the first case; restate calmly in the second.
   Never drop a reasoned position only because it was questioned, and never defend one only because it was stated.
7. **A defined deliverable shape and a defined stop.** Findings first, rationale second, open questions last; and a rule for
   when to stop and ask a person.
8. **No invented facts.** Registry results, sources, dates and measurements come from the user or a script, or are marked as assumed.

## Why these choices

- 🟢 Anthropic, "Building effective agents" (2024): prefer simple, composable patterns; give the agent clear tools and
  documentation; add structure only where it earns its place. This is why the suite is scripts plus short skills, not one
  long prompt.
- 🟢 Anthropic, prompt engineering documentation: be clear and direct, give context and the reason behind an instruction,
  and structure long inputs. Basis for items 1 to 3 and 7.
- 🟢 Liu et al., "Lost in the Middle: How Language Models Use Long Contexts", 2023 (arXiv:2307.03172): information in the
  middle of a long context is used less reliably. Basis for short SKILL files, hard rules placed visibly, and references one level deep.
- 🟢 Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", 2023 (arXiv:2306.05685): model judges show
  position, length and self-preference biases. Basis for running the deterministic lint first and asking a second, fresh-context reader.
- 🟢 Greshake et al., "Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt
  Injection", 2023 (arXiv:2302.12173). Content the agent reads can carry instructions. Basis for item 5.
- 🟢 Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models", 2022 (arXiv:2201.11903). Intermediate
  steps help multi-step reasoning. Basis for numbered workflows; the agent shows its checks, not a stream of thought.

## Claims to hold loosely

- 🔴 "Tell the model it is the world's best expert and quality rises." Effects of persona lines are small and uneven. The agents
  here carry a role for scope and voice, and their quality comes from gates, scripts and evidence.
- 🟡 The challenge-handling and reasons-where-judgment-lives rules are a working doctrine, not a tested result. Treat them as
  defaults and measure on your own failures: keep the failing output, find the violated expectation, patch minimally, retest.
