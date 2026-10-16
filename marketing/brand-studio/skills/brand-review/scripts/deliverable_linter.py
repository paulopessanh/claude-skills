#!/usr/bin/env python3
"""deliverable_linter.py — the mechanical layer of a review: what a machine can catch before a person reads.

It lints a text deliverable (markdown, plain text, or HTML with the tags stripped) against a house-style
profile. It covers the layers a program can cover and says so: facts, narrative, concept and the client's
reaction still need the human or model review (see the brand-review skill).

Checks (BLOCK holds the deliverable, WARN asks for a look):
  BANNED_CHAR       BLOCK  characters the profile bans (default: em dash, en dash, semicolon)
  EMOJI             BLOCK  emoji, unless --allow-emoji (voting legends)
  PLACEHOLDER       BLOCK  TODO, TBD, XXX (capitals only), lorem ipsum, [..], {{ }}, [inserir ...] markers
  VETOED_COLOUR     BLOCK  a hex colour in the text within 25 degrees of a hue the client vetoed (--vetoed-hex)
  CLICHE            WARN   phrases from the profile's cliché list
  HEDGE             WARN   conditional language where a statement is possible
  PASSIVE           WARN   a likely passive construction (heuristic, Portuguese and English)
  TITLE_PERIOD      WARN   a markdown heading that ends with a period
  UNSOURCED_NUMBER  WARN   a figure (%, money, years, counts) on a line with no source or link
  TERM_VARIANT      WARN   a variant of a term the profile fixes (for example logo vs logotipo)
  YEAR_RANGE        WARN   a four-digit year outside 1900 .. as-of year + 2

Exit codes: 0 RELEASED | 1 input error | 2 RELEASED_WITH_CAVEATS | 4 HELD
Stdlib only. No network. Deterministic.
"""

import argparse
import colorsys
import datetime
import json
import math
import os
import re
import sys

DEFAULT_PROFILE = {
    "name": "plain-ptbr-direct",
    "banned_chars": {"—": "em dash", "–": "en dash", ";": "semicolon"},
    "cliches": ["sinergia", "disruptivo", "alavancar", "mudar o jogo", "game changer", "de ponta", "melhores praticas", "solucao inovadora",
                "cutting-edge", "state-of-the-art", "world-class", "best-in-class", "unparalleled", "passionate about", "paradigma",
                "ecossistema", "jornada transformadora", "nivel seguinte", "next level", "holistico", "robusto e escalavel"],
    "hedges": ["talvez", "poderia", "poderia ser", "pode ser que", "possivelmente", "perhaps", "might", "could potentially", "it seems"],
    "preferred_terms": {},
    "placeholders": ["TODO", "TBD", "XXX", "lorem ipsum", "{{", "}}"],     # TODO, TBD, XXX match in capitals only
}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF⭐⬆✅❌]")
HEXRE = re.compile(r"#(?:[0-9a-fA-F]{6})\b")
NUMBER = re.compile(r"\b\d[\d.,]*\s?(%|por cento|mil\b|milh|bilh|anos\b|years\b|x\b|R\$|US\$|€)|R\$\s?\d|US\$\s?\d|€\s?\d", re.I)
SOURCE = re.compile(r"(fonte|source|https?://|www\.|\(\d{4}\)|segundo|according to|dados de)", re.I)
PASSIVE_PT = re.compile(r"\b(foi|foram|é|são|será|serão|sendo|fora)\s+\w+(ad[oa]s?|id[oa]s?)\b", re.I)
PASSIVE_EN = re.compile(r"\b(was|were|is|are|been|being)\s+\w+ed\s+by\b", re.I)


def fold(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def hue(hexv):
    v = hexv.lstrip("#")
    r, g, b = (int(v[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = lin(r), lin(g), lin(b)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


def lint(text, prof, vetoed, allow_emoji, year):
    out = []
    add = lambda lvl, code, ln, msg: out.append({"level": lvl, "code": code, "line": ln, "message": msg})
    vet = [hue(v)[1] for v in vetoed if hue(v)[0] >= 0.04]
    for n, line in enumerate(text.splitlines(), 1):
        f = fold(line)
        for ch, nm in prof["banned_chars"].items():
            if ch in line:
                add("BLOCK", "BANNED_CHAR", n, f"{nm} ({ch!r})")
        if not allow_emoji and EMOJI.search(line):
            add("BLOCK", "EMOJI", n, "emoji in text")
        hit = None
        for ph in prof["placeholders"]:
            # Capitalised markers (TODO, TBD, XXX) match in capitals only: Portuguese "todo" means "every".
            pat = r"(?<![A-Za-z0-9])" + re.escape(ph) + r"(?![A-Za-z0-9])"
            if re.search(pat, line, 0 if ph.isupper() else re.I):
                hit = f"unfinished marker '{ph}'"
                break
        if not hit and (re.search(r"\[\s*(x+|\.\.\.|\u2026)?\s*\]", line)
                        or re.search(r"\[[^\]\n]*\b(inserir|preencher|fill in|placeholder)\b[^\]\n]*\]", line, re.I)):
            hit = "unfinished marker [..]"
        if hit:
            add("BLOCK", "PLACEHOLDER", n, hit)
        for hx in HEXRE.findall(line):
            c, h = hue(hx)
            if c >= 0.04 and any(min(abs(h - v), 360 - abs(h - v)) <= 25 for v in vet):
                add("BLOCK", "VETOED_COLOUR", n, f"{hx} is within 25 degrees of a vetoed hue")
        for cl in prof["cliches"]:
            if cl in f:
                add("WARN", "CLICHE", n, f"cliché '{cl}'")
        for hd in prof["hedges"]:
            if re.search(r"(?<![a-z])" + re.escape(hd) + r"(?![a-z])", f):
                add("WARN", "HEDGE", n, f"conditional language '{hd}'")
        if PASSIVE_PT.search(line) or PASSIVE_EN.search(line):
            add("WARN", "PASSIVE", n, "likely passive voice: " + (PASSIVE_PT.search(line) or PASSIVE_EN.search(line)).group(0))
        if re.match(r"\s*#{1,6}\s", line) and line.rstrip().endswith("."):
            add("WARN", "TITLE_PERIOD", n, "heading ends with a period")
        if NUMBER.search(line) and not SOURCE.search(line) and not re.match(r"\s*#", line):
            add("WARN", "UNSOURCED_NUMBER", n, "a figure with no source on the line")
        for pref, variants in prof["preferred_terms"].items():
            for v in variants:
                if re.search(r"(?<![a-z])" + re.escape(fold(v)) + r"(?![a-z])", f):
                    add("WARN", "TERM_VARIANT", n, f"use '{pref}' instead of '{v}'")
        for y in re.findall(r"\b(1[0-9]{3}|2[0-9]{3})\b", line):
            if not 1900 <= int(y) <= year + 2:
                add("WARN", "YEAR_RANGE", n, f"year {y} is outside 1900..{year + 2}")
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Mechanical review layer: house style, placeholders, vetoes, unsourced figures.")
    ap.add_argument("--input", help="text, markdown or html file")
    ap.add_argument("--sample", action="store_true", help="lint assets/example_deliverable.md")
    ap.add_argument("--profile", help="house-style profile JSON (default: built-in plain-ptbr-direct)")
    ap.add_argument("--vetoed-hex", action="append", default=[], help="a hex colour the client vetoed (repeatable)")
    ap.add_argument("--allow-emoji", action="store_true")
    ap.add_argument("--as-of-year", type=int, default=datetime.date.today().year)
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_deliverable.md") if a.sample else a.input
    if not path:
        ap.error("provide --input or --sample")
    prof = dict(DEFAULT_PROFILE)
    try:
        if a.profile:
            with open(a.profile, encoding="utf-8") as fh:
                prof.update(json.load(fh))
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        if path.lower().endswith((".html", ".htm")):
            text = re.sub(r"<[^>]+>", " ", text)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    vet = list(a.vetoed_hex) + (["#C9A227"] if a.sample else [])
    findings = lint(text, prof, vet, a.allow_emoji, a.as_of_year)
    blocks = sum(1 for f in findings if f["level"] == "BLOCK")
    code = 4 if blocks else (2 if findings else 0)
    verdict = {0: "RELEASED", 2: "RELEASED_WITH_CAVEATS", 4: "HELD"}[code]
    if a.output == "json":
        print(json.dumps({"verdict": verdict, "profile": prof["name"], "findings": findings}, indent=2, ensure_ascii=False))
    else:
        print(f"Verdict: {verdict}   profile: {prof['name']}   blocks: {blocks}   warnings: {len(findings) - blocks}")
        for f in findings:
            print(f"  line {f['line']:<4} [{f['level']}] {f['code']}: {f['message']}")
        print("Mechanical layer only. Facts, narrative, concept and the client's reading still need the review layers.")
    sys.exit(code)


if __name__ == "__main__":
    main()
