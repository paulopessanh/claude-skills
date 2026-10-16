#!/usr/bin/env python3
"""prohibitions.py — the prohibition palette: what lives outside the brand, with examples nobody can misread.

A rule that says "do not use dirty colours" starts an argument. A card that shows the dirty colour, its hex and the
reason ends it. This tool builds the prohibitions from the palette itself, so every example is a real colour that a
real team could pick by mistake:

  P01  near-miss colours      a tone that looks like a brand colour and is not
  P02  client vetoes          hues and hexes the client refused
  P03  pairs that look fine   brand colours that sit on each other under 3:1 but look separate on a good screen
  P04  pairs that vibrate     saturated colours of far hues at the same lightness
  P05  muddy gradients        pairs whose straight RGB mix loses chroma in the middle
  P06  pure black and white   #000000 and #FFFFFF where the brand has tinted ones
  P07  grey without a hue     the grey that does not belong to the family
  P08  status as brand        status colours used as brand colours, and brand colours that read as a status
  P09  colour alone           a meaning carried by colour only
  P10  too many colours       more than three families in one piece
  P11  a recoloured mark      the mark in a colour that is not on the list
  P12  rainbow gradients      gradients with a hue arc above 90 degrees
  P13  black shadows          pure black shadows on a coloured surface

Each item has a severity: BLOCK (never ships), ALERT (needs written approval), GUIDE (a default).
Items that depend on the palette and find nothing say so: 'none in this palette'. Exit: 0 | 1 input error.
Stdlib only. No network. Deterministic.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _colorlib as cl  # noqa: E402


def sw(hexes, caption):
    return {"kind": "swatch", "hexes": hexes, "caption": caption}


def pair(fg, bg, caption):
    return {"kind": "pair", "fg": fg, "bg": bg, "ratio": int(cl.contrast(fg, bg) * 100) / 100, "caption": caption}


def grad(a, b, caption):
    return {"kind": "gradient", "hexes": [a, b], "caption": caption}


def naive_ratio(a, b, n=33):
    ca, cb = cl.oklch(a)[1], cl.oklch(b)[1]
    weak = min(ca, cb)
    if weak < 0.03:
        return None
    return min(cl.oklch(cl.lerp_srgb(a, b, i / (n - 1)))[1] for i in range(n)) / weak


def build(scales, neutral, status, vetoed, sigla, allow_white):
    fams = scales["families"]
    bases = [(f["family"], f["base"]) for f in fams]
    items = []

    def add(pid, title, severity, rule, why, examples, scope=("digital", "impressão")):
        items.append({"id": pid, "title": title, "severity": severity, "rule": rule, "why": why,
                      "examples": examples, "scope": list(scope)})

    # P01 near-miss
    ex = []
    for name, b in bases:
        L, C, h = cl.oklch(b["hex"])
        for tag, (dl, dc, dh) in (("mais claro", (0.03, 1.0, 0)), ("menos saturado", (0, 0.88, 0)), ("matiz deslocado", (0, 1.0, 7))):
            hx = cl.oklch_to_hex(L + dl, C * dc, (h + dh) % 360)
            ex.append(sw([b["hex"], hx], f"{name}: o oficial e um {tag} ({hx}, distância {cl.oklab_dist(b['hex'], hx):.3f}). O segundo está errado."))
    add("P01", "Cor quase igual à da marca", "BLOCK",
        "Só entram os hex dos tokens. Nada de ajustar a olho, de pegar o conta-gotas de uma foto ou de 'clarear um pouco'.",
        "O olho não vê a diferença e a marca vira três marcas. Em impressão o desvio aparece lado a lado.", ex[:6])

    # P02 vetoes
    if vetoed:
        add("P02", "Vetos do cliente", "BLOCK",
            "Estas cores e as vizinhas de matiz estão fora do universo da marca, em qualquer peça.",
            "O cliente recusou. Reabrir exige nova decisão por escrito.",
            [sw([cl.norm_hex(v)], f"{cl.norm_hex(v)} vetado.") for v in vetoed])
    else:
        add("P02", "Vetos do cliente", "BLOCK", "Nenhum veto registrado. Pergunte ao cliente antes de fechar o manual.",
            "Um veto descoberto depois do lançamento custa a peça.", [])

    # P03 deceptive pairs
    cands = [(f"{n}", b["hex"], b["token"]) for n, b in bases]
    for f in fams:
        for i, s in enumerate(f["scales"]["Tint"]["steps"][:2]):
            cands.append((f"{f['family']} Tint{i + 1}", s["hex"], s["token"]))
        cands.append((f"{f['family']} Shade1", f["scales"]["Shade"]["steps"][0]["hex"], f["scales"]["Shade"]["steps"][0]["token"]))
    for st in neutral["steps"][3:7]:
        cands.append((st["token"].split("_")[-1], st["hex"], st["token"]))
    bad = []
    for na, ha, _ in cands:
        for nb, hb, _ in cands:
            if ha < hb:
                r = cl.contrast(ha, hb)
                if 1.5 <= r < 3.0 and cl.oklab_dist(ha, hb) > 0.08:
                    bad.append((r, na, ha, nb, hb))
    bad.sort(reverse=True)
    add("P03", "Pares que parecem separados e não passam", "BLOCK",
        "Texto, ícone ou traço entre duas cores com menos de 3:1 não entra. Confira o par na tabela de regras de uso.",
        "Em uma tela boa parece legível. Em sol, em tela barata e para quem tem baixa visão, some.",
        [pair(h1, h2, f"{n1} sobre {n2}: {int(cl.contrast(h1, h2) * 100) / 100}:1.") for _, n1, h1, n2, h2 in bad[:6]]
        or [])
    # P04 vibration
    vib = []
    allc = [(n, b["hex"]) for n, b in bases] + [(f["family"] + " Tint3", f["scales"]["Tint"]["steps"][2]["hex"]) for f in fams] \
        + [(f["family"] + " Shade2", f["scales"]["Shade"]["steps"][1]["hex"]) for f in fams]
    for i, (na, ha) in enumerate(allc):
        for nb, hb in allc[i + 1:]:
            La, Ca, ha_ = cl.oklch(ha)
            Lb, Cb, hb_ = cl.oklch(hb)
            if Ca > 0.10 and Cb > 0.10 and cl.hue_gap(ha_, hb_) > 110 and abs(La - Lb) < 0.15:
                vib.append((na, ha, nb, hb))
    add("P04", "Cores que vibram juntas", "ALERT",
        "Duas cores saturadas de matizes opostos e luminosidade parecida não ficam coladas. Separe com neutro ou mude a luminosidade.",
        "A borda entre elas pisca e cansa a leitura.",
        [pair(h1, h2, f"{n1} ao lado de {n2}.") for n1, h1, n2, h2 in vib[:4]]
        or [sw([], "Nenhum par da paleta atual vibra. A regra vale para novas cores.")])
    # P05 muddy gradients
    mud = []
    for i, (na, ba) in enumerate(bases):
        for nb, bb in bases[i + 1:]:
            r = naive_ratio(ba["hex"], bb["hex"])
            if r is not None and r < 0.6:
                mud.append((r, na, ba["hex"], nb, bb["hex"]))
    mud.sort()
    add("P05", "Degradê com meio sujo (grey limbo)", "BLOCK",
        "Não misture duas famílias por mistura direta de RGB. Use o gradient_builder: ele mede o croma das 33 amostras.",
        "A mistura direta perde a cor no meio e fica cinza ou lama.",
        [grad(h1, h2, f"{n1} para {n2} em RGB direto mantém só {r:.0%} do croma.") for r, n1, h1, n2, h2 in mud[:4]]
        or [sw([], "Nenhum par de famílias desta paleta suja em RGB direto. A regra continua valendo para novas cores.")])
    # P06 pure black / white
    ink = neutral["roles"]["light"]["text_strong"]
    exs = [sw(["#000000", ink["hex"]], f"Preto puro #000000 no lugar do {ink['token']} ({ink['hex']}). O primeiro está errado.")]
    if not allow_white:
        wt = neutral["roles"]["light"]["surface"]
        exs.append(sw(["#FFFFFF", wt["hex"]], f"Branco puro no lugar do {wt['token']} ({wt['hex']}). O primeiro está errado."))
    add("P06", "Preto e branco puros", "ALERT",
        "Texto e fundos usam os neutros tingidos da marca. Preto puro #000000 não entra. " + ("Branco puro só onde o papel já é branco." if allow_white else "Branco puro #FFFFFF não entra."),
        "Preto e branco puros destoam do resto da paleta e em offset o preto puro sai lavado.", exs)
    # P07 untinted grey
    ug = neutral["untinted_example"]
    add("P07", "Cinza sem matiz", "ALERT",
        "Todo cinza vem da escala de neutros da marca. Cinza de editor, cinza de sistema e cinza de foto não entram.",
        "Ao lado de uma cor de marca, o cinza sem matiz parece sujo e de outra marca.",
        [sw([ug["hex"], neutral["steps"][5]["hex"]],
            f"{ug['hex']} (sem matiz) contra {neutral['steps'][5]['token']} ({neutral['steps'][5]['hex']}), distância "
            f"{cl.oklab_dist(ug['hex'], neutral['steps'][5]['hex']):.3f}. A diferença é pequena de propósito: por isso decide o hex, não o olho. O primeiro está errado.")])
    # P08 status vs brand
    exs = []
    if status:
        for k in ("positive", "negative", "warning", "info"):
            exs.append(sw([status["statuses"][k]["strong"]["hex"]], f"{status['statuses'][k]['label']}: só para estado, nunca para a marca."))
        for f in status["findings"]:
            if f["code"] == "BRAND_CLASH":
                exs.append(sw([], f["message"]))
    add("P08", "Cor de status como cor de marca, e o contrário", "BLOCK",
        "Verde, vermelho, âmbar e azul de status não colorem logo, botão primário, decoração ou gradiente. Cor de marca parecida com um status não sinaliza estado.",
        "Quando a marca usa vermelho de erro como acento, o botão parece um alerta.", exs)
    # P09, P10, P11, P12, P13
    add("P09", "Cor como única informação", "BLOCK",
        "Todo significado de cor tem também ícone, forma, texto ou posição.",
        "Cerca de 1 em cada 12 homens tem alguma diferença na visão de cor, e a impressão em preto e branco apaga a cor.",
        [sw([], "Um indicador 'bom' e um 'ruim' só em verde e vermelho, sem ícone nem palavra.")])
    add("P10", "Cores demais na mesma peça", "ALERT",
        "No máximo três famílias da paleta, mais os neutros. O acento ocupa até 10% da área.",
        "A marca é reconhecida pela contenção. Mais famílias diluem.",
        [sw([b["hex"] for _, b in bases] + ["#8E44AD", "#F39C12"], "As três famílias da marca e duas cores de fora. As duas últimas estão erradas.")])
    add("P11", "Marca recolorida", "BLOCK",
        "A marca só aparece nas versões do manual: cor base da principal, versão clara da principal, branco tingido e a versão em um tom.",
        "Uma marca recolorida é outra marca, e o cliente deixa de reconhecê-la.",
        [sw([bases[0][1]["hex"], bases[-1][1]["hex"]], f"A marca na cor {bases[-1][0]} ({bases[-1][1]['hex']}) é recolorir. O segundo está errado.")])
    wide = []
    for i, (na, ba) in enumerate(bases):
        for nb, bb in bases[i + 1:]:
            gap = cl.hue_gap(cl.oklch(ba["hex"])[2], cl.oklch(bb["hex"])[2])
            if gap > 90 and min(cl.oklch(ba["hex"])[1], cl.oklch(bb["hex"])[1]) >= 0.03:
                wide.append((gap, na, ba["hex"], nb, bb["hex"]))
    wide.sort(reverse=True)
    add("P12", "Degradê arco-íris", "ALERT",
        "O degradê vai da cor principal para uma só outra família, com arco de matiz até 90 graus. Acima disso, vira arco-íris.",
        "Muitos matizes no mesmo degradê parecem outro produto.",
        [grad(h1, h2, f"{n1} para {n2}: arco de {g:.0f} graus.") for g, n1, h1, n2, h2 in wide[:3]]
        or [sw([], "Nenhum par da paleta passa de 90 graus.")])
    add("P13", "Sombra preta pura", "GUIDE",
        "Sombra sobre cor usa um shade da própria cor, com opacidade, nunca preto puro.",
        "O preto puro suja o fundo colorido e quebra a harmonia.",
        [sw(["#000000", bases[0][1]["hex"]], f"Sombra #000000 sobre {bases[0][0]}. Use {fams[0]['scales']['Shade']['steps'][2]['token']} ({fams[0]['scales']['Shade']['steps'][2]['hex']}) com 30 a 50% de opacidade.")])
    return {"sigla": sigla, "items": items, "count": len(items),
            "how_to_use": "Cada item é um cartão: regra, motivo e exemplos reais. Mostre os exemplos errados ao time e ao terceirizado.",
            "note": "Examples are generated from the palette. A new colour needs a new run."}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scales", required=True)
    ap.add_argument("--neutral", required=True)
    ap.add_argument("--status", help="output of restricted_palette.py")
    ap.add_argument("--vetoed", nargs="*", default=[])
    ap.add_argument("--allow-white", action="store_true", help="the brand allows pure white on paper")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        with open(a.scales, encoding="utf-8") as f:
            scales = json.load(f)
        with open(a.neutral, encoding="utf-8") as f:
            neutral = json.load(f)
        status = None
        if a.status:
            with open(a.status, encoding="utf-8") as f:
                status = json.load(f)
        res = build(scales, neutral, status, a.vetoed, scales["brand"]["sigla"], a.allow_white)
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e!r}", file=sys.stderr)
        return 1
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
