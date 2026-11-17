"""Build the check database of an area: one row per check, with the classification fields, from the data
that already exists (data/world/<Area>.json for names, regions, rules, IDs and randomizability;
data/checks/<Area>.json for the game's placement hashes and original contents).

    python tools/build_db.py KokiriForest [more areas...]

Writes data/db/<Area>.json. That file is generated: never edit it by hand, edit data/world/ instead and
build again. Only checks that have a permanent ID ("id") are included.

Row fields
    unique_check_id      our permanent ID (data/ids.json, README "Check IDs")
    check_name           display name
    region               logic region
    area                 the game's map (Banc folder) of the region
    check_type           chest, skulltula, scrub, shop, pot, freestanding, rock, boulder, bush, gift, gossip
    object_id            the game's own placement(s): [{scene, spot, hash, actor, files, ages}]; [] for an
                         event with no map placement (see object_id_note)
    vanilla_contents     {"value": item or null, "source": where it comes from, "note": why it is null}
    randomizable         "yes" (changed in game and it worked), "no", or "untested"; randomizable_note
    requirements         what it takes to get the check from the start of the game, for a child and an
                         adult: a list of alternatives (any one is enough), each a list of items and settings
                         that must be on; [[]] = nothing needed, null = impossible at that age
                         (logic/requirements.py)
    requirements_note    when the answer still goes through a 'not mapped yet' placeholder region
    check_rule           the check's own rule: only what is needed once in its region ("True" = nothing more)
    verification_status  "verified in game" or "not verified in game" (the region's "verified" flag)
    notes                the check's own note, if any
    missable             only when the check can go away for good during the game (e.g. a rock the level
                         removes after a dungeon): why; nothing required may be placed there
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from logic.world import World  # noqa: E402
from logic.requirements import requirements, placeholder_ages  # noqa: E402


def check_type(world, region, loc):
    if loc.get('kind'):
        return loc['kind']
    sps = world.spots_of(region, loc)
    if sps:
        sc, sp = sps[0]
        return world.checks[sc][sp]['kind']
    return None


def vanilla(world, region, loc, ctype):
    sps = world.spots_of(region, loc)
    if ctype == 'gossip':
        return {'value': None, 'source': None, 'note': 'hint stone, gives no item'}
    if ctype == 'skulltula':
        return {'value': 'GoldSkulltulaToken', 'source': 'check kind (not stored in the map data)', 'note': None}
    if not sps and loc.get('gift'):
        g = loc['gift']
        return {'value': g['item'], 'source': 'event flow %s, %s' % (g['flow'], g['event']), 'note': None}
    if not sps:
        return {'value': None, 'source': None,
                'note': 'event with no map placement; contents not found in the game data yet'}
    spot = world.checks[sps[0][0]][sps[0][1]]
    if spot.get('item'):
        return {'value': spot['item'], 'source': 'map data', 'note': None}
    tables = sorted({p.get('params', {}).get('Drop__DropTable') for p in spot['placements']} - {None})
    if tables:
        return {'value': None, 'source': None, 'note': 'random drop (%s)' % ', '.join(tables)}
    if ctype in ('rock', 'bush', 'boulder'):
        return {'value': None, 'source': None,
                'note': 'probably a random drop (rupees, hearts...), not confirmed in game; '
                        'no item or drop table in the map data'}
    return {'value': None, 'source': None, 'note': 'no item or drop table in the map data'}


def objects(world, region, loc):
    out = []
    for sc, sp, p in world.placements_of(region, loc):
        out.append({'scene': sc, 'spot': sp, 'hash': p['hash'], 'actor': p['actor'],
                    'files': p['files'], 'ages': p['ages']})
    return out


def build(world, area):
    rows = []
    req = requirements(world)
    ph = placeholder_ages(world)
    for r in world.regions.values():
        if r.scene != area:
            continue
        for name, loc in r.locations.items():
            if 'id' not in loc:
                continue
            ctype = check_type(world, r, loc)
            row = {
                'unique_check_id': loc['id'],
                'check_name': name,
                'region': r.name,
                'area': r.scene,
                'check_type': ctype,
                'object_id': objects(world, r, loc),
                'vanilla_contents': vanilla(world, r, loc, ctype),
                'randomizable': loc.get('randomizable'),
                'randomizable_note': loc.get('randomizable_note'),
                'requirements': req[name],
                'check_rule': str(loc.get('rule', True)),
                'verification_status': 'verified in game' if r.verified else 'not verified in game',
            }
            if ph.get(name):
                row['requirements_note'] = ('the %s answer still goes through placeholder regions (not mapped yet): '
                                            'it will change as the world is mapped' % ' and '.join(ph[name]))
            if not row['object_id']:
                row['object_id_note'] = 'no map placement (an event); its ID in the game is still to be found'
            if loc.get('note'):
                row['notes'] = loc['note']
            if loc.get('missable'):
                row['missable'] = loc['missable']
            rows.append(row)
    return sorted(rows, key=lambda x: x['unique_check_id'])


def main(areas):
    w = World()
    os.makedirs(os.path.join(ROOT, 'data', 'db'), exist_ok=True)
    for area in areas:
        rows = build(w, area)
        out = os.path.join(ROOT, 'data', 'db', area + '.json')
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(rows, f, indent=1, ensure_ascii=False)
            f.write('\n')
        print(area, len(rows), 'checks ->', out)


if __name__ == '__main__':
    main(sys.argv[1:])
