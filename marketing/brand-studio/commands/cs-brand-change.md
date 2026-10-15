---
name: "cs-brand-change"
description: "/cs:brand-change — Log and triage a client change request: verbatim text, the need behind it, the steps it touches, clashes with locked decisions, and a suggested accept, negotiate or defend for a person to decide."
argument-hint: "[the client's request, verbatim] [touches: scope,audience,name,anatomy,symbol,colour,type,elements,voice,pieces]"
---

# /cs:brand-change — A client asked for a change

**Command:** `/cs:brand-change "<verbatim request>" --touches colour,symbol`

```bash
S=marketing/brand-studio/skills/brand-studio/scripts
python3 $S/brand_state.py change --text "<verbatim>" --origin "call 12/10" --touches colour,symbol
python3 $S/brand_state.py resolve CH01 --class negotiate --by "Lead"     # a person decides
python3 $S/brand_state.py reopen <earliest affected step> --reason "CH01"
```

The triage lists affected steps, which approved ones would reopen, and any clash with a pétreo or vetado. It suggests; it does
not decide. After you accept, reopen the earliest affected step: every later step turns stale and must be revalidated with a
reason or reworked. Then update the team guidelines and the manual.
