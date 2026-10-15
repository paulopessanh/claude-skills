#!/usr/bin/env python3
"""ecosystem_builder.py — builds the complete brand ecosystem from one source file.

Input is brand-source.v1: the story, purpose, pétreos, concept, symbol parameters, colour, typography, elements, photography,
motion, voice, applications, governance, FAQ and changelog of an approved brand. Output is a folder:

  brandbook/   the brandbook, one HTML page with every chapter (history, purpose, concept, form, colour, type, voice ...)
  logo/        symbol, wordmark, horizontal, vertical and seal in three polarities, the animated symbol, the site icon
  elements/    contour pattern (light, dark), divider, six pictograms, colour sheet
  applications/ pack label, card (front, back), social post, site home, gift box lid, letterhead
  tokens/      CSS and JSON tokens, and the guidelines spec the completeness check reads
  voice/       voice and messaging guide
  source/      the brand-source.v1 file the package was built from
  MANIFEST.json, README.md   every file with its role, size and SHA-256

Refusals (exit 4): the source check blocks (a step not approved, a missing layer, a vetoed hue ...). Nothing is built from a
source that ecosystem_source_check.py refuses. The logo files are a geometric study generated from parameters, for the team
to refine in vector; their text uses live fonts and must be converted to outlines before print. CMYK is approximate.

Exit codes: 0 BUILT | 1 input error | 3 INSUFFICIENT source | 4 REFUSED by the source check
Stdlib only. No network. Deterministic: the same source gives the same bytes.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _ecoassets as A      # noqa: E402
import _ecobook as BK       # noqa: E402
import ecosystem_source_check as SC   # noqa: E402
from _ecolib import tokens, file_stem, hex_rgb, cmyk_approx, contrast   # noqa: E402


def guidelines_spec(b, flat):
    col = b["colour"]
    sy = b["symbol"]
    toks = [{"token": k, "hex": v, "rgb": list(hex_rgb(v)), "cmyk": cmyk_approx(v), "cmyk_status": "approx"} for k, v in flat.items()]
    ratio = {side: ", ".join(f"{t} {p}%" for t, p in items) for side, items in col["ratio"].items()}
    return {
        "brand": b["identity"]["name"],
        "logo": {"versions": ["horizontal", "vertical", "symbol", "wordmark", "seal"], "polarities": ["positive", "negative", "mono"],
                 "protection_area": {"rule": sy["protection_rule"], "relative_to": "symbol"}, "min_size": sy["min_size"],
                 "misuse": [m for m in sy["misuse"]]},
        "colour": {"tokens": toks, "ratio": ratio,
                   "pairs": [{"fg": b_hex(flat, p["fg"]), "bg": b_hex(flat, p["bg"]), "declared": p["declared"]} for p in col["pairs"]]},
        "typography": {"fonts": [{k: f[k] for k in ("role", "name", "license", "fallback")} for f in b["typography"]["fonts"]],
                       "scale": b["typography"]["scale"]},
        "graphic_elements": {"origin_rule": b["elements"]["origin_rule"]},
        "voice": {"traits": [{"name": t["name"], "is": t["is"], "is_not": t["is_not"]} for t in b["voice"]["traits"]]},
        "applications": [a["name"] for a in b["applications"]],
    }


def b_hex(flat, token):
    return flat[token]


def voice_md(b):
    v, ident = b["voice"], b["identity"]
    L = [f"# Voz e mensagens da {ident['name']}", "", f"Versão {ident['version']}, {ident['date']}.", "",
         "## Posicionamento", "", b["purpose"]["positioning"], "", "## Manifesto", ""]
    L += [f"{x}" for x in b["concept"]["manifesto"]]
    L += ["", "## Traços de voz", ""]
    for t in v["traits"]:
        L += [f"### {t['name']}", "", f"- É: {t['is']}", f"- Não é: {t['is_not']}", f"- Assim: {t['example_do']}", f"- Assim não: {t['example_dont']}", ""]
    L += ["## Mensagens por território", ""]
    for m in v["messaging"]:
        L += [f"- {m['territory']}: {m['message']} Prova: {m['proof']}"]
    L += ["", "## Vocabulário", "", "Use: " + ", ".join(v["vocabulary"]["use"]) + ".", "", "Evite: " + ", ".join(v["vocabulary"]["avoid"]) + ".", "", "## Tom por canal", ""]
    L += [f"- {m['channel']}: {m['tone']}" for m in v["tone_by_channel"]]
    return "\n".join(L) + "\n"


def readme(b, files):
    ident = b["identity"]
    note = "Marca fictícia criada para o teste do processo. Nenhum texto ou número descreve uma empresa real.\n\n" if b.get("fictional") else ""
    rows = "\n".join(f"- `{p}`: {r}" for p, r in files)
    return (f"# Ecossistema da marca {ident['name']}\n\nVersão {ident['version']}, {ident['date']}.\n\n{note}"
            "Abra `brandbook/` primeiro. Ele reúne história, propósito, conceito, forma, cor, tipografia, elementos, fotografia, movimento, voz, aplicações, tokens e governança.\n\n"
            "## O que está aqui\n\n" + rows + "\n\n## Antes de entregar\n\n"
            "- Os arquivos de logo são um estudo geométrico gerado por parâmetros. O time de criação refina e finaliza em vetor.\n"
            "- O texto das assinaturas usa fonte viva. Converta em curvas antes da gráfica.\n"
            "- O CMYK é aproximado. Os valores de impressão saem de um perfil ICC e de uma prova.\n"
            "- Confirme a licença e o arquivo de cada fonte.\n"
            "- Rode `ecosystem_auditor.py` depois de qualquer edição para conferir cores, contraste, nomes e textos.\n")


def build(src_path, out, state=None, fragment=None):
    with open(src_path, encoding="utf-8") as fh:
        b = json.load(fh)
    if b.get("schema") != "brand-source.v1":
        print("error: schema must be brand-source.v1", file=sys.stderr)
        return 1
    findings, present = SC.check(b, state)
    blocks = [f for f in findings if f[0] == "BLOCK"]
    if len(present) < len(SC.SECTIONS) / 2:
        print(f"INSUFFICIENT: the source has {len(present)} of {len(SC.SECTIONS)} sections. Nothing was built.")
        return 3
    if blocks:
        print("REFUSED by the source check. Nothing was built:")
        for l, c, m in blocks:
            print(f"  [{l}] {c}: {m}")
        return 4
    flat, fams = tokens(b)
    c = A.Ctx(b, flat, fams)
    S = lambda n, ext="svg": file_stem(b, n) + "." + ext
    svgs, files = {}, []

    def put(folder, name, content, role, ext="svg", key=None):
        rel = f"{folder}/{S(name, ext)}"
        full = os.path.join(out, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        files.append((rel, role))
        if ext == "svg":
            svgs[key or name] = content

    for pol in ("positive", "negative", "mono"):
        P = pol.capitalize()
        put("logo", f"Symbol-{P}", A.symbol_svg(c, pol), f"Símbolo, versão {pol}")
        put("logo", f"Horizontal-{P}", A.lockup_svg(c, pol, "horizontal"), f"Assinatura horizontal, versão {pol}")
        put("logo", f"Vertical-{P}", A.lockup_svg(c, pol, "vertical"), f"Assinatura vertical, versão {pol}")
        put("logo", f"Seal-{P}", A.seal_svg(c, pol), f"Selo, versão {pol}")
        put("logo", f"Wordmark-{P}", A.wordmark_svg(c, pol), f"Nome, versão {pol}")
    put("logo", "Symbol-Animated", A.animated_svg(c), "Símbolo animado (respeita menos movimento)")
    put("logo", "Favicon", A.favicon_svg(c), "Ícone do site")
    put("elements", "Pattern-Light", A.pattern_svg(c, False), "Padrão de linhas de nível, claro")
    put("elements", "Pattern-Dark", A.pattern_svg(c, True), "Padrão de linhas de nível, escuro")
    put("elements", "Divider", A.divider_svg(c), "Divisor")
    for pc in b["elements"]["pictograms"]:
        put("elements", f"Pictogram-{pc['id'].capitalize()}", A.picto_svg(c, pc["id"], pc["name"]), f"Pictograma {pc['name']}")
    put("elements", "Palette", A.palette_svg(c), "Folha de paleta com tokens e HEX")
    for ap in b["applications"]:
        for nm, fn in A.APP_FILES[ap["id"]]:
            put("applications", nm, fn(c), f"Aplicação: {ap['name']}")
    put("tokens", "Tokens", json.dumps({"brand": b["identity"]["name"], "version": b["identity"]["version"], "colour": flat}, indent=2, ensure_ascii=False) + "\n",
        "Tokens de cor em JSON", "json")
    css_t = ":root {\n" + "\n".join(f"  --{k.lower().replace('_', '-')}: {v};" for k, v in flat.items()) + "\n}\n"
    put("tokens", "Tokens", css_t, "Tokens de cor em CSS", "css")
    put("tokens", "Guidelines-Spec", json.dumps(guidelines_spec(b, flat), indent=2, ensure_ascii=False) + "\n", "Especificação das guidelines (para a checagem de completude)", "json")
    put("voice", "Voz-e-Mensagens", voice_md(b), "Guia de voz e mensagens", "md")
    put("source", "Source", json.dumps(b, indent=2, ensure_ascii=False) + "\n", "A fonte única da qual tudo foi gerado", "json")
    book_rel = f"brandbook/{S('Brandbook', 'html')}"
    listing = files + [(book_rel, "O manual da marca, uma página"), ("MANIFEST.json", "Cada arquivo com função, tamanho e SHA-256"), ("README.md", "Como abrir e o que conferir antes de entregar")]
    page = BK.build(b, flat, fams, c, svgs, listing, standalone=True)
    os.makedirs(os.path.join(out, "brandbook"), exist_ok=True)
    with open(os.path.join(out, book_rel), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    files.append((book_rel, "O manual da marca, uma página"))
    if fragment:
        with open(fragment, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(BK.build(b, flat, fams, c, svgs, listing, standalone=False))
    with open(os.path.join(out, "README.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(readme(b, listing))
    files.append(("README.md", "Como abrir e o que conferir antes de entregar"))
    manifest = []
    for rel, role in sorted(files):
        data = open(os.path.join(out, rel), "rb").read()
        manifest.append({"path": rel, "role": role, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    with open(os.path.join(out, "MANIFEST.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"brand": b["identity"]["name"], "version": b["identity"]["version"], "built_from": "source/",
                   "geometric_study": True, "files": manifest}, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    warns = [f for f in findings if f[0] == "WARN"]
    print(f"BUILT {len(manifest) + 1} files into {out}")
    for l, cd, m in warns:
        print(f"  [{l}] {cd}: {m}")
    print(f"  brandbook: {book_rel}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Build the complete brand ecosystem from a brand-source.v1 file.")
    ap.add_argument("--source", help="brand-source.v1 JSON (see assets/example_serra_fina_brand.json)")
    ap.add_argument("--out", help="output folder (created; existing files with the same names are replaced)")
    ap.add_argument("--state", help="brand-state.json: steps 1-8 must be approved there")
    ap.add_argument("--artifact-fragment", help="also write the brandbook as a page fragment for the Artifact tool")
    ap.add_argument("--sample", action="store_true", help="build the example into a temporary folder and list it")
    a = ap.parse_args()
    if a.sample:
        src = os.path.join(HERE, "..", "assets", "example_serra_fina_brand.json")
        out = tempfile.mkdtemp(prefix="eco-sample-")
        rc = build(src, out)
        if rc == 0:
            n = sum(len(f) for _, _, f in os.walk(out))
            print(f"  sample folder (removed on exit): {n} files")
        shutil.rmtree(out, ignore_errors=True)
        return rc
    if not a.source or not a.out:
        ap.error("provide --source and --out, or --sample")
    try:
        return build(a.source, a.out, a.state, a.artifact_fragment)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
