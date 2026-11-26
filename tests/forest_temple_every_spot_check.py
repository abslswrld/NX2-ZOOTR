"""Forest Temple, every spot (decision 27: "a build script for every spot"; phase 1).

One build puts an item on every one of the temple's 47 checks, a different item on each, and every check is
read back from the mod folder: the right object of the map holds the right thing (a chest its item, a pot its
one-time version, a Gold Skulltula its token-built version, the boss's heart its ground version, the Medallion's
cutscene its item), every new actor those name was written with its table row, nothing else of the two maps
changed, and every file of the build has its entry in the resource size table. It needs no play time: what a
spot does in game is tested once for each kind of check and for each unusual spot (CHANGELOG.md).

Also read from the game's files, because the in-game test goes by it: which of the temple's 12 chests name no
contents, and which only appear after a fight, a switch or a Poe.

Only reads the game; the build goes to a temporary folder that is removed again.

    python tests/forest_temple_every_spot_check.py "C:\\...\\romfs"
"""
import contextlib
import io
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import dungeon_items  # noqa: E402
import dungeon_keys  # noqa: E402
import ground_items  # noqa: E402
import once_items  # noqa: E402
from formats import zstd, byml, sarc, evfl, restbl  # noqa: E402
from logic.world import World  # noqa: E402

AREA = 'ForestTemple'
MAPS = ('Banc/ForestTemple/ForestTemple_Static.bcett.byml', 'Banc/ForestTemple/ForestTemple_Dynamic.bcett.byml')
KEY, BOSS_KEY = 'Item_Dungeon_SmallKey@' + AREA, 'Item_Dungeon_BossKey@' + AREA
# check -> item: a different item on each of the 47. No trade quest item, no Deku Nuts or Sticks, no small bag,
# and of an upgrade family only its first level (CLAUDE.md)
PLAN = {
    # the 12 chests
    'FT_ENTRANCE_CHEST': 'Item_Range_Bow', 'FT_FIRST_STALFOS_ROOM_CHEST': 'Item_Hookshot',
    'FT_EAST_COURTYARD_CHEST': 'Item_Boomerang', 'FT_BLOCK_ROOM_EYE_SWITCH_CHEST': 'Item_Hammer',
    'FT_BOW_CHEST': 'Item_Shield_Mirror', 'FT_BETH_CHEST': 'Item_GlassTruth', 'FT_JOELLE_CHEST': 'Item_HeavyBoot',
    'FT_FLOORMASTER_CHEST': 'Item_HoverBoot', 'FT_WELL_CHEST': 'Item_Scale_Silver',
    'FT_FALLING_CEILING_ROOM_CHEST': 'Item_Arrow_Fire', 'FT_BASEMENT_CHEST': 'Item_Arrow_Ice',
    'FT_BOSS_KEY_CHEST': 'Item_Arrow_Light',
    # the 5 Gold Skulltulas
    'FT_ENTRANCE_GS': 'Item_DinFire', 'FT_LOBBY_GS': 'Item_FaroreWind', 'FT_EAST_COURTYARD_GS': 'Item_NayruLove',
    'FT_WEST_COURTYARD_GS': 'Obj_Heart_Piece', 'FT_BASEMENT_GS': 'Item_Bottle',
    # the boss's heart and the Medallion's cutscene
    'FT_PHANTOM_GANON_HEART_CONTAINER_ITEM': 'Item_Gauntlet_Goron', 'FT_FOREST_MEDALLION_GIFT': 'Item_MagicBean',
    # the 28 pots
    'FT_LOBBY_POT_01': 'Item_Stone_Forest', 'FT_LOBBY_POT_02': 'Item_Stone_Fire',
    'FT_LOBBY_POT_03': 'Item_Stone_Water', 'FT_LOBBY_POT_04': 'Item_Medal_Light',
    'FT_LOBBY_POT_05': 'Item_Medal_Forest', 'FT_LOBBY_POT_06': 'Item_Medal_Fire',
    'FT_FIRST_STALFOS_ROOM_POT_01': 'Item_Medal_Water', 'FT_FIRST_STALFOS_ROOM_POT_02': 'Item_Medal_Shadow',
    'FT_BLOCK_ROOM_POT_01': 'Item_Medal_Spirit', 'FT_BLOCK_ROOM_POT_02': 'Item_AgonyStone',
    'FT_BLOCK_ROOM_POT_03': 'Item_Token_Gerudo', 'FT_WELL_POT_01': 'Item_Bottle_Letter',
    'FT_WELL_POT_02': 'Item_Wallet_Medium', 'FT_BOW_ROOM_POT_01': 'Item_BombBag_Small',
    'FT_BOW_ROOM_POT_02': 'Item_Range_SlingShot', 'FT_BOW_ROOM_POT_03': 'Item_StickBag_Medium',
    'FT_BOW_ROOM_POT_04': 'Item_NutBag_Medium', 'FT_BETH_ROOM_POT_01': 'Item_FairyBless_MP',
    'FT_BETH_ROOM_POT_02': 'Item_Ocarina_Fairy', 'FT_BETH_ROOM_POT_03': 'Item_Sword_Kokiri',
    'FT_AMY_ROOM_POT_01': 'Item_BombchuBundle_Small', 'FT_AMY_ROOM_POT_02': 'Item_FairyBless_DefenseDouble',
    'FT_FROZEN_EYE_SWITCH_ROOM_POT_01': 'Obj_Rupee_Gold', 'FT_FROZEN_EYE_SWITCH_ROOM_POT_02': 'Obj_Rupee_Purple',
    'FT_BASEMENT_POT_01': 'Obj_Shield_Hylian', 'FT_BASEMENT_POT_02': 'Obj_Shield_Deku',
    'FT_BASEMENT_POT_03': KEY, 'FT_BASEMENT_POT_04': BOSS_KEY,
}
# the temple's chests, as the game's files have them (the in-game test goes by this)
NAMES_NOTHING = ['FT_FALLING_CEILING_ROOM_CHEST']
# check -> (the module of the room's logic that makes the chest appear, the flag it waits for)
APPEARS = {
    'FT_FIRST_STALFOS_ROOM_CHEST': ('Gimmick_TreasureBoxAppear_Any_Magic_9a58', 'Gimmick_DefeatEnemy_Open_ForestTemple_01'),
    'FT_FLOORMASTER_CHEST': ('Gimmick_TreasureBoxAppear_Any_Magic_9a58', 'Gimmick_DefeatEnemy_Open_ForestTemple_02'),
    'FT_JOELLE_CHEST': ('Gimmick_TreasureBoxAppear_Any_Magic_9a58', 'ForestTemple_DefeatJoe'),
    'FT_BETH_CHEST': ('Gimmick_TreasureBoxAppear_02_Any_Any_Magic_af8d', 'ForestTemple_DefeatBeth'),
    'FT_BOW_CHEST': ('Gimmick_TreasureBoxAppear_Magic_03_Enemy_2f95', 'Gimmick_DefeatEnemy_Open_ForestTemple_03'),
    'FT_BLOCK_ROOM_EYE_SWITCH_CHEST': ('Gimmick_TreasureBoxAppear_Fall_c6e5', 'ForestTemple_Room08_EyeSwitch_Clear'),
}
SUPPLY_TABLE = 'Drop/DropSubTable/Obj_TBox.game__drop__DropSubTable.bgyml'
SUPPLIES = ['Mp', 'ArrowOrDekuSeed', 'DekuNut', 'Bomb']        # what the chest's own table picks from


def check(name, ok, detail=''):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED %s' % (detail,)))
    return ok


def dyn(actor):
    return dict(actor.get('Dynamic') or {})


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())

    def plain(path, root=romfs):
        p = os.path.join(root, *path.split('/'))
        if os.path.exists(p):
            return open(p, 'rb').read()
        return zstd.decompress(open(p + '.zs', 'rb').read(), d) if os.path.exists(p + '.zs') else None

    good = True
    w = World()
    db = json.load(open(os.path.join(ROOT, 'data', 'db', AREA + '.json'), encoding='utf-8'))
    kinds = {r['unique_check_id']: r['check_type'] for r in db}
    places = {}                                        # check -> [(map file, placement hash)]
    for cid in kinds:
        reg, _, loc = build_mod.find_check(w, cid)
        places[cid] = [('Banc/%s/%s' % (scene, fn[:-3]), p['hash'])
                       for scene, _, p in w.placements_of(reg, loc) for fn in p['files']]
    game = {m: byml.loads(plain(m)).root for m in MAPS}
    actors = {m: {str(int(a['Hash'])): a for a in game[m]['Actors']} for m in MAPS}

    # ---- the plan
    count = {k: sum(1 for v in kinds.values() if v == k) for k in sorted(set(kinds.values()))}
    good &= check('the plan has an item for every check of the temple: %d checks (%s)'
                  % (len(kinds), ', '.join('%d %s' % (n, k) for k, n in count.items())),
                  sorted(PLAN) == sorted(kinds) and len(kinds) == 47, sorted(set(kinds) ^ set(PLAN)))
    families = [lv for lv in build_mod.FAMILIES.values()]
    later = {x for lv in families for x in lv[1:]}
    good &= check('  a different item on each; none that is never placed, and of a family only its first level',
                  len(set(PLAN.values())) == len(PLAN) and not set(PLAN.values()) & set(build_mod.NEVER_GIVEN)
                  and not set(PLAN.values()) & later, sorted(set(PLAN.values()) & later))
    good &= check('  every check but the Medallion\'s cutscene is one object of the temple\'s two map files',
                  all(len(places[c]) == 1 and places[c][0][0] in MAPS and places[c][0][1] in actors[places[c][0][0]]
                      for c in kinds if kinds[c] != 'gift')
                  and [c for c in kinds if kinds[c] == 'gift'] == ['FT_FOREST_MEDALLION_GIFT'],
                  {c: places[c] for c in kinds if len(places[c]) != 1})

    # ---- the temple's chests in the game's files
    chests = sorted(c for c in kinds if kinds[c] == 'chest')
    here = lambda c: actors[places[c][0][0]][places[c][0][1]]   # noqa: E731
    nothing = [c for c in chests if not dyn(here(c)).get('Drop__DropActor') and not dyn(here(c)).get('Drop__DropTable')]
    box = sarc.Sarc.read(plain(ground_items.pack_path(str(here(NAMES_NOTHING[0])['Gyaml'])))).files
    rows = byml.loads(box[SUPPLY_TABLE]).root['Items']
    hashes = [build_mod.start_state.name_hash(n) for n in SUPPLIES]
    good &= check('one of the 12 chests names no contents in the map (%s): it gives from the chest\'s own table, '
                  'the supply Link is shortest of (%s)' % (', '.join(nothing), ', '.join(SUPPLIES)),
                  nothing == NAMES_NOTHING and len(rows) == 1 and not str(rows[0]['DropActorName'])
                  and sorted(int(x) for x in rows[0]['MostDepletedResource']) == sorted(hashes)
                  and int(rows[0]['Type']) == build_mod.start_state.name_hash('MostDepletedResource'),
                  (nothing, rows))
    groups = {}                                        # placement hash -> (logic module, the chest's name in it)
    linked = set()
    for m in MAPS:
        for g in game[m].get('AiGroups', []):
            for x in g.get('References', []):
                groups[str(int(x['Reference']))] = (str(g.get('Logic')), str(x.get('Id')))
        for a in game[m]['Actors']:
            if a['Gyaml'] == 'EventRequestActor':
                linked |= {str(int(l['Dst'])) for l in (a.get('Links') or [])}
    found = {}
    for c in chests:
        h = places[c][0][1]
        if h not in groups:
            continue
        logic = plain('Logic/' + groups[h][0].split('/')[-1] + 'b')
        names = set(s.decode() for s in re.findall(rb'[\x20-\x7e]{4,}', logic))
        module = sorted(n[:-len('.logic.module')] for n in names
                        if n.startswith('Gimmick_TreasureBoxAppear') and n.endswith('.logic.module'))
        if module:
            found[c] = (module, names)
    good &= check('six chests only appear: their room\'s logic runs an "appear" module (two after a fight, one '
                  'after the Bow room\'s fight, two after a Poe is beaten, one from an eye switch)',
                  sorted(found) == sorted(APPEARS)
                  and all(APPEARS[c][0] in found[c][0] and APPEARS[c][1] in found[c][1] for c in APPEARS)
                  and all(places[c][0][1] in linked for c in APPEARS),
                  {c: v[0] for c, v in found.items()})
    good &= check('  Joelle\'s and the Floormaster\'s chest appear through the same module as the first Stalfos '
                  'room\'s; Beth\'s through one no other chest of the temple uses',
                  len({APPEARS[c][0] for c in ('FT_JOELLE_CHEST', 'FT_FLOORMASTER_CHEST',
                                               'FT_FIRST_STALFOS_ROOM_CHEST')}) == 1
                  and [c for c in APPEARS if APPEARS[c][0] == APPEARS['FT_BETH_CHEST'][0]] == ['FT_BETH_CHEST'])

    # ---- the build
    with tempfile.TemporaryDirectory() as tmp:
        with contextlib.redirect_stdout(io.StringIO()) as out:
            build_mod.main(['--romfs', romfs, '--out', tmp, '--name', 'every'] + ['%s=%s' % x for x in sorted(PLAN.items())])
        said, folder = out.getvalue(), os.path.join(tmp, 'every', 'romfs')
        files = sorted(os.path.relpath(os.path.join(dp, f), folder).replace(os.sep, '/')
                       for dp, _, fn in os.walk(folder) for f in fn)
        good &= check('one build takes all 47 (%d files written)' % len(files),
                      all(m + '.zs' in files for m in MAPS) and all(re.search(r'^%s\s' % c, said, re.M) for c in PLAN),
                      [c for c in PLAN if not re.search(r'^%s\s' % c, said, re.M)])
        back = {m: {str(int(a['Hash'])): a for a in byml.loads(plain(m, folder)).root['Actors']} for m in MAPS}
        info = {str(r['__RowId']) for r in byml.loads(plain(build_mod.ACTOR_INFO, folder)).root}
        game_info = {str(r['__RowId']) for r in byml.loads(plain(build_mod.ACTOR_INFO)).root}

        def want(cid, item):
            """what the check's object should name"""
            kind = kinds[cid]
            if item == KEY:                            # in its own dungeon: the named key (decision 46)
                return dungeon_keys.name(AREA, 'once', True)
            if item == BOSS_KEY:
                return dungeon_items.name('Item_Dungeon_BossKey', AREA, 'once')
            what = ground_items.kind_of(plain, item)
            if item in build_mod.SCRUB_COMPANIONS and kind in build_mod.LONE_WEAPON_KINDS:
                # a first weapon alone: its turning item of one level, which gives its bag (part 10)
                return once_items.once_name(item)
            if kind == 'chest':
                return ground_items.ground_name(item, 'held') if what == 'equipment' else item
            if kind == 'skulltula':
                return ground_items.ground_name(item, 'token')
            if kind == 'pot':
                return once_items.plain_name(item) if what in ('item', 'equipment') else ground_items.ground_name(item, 'token')
            return item if what == 'ground' else ground_items.ground_name(item)        # a loose item

        held, wrong = {}, []
        for cid, item in sorted(PLAN.items()):
            if kinds[cid] == 'gift':
                continue
            m, h = places[cid][0]
            a = back[m][h]
            held[cid] = str(a['Gyaml']) if kinds[cid] == 'freestanding' else dyn(a).get('Drop__DropActor')
            if held[cid] != want(cid, item):
                wrong.append((cid, held[cid], want(cid, item)))
        good &= check('read back, the 12 chests: each holds its item', not [x for x in wrong if kinds[x[0]] == 'chest'],
                      wrong)
        good &= check('read back, the 28 pots: each drops the one-time version of its item, and none names a drop '
                      'table any more',
                      not [x for x in wrong if kinds[x[0]] == 'pot']
                      and not any(build_mod.POT_TABLE_KEY in dyn(back[places[c][0][0]][places[c][0][1]])
                                  for c in PLAN if kinds[c] == 'pot'), wrong)
        good &= check('read back, the 5 Gold Skulltulas: each drops the token-built version of its item',
                      not [x for x in wrong if kinds[x[0]] == 'skulltula'], wrong)
        good &= check('read back, the boss\'s heart: the object is the ground version of its item',
                      not [x for x in wrong if kinds[x[0]] == 'freestanding'], wrong)
        gift = w.regions and build_mod.find_check(w, 'FT_FOREST_MEDALLION_GIFT')[2]['gift']
        flow_path = 'Event/EventFlow/%s.110.bfevfl' % gift['flow']
        flow = plain(flow_path, folder)
        fc = evfl.loads(flow).flowchart if flow else None
        ev = [e for e in fc.events if e.name == gift['event']][0] if fc else None
        good &= check('read back, the Medallion\'s cutscene: its step %s gives %s, in the file the game loads (%s)'
                      % (gift['event'], PLAN['FT_FOREST_MEDALLION_GIFT'], flow_path.split('/')[-1]),
                      ev is not None and dict(ev.params).get('ActorName') == PLAN['FT_FOREST_MEDALLION_GIFT'],
                      ev and dict(ev.params))
        good &= check('  the 46 objects hold 46 different things',
                      len(set(held.values())) == len(held) == 46, sorted(held.values()))
        ours = sorted({v for v in held.values() if v not in game_info})
        missing = [v for v in ours if v not in info or ground_items.pack_path(v) + '.zs' not in files]
        good &= check('every actor those name exists: %d are the game\'s own, %d are new, each written as a pack '
                      'with its row in the actor table' % (len(set(held.values())) - len(ours), len(ours)),
                      not missing and len(ours) >= 34, missing)
        changed = {m: {h for c in PLAN if kinds[c] != 'gift' for mm, h in places[c] if mm == m} for m in MAPS}
        good &= check('nothing else of the two maps changed: the other %d objects are as the game has them'
                      % sum(len(back[m]) - len(changed[m]) for m in MAPS),
                      all(len(back[m]) == len(actors[m])
                          and all(back[m][h] == actors[m][h] for h in back[m] if h not in changed[m])
                          for m in MAPS))
        table = restbl.Restbl.read(zstd.decompress(open(os.path.join(folder, build_mod.RESTBL_PATH), 'rb').read(), d))
        rest = build_mod.RESTBL_PATH.replace(os.sep, '/')
        short = []
        for f in files:
            if f == rest:
                continue
            path = f[:-3] if f.endswith('.zs') else f
            size = len(plain(path, folder))
            if table.get(path) is None or table.get(path) < size:
                short.append((path, table.get(path), size))
        good &= check('every file of the build has an entry in the resource size table, at least its own size '
                      '(%d files)' % (len(files) - 1), not short, short[:5])

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
