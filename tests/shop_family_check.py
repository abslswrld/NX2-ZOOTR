"""Phase 2, parts 1 and 3: an upgrade family on a shop shelf (to test in game).

    python tests/shop_family_check.py "<romfs>"

What it checks:
- From the game's files: the shops' shared sale flow (DisplayShop) puts the shelf's item in the inventory
  with one of five steps, each with a next step; no shelf of the game is named as a pair's second level; the
  game's own inventory question and its name write (the scrubs') are found.
- A family's shelf is a shelf of its own that Link can never have (in game 2026-11-27 the Bomb Bag's shop
  version said "Sold out" once Link had a Bomb Bag): named itself in its row and its name file, its label the
  first level's name, "not put in the inventory" in its item settings and its row as the game's heart shelf.
- The sale flow does the rest, read back for Silver Scale > Gold Scale, for the three bomb bags and for the
  Fairy Slingshot's family: behind each of the two "shelf picked" steps, before the shopkeeper names the item,
  "is it the shelf?" -> the inventory questions, the highest level first -> the name of the level Link gets
  next written into Shop_SelectItemName (the first level's when Link has none), two frames, then on; in front
  of each of the five giving steps "is it <that level>?" -> the level added (the first level with what it
  needs: the Fairy Slingshot with its seed bag) and the shelf's own step passed by. Nothing else of the flow
  changed.
- The pair's build with a dungeon's small key on another shelf: both changes stand in the flow.
- Refused: two upgrades of one family in one shop (decision 51): the pair on two shelves, the pair beside its
  first level alone, one level alone on two shelves.
- A first weapon alone on a shelf (the Fairy Bow) is its own shop version and comes with its small bag (from
  the game's files: a shelf's own steps give nothing but its item).
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
from formats import zstd, byml, evfl, restbl, sarc, msbt  # noqa: E402
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

        # ---- a family's shelf: a shelf of its own that Link can never have; the sale flow does the rest
        heart = sarc.Sarc.read(plain(ground_items.pack_path(shop_items.NOT_PUSHED_SHELF))).files
        not_pushed = byml.loads(heart[ground_items._ref_path(ground_items.resolved_components(
            heart, shop_items.NOT_PUSHED_SHELF)['PouchContentRef'])]).root['SpecialDeal']

        def family(build, shelf, levels, names, comes_with, n0):
            """the checks of one family's shelf in a build; levels: the items; names: what the inventory knows
            them by; comes_with: what the first level needs; n0: the flow's events before the family's edit"""
            ok_all = True
            out, folder, files = builds[build]
            first = levels[0]
            packs = [f for f in files if f.startswith('Pack/Actor/%s%s_' % (shop_items.PREFIX, first[len('Item_'):]))]
            name = os.path.basename(packs[0])[:-len('.pack.zs')] if len(packs) == 1 else ''
            r, _, loc = build_mod.find_check(w, shelf)
            maps = [plain('Banc/%s/%s' % (scene, fn[:-3] if fn.endswith('.zs') else fn), folder)
                    for scene, _, pl in w.placements_of(r, loc) for fn in pl['files']]
            pack = sarc.Sarc.read(plain(packs[0][:-3], folder)).files if name else {}
            comp = ground_items.resolved_components(pack, name) if name else {}
            sroot = byml.loads(pack[ground_items._ref_path(comp['PouchContentRef'])]).root if name else {}
            arow = {x['__RowId']: x for x in byml.loads(plain(ground_items.table_path('ActorInfo'), folder)).root}
            prow = {x['__RowId']: x for x in byml.loads(plain(ground_items.table_path('PouchActorInfo'), folder)).root}
            mals = [f for f in files if f.startswith('Mals/USen')]
            texts = msbt.Msbt.read(sarc.Sarc.read(plain(mals[0][:-3], folder)).files[
                dungeon_keys.MESSAGE_FILE]).texts if mals else {}
            ok_all &= check('%s: %s (%s): the shelf is %s, a shelf of its own: in the map, named itself (row and name '
                            'file), its label the first level\'s name, "not put in the inventory" in its item '
                            'settings and its row (as the game\'s %s); no shop version of another level'
                            % (build, shelf, ' > '.join(levels), name, shop_items.NOT_PUSHED_SHELF),
                            name.endswith('_Family') and any(m is not None and name.encode() in m for m in maps)
                            and arow.get(name, {}).get('ActorName') == name
                            and comp.get('ActorNameRef') == shop_items.NAME_REF % name
                            and sroot.get('SpecialDeal') == not_pushed and 'PouchActor' not in sroot
                            and prow.get(name, {}).get('PouchSpecialDeal') == shop_items.NOT_PUSHED
                            and not set(prow.get(name, {})) - set(shop_items.FAMILY_ROW)
                            and texts.get(name + '_Name') == texts.get(names[0] + '_Name') is not None
                            and not [f for f in files for x in levels[1:] if x[len('Item_'):] + '_' in f
                                     and f.startswith('Pack/Actor/' + shop_items.PREFIX)],
                            (packs, sroot, prow.get(name)))
            fc = evfl.loads(plain(build_mod.SHOP_SALE_FLOW, folder)).flowchart

            def name_of(e):
                return fc.actors[e.actor].name, (fc.actors[e.actor].actions[e.action] if e.type == 'action'
                                                 else fc.actors[e.actor].queries[e.query])

            def asks(value):
                return [e for e in fc.events[n0:] if e.type == 'switch' and name_of(e) == build_mod.SHOP_NAME_QUERY
                        and dict(e.params) == dict(name_params, Value=value)]

            def adds(e, item):
                return e.type == 'action' and name_of(e) == build_mod.SHOP_ADD \
                    and dict(e.params) == dict(build_mod.shop_add_params(item))

            def writes(i, value, on):
                wr = fc.events[i]
                wait = fc.events[wr.next] if wr.type == 'action' and wr.next is not None else None
                return (wait is not None and name_of(wr) == ('GameDataActor', build_mod.SCRUB_NAME_WRITE)
                        and dict(wr.params) == {'GameDataName': build_mod.SHOP_ITEM_VAR, 'Index': -1, 'Value': value}
                        and name_of(wait) == ('EventSystemActor', 'EventWait')
                        and dict(wait.params).get('Frames') == build_mod.SCRUB_WRITE_WAIT and wait.next == on)

            heads = asks(name)
            ok = len(heads) == len(picked) and sorted(fc.events[f].next for f in picked) == sorted(
                fc.events.index(h) for h in heads)
            for head in heads:                          # behind each "shelf picked" step
                on = dict(head.cases)[1]
                ok &= on in [game.events[f].next for f in picked]
                at = dict(head.cases)[0]
                for k in reversed(range(1, len(levels))):          # the highest level is asked about first
                    q = fc.events[at]
                    ok &= (q.type == 'switch' and name_of(q) == (build_mod.GIFT_PAIR_ACTOR, build_mod.GIFT_PAIR_QUERY)
                           and dict(q.params) == {'Num': 1, 'Actor': names[k - 1]}
                           and writes(dict(q.cases)[ask[2]], names[k], on))
                    if not ok:
                        break
                    at = dict(q.cases)[ask[3]]
                ok = ok and writes(at, names[0], on)
            ok_all &= check('%s: behind each of the %d "shelf picked" steps, before the shopkeeper names the item: is '
                            'it %s? -> %s; has none -> %s; each written into %s, %d frames, then on'
                            % (build, len(picked), name, '; '.join(
                                'has %s -> %s' % (names[k - 1], names[k]) for k in reversed(range(1, len(levels)))),
                               names[0], build_mod.SHOP_ITEM_VAR, build_mod.SCRUB_WRITE_WAIT), ok)
            ok = True
            for k, (item, known) in enumerate(zip(levels, names)):
                placed = asks(known)
                ok &= len(placed) == len(gives)
                for e in placed:
                    at = dict(e.cases)[0]
                    for c in (comes_with if k == 0 else ()):
                        ok &= adds(fc.events[at], c)
                        at = fc.events[at].next
                    ok &= adds(fc.events[at], item) and fc.events[at].next in [game.events[g].next for g in gives]
            new = len(picked) * 3 * len(levels) + len(gives) * (2 * len(levels) + len(comes_with))
            ok_all &= check('%s: in front of each of the %d giving steps: is it %s? -> %sadded, then on behind the '
                            'step (the shelf itself gives nothing); %d new events'
                            % (build, len(gives), '? / '.join(names),
                               '%s and the first level ' % ', '.join(comes_with) if comes_with else 'that level ', new),
                            ok and len(asks(name)) == len(picked), (len(fc.events) - n0, new))
            return ok_all, fc, new

        n_game = len(game.events)
        n_key = len(sold) * 2 + 1
        ok, fc, new = family('pair', SHELF, (FIRST, SECOND), (FIRST, SECOND), [], n_game)
        good &= ok
        good &= check('pair: the game\'s %d events are there as they were (their leads apart); %d events in all'
                      % (n_game, len(fc.events)),
                      all((o.type, o.name, o.params) == (b.type, b.name, b.params) for o, b in zip(game.events, fc.events))
                      and len(fc.events) == n_game + new)
        ok, fc, new = family('both', SHELF, (FIRST, SECOND), (FIRST, SECOND), [], n_game + n_key)
        good &= ok and len(fc.events) == n_game + n_key + new
        ok, fc, new = family('three', SHELF, BAGS, BAGS, [], n_game)
        good &= ok and len(fc.events) == n_game + new
        ok, fc, new = family('weapons', SHELF, SEEDS, (SLING,) + SEEDS[1:], ['Item_BulletBag_Small'], n_game)
        good &= ok

        # ---- a first weapon alone on a shelf: its own shop version, and its bag in front of the shelf's step
        game_adds = [e for e in game.events if e.type == 'action'
                     and (game.actors[e.actor].name, game.actors[e.actor].actions[e.action]) == build_mod.SHOP_ADD]
        alone = [e for e in fc.events[n_game:] if e.type == 'switch'
                 and (fc.actors[e.actor].name, fc.actors[e.actor].queries[e.query]) == build_mod.SHOP_NAME_QUERY
                 and dict(e.params) == dict(name_params, Value=BOW)]
        bags = [fc.events[dict(e.cases)[0]] for e in alone]
        good &= check('weapons: the game\'s sale flow adds nothing to the inventory by itself (%d %s steps); the Fairy '
                      'Bow alone on a shelf is its own shop version (%s), and in front of each of the %d giving steps '
                      '"is it %s?" adds %s and leads on to the shelf\'s own step'
                      % (len(game_adds), build_mod.SHOP_ADD[1], 'sold once', len(gives), BOW, 'Item_Quiver_Small'),
                      not game_adds and len(alone) == len(gives)
                      and all(b.type == 'action' and dict(b.params) == dict(build_mod.shop_add_params('Item_Quiver_Small'))
                              and b.next is not None for b in bags)
                      and len(fc.events) == n_game + new + len(gives) * 2
                      and any(f for f in builds['weapons'][2] if f.startswith('Pack/Actor/%sRange_Bow_' % shop_items.PREFIX)
                              and f.endswith('_Once.pack.zs')), len(fc.events) - n_game)

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
