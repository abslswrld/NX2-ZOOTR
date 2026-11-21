"""Turning items test: what tools/turn_items.py and tools/build_mod.py make of a progressive pair on a
freestanding item, on the game's own files. Reads only; writes nothing.

    python tests/ground_prog_check.py "C:\\...\\romfs"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import ground_items  # noqa: E402
import item_pose  # noqa: E402
import shop_items  # noqa: E402
import sizes  # noqa: E402
import turn_items  # noqa: E402
from formats import zstd, byml, sarc, ainb  # noqa: E402
from logic.world import World  # noqa: E402

MAP = 'Banc/KokiriForest/KokiriForest_Child_Dynamic.bcett.byml'
SPOTS = ('KF_RUPEE_NEAR_MIDO_ITEM', 'KF_RUPEE_NEAR_FADO_ITEM_01')    # two freestanding blue rupees (child)
PAIR = ('Item_Scale_Silver', 'Item_Scale_Gold')
GUARDS = ['QueryDeathIsDead', 'QueryEventMemberIsEventMemberSomeReason', 'QueryIsPlayingMainEvent']
# one check of each kind a pair is refused on
REFUSED = ('KF_KOKIRI_CHILD_SHOP_01', 'KF_HOUSE_OF_TWINS_CHILD_POT_01', 'KF_CIRCLE_CENTER_ROCK',
           'KF_NEAR_SARIAS_HOUSE_CHILD_BUSH_01', 'KF_KNOW_IT_ALL_HOUSE_GS', 'LW_SARIA_GIFT', 'LW_NEAR_BRIDGE_SCRUB')
CLOSE = ('KF_SARIAS_HOUSE_HEART_ITEM_03', 'KF_SARIAS_HOUSE_HEART_ITEM_04')     # 1.4 m apart
# what the drop kinds' entries are in the game: the constant over the size rounded up to 32, for a file with
# one element in its list (fitted on the game's files of each kind, out/RESEARCH_ground_progressive.md)
DROP_ENTRY = {'game__component__DropParam': 5136 + 8, 'game__drop__DropTable': 5112 + 8,
              'game__drop__DropSubTable': 5472}


def check(name, ok):
    print('%-86s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def refused(f, *args):
    try:
        f(*args)
    except SystemExit:
        return True
    return False


def shape(n, children=None):
    """what a node is, apart from where it sits: its number, its links' targets, the query its input reads, and
    the two values a turning AI sets (the name asked for, the drop switch)"""
    links = {(lt, l.name, l.extra) for lt, ls in enumerate(n.links) for l in ls}
    return (n.type, n.name, n.flags, n.name_hash, n.exb_count, n.exb_size, len(n.attachments),
            tuple((t, x.name, x.value, x.flags) for t in ainb.PARAM_TYPES for x in n.immediates[t]),
            tuple((t, x.name, x.flags, x.cls, x.node >= 0,
                   None if (n.name, x.name) in (('QueryGetPouchContentNumByActorName', 'ActorName'),
                                                ('OneShotDropSetDropValid', 'IsValid')) or x.node >= 0 else x.value)
                  for t in ainb.PARAM_TYPES for x in n.inputs[t]),
            tuple((t, x.name, x.flag, x.cls) for t in ainb.PARAM_TYPES for x in n.outputs[t]),
            frozenset(links), len(n.preconditions))


def equip_row(item):
    """the row fields an ocarina's ground and turning versions add: the real ocarina named as Link's equipment
    (tools/ground_items.py, "An ocarina on the ground"); none for other items"""
    if item not in ('Item_Ocarina_Fairy', 'Item_Ocarina_Time'):
        return {}
    path = 'Work/Actor/%s.engine__actor__ActorParam.gyml' % item
    return {k: path for k in ground_items.EQUIP_ROW}


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    plain = lambda path: zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)  # noqa: E731
    table_rows = lambda t: byml.loads(plain(ground_items.table_path(t))).root   # noqa: E731
    model = lambda project: os.path.exists(os.path.join(romfs, 'Model', project + '.anim.bfres.zs'))  # noqa: E731
    rows = {t: {r['__RowId']: r for r in table_rows(t)} for t in ground_items.TABLES}
    world = World()
    good = True

    # where a pair goes
    good &= check('a pair on a freestanding item is a turning item, in a chest a checking chest',
                  [build_mod.pair_kind(world, c) for c in SPOTS + ('KF_MIDO_CHEST_01',)]
                  == ['freestanding', 'freestanding', 'chest'])
    good &= check('a pair is refused on a shelf, a pot, a rock, a bush, a Gold Skulltula, a gift and a scrub',
                  all(refused(build_mod.pair_kind, world, c) for c in REFUSED))
    good &= check('only the listed pairs, first level first',
                  all(len(p) == 2 and p[::-1] not in build_mod.PROGRESSIVE_PAIRS
                      for p in build_mod.PROGRESSIVE_PAIRS) and PAIR in build_mod.PROGRESSIVE_PAIRS)
    good &= check('families of three levels are refused',
                  refused(turn_items.build, PAIR + ('Item_Hookshot',), 0, plain, table_rows, model))
    far = build_mod.turn_spacing(world, {c: PAIR for c in SPOTS})
    good &= check('the two test spots are far apart (%.1f m)' % (far[0][2] if far else 0),
                  len(far) == 1 and far[0][2] > 20)
    good &= check('two items of one family %.1f m apart or less are refused; of two families not'
                  % build_mod.TURN_MIN_DISTANCE,
                  refused(build_mod.turn_spacing, world, {c: PAIR for c in CLOSE})
                  and build_mod.turn_spacing(world, {CLOSE[0]: PAIR, CLOSE[1]: ('Item_Hookshot', 'Item_Longshot')})
                  == [])

    # the map: the two placements get First's turning item, nothing else changes
    first = turn_items.turn_name(PAIR[0])
    planned = build_mod.plan(world, [(c, first) for c in SPOTS])
    old = plain(MAP)
    before = {str(int(a['Hash'])): a for a in byml.loads(old).root['Actors']}
    good &= check('both spots are freestanding blue rupees of the child map, one placement each',
                  list(planned) == [MAP] and len(planned[MAP]) == 2
                  and all(v[2:] == ('Obj_Rupee_Blue', 'freestanding') and before[h]['Gyaml'] == 'Obj_Rupee_Blue'
                          for h, v in planned[MAP].items()))
    new, found, _ = build_mod.patch_file(old, planned[MAP])
    ok = len(byml.loads(new).root['Actors']) == len(before)
    for a in byml.loads(new).root['Actors']:
        h = str(int(a['Hash']))
        ok &= a == (dict(before[h], Gyaml=first) if h in planned[MAP] else before[h])
    good &= check('the two placements become %s; nothing else changes' % first, ok)

    # the actors and their AI, for every pair
    shared = sarc.Sarc.read(plain(turn_items.AI_PACK)).files
    base = ainb.loads(shared[shop_items.ai_path(turn_items.BASE_AI)])
    sources = [base] + [ainb.loads(shared[p]) for p in turn_items.SOURCES.values()]
    sources.append(ainb.loads(sarc.Sarc.read(plain(ground_items.pack_path(turn_items.DROP_ACTOR)))
                              .files[turn_items.DROP_AI]))
    game_shapes = {shape(n) for doc in sources for n in doc.nodes}
    # a sequence keeps its kind of child link whatever their number
    game_names = {(n.type, n.name) for doc in sources for n in doc.nodes}
    root = base.commands[0].left
    fly = sarc.Sarc.read(plain(ground_items.pack_path(turn_items.DROP_TEMPLATE))).files
    out = build_mod.Output(romfs, None, d)
    ai_ok = copies = branch = names_ok = packs = rows_ok = drops = size_ok = lift_ok = True
    lifted = set()
    said = []
    for family in sorted(build_mod.PROGRESSIVE_PAIRS):
        for level, item in enumerate(family):
            last = level == 1
            name, pack, new_inner, new_rows, loose = turn_items.build(family, level, plain, table_rows, model)
            files = sarc.Sarc.read(pack).files
            ai = turn_items.ai_name(item)
            short = item[len('Item_'):]
            names_ok &= name == 'Obj_NX2P_' + short and ai == 'NX2_Turn_' + short \
                and name not in rows['ActorInfo'] and len(name) <= 63
            data = files[shop_items.ai_path(ai)]
            doc = ainb.loads(data)
            what = turn_items.describe(data)
            # reads back with the project's reader, the game's 13 nodes untouched
            ai_ok &= doc.write() == data and doc.filename == ai + '.root' and len(doc.nodes) == 13 + what['new']
            for i, (o, b) in enumerate(zip(base.nodes, doc.nodes)):
                if i == root:
                    ai_ok &= [(l.node, l.name, l.extra) for l in b.links[2]][:-1] \
                        == [(l.node, l.name, l.extra) for l in o.links[2]] and b.links[2][-1].node >= 13 \
                        and shape(o) == shape(b)
                else:
                    ai_ok &= shop_items._node_state(o) == shop_items._node_state(b)
            ai_ok &= shop_items._doc_state(doc) == shop_items._doc_state(base)
            # every new node is a game node of the same type
            for n in doc.nodes[13:]:
                copies &= shape(n) in game_shapes and (n.type, n.name) in game_names
            ids = [bytes(n.guid) for n in doc.nodes]
            copies &= len(set(ids)) == len(ids)
            # the branch
            branch &= what['guards'] == GUARDS and what['own'] == item and what['drops'] == (not last) \
                and what['later'] == list(family[level + 1:])
            branch &= what['turn'] == ([('OneShotGenericDeleteThisActor', [])] if last else [
                ('OneShotDropSetDropValid', [True]), ('OneShotDropDrop', []), ('OneShotGenericDeleteThisActor', [])])
            branch &= what['enter'] == ([] if last else [('OneShotDropSetDropValid', [False])])
            branch &= what['new'] == (13 if last else 22)
            if family == PAIR:
                said.append('  %s: %d nodes (%d new), %d bytes' % (ai, len(doc.nodes), what['new'], len(data)))
            # the pack and its settings
            comp = ground_items.resolved_components(files, name)
            ap = byml.loads(files[ground_items.ap_path(name)]).root
            pouch = byml.loads(files[ground_items.pouch_param_path(name)]).root
            packs &= ap['$parent'] == 'Work/Actor/Obj_Item_Base.engine__actor__ActorParam.gyml' \
                and comp['AIInfoRef'] == '?' + shop_items.ai_info_path(ai) \
                and dict(byml.loads(files[shop_items.ai_info_path(ai)]).root) \
                == {'RootAIRef': 'Work/AI/Root/%s.root.ain' % ai} \
                and pouch.get('DefaultAutoGet') is True \
                and pouch.get('PouchActor') == 'Work/' + ground_items.ap_path(item)[:-len('.bgyml')] + '.gyml' \
                and ('DropRef' in comp) == (not last)
            refs = set()
            for p, x in files.items():
                if p.endswith('.bgyml'):
                    refs |= set(ground_items._refs(byml.loads(x).root))
            packs &= not [r for r in refs if r not in files and 'NX2' in r]
            if not last:
                nxt = turn_items.turn_name(family[1])
                dp = byml.loads(files[turn_items.drop_param_path(name)]).root
                dt = byml.loads(files[turn_items.drop_table_path(name)]).root
                ds = byml.loads(files[turn_items.drop_sub_path(name)]).root
                fs = byml.loads(fly[turn_items.drop_sub_path(turn_items.DROP_TEMPLATE)]).root
                drops &= comp['DropRef'] == '?' + turn_items.drop_param_path(name) \
                    and dict(dp) == {'$parent': 'Work/Component/DropParam/Default.game__component__DropParam.gyml',
                                     'DropTableResourceList': [
                                         'Work/' + turn_items.drop_table_path(name)[:-len('.bgyml')] + '.gyml']} \
                    and dict(dt) == {'SubTableList': [
                        'Work/' + turn_items.drop_sub_path(name)[:-len('.bgyml')] + '.gyml']} \
                    and len(ds['Items']) == 1 and ds['Items'][0]['DropActorName'] \
                    == 'Work/' + ground_items.ap_path(nxt)[:-len('.bgyml')] + '.gyml' \
                    and {k: v for k, v in ds['Items'][0].items() if k != 'DropActorName'} \
                    == {k: v for k, v in fs['Items'][0].items() if k != 'DropActorName'} \
                    and all(files[p] == fly[p] for p in turn_items.DROP_SHARED)
            else:
                drops &= not [p for p in files if 'Drop/' in p or '/DropParam/' in p]
            # the rows
            a, g, p = (new_rows[t] for t in ground_items.TABLES)
            rows_ok &= a['__RowId'] == g['__RowId'] == p['__RowId'] == name and a['ActorName'] == item \
                and a['FmdbName'] == rows['ActorInfo'][item]['FmdbName'] \
                and int(a['InstanceHeapSize']) > int(rows['ActorInfo'][ground_items.TEMPLATE]['InstanceHeapSize']) \
                and dict(g, __RowId=ground_items.TEMPLATE) == dict(rows['GameActorInfo'][ground_items.TEMPLATE]) \
                and dict(p, __RowId=item) == dict(rows['PouchActorInfo'][item], **equip_row(item))
            # how high it lies (ground_items.GROUND_LIFT): a lifted copy of the level's own animation project,
            # only its name and the ground pose's height changed; the lowest vertex 0.05 above the ground
            anim = byml.loads(files[ground_items._ref_path(comp['AnimationRef'])]).root['AnimationResources']
            projects = [x['ModelProjectName'] for x in anim]
            lift_ok &= a['AnimationResources'] == anim and (len(loose) == 1) == (item in ground_items.GROUND_LIFT)
            for path, (x, like, old_h, new_h, own_path) in loose.items():
                made_of, game = plain(like), plain(own_path)
                own = own_path[len('Model/'):-len('.anim.bfres')]
                model_file = plain('Model/%s.%s.bfres' % (a['ModelProjectName'], a['FmdbName']))
                low = ground_items.vertex_low(x, model_file, None) + ground_items.SPIN_ROOT_LIFT
                was = ground_items.vertex_low(game, model_file, None) + ground_items.SPIN_ROOT_LIFT
                pose, old_pose = item_pose.read_pose(x), item_pose.read_pose(game)
                # held up: the game's own pose (its Pose_GetDemo, or its Pose_Common when it has none)
                was_held = ground_items.HELD_POSE if ground_items.has_held_pose(game) else ground_items.GROUND_POSE
                held, old_held = item_pose.read_pose(x, ground_items.HELD_POSE), item_pose.read_pose(game, was_held)
                lifted_name = ground_items.lifted_project(own, game)
                lift_ok &= path == 'Model/%s.anim.bfres' % lifted_name \
                    and not os.path.exists(os.path.join(romfs, *path.split('/')) + '.zs') \
                    and projects == [ground_items.COMMON_ANIM, lifted_name] \
                    and like == (own_path if was_held == ground_items.HELD_POSE
                                 else ground_items.model_path(ground_items.HELD_BASE)) \
                    and len(x) == len(made_of) and len(path) == len(like) \
                    and (like != own_path or sum(i != j for i, j in zip(x, made_of)) <= 12) \
                    and (pose['scale'], pose['rot'], pose['move'][0], pose['move'][2]) \
                    == (old_pose['scale'], old_pose['rot'], old_pose['move'][0], old_pose['move'][2]) \
                    and abs(pose['move'][1] - new_h) < 1e-6 and abs(old_pose['move'][1] - old_h) < 1e-6 \
                    and all(held[f] == old_held[f] for f in ('scale', 'rot', 'move'))
                if item not in ground_items.GROUND_LIFT_BOX:
                    lift_ok &= abs(low - ground_items.GROUND_GAP) < 1e-5 and was < 0
                if path not in lifted:                    # one copy for an item's versions, as the build does
                    lifted.add(path)
                    out.add(path, x, like, made_of)
                    lift_ok &= out.table.get(path) == out.table.get(like)
                if family == PAIR:
                    said.append('  %s: pose height %.4f -> %.4f, lowest vertex %.4f -> %.4f above the ground (%s)'
                                % (item, old_h, new_h, was, low, path))
            # the size entries, made as the build makes them
            tpl_name = ground_items.template_of(name)
            like_files = dict(shared)
            for actor in (tpl_name, turn_items.DROP_TEMPLATE):
                like_files.update(sarc.Sarc.read(plain(ground_items.pack_path(actor))).files)
            path = ground_items.pack_path(name)
            out.add(path, pack, ground_items.pack_path(tpl_name), plain(ground_items.pack_path(tpl_name)))
            size_ok &= out.table.get(path) >= sizes.rule(path, pack)
            for inner, (x, like) in new_inner.items():
                out.add(inner, x, like, like_files[like])
            for inner, x in files.items():
                e, need = out.table.get(inner), sizes.rule(inner, x)
                size_ok &= e is not None and (need is None or e >= need)
                kind = sizes.bgyml_type(inner)
                if inner in new_inner and kind in DROP_ENTRY:
                    size_ok &= e == sizes.size32(len(x)) + DROP_ENTRY[kind]
                elif inner in new_inner and ground_items.EQUIP_COMPONENT in inner:
                    # an ocarina's equipment file (no rule for its kind): the ground shield's headroom, as built
                    eq_like = new_inner[inner][1]
                    size_ok &= e == max(out.table.get(eq_like) - len(like_files[eq_like]) + len(x),
                                        sizes.entry(inner, x, out.table.get(eq_like), like_files[eq_like]))
                elif inner in new_inner:
                    size_ok &= need is not None
                if family == PAIR and inner in new_inner:
                    said.append('  %-86s %6d bytes, entry %6d' % (inner, len(x), e))
    good &= check('turning items: Obj_NX2P_<level> with the AI NX2_Turn_<level>, new to the game', names_ok)
    good &= check('their AI reads back; the 13 nodes of DropItem.root are untouched (one child more)', ai_ok)
    good &= check('  every new node is a copy of a game node of the same type', copies)
    good &= check('  the branch: dead / in an event / main event playing stop it; then "Link owns this level"', branch)
    good &= check('ground items of the level (Obj_Item_Base), walked into, stored under the item\'s name', packs)
    good &= check('the first level\'s drop files name the second level\'s actor; the second has none', drops)
    good &= check('three table rows each: the item\'s name and model, the ground parts, the item row', rows_ok)
    good &= check('levels in GROUND_LIFT: a lifted copy, the ground pose only higher, lowest vertex %.2f above '
                  'the ground, held up the game\'s pose; the others have none' % ground_items.GROUND_GAP,
                  lift_ok and bool(lifted))
    good &= check('every file of the packs has a size entry that meets the rules (drop kinds: the game\'s)',
                  size_ok)
    print('\n'.join(said))

    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
