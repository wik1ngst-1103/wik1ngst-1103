---
version: 1
slug: "readme-md"
primary_target: "README.md"
related_targets: []
---

# Surface: GitHub profile README

Mode: Experience. Audience: dev community browsing github.com/wik1ngst-1103. Job: recognise the gamer-dev identity of Le Thanh Son at a glance, see his stack and what he's working on, then follow or reach him.
Constraints: GitHub sanitizes Markdown, so no CSS or JS. All design lives in SVG cards (text outlined), each with light and dark variants through <picture>. Use only true facts (PRODUCT.md). Live cards come from the GitHub API in Actions.

## Direction contract

THESIS: A quiet game HUD. The profile reads like a character screen (name plate, character sheet, loadout, quest log, player stats) in GitHub's own neutral surfaces. It refuses both the neon widget stack and the loud arcade cabinet the user rejected as too colourful (2026-11-27).

OWN-WORLD: Neutral card surfaces matched to GitHub light/dark, 1.5px hairline borders, 14px corners. One amber accent (#E3B341 dark / #9A6700 light) used only for pixel section headings, the cursors, the helmet horns, filled bar segments and the contribution-snake ramp. Press Start 2P only for the handle and section headings; Barlow for everything people read. Monochrome Simple Icons.

STORY: Name plate (WIK1NGST, Le Thanh Son, stack line, pixel helmet) → character sheet + loadout → now playing + quest log (live) → player stats + top languages (live) → contribution snake → follow / Facebook / coffee.

FIRST VIEWPORT: Name plate card full width: pixel handle followed by a static amber block cursor at left, name and stack below, a 16×13 pixel helmet sprite at right. The character sheet + loadout card (hairline label…value rows in two columns) starts directly below. The only blinking cursor marks the now-playing row of the quest log.

FORM: Attract Mode world, quieted into a HUD after user feedback; candidate 7 of 7 on the original ordered list. seed:772f7a143b8ba209

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
