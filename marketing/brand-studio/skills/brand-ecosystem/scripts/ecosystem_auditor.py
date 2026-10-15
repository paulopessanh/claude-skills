#!/usr/bin/env python3
"""ecosystem_auditor.py — audits a built brand ecosystem without trusting the builder.

It reads the package folder (MANIFEST.json and the source copy) and checks the files themselves.

BLOCK (exit 4):
  MANIFEST_MISSING     a file listed in MANIFEST.json does not exist
  SVG_NOT_XML          an SVG that does not parse
  COLOUR_NOT_TOKEN     a colour in any SVG, HTML or CSS file that is not a token of the brand
  VETOED_HUE           a colour within 25 degrees of a vetoed hue
  FONT_NOT_DECLARED    a font family used that the source does not declare (neither as a font nor as its fallback)
  TEXT_CONTRAST        text whose colour against its recorded background is under 4.5:1 (3:1 from 24 px; logotypes are exempt)
  TOKENS_DIFFER        tokens.json does not equal the tokens recomputed from the source
  MISSING_IN_BOOK      the brandbook lacks the name, tagline, descriptor, a pétreo, the mission, a voice trait, an application, a font or a token
  MISSING_CHAPTER      a required chapter is absent from the brandbook
  BROKEN_ANCHOR        a link to an id that does not exist; DUPLICATE_ID
  EXTERNAL_RESOURCE    anything loaded from outside, except the Google Fonts stylesheet and its font files
  HOUSE_STYLE          banned characters (em dash, en dash, semicolon), emoji or unfinished markers in the visible text
  SPEC_CONFLICT        the guidelines spec disagrees with itself (HEX and RGB, or a contrast pair that fails its declared level)
WARN (exit 2):
  EDITED_AFTER_BUILD   a file's SHA-256 differs from MANIFEST.json (someone edited it: rerun the audit, then rebuild from the source)
  UNLISTED_FILE        a file in the folder that MANIFEST.json does not list
  BAD_FILE_NAME        a file name outside {SIGLA}_{Name}_V{NN}_{DDMMAA}.ext
  A11Y                 an inline SVG without role and label; no lang; not exactly one h1
  VOICE                clichés or conditional language in the visible text

Always printed: the logo files are a geometric study to be refined in vector, and CMYK is approximate.

Exit codes: 0 CLEAN | 1 input error | 2 CLEAN_WITH_CAVEATS | 4 BLOCKED
Stdlib only. No network. Deterministic.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _ecolib import tokens, contrast, hex_rgb, oklch, hue_gap, NAME_RE, VETO_TOL, CHROMA_MIN   # noqa: E402

CHAPTERS = ["historia", "proposito", "petreos", "conceito", "personalidade", "nome", "simbolo", "versoes", "uso", "cor", "tipografia",
            "elementos", "fotografia", "movimento", "voz", "aplicacoes", "tokens", "governanca", "faq", "historico"]
GENERIC = {"serif", "sans-serif", "monospace", "cursive", "inherit", "system-ui"}
HEXC = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])")
RGBC = re.compile(r"rgba?\([^)]*\)|hsla?\([^)]*\)", re.I)
COLOR_ATTRS = ("fill", "stroke", "stop-color", "flood-color", "color")
BANNED = {"—": "em dash", "–": "en dash", ";": "semicolon"}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF✅❌]")
PLACE = re.compile(r"\b(TODO|TBD|XXX)\b|(?i:lorem ipsum)|\{\{|\}\}")
CLICHES = ["sinergia", "disruptivo", "alavancar", "mudar o jogo", "game changer", "de ponta", "solução inovadora", "cutting-edge", "state-of-the-art",
           "world-class", "best-in-class", "paradigma", "jornada transformadora", "next level", "holístico"]
HEDGES = ["talvez", "poderia", "pode ser que", "possivelmente"]


def fold(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


class Page(HTMLParser):
    """Collects what the checks need from the brandbook HTML in one pass."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.hrefs, self.text, self.h1, self.svgs, self.externals = [], [], [], 0, [], []
        self.styles, self.attrs_colour, self.texts_svg, self.lang = [], [], [], None
        self.skip, self.in_style, self.stack = 0, False, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.stack.append(tag)
        if tag == "html":
            self.lang = a.get("lang")
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag in ("script", "style", "pre", "code"):
            self.skip += 1
        if tag == "style":
            self.in_style = True
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        if tag == "svg" and "xmlns" not in a or tag == "svg":
            self.svgs.append((a.get("role"), a.get("aria-label")))
        for k in ("src", "href"):
            v = a.get(k, "")
            # <link> is judged separately (only the Google Fonts hosts are allowed); <a> may point anywhere.
            if v.startswith(("http://", "https://", "//")) and tag not in ("a", "link"):
                self.externals.append(v)
        if "style" in a:
            self.styles.append(a["style"])
        for k in COLOR_ATTRS:
            if k in a:
                self.attrs_colour.append(a[k])
        if tag == "text":
            self.texts_svg.append(a)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "pre", "code"):
            self.skip = max(0, self.skip - 1)
        if tag == "style":
            self.in_style = False
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self.in_style:
            self.styles.append(data)
        elif not self.skip:
            self.text.append(data)


def families(value):
    out = []
    for part in re.split(r",(?![^(]*\))", value):
        p = part.strip().strip("'\"")
        if p:
            out.append(p)
    return out


def audit(root, out_findings):
    F = out_findings
    add = lambda lvl, code, msg: F.append((lvl, code, msg))
    mpath = os.path.join(root, "MANIFEST.json")
    if not os.path.isfile(mpath):
        raise ValueError(f"{mpath} not found: is this a built ecosystem folder?")
    man = json.load(open(mpath, encoding="utf-8"))
    src = json.load(open(os.path.join(root, "source", next(f for f in os.listdir(os.path.join(root, "source")) if f.endswith(".json"))), encoding="utf-8"))
    flat, _ = tokens(src)
    allowed = {v.upper() for v in flat.values()}
    veto = [oklch(h)[2] for h in src["colour"].get("vetoed_hexes", []) if oklch(h)[1] >= CHROMA_MIN]
    declared_fonts = set()
    for f in src["typography"]["fonts"]:
        declared_fonts.add(f["name"])
        declared_fonts.update(families(f["fallback"]))
    listed = {m["path"] for m in man["files"]}
    # ---- manifest, names
    for m in man["files"]:
        fp = os.path.join(root, m["path"])
        if not os.path.isfile(fp):
            add("BLOCK", "MANIFEST_MISSING", m["path"])
        elif hashlib.sha256(open(fp, "rb").read()).hexdigest() != m["sha256"]:
            add("WARN", "EDITED_AFTER_BUILD", m["path"])
    for dp, _, fs in os.walk(root):
        for f in fs:
            rel = os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")
            if rel not in listed and rel != "MANIFEST.json":
                add("WARN", "UNLISTED_FILE", rel)
            if rel not in ("README.md", "MANIFEST.json") and not re.match(NAME_RE, f):
                add("WARN", "BAD_FILE_NAME", rel)
    used_colours, used_fonts, text_all = set(), set(), []

    def colours_in(s):
        for h in HEXC.findall(s):
            used_colours.add(h.upper() if len(h) == 7 else "#" + "".join(ch * 2 for ch in h[1:]).upper())
        for r in RGBC.findall(s):
            add("BLOCK", "COLOUR_NOT_TOKEN", f"{r} (a token is a hex colour)")

    def check_text(a, where):
        fill, bg, size = a.get("fill"), a.get("data-bg"), a.get("data-size")
        if a.get("data-exempt") == "logotype" or not (fill and bg and size):
            return
        if not (HEXC.fullmatch(fill) and HEXC.fullmatch(bg)):
            return
        sz = float(size)
        need = 3.0 if sz >= 24 else 4.5
        r = contrast(fill, bg)
        if r < need:
            add("BLOCK", "TEXT_CONTRAST", f"{where}: {fill} on {bg} is {r:.2f}:1 at {sz:g}px (needs {need}:1)")

    # ---- svg files
    for rel in sorted(listed):
        fp = os.path.join(root, rel)
        if not os.path.isfile(fp):
            continue
        if rel.endswith(".svg"):
            try:
                tree = ET.parse(fp)
            except ET.ParseError as e:
                add("BLOCK", "SVG_NOT_XML", f"{rel}: {e}")
                continue
            for el in tree.iter():
                for k in COLOR_ATTRS:
                    if k in el.attrib:
                        colours_in(el.attrib[k])
                if "style" in el.attrib:
                    colours_in(el.attrib["style"])
                if el.tag.endswith("style") and el.text:
                    colours_in(el.text)
                if el.attrib.get("font-family"):
                    used_fonts.update(families(el.attrib["font-family"]))
                if el.tag.endswith("text"):
                    check_text(el.attrib, rel)
            root_el = tree.getroot()
            if not root_el.attrib.get("aria-label") or root_el.attrib.get("role") != "img":
                add("WARN", "A11Y", f"{rel}: the SVG needs role=img and an aria-label")
        elif rel.endswith(".css"):
            colours_in(open(fp, encoding="utf-8").read())
        elif rel.endswith(".md"):
            text_all.append((rel, open(fp, encoding="utf-8").read()))
    # ---- brandbook
    books = [r for r in listed if r.endswith(".html")]
    if not books:
        add("BLOCK", "MISSING_CHAPTER", "no brandbook HTML in the manifest")
        return src, flat
    page = Page()
    html_src = open(os.path.join(root, books[0]), encoding="utf-8").read()
    page.feed(html_src)
    for s in page.styles + page.attrs_colour:
        colours_in(s)
        for m in re.finditer(r"font-family\s*:\s*([^;}]+)", s):
            used_fonts.update(families(m.group(1)))
        for m in re.finditer(r"font\s*:[^;}]*?(?:\d|\))\s+((?:'[^']+'|\"[^\"]+\"|[A-Za-z][\w -]*)(?:\s*,\s*(?:'[^']+'|[A-Za-z][\w -]*))*)", s):
            pass
    for a in page.texts_svg:
        check_text(a, books[0])
        if a.get("font-family"):
            used_fonts.update(families(a["font-family"]))
    text = re.sub(r"\s+", " ", " ".join(page.text))
    text_all.append((books[0], text))
    # chapters, anchors, ids
    for ch in CHAPTERS:
        if ch not in page.ids:
            add("BLOCK", "MISSING_CHAPTER", ch)
    dup = {i for i in page.ids if page.ids.count(i) > 1}
    for d in sorted(dup):
        add("BLOCK", "DUPLICATE_ID", d)
    for h in page.hrefs:
        if h.startswith("#") and len(h) > 1 and h[1:] not in page.ids:
            add("BLOCK", "BROKEN_ANCHOR", h)
    for ex in page.externals:
        add("BLOCK", "EXTERNAL_RESOURCE", ex)
    for m in re.finditer(r"url\((?!#|data:)([^)]+)\)", " ".join(page.styles + [html_src])):
        u = m.group(1).strip("'\" ")
        if u.startswith(("http", "//")):
            add("BLOCK", "EXTERNAL_RESOURCE", u)
    for m in re.finditer(r'<link[^>]+href="(https?://[^"]+)"', html_src):
        host = re.match(r"https?://([^/]+)", m.group(1)).group(1)
        if host not in ("fonts.googleapis.com", "fonts.gstatic.com"):
            add("BLOCK", "EXTERNAL_RESOURCE", m.group(1))
    if not page.lang:
        add("WARN", "A11Y", "the page has no lang attribute")
    if page.h1 != 1:
        add("WARN", "A11Y", f"the page has {page.h1} h1 elements; expected 1")
    bad_svg = sum(1 for r, l in page.svgs if r != "img" or not l)
    if bad_svg:
        add("WARN", "A11Y", f"{bad_svg} inline SVG(s) without role=img and aria-label")
    # ---- colour, hue, font closure
    for hx in sorted(used_colours):
        if hx not in allowed:
            add("BLOCK", "COLOUR_NOT_TOKEN", hx)
        else:
            c_, h_ = oklch(hx)[1], oklch(hx)[2]
            if c_ >= CHROMA_MIN and any(hue_gap(h_, v) <= VETO_TOL for v in veto):
                add("BLOCK", "VETOED_HUE", hx)
    for fnt in sorted(used_fonts):
        if fnt not in declared_fonts and fnt.lower() not in GENERIC and not fnt.startswith("var("):
            add("BLOCK", "FONT_NOT_DECLARED", fnt)
    # ---- source consistency
    need = [src["identity"]["name"], src["identity"]["tagline"], src["identity"]["descriptor"], src["purpose"]["mission"]]
    need += [p["text"] for p in src["petreos"]] + [t["name"] for t in src["voice"]["traits"]] + [a["name"] for a in src["applications"]]
    need += [f["name"] for f in src["typography"]["fonts"]] + [f"{src['identity']['sigla']}_{f['universe_name']}_50" for f in src["colour"]["families"]]
    need += [h for h in src["history"]["paragraphs"][:1]]
    miss = [n for n in need if n not in text and n.replace("’", "'") not in text]
    for n in miss:
        add("BLOCK", "MISSING_IN_BOOK", n[:70])
    tj = os.path.join(root, next((r for r in listed if r.endswith(".json") and "Tokens" in r), ""))
    if os.path.isfile(tj):
        cur = json.load(open(tj, encoding="utf-8")).get("colour", {})
        if {k: v.upper() for k, v in cur.items()} != {k: v.upper() for k, v in flat.items()}:
            add("BLOCK", "TOKENS_DIFFER", "tokens JSON differs from the tokens recomputed from the source")
    # ---- house style on visible text
    for where, tx in text_all:
        for ch, nm in BANNED.items():
            if ch in tx:
                add("BLOCK", "HOUSE_STYLE", f"{where}: {nm}")
        if EMOJI.search(tx):
            add("BLOCK", "HOUSE_STYLE", f"{where}: emoji")
        if PLACE.search(tx):
            add("BLOCK", "HOUSE_STYLE", f"{where}: unfinished marker")
        f_ = fold(tx)
        for cl in CLICHES:
            if fold(cl) in f_:
                add("WARN", "VOICE", f"{where}: cliché '{cl}'")
        for hd in HEDGES:
            if re.search(r"(?<![a-z])" + hd + r"(?![a-z])", f_):
                add("WARN", "VOICE", f"{where}: conditional language '{hd}'")
    # ---- guidelines spec
    sp = next((r for r in listed if "Guidelines-Spec" in r), None)
    if sp and os.path.isfile(os.path.join(root, sp)):
        spec = json.load(open(os.path.join(root, sp), encoding="utf-8"))
        for t in spec["colour"]["tokens"]:
            if tuple(t["rgb"]) != hex_rgb(t["hex"]):
                add("BLOCK", "SPEC_CONFLICT", f"{t['token']}: RGB does not equal HEX")
        for p in spec["colour"]["pairs"]:
            need_r = {"AA": 4.5, "AA_large": 3.0, "AAA": 7.0}.get(p["declared"], 4.5)
            if contrast(p["fg"], p["bg"]) < need_r:
                add("BLOCK", "SPEC_CONFLICT", f"{p['fg']} on {p['bg']} is {contrast(p['fg'], p['bg']):.2f}:1 but declared {p['declared']}")
    return src, flat


def main():
    ap = argparse.ArgumentParser(description="Audit a built brand ecosystem folder.")
    ap.add_argument("--dir", help="the folder written by ecosystem_builder.py")
    ap.add_argument("--sample", action="store_true", help="build the example into a temporary folder and audit it")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    cleanup = None
    if a.sample:
        import subprocess
        import tempfile
        import shutil
        cleanup = tempfile.mkdtemp(prefix="eco-audit-")
        r = subprocess.run([sys.executable, os.path.join(HERE, "ecosystem_builder.py"), "--source",
                            os.path.join(HERE, "..", "assets", "example_serra_fina_brand.json"), "--out", cleanup], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout + r.stderr, file=sys.stderr)
            sys.exit(1)
        root = cleanup
    elif a.dir:
        root = a.dir
    else:
        ap.error("provide --dir or --sample")
    F = []
    try:
        audit(root, F)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        if cleanup:
            import shutil
            shutil.rmtree(cleanup, ignore_errors=True)
    F = list(dict.fromkeys(F))
    blocks = [f for f in F if f[0] == "BLOCK"]
    code = 4 if blocks else (2 if F else 0)
    verdict = {0: "CLEAN", 2: "CLEAN_WITH_CAVEATS", 4: "BLOCKED"}[code]
    notes = ["The logo files are a geometric study generated from parameters: refine and finalise them in vector.",
             "Text in the logo files uses live fonts: convert to outlines before print.", "CMYK is approximate: print values need an ICC profile and a printed proof."]
    if a.output == "json":
        print(json.dumps({"verdict": verdict, "blocks": len(blocks), "warnings": len(F) - len(blocks),
                          "findings": [{"level": l, "code": c, "message": m} for l, c, m in F], "notes": notes}, indent=2, ensure_ascii=False))
    else:
        print(f"Verdict: {verdict}   blocks: {len(blocks)}   warnings: {len(F) - len(blocks)}")
        for l, c, m in F:
            print(f"  [{l}] {c}: {m}")
        for n in notes:
            print("  NOTE: " + n)
    sys.exit(code)


if __name__ == "__main__":
    main()
