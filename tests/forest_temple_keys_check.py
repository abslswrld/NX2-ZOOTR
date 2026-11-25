"""Forest Temple keys test: the temple's small keys on other checks of the temple (phase 1, part 4).

Read from the game's own files: what makes an item a small key (its inventory settings), and where the temple's
five are. Then: the versions of the key the builder makes for a pot and a Gold Skulltula keep those settings and
give the key itself; the test build's placement (out/TEST_CHECKLIST.md) walked with the logic (every door opens
with the keys found before it), and placements that must fail; a whole build of it read back from the mod
folder. Only reads the game; the build goes to a temporary folder that is removed again.

    python tests/forest_temple_keys_check.py "C:\\...\\romfs"
"""
import contextlib
import glob
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import forest_temple_check as ft  # noqa: E402
import ground_items  # noqa: E402
from formats import zstd, byml, sarc  # noqa: E402
from logic.world import World  # noqa: E402

AREA = 'ForestTemple'
MAPS = ('Banc/ForestTemple/ForestTemple_Static.bcett.byml', 'Banc/ForestTemple/ForestTemple_Dynamic.bcett.byml')
KEY_ITEM, KEY_GROUND = 'Item_Dungeon_SmallKey', 'Obj_Dungeon_SmallKey'   # in a chest; lying on the ground
KEY_CHESTS = ('FT_ENTRANCE_CHEST', 'FT_FIRST_STALFOS_ROOM_CHEST', 'FT_WELL_CHEST', 'FT_FLOORMASTER_CHEST',
              'FT_JOELLE_CHEST')
FIXES = ('skippable_opening', 'magic_is_separate', 'bombs_without_bracelet', 'bombchus_without_bag',
         'forest_temple_bow_room_door')
# the test build of part 4: check -> item. The five keys on a Gold Skulltula, three pots and the Bow's chest;
# their five chests hold other items; the Bow is in the map's chest
SAMPLE = [
    ('FT_ENTRANCE_GS', KEY_GROUND),                       # key 1: the game's ground key, dropped by a skulltula
    ('FT_LOBBY_POT_01', KEY_GROUND),                      # key 2: the game's ground key, in a pot
    ('FT_FIRST_STALFOS_ROOM_POT_01', KEY_ITEM),           # key 3: the chest's key, in a pot (our ground version)
    ('FT_BLOCK_ROOM_POT_01', KEY_GROUND),                 # key 4
    ('FT_BOW_CHEST', KEY_ITEM),                           # key 5: in another chest (a big one)
    ('FT_ENTRANCE_CHEST', 'Item_Hammer'),
    ('FT_FIRST_STALFOS_ROOM_CHEST', 'Item_GlassTruth'),
    ('FT_WELL_CHEST', 'Item_Shield_Mirror'),
    ('FT_FLOORMASTER_CHEST', 'Item_Arrow_Fire'),
    ('FT_JOELLE_CHEST', 'Item_Arrow_Ice'),
    ('FT_EAST_COURTYARD_CHEST', 'Item_Range_Bow'),
    ('FT_LOBBY_POT_02', 'Item_HoverBoot'),                # the height fix: the Hover Boots from a pot
    ('FT_LOBBY_POT_03', 'Item_HeavyBoot'),                # and the Iron Boots
]
LOGIC_NAME = dict(ft.LOGIC_NAME, **{KEY_GROUND: ft.KEY})


def check(name, ok, detail=''):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED %s' % (detail,)))
    return ok


def refused(fn, *args):
    try:
        fn(*args)
    except SystemExit as e:
        return str(e)
    return None


def tree(folder):
    return sorted(os.path.relpath(f, folder).replace(os.sep, '/')
                  for f in glob.glob(os.path.join(folder, '**', '*'), recursive=True) if os.path.isfile(f))


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    plain = lambda path: zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)   # noqa: E731
    w = World()
    good = True
    locs = {l['id']: (r, name, l) for r in w.regions.values() if r.scene == AREA
            for name, l in r.locations.items() if l.get('id')}
    spots = w.checks[AREA]
    name_to_id = {name: cid for cid, (_, name, _) in locs.items()}
    game_item = {l['id']: spots[l['spot']]['item'] for _, _, l in locs.values() if 'spot' in l}

    # ---- the game's files: what a small key is
    pouch = {str(r['__RowId']): r for r in byml.loads(plain(ground_items.table_path('PouchActorInfo'))).root}
    is_key = lambda row: row.get('PouchSpecialDeal') == 'SmallKey' and bool(row.get('PouchStockable'))   # noqa: E731
    good &= check('the game: the chest\'s key (%s) and the ground key (%s) are small keys by their inventory '
                  'settings (PouchSpecialDeal SmallKey, counted)' % (KEY_ITEM, KEY_GROUND),
                  is_key(pouch[KEY_ITEM]) and is_key(pouch[KEY_GROUND]))
    good &= check('  the temple has five, in five chests; no other check of the temple gives one',
                  sorted(c for c, i in game_item.items() if i == KEY_ITEM) == sorted(KEY_CHESTS)
                  and not any(i == KEY_GROUND for i in game_item.values()))

    # ---- the logic: a placement walked with the items where it puts them
    def walk(placed, start=ft.ARRIVE):
        """collect the temple's checks in rounds, taking what `placed` (else the game) puts on each; returns
        (checks got, state)"""
        items, got = list(start), set()
        while True:
            _, reach, state = w.search(items)
            new = {name_to_id[n] for n in reach if n in name_to_id} - got
            if not new:
                return got, state
            for cid in sorted(new):
                got.add(cid)
                name = LOGIC_NAME.get(placed.get(cid, game_item.get(cid)))
                if name:
                    items.append(name)

    sample = dict(SAMPLE)
    keys = sorted(c for c, i in sample.items() if i in (KEY_ITEM, KEY_GROUND))
    good &= check('the test placement: five keys, none in a chest that holds one in the game; those five chests '
                  'hold other items; no item but the key is placed twice',
                  len(keys) == 5 and not set(keys) & set(KEY_CHESTS) and set(KEY_CHESTS) <= set(sample)
                  and len({i for i in sample.values() if i not in (KEY_ITEM, KEY_GROUND)})
                  == len(sample) - 5, keys)
    got, state = walk(sample)
    good &= check('  walked with the logic: all 47 checks, five keys, Phantom Ganon beaten',
                  len(got) == 47 and state.count(ft.KEY) == 5 and state.count('Forest Temple Clear') == 1,
                  (len(got), state.count(ft.KEY)))
    order = []
    for n in range(1, 6):                                 # the keys in hand when each locked door is reached
        _, reach, st = w.search(ft.ARRIVE + [ft.KEY] * (n - 1))
        here = {name_to_id[x] for x in reach if x in name_to_id}
        order.append(sum(1 for c in keys if c in here))
    good &= check('  every locked door is reached with enough keys found before it (keys reachable with 0..4 '
                  'in hand: %s)' % order, all(have >= n for n, have in enumerate(order, 1)), order)
    late = dict(sample, FT_ENTRANCE_GS='Item_Hammer', FT_ENTRANCE_CHEST='Item_Boomerang',
                FT_LOBBY_POT_04=KEY_GROUND)
    got, state = walk(late)
    good &= check('a placement with no key in the first room is stuck at the first door (2 checks, 0 keys)',
                  got == {'FT_ENTRANCE_CHEST', 'FT_ENTRANCE_GS'} and state.count(ft.KEY) == 0, sorted(got))
    behind = dict(sample, FT_BLOCK_ROOM_POT_01='Item_Boomerang', FT_FROZEN_EYE_SWITCH_ROOM_POT_01=KEY_GROUND)
    got, state = walk(behind)
    good &= check('a placement with the fifth key behind the fifth locked door stops at that door: 4 keys, no boss',
                  state.count(ft.KEY) == 4 and not state.count('Forest Temple Clear')
                  and 'FT_BETH_CHEST' in got and 'FT_FROZEN_EYE_SWITCH_ROOM_POT_01' not in got,
                  (state.count(ft.KEY), len(got)))
    got, state = walk({})
    good &= check('the game\'s own placement still walks: 47 checks, five keys',
                  len(got) == 47 and state.count(ft.KEY) == 5)

    # ---- a whole build: the test sample
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *args):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(args))
            return out.getvalue(), os.path.join(tmp, name, 'romfs')

        fixes = [x for f in FIXES for x in ('--fix', f)]
        said, folder = run('keys', *fixes, *['%s=%s' % x for x in SAMPLE])
        files = tree(folder)
        read = lambda f: zstd.decompress(open(os.path.join(folder, *f.split('/')), 'rb').read(), d)   # noqa: E731
        good &= check('the sample builds with the standing fixes (%d placements, %d files)'
                      % (len(SAMPLE), len(files)), all(m + '.zs' in files for m in MAPS)
                      and build_mod.BOW_ROOM_LOGIC in files, files[:5])
        back = {str(int(a['Hash'])): a for m in MAPS if m + '.zs' in files
                for a in byml.loads(read(m + '.zs')).root['Actors']}
        game = {str(int(a['Hash'])): a for m in MAPS for a in byml.loads(plain(m)).root['Actors']}
        held, changed = {}, set()
        for cid, _ in SAMPLE:
            p, = spots[locs[cid][2]['spot']]['placements']
            changed.add(p['hash'])
            held[cid] = dict(back[p['hash']].get('Dynamic') or {}).get('Drop__DropActor')
        versions = sorted({held[c] for c in keys})
        good &= check('  read back: the five keys are where the placement puts them (%s)' % ', '.join(versions),
                      held['FT_BOW_CHEST'] == KEY_ITEM
                      and all((held[c] or '').startswith('Obj_NX2') and held[c].endswith('Dungeon_SmallKey')
                              for c in keys if c != 'FT_BOW_CHEST'), held)
        good &= check('  the five chests that held a key hold their new item; every other object of both maps '
                      'is as the game has it',
                      all(held[c] == sample[c] for c in KEY_CHESTS) and len(back) == len(game)
                      and all(back[h] == game[h] for h in back if h not in changed))
        rows = {str(r['__RowId']): r for r in byml.loads(read(ground_items.table_path('PouchActorInfo') + '.zs')).root}
        own = [v for v in versions if v != KEY_ITEM]
        same = lambda v: {k: x for k, x in rows[v].items() if k != '__RowId'} == \
            {k: x for k, x in pouch[KEY_ITEM].items() if k != '__RowId'}   # noqa: E731
        good &= check('  each key version the builder made (%d) is a small key by the same inventory settings '
                      'as the game\'s' % len(own), len(own) >= 2 and all(v in rows and same(v) for v in own), own)

        def pouch_actor(version):
            """the item a version goes into the inventory as: PouchActor of its item settings, its own or the
            one it inherits"""
            fs = sarc.Sarc.read(read(ground_items.pack_path(version) + '.zs')).files
            path = 'Component/PouchContentParam/%s.game__component__PouchContentParam.bgyml' % version
            while path in fs:
                root = byml.loads(fs[path]).root
                if 'PouchActor' in root:
                    return str(root['PouchActor'])
                path = str(root.get('$parent', '')).replace('Work/', '').replace('.gyml', '.bgyml')
            return None
        good &= check('  and goes into the inventory as the key itself (%s)' % KEY_ITEM,
                      all((pouch_actor(v) or '').endswith('/%s.engine__actor__ActorParam.gyml' % KEY_ITEM)
                          for v in own), {v: pouch_actor(v) for v in own})
        good &= check('  the boots lie higher from a pot (the height fix): both are raised in the build\'s report',
                      'Item_HoverBoot: lies 0.190 higher' in said and 'Item_HeavyBoot: lies 0.197 higher' in said)
        said2, _ = run('bosschest', 'FT_BOSS_KEY_CHEST=%s' % KEY_ITEM)
        good &= check('a key in the boss key\'s chest: accepted since part 7, its own opening event removed',
                      'special opening event ForesetTemple_GetBossKey removed' in said2, said2[-300:])

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
