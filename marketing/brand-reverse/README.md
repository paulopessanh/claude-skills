# brand-reverse

Reverse engineer how a brand and its visual identity were made, then turn what you learn into
a creative process for a new brand. Português: engenharia reversa de marca e identidade visual.

You see a brand's outputs, never its inputs. This plugin keeps the guesses honest.

```bash
S=skills/brand-reverse/scripts
python3 $S/evidence_ledger.py       --sample   # claim gate
python3 $S/palette_logic_analyzer.py --sample  # colour and type logic
python3 $S/process_reconstructor.py --sample   # eight-stage rebuild (add --plan for yours)
python3 $S/method_transfer_guard.py --sample   # method, not marks
```

The sample is a fictional brand. Nothing here makes a claim about a real company.

| Tool | Refuses |
|---|---|
| `evidence_ledger.py` | Intent written as fact, inference with no rival, citations that do not exist |
| `palette_logic_analyzer.py` | Fewer than two colours; flags unusable contrast and type sprawl |
| `process_reconstructor.py` | Fewer than three recoverable stages; requirements implied downstream |
| `method_transfer_guard.py` | Hex, names, typefaces or assets in patterns; a new brand too close to the reference |

Not legal advice. A clean guard result is not trademark clearance.
Stdlib only, no network, no scraping.
