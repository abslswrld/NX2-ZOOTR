"""Checking chest test: what tools/build_mod.py does with the game's checking chests (Obj_TBox_A_06) and with
the progressive pairs, on the game's own files. Reads only; writes nothing.

    python tests/chest_check.py "C:\\...\\romfs"
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import ground_items  # noqa: E402
from formats import zstd, byml, restbl, sarc  # noqa: E402

MIDO = ('Banc/KokiriForest/KokiriForest_Child_Dynamic.bcett.byml',
        'Banc/KokiriForest/KokiriForest_Adult_Dynamic.bcett.byml')
MIDO_CHESTS = ('12786193094758345086', '10831981390482426294')      # KF_MIDO_CHEST_01, _02 (top)
MIDO_BOTTOM = ('4555665598794293658', '9725242744547055868')        # KF_MIDO_CHEST_03, _04
PAIR = ('Item_Scale_Silver', 'Item_Scale_Gold')
HOOKSHOTS = ('Item_Hookshot', 'Item_Longshot')
OCARINAS = ('Item_Ocarina_Fairy', 'Item_Ocarina_Time')
# the game's own chests that give the Hookshot and the Longshot: (map, placement, item)
GAME_CHESTS = (('Banc/Graveyard/Graveyard_Adult_Static.bcett.byml', '16041366920820397198', 'Item_Hookshot'),
               ('Banc/WaterTemple/WaterTemple_Static.bcett.byml', '18059711820131847165', 'Item_Longshot'))
GAME_DATA = 'GameData/GameDataList.Product.110.byml'
# the names the game's own checking chests look for, and the inventory item each stands for
STAND_INS = {'TBox_Shield_Deku': 'Weapon_Shield_Deku', 'TBox_Shield_Hylian': 'Weapon_Shield_Hylian',
             'Item_Range_Bow': 'Weapon_Range_Bow'}


def name_hash(name):
    """the hash a game data entry is stored under (MurmurHash3, 32 bits, seed 0)"""
    key, h = name.encode('ascii'), 0
    rot = lambda x, r: ((x << r) | (x >> (32 - r))) & 0xffffffff   # noqa: E731
    for i in range(0, len(key), 4):
        k = int.from_bytes(key[i:i + 4], 'little')
        h ^= rot(k * 0xcc9e2d51 & 0xffffffff, 15) * 0x1b873593 & 0xffffffff
        if i + 4 <= len(key):
            h = (rot(h, 13) * 5 + 0xe6546b64) & 0xffffffff
    h ^= len(key)
    h = (h ^ h >> 16) * 0x85ebca6b & 0xffffffff
    h = (h ^ h >> 13) * 0xc2b2ae35 & 0xffffffff
    return h ^ h >> 16


def check(name, ok):
    print('%-74s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    rd = lambda path: zstd.decompress(open(path, 'rb').read(), d)   # noqa: E731
    table = restbl.Restbl.read(rd(os.path.join(romfs, build_mod.RESTBL_PATH)))
    good = True

    # every game map: the size rule, and its checking chests given an item
    rule, chests, plain = True, 0, 0
    for f in sorted(glob.glob(os.path.join(romfs, 'Banc', '**', '*.bcett.byml.zs'), recursive=True)):
        rel = os.path.relpath(f, romfs).replace(os.sep, '/')[:-3]
        old = rd(f)
        rule &= table.get(rel) == build_mod.map_entry(len(old))
        before = {str(int(a['Hash'])): a for a in byml.loads(old).root.get('Actors', [])}
        mine = [h for h, a in before.items() if a['Gyaml'] in build_mod.PLAIN_CHEST]
        if not mine:
            continue
        chests += len(mine)
        new, found, _ = build_mod.patch_file(old, {h: ('TEST', 'Item_Boomerang', None, 'chest') for h in mine})
        for a in byml.loads(new).root['Actors']:
            h = str(int(a['Hash']))
            want = dict(before[h])
            if h in mine:
                want['Gyaml'] = build_mod.PLAIN_CHEST[want['Gyaml']]
                want['Dynamic'] = dict({k: v for k, v in want['Dynamic'].items()
                                        if k not in build_mod.CHECK_SETTINGS}, Drop__DropActor='Item_Boomerang')
                plain += a == want
            elif a != want:
                plain = -1000
    good &= check('map files: every size entry is the length rounded up to 32, plus 264', rule)
    good &= check('the game has 9 checking chests', chests == 9)
    good &= check('given an item, each becomes an ordinary chest without its check; nothing else changes',
                  plain == chests)

    # a progressive pair in two of Mido's chests
    old = rd(os.path.join(romfs, *MIDO[0].split('/')) + '.zs')
    before = {str(int(a['Hash'])): a for a in byml.loads(old).root['Actors']}
    new, found, _ = build_mod.patch_file(
        old, {h: ('TEST', PAIR[0], None, 'chest') for h in MIDO_CHESTS}, {h: PAIR for h in MIDO_CHESTS})
    ok = True
    for a in byml.loads(new).root['Actors']:
        h = str(int(a['Hash']))
        want = dict(before[h])
        if h in MIDO_CHESTS:
            want['Gyaml'] = 'Obj_TBox_A_06'
            want['Dynamic'] = dict(want['Dynamic'], Drop__DropActor=PAIR[0], Drop__CheckActor=PAIR[0],
                                   Drop__DropActor_Substitute=PAIR[1])
        ok &= a == want
    good &= check('progressive pair: two of Mido\'s chests become checking chests; nothing else changes', ok)
    good &= check('progressive pair: the same settings as the game\'s own checking chests',
                  all(set(a['Dynamic']) - {'GetEventName'} == {'Drop__CheckActor', 'Drop__DropActor',
                                                               'Drop__DropActor_Substitute'}
                      for a in byml.loads(new).root['Actors'] if str(int(a['Hash'])) in MIDO_CHESTS))
    try:
        build_mod.patch_file(old, {'16757992849254467386': ('TEST', PAIR[0], None, 'chest')},
                             {'16757992849254467386': PAIR})
        refused = False
    except SystemExit:
        refused = True
    good &= check('progressive pair: refused in a big chest (the Kokiri Sword chest)', refused)

    # the pairs: their names, and how a chest holds them
    plain = lambda path: rd(os.path.join(romfs, *path.split('/')) + '.zs')   # noqa: E731

    def in_chest(item):                                # as build_mod.main's in_chest
        if ground_items.kind_of(plain, item) == 'equipment':
            return ground_items.ground_name(item, 'held')
        return item

    good &= check('the pairs: scales, hookshots, ocarinas',
                  build_mod.PROGRESSIVE_PAIRS == {PAIR, HOOKSHOTS, OCARINAS})
    rows = {t: {r['__RowId']: r for r in byml.loads(plain(ground_items.table_path(t))).root}
            for t in ground_items.TABLES}
    data = byml.loads(plain(GAME_DATA)).root['Data']
    saved = {kind: {int(e['Hash']) for e in data[kind]} for kind in ('Bool', 'Int')}
    names = sorted(x for pair in build_mod.PROGRESSIVE_PAIRS for x in pair)
    good &= check('every item of a pair is an inventory item under its own name (PouchActorInfo, ActorName)',
                  all(x in rows['PouchActorInfo'] and rows['ActorInfo'][x]['ActorName'] == x for x in names))
    good &= check('  and is saved under it (IsGet.<name>, PouchData.<name>.StockNum)',
                  all(name_hash('IsGet.' + x) in saved['Bool']
                      and name_hash('PouchData.%s.StockNum' % x) in saved['Int'] for x in names))
    # the names the game's checking chests look for are not saved names: the inventory question takes the
    # actor a chest gives and finds the item it stands for (its ActorName)
    good &= check("the game's own checks name a chest's actor, found by the item it stands for",
                  all(rows['ActorInfo'][a]['ActorName'] == item and name_hash('IsGet.' + a) not in saved['Bool']
                      and name_hash('IsGet.' + item) in saved['Bool'] for a, item in STAND_INS.items()))
    ok = True
    for path, h, item in GAME_CHESTS:
        actors = {str(int(a['Hash'])): a for a in byml.loads(plain(path)).root['Actors']}
        ok &= h in actors and actors[h]['Gyaml'].startswith('Obj_TBox') \
            and actors[h]['Dynamic']['Drop__DropActor'] == item
    good &= check("the game's own chests give Item_Hookshot (Graveyard) and Item_Longshot (Water Temple)", ok)
    good &= check('scales and hookshots are held up as they are; ocarinas as held-up versions',
                  [in_chest(x) for x in PAIR + HOOKSHOTS + OCARINAS]
                  == list(PAIR + HOOKSHOTS) + ['Item_NX2_Ocarina_Fairy', 'Item_NX2_Ocarina_Time'])
    good &= check('pair_check: look for First by its own name, hold Second as a chest gives it',
                  build_mod.pair_check(HOOKSHOTS, in_chest) == ('Item_Hookshot', 'Item_Longshot')
                  and build_mod.pair_check(OCARINAS, in_chest) == ('Item_Ocarina_Fairy', 'Item_NX2_Ocarina_Time'))

    # a held-up ocarina as a checking chest's item: an item event actor like the Boomerang's, that knows the
    # get-demo command, named and put in the inventory as the ocarina
    ok = True
    for item in OCARINAS:
        name, pack, new_inner, new_rows, loose = ground_items.build(
            item, plain, lambda t: list(rows[t].values()),
            lambda project: os.path.exists(os.path.join(romfs, 'Model', project + '.anim.bfres.zs')), 'held')
        files = sarc.Sarc.read(pack).files
        comp = ground_items.resolved_components(files, name)
        pouch = byml.loads(files[ground_items.pouch_param_path(name)]).root
        ok &= name == in_chest(item) and not loose
        ok &= 'Actor/Item_EventObject_Base.engine__actor__ActorParam.bgyml' in files
        ok &= comp['ActorNameRef'] == '?ActorSystem/ActorName/%s.engine__actor__ActorName.bgyml' % item
        ok &= ground_items.GET_DEMO in plain(comp['ASRef'][1:])
        ok &= dict(pouch) == {'$parent': 'Work/' + ground_items.pouch_param_path(item)[:-len('.bgyml')] + '.gyml',
                              'PouchActor': 'Work/' + ground_items.ap_path(item)[:-len('.bgyml')] + '.gyml'}
        ok &= new_rows['ActorInfo']['ActorName'] == item and new_rows['ActorInfo']['__RowId'] == name
        ok &= dict(new_rows['PouchActorInfo'], __RowId=item) == dict(rows['PouchActorInfo'][item])
        ok &= name_hash('IsGet.' + name) not in saved['Bool']      # not a saved name: found as the ocarina
    good &= check('held-up ocarinas: item event actors with the get demo, standing for the ocarina', ok)

    # the two new pairs in Mido's four chests, at both ages; nothing else changes
    ok = same = True
    for path in MIDO:
        old = plain(path)
        before = {str(int(a['Hash'])): a for a in byml.loads(old).root['Actors']}
        pairs = dict({h: HOOKSHOTS for h in MIDO_CHESTS}, **{h: OCARINAS for h in MIDO_BOTTOM})
        new, found, _ = build_mod.patch_file(
            old, {h: ('TEST', in_chest(pair[0]), None, 'chest') for h, pair in pairs.items()},
            {h: build_mod.pair_check(pair, in_chest) for h, pair in pairs.items()})
        ok &= set(pairs) <= set(before) and len(byml.loads(new).root['Actors']) == len(before)
        for a in byml.loads(new).root['Actors']:
            h = str(int(a['Hash']))
            want = dict(before[h])
            if h in pairs:
                first, second = pairs[h]
                want['Gyaml'] = 'Obj_TBox_A_06'
                want['Dynamic'] = dict(want['Dynamic'], Drop__DropActor=in_chest(first), Drop__CheckActor=first,
                                       Drop__DropActor_Substitute=in_chest(second))
                same &= set(a['Dynamic']) - {'GetEventName'} == {'Drop__CheckActor', 'Drop__DropActor',
                                                                 'Drop__DropActor_Substitute'}
            ok &= a == want
    good &= check("hookshots in Mido's top chests, ocarinas in the bottom ones, both ages; nothing else changes",
                  ok)
    good &= check("  with the same settings as the game's own checking chests", same)

    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
