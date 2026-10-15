---
name: brand-ecosystem
description: Use when an approved brand must become the complete ecosystem, step 9. Triggers include "ecossistema da marca", "pacote completo da marca", "gerar logo e assets", "brand kit", "brandbook", "manual da marca com história, conceito, forma, cor e tipografia", "brand ecosystem", "design tokens da marca". Builds from one source file the story, concept, symbol, colour, type, voice, applications, tokens and an HTML manual, then audits the package against its own source before anything is delivered.
license: MIT
metadata:
  version: 1.0.0
  author: Alireza Rezvani
  category: marketing
  updated: 2026-10-15
---

# Brand Ecosystem: one source, every asset

A brand delivered as separate files drifts: the manual says one blue, the logo uses another. This skill removes the
drift. One source file feeds a generator, and a separate auditor reads the result without trusting the generator.
Reply in the user's language.

## Workflow

1. **Gate the source.** Fill `brand-source.v2` ([`assets/example_serra_fina_brand.json`](assets/example_serra_fina_brand.json)):
   story, purpose, pétreos, concept, personality, name, symbol geometry, colour families, type, elements, voice,
   applications, governance, plus the manual sections: scope, wordmark, lockups, version and background matrices, minimum sizes and protection by version, name in text, production sheets and delivery. Every number comes from approved steps 1 to 8.

```bash
python3 scripts/ecosystem_source_check.py --input brand.json --state brand-state.json
```

   Exit 0 ready, 2 thin, 3 sections missing, 4 refused (a vetoed hue, a placeholder, a step not approved).

2. **Build.**

```bash
python3 scripts/ecosystem_builder.py --source brand.json --out ./pkg --state brand-state.json
```

   It writes logo versions, elements, applications, tokens (JSON, CSS, guidelines spec), the voice guide, the HTML
   brandbook, a README and a `MANIFEST.json` with a SHA-256 per file. Names follow `{SIGLA}_{Name}_V{NN}_{DDMMAA}`.

3. **Audit.**

```bash
python3 scripts/ecosystem_auditor.py --dir ./pkg
```

   Exit 0 clean, 2 caveats, 4 blocked. It checks palette closure, vetoed hues, font closure, text contrast, anchors,
   accessibility, external resources and that the manual repeats the source numbers. It recomputes from the logo files themselves the contrast of every version on every background the matrix allows, the minimum size of each lockup and the delivery formats.

4. **Edit and share.** The Artifact version of the brandbook lets writers edit narrative text (history, purpose, concept,
   personality, name, photography, voice, FAQ, governance), save it to `content.json`, and download a clean HTML for the
   client. Colour, type, symbol, tokens and the locked decisions stay read only, so the manual keeps matching the logo.

5. **Record and hand over.** Submit step 9 in `brand_state.py` with the audit exit code as evidence. A person approves.

## Rules

- **Never edit a generated file.** Change the source and rebuild, or the manual stops matching the logo.
- **The symbol is a geometric study.** Say so to the team. A professional refines it before launch.
- **Text in logo files uses live fonts.** Convert to outlines before print.
- **CMYK values are approximate.** Print needs a profile and a proof.
- **A name that has not been searched is not cleared.** The package never claims trademark clearance.
- **The auditor outranks the builder.** A blocked audit stops delivery, whatever the builder printed.

See [`references/ecosystem_anatomy.md`](references/ecosystem_anatomy.md) and
[`references/generative_geometry.md`](references/generative_geometry.md).
