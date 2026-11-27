#!/usr/bin/env python3
"""Build the static SVG cards for the profile README, in light and dark.

Every word is converted to outlines, so the SVGs render the same inside
GitHub's <img> sandbox, where web fonts can't load. Live cards (stats,
quests) are built by scripts/build_live.py in GitHub Actions.

    python3 -m venv .venv && .venv/bin/pip install fonttools
    .venv/bin/python scripts/build_assets.py

Fonts (OFL, github.com/google/fonts) and icons (CC0, simple-icons) are
downloaded into scripts/.fonts and scripts/.icons on first run.
"""
from __future__ import annotations

import html
import pathlib
import re
import urllib.request

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
FONT_DIR = ROOT / "scripts" / ".fonts"
ICON_DIR = ROOT / "scripts" / ".icons"
W = 1000  # every full-width card shares this width

# ── Profile facts (keep true; see PRODUCT.md) ─────────────────────────────
HANDLE = "WIK1NGST"
NAME = "Le Thanh Son"
ROLE = "Developer"
CHARACTER = [
    ("CLASS", "Developer"),
    ("FAV WEAPON", "JavaScript"),
    ("SPAWN", "11 . 03 . 2001"),
    ("SIDE QUESTS", "Math · English"),
]
LOADOUT = [  # icons, label
    (["javascript", "typescript"], "JavaScript · TypeScript"),
    (["react", "nextdotjs"], "React · Next.js"),
    (["nodedotjs"], "Node.js"),
    (["rust"], "Rust"),
]

# ── Themes: neutral surfaces, one amber accent ────────────────────────────
THEMES = {
    "dark": {
        "card": "#151B23", "border": "#2A313C", "text": "#E6EDF3", "muted": "#8D96A0",
        "accent": "#E3B341", "empty": "#262D38",
    },
    "light": {
        "card": "#F6F8FA", "border": "#D8DEE4", "text": "#1F2328", "muted": "#59636E",
        "accent": "#9A6700", "empty": "#E3E7EB",
    },
}

FONTS = {  # key: (google/fonts path, cap-height override)
    "pixel": ("ofl/pressstart2p/PressStart2P-Regular.ttf", 875),
    "body": ("ofl/barlow/Barlow-Medium.ttf", None),
    "strong": ("ofl/barlow/Barlow-SemiBold.ttf", None),
}


def fmt(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


class Face:
    def __init__(self, key: str):
        rel, cap = FONTS[key]
        local = FONT_DIR / pathlib.Path(rel).name
        if not local.exists():
            FONT_DIR.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(f"https://github.com/google/fonts/raw/main/{rel}", local)
        font = TTFont(local)
        self.gs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self.hmtx = font["hmtx"]
        self.cap = cap or font["OS/2"].sCapHeight

    def clean(self, s: str) -> str:
        """Drop characters the face can't draw (emoji, CJK) and collapse spaces."""
        return re.sub(r"\s+", " ", "".join(c if ord(c) in self.cmap else " " for c in s)).strip()

    def width(self, s: str, cap: float, track: float = 0) -> float:
        k = cap / self.cap
        return sum(self.hmtx[self.cmap[ord(c)]][0] * k for c in s) + track * max(len(s) - 1, 0)

    def fit(self, s: str, cap: float, max_w: float, track: float = 0) -> str:
        s = self.clean(s)
        if self.width(s, cap, track) <= max_w:
            return s
        while s and self.width(s + "…", cap, track) > max_w:
            s = s[:-1]
        return s.rstrip() + "…"

    def path(self, s: str, cap: float, x: float, y: float, anchor: str = "start", track: float = 0) -> str:
        s = self.clean(s)
        k = cap / self.cap
        x -= {"start": 0, "middle": 0.5, "end": 1}[anchor] * self.width(s, cap, track)
        pen = SVGPathPen(self.gs, ntos=fmt)
        for c in s:
            g = self.cmap[ord(c)]
            self.gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
            x += self.hmtx[g][0] * k + track
        return pen.getCommands()


pixel, body, strong = Face("pixel"), Face("body"), Face("strong")


def text(face: Face, s: str, cap: float, x: float, y: float, fill: str, anchor: str = "start", track: float = 0) -> str:
    return f'<path d="{face.path(s, cap, x, y, anchor, track)}" fill="{fill}"/>'


def icon(slug: str, x: float, y: float, size: float, fill: str) -> str:
    local = ICON_DIR / f"{slug}.svg"
    if not local.exists():
        ICON_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(f"https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/{slug}.svg", local)
    d = re.search(r' d="([^"]+)"', local.read_text()).group(1)
    return f'<path transform="translate({fmt(x)} {fmt(y)}) scale({size/24:.4f})" d="{d}" fill="{fill}"/>'


def svg(w: int, h: int, title: str, inner: str, style: str = "") -> str:
    t = html.escape(title, quote=True)
    style_block = f"<style>{style}</style>" if style else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{t}"><title>{t}</title>{style_block}{inner}</svg>\n'
    )


def card(w: int, h: int, t: dict) -> str:
    return f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="{t["card"]}" stroke="{t["border"]}" stroke-width="1.5"/>'


def heading(label: str, x: float, y: float, t: dict) -> str:
    return text(pixel, label, 16, x, y, t["accent"], track=1)


def rule(x1: float, x2: float, y: float, t: dict) -> str:
    return f'<path d="M{fmt(x1)} {fmt(y)}H{fmt(x2)}" stroke="{t["border"]}" stroke-width="1"/>'


# ── Pixel sprite: a 16×13 helmet, nod to the handle ──────────────────────
HELMET = [
    "................",
    "a..............a",
    "aa............aa",
    "aa.....tt.....aa",
    ".aa..tttttt..aa.",
    ".aaatttttttttaa.",
    "..atttttttttta..",
    "...tttttttttt...",
    "..mmmmmmmmmmmm..",
    "..ttt..tt..ttt..",
    "..ttt..tt..ttt..",
    "..tt...tt...tt..",
    ".......tt.......",
]


def sprite(x: float, y: float, px: float, t: dict) -> str:
    colour = {"a": t["accent"], "t": t["text"], "m": t["muted"]}
    return "".join(
        f'<rect x="{fmt(x + c * px)}" y="{fmt(y + r * px)}" width="{px}" height="{px}" fill="{colour[ch]}"/>'
        for r, row in enumerate(HELMET) for c, ch in enumerate(row) if ch != "."
    )


# ── Static cards ──────────────────────────────────────────────────────────
STACK = "JavaScript, TypeScript, React, Node.js, Rust"


def header(t: dict) -> str:
    H = 220
    inner = (
        card(W, H, t)
        + text(pixel, HANDLE, 34, 44, 96, t["text"], track=2)
        + f'<rect x="{fmt(44 + pixel.width(HANDLE, 34, 2) + 14)}" y="62" width="20" height="34" fill="{t["accent"]}"/>'
        + text(strong, NAME, 24, 46, 146, t["text"])
        + text(body, f"{ROLE}  ·  {STACK}", 17, 46, 182, t["muted"])
        + sprite(W - 44 - 16 * 7, (H - 13 * 7) / 2, 7, t)
    )
    return svg(W, H, f"{HANDLE}: {NAME}, {ROLE.lower()} ({STACK})", inner)


def sheet(t: dict) -> str:
    H = 316
    parts = [card(W, H, t), heading("CHARACTER", 40, 62, t), heading("LOADOUT", 540, 62, t)]
    parts.append(f'<path d="M500 40V{H-40}" stroke="{t["border"]}" stroke-width="1.5"/>')
    for i, ((k, v), (icons, label)) in enumerate(zip(CHARACTER, LOADOUT)):
        y = 124 + i * 54
        parts.append(text(body, k, 17, 40, y, t["muted"], track=1))
        parts.append(text(strong, v, 20, 460, y, t["text"], "end"))
        for j, slug in enumerate(icons):
            parts.append(icon(slug, 540 + j * 34, y - 22, 24, t["text"]))
        parts.append(text(strong, label, 20, 960, y, t["text"], "end"))
        if i < len(CHARACTER) - 1:
            parts.append(rule(40, 460, y + 22, t))
            parts.append(rule(540, 960, y + 22, t))
    facts = "; ".join(f"{k.title()}: {v}" for k, v in CHARACTER)
    gear = ", ".join(label for _, label in LOADOUT)
    return svg(W, H, f"Character: {facts}. Loadout: {gear}.", "".join(parts))


def title_strip(label: str, t: dict) -> str:
    return svg(W, 44, label.title(), heading(label, 40, 30, t))


def link(slug: str, label: str, t: dict) -> str:
    w, h = 320, 96
    cap = min(18, 18 * (w - 108) / strong.width(label, 18))
    inner = card(w, h, t) + icon(slug, 34, (h - 28) / 2, 28, t["text"]) + text(strong, label, cap, 84, h / 2 + cap / 2, t["text"])
    return svg(w, h, label, inner)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    for name, t in THEMES.items():
        files = {
            f"header-{name}.svg": header(t),
            f"sheet-{name}.svg": sheet(t),
            f"title-contrib-{name}.svg": title_strip("CONTRIBUTIONS", t),
            f"link-github-{name}.svg": link("github", "Follow", t),
            f"link-facebook-{name}.svg": link("facebook", "Facebook", t),
            f"link-coffee-{name}.svg": link("buymeacoffee", "Buy me a coffee", t),
        }
        for fn, content in files.items():
            (OUT / fn).write_text(content)
            print(f"{fn:26} {len(content)/1024:6.1f} KB")


if __name__ == "__main__":
    main()
