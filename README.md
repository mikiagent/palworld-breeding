# Pal Breeder: Palworld breeding calculator

Static, dependency-free Palworld breeding calculator for game version 1.0. Live at https://palworld-breeding-nu.vercel.app/

- Parents → child lookup and child → parents reverse lookup, both URL-addressable (`/?a=lamball&b=cattiva`, `/?child=anubis&with=penking`).
- A page per Pal (`/pal/<slug>/`) with Paldeck number, elements, partner skill, every parent pair that produces it, and what it breeds with every other Pal.
- `/pals/` grid with name and element filters, `/passive-skills/` list.
- Dark and light theme, mobile-first, sitemap, robots, ads.txt, AdSense loader in every head.

## Build

```bash
python3 scripts/build.py      # writes ./site
python3 scripts/serve.py 8787 # local preview
```

Vercel runs `python3 scripts/build.py` and serves `site/` (see `vercel.json`). No npm, no framework.

## Data and freshness report (reviewed 2026-10-17)

| File | Rows | Status |
|---|---|---|
| `data/breeding.csv` | 44,851 | Complete. 299 Pals → 44,850 unordered pairs (every pair incl. self-pairs is present once; the extra row is the gender-dependent Katress + Wixen pair). 248 special combinations flagged. Matches the pair count on palworld.kimpton.io ("300 owned" there includes Astralym, which cannot be bred). |
| `data/partner-skills-source.csv` | 299 rows, 255 unique Pals | 26 Pals appear twice with paraphrased text (the longer text is used). 45 Pals added in v1.0 were missing (Sekhmet, Wistella, Renjishi, Solenne, Whalaska, Snock, Starryon, Tetroise, etc.). Those 45 were pulled from paldb.cc on 2026-10-17 and live in `data/paldb-partner-skills.json`. Gumoss Flower uses Gumoss's skill. |
| `data/passive-skills.csv` | 115 | Complete for v1.0 (102 Pal passives, 7 World Tree, 5 Mutation, 1 Legendary). Rank -3 to 5. |
| `data/paldex.txt` | 299 | Paldeck numbers and elements, from paldb.cc. |

Game version check: Palworld 1.0 launched 2026-07-10 with 72 new Pals. Patches 1.0.1 (Jul 15), 1.0.2, 1.0.3 (Aug), 1.0.4 (Sep 7) and 1.0.5 (Sep 15) added no Pals and changed no breeding results, so the July data is current as of October 2026.

Known gaps and naming notes:
- Astralym (#204) exists in the Paldeck but has no breeding combinations and no documented partner skill, so it is left out.
- The CSV and kimpton.io call #163B "Snock Lux"; paldb.cc calls the same Pal "Snock Terra" (Electric/Ground). The site keeps "Snock Lux".
- Pal artwork is Pocketpair's, so the site uses element-coloured initials instead of game images.

## AdSense

Publisher `ca-pub-6122961547647042`. Loader tag in `templates/layout.html`, `site/ads.txt` written by the build, privacy policy at `/privacy/`.
