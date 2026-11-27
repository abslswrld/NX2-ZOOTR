"""Phase 2, part 1: an upgrade pair on a shop shelf (a trial, to test in game).

    python tests/shop_family_check.py "<romfs>"

What it checks:
- From the game's files: the shops' shared sale flow (DisplayShop) puts the shelf's item in the inventory
  with one of five steps, each with a next step; no shelf of the game is named as a pair's second level; the
  game's own inventory question and its name write (the scrubs') are found.
- A build with Silver Scale > Gold Scale on a Kokiri Shop shelf, read back: the shelf is the Silver Scale's
  shop version, sold once; behind each of the flow's two "shelf picked" steps, before the shopkeeper names the
  item, stands "is it the Silver Scale?" -> "Link has the Silver Scale?" -> yes: the Gold Scale's name is written
  into Shop_SelectItemName, two frames pass, then on; in front of each of the five giving steps stands "is it the Gold
  Scale?" -> yes: the Gold Scale is added and the shelf's own step is passed by. Nothing else of the flow
  changed.
- The same build with a dungeon's small key on another shelf: both changes stand in the flow.
- Refused: two upgrades of one family in one shop (decision 51): the pair on two shelves, the pair beside its
  first level alone, one level alone on two shelves.
- Three levels on a shelf (phase 2, part 3): the three bomb bags; two inventory questions behind each "shelf
  picked" step, the higher level first, and in front of each giving step the second or the third level added
  in the shelf item's place.
- A first weapon on a shelf comes with its small bag: the Fairy Slingshot as the first level of its family,
  and the Fairy Bow alone on a shelf (from the game's files: a shelf's own steps give nothing but its item).
- How many shelves per shop are randomized (decision 37): every shop shelf of the data has a place in its
  shop's order ("shelf_rank"), and `World.shop_shelves(n)` names the first n of each shop and age.
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
import dungeon_keys  # noqa: E402
import ground_items  # noqa: E402
import item_pose  # noqa: E402
import shop_items  # noqa: E402
from formats import zstd, byml, evfl, restbl, sarc  # noqa: E402
from logic.world import World  # noqa: E402

FIX = ['--fix', 'kokiri_shop_full_stock']
SHELF, SHELF2 = 'KF_KOKIRI_CHILD_SHOP_01', 'KF_KOKIRI_CHILD_SHOP_02'
FIRST, SECOND = 'Item_Scale_Silver', 'Item_Scale_Gold'
PAIR = '%s=%s>%s' % (SHELF, FIRST, SECOND)
D = 'ForestTemple'
BAGS = ('Item_BombBag_Small', 'Item_BombBag_Medium', 'Item_BombBag_Large')
SEEDS = ('Item_Range_SlingShot', 'Item_BulletBag_Medium', 'Item_BulletBag_Large')
SLING, BOW = 'Weapon_Range_SlingShot', 'Weapon_Range_Bow'      # the names the inventory and the shop know them by
BUILDS = {'pair': FIX + [PAIR],
          'both': FIX + [PAIR, '%s=Item_Dungeon_SmallKey@%s' % (SHELF2, D)],
          'three': FIX + ['%s=%s' % (SHELF, '>'.join(BAGS))],
          'weapons': FIX + ['%s=%s' % (SHELF, '>'.join(SEEDS)), '%s=Item_Range_Bow' % SHELF2]}
ONE_PER_SHOP = 'a shop holds at most one upgrade of a family'
REFUSED = [(FIX + [PAIR, '%s=%s>%s' % (SHELF2, FIRST, SECOND)], ONE_PER_SHOP),
           (FIX + [PAIR, '%s=%s' % (SHELF2, FIRST)], ONE_PER_SHOP),
           (FIX + ['%s=Item_BombBag_Small' % SHELF, 'KF_KOKIRI_ADULT_SHOP_03=Item_BombBag_Small'], ONE_PER_SHOP)]


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
    gives = build_mod.shop_give_steps(game)
    picked = build_mod.shop_focus_steps(game)
    rows = {r['__RowId']: r for r in byml.loads(plain(ground_items.table_path('ActorInfo'))).root}
    shelf_names = {r.get('ActorName') for n, r in rows.items() if n.startswith('Shop_')}
    ask = build_mod.gift_pair_template(evfl.loads(plain(build_mod.GIFT_PAIR_FLOW)).flowchart)
    write = build_mod.scrub_pair_template(evfl.loads(plain(build_mod.SCRUB_FLOW)).flowchart)[1]
    good &= check('the game\'s sale flow gives the shelf\'s item with one of %d steps (%s), each with a next step'
                  % (len(gives), ', '.join(sorted({a for _, a in build_mod.SHOP_GIVES}))),
                  len(gives) == 5 and {build_mod._action_name(game, game.events[i]) for i in gives}
                  == {a for _, a in build_mod.SHOP_GIVES})
    later = {f[k] for f in build_mod.FAMILIES.values() for k in range(1, len(f))}
    good &= check('  no shelf of the game (%d names) is named as a later level of a family; the Silver and the '
                  'Gold Scale are named themselves' % len(shelf_names),
                  not {rows[x].get('ActorName') or x for x in later if x in rows} & shelf_names
                  and all((rows[x].get('ActorName') or x) == x for x in (FIRST, SECOND)))
    good &= check('  the game\'s inventory question (%s) and its name write (%s, a saved string) are found'
                  % (build_mod.GIFT_PAIR_QUERY, build_mod.SCRUB_NAME_WRITE),
                  ask[2:] == (0, 1) and list(ask[1]) == ['Num', 'Actor']
                  and sorted(write[0]) == ['GameDataName', 'Index', 'Value'])

    # ---- how many shelves per shop are randomized (decision 37)
    shelves = sorted(loc['id'] for reg in w.regions.values() for loc in reg.locations.values()
                     if loc.get('kind') == 'shop')
    ranks = {loc['id']: loc.get('shelf_rank') for reg in w.regions.values() for loc in reg.locations.values()
             if loc.get('kind') == 'shop'}
    last = sorted(c for c, k in ranks.items() if k == 8)
    good &= check('the %d shop shelves of the data each have a place in their shop\'s order; World.shop_shelves(n) '
                  'names none for 0, the first of each age for 1, all for 8 and more; the Deku Shield\'s shelf is last'
                  % len(shelves),
                  not w.problems() and len(shelves) == 16 and w.shop_shelves(0) == []
                  and w.shop_shelves(1) == sorted(c for c, k in ranks.items() if k == 1) and len(w.shop_shelves(1)) == 2
                  and all(set(w.shop_shelves(n)) < set(w.shop_shelves(n + 1)) for n in range(8))
                  and w.shop_shelves(8) == shelves == w.shop_shelves(20)
                  and last == ['KF_KOKIRI_ADULT_SHOP_06', 'KF_KOKIRI_CHILD_SHOP_06'], (ranks, w.problems()))

    # ---- refused before anything is written
    for args, said in REFUSED:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                build_mod.main(['--romfs', romfs, '--out', os.path.join(tempfile.gettempdir(), 'nx2_never'),
                                '--name', 'never'] + args)
            got = None
        except SystemExit as e:
            got = str(e)
        good &= check('refused: %s' % ' '.join(args[2:])[:84], got is not None and (said is None or said in got), got)

    builds = {}
    with tempfile.TemporaryDirectory() as tmp:
        for name, args in BUILDS.items():
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + args)
            folder = os.path.join(tmp, name, 'romfs')
            files = sorted(os.path.relpath(os.path.join(dp, f), folder).replace(os.sep, '/')
                           for dp, _, fn in os.walk(folder) for f in fn)
            builds[name] = (out.getvalue(), folder, files)
            good &= check('build "%s": %d files written' % (name, len(files)),
                          build_mod.SHOP_SALE_FLOW + '.zs' in files)

        # ---- the pair
        out, folder, files = builds['pair']
        shop = [f for f in files if f.startswith('Pack/Actor/%s%s_' % (shop_items.PREFIX, FIRST[len('Item_'):]))]
        name = os.path.basename(shop[0])[:-len('.pack.zs')] if len(shop) == 1 else None
        r, _, loc = build_mod.find_check(w, SHELF)
        maps = [plain('Banc/%s/%s' % (scene, fn[:-3] if fn.endswith('.zs') else fn), folder)
                for scene, _, p in w.placements_of(r, loc) for fn in p['files']]
        good &= check('%s (%s > %s): the shelf is %s, the first level\'s shop version, sold once; no shop version of '
                      'the second level is made' % (SHELF, FIRST, SECOND, name),
                      name is not None and name.endswith('_Once') and any(m is not None and name.encode() in m
                                                                         for m in maps)
                      and not [f for f in files if SECOND[len('Item_'):] in f], shop)

        def read(build, before):
            """(the flow of a build, the number of events it had before the pair's edit)"""
            return evfl.loads(plain(build_mod.SHOP_SALE_FLOW, builds[build][1])).flowchart, before

        for build, n0 in (('pair', len(game.events)), ('both', len(game.events) + len(sold) * 2 + 1)):
            back, _ = read(build, n0)

            def name_of(e):
                return back.actors[e.actor].name, (back.actors[e.actor].actions[e.action] if e.type == 'action'
                                                   else back.actors[e.actor].queries[e.query])

            def asks(value):
                return [e for e in back.events[n0:] if e.type == 'switch' and name_of(e) == build_mod.SHOP_NAME_QUERY
                        and dict(e.params) == dict(name_params, Value=value)]

            heads = asks(FIRST)
            ok = len(heads) == len(picked) and sorted(back.events[f].next for f in picked) == sorted(
                back.events.index(h) for h in heads)
            for head in heads:                          # behind each "shelf picked" step
                on = dict(head.cases)[1]
                q = back.events[dict(head.cases)[0]]
                wr = back.events[dict(q.cases)[ask[2]]] if q.type == 'switch' else None
                wait = back.events[wr.next] if wr is not None and wr.type == 'action' and wr.next is not None else None
                ok &= (wait is not None and name_of(q) == (build_mod.GIFT_PAIR_ACTOR, build_mod.GIFT_PAIR_QUERY)
                       and dict(q.params) == {'Num': 1, 'Actor': FIRST}
                       and name_of(wr) == ('GameDataActor', build_mod.SCRUB_NAME_WRITE)
                       and dict(wr.params) == {'GameDataName': build_mod.SHOP_ITEM_VAR, 'Index': -1, 'Value': SECOND}
                       and name_of(wait) == ('EventSystemActor', 'EventWait')
                       and dict(wait.params).get('Frames') == build_mod.SCRUB_WRITE_WAIT and wait.next == on
                       and dict(q.cases)[ask[3]] == on and on in [game.events[f].next for f in picked])
            good &= check('%s: behind each of the %d "shelf picked" steps, before the shopkeeper names the item: is '
                          'it %s? -> Link has %s? -> yes: %s written into %s, %d frames, then on; no: on'
                          % (build, len(picked), FIRST, FIRST, SECOND, build_mod.SHOP_ITEM_VAR,
                             build_mod.SCRUB_WRITE_WAIT), ok)
            placed = asks(SECOND)
            adds = [back.events[dict(e.cases)[0]] for e in placed]
            good &= check('%s: in front of each of the %d giving steps: is it %s? -> yes: %s added, then on behind the '
                          'step; no: the step' % (build, len(gives), SECOND, SECOND),
                          sorted(dict(e.cases)[1] for e in placed) == sorted(gives)
                          and all(a.type == 'action' and name_of(a) == build_mod.SHOP_ADD
                                  and dict(a.params) == dict(build_mod.shop_add_params(SECOND))
                                  and a.next == game.events[dict(e.cases)[1]].next for a, e in zip(adds, placed))
                          and len(back.events) == n0 + 4 * len(picked) + 2 * len(gives), len(back.events) - n0)
            kept = all((o.type, o.name, o.params) == (b.type, b.name, b.params) for o, b in zip(game.events, back.events))
            good &= check('%s: the game\'s %d events are there as they were (their leads apart)' % (build, len(game.events)),
                          kept)
        # ---- three levels, and a first weapon's bag
        def flow_of(build):
            fc = evfl.loads(plain(build_mod.SHOP_SALE_FLOW, builds[build][1])).flowchart
            n0 = len(game.events)

            def name_of(e):
                return fc.actors[e.actor].name, (fc.actors[e.actor].actions[e.action] if e.type == 'action'
                                                 else fc.actors[e.actor].queries[e.query])

            def asks(value):
                return [e for e in fc.events[n0:] if e.type == 'switch' and name_of(e) == build_mod.SHOP_NAME_QUERY
                        and dict(e.params) == dict(name_params, Value=value)]

            def adds(e, item):
                return e.type == 'action' and name_of(e) == build_mod.SHOP_ADD \
                    and dict(e.params) == dict(build_mod.shop_add_params(item))

            return fc, n0, name_of, asks, adds

        fc, n0, name_of, asks, adds = flow_of('three')
        heads = [e for e in asks(BAGS[0])]
        ok = len(heads) == len(picked)
        for head in heads:
            on = dict(head.cases)[1]
            q2 = fc.events[dict(head.cases)[0]]                    # "has the second level?" stands first
            q1 = fc.events[dict(q2.cases)[ask[3]]] if q2.type == 'switch' else None
            for q, owned, written in ((q2, BAGS[1], BAGS[2]), (q1, BAGS[0], BAGS[1])):
                wr = fc.events[dict(q.cases)[ask[2]]] if q is not None and q.type == 'switch' else None
                wait = fc.events[wr.next] if wr is not None and wr.type == 'action' and wr.next is not None else None
                ok &= (wait is not None and name_of(q) == (build_mod.GIFT_PAIR_ACTOR, build_mod.GIFT_PAIR_QUERY)
                       and dict(q.params) == {'Num': 1, 'Actor': owned}
                       and dict(wr.params) == {'GameDataName': build_mod.SHOP_ITEM_VAR, 'Index': -1, 'Value': written}
                       and dict(wait.params).get('Frames') == build_mod.SCRUB_WRITE_WAIT and wait.next == on)
            ok &= q1 is not None and dict(q1.cases)[ask[3]] == on
        good &= check('three: behind each "shelf picked" step: is it %s? -> has %s? -> %s written; else has %s? -> %s '
                      'written; else on' % (BAGS[0], BAGS[1], BAGS[2], BAGS[0], BAGS[1]), ok)
        ok = True
        for later in BAGS[1:]:
            placed = asks(later)
            ok &= len(placed) == len(gives) and all(
                adds(fc.events[dict(e.cases)[0]], later) for e in placed)
        good &= check('three: in front of each of the %d giving steps: is it %s? -> added; is it %s? -> added; '
                      '%d new events in all' % (len(gives), BAGS[1], BAGS[2], len(fc.events) - n0),
                      ok and len(fc.events) == n0 + len(picked) * 7 + len(gives) * 4
                      and not [f for f in builds['three'][2] if 'BombBag_Medium' in f or 'BombBag_Large' in f])

        fc, n0, name_of, asks, adds = flow_of('weapons')
        game_adds = [e for e in game.events if e.type == 'action'
                     and (game.actors[e.actor].name, game.actors[e.actor].actions[e.action]) == build_mod.SHOP_ADD]
        ok = True
        for weapon, bag, family in ((SLING, 'Item_BulletBag_Small', True), (BOW, 'Item_Quiver_Small', False)):
            comes = [e for e in asks(weapon) if fc.events[dict(e.cases)[0]].type == 'action']
            ok &= len(comes) == len(gives) and all(
                adds(fc.events[dict(e.cases)[0]], bag) and fc.events[dict(e.cases)[0]].next is not None for e in comes)
            ok &= (len(asks(weapon)) - len(comes)) == (len(picked) if family else 0)
        good &= check('weapons: the game\'s sale flow adds nothing to the inventory by itself (%d %s steps); in front '
                      'of each giving step the Fairy Slingshot (a family\'s first level) comes with %s and the Fairy '
                      'Bow (alone on a shelf) with %s; the Slingshot\'s later levels are chosen as any family\'s'
                      % (len(game_adds), build_mod.SHOP_ADD[1], 'Item_BulletBag_Small', 'Item_Quiver_Small'),
                      ok and not game_adds and len(asks(SEEDS[1])) == len(gives) == len(asks(SEEDS[2])))

        # the Bomb Bag, the Fairy Slingshot and the Fairy Bow have a centred pose: lifted on the shelf by what
        # their model hangs under the shelf point (as the scales, tests/shop_shelf_keys_check.py)
        lows = {}
        for item in (BAGS[0], SEEDS[0], 'Item_Range_Bow'):
            pack = sarc.Sarc.read(plain(ground_items.pack_path(item))).files
            anims = byml.loads(pack[ground_items._ref_path(ground_items.resolved_components(pack, item)[
                'AnimationRef'])]).root['AnimationResources']
            project, = [x['ModelProjectName'] for x in anims if x['ModelProjectName'] != shop_items.COMMON_ANIM]
            pose = item_pose.read_pose(plain(item_pose.model_path(project)))
            points, bind, _ = item_pose.model_points(plain('Model/%s.%s.bfres' % (rows[item]['ModelProjectName'],
                                                                                  rows[item]['FmdbName'])))
            lows[item] = item_pose.extent(points, bind, pose['scale'], pose['rot'], pose['move'])[0][1]
        said = builds['three'][0] + builds['weapons'][0]
        good &= check('shelf lifts: the Bomb Bag, the Fairy Slingshot and the Fairy Bow stand on the shelf (lifted by '
                      'what hangs under the shelf point: %s)'
                      % ', '.join('%s %.2f for %.3f' % (k, shop_items.SHELF_LIFT.get(k, 0), -v)
                                  for k, v in sorted(lows.items())),
                      all(abs(shop_items.SHELF_LIFT.get(k, 0) + v) <= 0.01 for k, v in lows.items())
                      and said.count('shelf lift') == 3 and '0.19 m higher' in builds['three'][0]
                      and '0.18 m higher' in builds['weapons'][0] and '0.42 m higher' in builds['weapons'][0], lows)

        key = dungeon_keys.name(D, 'chest', True)
        both = evfl.loads(plain(build_mod.SHOP_SALE_FLOW, builds['both'][1])).flowchart
        good &= check('both: the dungeon key\'s questions (%d) stand in the flow beside the pair\'s' % (len(sold) + 1),
                      sum(1 for e in both.events if e.type == 'switch' and isinstance(e.params, dict)
                          and e.params.get('Value') == key) == len(sold) + 1)

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
