"""Progressive families on Gold Skulltulas test (tools/skulltula_items.py): every upgrade family of
tools/build_mod.py (FAMILIES) on a Gold Skulltula check. Checked on the game's own files: how a skulltula is
marked done (its drop's AI and the flag it is handed), what the game's drop code has for "dropped only once ..."
and "... until then this in its place", the saved yes/no "Link ever got" of every level; then what is built:
each level's drop (the token's marking kept, the new branch), the rows added to the drop code's two lists, what
a skulltula drops for everything Link can own (no level skipped, none given twice, the skulltula marked once),
what happens if the drop code does not replace as read (nothing wrong is ever picked up), and whole builds.
Only reads the game; the builds it runs go to a temporary folder that is removed again.

    python tests/skulltula_prog_check.py "C:\\...\\romfs"
"""
import contextlib
import glob
import io
import itertools
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import drop_tables  # noqa: E402
import ground_items  # noqa: E402
import once_items  # noqa: E402
import shop_items  # noqa: E402
import skulltula_items  # noqa: E402
import turn_items  # noqa: E402
from formats import zstd, byml, sarc, ainb  # noqa: E402
from logic.world import World  # noqa: E402

FAMILIES = build_mod.FAMILIES
WEAPONS = {'Item_Range_SlingShot': ('Weapon_Range_SlingShot', [('Item_BulletBag_Small', 1), ('Item_DekuSeed', 30)]),
           'Item_Range_Bow': ('Weapon_Range_Bow', [('Item_Quiver_Small', 1), ('Item_Arrow_Normal', 30)])}
# the Gold Skulltula checks of the mapped areas (the Lost Woods and the Meadow have no IDs yet: by name)
SKULLTULAS = ('KF_KNOW_IT_ALL_HOUSE_GS', 'KF_BEAN_PATCH_GS', 'KF_HOUSE_OF_TWINS_GS', 'LW GS Bean Patch Near Bridge',
              'LW GS Bean Patch Near Theater', 'LW GS Above Theater', 'SFM GS')
SKULLTULA = 'Enemy_Skulltula_Gold'
MARK = 'OneShotGoldTokenDeadAfter'
HAND_OVER = 'QueryBlackboardOverwriteParamAddNoRespawnGmdHash'
TOKEN_AI = 'AI/Item_Token_Gold.root.ainb'
SKULLTULA_AI = 'AI/Enemy_Skulltula_Gold.utility.root.ainb'
FLOW = 2


def check(name, ok):
    print('%-118s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def refused(f, *args, **kw):
    try:
        f(*args, **kw)
    except SystemExit:
        return True
    return False


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    rd = lambda p: zstd.decompress(open(p, 'rb').read(), d)   # noqa: E731

    def plain(path):
        p = os.path.join(romfs, *path.split('/'))
        return open(p, 'rb').read() if os.path.exists(p) else rd(p + '.zs')

    table_rows = lambda t: byml.loads(plain(ground_items.table_path(t))).root   # noqa: E731
    model = lambda project: os.path.exists(os.path.join(romfs, 'Model', project + '.anim.bfres.zs'))  # noqa: E731
    known = {r['__RowId']: r.get('ActorName') for r in table_rows('ActorInfo')}
    known_as = lambda item: known.get(item) or item   # noqa: E731
    world = World()
    good = True

    # ------------------------------------------------------------------------------ what the game's files show
    print('The game')
    token = sarc.Sarc.read(plain(ground_items.pack_path(ground_items.TOKEN))).files
    doc = ainb.loads(token[TOKEN_AI])
    root = doc.nodes[doc.commands[0].left]
    dead = doc.nodes[root.links[FLOW][0].node]                       # dead? -> by reason
    by_reason = doc.nodes[dict((l.name, l.node) for l in dead.links[FLOW])['True']]
    ten = [doc.nodes[l.node] for l in by_reason.links[FLOW] if tuple(l.extra) == (0, 10)]
    marks = [doc.nodes[l.node].name for n in ten for l in n.links[FLOW]]
    good &= check('the token marks its skulltula when it is picked up: its AI, dead with reason 10 -> %s' % MARK,
                  len(doc.nodes) == skulltula_items.BASE_NODES and MARK in marks
                  and doc.nodes[dead.inputs['bool'][0].node].name == 'QueryDeathIsDead')
    gs = sarc.Sarc.read(plain(ground_items.pack_path(SKULLTULA))).files
    hand = [n for n in ainb.loads(gs[SKULLTULA_AI]).nodes if n.name == HAND_OVER]
    table = byml.loads(token[ground_items.TOKEN_FILES[1]]).root
    keys = {e['BBKey']: e['InitVal'] for e in table.get('BlackboardParamU64Array', [])}
    good &= check('the skulltula hands its flag to its drop under the key the token has (%s)' % ground_items.TOKEN_KEY,
                  len(hand) == 1 and {x.name: x.value for x in hand[0].immediates['string']}.get('Key')
                  == ground_items.TOKEN_KEY and list(keys) == [ground_items.TOKEN_KEY])
    good &= check('  a table can only start that key with a 32-bit number (the game\'s is 0, stored as 32 bits): '
                  'the flag (64 bits) cannot be written into a second drop\'s table',
                  type(keys[ground_items.TOKEN_KEY]) is byml.UInt and keys[ground_items.TOKEN_KEY] == 0)
    flags = {int(e['Hash']): int(e['ResetTypeValue'])
             for e in byml.loads(plain(skulltula_items.GAME_DATA)).root['Data']['Bool64bitKey']}
    hashes = []
    for p in glob.glob(os.path.join(romfs, 'Banc', '**', '*.bcett.byml.zs'), recursive=True):
        hashes += [int(a['Hash']) for a in byml.loads(rd(p)).root.get('Actors', []) if a.get('Gyaml') == SKULLTULA]
    good &= check('every Gold Skulltula placement (%d) has its two saved flags, never reset (the two the token sets)'
                  % len(set(hashes)), len(set(hashes)) >= 100
                  and all(flags.get(h) == build_mod.FLAG_KEPT and flags.get(h ^ 2) == build_mod.FLAG_KEPT
                          for h in hashes))
    drop_file = plain(skulltula_items.DROP_GLOBAL)
    rows0, order0 = skulltula_items.drop_rows_read(drop_file)
    m = byml.loads(drop_file).root['DropLotteryMasterData']
    unlock0 = {turn_items._actor_of(u['Actor']): u['GameDataName'] for u in m['DropUnlockCondition']}
    good &= check('the drop code\'s lists: every actor that is "only dropped once a saved yes/no is true" (%d) has '
                  'a row "not unlocked -> another actor in its place"' % len(unlock0),
                  len(unlock0) == 10 and set(unlock0) <= set(rows0)
                  and all(rows0[a][0] == unlock0[a] and rows0[a][1] == [(100, 'Obj_Rupee_Green')] for a in unlock0))
    named = 0
    for p in glob.glob(os.path.join(romfs, 'Banc', '**', '*.bcett.byml.zs'), recursive=True):
        named += sum((a.get('Dynamic') or {}).get('Drop__DropActor') == 'Animal_Insect'
                     for a in byml.loads(rd(p)).root.get('Actors', []))
    good &= check('  the game itself has such an actor named by placements (Drop__DropActor: Animal_Insect, %d)'
                  % named, named > 0 and 'Animal_Insect' in unlock0)
    game_data = plain(skulltula_items.GAME_DATA)
    ok = all(skulltula_items.got_flag(game_data, known_as(x)) == 'IsGet.' + known_as(x)
             for f in FAMILIES.values() for x in f[:-1])
    good &= check('every level but the last of every family has its saved "Link ever got it" (IsGet.<name>), under '
                  'the name the inventory knows it by', ok and refused(skulltula_items.got_flag, game_data,
                                                                      'Item_Range_SlingShot')
                  and skulltula_items.mm3('IsGet.Item_Scale_Silver') == skulltula_items.mm3('IsGet.Item_Scale_Silver')
                  and skulltula_items.mm3('') == 0)

    # ---------------------------------------------------------------------------------- what is built
    print('The drops')
    shared = sarc.Sarc.read(plain(skulltula_items.AI_PACK)).files
    built, ok, kept, branch, bags, rows_ok, plain_ok = {}, True, True, True, True, True, True
    for n, family in FAMILIES.items():
        for level, item in enumerate(family):
            weapon = WEAPONS.get(item) if level == 0 else None
            name, pack, new_inner, rows, loose = skulltula_items.build(family, level, plain, table_rows, model,
                                                                       weapon[0] if weapon else None)
            files = sarc.Sarc.read(pack).files
            built[item] = (name, files)
            base = ground_items.build(item, plain, table_rows, model, 'token')
            base_files = sarc.Sarc.read(base[1]).files
            ai = skulltula_items.ai_name(item)
            comp = ground_items.resolved_components(files, name)
            base_comp = ground_items.resolved_components(base_files, base[0])
            # the token version of that level under another name, with an AI of its own: every other file as it is
            same = {p.replace(base[0], name): x for p, x in base_files.items()
                    if p != ground_items.ap_path(base[0])}
            ok &= name == skulltula_items.drop_name(item) and name.startswith(skulltula_items.PREFIX) \
                and all(files.get(p) == x for p, x in same.items()) \
                and set(files) - set(same) == {ground_items.ap_path(name), shop_items.ai_path(ai),
                                               shop_items.ai_info_path(ai)} \
                and {k: v for k, v in comp.items() if k != 'AIInfoRef'} \
                == {k: v.replace(base[0], name) for k, v in base_comp.items() if k != 'AIInfoRef'} \
                and comp['AIInfoRef'] == '?' + shop_items.ai_info_path(ai)
            # what marks the skulltula: the token's blackboard table (the key), its death settings, its 12 nodes
            new_doc, old_doc = ainb.loads(files[shop_items.ai_path(ai)]), ainb.loads(token[TOKEN_AI])
            new_root = new_doc.nodes[new_doc.commands[0].left]
            kept &= all(comp.get(r) == v for r, v in ground_items.TOKEN_KEEPS.items() if r != 'AIInfoRef') \
                and files[ground_items.TOKEN_FILES[1]] == token[ground_items.TOKEN_FILES[1]] \
                and files[TOKEN_AI] == token[TOKEN_AI] \
                and all(shop_items._node_state(a) == shop_items._node_state(b)
                        for i, (a, b) in enumerate(zip(old_doc.nodes, new_doc.nodes))
                        if i != new_doc.commands[0].left) \
                and [(l.node, l.name) for l in new_root.links[FLOW][:2]] \
                == [(l.node, l.name) for l in old_doc.nodes[old_doc.commands[0].left].links[FLOW]]
            what = skulltula_items.describe(files[shop_items.ai_path(ai)])
            branch &= what['token'] and what['previous'] == (family[level - 1] if level else None) \
                and what['taken'] == list(family[level:]) \
                and what['guards'] == [q for q, _ in turn_items.GUARDS] + [turn_items.Q_ASKED] \
                and what['name'] == ai + '.root' and (what['bundle'] is None) == (weapon is None)
            plain_ok &= weapon is not None or (what['own'] is None and what['bundle'] is None)
            if weapon:
                gives = [(turn_items._actor_of(x), k) for x, k in what['bundle']['gives']]
                turn = turn_items.describe(sarc.Sarc.read(turn_items.build(family, 0, plain, table_rows, model,
                                                                           weapon[0])[1]).files[
                    shop_items.ai_path(turn_items.ai_name(item))])
                bags &= gives == weapon[1] and what['bundle']['bag'] == weapon[1][0][0] and what['own'] == item \
                    and what['bundle'] == turn['bundle']
            rows_ok &= {t: r['__RowId'] for t, r in rows.items()} == {t: name for t in ground_items.TABLES} \
                and all({k: v for k, v in rows[t].items() if k not in ('__RowId', 'InstanceHeapSize')}
                        == {k: v for k, v in base[3][t].items() if k not in ('__RowId', 'InstanceHeapSize')}
                        for t in rows) \
                and int(rows['ActorInfo']['InstanceHeapSize']) > int(base[3]['ActorInfo']['InstanceHeapSize'])
    good &= check('every level of every family (%d): the token version of that level under a name of its own, '
                  'with an AI of its own and nothing else changed'
                  % len(built), ok and len(built) == sum(len(f) for f in FAMILIES.values()))
    good &= check('  each keeps what marks the skulltula: the token\'s blackboard key, its death settings, and its '
                  '12 AI nodes as they are (the root only runs our branch beside them)', kept)
    good &= check('  the new branch: the turning items\' four guards, then "Link does not own the level before" -> '
                  'delete itself (first levels: no such question), then "Link owns this level or a later one" -> '
                  'delete itself', branch)
    good &= check('  the Fairy Slingshot and the Fairy Bow give what a chest gives with them (the small bag, 30 '
                  'seeds or arrows), as their turning items do, while Link has no small bag', bags)
    good &= check('  their table rows: the token version\'s under the new name, with more memory for the AI', rows_ok)
    good &= check('  a first level that is no weapon gives nothing more with itself', plain_ok)

    # ------------------------------------------------------------------------------------ the two lists
    print('The drop code\'s lists')
    chains = {n: skulltula_items.chain(f, known_as) for n, f in FAMILIES.items()}
    new, added = skulltula_items.drop_rows(drop_file, list(chains.values()))
    rows1, order1 = skulltula_items.drop_rows_read(new)
    ok = True
    for n, f in FAMILIES.items():
        names = [x for x, _ in chains[n]]
        ok &= names == [skulltula_items.drop_name(x) for x in f]
        for k in range(1, len(f)):
            ok &= rows1[names[k]] == ('IsGet.' + known_as(f[k - 1]), [(100, names[k - 1])])
        ok &= names[0] not in rows1
    good &= check('one row in each list per level but the first: "dropped once Link ever got the level before", '
                  '"until then the level before in its place" (%d rows)' % len(added),
                  ok and len(added) == sum(len(f) - 1 for f in FAMILIES.values()))
    good &= check('  the game\'s own rows are as they were, in their places; ours come after them, a family\'s '
                  'highest level first',
                  {a: rows1[a] for a in rows0} == rows0 and order1[:len(order0)] == order0
                  and all(order1.index(chains[n][k][0]) < order1.index(chains[n][k - 1][0])
                          for n, f in FAMILIES.items() for k in range(2, len(f)))
                  and skulltula_items.drop_rows(new, list(chains.values()))[1] == {})
    good &= check('  refused: rows for an actor that already has other rows',
                  refused(skulltula_items.drop_rows, new, [[('Obj_NX2_GS_Scale_Silver', 'IsGet.Item_Hookshot'),
                                                           ('Obj_NX2S_Scale_Gold', 'x')]]))

    # what a skulltula gives, for everything Link can own when it dies: the drop code as read, then the dropped
    # level's own branch (it deletes itself while Link does not own the level before, and once he owns it or a
    # later level)
    def alive(family, k, owned):
        """whether the drop of level k stays (can be picked up) while Link owns `owned`"""
        return (not k or family[k - 1] in owned) and not any(x in owned for x in family[k:])

    def gives(family, names, owned, got, replace=99):
        """the level picked up from a skulltula of `family` (None: nothing lies there). owned: what the inventory
        holds; got: the levels Link ever got; replace: how many times the drop code replaces (as read: as often
        as needed)"""
        actor, k = names[-1], len(names) - 1
        while k and family[k - 1] not in got and replace:
            actor, k, replace = names[k - 1], k - 1, replace - 1
        if actor != skulltula_items.decide(rows1, names[-1], lambda flag: flag in {
                'IsGet.' + known_as(x) for x in got}) and replace == 99:
            raise SystemExit('the model and the rows disagree')
        if not alive(family, k, owned):
            return None                                # its own branch: deletes itself
        return family[k]

    order_ok, once_ok, safe_ok, extra_ok, twice_ok = True, True, True, True, True
    for n, f in FAMILIES.items():
        names = [x for x, _ in chains[n]]
        # every set of levels Link can own: the lowest level he never got, never one he has, never one too high
        for r in range(len(f) + 1):
            owned = set(f[:r])
            g = gives(f, names, owned, owned)
            order_ok &= g == (f[r] if r < len(f) else None)
        # as many skulltulas as levels, killed one after the other (each drop picked up, or left and the
        # skulltula killed again later): the levels in order, each skulltula marked by the one drop it gave
        for leave in itertools.product((False, True), repeat=len(f)):
            owned, marked, out = set(), [], []
            for s in range(len(f)):
                if leave[s]:                            # the drop is left lying: gone with the area, not marked
                    first = gives(f, names, owned, owned)
                    once_ok &= first == f[len(owned)]
                g = gives(f, names, owned, owned)
                out.append(g)
                owned.add(g)
                marked.append(s)                        # the drop is the skulltula's own: marks it when picked up
            once_ok &= out == list(f) and marked == list(range(len(f)))
        # one skulltula more than levels: what it drops removes itself (Link has every level), nothing is marked
        extra_ok &= gives(f, names, set(f), set(f)) is None
        # two drops of one family made before either is picked up (both the same level), or the level got
        # somewhere else while a drop lay there: once Link owns that level, the drop lying there removes itself
        for k in range(len(f)):
            twice_ok &= alive(f, k, set(f[:k])) and not alive(f, k, set(f[:k + 1])) \
                and not any(alive(f, k, set(f[:k]) | {x}) for x in f[k:])
        # should the drop code not replace at all, or only once: nothing that skips a level is ever picked up
        for r in range(len(f) + 1):
            owned = set(f[:r])
            for times in (0, 1):
                g = gives(f, names, owned, owned, replace=times)
                safe_ok &= g is None or g == (f[r] if r < len(f) else f[-1]) or g in owned
                safe_ok &= g is None or f.index(g) <= r
    good &= check('a skulltula drops the lowest level Link never got, whatever he owns (every family, every state)',
                  order_ok)
    good &= check('  as many skulltulas as levels, drops taken or left and fetched later: every level once, in '
                  'order, and every skulltula marked by the one drop it gave', once_ok)
    good &= check('  one skulltula more than the family has levels: its drop removes itself, nothing marked',
                  extra_ok)
    good &= check('  a level Link already owns (two drops lying at once, or got elsewhere while it lay there) '
                  'removes itself: no level given twice', twice_ok)
    good &= check('  should the drop code replace less than read (not at all, or once): a level that would skip one '
                  'deletes itself, nothing wrong can be picked up', safe_ok)

    # ------------------------------------------------------------------------------------- whole builds
    # Since 2026-11-22 a family on a Gold Skulltula is the one-time turning item a rock drops
    # (tools/once_items.py): in game the drop code never put a lower level in place, so the rows and drops
    # checked above are not used by builds any more
    print('Whole builds')
    good &= check('a family on a Gold Skulltula is planned as a Gold Skulltula\'s (not as a chest\'s or a '
                  'freestanding item\'s)',
                  all(build_mod.skulltula_pair_kind(world, c) for c in SKULLTULAS)
                  and not build_mod.skulltula_pair_kind(world, 'KF_MIDO_CHEST_01')
                  and refused(build_mod.pair_kind, world, SKULLTULAS[0]))
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *assign):
            with contextlib.redirect_stdout(io.StringIO()) as said:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(assign))
            base = os.path.join(tmp, name, 'romfs')
            return base, said.getvalue(), {os.path.relpath(f, base).replace(os.sep, '/')
                                           for f in glob.glob(os.path.join(base, '**', '*'), recursive=True)
                                           if os.path.isfile(f)}

        fams = list(FAMILIES.items())
        ok, maps_ok, packs_ok, other_ok, untouched_ok = True, True, True, True, True
        for part, some in enumerate((fams[:6], fams[6:])):
            placed = dict(zip(SKULLTULAS, some))
            extra = ['KF_MIDO_CHEST_01=Item_Boomerang'] + (['%s=Item_Bottle' % SKULLTULAS[6]] if part else [])
            base, said, files = run('gs%d' % part, *(['%s=%s' % (c, '>'.join(f)) for c, (n, f) in placed.items()]
                                                    + extra))
            changed = {p['hash'] for c in list(placed) + ([SKULLTULAS[6]] if part else [])
                       for _, _, p in world.placements_of(*build_mod.find_check(world, c)[::2])}
            for c, (n, f) in placed.items():
                r, _, loc = build_mod.find_check(world, c)
                for scene, spot_id, p in world.placements_of(r, loc):
                    for fn in p['files']:
                        path = os.path.join(base, 'Banc', scene, fn)
                        acts = {str(int(a['Hash'])): a for a in byml.loads(rd(path)).root['Actors']}
                        orig = {str(int(a['Hash'])): a for a in byml.loads(
                            rd(os.path.join(romfs, 'Banc', scene, fn))).root['Actors']}
                        a = acts[p['hash']]
                        maps_ok &= a['Gyaml'] == SKULLTULA \
                            and a['Dynamic'].get('Drop__DropActor') == once_items.once_name(f[0]) \
                            and {k: v for k, v in a['Dynamic'].items() if k != 'Drop__DropActor'} \
                            == {k: v for k, v in dict(orig[p['hash']].get('Dynamic') or {}).items()
                                if k != 'Drop__DropActor'} \
                            and all(acts[h] == o for h, o in orig.items() if h not in changed and o['Gyaml'] == SKULLTULA)
                ok &= ('a turning item as the skulltula\'s drop: %s on the ground while Link has no %s, then %s'
                       % (f[0], f[0], f[1])) in said
                packs_ok &= all(('Pack/Actor/%s.pack.zs' % once_items.once_name(x)) in files
                                and ('once   version %-22s for %s' % (once_items.once_name(x), x)) in said for x in f)
            info = {r['__RowId'] for r in byml.loads(rd(os.path.join(
                base, *ground_items.table_path('ActorInfo').split('/')) + '.zs')).root}
            packs_ok &= all(once_items.once_name(x) in info for c, (n, f) in placed.items() for x in f)
            # nothing of the drop code's way: its lists, the skulltula's own pack, the Obj_NX2S_ drops
            untouched_ok &= skulltula_items.DROP_GLOBAL not in files \
                and (ground_items.pack_path(SKULLTULA) + '.zs') not in files \
                and not any('/Obj_NX2S_' in x for x in files)
            if part:                                    # a plain item on a skulltula beside them: as before
                other_ok &= 'Pack/Actor/Obj_NX2_GS_Bottle.pack.zs' in files
        good &= check('all %d families build on Gold Skulltulas (two builds): each is a turning item as the '
                      'skulltula\'s drop' % len(fams), ok)
        good &= check('  the skulltula\'s placement names the first level\'s one-time turning item (Drop__DropActor); '
                      'nothing else of it, and no other skulltula, changes', maps_ok)
        good &= check('  every level\'s one-time turning item is in the mod (pack and table row)', packs_ok)
        good &= check('  the drop code\'s lists, the skulltula\'s own pack and the Obj_NX2S_ drops are not in the mod',
                      untouched_ok)
        good &= check('  a plain item on another skulltula is the plain token version', other_ok)
        base, said, files = run('none', 'KF_MIDO_CHEST_01=Item_Scale_Silver>Item_Scale_Gold',
                                '%s=Item_Scale_Silver' % SKULLTULAS[0])
        good &= check('a build without a family on a skulltula: its plain item is the token version, no turning item',
                      skulltula_items.DROP_GLOBAL not in files and 'Pack/Actor/Obj_NX2_GS_Scale_Silver.pack.zs' in files
                      and not any('/Obj_NX2S_' in f or '/Obj_NX2Q_' in f for f in files))
        # (a family on a pot builds since 2026-11-22: tests/one_time_check.py)
        good &= check('still refused: a later level alone on a skulltula, a family that is none, a family on a '
                      'shelf',
                      refused(run, 'no1', '%s=Item_Scale_Gold' % SKULLTULAS[0])
                      and refused(run, 'no2', '%s=Item_Scale_Gold>Item_Scale_Silver' % SKULLTULAS[0])
                      and refused(run, 'no4', 'KF_KOKIRI_CHILD_SHOP_01=Item_Scale_Silver>Item_Scale_Gold'))

    print()
    print('ALL OK' if good else 'SOME CHECKS FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
