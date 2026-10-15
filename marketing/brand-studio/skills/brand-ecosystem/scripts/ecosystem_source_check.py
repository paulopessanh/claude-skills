#!/usr/bin/env python3
"""ecosystem_source_check.py — is the single source of the brand complete enough to build an ecosystem from?

The ecosystem (brandbook, logo files, tokens, pattern, pictograms, applications, voice guide) is generated from ONE
file, brand-source.v1, so that no colour, name or sentence can differ between two places. This script decides whether
that file may be built from. It builds nothing.

Refusals (BLOCK, exit 4):
  NOT_APPROVED     a step from 1 to 8 is not approved (with --state: read from the project state; without: from provenance)
  MISSING_SECTION  a required section is absent: identity, provenance, history, purpose, petreos, vetados, personality,
                   audience, concept, symbol, colour, typography, elements, photography, motion, voice, applications,
                   governance, faq, changelog
  NO_SOURCE        history has no sources: a story needs the documents it came from
  PLACEHOLDER      TODO, TBD, lorem ipsum, XXX, [..], {{ }} anywhere in the text
  BAD_HEX          a colour is not a six-digit hex
  VETOED_HUE       a family or neutral sits within 25 degrees of a vetoed hue
  BAD_REFERENCE    a ratio or pair names a token that does not exist, or a font role that does not exist
  BAD_SYMBOL       the symbol vertices are not a closed alternating ridge (start and end at 0, alternate up and down)
  UNKNOWN_APP      an application id the builder cannot draw (bag, card, social, site, box, letterhead)
  TOO_FEW          fewer than the minimum items: 3 pétreos, 3 voice traits, 3 manifesto lines, 3 fonts roles, 4 applications, 6 misuse cases
Schema v2 adds the sections an identity manual needs beyond the v1 layers, each with its own refusal (a v1 source is refused as SOURCE_V1):
  MISSING_SECTION  scope and ip_notice (governance), wordmark, lockups, versions.matrix, usage (min sizes, protection, background matrix,
                   conflicting-background rule), typography.restrictions, colour.spot_refs, voice.name_in_text, support_rules, delivery
  MIN_SIZE_BELOW_GEOMETRY  a lockup's declared minimum is smaller than the symbol minimum scaled by the file's width ratio
  BAD_MATRIX       a background matrix row names an unknown version, background or status, or marks a version preferred or allowed on a
                   background where the mark's ink has less than 3:1 contrast, or a version has no preferred background
  BAD_REFERENCE    (v2) a restriction names a font role that does not exist; a spot reference names a family that does not exist or is
                   marked matched with no code
Warnings (exit 2):
  NOT_LABELLED     the source is marked fictional but has no _note, or is real but carries a _note
  NO_PROOF         a messaging territory has no proof; a pétreo has no visual translation

Exit codes: 0 READY | 1 input error | 2 READY_WITH_CAVEATS | 3 INSUFFICIENT (under half the sections) | 4 BLOCKED
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import math
import re
import sys

SECTIONS = ["identity", "provenance", "history", "purpose", "petreos", "vetados", "personality", "audience", "concept", "symbol",
            "colour", "typography", "elements", "photography", "motion", "voice", "applications", "governance", "faq", "changelog"]
APPS = {"bag", "card", "social", "site", "box", "letterhead"}
PICTOS = {"ridge", "lot", "altitude", "time", "gift", "origin"}
# Case-sensitive on purpose: Portuguese "todo" (every) and "preencher" (to fill in) are ordinary words.
PLACEHOLDER = re.compile(r"\b(TODO|TBD|XXX)\b|(?i:lorem ipsum)|\{\{|\}\}|\[\s*(x+|\.\.\.|\u2026)?\s*\]|(?i:\[[^\]]*\b(inserir|preencher|fill in|placeholder)\b[^\]]*\])")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
VETO_TOL = 25


def hue(hx):
    v = hx.lstrip("#")
    r, g, b = ((lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)(int(v[i:i + 2], 16) / 255.0) for i in (0, 2, 4))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if not str(k).startswith("_"):
                yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


LOCKUPS = ("symbol", "horizontal", "vertical")
POLS = ("positive", "negative", "mono")
STATUSES = ("preferred", "allowed", "forbidden")
PROD_KEYS = ("format", "colour_mode", "process", "material", "finishing", "scale")


def check_v2(b, add, tokens):
    import math
    from _ecolib import tokens as mk_tokens, contrast as ctr
    import _ecoassets as A
    ident = b.get("identity", {})
    sig = ident.get("sigla", "")
    g = b.get("governance", {})
    for k in ("scope", "ip_notice"):
        if not str(g.get(k, "")).strip():
            add("BLOCK", "MISSING_SECTION", f"governance.{k}")
    wm = b.get("wordmark", {})
    cap, xh = wm.get("cap_height_ratio", 0), wm.get("x_height_ratio", 0)
    if not str(wm.get("lettering", "")).strip() or not (0.5 <= cap <= 0.95 and 0.25 <= xh < cap):
        add("BLOCK", "MISSING_SECTION", "wordmark needs lettering, cap_height_ratio (0.5 to 0.95) and x_height_ratio (0.25 up to the cap height)")
    lk = b.get("lockups", {})
    for k in ("horizontal", "vertical"):
        if not str(lk.get(k, {}).get("when", "")).strip():
            add("BLOCK", "MISSING_SECTION", f"lockups.{k}.when")
    mx = b.get("versions", {}).get("matrix", [])
    seen = set()
    if len(mx) < 6:
        add("BLOCK", "TOO_FEW", "versions.matrix needs 6 or more rows (lockup, polarity, use_when)")
    for r in mx:
        key = (r.get("lockup"), r.get("polarity"))
        if r.get("lockup") not in LOCKUPS or r.get("polarity") not in POLS or not str(r.get("use_when", "")).strip() or key in seen:
            add("BLOCK", "BAD_MATRIX", f"versions.matrix row {key}: unknown, repeated or without use_when")
        seen.add(key)
    us = b.get("usage", {})
    try:
        flat, fams = mk_tokens(b)
        c = A.Ctx(b, flat, fams)
    except (KeyError, ValueError, TypeError):
        return
    ms = b.get("symbol", {}).get("min_size", {})
    rows = {r.get("lockup"): r for r in us.get("min_size_by_version", [])}
    for k in LOCKUPS:
        r = rows.get(k)
        if not r or not r.get("print_mm") or not r.get("screen_px"):
            add("BLOCK", "MISSING_SECTION", f"usage.min_size_by_version for {k}")
            continue
        ratio = A.width_ratio(c, k)
        floor_mm, floor_px = math.ceil(ms.get("print_mm", 0) * ratio - 1e-9), math.ceil(ms.get("screen_px", 0) * ratio - 1e-9)
        if r["print_mm"] < floor_mm or r["screen_px"] < floor_px:
            add("BLOCK", "MIN_SIZE_BELOW_GEOMETRY", f"{k}: {r['print_mm']} mm and {r['screen_px']} px, but the symbol minimum scaled by the file width is {floor_mm} mm and {floor_px} px")
    pr = {r.get("lockup"): r.get("peak_heights") for r in us.get("protection_by_version", [])}
    if any(k not in pr or not isinstance(pr[k], (int, float)) or not 0.5 <= pr[k] <= 2 for k in LOCKUPS):
        add("BLOCK", "MISSING_SECTION", "usage.protection_by_version: every lockup needs peak_heights between 0.5 and 2")
    elif len(set(pr.values())) > 1:
        add("WARN", "NO_PROOF", "protection area differs between versions: a single fraction for all versions is easier to police")
    for k in ("conflicting_background_rule", "text_alignment"):
        if not str(us.get(k, "")).strip():
            add("BLOCK", "MISSING_SECTION", f"usage.{k}")
    bgs = {r.get("background") for r in us.get("background_matrix", [])}
    best = {f"{k}.{p}": 0 for k in LOCKUPS for p in POLS}
    for r in us.get("background_matrix", []):
        v, bg, st = r.get("version", ""), r.get("background"), r.get("status")
        k, _, p = v.partition(".")
        if v not in best or st not in STATUSES or not bg:
            add("BLOCK", "BAD_MATRIX", f"row {v!r} on {bg!r}: unknown version or status")
            continue
        if bg == "foto":
            if not r.get("note"):
                add("BLOCK", "BAD_MATRIX", f"{v} on foto needs a note saying when it holds")
            continue
        if f"{sig}_{bg}" not in tokens:
            add("BLOCK", "BAD_MATRIX", f"{v} on {bg}: not a token of the brand")
            continue
        if st != "forbidden":
            ratio = ctr(flat[f"{sig}_{A.ink_of(c, p)}"], flat[f"{sig}_{bg}"])
            if ratio < 3.0:
                add("BLOCK", "BAD_MATRIX", f"{v} on {bg} is {st} but the ink has {ratio:.2f}:1 contrast (needs 3:1)")
        if st == "preferred":
            best[v] += 1
    if len(bgs - {"foto"}) < 4 or any(n == 0 for n in best.values()):
        add("BLOCK", "BAD_MATRIX", "the matrix needs 4 or more backgrounds and a preferred background for every version" + (": none for " + ", ".join(k for k, n in best.items() if n == 0) if any(n == 0 for n in best.values()) else ""))
    roles = {f.get("role") for f in b.get("typography", {}).get("fonts", [])}
    rs = b.get("typography", {}).get("restrictions", [])
    if len(rs) < 2 or any(r.get("font_role") not in roles or not r.get("rule") for r in rs):
        add("BLOCK", "BAD_REFERENCE", "typography.restrictions: 2 or more, each with a font role that exists and a rule")
    fam_names = {f.get("universe_name") for f in b.get("colour", {}).get("families", [])}
    sp = b.get("colour", {}).get("spot_refs", [])
    if not sp or any(r.get("family") not in fam_names or (r.get("status") == "matched" and not r.get("code")) or r.get("status") not in ("matched", "pending_match") for r in sp):
        add("BLOCK", "BAD_REFERENCE", "colour.spot_refs: one per family, status matched (with a code) or pending_match")
    if not str(b.get("colour", {}).get("large_area_rule", "")).strip():
        add("BLOCK", "MISSING_SECTION", "colour.large_area_rule")
    nt = b.get("voice", {}).get("name_in_text", {})
    if ident.get("name", "") not in str(nt.get("case", "")) or len(nt.get("never", [])) < 2 or not nt.get("class"):
        add("BLOCK", "MISSING_SECTION", "voice.name_in_text needs class, a case rule that writes the name as it must appear, and 2 or more never rules")
    sr = b.get("elements", {}).get("support_rules", {})
    if not sr.get("as_mask") or not sr.get("as_cut_template") or not sr.get("colours_allowed") or any(f"{sig}_{t}" not in tokens for t in sr.get("colours_allowed", [])):
        add("BLOCK", "BAD_REFERENCE", "elements.support_rules needs as_mask, as_cut_template and colours_allowed that are tokens")
    sg = b.get("elements", {}).get("symbol_as_graphic", {})
    if len(sg.get("positions", [])) < 2 or len(sg.get("colour_options", [])) < 2 or not sg.get("where"):
        add("BLOCK", "MISSING_SECTION", "elements.symbol_as_graphic needs 2 or more positions, 2 or more colour options and where")
    for a in b.get("applications", []):
        pd = a.get("production", {})
        if any(not str(pd.get(k, "")).strip() for k in PROD_KEYS):
            add("BLOCK", "MISSING_SECTION", f"application {a.get('id')}: production needs {', '.join(PROD_KEYS)}")
    dl = b.get("delivery", {})
    if not dl.get("formats") or not dl.get("colour_systems") or not dl.get("outlined_and_editable"):
        add("BLOCK", "MISSING_SECTION", "delivery needs formats, colour_systems and outlined_and_editable")


def check(b, state_path=None):
    out = []
    add = lambda lvl, code, msg: out.append((lvl, code, msg))
    present = [s for s in SECTIONS if s in b and b[s]]
    for s in SECTIONS:
        if s not in b or not b[s]:
            add("BLOCK", "MISSING_SECTION", s)
    if len(present) < len(SECTIONS) / 2:
        return out, present
    ident = b.get("identity", {})
    for k in ("name", "sigla", "descriptor", "tagline", "language", "version", "date"):
        if not str(ident.get(k, "")).strip():
            add("BLOCK", "MISSING_SECTION", f"identity.{k}")
    # approved steps
    need = ["1", "2", "3", "4", "5", "6", "6.5", "7", "8"]
    if state_path:
        try:
            with open(state_path, encoding="utf-8") as fh:
                S = json.load(fh)["steps"]
            bad = [s for s in need if S[s]["status"] != "approved"]
        except (OSError, ValueError, KeyError) as e:
            bad, _ = [f"state unreadable: {e}"], None
    else:
        have = set(b.get("provenance", {}).get("steps_approved", []))
        bad = [s for s in need if s not in have]
    if bad:
        add("BLOCK", "NOT_APPROVED", "the ecosystem is built only from approved steps; not approved: " + ", ".join(map(str, bad)))
    h = b.get("history", {})
    if not h.get("sources"):
        add("BLOCK", "NO_SOURCE", "history lists no source documents")
    if len(h.get("paragraphs", [])) < 2 or not h.get("name_origin"):
        add("BLOCK", "TOO_FEW", "history needs 2 or more paragraphs and the origin of the name")
    for k in ("mission", "vision", "positioning", "promise"):
        if not str(b.get("purpose", {}).get(k, "")).strip():
            add("BLOCK", "MISSING_SECTION", f"purpose.{k}")
    pet = b.get("petreos", [])
    if len(pet) < 3 or any(not p.get("origin") for p in pet):
        add("BLOCK", "TOO_FEW", "3 or more pétreos, each with a traceable origin")
    if any(not p.get("visual_translation") for p in pet):
        add("WARN", "NO_PROOF", "a pétreo has no visual translation")
    if not b.get("vetados") or any(not v.get("reason") for v in b.get("vetados", [])):
        add("BLOCK", "TOO_FEW", "vetados need a reason each")
    if len(b.get("concept", {}).get("manifesto", [])) < 3 or not b.get("concept", {}).get("big_idea"):
        add("BLOCK", "TOO_FEW", "concept needs a big idea and 3 or more manifesto lines")
    if not all(b.get("concept", {}).get("formula", {}).get(k) for k in ("icon", "index", "symbol")):
        add("BLOCK", "MISSING_SECTION", "concept.formula needs icon, index and symbol")
    sy = b.get("symbol", {})
    v = sy.get("vertices", [])
    if not (len(v) >= 5 and v[0] == 0 and v[-1] == 0 and all((v[i + 1] - v[i]) * (v[i + 2] - v[i + 1]) < 0 for i in range(len(v) - 2))
            and all(x >= 0 for x in v) and 20 <= sy.get("slope_deg", 0) <= 70 and 0.03 <= sy.get("stroke_ratio", 0) <= 0.15):
        add("BLOCK", "BAD_SYMBOL", "vertices must start and end at 0, alternate up and down, never go negative; slope 20-70 degrees; stroke ratio 0.03-0.15")
    ms = sy.get("min_size", {})
    if not (ms.get("print_mm") and ms.get("screen_px")) or not sy.get("protection_rule"):
        add("BLOCK", "MISSING_SECTION", "symbol needs min_size in mm and px and a protection rule")
    if len(sy.get("misuse", [])) < 6:
        add("BLOCK", "TOO_FEW", "symbol needs 6 or more misuse cases")
    col = b.get("colour", {})
    tokens = set()
    veto = [hue(x)[1] for x in col.get("vetoed_hexes", []) if HEX.match(x) and hue(x)[0] >= 0.04]
    sigla = ident.get("sigla", "")
    for f in col.get("families", []):
        if not HEX.match(f.get("hex", "")):
            add("BLOCK", "BAD_HEX", f"family {f.get('universe_name')}: {f.get('hex')!r}")
            continue
        for st in col.get("steps", []):
            tokens.add(f"{sigla}_{f['universe_name']}_{st}")
        c, hh = hue(f["hex"])
        if c >= 0.04 and any(min(abs(hh - x), 360 - abs(hh - x)) <= VETO_TOL for x in veto):
            add("BLOCK", "VETOED_HUE", f"{f['universe_name']} {f['hex']} is within {VETO_TOL} degrees of a vetoed hue")
    for n in col.get("neutrals", []):
        if not HEX.match(n.get("hex", "")):
            add("BLOCK", "BAD_HEX", f"neutral {n.get('name')}: {n.get('hex')!r}")
        else:
            tokens.add(n["token"])
            c, hh = hue(n["hex"])
            if c >= 0.04 and any(min(abs(hh - x), 360 - abs(hh - x)) <= VETO_TOL for x in veto):
                add("BLOCK", "VETOED_HUE", f"neutral {n['name']} is within {VETO_TOL} degrees of a vetoed hue")
    if not col.get("families") or len(col.get("neutrals", [])) < 2:
        add("BLOCK", "TOO_FEW", "colour needs 1 or more families and 2 or more neutrals")
    for side, items in col.get("ratio", {}).items():
        if sum(p for _, p in items) != 100:
            add("BLOCK", "BAD_REFERENCE", f"colour ratio {side} adds to {sum(p for _, p in items)}, not 100")
        for t, _ in items:
            if t not in tokens:
                add("BLOCK", "BAD_REFERENCE", f"ratio {side} names unknown token {t}")
    for p in col.get("pairs", []):
        for k in ("fg", "bg"):
            if p.get(k) not in tokens:
                add("BLOCK", "BAD_REFERENCE", f"pair names unknown token {p.get(k)}")
    fonts = b.get("typography", {}).get("fonts", [])
    roles = {f.get("role") for f in fonts}
    if not {"headline", "body"} <= roles or any(not all(f.get(k) for k in ("name", "license", "fallback", "usage", "google_family")) for f in fonts):
        add("BLOCK", "TOO_FEW", "typography needs headline and body fonts with name, google_family, license, fallback and usage")
    sc = b.get("typography", {}).get("scale", [])
    if len(sc) < 5 or any(x.get("font_role") not in roles for x in sc):
        add("BLOCK", "BAD_REFERENCE", "type scale needs 5 or more levels, each with a font role that exists")
    el = b.get("elements", {})
    if not el.get("origin_rule") or not el.get("pattern"):
        add("BLOCK", "MISSING_SECTION", "elements need an origin rule and a pattern")
    if len(el.get("pictograms", [])) < 3 or any(p.get("id") not in PICTOS for p in el.get("pictograms", [])):
        add("BLOCK", "UNKNOWN_APP", f"pictograms: 3 or more from {', '.join(sorted(PICTOS))}")
    ph, mo = b.get("photography", {}), b.get("motion", {})
    if len(ph.get("principles", [])) < 3 or len(ph.get("do", [])) < 2 or len(ph.get("dont", [])) < 2:
        add("BLOCK", "TOO_FEW", "photography needs 3 principles, 2 do and 2 dont")
    if len(mo.get("principles", [])) < 3 or not mo.get("logo_animation", {}).get("duration_ms"):
        add("BLOCK", "TOO_FEW", "motion needs 3 principles and a logo animation duration")
    vo = b.get("voice", {})
    tr = vo.get("traits", [])
    if len(tr) < 3 or any(not all(t.get(k) for k in ("name", "is", "is_not", "example_do", "example_dont")) for t in tr):
        add("BLOCK", "TOO_FEW", "voice needs 3 traits, each with is, is_not, example_do and example_dont")
    if len(vo.get("messaging", [])) < 2 or not vo.get("vocabulary", {}).get("use") or not vo.get("vocabulary", {}).get("avoid"):
        add("BLOCK", "TOO_FEW", "voice needs 2 messaging territories and a vocabulary to use and to avoid")
    if any(not m.get("proof") for m in vo.get("messaging", [])):
        add("WARN", "NO_PROOF", "a messaging territory has no proof")
    apps = b.get("applications", [])
    if len(apps) < 4:
        add("BLOCK", "TOO_FEW", "4 or more applications")
    for a in apps:
        if a.get("id") not in APPS:
            add("BLOCK", "UNKNOWN_APP", f"application '{a.get('id')}': the builder draws {', '.join(sorted(APPS))}")
        if not a.get("spec") or len(a.get("rules", [])) < 2:
            add("BLOCK", "TOO_FEW", f"application {a.get('id')} needs a spec and 2 or more rules")
    g = b.get("governance", {})
    if not all(g.get(k) for k in ("owner", "approval_flow", "review_cycle", "contact")):
        add("BLOCK", "MISSING_SECTION", "governance needs owner, approval_flow, review_cycle and contact")
    if len(b.get("faq", [])) < 3 or not b.get("changelog"):
        add("BLOCK", "TOO_FEW", "3 or more FAQ entries and a changelog")
    for s in strings(b):
        if PLACEHOLDER.search(s):
            add("BLOCK", "PLACEHOLDER", f"unfinished marker in: {s[:70]}")
            break
    if b.get("schema") == "brand-source.v2":
        check_v2(b, add, tokens)
    else:
        add("BLOCK", "SOURCE_V1", "brand-source.v1 has no scope, wordmark, lockups, version and background matrices, per-version sizes, production sheets or delivery: upgrade to brand-source.v2")
    if b.get("fictional") and not b.get("_note"):
        add("WARN", "NOT_LABELLED", "marked fictional but carries no _note saying so")
    if not b.get("fictional") and b.get("_note"):
        add("WARN", "NOT_LABELLED", "carries a _note but is not marked fictional")
    return list(dict.fromkeys(out)), present


def main():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Decide whether a brand-source.v1 file may be built into an ecosystem.")
    ap.add_argument("--input", help="brand-source.v1 JSON (see assets/example_serra_fina_brand.json)")
    ap.add_argument("--state", help="brand-state.json: verify steps 1-8 are approved there")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--output", choices=["human", "json"], default="human")
    a = ap.parse_args()
    path = os.path.join(here, "..", "assets", "example_serra_fina_brand.json") if a.sample else a.input
    if not path:
        ap.error("provide --input or --sample")
    try:
        with open(path, encoding="utf-8") as fh:
            b = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if b.get("schema") not in ("brand-source.v1", "brand-source.v2"):
        print("error: schema must be brand-source.v1 or brand-source.v2", file=sys.stderr)
        sys.exit(1)
    f, present = check(b, a.state)
    if len(present) < len(SECTIONS) / 2:
        verdict, code = "INSUFFICIENT", 3
    elif any(x[0] == "BLOCK" for x in f):
        verdict, code = "BLOCKED", 4
    elif f:
        verdict, code = "READY_WITH_CAVEATS", 2
    else:
        verdict, code = "READY", 0
    res = {"verdict": verdict, "sections_present": f"{len(present)}/{len(SECTIONS)}", "findings": [{"level": l, "code": c, "message": m} for l, c, m in f]}
    if a.output == "json":
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"Verdict: {verdict}   sections present: {len(present)}/{len(SECTIONS)}")
        for l, c, m in f:
            print(f"  [{l}] {c}: {m}")
    sys.exit(code)


if __name__ == "__main__":
    main()
