# brand-studio

The full creative cycle of brand creation and visual identity, from briefing to manual. Português: processo criativo de marca e
identidade visual, de ponta a ponta.

Seven skills, one project state, five agents. Step 9 (brand-ecosystem) turns the approved brand into the full package: story, concept, symbol, colour, type, voice, applications, tokens and an HTML manual, audited against its own source.

| Skill | Steps | Answers |
|---|---|---|
| `brand-studio` (orchestrator) | all | where are we, what is next, what did this change break |
| `brand-discovery` | 1 to 3 | what do we know, what is missing, what does the category look like |
| `brand-direction` | 4 and 5 | what do we draw, what do we not draw, what did the client choose |
| `brand-color` | 4 | which colours, for which job, on which background, and what is never allowed |
| `brand-system` | 6 to 8 | is the identity complete, do the numbers agree, is the manual in sync |
| `brand-review` | every step | what is wrong, how will the client read it, what does this request touch |

It connects to [`../brand-reverse`](../brand-reverse) by data: reverse-engineer a reference brand there, carry only its value-free
`pattern` lines into direction, and pass the new brief through its `method_transfer_guard.py`.

## How the skills depend on each other

By contract, not by code. They exchange JSON files (brief, competitors, colours, votes, guidelines spec, project state). No skill
imports another's script, so each one can be extracted and used alone, and together they behave as one process.

## Try it

```bash
S=skills
python3 $S/brand-studio/scripts/brand_state.py --sample          # gates, refusals, reopen
python3 $S/brand-studio/scripts/brand_router.py --sample
python3 $S/brand-discovery/scripts/brief_gap_analyzer.py --sample
python3 $S/brand-discovery/scripts/competitor_matrix.py --sample
python3 $S/brand-direction/scripts/naming_screener.py --sample
python3 $S/brand-direction/scripts/color_system_builder.py --sample
python3 $S/brand-direction/scripts/anatomy_validator.py --sample
python3 $S/brand-direction/scripts/vote_tally.py --sample
python3 $S/brand-review/scripts/deliverable_linter.py --sample
python3 $S/brand-system/scripts/guidelines_completeness.py --sample
python3 $S/brand-system/scripts/asset_name_checker.py --sample
```

Examples are about fictional clients. Stdlib only, no network. Scripts help; they do not clear trademarks, print colour, or
replace a person who decides.
