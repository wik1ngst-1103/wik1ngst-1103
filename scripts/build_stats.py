#!/usr/bin/env python3
"""Render the live-stats CRT (repos, stars, followers, top languages) as an SVG.

Runs in .github/workflows/snake.yml with GITHUB_TOKEN set and writes to the
`output` branch, so the README never depends on a third-party stats endpoint.

    GITHUB_TOKEN=... python scripts/build_stats.py --user wik1ngst-1103 --out dist/stats.svg
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_assets import (  # noqa: E402
    CREAM, INK_3, YELLOW, bungee, cabinet, crt, fmt, pixel, svg,
)

API = "https://api.github.com"


def get(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-stats"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect(user: str) -> dict:
    profile = get(f"{API}/users/{user}")
    repos, page = [], 1
    while True:
        batch = get(f"{API}/users/{user}/repos?per_page=100&type=owner&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]
    langs: dict[str, int] = {}
    for r in own:
        for name, size in get(r["languages_url"]).items():
            langs[name] = langs.get(name, 0) + size
    return {
        "repos": profile["public_repos"],
        "stars": sum(r["stargazers_count"] for r in own),
        "followers": profile["followers"],
        "languages": langs,
    }


def render(data: dict) -> str:
    W, H = 1000, 640
    sx, sy, sw, sh = 52, 46, 896, 548
    defs, glass, over = crt(sx, sy, sw, sh, "t")
    p: list[str] = []

    p.append(f'<path d="{bungee.path("PLAYER STATS", 36, W/2, 128, "middle", 4)}" fill="{YELLOW}"/>')

    for (label, value), x in zip(
        (("REPOS", data["repos"]), ("STARS", data["stars"]), ("FOLLOWERS", data["followers"])),
        (230, 500, 770),
    ):
        p.append(f'<path d="{pixel.path(label, 16, x, 186, "middle")}" fill="{YELLOW}"/>')
        p.append(f'<path d="{pixel.path(str(value), 32, x, 238, "middle")}" fill="{CREAM}"/>')

    total = sum(data["languages"].values()) or 1
    top = sorted(data["languages"].items(), key=lambda kv: -kv[1])[:6]
    lead = top[0][1] if top else 1
    y0, step, segs = 312, 46, 16
    for i, (name, size) in enumerate(top):
        y = y0 + i * step
        pct = 100 * size / total
        filled = max(1, round(segs * size / lead))
        p.append(f'<path d="{pixel.path(name.upper()[:16], 16, 110, y)}" fill="{CREAM}"/>')
        blocks = "".join(
            f'<rect x="{fmt(470 + k * 19)}" y="{y-16}" width="14" height="16" '
            f'fill="{YELLOW if k < filled else INK_3}"/>'
            for k in range(segs)
        )
        p.append(blocks)
        p.append(f'<path d="{pixel.path(f"{pct:.0f}%", 16, 890, y, "end")}" fill="{YELLOW}"/>')


    body = f"""
<defs>{defs}</defs>
{cabinet(W, H, 26)}
{glass}
<g clip-path="url(#tc)">{''.join(p)}</g>
{over}
"""
    langs = ", ".join(f"{n} {100*s/total:.0f}%" for n, s in top)
    alt = f"Player stats: {data['repos']} repos, {data['stars']} stars, {data['followers']} followers. Top languages: {langs}."
    return svg(W, H, alt, body)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample", help="render from a JSON file instead of the API (local preview only)")
    a = ap.parse_args()
    data = json.loads(pathlib.Path(a.sample).read_text()) if a.sample else collect(a.user)
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(data))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
