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
import html
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _ecolib import tokens, contrast, hex_rgb, oklch, hue_gap, NAME_RE, VETO_TOL, CHROMA_MIN   # noqa: E402

CHAPTERS = ["historia", "proposito", "petreos", "conceito", "personalidade", "nome", "simbolo", "logotipo", "versoes", "fundos", "uso", "cor",
            "tipografia", "elementos", "fotografia", "movimento", "voz", "aplicacoes", "tokens", "entrega", "governanca", "faq", "historico"]
POLF = {"positive": "Positive", "negative": "Negative", "mono": "Mono"}
KINDF = {"symbol": "Symbol", "horizontal": "Horizontal", "vertical": "Vertical"}
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
        self.svg_depth, self.text_plain = 0, []

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
        if tag == "svg":
            self.svg_depth += 1
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
        if tag == "svg":
            self.svg_depth = max(0, self.svg_depth - 1)
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self.in_style:
            self.styles.append(data)
        elif not self.skip:
            self.text.append(data)
            if not self.svg_depth:
                self.text_plain.append(data)


def families(value):
    out = []
    for part in re.split(r",(?![^(]*\))", value):
        p = part.strip().strip("'\"")
        if p:
            out.append(p)
    return out


def logo_file(root, listed, kind, pol):
    """Path of a logo file in the package, found by its role name, never by the generator's code."""
    want = f"-{POLF[pol]}."
    for r in sorted(listed):
        if r.startswith("logo/") and f"_{KINDF[kind]}{want[:-1]}_" in r and r.endswith(".svg"):
            return os.path.join(root, r)
    return None


def svg_ink_and_width(fp):
    """The colour the mark is drawn in (first stroke on a line or polyline) and the width of the file."""
    root_el = ET.parse(fp).getroot()
    ink = None
    for el in root_el.iter():
        if el.tag.endswith(("polyline", "line")) and el.attrib.get("stroke"):
            ink = el.attrib["stroke"]
            break
    return ink, float(root_el.attrib.get("width", "0") or 0)


def audit_v2(root, listed, src, flat, add, text, notes):
    """Numbers the manual states about versions, sizes and backgrounds, recomputed from the files themselves."""
    import math
    sig = src["identity"]["sigla"]
    ink, wid = {}, {}
    for k in KINDF:
        for pol in POLF:
            fp = logo_file(root, listed, k, pol)
            if fp is None:
                add("BLOCK", "MISSING_CHAPTER", f"logo file for {k} {pol}")
                continue
            ink[(k, pol)], wid[(k, pol)] = svg_ink_and_width(fp)
    if not wid:
        return
    us = src.get("usage", {})
    for r in us.get("background_matrix", []):
        k, _, pol = r["version"].partition(".")
        if r["background"] == "foto" or r["status"] == "forbidden" or (k, pol) not in ink:
            continue
        bg = flat.get(f"{sig}_{r['background']}")
        if bg is None or not ink[(k, pol)]:
            add("BLOCK", "MATRIX_UNKNOWN", f"{r['version']} on {r['background']}")
            continue
        ratio = contrast(ink[(k, pol)], bg)
        if ratio < 3.0:
            add("BLOCK", "MATRIX_CONTRAST", f"{r['version']} is {r['status']} on {r['background']} but the ink in the file has {ratio:.2f}:1 (needs 3:1)")
    sym_w = wid.get(("symbol", "positive"), 0)
    ms = src["symbol"]["min_size"]
    for r in us.get("min_size_by_version", []):
        w = wid.get((r["lockup"], "positive"), 0)
        if not (sym_w and w):
            continue
        ratio = w / sym_w
        if r["print_mm"] < math.ceil(ms["print_mm"] * ratio - 1e-9) or r["screen_px"] < math.ceil(ms["screen_px"] * ratio - 1e-9):
            add("BLOCK", "MIN_SIZE_BELOW_FILE", f"{r['lockup']}: declared {r['print_mm']} mm and {r['screen_px']} px, but the file is {ratio:.2f} times the symbol width")
    exts = {os.path.splitext(r)[1].lstrip(".") for r in listed}
    for f in src.get("delivery", {}).get("formats", []):
        if f not in exts:
            add("BLOCK", "DELIVERY_NOT_IN_PACKAGE", f"delivery lists {f} but the package has no such file")
    name = src["identity"]["name"]
    for where, tx in text:
        if name.upper() in tx:
            add("BLOCK", "NAME_CASE", f"{where}: the name in all capitals in running text")
    pend = [r["family"] for r in src["colour"].get("spot_refs", []) if r.get("status") == "pending_match"]
    if pend:
        notes.append("Spot colour is pending a press match for: " + ", ".join(pend) + ". Do not print as spot colour until a code is confirmed.")


STRAT_IDS = ["metodo", "diagnostico", "viradas", "direcao", "tom", "plataforma"]
SKIP_KEYS = {"status", "copyability", "kind", "letter", "position", "count", "n", "share", "highest_value"}


def leaf_strings(o):
    if isinstance(o, str):
        if len(o) >= 3:
            yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if not str(k).startswith("_") and k not in SKIP_KEYS:
                yield from leaf_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from leaf_strings(v)


def audit_strategy(src, html_src, text, add):
    """The strategic chapters: present, numbered in order, and repeating the source. Cells of the platform are re-derived here."""
    st = src["strategy"]
    sec = re.findall(r'<section id="([^"]+)" class="ch">', html_src)
    for cid in STRAT_IDS:
        if cid not in sec:
            add("BLOCK", "MISSING_CHAPTER", cid)
    nums = [int(n) for n in re.findall(r'<p class="eyebrow">Cap\u00edtulo (\d+)</p>', html_src)]
    if nums != list(range(1, len(sec) + 1)):
        add("BLOCK", "CHAPTER_NUMBERING", f"chapter numbers {nums[:6]}... are not 1 to {len(sec)} in order")
    nav = re.search(r'<nav class="toc"[^>]*>(.*?)</nav>', html_src, re.S)
    links = re.findall(r'href="#([^"]+)"', nav.group(1)) if nav else []
    if links != sec:
        add("BLOCK", "CHAPTER_NUMBERING", "the chapter list does not follow the order of the chapters")
    need = list(leaf_strings(st))
    for blk in ("audience", "history", "concept", "voice"):
        for key in {"audience": ["personas"], "history": ["arc"], "concept": ["reasons"], "voice": ["principles", "before_after", "dictionary"]}[blk]:
            need += list(leaf_strings(src[blk].get(key, [])))
    need += list(leaf_strings(src["personality"].get("archetype", {}))) + list(leaf_strings(src["personality"].get("scales", [])))
    need += [src["purpose"]["essence"], src["purpose"]["reason_to_exist"]]
    seen = set()
    for n in need:
        if n in seen:
            continue
        seen.add(n)
        if n not in text and n.replace("\u2019", "'") not in text:
            add("BLOCK", "MISSING_IN_BOOK", "strategy: " + n[:60])
    # the label of each personality ruler is computed from its position: 0 and 4 are the ends, 2 is the middle
    for x in src["personality"].get("scales", []):
        lab = {0: "100% " + x["left"], 1: "75% " + x["left"], 2: "Equil\u00edbrio", 3: "75% " + x["right"], 4: "100% " + x["right"]}.get(x.get("position"))
        if lab is None or lab not in text:
            add("BLOCK", "MISSING_IN_BOOK", f"ruler label for {x['left']} / {x['right']}")
    # tensions without a decision, and the decision itself
    for t in st.get("tensions", []):
        if not str(t.get("decision", "")).strip():
            add("BLOCK", "TENSION_NO_DECISION", str(t.get("side_a", ""))[:50])
    # shares
    sh = [x.get("share", 0) for x in st.get("content_pillars", [])]
    if sh and sum(sh) != 100:
        add("BLOCK", "SHARES_NOT_100", f"content pillars add up to {sum(sh)}")
    for x in st.get("content_pillars", []):
        if f"{x['share']}%" not in text:
            add("BLOCK", "MISSING_IN_BOOK", f"share {x['share']}% of {x['name']}")
    # small sample
    pc = st.get("perception")
    if pc:
        if not pc.get("n") or "qualitativ" not in fold(pc.get("sample_note", "")):
            add("BLOCK", "SAMPLE_UNLABELLED", "the perception research needs n and a note that it is qualitative")
        if f"Respostas v\u00e1lidas: {pc.get('n')}" not in text:
            add("BLOCK", "MISSING_IN_BOOK", "perception sample size")
    # sources of market data
    outlets = {x["outlet"] for x in st.get("sources", [])}
    for m in st.get("market_data", []):
        if m.get("source") not in outlets:
            add("BLOCK", "DATA_NO_SOURCE", str(m.get("label", ""))[:50])
    # the 12 cells of the platform, derived again from the source
    cells = platform_values(src)
    m_ = re.search(r'<dl class="plat">(.*?)</dl>', html_src, re.S)
    page_cells = [html.unescape(re.sub(r"<[^>]+>", "", x)) for x in re.findall(r"<dd>(.*?)</dd>", m_.group(1), re.S)] if m_ else []
    if len(page_cells) != 12:
        add("BLOCK", "PLATFORM_CELLS", f"the platform page has {len(page_cells)} cells; expected 12")
    for i, (want, got) in enumerate(zip(cells, page_cells)):
        if want.strip() != got.strip():
            add("BLOCK", "PLATFORM_CELLS", f"cell {i + 1} does not repeat its source: '{got[:50]}'")


def platform_values(src):
    """The 12 cells of the platform, derived again from the source (independent of the builder)."""
    st = src["strategy"]
    vals = ", ".join(v["name"] for v in st.get("values", []))
    traits = ", ".join(t["name"] for t in src["voice"]["traits"])
    return [src["concept"]["big_idea"], src["identity"]["tagline"], src["purpose"]["essence"], src["purpose"]["reason_to_exist"], src["purpose"]["promise"], st.get("category", ""),
            src["purpose"]["positioning"], vals, src["personality"]["archetype"]["intersection_name"], traits, src["audience"]["summary"], st.get("synthesis", {}).get("desired_perception", "")]


def audit_deck(src, html_src, text, add, where):
    """The deck follows the same consistency rules as the reference manual's lessons: numbering, running header, year, contents, derived platform."""
    st = src["strategy"]
    arts = re.findall(r'<article class="sl[^"]*" id="dk-(\d+)" data-n="(\d+)"(?: data-ch="(\d)")?', html_src)
    if not arts:
        add("BLOCK", "DECK_EMPTY", f"{where}: no slides found")
        return
    ids = [int(a) for a, _, _ in arts]
    ns = [int(n) for _, n, _ in arts]
    if ids != list(range(1, len(arts) + 1)) or ns != ids:
        add("BLOCK", "DECK_NUMBERING", f"{where}: slide numbers are not 1 to {len(arts)} in order and unique")
    pg = [int(x) for x in re.findall(r'<span class="pg">(\d+)</span>', html_src)]
    if pg != list(range(2, len(arts) + 1)):
        add("BLOCK", "DECK_NUMBERING", f"{where}: the page numbers in the footers are not 2 to {len(arts)} in order and unique")
    years = set(re.findall(r"<footer><span>[^<]*</span><span>[^<]*? \u00b7 (\d{4})</span>", html_src))
    if years != {str(src["identity"]["date"])[:4]}:
        add("BLOCK", "DECK_YEAR", f"{where}: the footers show years {sorted(years)}; the date of the source is {src['identity']['date']}")
    heads = {}
    for n_, ch_, lab in re.findall(r'<article class="sl[^"]*" id="dk-(\d+)" data-n="\d+" data-ch="(\d)"[^>]*>(?:<span class="wm"[^>]*>[^<]*</span>)?<header><span>([^<]*)</span>', html_src):
        heads.setdefault(ch_, set()).add(lab)
    for ch_, labs in heads.items():
        if len(labs) != 1:
            add("BLOCK", "DECK_HEADER", f"{where}: chapter {ch_} has more than one running header: {sorted(labs)}")
    toc = re.search(r'<div class="tc">(.*?)</div></div>(?:<p class="tn">.*?</p>)?<footer>', html_src, re.S)
    if not toc:
        add("BLOCK", "DECK_TOC", f"{where}: no contents slide")
    else:
        groups = re.findall(r"<div><h3>([^<]*)</h3>((?:<a .*?</a>)+)</div>", toc.group(1), re.S)
        if not groups:
            add("BLOCK", "DECK_TOC", f"{where}: the contents slide lists no parts")
        for gname, rows in groups:
            for to, pgn in re.findall(r'<a data-to="dk-(\d+)"><span>[^<]*</span><b>(\d+)</b></a>', rows):
                if to != pgn or int(to) > len(arts):
                    add("BLOCK", "DECK_TOC", f"{where}: the contents point to page {pgn} but the link goes to slide {to}")
                    continue
                m = re.search(r'<article class="sl[^"]*" id="dk-' + to + r'" data-n="\d+" data-ch="\d"[^>]*>(?:<span class="wm"[^>]*>[^<]*</span>)?<header><span>([^<]*)</span>', html_src)
                if not m or html.unescape(m.group(1)) != html.unescape(gname):
                    add("BLOCK", "DECK_HEADER", f"{where}: slide {to} runs under '{m.group(1) if m else '?'}' but the contents list it under '{gname}'")
    m_ = re.search(r'<dl class="plat">(.*?)</dl>', html_src, re.S)
    cells = [html.unescape(re.sub(r"<[^>]+>", "", x)) for x in re.findall(r"<dd>(.*?)</dd>", m_.group(1), re.S)] if m_ else []
    want = platform_values(src)
    if len(cells) != 12 or any(a.strip() != b_.strip() for a, b_ in zip(want, cells)):
        add("BLOCK", "PLATFORM_CELLS", f"{where}: the platform slide does not repeat its sources")
    for t in st.get("tensions", []):
        if t["decision"] not in text:
            add("BLOCK", "MISSING_IN_BOOK", f"{where}: tension decision: {t['decision'][:50]}")
    for x in st.get("content_pillars", []):
        if f"{x['share']}%" not in text:
            add("BLOCK", "MISSING_IN_BOOK", f"{where}: share {x['share']}% of {x['name']}")
    pc = st.get("perception")
    if pc and f"Respostas v\u00e1lidas: {pc['n']}" not in text:
        add("BLOCK", "SAMPLE_UNLABELLED", f"{where}: the deck shows the research without its sample size")
    extra = []
    for x in st.get("market_data", []):
        extra += [x["label"], x["figure"], x["source"]]
    for x in st.get("market_shifts", []):
        extra += [x["date"], x["fact"], x["effect"]]
    for x in st.get("market_implications", []):
        extra += [x["title"], x["text"]]
    for x in st.get("value_equation", {}).get("reading", []):
        extra += [x["factor"], x["reading"], x["action"]]
    ss_ = st.get("slogan_system")
    if ss_:
        extra += [ss_["first_beat"], ss_["second_beat"]] + [u["line"] for u in ss_["usage"]] + list(ss_["support_lines"])
    ba_ = st.get("brand_architecture")
    if ba_:
        extra += [ba_["parent"], ba_["rule"]] + list(ba_["children"])
    for n in extra:
        if n not in text:
            add("BLOCK", "MISSING_IN_BOOK", f"{where}: {n[:50]}")
    for x in st.get("value_equation", {}).get("reading", []):
        if not re.search(re.escape(html.escape(x["factor"])) + r"</span><span class=\"(?:tr|pb)[^>]*>.*?</span><b>" + str(x["score"]) + r" de 5</b>", html_src, re.S) and not re.search(re.escape(html.escape(x["factor"])) + r"</span><span class=\"tr\"><i style=\"width:\d+%\"></i></span><b>" + str(x["score"]) + r" de 5</b>", html_src):
            add("BLOCK", "MISSING_IN_BOOK", f"{where}: score {x['score']} of {x['factor']}")
    for n in [st["guiding_question"], st["synthesis"]["territory"], src["purpose"]["positioning"], src["concept"]["big_idea"]] + [v["name"] for v in st["values"]]:
        if n not in text:
            add("BLOCK", "MISSING_IN_BOOK", f"{where}: {n[:50]}")


def audit(root, out_findings, notes=None):
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
    html_files = sorted(r for r in listed if r.endswith(".html"))
    books = [r for r in html_files if "Brandbook" in r] or html_files[:1]
    decks = [r for r in html_files if "_Deck_" in r]
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
    if src.get("strategy"):
        if 'id="deck-open"' not in html_src or 'id="deck"' not in html_src:
            add("BLOCK", "MISSING_CHAPTER", "the manual has no deck button or no deck")
        audit_deck(src, html_src, text, add, "manual")
        if not decks:
            add("BLOCK", "MISSING_CHAPTER", "no deck file in the manifest")
    for dr in decks:
        dpage = Page()
        dsrc = open(os.path.join(root, dr), encoding="utf-8").read()
        dpage.feed(dsrc)
        for s_ in dpage.styles + dpage.attrs_colour:
            colours_in(s_)
            for m in re.finditer(r"font-family\s*:\s*([^;}]+)", s_):
                used_fonts.update(families(m.group(1)))
        for a in dpage.texts_svg:
            check_text(a, dr)
            if a.get("font-family"):
                used_fonts.update(families(a["font-family"]))
        for ex in dpage.externals:
            add("BLOCK", "EXTERNAL_RESOURCE", ex)
        for d_ in sorted({i for i in dpage.ids if dpage.ids.count(i) > 1}):
            add("BLOCK", "DUPLICATE_ID", f"deck: {d_}")
        dtext = re.sub(r"\s+", " ", " ".join(dpage.text))
        text_all.append((dr, dtext))
        if src.get("strategy"):
            audit_deck(src, dsrc, dtext, add, "deck")
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
    if src.get("schema") == "brand-source.v2":
        need += [src["governance"]["scope"], src["governance"]["ip_notice"], src["wordmark"]["lettering"], src["lockups"]["horizontal"]["when"], src["lockups"]["vertical"]["when"],
                 src["usage"]["conflicting_background_rule"], src["usage"]["text_alignment"], src["voice"]["name_in_text"]["case"], src["delivery"]["outlined_and_editable"],
                 src["colour"]["large_area_rule"]]
        need += [r["use_when"] for r in src["versions"]["matrix"]] + [r["rule"] for r in src["typography"]["restrictions"]]
        need += [f"{r['print_mm']} mm" for r in src["usage"]["min_size_by_version"]] + [a["production"]["format"] for a in src["applications"]]
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
    if src.get("schema") == "brand-source.v2":
        audit_v2(root, listed, src, flat, add, [t for t in text_all if t[0] != books[0]] + [(books[0], re.sub(r"\s+", " ", " ".join(page.text_plain)))], notes if notes is not None else [])
    if src.get("strategy"):
        audit_strategy(src, html_src, text, add)
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
    F, extra_notes = [], []
    try:
        audit(root, F, extra_notes)
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
    notes += extra_notes
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
