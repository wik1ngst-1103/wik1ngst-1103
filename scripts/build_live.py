#!/usr/bin/env python3
"""Render the live cards (player stats, quest log) in light and dark.

Runs daily in .github/workflows/snake.yml with GITHUB_TOKEN and publishes to
the `output` branch, so the README never depends on a third-party endpoint.

    GITHUB_TOKEN=... python scripts/build_live.py --user wik1ngst-1103 --out dist
    python scripts/build_live.py --user x --out /tmp/x --sample data.json   # local preview
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_assets import THEMES, W, body, card, fmt, heading, rule, strong, svg, text  # noqa: E402

API = "https://api.github.com"
PROFILE_REPO = "wik1ngst-1103"  # the README repo itself never counts as a quest


def request(url: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-cards"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect(user: str) -> dict:
    profile = request(f"{API}/users/{user}")
    repos, page = [], 1
    while True:
        batch = request(f"{API}/users/{user}/repos?per_page=100&type=owner&sort=pushed&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"] and r["name"] != PROFILE_REPO]
    langs: dict[str, int] = {}
    for r in own:
        for name, size in request(r["languages_url"]).items():
            langs[name] = langs.get(name, 0) + size
    year = {}
    try:  # contributions need GraphQL; the card degrades gracefully without them
        q = "query($l:String!){user(login:$l){contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions}}}"
        c = request(f"{API}/graphql", {"query": q, "variables": {"l": user}})["data"]["user"]["contributionsCollection"]
        year = {"commits": c["totalCommitContributions"], "prs": c["totalPullRequestContributions"], "issues": c["totalIssueContributions"]}
    except Exception as e:  # noqa: BLE001
        print(f"contributions unavailable: {e}", file=sys.stderr)
    own.sort(key=lambda r: r["pushed_at"], reverse=True)
    return {
        "repos": profile["public_repos"],
        "followers": profile["followers"],
        "stars": sum(r["stargazers_count"] for r in own),
        "year": year,
        "languages": langs,
        "quests": [
            {"name": r["name"], "description": r["description"] or "", "language": r["language"] or "",
             "stars": r["stargazers_count"], "pushed": r["pushed_at"][:10]}
            for r in own[:5]
        ],
    }


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


LANG_NAMES = {"Jupyter Notebook": "Jupyter"}


def stats(d: dict, t: dict) -> str:
    H = 500
    p = [card(W, H, t), heading("PLAYER STATS", 40, 62, t)]
    columns = []
    if d["year"]:
        columns.append(("LAST 12 MONTHS", [("Commits", d["year"]["commits"]), ("Pull requests", d["year"]["prs"]), ("Issues", d["year"]["issues"])]))
    columns.append(("ALL TIME", [("Public repos", d["repos"]), ("Stars earned", d["stars"]), ("Followers", d["followers"])]))
    for c, (sub, rows) in enumerate(columns):
        x0 = 40 + c * 500
        p.append(text(body, sub, 17, x0, 112, t["muted"], track=1))
        for i, (label, value) in enumerate(rows):
            y = 162 + i * 46
            p.append(text(body, label, 17, x0, y, t["text"]))
            p.append(text(strong, f"{value:,}", 20, x0 + 420, y, t["text"], "end"))
            if i < len(rows) - 1:
                p.append(rule(x0, x0 + 420, y + 18, t))

    p.append(rule(40, 960, 290, t))
    p.append(heading("TOP LANGUAGES", 40, 340, t))
    total = sum(d["languages"].values()) or 1
    top = sorted(d["languages"].items(), key=lambda kv: -kv[1])[:6]
    segs = 20
    for i, (name, size) in enumerate(top):
        x, y = 40 + (i % 2) * 500, 390 + (i // 2) * 40
        pct = 100 * size / total
        filled = max(1, round(segs * pct / 100 * 2))  # one segment = 2.5%
        p.append(text(strong, strong.fit(LANG_NAMES.get(name, name), 16, 120), 16, x, y, t["text"]))
        p.append("".join(
            f'<rect x="{x + 136 + k * 11}" y="{y - 14}" width="8" height="14" rx="1" fill="{t["accent"] if k < filled else t["empty"]}"/>'
            for k in range(segs)
        ))
        p.append(text(body, f"{pct:.0f}%", 16, x + 420, y, t["muted"], "end"))
    if not top:
        p.append(text(body, "No language data yet", 16, 40, 390, t["muted"]))

    facts = ", ".join(f"{label.lower()} {v}" for _, rows in columns for label, v in rows)
    langs = ", ".join(f"{n} {100*s/total:.0f}%" for n, s in top)
    return svg(W, H, f"Player stats: {facts}. Top languages: {langs}.", "".join(p))


def quests(d: dict, t: dict) -> str:
    qs = d["quests"]
    p = [heading("QUEST LOG", 40, 62, t)]
    if not qs:
        H = 150
        p.append(text(body, "No public quests yet", 17, 40, 112, t["muted"]))
        return svg(W, H, "Quest log: no public repositories yet.", card(W, H, t) + "".join(p))
    legend = "NOW PLAYING"
    lw = body.width(legend, 17, 1)
    p.append(f'<rect x="{fmt(960 - lw - 22)}" y="45" width="10" height="17" fill="{t["accent"]}"/>')
    p.append(text(body, legend, 17, 960, 62, t["muted"], "end", 1))
    y = 120
    for i, q in enumerate(qs[:5]):
        if i == 0:
            p.append(f'<rect class="cur" x="40" y="{y - 19}" width="12" height="20" fill="{t["accent"]}"/>')
        p.append(text(strong, strong.fit(q["name"], 19, 520), 19, 66, y, t["text"]))
        p.append(text(body, body.fit(LANG_NAMES.get(q["language"], q["language"]), 16, 150), 16, 640, y, t["muted"]))
        p.append(text(body, q["pushed"], 16, 960, y, t["muted"], "end"))
        if i == 0 and q["description"]:
            y += 30
            p.append(text(body, body.fit(q["description"], 16, 894), 16, 66, y, t["muted"]))
        if i < min(len(qs), 5) - 1:
            p.append(rule(40, 960, y + 22, t))
        y += 54
    H = y - 54 + 44
    css = (
        "@keyframes c{0%{opacity:1}50%{opacity:0}}.cur{animation:c 1.2s step-end infinite}"
        "@media (prefers-reduced-motion:reduce){.cur{animation:none}}"
    )
    now = qs[0]
    alt = f"Quest log. Now playing: {now['name']}" + (f" ({now['description']})" if now["description"] else "")
    alt += ". Recent: " + ", ".join(q["name"] for q in qs[1:5])
    return svg(W, H, alt, card(W, H, t) + "".join(p), css)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample", help="render from a JSON file instead of the API (local preview only)")
    a = ap.parse_args()
    d = json.loads(pathlib.Path(a.sample).read_text()) if a.sample else collect(a.user)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, t in THEMES.items():
        (out / f"stats-{name}.svg").write_text(stats(d, t))
        (out / f"quests-{name}.svg").write_text(quests(d, t))
    print(f"wrote live cards to {out}")


if __name__ == "__main__":
    main()
