#!/usr/bin/env python3
"""physical_spaces.py — supplementary palettes for physical spaces: store, showroom, office.

Screen colour and wall colour are different problems. A wall is lit by a lamp, seen at an angle and measured by how
much light it returns, not by its hex. This tool plans each surface of a space from the brand palette: which token,
how much of the space, what finish, and what light reflectance (LRV) to expect, then checks the plan.

LRV here is estimated from the hex. It is a planning figure. The paint or the material has its own measured LRV
and its own sample. Every surface carries spec.status = pending_match until a physical sample is approved on site,
under the lighting of the space.

Spaces and their share of brand colour (the rest is neutral):
  loja        up to 35%   the brand is the experience
  showroom    up to 20%   the product is the protagonist, the walls recede
  escritorio  up to 25%   the brand is present, never tiring

Rules:
  FLOOR_WALL    WARN  the main wall and the floor differ by less than 30 LRV points (a common accessibility practice,
                      so people with low vision can tell floor from wall)
  CEILING       WARN  the ceiling is under LRV 80: the light has nowhere to bounce
  BRAND_SHARE   WARN  the brand colours cover more of the surfaces than the space allows
  SIGN_CONTRAST WARN  the sign text does not reach 4.5:1 on its fill
  DARK_WALL     WARN  the brand wall has LRV under 10: it absorbs light, so add wall washers or keep it to one wall
  SHARES        BLOCK the surface shares do not add up to 100

Lighting is a recommendation by space and by the warmth of the neutral. Exit: 0 ok | 1 input error | 2 warnings | 4 blocked.
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402

WHITE, INK = "#FFFFFF", "#12161C"
SPEC = {"system": "amostra física", "status": "pending_match", "code": ""}
LIMIT = {"loja": 35, "showroom": 20, "escritorio": 25}


def fam(data, name):
    return next(f for f in data["families"] if f["family"] == name)


def step(f, kind, i):
    return f["base"] if kind == "base" else f["scales"][kind]["steps"][i - 1]


def plans(scales, neutral, p, s, a):
    N = neutral["steps"]
    P, S, A = fam(scales, p), fam(scales, s), fam(scales, a)
    return {
        "loja": ("Loja", [
            ("Parede de fundo", N[1], 35, "fosco", "Deixa o produto e a cor da marca aparecerem.", False),
            ("Parede de marca", step(P, "base", 0), 15, "fosco ou acetinado", "Uma só parede, atrás do ponto de maior atenção.", True),
            ("Teto", N[0], 10, "fosco", "Devolve a luz para o ambiente.", False),
            ("Piso", N[5], 20, "fosco ou acetinado", "Mais escuro que a parede, para ler o espaço.", False),
            ("Mobiliário e gôndolas", step(P, "Shade", 2), 15, "laca fosca ou madeira tingida", "Peso visual da marca sem competir com o produto.", True),
            ("Sinalização e destaques", step(A, "base", 0), 5, "acetinado", "Só onde a pessoa precisa decidir ou achar o caminho.", True)]),
        "showroom": ("Showroom", [
            ("Paredes", N[0], 45, "fosco", "Neutro claro: o produto é o protagonista.", False),
            ("Parede de marca", step(P, "Shade", 2), 10, "fosco", "Uma parede de fundo, nunca em volta do produto.", True),
            ("Teto", N[0], 10, "fosco", "Branco tingido, nunca branco puro.", False),
            ("Piso", N[4], 20, "acetinado", "Neutro médio, sem competir com as cores do produto.", False),
            ("Expositores", N[8], 10, "fosco", "Neutro escuro para destacar o objeto.", False),
            ("Destaques", step(A, "base", 0), 5, "acetinado", "Etiquetas, preços e pontos de chamada.", True)]),
        "escritorio": ("Escritório", [
            ("Paredes", N[1], 47, "fosco", "Neutro claro, confortável para o dia todo.", False),
            ("Parede de marca", step(P, "Tone", 4), 10, "fosco", "Cor calma, uma por andar ou sala.", True),
            ("Teto", N[0], 10, "fosco", "Distribui a luz.", False),
            ("Piso", N[5], 18, "fosco", "Contraste com a parede, sem brilho.", False),
            ("Mobiliário", step(S, "Shade", 1), 10, "laca fosca ou madeira tingida", "Cor secundária, mais funda que a parede.", True),
            ("Destaques", step(A, "base", 0), 5, "acetinado", "Pequenos pontos: almofadas, sinalização, quadros.", True)]),
    }


def lighting(space, temp):
    warm = temp in ("quente", "rosada")
    if space == "loja":
        return {"temperatura": "3000 K" if warm else "3500 K", "irc": "90 ou mais",
                "nota": "Luz que respeita a cor do produto e da marca. Teste cada superfície sob esta luz."}
    if space == "showroom":
        return {"temperatura": "3500 K" if warm else "4000 K", "irc": "90 ou mais",
                "nota": "A cor do produto precisa ser fiel. Evite luz colorida nas paredes."}
    return {"temperatura": "3500 K a 4000 K", "irc": "80 ou mais", "nota": "Luz neutra para trabalho. Evite luz muito fria."}


def build(scales, neutral, p, s, a):
    findings, spaces = [], []
    for key, (label, rows) in plans(scales, neutral, p, s, a).items():
        total = sum(r[2] for r in rows)
        fs = []
        if total != 100:
            fs.append(("BLOCK", "SHARES", f"{label}: shares add up to {total}, not 100."))
        surfaces = []
        brand = 0
        for name, c, share, fin, note, is_brand in rows:
            brand += share if is_brand else 0
            surfaces.append({"surface": name, "token": c["token"], "hex": c["hex"], "share_percent": share,
                             "lrv_estimated": cl.lrv(c["hex"]), "finish": fin, "note": note, "cmyk_approx": c["cmyk_approx"],
                             "spec": dict(SPEC)})
        by = {x["surface"]: x for x in surfaces}
        wall = next(x for n, x in by.items() if n.startswith("Parede") and "marca" not in n or n == "Paredes")
        floor, ceil = by["Piso"], by["Teto"]
        if abs(wall["lrv_estimated"] - floor["lrv_estimated"]) < 30:
            fs.append(("WARN", "FLOOR_WALL", f"{label}: wall and floor differ by under 30 LRV points."))
        if ceil["lrv_estimated"] < 80:
            fs.append(("WARN", "CEILING", f"{label}: ceiling LRV {ceil['lrv_estimated']} is under 80."))
        for x in surfaces:
            if x["surface"].startswith("Parede de marca") and x["lrv_estimated"] < 10:
                fs.append(("WARN", "DARK_WALL", f"{label}: the brand wall has LRV {x['lrv_estimated']}. A very dark wall absorbs light: add wall washers or keep it to one wall."))
        if brand > LIMIT[key]:
            fs.append(("WARN", "BRAND_SHARE", f"{label}: brand colours cover {brand}% of the surfaces, the limit is {LIMIT[key]}%."))
        sign = by.get("Sinalização e destaques") or by.get("Destaques")
        lab = WHITE if cl.contrast(WHITE, sign["hex"]) >= cl.contrast(INK, sign["hex"]) else INK
        sign["text_on_it"] = {"hex": lab, "contrast": round(cl.contrast(lab, sign["hex"]), 2)}
        if sign["text_on_it"]["contrast"] < 4.5:
            fs.append(("WARN", "SIGN_CONTRAST", f"{label}: sign text on {sign['hex']} stays under 4.5:1."))
        spaces.append({"id": key, "label": label, "brand_share_percent": brand, "brand_share_limit": LIMIT[key],
                       "lighting": lighting(key, neutral["temperature"]), "surfaces": surfaces,
                       "findings": [{"level": x, "code": y, "message": z} for x, y, z in fs]})
        findings += fs
    verdict = "BLOCKED" if any(f[0] == "BLOCK" for f in findings) else ("CAVEATS" if findings else "CLEAN")
    return {"sigla": neutral["sigla"], "spaces": spaces,
            "rules": ["A tinta e o material reais têm LRV medido no catálogo. O LRV daqui é estimativa de planejamento.",
                      "Aprove cada superfície por amostra física, no local, sob a iluminação do espaço. Cada uma está como pending_match.",
                      "Acabamento fosco em paredes grandes evita reflexos que mudam a cor ao longo do dia.",
                      "Uma única parede de marca por ambiente. Duas disputam a atenção."],
            "findings": [{"level": x, "code": y, "message": z} for x, y, z in findings],
            "verdict": verdict, "note": "CMYK values are approximate. PMS needs a printed match."}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scales", required=True, help="output of tonal_scales.py")
    ap.add_argument("--neutral", required=True, help="output of neutral_scale.py")
    ap.add_argument("--primary", required=True)
    ap.add_argument("--secondary", required=True)
    ap.add_argument("--accent", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        with open(a.scales, encoding="utf-8") as f:
            scales = json.load(f)
        with open(a.neutral, encoding="utf-8") as f:
            neutral = json.load(f)
        res = build(scales, neutral, a.primary, a.secondary, a.accent)
    except (OSError, ValueError, KeyError, StopIteration) as e:
        print(f"error: {e!r}", file=sys.stderr)
        return 1
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)
    return {"BLOCKED": 4, "CAVEATS": 2, "CLEAN": 0}[res["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
