#!/usr/bin/env python3
"""_ecolib.py — shared maths of the brand ecosystem: colour, symbol geometry, tokens, file names.

Imported by ecosystem_builder.py and ecosystem_auditor.py so that the two can never disagree about a colour, a token
name or a file name. It is a library, not a command: running it only prints this text.

Colour: sRGB <-> OKLab (Bjorn Ottosson, 2020), WCAG 2.1 contrast, gamut-safe lightness ramps, an approximate CMYK.
Geometry: the ridge symbol. Vertices are fractions of the tallest peak, x follows from one constant slope angle.
Tokens: {SIGLA}_{Universe}_{step} for each family, plus the named neutrals.
Names: {SIGLA}_{Name}_V{NN}_{DDMMAA}.{ext}

Stdlib only. No network. Deterministic.
"""

import math
import re
import sys

HEXRE = re.compile(r"^#[0-9a-fA-F]{6}$")
VETO_TOL = 25     # degrees of OKLCH hue; the same tolerance as color_system_builder.py and competitor_matrix.py
CHROMA_MIN = 0.04


# ---------------------------------------------------------------- colour
def hex_rgb(h):
    if not HEXRE.match(str(h).strip()):
        raise ValueError(f"bad hex colour: {h!r}")
    v = h.strip().lstrip("#")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _delin(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def oklab(h):
    r, g, b = (_lin(c / 255.0) for c in hex_rgb(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def oklch(h):
    L, a, b = oklab(h)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def _from_oklab(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def _in_gamut(lrgb):
    return all(-1e-6 <= c <= 1 + 1e-6 for c in lrgb)


def oklch_to_hex(L, C, h):
    a, b = math.cos(math.radians(h)), math.sin(math.radians(h))
    if not _in_gamut(_from_oklab(L, C * a, C * b)):
        lo, hi = 0.0, C
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if _in_gamut(_from_oklab(L, mid * a, mid * b)) else (lo, mid)
        C = lo
    return rgb_hex([_delin(min(1, max(0, c))) * 255 for c in _from_oklab(L, C * a, C * b)])


def luminance(h):
    r, g, b = (_lin(c / 255.0) for c in hex_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(h1, h2):
    a, b = sorted((luminance(h1), luminance(h2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def cmyk_approx(h):
    r, g, b = (c / 255.0 for c in hex_rgb(h))
    k = 1 - max(r, g, b)
    if k >= 1:
        return [0, 0, 0, 100]
    return [round(100 * v) for v in ((1 - r - k) / (1 - k), (1 - g - k) / (1 - k), (1 - b - k) / (1 - k), k)]


def hue_gap(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def ramp(base_hex, steps):
    """{step: hex}. Step 50 is the base itself; lighter steps rise toward L 0.97, darker ones fall toward L 0.18."""
    L0, C0, h = oklch(base_hex)
    out = {}
    for s in steps:
        if s == 50:
            out[s] = "#" + base_hex.lstrip("#").upper()
        elif s < 50:
            t = (50 - s) / 40.0
            out[s] = oklch_to_hex(L0 + (0.97 - L0) * t, C0 * (0.15 + 0.85 * (1 - t)), h)
        else:
            frac = min(1.0, (s - 50) / 25.0)
            out[s] = oklch_to_hex(L0 - (L0 - 0.18) * frac if L0 > 0.18 else L0, C0 * (1 - 0.35 * frac), h)
    return out


def tokens(b):
    """Flat {token: hex} for every family step and neutral, plus metadata for the brandbook."""
    sig = b["identity"]["sigla"]
    col = b["colour"]
    flat, fam_meta = {}, []
    for f in col["families"]:
        r = ramp(f["hex"], col["steps"])
        fam_meta.append({"universe": f["universe_name"], "pt_name": f["pt_name"], "base": f["hex"].upper(), "role": f.get("role", ""),
                         "meaning": f.get("meaning", ""), "steps": {s: {"token": f"{sig}_{f['universe_name']}_{s}", "hex": h} for s, h in r.items()}})
        for s, h in r.items():
            flat[f"{sig}_{f['universe_name']}_{s}"] = h
    for n in col["neutrals"]:
        flat[n["token"]] = n["hex"].upper()
    return flat, fam_meta


# ---------------------------------------------------------------- geometry
def ridge_points(vertices, slope_deg, hmax=100.0):
    """Points (x, y) with y measured UP from the baseline, x from one constant slope angle."""
    t = math.tan(math.radians(slope_deg))
    pts, x = [(0.0, 0.0)], 0.0
    for i in range(1, len(vertices)):
        dy = (vertices[i] - vertices[i - 1]) * hmax
        x += abs(dy) / t
        pts.append((x, vertices[i] * hmax))
    return pts


def polyline(pts, hmax, ox=0.0, oy=0.0, sc=1.0):
    return " ".join(f"{ox + x * sc:.2f},{oy + (hmax - y) * sc:.2f}" for x, y in pts)


def polyline_length(pts, sc=1.0):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) * sc


# ---------------------------------------------------------------- names
def file_stem(b, name):
    ident = b["identity"]
    major = int(str(ident["version"]).split(".")[0])
    y, m, d = ident["date"].split("-")
    return f"{ident['sigla']}_{name}_V{major:02d}_{d}{m}{y[2:]}"


NAME_RE = r"^[A-Z]{2,5}_[A-Za-z0-9\-]+_V\d{2}_\d{6}\.[a-z0-9]+$"

if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
