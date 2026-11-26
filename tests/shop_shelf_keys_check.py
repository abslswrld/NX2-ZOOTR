"""Phase 1, part 12: a dungeon's small key, boss key, map or compass on a shop shelf (to test in game).

    python tests/shop_shelf_keys_check.py "<romfs>"

What it checks:
- From the game's files: a sale is an event of the shops' shared flow DisplayShop, which keeps the picked
  item's name in Shop_SelectItemName and asks about it itself (the tunics); that name is the shelf's inventory
  name (ActorInfo: ActorName); the flow counts a sale in five places, and asks once, with three different
  answers, whether Link can carry the item.
- A build with a small key, a boss key and a map on three shelves, read back: each shelf is a shop version
  (sold once) of the version a chest holds, named as that version; behind every step that counts a sale stands
  the name question for each of the three, "yes" leading to the chests' own step (one more on the key count,
  or the item's field set) and then on as before; in front of the "can Link carry it" question the same
  question leads ours to its "yes". Nothing else of the flow changed.
- A build with an ordinary item on a shelf does not touch the flow.
"""
import contextlib
import io
import os
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
import item_pose  # noqa: E402
import shop_items  # noqa: E402
from formats import zstd, byml, sarc, evfl, restbl  # noqa: E402
from logic.world import World  # noqa: E402

D, D2 = 'ForestTemple', 'FireTemple'
FIX = ['--fix', 'kokiri_shop_full_stock']
SHELVES = {'KF_KOKIRI_CHILD_SHOP_01': ('Item_Dungeon_SmallKey@' + D, dungeon_keys.name(D, 'chest', True),
                                       build_mod.KEY_ADD[1],
                                       {'GameDataName': dungeon_keys.flag(D), 'Value': 1, 'Index': -1}),
           'KF_KOKIRI_CHILD_SHOP_02': ('Item_Dungeon_BossKey@' + D, dungeon_items.name('Item_Dungeon_BossKey', D, 'chest'),
                                       build_mod.KEY_SET[1],
                                       {'GameDataName': dungeon_items.flag('Item_Dungeon_BossKey', D),
                                        'Value': True, 'Index': -1}),
           'KF_KOKIRI_CHILD_SHOP_03': ('Item_Dungeon_Map@' + D2, dungeon_items.name('Item_Dungeon_Map', D2, 'chest'),
                                       build_mod.KEY_SET[1],
                                       {'GameDataName': dungeon_items.flag('Item_Dungeon_Map', D2),
                                        'Value': True, 'Index': -1})}
BUILDS = {'shelves': FIX + ['%s=%s' % (c, v[0]) for c, v in sorted(SHELVES.items())],
          'plain': FIX + ['KF_KOKIRI_CHILD_SHOP_01=Item_Boomerang']}
TUNIC = ('Shop_Armor_Zora', 'Armor_Adult_Zora')


def check(name, ok, detail=''):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED %s' % (detail,)))
    return ok


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())

    def plain(path, root=romfs):
        p = os.path.join(root, *path.split('/'))
        if os.path.exists(p):
            return open(p, 'rb').read()
        return zstd.decompress(open(p + '.zs', 'rb').read(), d) if os.path.exists(p + '.zs') else None

    good = True
    w = World()

    # ---- the game's files
    game = evfl.loads(plain(build_mod.SHOP_SALE_FLOW)).flowchart
    sold, can, name_params = build_mod.shop_flow_parts(game)
    asked = {e.params['Value'] for e in game.events if e.type == 'switch' and isinstance(e.params, dict)
             and e.params.get('GameDataName') == build_mod.SHOP_ITEM_VAR and 'Value' in e.params}
    rows = {r['__RowId']: r for r in byml.loads(plain(ground_items.table_path('ActorInfo'))).root}
    good &= check('the game\'s sale flow asks about the picked item by name (%s: %d names, %s among them), and '
                  'that name is the shelf\'s inventory name (%s: %s)'
                  % (build_mod.SHOP_ITEM_VAR, len(asked), TUNIC[1], TUNIC[0], rows[TUNIC[0]].get('ActorName')),
                  TUNIC[1] in asked and rows[TUNIC[0]].get('ActorName') == TUNIC[1]
                  and dict(name_params)['GameDataName'] == build_mod.SHOP_ITEM_VAR)
    good &= check('  it counts a sale in %d places (%s), each with a next step, and asks once whether Link can '
                  'carry the item, with three different answers' % (len(sold), build_mod.SHOP_SOLD[1]),
                  len(sold) == 5 and all(game.events[i].next is not None for i in sold)
                  and len({t for _, t in game.events[can].cases}) == 3)

    builds = {}
    with tempfile.TemporaryDirectory() as tmp:
        for name, args in BUILDS.items():
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + args)
            folder = os.path.join(tmp, name, 'romfs')
            files = sorted(os.path.relpath(os.path.join(dp, f), folder).replace(os.sep, '/')
                           for dp, _, fn in os.walk(folder) for f in fn)
            builds[name] = (out.getvalue(), folder, files)
            good &= check('build "%s": %d files written' % (name, len(files)), bool(files))

        out, folder, files = builds['shelves']
        flow_file = build_mod.SHOP_SALE_FLOW + '.zs'
        good &= check('the build with our shelves writes the sale flow; the one with an ordinary item does not',
                      flow_file in files and flow_file not in builds['plain'][2])
        back = evfl.loads(plain(build_mod.SHOP_SALE_FLOW, folder)).flowchart
        n0 = len(game.events)
        info = {r['__RowId']: r for r in byml.loads(plain(ground_items.table_path('ActorInfo'), folder)).root}
        pouch = {r['__RowId']: r for r in byml.loads(plain(ground_items.table_path('PouchActorInfo'), folder)).root}

        def act(e):
            return (back.actors[e.actor].name, back.actors[e.actor].actions[e.action]) if e.type == 'action' else None

        def questions(item):
            return [i for i, e in enumerate(back.events) if i >= n0 and e.type == 'switch'
                    and back.actors[e.actor].queries[e.query] == build_mod.SHOP_NAME_QUERY[1]
                    and dict(e.params) == dict(name_params, Value=item)]

        def own(i):
            while i is not None and i >= n0:
                i = dict(back.events[i].cases).get(1)
            return i

        for cid, (asked_for, version, action, params) in sorted(SHELVES.items()):
            shop = [f for f in files if f.startswith('Pack/Actor/%s%s_' % (shop_items.PREFIX, version[len('Item_'):]))]
            name = os.path.basename(shop[0])[:-len('.pack.zs')] if len(shop) == 1 else None
            r, _, loc = build_mod.find_check(w, cid)
            maps = [plain('Banc/%s/%s' % (scene, fn[:-3] if fn.endswith('.zs') else fn), folder)
                    for scene, _, p in w.placements_of(r, loc) for fn in p['files']]
            pack = sarc.Sarc.read(plain(shop[0][:-3], folder)).files if name else {}
            sets = byml.loads(pack[ground_items.pouch_param_path(name)]).root if name else {}
            good &= check('%s (%s): the shelf is %s, a shop version sold once of %s, named as it; its item '
                          'settings name %s for the pouch' % (cid, asked_for, name, version, version),
                          name is not None and name.endswith('_Once') and any(m is not None and name.encode() in m
                                                                             for m in maps)
                          and info[name]['ActorName'] == version == info[version]['ActorName']
                          and pouch[name].get('PouchSpecialDeal') == pouch[version].get('PouchSpecialDeal')
                          and int(pouch[name]['BuyingPrice']) > 0
                          and str(sets.get('PouchActor', '')).endswith('/%s.engine__actor__ActorParam.gyml' % version),
                          (name, dict(sets)))
            qs = questions(version)
            counted = []
            for i in sold:                              # behind each sale step: this item's question
                at, hit = back.events[i].next, None
                while at is not None and at >= n0:
                    if at in qs:
                        hit = at
                    at = dict(back.events[at].cases)[1]
                step = back.events[dict(back.events[hit].cases)[0]] if hit is not None else None
                counted.append(hit is not None and at == game.events[i].next and act(step) == (
                    build_mod.KEY_ADD[0], action) and dict(step.params) == params and own(step.next) == game.events[i].next)
            carry = [i for i in qs if dict(back.events[i].cases)[0] == dict(game.events[can].cases)[0]]
            good &= check('  the sale flow: behind each of the %d sale steps "is it %s?" -> %s %s, then on as '
                          'before; and one in front of "can Link carry it", leading to its "yes"'
                          % (len(sold), version, action, params['GameDataName']),
                          len(qs) == len(sold) + 1 and all(counted) and len(carry) == 1
                          and own(dict(back.events[carry[0]].cases)[1]) == can, (len(qs), counted, carry))
        # the boss key, the compass and the map have a centred pose: lifted on the shelf by what their model
        # hangs under the shelf point (in game 2026-11-25 the boss key and the compass sat in the shelf)
        lows = {}
        for item in ('Item_Dungeon_BossKey', 'Item_Dungeon_Compass', 'Item_Dungeon_Map', 'Item_Dungeon_SmallKey'):
            pack = sarc.Sarc.read(plain(ground_items.pack_path(item))).files
            anims = byml.loads(pack[ground_items._ref_path(ground_items.resolved_components(pack, item)[
                'AnimationRef'])]).root['AnimationResources']
            project, = [x['ModelProjectName'] for x in anims if x['ModelProjectName'] != shop_items.COMMON_ANIM]
            pose = item_pose.read_pose(plain(item_pose.model_path(project)))
            points, bind, _ = item_pose.model_points(plain('Model/%s.%s.bfres' % (rows[item]['ModelProjectName'],
                                                                                  rows[item]['FmdbName'])))
            lows[item] = item_pose.extent(points, bind, pose['scale'], pose['rot'], pose['move'])[0][1]
        lifted = {k: v for k, v in shop_items.SHELF_LIFT.items() if k in lows}
        good &= check('  shelf lifts: the boss key, the compass and the map stand on the shelf (lifted by what '
                      'hangs under the shelf point: %s); the small key stands on it by itself (%+.3f)'
                      % (', '.join('%s %.2f for %.3f' % (k[len('Item_Dungeon_'):], v, -lows[k])
                                   for k, v in sorted(lifted.items())), lows['Item_Dungeon_SmallKey']),
                      sorted(lifted) == ['Item_Dungeon_BossKey', 'Item_Dungeon_Compass', 'Item_Dungeon_Map']
                      and all(abs(v + lows[k]) <= 0.01 for k, v in lifted.items())
                      and abs(lows['Item_Dungeon_SmallKey']) <= 0.03
                      and out.count('shelf lift') == 2 and '0.22 m higher' in out and '0.20 m higher' in out, lows)
        kept = all((o.type, o.name, o.params) == (b.type, b.name, b.params)
                   and [own(x) for x in build_mod._flow_links(b)] == build_mod._flow_links(o)
                   for o, b in zip(game.events, back.events))
        good &= check('  the game\'s %d events of the flow are as they were but for those leads; %d new events'
                      % (n0, len(back.events) - n0), kept and len(back.events) == n0 + 3 * (2 * len(sold) + 1))

        short = []
        for name, (_, folder, files) in builds.items():
            written = os.path.join(folder, build_mod.RESTBL_PATH)
            table = restbl.Restbl.read(zstd.decompress(open(written if os.path.exists(written) else os.path.join(
                romfs, build_mod.RESTBL_PATH), 'rb').read(), d))
            rest = build_mod.RESTBL_PATH.replace(os.sep, '/')
            for f in files:
                path = f[:-3] if f.endswith('.zs') else f
                if f != rest and (table.get(path) is None or table.get(path) < len(plain(path, folder))):
                    short.append((name, path))
        good &= check('every file of the %d builds has an entry in the resource size table, at least its own size'
                      % len(builds), not short, short[:5])

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
