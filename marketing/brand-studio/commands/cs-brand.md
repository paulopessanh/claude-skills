---
name: "cs-brand"
description: "/cs:brand — Open, resume or route a brand creation and visual identity project. Reads the project state, routes the request to discovery, direction, system, review or reverse, and keeps every step behind its gate."
argument-hint: "[what you want to do, in your words, or 'novo projeto']"
---

# /cs:brand — The branding process, from briefing to manual

**Command:** `/cs:brand [request]`

Uses the `cs-brand-lead` agent and the `brand-studio` skill.

## When to run

- "Novo cliente de marca" / "retomar o projeto" / "qual o próximo passo"
- A client request arrives and you need to know what it touches
- You are unsure which step a task belongs to

## What happens

1. The lead reads `brand-state.json` (or asks only for what is missing to create it).
2. The router picks a lane: discovery (steps 1-3), direction (4-5), system (6-8), review, reverse. Ambiguous: it asks one question.
3. The step starts only if its prerequisites are approved. Work is delegated, then held at its gate with evidence.
4. Review and the client's eyes run before delivery. You get a status report after every action.

```bash
S=marketing/brand-studio/skills/brand-studio/scripts
python3 $S/brand_state.py init --client "Name" --sigla ABC --decisors "A,B"
python3 $S/brand_router.py --goal "..." --state brand-state.json
python3 $S/brand_state.py next
```
