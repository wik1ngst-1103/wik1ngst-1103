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
from build_assets import THEMES, W, body, card, heading, rule, strong, svg, text  # noqa: E402

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


def stats(d: dict, t: dict) -> str:
    H = 346
    p = [card(W, H, t), heading("PLAYER STATS", 40, 56, t)]
    counters = []
    if d["year"]:
        counters += [("COMMITS", d["year"]["commits"]), ("PULL REQUESTS", d["year"]["prs"]), ("ISSUES", d["year"]["issues"])]
        p.append(text(body, "LAST 12 MONTHS", 10, 960, 55, t["muted"], "end", 2))
    counters += [("REPOS", d["repos"]), ("STARS", d["stars"]), ("FOLLOWERS", d["followers"])]
    col = 920 / len(counters)
    for i, (label, value) in enumerate(counters):
        x = 40 + i * col
        p.append(text(strong, f"{value:,}", 30, x, 118, t["text"]))
        p.append(text(body, label, 10, x + 1, 142, t["muted"], track=2))

    p.append(rule(40, 960, 172, t))
    p.append(heading("TOP LANGUAGES", 40, 212, t))
    total = sum(d["languages"].values()) or 1
    top = sorted(d["languages"].items(), key=lambda kv: -kv[1])[:6]
    segs = 20
    for i, (name, size) in enumerate(top):
        x, y = 40 + (i % 2) * 480, 254 + (i // 2) * 34
        pct = 100 * size / total
        filled = max(1, round(segs * pct / 100 * 2))  # one segment = 2.5%
        p.append(text(strong, strong.fit(name, 14, 130), 14, x, y, t["text"]))
        p.append("".join(
            f'<rect x="{x + 148 + k * 11}" y="{y - 12}" width="8" height="12" rx="1" fill="{t["accent"] if k < filled else t["empty"]}"/>'
            for k in range(segs)
        ))
        p.append(text(body, f"{pct:.0f}%", 13, x + 424, y, t["muted"], "end"))
    if not top:
        p.append(text(body, "No language data yet", 14, 40, 252, t["muted"]))

    alt = ", ".join(f"{v} {k.lower()}" for k, v in counters) + ". Top languages: " + ", ".join(
        f"{n} {100*s/total:.0f}%" for n, s in top)
    return svg(W, H, f"Player stats: {alt}.", "".join(p))


def quests(d: dict, t: dict) -> str:
    qs = d["quests"]
    rows = qs[1:5]
    H = (262 + 44 * len(rows) if rows else 196) if qs else 150
    p = [card(W, H, t), heading("NOW PLAYING", 40, 56, t)]
    if not qs:
        p.append(text(body, "No public quests yet", 16, 40, 104, t["muted"]))
        return svg(W, H, "Now playing: no public repositories yet.", "".join(p))
    now = qs[0]
    p.append(text(strong, strong.fit(now["name"], 24, 920), 24, 40, 104, t["text"]))
    if now["description"]:
        p.append(text(body, body.fit(now["description"], 16, 920), 16, 40, 136, t["muted"]))
    meta = "  ·  ".join(x for x in (now["language"], plural(now["stars"], "star"), f"updated {now['pushed']}") if x)
    p.append(text(body, meta, 13, 40, 164, t["muted"]))
    if rows:
        p.append(rule(40, 960, 190, t))
        p.append(heading("QUEST LOG", 40, 226, t))
        for i, q in enumerate(rows):
            y = 270 + i * 44
            p.append(text(strong, strong.fit(q["name"], 16, 470), 16, 40, y, t["text"]))
            p.append(text(body, body.fit(q["language"], 14, 150), 14, 560, y, t["muted"]))
            p.append(text(body, plural(q["stars"], "star"), 14, 760, y, t["muted"]))
            p.append(text(body, q["pushed"], 14, 960, y, t["muted"], "end"))
    alt = f"Now playing: {now['name']}. Quest log: " + ", ".join(q["name"] for q in rows)
    return svg(W, H, alt, "".join(p))


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
