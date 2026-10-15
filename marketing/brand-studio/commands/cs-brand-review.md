---
name: "cs-brand-review"
description: "/cs:brand-review — Review a branding deliverable before it goes out: mechanical lint, nine review layers with a second independent reading, the client's eyes, and a verdict of released, released with caveats or held."
argument-hint: "[path to the deliverable, plus the client's vetoed colours if any]"
---

# /cs:brand-review — Find the error before the client does

**Command:** `/cs:brand-review <deliverable> [--vetoed-hex #RRGGBB]`

Uses the `cs-brand-reviewer` agent (fresh context) and the `brand-review` skill.

```bash
S=marketing/brand-studio/skills/brand-review/scripts
python3 $S/deliverable_linter.py --input deliverable.md --vetoed-hex "#C9A227"
```

Then: nine layers, the decisor and end-customer reading, adherence map, studio biases, rejection risk with its reason. Output in
three levels (blocking, important, polish), a verdict, the layers not checked, and likely client questions with ready answers.
Record the verdict with `brand_state.py review --verdict ... --lint-exit <0|2>`: a release without the linter result, or on exit 4, is refused.
