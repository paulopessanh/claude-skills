"""_colorlib.py — colour maths for brand-color. Stdlib only, no network, deterministic.

Spaces: sRGB hex, HSL, OKLab/OKLCH. Gamut mapping keeps lightness and hue and lowers chroma until
the colour fits sRGB. Contrast: WCAG 2.x ratio and APCA Lc (W3 0.0.98G).
CMYK here is a naive conversion and always approximate. PMS (Pantone) cannot be computed:
it needs the licensed library and a printed match, so callers must carry it as pending_match.
"""

import math
import re

HEXRE = re.compile(r"^#?[0-9a-fA-F]{6}$")


def norm_hex(h):
    if not HEXRE.match(str(h).strip()):
        raise ValueError(f"bad hex colour: {h!r}")
    return "#" + str(h).strip().lstrip("#").upper()


def hex_rgb(h):
    v = norm_hex(h).lstrip("#")
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


def fit_chroma(L, C, h):
    """Largest chroma <= C that fits sRGB at this lightness and hue."""
    a, b = math.cos(math.radians(h)), math.sin(math.radians(h))
    if _in_gamut(_from_oklab(L, C * a, C * b)):
        return C
    lo, hi = 0.0, C
    for _ in range(32):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _in_gamut(_from_oklab(L, mid * a, mid * b)) else (lo, mid)
    return lo


def oklch_to_hex(L, C, h):
    L = max(0.0, min(1.0, L))
    C = fit_chroma(L, max(0.0, C), h)
    a, b = math.cos(math.radians(h)), math.sin(math.radians(h))
    return rgb_hex([_delin(min(1, max(0, c))) * 255 for c in _from_oklab(L, C * a, C * b)])


def max_chroma(L, h):
    return fit_chroma(L, 0.5, h)


def hsl(h):
    r, g, b = (c / 255.0 for c in hex_rgb(h))
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, round(l * 100, 1)
    d = mx - mn
    s = d / (1 - abs(2 * l - 1))
    if mx == r:
        hh = ((g - b) / d) % 6
    elif mx == g:
        hh = (b - r) / d + 2
    else:
        hh = (r - g) / d + 4
    return round(hh * 60 % 360, 1), round(s * 100, 1), round(l * 100, 1)


def luminance(h):
    r, g, b = (_lin(c / 255.0) for c in hex_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(h1, h2):
    a, b = sorted((luminance(h1), luminance(h2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def _apca_y(h):
    r, g, b = (c / 255.0 for c in hex_rgb(h))
    y = 0.2126729 * r ** 2.4 + 0.7151522 * g ** 2.4 + 0.0721750 * b ** 2.4
    return y if y >= 0.022 else y + (0.022 - y) ** 1.414


def apca(text_hex, bg_hex):
    """APCA Lc, signed: positive is dark text on light, negative is light text on dark."""
    yt, yb = _apca_y(text_hex), _apca_y(bg_hex)
    if abs(yb - yt) < 0.0005:
        return 0.0
    if yb > yt:
        s = (yb ** 0.56 - yt ** 0.57) * 1.14
        return 0.0 if s < 0.1 else round((s - 0.027) * 100, 1)
    s = (yb ** 0.65 - yt ** 0.62) * 1.14
    return 0.0 if s > -0.1 else round((s + 0.027) * 100, 1)


def cmyk_approx(h):
    r, g, b = (c / 255.0 for c in hex_rgb(h))
    k = 1 - max(r, g, b)
    if k >= 1:
        return [0, 0, 0, 100]
    return [round(100 * v) for v in ((1 - r - k) / (1 - k), (1 - g - k) / (1 - k), (1 - b - k) / (1 - k), k)]


def hue_gap(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def hue_lerp(h1, h2, t):
    """Shortest-arc hue interpolation."""
    d = ((h2 - h1 + 180) % 360) - 180
    return (h1 + d * t) % 360


def lerp_oklch(c1, c2, t):
    """c1, c2: (L, C, h). Linear in L and C, shortest arc in h."""
    return (c1[0] + (c2[0] - c1[0]) * t, c1[1] + (c2[1] - c1[1]) * t, hue_lerp(c1[2], c2[2], t))


def lerp_srgb(h1, h2, t):
    a, b = hex_rgb(h1), hex_rgb(h2)
    return rgb_hex([a[i] + (b[i] - a[i]) * t for i in range(3)])


def describe(h):
    L, C, hh = oklch(h)
    return {"hex": norm_hex(h), "rgb": list(hex_rgb(h)), "hsl": list(hsl(h)),
            "oklch": [round(L, 3), round(C, 3), round(hh, 1)], "cmyk_approx": cmyk_approx(h)}
