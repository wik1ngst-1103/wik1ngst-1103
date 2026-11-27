#!/usr/bin/env python3
"""Build the arcade-cabinet SVG assets for the profile README.

Every word is converted to outlines, so the SVGs render the same inside
GitHub's <img> sandbox, where web fonts can't load.

    python3 -m venv .venv && .venv/bin/pip install fonttools
    .venv/bin/python scripts/build_assets.py

Fonts (OFL, from github.com/google/fonts) are downloaded into
scripts/.fonts/ the first time and are not committed. The live stats
screen is built separately by scripts/build_stats.py in GitHub Actions.
"""
from __future__ import annotations

import pathlib
import urllib.request

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
FONT_DIR = ROOT / "scripts" / ".fonts"

# ── Profile facts (keep true; see PRODUCT.md) ─────────────────────────────
HANDLE = "WIK1NGST"
NAME = "LE THANH SON"
ROLE = "DEVELOPER"
SCORES = [  # rank, stat, value
    ("1ST", "PLAYER", NAME),
    ("2ND", "CLASS", ROLE),
    ("3RD", "FAV WEAPON", "JAVASCRIPT"),
    ("4TH", "SPAWN", "11.03.2001"),
    ("5TH", "SIDE QUEST", "MATH + ENGLISH"),
]

# ── Tokens: cobalt enamel + marquee yellow + one red, on ink and cream ────
COBALT = "#1C3FAA"
COBALT_HI = "#2A52CC"
COBALT_LO = "#132D80"
YELLOW = "#FFC93C"
YELLOW_LO = "#C99415"
RED = "#E8452C"  # only the live action: FOLLOW disc, PRESS START, marquee extrusion
RED_LO = "#A92E1B"
INK = "#0E0F1A"
INK_2 = "#1B1D2E"
INK_3 = "#2A2D44"
CREAM = "#F6F1E6"
CREAM_DIM = "#B9B4C8"  # cream tinted toward the CRT ink, for small print on glass
CREAM_ON_COBALT = "#D8DEF5"

FONTS = {  # key: (google/fonts path, variable weight, cap-height override)
    "bungee": ("ofl/bungee/Bungee-Regular.ttf", None, None),
    "barlow": ("ofl/barlowcondensed/BarlowCondensed-Bold.ttf", None, None),
    "pixel": ("ofl/pressstart2p/PressStart2P-Regular.ttf", None, 875),
}


def fmt(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


class Face:
    def __init__(self, key: str):
        rel, wght, cap = FONTS[key]
        local = FONT_DIR / pathlib.Path(rel).name
        if not local.exists():
            FONT_DIR.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(f"https://github.com/google/fonts/raw/main/{rel}", local)
        font = TTFont(local)
        if wght:
            font = instancer.instantiateVariableFont(font, {"wght": wght})
        self.gs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self.hmtx = font["hmtx"]
        self.upm = font["head"].unitsPerEm
        self.cap = cap or font["OS/2"].sCapHeight

    def size_for_cap(self, cap_px: float) -> float:
        return cap_px * self.upm / self.cap

    def width(self, text: str, cap: float, track: float = 0) -> float:
        s = self.size_for_cap(cap) / self.upm
        return sum(self.hmtx[self.cmap[ord(c)]][0] * s for c in text) + track * (len(text) - 1)

    def path(self, text: str, cap: float, x: float, y: float, anchor: str = "start", track: float = 0) -> str:
        s = self.size_for_cap(cap) / self.upm
        w = self.width(text, cap, track)
        x -= {"start": 0, "middle": w / 2, "end": w}[anchor]
        pen = SVGPathPen(self.gs, ntos=fmt)
        for c in text:
            g = self.cmap[ord(c)]
            self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
            x += self.hmtx[g][0] * s + track
        return pen.getCommands()


bungee, barlow, pixel = Face("bungee"), Face("barlow"), Face("pixel")


def svg(w: int, h: int, title: str, body: str, style: str = "") -> str:
    style_block = f"<style>{style}</style>" if style else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{title}"><title>{title}</title>{style_block}{body}</svg>\n'
    )


def bolt(cx: float, cy: float) -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="6" fill="{COBALT_LO}"/>'
        f'<path d="M{cx-3.5} {cy}h7" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
    )


def cabinet(w: int, h: int, r: int = 22) -> str:
    """Cobalt enamel body with a black T-molding edge: the ground of every part."""
    return (
        f'<rect width="{w}" height="{h}" rx="{r}" fill="{INK}"/>'
        f'<rect x="6" y="6" width="{w-12}" height="{h-12}" rx="{r-5}" fill="{COBALT}"/>'
    )


def crt(x: int, y: int, w: int, h: int, gid: str) -> tuple[str, str, str]:
    """Return (defs, glass, scanlines+rim) for a CRT set into the cabinet."""
    defs = f"""
  <radialGradient id="{gid}g" cx="50%" cy="46%" r="72%">
    <stop offset="0" stop-color="#16204A"/><stop offset=".7" stop-color="#0B1030"/><stop offset="1" stop-color="#05071A"/>
  </radialGradient>
  <clipPath id="{gid}c"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="34"/></clipPath>"""
    glass = (
        f'<rect x="{x-14}" y="{y-14}" width="{w+28}" height="{h+28}" rx="44" fill="{INK}"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="34" fill="url(#{gid}g)"/>'
    )
    scan = "".join(f'<rect x="{x}" y="{yy}" width="{w}" height="1.4"/>' for yy in range(y, y + h, 4))
    over = (
        f'<g clip-path="url(#{gid}c)" fill="#000" opacity=".28">{scan}</g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="34" fill="none" stroke="{INK_3}" stroke-width="3"/>'
    )
    return defs, glass, over


# ── Marquee ───────────────────────────────────────────────────────────────
def marquee() -> str:
    W, H = 1000, 300
    cap = 112
    handle_w = bungee.width(HANDLE, cap, 6)
    if handle_w > 820:
        cap *= 820 / handle_w
    handle = bungee.path(HANDLE, cap, W / 2, 178, "middle", 6)
    sub = barlow.path(f"{NAME}  ·  {ROLE}", 24, W / 2, 256, "middle", 6)
    extrude = "".join(f'<use href="#h" x="{i}" y="{i}"/>' for i in range(9, 0, -1))
    body = f"""
<defs>
  <radialGradient id="lit" cx="50%" cy="42%" r="70%">
    <stop offset="0" stop-color="{COBALT_HI}"/><stop offset="1" stop-color="{COBALT_LO}"/>
  </radialGradient>
  <clipPath id="panel"><rect x="18" y="18" width="964" height="264" rx="10"/></clipPath>
  <path id="h" d="{handle}"/>
</defs>
<rect width="{W}" height="{H}" rx="22" fill="{INK}"/>
<rect x="18" y="18" width="964" height="264" rx="10" fill="url(#lit)"/>
<g clip-path="url(#panel)">
  <path d="M-20 134h1040v16H-20z" fill="{YELLOW}"/>
  <path d="M-20 158h1040v16H-20z" fill="{RED}"/>
  <path d="M-20 182h1040v6H-20z" fill="{CREAM}" opacity=".85"/>
</g>
<g fill="{RED_LO}" stroke="{INK}" stroke-width="10" stroke-linejoin="round" paint-order="stroke">{extrude}</g>
<g fill="{RED_LO}">{extrude}</g>
<use href="#h" fill="{YELLOW}" stroke="{INK}" stroke-width="3" stroke-linejoin="round" paint-order="stroke"/>
<path d="{sub}" fill="{CREAM}"/>
"""
    return svg(W, H, f"{HANDLE} — {NAME}, {ROLE.lower()}", body)


# ── CRT screen in attract mode ────────────────────────────────────────────
def screen() -> str:
    W, H = 1000, 600
    sx, sy, sw, sh = 52, 46, 896, 508
    defs, glass, over = crt(sx, sy, sw, sh, "s")
    parts: list[str] = []
    css = [
        "@keyframes blink{0%{opacity:1}50%{opacity:0}}",
        ".blink{animation:blink 1.1s step-end infinite}",
    ]

    # status line
    parts.append(f'<path d="{pixel.path("HI-SCORE", 18, W/2 - 12, 118, "end")}" fill="{YELLOW}"/>')
    parts.append(f'<path d="{pixel.path("110301", 18, W/2 + 12, 118, "start")}" fill="{CREAM}"/>')

    parts.append(f'<path d="{bungee.path("HIGH SCORES", 36, W/2, 196, "middle", 4)}" fill="{YELLOW}"/>')

    colours = [YELLOW, CREAM, YELLOW, CREAM, YELLOW]
    y0, step, cap = 262, 50, 20
    for i, ((rank, stat, value), colour) in enumerate(zip(SCORES, colours)):
        y = y0 + i * step
        stat_end = 214 + pixel.width(stat, cap)
        val_start = 890 - pixel.width(value, cap)
        dots = "".join(
            f'<rect x="{fmt(x)}" y="{y-5}" width="5" height="5"/>'
            for x in [stat_end + 18 + k * 15 for k in range(200)]
            if x < val_start - 20
        )
        row = (
            f'<path d="{pixel.path(rank, cap, 110, y)}"/>'
            f'<path d="{pixel.path(stat, cap, 214, y)}"/>'
            f'<g opacity=".5">{dots}</g>'
            f'<path d="{pixel.path(value, cap, 890, y, "end")}"/>'
        )
        parts.append(f'<g class="r{i}" fill="{colour}">{row}</g>')
        # Visible on load; the table clears at 84% of the loop and re-enters row by row.
        on = 86 + i * 2.5
        css.append(
            f"@keyframes r{i}{{0%{{opacity:1}}84%{{opacity:0}}{on}%{{opacity:1}}100%{{opacity:1}}}}"
            f".r{i}{{animation:r{i} 11s step-end infinite}}"
        )

    parts.append(
        f'<g class="blink"><path d="{bungee.path("PRESS START", 24, W/2, 520, "middle", 5)}" fill="{RED}"/></g>'
    )
    css.append("@media (prefers-reduced-motion:reduce){*{animation:none!important}}")

    body = f"""
<defs>{defs}</defs>
{cabinet(W, H, 26)}
{glass}
<g clip-path="url(#sc)">{''.join(parts)}</g>
{over}
"""
    alt = "High scores: " + "; ".join(f"{s.title()} {v.title()}" for _, s, v in SCORES) + ". Press start to follow."
    return svg(W, H, alt, body, "".join(css))


# ── Control-panel buttons (identical units; red only for the live action) ─
def button(word: str, dome: str, dome_lo: str, label: str) -> str:
    W, H = 490, 170
    cx, cy = 96, 85
    cap = 44
    if bungee.width(word, cap, 2) > 270:
        cap *= 270 / bungee.width(word, cap, 2)
    body = f"""
<defs>
  <radialGradient id="d" cx="38%" cy="32%" r="75%">
    <stop offset="0" stop-color="{dome}"/><stop offset="1" stop-color="{dome_lo}"/>
  </radialGradient>
</defs>
{cabinet(W, H)}
<circle cx="{cx}" cy="{cy}" r="56" fill="{INK}"/>
<circle cx="{cx}" cy="{cy}" r="49" fill="{INK_3}"/>
<circle cx="{cx}" cy="{cy+4}" r="41" fill="{dome_lo}"/>
<circle cx="{cx}" cy="{cy}" r="41" fill="url(#d)"/>
<ellipse cx="{cx-13}" cy="{cy-17}" rx="16" ry="9" transform="rotate(-28 {cx-13} {cy-17})" fill="{CREAM}" opacity=".55"/>
<path d="{bungee.path(word, cap, 180, cy + cap / 2, "start", 2)}" fill="{CREAM}"/>
"""
    return svg(W, H, label, body)


# ── Section label strip ───────────────────────────────────────────────────
def label(text: str) -> str:
    W, H = 1000, 72
    body = f"""
{cabinet(W, H, 16)}
<path d="{barlow.path(text, 22, 30, 47, "start", 6)}" fill="{YELLOW}"/>
<path d="M886 18h20l-14 36h-20z" fill="{YELLOW}"/>
<path d="M914 18h20l-14 36h-20z" fill="{CREAM}"/>
<path d="M942 18h20l-14 36h-20z" fill="{INK}"/>
"""
    return svg(W, H, text.title(), body)


# ── Coin door: the page's close, linked to Buy Me a Coffee ────────────────
def coin_door() -> str:
    W, H = 1000, 200
    cx = 820
    body = f"""
{cabinet(W, H)}
<rect x="700" y="26" width="240" height="148" rx="12" fill="{INK}"/>
<rect x="710" y="36" width="220" height="128" rx="8" fill="{INK_2}" stroke="{INK_3}" stroke-width="2"/>
<rect x="{cx-58}" y="54" width="116" height="62" rx="8" fill="{YELLOW}"/>
<rect x="{cx-58}" y="54" width="116" height="62" rx="8" fill="none" stroke="{YELLOW_LO}" stroke-width="3"/>
<rect x="{cx-5}" y="64" width="10" height="42" rx="3" fill="{INK}"/>
<rect x="{cx-26}" y="130" width="52" height="18" rx="4" fill="{INK}" stroke="{INK_3}" stroke-width="2"/>
<path d="{bungee.path("INSERT COIN", 38, 56, 100, "start", 4)}" fill="{YELLOW}"/>
<path d="{barlow.path("BUY ME A COFFEE", 22, 58, 142, "start", 6)}" fill="{CREAM}"/>
{bolt(22, 22)}{bolt(W-22, 22)}{bolt(22, H-22)}{bolt(W-22, H-22)}
"""
    return svg(W, H, "Insert coin: buy me a coffee", body)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    files = {
        "marquee.svg": marquee(),
        "screen.svg": screen(),
        "btn-follow.svg": button("FOLLOW", RED, RED_LO, "Follow on GitHub"),
        "btn-facebook.svg": button("FACEBOOK", YELLOW, YELLOW_LO, "Facebook"),
        "label-demo.svg": label("DEMO PLAY — CONTRIBUTION SNAKE"),
        "label-stats.svg": label("LIVE STATS"),
        "coin-door.svg": coin_door(),
    }
    for name, content in files.items():
        (OUT / name).write_text(content)
        print(f"{name:18} {len(content)/1024:6.1f} KB")


if __name__ == "__main__":
    main()
