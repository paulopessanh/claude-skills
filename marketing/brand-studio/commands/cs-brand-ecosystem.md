---
name: "cs-brand-ecosystem"
description: "/cs:brand-ecosystem — Build and audit the complete brand ecosystem (step 9) from one approved source: logo versions, elements, applications, tokens, voice guide and the HTML brandbook."
argument-hint: "[brand-source.json] [output folder]"
---

# /cs:brand-ecosystem — Build the whole brand

**Command:** `/cs:brand-ecosystem brand.json ./pkg`

```bash
S=marketing/brand-studio/skills/brand-ecosystem/scripts
python3 $S/ecosystem_source_check.py --input brand.json --state brand-state.json
python3 $S/ecosystem_builder.py --source brand.json --out ./pkg --state brand-state.json
python3 $S/ecosystem_auditor.py --dir ./pkg
```

Stop if the source check exits 3 or 4. Report the audit verdict, the file count and the three standing notes. Then submit
step 9 with the audit exit code as evidence. A person approves.
