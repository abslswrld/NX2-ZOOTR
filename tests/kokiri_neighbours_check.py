"""Phase 1, part 10: Kokiri Forest and its neighbours (to test in game).

    python tests/kokiri_neighbours_check.py "<romfs>"

What it checks, each on a build read back from the files written:
- The starting state's leftovers (tools/start_state.py): an item the inventory keeps under another name is
  pushed as it is placed (Item_Range_SlingShot, Item_Range_Bow, Item_Gauntlet_Goron), a first weapon with what
  the game's chests give with it (the small bag, 30 seeds or arrows); --start-hearts changes the module's own
  Life and MaxLife; --start-rupees adds one set of PlayerStatus.CurrentRupee. From the game's files: the names
  the inventory keeps those items under, and that a placement's saved flag has no default value (a chest open
  from the start is not possible).
- A first weapon placed alone on a pot, a Gold Skulltula or a freestanding item is its turning item of one
  level: it gives what a chest gives with it and has no next level (in game 2026-11-25 a Fairy Bow alone in a
  pot came without its quiver).
- A dungeon's small key, boss key, map or compass from a person (a gift with flow data) and from a Deku Scrub:
  the version a chest holds is handed over, and the chests' own step follows the get (one more on the key
  count, or the item's field set); refused on a cutscene gift and on a shelf.
- A stone or a Medallion from a person, a cutscene gift, a scrub and a shelf builds.
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
import once_items  # noqa: E402
import shop_items  # noqa: E402
import start_state  # noqa: E402
import turn_items  # noqa: E402
from formats import zstd, byml, sarc, evfl, restbl  # noqa: E402
from logic.world import World  # noqa: E402

D = 'ForestTemple'
GIFT, SCRUB, SHELF, CUTSCENE = 'KF_CIRCLE_KOKIRI_GIFT', 'LW_NEAR_BRIDGE_SCRUB', 'KF_KOKIRI_CHILD_SHOP_01', 'LW_SARIA_GIFT'
POT, GS, GROUND = 'KF_KNOW_IT_ALL_HOUSE_CHILD_POT_01', 'KF_KNOW_IT_ALL_HOUSE_GS', 'KF_RUPEE_NEAR_MIDO_ITEM'
SLING, BOW, BRACELET = 'Item_Range_SlingShot', 'Item_Range_Bow', 'Item_Gauntlet_Goron'
KEPT_AS = {SLING: 'Weapon_Range_SlingShot', BOW: 'Weapon_Range_Bow', BRACELET: 'Armor_Child_Gauntlet_Goron'}
WITH = {SLING: [('Item_BulletBag_Small', 1), ('Item_DekuSeed', 30)],
        BOW: [('Item_Quiver_Small', 1), ('Item_Arrow_Normal', 30)]}
HEARTS, RUPEES = 5, 50
CIRCLE = ['--fix', 'kokiri_circle_after_dungeons']                    # the gift's check needs it
BUILDS = {
    'start': ['--start', SLING, '--start', BOW, '--start', BRACELET, '--start-hearts', str(HEARTS),
              '--start-rupees', str(RUPEES)],
    'placed': CIRCLE + ['%s=Item_Dungeon_SmallKey@%s' % (GIFT, D), '%s=Item_Dungeon_BossKey@%s' % (SCRUB, D),
                        '%s=%s' % (POT, BOW), '%s=%s' % (GS, SLING)],
    'items': CIRCLE + ['%s=Item_Dungeon_Map@%s' % (GIFT, D), '%s=Item_Dungeon_SmallKey@%s' % (SCRUB, D),
                       '%s=%s' % (GROUND, BOW)],
    'rewards': CIRCLE + ['--fix', 'kokiri_shop_full_stock', '%s=Item_Stone_Forest' % GIFT,
                         '%s=Item_Medal_Water' % SCRUB, '%s=Item_Stone_Fire' % SHELF, '%s=Item_Medal_Fire' % CUTSCENE],
}
REFUSED = [
    (['%s=Item_Dungeon_SmallKey@%s' % (CUTSCENE, D)], 'cutscene gift or a song'),
    (['--fix', 'kokiri_shop_full_stock', '%s=Item_Dungeon_Map@%s' % (SHELF, D)], 'cannot be put on a shop'),
    (['%s=%s' % (POT, BOW), '%s=Item_Range_Bow>Item_Quiver_Medium>Item_Quiver_Large' % GROUND],
     'the same item on two checks'),
]


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
    known = {r['__RowId']: r.get('ActorName') for r in byml.loads(plain(ground_items.table_path('ActorInfo'))).root}
    data = start_state.GameData(plain(start_state.GAME_DATA))
    good &= check('the game keeps %s under another name, which has the saved pair: %s'
                  % (', '.join(KEPT_AS), ', '.join(KEPT_AS.values())),
                  all(known.get(x) == y and not data.owns(x) and data.owns(y) for x, y in KEPT_AS.items()),
                  {x: known.get(x) for x in KEPT_AS})
    game_status = start_state.read_status(plain(start_state.MODULE))
    rupees = data.find('%s.%s' % (start_state.STATUS, start_state.STATUS_RUPEES))
    good &= check('  a new file\'s hearts are the module\'s own Life and MaxLife (12 each), its rupees '
                  'PlayerStatus.CurrentRupee (an Int, saved, not set by the module)',
                  game_status.get('Life') == game_status.get('MaxLife') == 3 * start_state.HEART
                  and start_state.STATUS_RUPEES not in game_status and rupees is not None and rupees[0] == 'Int'
                  and int(rupees[1]['SaveFileIndex']) == start_state.SLOT_SAVE, game_status)
    placed_flags = byml.loads(plain(start_state.GAME_DATA)).root['Data']['Bool64bitKey']
    good &= check('  a placement\'s saved flag (%d of them) has no default value: a chest open from the start is '
                  'not possible this way' % len(placed_flags),
                  all(set(e) <= {'Hash', 'ResetTypeValue', 'SaveFileIndex', 'ExtraByte'} for e in placed_flags))
    shared = sarc.Sarc.read(plain(turn_items.AI_PACK)).files
    good &= check('  the game\'s chests give the small bag and 30 seeds or arrows with a first weapon',
                  all(turn_items.first_get(shared, KEPT_AS[x])[1] == WITH[x] for x in WITH))

    # ---- refused before anything is written
    for args, said in REFUSED:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                build_mod.main(['--romfs', romfs, '--out', os.path.join(tempfile.gettempdir(), 'nx2_never'),
                                '--name', 'never'] + args)
            got = None
        except SystemExit as e:
            got = str(e)
        good &= check('refused: %s ("%s")' % (' '.join(args)[:70], said), got is not None and said in got, got)

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

        # ---- the starting state
        folder = builds['start'][1]
        items, flags = start_state.read(plain(start_state.MODULE, folder))
        game_items = start_state.read(plain(start_state.MODULE))[0]
        want = game_items + [(SLING, 1)] + WITH[SLING] + [(BOW, 1)] + WITH[BOW] + [(BRACELET, 1)]
        good &= check('start: the game\'s %d pushes, then the Fairy Slingshot, its bag and 30 seeds, the Fairy Bow, '
                      'its quiver and 30 arrows, the Goron Bracelet, each as it is placed' % len(game_items),
                      items == want and not flags, items)
        status = start_state.read_status(plain(start_state.MODULE, folder))
        good &= check('  %d hearts (Life and MaxLife %d, the module\'s own two sets), %d rupees (one more set), '
                      'the module\'s other sets as they were' % (HEARTS, HEARTS * start_state.HEART, RUPEES),
                      status == dict(game_status, Life=HEARTS * start_state.HEART,
                                     MaxLife=HEARTS * start_state.HEART, CurrentRupee=RUPEES), status)
        good &= check('  only the module is written', [f for f in builds['start'][2] if 'ResourceSizeTable' not in f]
                      == [start_state.MODULE], builds['start'][2])

        # ---- a first weapon alone
        def lone(build, version, ai, once):
            pack = plain(ground_items.pack_path(version), builds[build][1])
            if pack is None:
                return None
            ai_data = sarc.Sarc.read(pack).files[shop_items.ai_path(ai)]
            return turn_items.describe(once_items.unmarked(ai_data) if once else ai_data), ai_data

        for build, cid, item, once in (('placed', POT, BOW, True), ('placed', GS, SLING, True),
                                       ('items', GROUND, BOW, False)):
            version = once_items.once_name(item) if once else turn_items.turn_name(item)
            got = lone(build, version, (once_items if once else turn_items).ai_name(item), once)
            what = got[0] if got else {}
            gives = [(turn_items._actor_of(x), n) for x, n in (what.get('bundle') or {}).get('gives', [])]
            good &= check('%s alone on %s: %s gives %s while Link has no %s, has no next level and deletes itself '
                          'once Link owns it%s' % (item, cid, version, ', '.join('%d %s' % (n, x) for x, n in WITH[item]),
                                                   WITH[item][0][0], ', and marks what dropped it' if once else ''),
                          got is not None and gives == WITH[item] and what['bundle']['bag'] == WITH[item][0][0]
                          and what['own'] == item and not what['drops'] and not what['later']
                          and what['turn'] == [(turn_items.N_DELETE, [])] and not what['asked']
                          and (not once or once_items.marks_of(got[1])['picked_up']), what)
            r, _, loc = build_mod.find_check(w, cid)
            named = []
            for scene, _, p in w.placements_of(r, loc):
                for fn in p['files']:
                    m = plain('Banc/%s/%s' % (scene, fn[:-3] if fn.endswith('.zs') else fn), builds[build][1])
                    named.append(m is not None and version.encode() in m)
            good &= check('  every map of %s names %s' % (cid, version), bool(named) and all(named), named)

        # ---- a dungeon's key, boss key, map or compass from a person and from a scrub
        gift = build_mod.find_check(w, GIFT)[2]['gift']
        gift_flow = build_mod.flow_path(gift['flow'])
        game_fc = evfl.loads(plain(gift_flow)).flowchart
        game_ev = next(e for e in game_fc.events if e.name == gift['event'])
        leads = None if game_ev.next is None else game_fc.events[game_ev.next].name
        cases = (('placed', dungeon_keys.name(D, 'chest', True), build_mod.KEY_ADD[1],
                  {'GameDataName': dungeon_keys.flag(D), 'Value': 1, 'Index': -1}),
                 ('items', dungeon_items.name('Item_Dungeon_Map', D, 'chest'), build_mod.KEY_SET[1],
                  {'GameDataName': dungeon_items.flag('Item_Dungeon_Map', D), 'Value': True, 'Index': -1}))
        for build, version, action, params in cases:
            fc = evfl.loads(plain(gift_flow, builds[build][1])).flowchart
            e = next(x for x in fc.events if x.name == gift['event'])
            step = fc.events[e.next] if e.next is not None else None
            good &= check('%s: the gift hands over %s as it gave %s, then %s %s, then on as before'
                          % (build, version, gift['item'], action, params['GameDataName']),
                          e.type == 'subflow' and e.params.get('ActorName') == version and step is not None
                          and step.type == 'action' and fc.actors[step.actor].name == build_mod.KEY_ADD[0]
                          and fc.actors[step.actor].actions[step.action] == action and dict(step.params) == params
                          and (None if step.next is None else fc.events[step.next].name) == leads
                          and len(fc.events) == len(game_fc.events) + 1
                          and plain(ground_items.pack_path(version), builds[build][1]) is not None,
                          step and dict(step.params or {}))
        game_scrub = evfl.loads(plain(build_mod.SCRUB_FLOW)).flowchart
        cases = (('placed', dungeon_items.name('Item_Dungeon_BossKey', D, 'chest'), build_mod.KEY_SET[1],
                  {'GameDataName': dungeon_items.flag('Item_Dungeon_BossKey', D), 'Value': True, 'Index': -1}),
                 ('items', dungeon_keys.name(D, 'chest', True), build_mod.KEY_ADD[1],
                  {'GameDataName': dungeon_keys.flag(D), 'Value': 1, 'Index': -1}))
        for build, version, action, params in cases:
            fc = evfl.loads(plain(build_mod.SCRUB_FLOW, builds[build][1])).flowchart
            sells = [e for e in fc.events if e.type == 'subflow' and e.entry == build_mod.SCRUB_SELL
                     and isinstance(e.params, dict) and e.params.get('ActorName') == version]
            bought = fc.events[sells[0].next] if len(sells) == 1 and sells[0].next is not None else None
            step = fc.events[dict(bought.cases)[0]] if bought is not None and bought.type == 'switch' \
                and dict(bought.cases).get(0) is not None else None
            good &= check('%s: the scrub sells %s once, and after a successful buy runs %s %s'
                          % (build, version, action, params['GameDataName']),
                          step is not None and bought.params.get('GameDataName') == 'ScrubBusiness_BuySuccess'
                          and list(dict(bought.cases)) == [0] and step.type == 'action' and step.next is None
                          and fc.actors[step.actor].name == build_mod.KEY_ADD[0]
                          and fc.actors[step.actor].actions[step.action] == action and dict(step.params) == params
                          and not [e for e in game_scrub.events if e.type == 'subflow' and isinstance(
                              e.params, dict) and e.params.get('ActorName') == version],
                          step and dict(step.params or {}))

        # ---- a stone or a Medallion from a person, a cutscene, a scrub and a shelf
        out, folder, files = builds['rewards']
        fc = evfl.loads(plain(gift_flow, folder)).flowchart
        e = next(x for x in fc.events if x.name == gift['event'])
        good &= check('rewards: the Kokiri Emerald from a person, a Medallion from Saria\'s cutscene, a Medallion '
                      'from the scrub, a stone on a shelf (sold once)',
                      e.type == 'subflow' and e.params.get('ActorName') == 'Item_Stone_Forest'
                      and 'adds Item_Medal_Fire' in out and 'sells Item_Medal_Water' in out
                      and any(f.startswith('Pack/Actor/%sStone_Fire' % shop_items.PREFIX) for f in files),
                      [f for f in files if 'Shop_' in f])

        short = []
        for name, (_, folder, files) in builds.items():
            written = os.path.join(folder, build_mod.RESTBL_PATH)   # not written when every file still fits
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
