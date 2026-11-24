"""Checks of the check database and the permanent check IDs, with a report.

    python tests/db_check.py

For every classified area (CLASSIFIED below): every object found in the game's map files has a check,
every check has a valid permanent ID, IDs are unique and registered in data/ids.json, the game's
placement hashes and our IDs are never mixed up, and data/db/<Area>.json is up to date.
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from logic.world import World  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import build_db  # noqa: E402

CLASSIFIED = ['KokiriForest', 'ForestTemple']          # areas whose checks all have IDs
TYPE_OF_KIND = {'chest': 'CHEST', 'skulltula': 'GS', 'scrub': 'SCRUB', 'shop': 'SHOP', 'pot': 'POT',
                'freestanding': 'ITEM', 'rock': 'ROCK', 'boulder': 'BOULDER', 'bush': 'BUSH',
                'gift': ('GIFT', 'SONG'), 'gossip': 'GOSSIP'}
ID_RE = re.compile(r'^([A-Z][A-Z0-9]*)(_[A-Z0-9]+)+$')
RANDOMIZABLE = {'yes', 'no', 'untested'}

w = World()
reg = json.load(open(os.path.join(ROOT, 'data', 'ids.json'), encoding='utf-8'))
errors = []

# every check with an ID, anywhere
with_id = {}
for r in w.regions.values():
    for name, loc in r.locations.items():
        if 'id' in loc:
            if loc['id'] in with_id:
                errors.append('duplicate ID %s (%s, %s)' % (loc['id'], with_id[loc['id']][1], name))
            with_id[loc['id']] = (r, name, loc)

# registry
active = {k for k, v in reg['ids'].items() if v['status'] == 'active'}
retired = {k for k, v in reg['ids'].items() if v['status'] == 'retired'}
for cid in sorted(set(with_id) - active):
    errors.append('%s: in the data but not an active ID in data/ids.json' % cid)
for cid in sorted(active - set(with_id)):
    errors.append('%s: active in data/ids.json but missing from the data (retire it instead)' % cid)
for cid in sorted(retired & set(with_id)):
    errors.append('%s: retired ID used again' % cid)

# ID format, area code, type code, numbering
groups = collections.defaultdict(list)
for cid, (r, name, loc) in with_id.items():
    m = ID_RE.match(cid)
    if not m:
        errors.append('%s: bad format' % cid)
        continue
    parts = cid.split('_')
    if parts[0] not in reg['areas']:
        errors.append('%s: unknown area code %s' % (cid, parts[0]))
    if not name.upper().startswith(parts[0] + ' '):
        errors.append('%s: area code does not match the name %r' % (cid, name))
    num = parts[-1] if parts[-1].isdigit() else None
    tcode = parts[-2] if num else parts[-1]
    kind = build_db.check_type(w, r, loc)
    want = TYPE_OF_KIND.get(kind)
    if tcode not in reg['types'] or tcode not in (want if isinstance(want, tuple) else (want,)):
        errors.append('%s: type code %s does not fit kind %s' % (cid, tcode, kind))
    if cid.isdigit():
        errors.append('%s: looks like a game hash' % cid)
    groups['_'.join(parts[:-1]) if num else cid].append(num)
for base, nums in groups.items():
    if None in nums and len(nums) > 1:
        errors.append('%s: used both with and without a number' % base)
    got = sorted(n for n in nums if n)
    if got and (any(len(n) != 2 for n in got) or [int(n) for n in got] != list(range(1, len(got) + 1))):
        errors.append('%s: numbers are not 01..%02d' % (base, len(got)))

# per classified area: coverage, hashes, randomizable, database up to date
totals = {}
for area in CLASSIFIED:
    rows = build_db.build(w, area)
    region_locs = [(r, n, l) for r in w.regions.values() if r.scene == area for n, l in r.locations.items()]
    for r, n, l in region_locs:
        if 'id' not in l:
            errors.append('%s: %s has no ID' % (area, n))
        if l.get('randomizable') not in RANDOMIZABLE:
            errors.append('%s: %s randomizable is %r' % (area, n, l.get('randomizable')))
    covered = {(sp, p['hash']) for r, n, l in region_locs for sc, sp, p in w.placements_of(r, l) if sc == area}
    for sid, spot in sorted(w.checks.get(area, {}).items()):
        for p in spot['placements']:
            if (sid, p['hash']) not in covered:
                errors.append('%s: object %s (%s, %s) has no check' % (area, sid, '/'.join(p['ages']), p['hash']))
    for row in rows:
        for o in row['object_id']:
            if not o['hash'].isdigit():
                errors.append('%s: object hash %r is not a game hash' % (row['unique_check_id'], o['hash']))
            if o['hash'] in with_id:
                errors.append('%s: game hash equals a check ID' % row['unique_check_id'])
        if row['check_type'] == 'gossip' and row['randomizable'] != 'no':
            errors.append('%s: gossip stone marked randomizable' % row['unique_check_id'])
    path = os.path.join(ROOT, 'data', 'db', area + '.json')
    if not os.path.exists(path) or json.load(open(path, encoding='utf-8')) != json.loads(json.dumps(rows)):
        errors.append('%s: data/db/%s.json is out of date (run tools/build_db.py %s)' % (area, area, area))
    c = collections.Counter
    totals[area] = {
        'objects found in the map files': len(w.checks.get(area, {})),
        'events with no map placement': sum(1 for x in rows if not x['object_id']),
        'checks (database entries)': len(rows),
        'classified': sum(1 for x in rows if x['check_type'] and x['randomizable'] in RANDOMIZABLE),
        'randomizable: yes': sum(1 for x in rows if x['randomizable'] == 'yes'),
        'randomizable: untested': sum(1 for x in rows if x['randomizable'] == 'untested'),
        'randomizable: no': sum(1 for x in rows if x['randomizable'] == 'no'),
        'verified in game': sum(1 for x in rows if x['verification_status'] == 'verified in game'),
        'not verified in game': sum(1 for x in rows if x['verification_status'] != 'verified in game'),
        'original contents unknown': sum(1 for x in rows if x['vanilla_contents']['value'] is None
                                         and x['check_type'] != 'gossip'),
        'by type': dict(sorted(c(x['check_type'] for x in rows).items())),
    }

# requirements (logic/requirements.py) agree with the search, for every check of the world
from logic.requirements import requirements  # noqa: E402
ALL_ITEMS = json.load(open(os.path.join(ROOT, 'data', 'items.json'), encoding='utf-8'))
BOOL_SETTINGS = [k for k, v in w.settings_defaults.items() if isinstance(v, bool)]


def _reaches(names, check, age):
    settings = {k: (k in names) for k in BOOL_SETTINGS}
    items = []
    for n in names:
        if n in settings:
            continue
        item, _, count = n.partition('*')
        items += [item] * int(count or 1)
    _, locs, _ = w.search(items, settings)
    return age in locs.get(check, ())


req = requirements(w)
req_checked = 0
for check, ages in req.items():
    for age, alts in ages.items():
        if alts is None:
            if _reaches(list(ALL_ITEMS) + BOOL_SETTINGS, check, age):
                errors.append('requirements: %s (%s) said impossible but the search reaches it' % (check, age))
            req_checked += 1
            continue
        for s in alts:
            if not _reaches(s, check, age):
                errors.append('requirements: %s (%s) %s does not reach it' % (check, age, s))
            for n in s:
                if _reaches([x for x in s if x != n], check, age):
                    errors.append('requirements: %s (%s) %s still reaches it without %s' % (check, age, s, n))
            req_checked += 1
print('requirements: %d checks x 2 ages, %d alternatives tried against the search' % (len(req), req_checked))

for area, t in totals.items():
    print('== %s' % area)
    for k, v in t.items():
        print('  %-34s %s' % (k, v))
print('IDs: %d active, %d retired, %d duplicates' % (len(active), len(retired),
                                                      sum(1 for e in errors if e.startswith('duplicate'))))
print('errors:', len(errors))
for e in errors:
    print('  ' + e)
sys.exit(1 if errors else 0)
