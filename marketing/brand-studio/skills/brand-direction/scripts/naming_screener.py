#!/usr/bin/env python3
"""naming_screener.py — screen name candidates against what a name cannot afford to be.

It does not create names and it is not a legal opinion. It removes the candidates that fail
for mechanical reasons, and prints the manual checks that stay with a person.

Per candidate:
  VETOED_TERM     BLOCK  contains a term the client vetoed
  NAME_CLOSE      BLOCK  similarity >= 0.80 to a competitor name, shares its distinctive word, or contains it whole
  CATEGORY_WORD   WARN   shares only a word the sector uses (listed in category_words); not distinctive
  INPI_CONFLICT   BLOCK  a registry check recorded a conflict
  NAME_NEAR       WARN   similarity 0.65-0.80 to a competitor name
  TOO_LONG        WARN   more than 14 letters
  TOO_MANY_SYLLABLES WARN  more than 4 syllables (vowel-group estimate)
  SPELLING_RISK   WARN   digits, hyphens, or letters with several common readings (x, c-cedilla, w, y, k)
  ABBREVIATION    WARN   the abbreviation the market will use matches a competitor's
  UNCHECKED       WARN   no INPI / domain / handle check recorded
  STALE_CHECK     WARN   a recorded check is older than 30 days
  DOMAIN_TAKEN    WARN   the domain check says taken

Manual checks printed for every candidate: connotations in each listed market and language,
pronunciation read aloud by three people, trademark classes to consult. Registries are consulted
by a person; this tool only records and ages the result.

Exit codes: 0 all CLEAR | 1 input error | 2 CAUTION (some warnings or some blocked) | 4 every candidate BLOCKED
Stdlib only. No network. Deterministic.
"""

import argparse
import datetime
import difflib
import json
import os
import re
import sys
import unicodedata


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s).lower()) if not unicodedata.combining(c))


def norm(s):
    return re.sub(r"[^a-z0-9]", "", fold(s))


def words(s):
    return re.findall(r"[a-z0-9]+", fold(s))


def syllables(name):
    return sum(len(re.findall(r"[aeiouy]+", w)) or 1 for w in words(name))


def abbreviation(name):
    w = words(name)
    return "".join(x[0] for x in w) if len(w) > 1 else (w[0][:3] if w else "")


def screen(c, data, as_of):
    out = []
    comps = data.get("competitors", [])
    for v in data.get("vetoed_terms", []):
        if norm(v) and norm(v) in norm(c):
            out.append(("BLOCK", "VETOED_TERM", f"contains the vetoed term '{v}'"))
    for comp in comps:
        r = difflib.SequenceMatcher(None, norm(c), norm(comp)).ratio()
        cat = {fold(w) for w in data.get("category_words", [])}
        both = {w for w in words(c) if len(w) >= 4} & {w for w in words(comp) if len(w) >= 4}
        shared, shared_cat = both - cat, both & cat
        contains = len(norm(comp)) >= 6 and norm(comp) in norm(c)
        if r >= 0.80 or shared or contains:
            why = f"shares '{sorted(shared)[0]}'" if shared else ("contains the whole name" if contains else "")
            out.append(("BLOCK", "NAME_CLOSE", f"too close to competitor '{comp}' (similarity {r:.2f}" + (f", {why}" if why else "") + ")"))
        elif shared_cat:
            out.append(("WARN", "CATEGORY_WORD", f"shares the category word '{sorted(shared_cat)[0]}' with '{comp}': common to the sector, not distinctive"))
        elif r >= 0.65:
            out.append(("WARN", "NAME_NEAR", f"similar to competitor '{comp}' ({r:.2f})"))
        if abbreviation(c) and abbreviation(c) == abbreviation(comp):
            out.append(("WARN", "ABBREVIATION", f"abbreviation '{abbreviation(c)}' is also used by '{comp}'"))
    letters = len(norm(c))
    if letters > 14:
        out.append(("WARN", "TOO_LONG", f"{letters} letters"))
    if syllables(c) > 4:
        out.append(("WARN", "TOO_MANY_SYLLABLES", f"about {syllables(c)} syllables"))
    risky = sorted({ch for ch in fold(c) if ch in "xwyk"} | ({"c-cedilla"} if "ç" in str(c).lower() else set()))
    if re.search(r"[0-9\-_]", c) or risky:
        out.append(("WARN", "SPELLING_RISK", "digits, hyphens or letters read in more than one way: " + (", ".join(risky) or "digit/hyphen")))
    reg = data.get("registry", {}).get(c, {})
    checked = False
    for kind in ("inpi", "domain", "handles"):
        item = reg.get(kind)
        if not item or item.get("status") in (None, "", "unknown"):
            continue
        checked = True
        try:
            age = (as_of - datetime.date.fromisoformat(item.get("date", ""))).days
        except ValueError:
            age = None
        if age is None or age > 30:
            out.append(("WARN", "STALE_CHECK", f"{kind} check is {'undated' if age is None else f'{age} days old'}"))
        if kind == "inpi" and item.get("status") == "conflict":
            out.append(("BLOCK", "INPI_CONFLICT", f"conflict recorded in classes {item.get('classes')}"))
        if kind == "domain" and item.get("status") == "taken":
            out.append(("WARN", "DOMAIN_TAKEN", "the domain is taken"))
    if not checked:
        out.append(("WARN", "UNCHECKED", "no INPI, domain or handle check recorded yet"))
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Screen brand name candidates. Not legal advice.")
    ap.add_argument("--input", help="naming JSON (see assets/example_naming.json)")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_naming.json") if a.sample else a.input
    if not path:
        ap.error("provide --input or --sample")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        as_of = datetime.date.fromisoformat(data.get("as_of") or datetime.date.today().isoformat())
        cands = data["candidates"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    rows = []
    for c in cands:
        f = screen(c, data, as_of)
        verdict = "BLOCKED" if any(x[0] == "BLOCK" for x in f) else ("CAUTION" if f else "CLEAR")
        rows.append({"candidate": c, "verdict": verdict, "findings": [{"level": l, "code": k, "message": m} for l, k, m in f]})
    rank = {"CLEAR": 0, "CAUTION": 1, "BLOCKED": 2}
    rows.sort(key=lambda r: (rank[r["verdict"]], len(r["findings"])))
    manual = [f"Read each candidate aloud with three people from the client's audience and write down what they heard and spelled.",
              "Connotations in: " + (", ".join(data.get("markets", [])) or "every market the brand will trade in"),
              "Consult the trademark office (Nice classes of the client's goods and services) and record status and date. This tool does not."]
    code = 4 if all(r["verdict"] == "BLOCKED" for r in rows) else (0 if all(r["verdict"] == "CLEAR" for r in rows) else 2)
    if a.output == "json":
        print(json.dumps({"as_of": str(as_of), "candidates": rows, "manual_checks": manual}, indent=2, ensure_ascii=False))
    else:
        for r in rows:
            print(f"{r['candidate']:<18} {r['verdict']}")
            for f in r["findings"]:
                print(f"    [{f['level']}] {f['code']}: {f['message']}")
        print("Manual checks that stay with a person:")
        for m in manual:
            print("  - " + m)
    sys.exit(code)


if __name__ == "__main__":
    main()
