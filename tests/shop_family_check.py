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
- Refused: three levels on a shelf; the first level alone on one shelf and its pair on another.
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
import shop_items  # noqa: E402
from formats import zstd, byml, evfl, restbl  # noqa: E402
from logic.world import World  # noqa: E402

FIX = ['--fix', 'kokiri_shop_full_stock']
SHELF, SHELF2 = 'KF_KOKIRI_CHILD_SHOP_01', 'KF_KOKIRI_CHILD_SHOP_02'
FIRST, SECOND = 'Item_Scale_Silver', 'Item_Scale_Gold'
PAIR = '%s=%s>%s' % (SHELF, FIRST, SECOND)
D = 'ForestTemple'
BUILDS = {'pair': FIX + [PAIR],
          'both': FIX + [PAIR, '%s=Item_Dungeon_SmallKey@%s' % (SHELF2, D)]}
REFUSED = [(FIX + ['%s=Item_BombBag_Small>Item_BombBag_Medium>Item_BombBag_Large' % SHELF], None),
           (FIX + [PAIR, '%s=%s' % (SHELF2, FIRST)], 'alone on a shelf')]


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
