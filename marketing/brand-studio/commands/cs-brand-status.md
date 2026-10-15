---
name: "cs-brand-status"
description: "/cs:brand-status — Status report of a branding project: nine steps with status and gate progress, stale steps, locked decisions, open client changes and the next action."
argument-hint: "[path to brand-state.json, default ./brand-state.json]"
---

# /cs:brand-status — Where the project stands

**Command:** `/cs:brand-status [state file]`

```bash
S=marketing/brand-studio/skills/brand-studio/scripts
python3 $S/brand_state.py status
python3 $S/brand_state.py next
python3 $S/brand_state.py log
```

Report: the step table (status, gate progress, verdict), anything stale and why, pétreos and vetados counts, open change
requests, risks to the schedule, and what the client owes. If a step is stale, say which upstream reopening caused it.
