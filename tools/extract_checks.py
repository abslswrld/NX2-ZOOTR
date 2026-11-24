"""List every check placed in an area, straight from the game's map files (Banc/<Area>/*.bcett.byml.zs).

    python tools/extract_checks.py "<romfs>" KokiriForest [more areas...]

Writes data/checks/<Area>.json. Placements at the same spot (same kind, same place: the child and adult
versions of a pot, the before/after versions of a shop shelf) are grouped into one spot, keyed by a short
id ('chest@-82.6,33.0'). Each spot records:
    kind      chest / skulltula / scrub / shop / pot / freestanding / rock / boulder / bush / gossip (hints only)
    item      what the base game puts there
    ages      'child', 'adult' or both (which map version has it)
    pos       x, y, z in the map (for naming, maps and the tracker)
    placements  the game's own placement hash(es), with the map file(s) and the flags (Presence) of each
    night_only, params ...
Names are left empty: they are given in data/world/<Area>.json, where the check is placed in a region.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from formats import zstd, byml  # noqa: E402


# Solid bushes. The game names them Obj_Plant_Grass_*: _A_01 and _A_03 use a bush model about 1 x 0.9 units
# (ActorInfo ModelAabb); _A_04 is a flat grass tuft (0.2 high), foliage, left out.
BUSHES = {'Obj_Plant_Grass_A_01', 'Obj_Plant_Grass_A_03'}


def kind_of(gyaml):
    g = gyaml
    if g.startswith('Obj_TBox') and not g.startswith('Obj_TBoxPedestal'):
        return 'chest'                         # (a pedestal is the stand some chests rise on, not a chest)
    if g == 'Enemy_Skulltula_Gold':
        return 'skulltula'
    if g == 'Enemy_Scrub_Business':
        return 'scrub'
    if g.startswith('Shop_') and not g.startswith('Shop_Board'):
        return 'shop'
    if g.startswith('Obj_Pot'):
        if g.endswith('_Respawn'):
            return None                        # a refill pot that comes back (arrows in the Forest Temple's
                                               # Bow room): never a check
        return 'pot'
    if g.startswith(('Obj_Rupee_', 'Obj_Heart')) or g in ('Obj_HeartPiece', 'Obj_Heart_Piece'):
        return 'freestanding'
    if g.startswith('Obj_GossipStone'):
        return 'gossip'
    if g.startswith('Obj_LiftRock'):
        return 'rock'
    if g.startswith('Obj_BrokenRock'):
        return 'boulder'                       # breakable with explosives / hammer
    if g in BUSHES:
        return 'bush'
    return None


def _plain(v):
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_plain(x) for x in v]
    if isinstance(v, float):
        return round(v, 3)
    if isinstance(v, int) and not isinstance(v, bool):
        return int(v)
    return v


def extract(romfs, area, dicts):
    folder = os.path.join(romfs, 'Banc', area)
    spots = {}
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith('.bcett.byml.zs') or not fn.startswith(area + '_'):
            continue
        age = 'child' if '_Child_' in fn else 'adult' if '_Adult_' in fn else None
        doc = byml.loads(zstd.decompress(open(os.path.join(folder, fn), 'rb').read(), dicts)).root
        for a in doc.get('Actors', []):
            k = kind_of(a['Gyaml'])
            if not k:
                continue
            dyn = _plain(dict(a.get('Dynamic') or {}))
            pos = [round(x, 1) for x in a.get('Translate', [0, 0, 0])]
            item = (dyn.get('Drop__DropActor') or dyn.get('ScrubBusiness_ShopItemActorName0')
                    or (a['Gyaml'][5:] if k == 'shop' else a['Gyaml'] if k == 'freestanding' else None))
            sid = '%s@%.1f,%.1f' % (k, round(pos[0] * 2) / 2, round(pos[2] * 2) / 2)
            if k in ('rock', 'boulder', 'bush'):           # these sit close together: keep them apart
                sid = '%s@%.1f,%.1f' % (k, pos[0], pos[2])
            if k == 'shop':
                sid = 'shop#%s' % dyn.get('ShopItemIndex', a['Gyaml'])
            spot = spots.setdefault(sid, {'kind': k, 'item': item, 'ages': [], 'pos': pos, 'placements': []})
            h = str(int(a['Hash']))
            pl = next((p for p in spot['placements'] if p['hash'] == h), None)
            if pl is None:
                pl = {'hash': h, 'actor': a['Gyaml'], 'ages': [], 'files': []}
                if a.get('Name'):
                    pl['name_in_map'] = a['Name']
                if a.get('Presence'):
                    pl['appears_if'] = _plain(dict(a['Presence']))
                if dyn:
                    pl['params'] = dyn
                spot['placements'].append(pl)
            for lst, v in ((pl['ages'], age), (spot['ages'], age), (pl['files'], fn)):
                if v and v not in lst:
                    lst.append(v)
            if dyn.get('Enemy_Skulltula_Gold_Nocturnal'):
                spot['night_only'] = True
    for spot in spots.values():
        spot['ages'].sort()
    return dict(sorted(spots.items()))


def main(argv):
    romfs, areas = argv[0], argv[1:]
    dicts = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    os.makedirs(os.path.join(ROOT, 'data', 'checks'), exist_ok=True)
    for area in areas:
        checks = extract(romfs, area, dicts)
        out = os.path.join(ROOT, 'data', 'checks', area + '.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(checks, f, indent=1, ensure_ascii=False)
        kinds = {}
        for c in checks.values():  # spots
            kinds[c['kind']] = kinds.get(c['kind'], 0) + 1
        print(area, len(checks), 'checks', kinds, '->', out)


if __name__ == '__main__':
    main(sys.argv[1:])
