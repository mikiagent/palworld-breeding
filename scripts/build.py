#!/usr/bin/env python3
"""Build the static Palworld breeding site into ./site from ./data and ./templates."""
import csv, json, re, os, shutil, html, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data'); TPL = os.path.join(ROOT, 'templates'); OUT = os.path.join(ROOT, 'site')
SITE_URL = os.environ.get('SITE_URL', 'https://palworld-breeding-nu.vercel.app')
ADSENSE = 'ca-pub-6122961547647042'
TODAY = datetime.date.today().isoformat()

def slug(n): return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')
def esc(s): return html.escape(s or '', quote=True)

# ---------- pals ----------
pals = []  # ordered by paldex
for line in open(os.path.join(DATA, 'paldex.txt')):
    if '|' not in line: continue
    num, name, els = [x.strip() for x in line.split('|')]
    pals.append({'slug': slug(name), 'name': name, 'num': num, 'els': [e.strip() for e in els.split(',')],
                 'crossover': num.startswith('T')})
idx = {p['slug']: i for i, p in enumerate(pals)}
by_slug = {p['slug']: p for p in pals}

# partner skills: user CSV (first occurrence, prefer longest effect) then paldb fallback
ps = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(DATA, 'partner-skills-source.csv'), encoding='utf-8-sig')):
    ps[slug(r['pal_name'])].append(r)
paldb = json.load(open(os.path.join(DATA, 'paldb-partner-skills.json')))
paldb = {slug(k.replace('_', ' ')): v for k, v in paldb.items()}
missing = []
for p in pals:
    s = p['slug']
    if s in ps:
        best = max(ps[s], key=lambda r: len(r['effect']))
        p['skill'] = best['partner_skill_name']; p['skill_effect'] = best['effect']; p['skill_src'] = 'palworld.gg'
    elif s in paldb and paldb[s]['skill'] and paldb[s]['skill'] != '-':
        v = paldb[s]; p['skill'] = v['skill']; p['skill_effect'] = re.sub(r'\s+([.,%)])', r'\1', v['effect']); p['skill_src'] = 'paldb.cc'
    elif s == 'gumoss-flower':
        g = by_slug['gumoss']; p['skill'] = g['skill']; p['skill_effect'] = g['skill_effect']; p['skill_src'] = 'palworld.gg (same as Gumoss)'
    else:
        p['skill'] = None; p['skill_effect'] = None; p['skill_src'] = None; missing.append(s)
print('pals without partner skill:', missing)

# ---------- breeding ----------
N = len(pals)
child = [[-1] * N for _ in range(N)]
special = set()
gender_rules = []  # (a, b, child, a_gender, b_gender)
rows = list(csv.DictReader(open(os.path.join(DATA, 'breeding.csv'))))
for r in rows:
    a, b, c = idx[r['parent_a']], idx[r['parent_b']], idx[r['child']]
    if r['parent_a_gender']:
        gender_rules.append((a, b, c, r['parent_a_gender'], r['parent_b_gender']))
        if child[a][b] == -1: child[a][b] = child[b][a] = c
        continue
    child[a][b] = child[b][a] = c
    if r['special_combination'] == 'true': special.add((min(a, b), max(a, b)))
pairs_total = sum(1 for i in range(N) for j in range(i, N) if child[i][j] >= 0)
print('pals', N, 'pairs', pairs_total, 'rows', len(rows))
parents_of = collections.defaultdict(list)
for i in range(N):
    for j in range(i, N):
        if child[i][j] >= 0: parents_of[child[i][j]].append((i, j))

# ---------- passives ----------
passives = list(csv.DictReader(open(os.path.join(DATA, 'passive-skills.csv'), encoding='utf-8-sig')))

# ---------- output ----------
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
shutil.copytree(os.path.join(ROOT, 'static'), OUT, dirs_exist_ok=True)
layout = open(os.path.join(TPL, 'layout.html')).read()

def page(path, title, desc, body, extra_head='', canonical=None):
    url = SITE_URL + (canonical if canonical is not None else path)
    out = (layout.replace('{{title}}', esc(title)).replace('{{desc}}', esc(desc)).replace('{{body}}', body)
           .replace('{{canonical}}', url).replace('{{extra_head}}', extra_head).replace('{{adsense}}', ADSENSE)
           .replace('{{year}}', TODAY[:4]))
    full = os.path.join(OUT, path.strip('/'), 'index.html') if path != '/' else os.path.join(OUT, 'index.html')
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w').write(out)
    return path

def avatar(p, size='md'):
    e = p['els'][0].lower(); e2 = p['els'][1].lower() if len(p['els']) > 1 else e
    ini = ''.join(w[0] for w in p['name'].replace('(', '').split()[:2]).upper()
    return f'<span class="avatar avatar-{size} el-{e}" data-el2="{e2}" aria-hidden="true">{ini}</span>'

def plink(p):
    return f'<a class="pl el-{p["els"][0].lower()}" href="/pal/{p["slug"]}/">{esc(p["name"])}</a>'

def chip(p, size='md'):
    return (f'<a class="palchip" href="/pal/{p["slug"]}/">{avatar(p, size)}<span class="palchip-text"><b>{esc(p["name"])}</b>'
            f'<small>#{p["num"]}</small></span></a>')

def els_html(p):
    return ''.join(f'<span class="el-tag el-{e.lower()}">{e}</span>' for e in p['els'])

urls = []
# --- home / calculator ---
home_body = open(os.path.join(TPL, 'home.html')).read()
urls.append(page('/', 'Palworld Breeding Calculator (v1.0, all 299 Pals)',
                 'Free Palworld breeding calculator for v1.0. Pick two parents to see the child, or pick a Pal to see every parent combination that breeds it. All 44,850 pairs, 299 Pals.',
                 home_body))

# --- pal list ---
grid = ''.join(
    f'<a class="palcard" href="/pal/{p["slug"]}/" data-name="{esc(p["name"].lower())}" data-els="{" ".join(e.lower() for e in p["els"])}">'
    f'{avatar(p, "lg")}<span class="palcard-num">#{p["num"]}</span><span class="palcard-name">{esc(p["name"])}</span>'
    f'<span class="palcard-els">{els_html(p)}</span></a>' for p in pals)
els_all = ['Neutral', 'Grass', 'Fire', 'Water', 'Electric', 'Ice', 'Ground', 'Dark', 'Dragon']
filters = ''.join(f'<button class="filter el-{e.lower()}" data-el="{e.lower()}" type="button">{e}</button>' for e in els_all)
urls.append(page('/pals/', 'All Palworld Pals: Paldeck list with elements and partner skills',
                 'Browse every Pal in Palworld v1.0, including subspecies and Terraria crossover Pals. Filter by element and open any Pal for its partner skill and breeding combinations.',
                 f'<h1>All Pals</h1><p class="lead">{N} Pals in Palworld v1.0, including subspecies and the Terraria crossover Pals. Open any Pal for its partner skill and every breeding combination.</p>'
                 f'<div class="toolbar"><input id="pal-filter" type="search" placeholder="Filter by name…" aria-label="Filter Pals by name"><div class="filters">{filters}</div></div>'
                 f'<div class="palgrid" id="palgrid">{grid}</div><p id="nomatch" class="muted" hidden>No Pals match.</p>'))

# --- pal pages ---
for i, p in enumerate(pals):
    combos = parents_of.get(i, [])
    # table: breed with every pal
    with_rows = ''.join(
        f'<tr><td>{plink(pals[j])}</td><td>{plink(pals[child[i][j]])}'
        f'{" <span class=\"badge\">special</span>" if (min(i,j),max(i,j)) in special else ""}</td></tr>'
        for j in range(N) if child[i][j] >= 0)
    self_pair = any(a == b == i for a, b in combos)
    parent_rows = ''.join(
        f'<tr><td>{plink(pals[a])}</td><td class="plus">+</td><td>{plink(pals[b])}</td></tr>'
        for a, b in combos if not (a == b))
    gender_note = ''
    for a, b, c, ga, gb in gender_rules:
        if c == i or i in (a, b):
            gender_note += (f'<p class="note"><b>Gender matters here:</b> {pals[a]["name"]} ({ga}) + {pals[b]["name"]} ({gb}) → '
                            f'<a href="/pal/{pals[c]["slug"]}/">{pals[c]["name"]}</a>.</p>')
    n_combos = len(combos)
    how = (f'<p>{p["name"]} can be bred from <b>{n_combos}</b> parent pair{"s" if n_combos != 1 else ""}.'
           + (' Two ' + p['name'] + ' always breed another ' + p['name'] + '.' if self_pair else '') + '</p>') if n_combos else \
          f'<p>No breeding pair produces {p["name"]} in v1.0 data. It has to be caught or hatched from a wild egg.</p>'
    skill = (f'<section class="card"><h2>Partner skill: {esc(p["skill"])}</h2><p>{esc(p["skill_effect"])}</p>'
             f'<p class="muted small">Source: {esc(p["skill_src"])}</p></section>') if p['skill'] else \
            '<section class="card"><h2>Partner skill</h2><p class="muted">Not yet documented for this Pal.</p></section>'
    body = (f'<nav class="crumbs"><a href="/pals/">All Pals</a> › {esc(p["name"])}</nav>'
            f'<header class="palhead">{avatar(p, "xl")}<div><h1>{esc(p["name"])}</h1><p class="muted">Paldeck #{p["num"]} · {els_html(p)}</p></div></header>'
            f'{skill}'
            f'<section class="card"><h2>How to breed {esc(p["name"])}</h2>{how}{gender_note}'
            + (f'<div class="tablewrap"><table class="combos"><thead><tr><th>Parent</th><th></th><th>Parent</th></tr></thead><tbody>{parent_rows}</tbody></table></div>' if parent_rows else '')
            + '</section>'
            f'<section class="card"><h2>Breed {esc(p["name"])} with any Pal</h2><p class="muted small">Child when {esc(p["name"])} is one parent. Gender does not matter except where noted.</p>'
            f'<div class="tablewrap"><table class="combos"><thead><tr><th>Other parent</th><th>Child</th></tr></thead><tbody>{with_rows}</tbody></table></div></section>'
            f'<p><a class="btn" href="/?child={p["slug"]}">Open {esc(p["name"])} in the calculator</a></p>')
    urls.append(page(f'/pal/{p["slug"]}/', f'How to breed {p["name"]} in Palworld: all {n_combos} parent combos',
                     f'{p["name"]} (#{p["num"]}, {"/".join(p["els"])}) breeding guide: {n_combos} parent pairs that produce {p["name"]}, its partner skill {p["skill"] or ""}, and what it breeds with every other Pal.',
                     body))

# --- passives ---
cat_order = ['Pals', 'Mutation', 'World Tree', 'Legendary']
prow = ''.join(
    f'<tr><td><b>{esc(r["passive_name"])}</b></td><td class="rank r{r["rank"].replace("-","m")}">{r["rank"]}</td><td>{esc(r["source_category"])}</td><td>{esc(r["effect"])}</td></tr>'
    for r in sorted(passives, key=lambda r: (cat_order.index(r['source_category']) if r['source_category'] in cat_order else 9, -int(r['rank']), r['passive_name'])))
urls.append(page('/passive-skills/', 'Palworld passive skills list (v1.0): all 115 passives with effects',
                 'Every passive skill in Palworld v1.0 with its rank and effect, including Mutation, World Tree and Legendary passives. Useful when planning what to breed.',
                 f'<h1>Passive skills</h1><p class="lead">All {len(passives)} passive skills in Palworld v1.0. Rank runs from -3 (worst) to 5 (best). Bred children inherit passives from parents, so these are what you are breeding for.</p>'
                 f'<div class="toolbar"><input id="passive-filter" type="search" placeholder="Filter passives…" aria-label="Filter passives"></div>'
                 f'<div class="tablewrap"><table class="passives" id="passives"><thead><tr><th>Passive</th><th>Rank</th><th>Category</th><th>Effect</th></tr></thead><tbody>{prow}</tbody></table></div>'))

# --- about / privacy ---
for name, title, desc in [('about', 'About this Palworld breeding calculator', 'What this site is, where its breeding data comes from, and how to report an error.'),
                          ('privacy', 'Privacy policy', 'How this site uses cookies and advertising (Google AdSense).')]:
    urls.append(page(f'/{name}/', title, desc, open(os.path.join(TPL, f'{name}.html')).read().replace('{{n_pals}}', str(N)).replace('{{n_pairs}}', f'{pairs_total:,}').replace('{{today}}', TODAY)))

# --- data for the client ---
data = {'pals': [{'s': p['slug'], 'n': p['name'], 'num': p['num'], 'e': p['els']} for p in pals],
        'child': child,
        'special': sorted(list(x) for x in special),
        'gender': [[a, b, c, ga, gb] for a, b, c, ga, gb in gender_rules]}
open(os.path.join(OUT, 'data.json'), 'w').write(json.dumps(data, separators=(',', ':')))

# --- sitemap / robots / ads ---
open(os.path.join(OUT, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    ''.join(f'  <url><loc>{SITE_URL}{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in urls) + '</urlset>\n')
open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n')
open(os.path.join(OUT, 'ads.txt'), 'w').write('google.com, pub-6122961547647042, DIRECT, f08c47fec0942fa0\n')
print('wrote', len(urls), 'pages to', OUT)
