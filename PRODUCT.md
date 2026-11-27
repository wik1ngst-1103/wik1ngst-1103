# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Other developers who land on github.com/wik1ngst-1103: friends, peers, and people who follow a link from a repo or commit. They glance at the profile for a few seconds to see who this person is, what they code in, and whether they're active.

## Product Purpose
The GitHub profile README of Le Thanh Son (handle `wik1ngst`, account `wik1ngst-1103`). It introduces him to the dev community with a modern gaming identity: personality first, still readable at a glance. Success: a visitor remembers the gamer-dev identity and can see what he works with and how to reach him.

## Positioning
A personal profile drawn from his own world (games, JavaScript, the `wik1ngst` handle), not a wall of stock widgets. The look should feel authored for this one person.

## Operating Context
- Rendered by GitHub's Markdown sanitizer: no CSS and no scripts. Only a subset of HTML works (`<p align>`, `<img>`, `<picture>`, `<a>`, `<table>`, `<sub>`, `<br>`).
- Visual design therefore has to live in image assets (SVG or raster) committed to the repo, or in third-party image endpoints.
- Visitors see it in GitHub's light or dark theme. `<picture>` with `prefers-color-scheme` is the only theme switch available.
- Third-party widget endpoints (vercel stats, trophies) can go down or hit rate limits. In Nov 2026 the trophy endpoint was rendering as a broken image.

## Capabilities and Constraints
- He now works as a developer. His exact role and stack beyond JavaScript are **unconfirmed**; don't invent specifics.
- `.github/workflows/snake.yml` generates the contribution snake on the `output` branch (Platane/snk).

## Brand Commitments
- Name: Le Thanh Son. Handle: wik1ngst. GitHub account: wik1ngst-1103.
- Modern gaming style, as he asked.
- Keep: birthday 11/03/2001, Facebook (facebook.com/lethanhson.wist0514), Buy Me a Coffee (buymeacoffee.com/thanhson0514).
- Old copy was English; keep English.

## Evidence on Hand
- JavaScript is his stated favourite language. In the past he named Mathematics and English as personal challenges.
- Thuy Loi University (studied there; not chosen to keep as a headline fact).
- `giphy.gif` in the repo; he did not choose to keep it on the profile.
- No projects, employers, or achievements were supplied. Don't fabricate any.

## Product Principles
1. Every image on the page must load. Prefer assets committed to this repo over fragile third-party endpoints.
2. Make his identity unmistakable within the first screen.
3. Feel hand-made: one coherent visual world, not a stack of mismatched widgets.
4. Show only true facts; leave gaps visible rather than inventing them.
