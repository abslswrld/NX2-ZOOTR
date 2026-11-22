"""Three-level chest test: what tools/three_chest.py and tools/build_mod.py make of a family of three levels in
small chests, on the game's own files. Reads only; writes nothing.

    python tests/three_chest_check.py "C:\\...\\romfs"
"""
import glob
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, HERE)

import build_mod  # noqa: E402
import ground_items  # noqa: E402
import shop_items  # noqa: E402
import sizes  # noqa: E402
import three_chest  # noqa: E402
from chest_check import name_hash, GAME_DATA  # noqa: E402
from formats import zstd, byml, sarc, ainb  # noqa: E402
from logic.world import World  # noqa: E402

FAMILY = ('Item_BombBag_Small', 'Item_BombBag_Medium', 'Item_BombBag_Large')
BAGS = (20, 30, 40)                                # bombs each level holds
CHEST = 'Obj_TBox_NX2_BombBag'
MIDO = ('Banc/KokiriForest/KokiriForest_Child_Dynamic.bcett.byml',
        'Banc/KokiriForest/KokiriForest_Adult_Dynamic.bcett.byml')
CHECKS = ('KF_MIDO_CHEST_01', 'KF_MIDO_CHEST_02', 'KF_MIDO_CHEST_03')
HASHES = ('12786193094758345086', '10831981390482426294', '4555665598794293658')
BIG = ('KF_KOKIRI_SWORD_CHEST', '16757992849254467386')              # a big chest (Obj_TBox_A_02)
# the game's own chest that gives the first level
GAME_CHEST = ('Banc/DodongoCavern/DodongoCavern_Static.bcett.byml', '12161709650443144121')
# one check of each kind a family is refused on at once, and of each kind it goes on in another way than a
# chest's (a turning item, a question in a flow: tests/families_check.py)
REFUSED = ('KF_KOKIRI_CHILD_SHOP_01', 'KF_HOUSE_OF_TWINS_CHILD_POT_01', 'KF_KNOW_IT_ALL_HOUSE_GS')
OTHER_WAYS = ('KF_RUPEE_NEAR_MIDO_ITEM', 'KF_CIRCLE_CENTER_ROCK', 'KF_NEAR_SARIAS_HOUSE_CHILD_BUSH_01',
              'KF_CIRCLE_KOKIRI_GIFT', 'LW_SARIA_GIFT', 'LW_NEAR_BRIDGE_SCRUB')
SETTINGS = ('Component/Blackboard/BlackboardParamTable/'
            'Drop_TreasureBox_A_06.engine__component__BlackboardParamTable.bgyml')
HOLDER_KINDS = 99                                  # the game's ActorHolderParam files (tests/size_check.py)


def check(name, ok):
    print('%-90s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def refused(f, *args):
    try:
        f(*args)
    except SystemExit:
        return True
    return False


def shape(n):
    """what a node is, apart from where it sits: its number, its links' targets, the nodes its inputs read, and
    the three values a three-level chest's AI sets (the name asked for, the actor made, its slot)"""
    own = (('QueryGetPouchContentNumByActorName', 'ActorName'), (three_chest.N_CREATE, 'ActorFileName'),
           (three_chest.N_CREATE, 'Key'), ('QuerySelectStringByBool', 'A'))
    return (n.type, n.name, n.flags, n.name_hash, n.exb_count, n.exb_size, len(n.attachments),
            tuple((t, x.name, x.value, x.flags) for t in ainb.PARAM_TYPES for x in n.immediates[t]),
            tuple((t, x.name, x.flags, x.cls, x.node >= 0,
                   None if (n.name, x.name) in own or x.node >= 0 else x.value)
                  for t in ainb.PARAM_TYPES for x in n.inputs[t]),
            tuple((t, x.name, x.flag, x.cls) for t in ainb.PARAM_TYPES for x in n.outputs[t]),
            frozenset((lt, l.name, l.extra) for lt, ls in enumerate(n.links) for l in ls), len(n.preconditions))


def slot_given(doc, owned, settings, condition):
    """the slot name a chest's AI hands to the chest module, worked out from the file's nodes for an inventory
    (`owned`: names Link has) and a placement's settings; the four kinds of question on the way are worked out
    as the game does (seen in game with the checking chest: the first item while Link doesn't have the item
    looked for, else the second)"""
    nodes = doc.nodes
    strings = [g.name for g in doc.globals['string']]
    bools = [g.name for g in doc.globals['bool']]
    # the AI's own names of the items, set from the settings when the chest starts (not empty here)
    values = dict(settings, MainDropActorName=settings['Drop__DropActor'],
                  SubDropActorName=settings['Drop__DropActor_Substitute'],
                  CheckActorName=settings['Drop__CheckActor'], Drop__CheckCondition=condition)

    def read(x, kind):
        if x.node >= 0:
            return out(x.node)
        if x.flags >> 31:
            return values[(strings if kind == 'string' else bools)[x.flags & 0xffff]]
        return x.value

    def out(i):
        n = nodes[i]
        b = [read(x, 'bool') for x in n.inputs['bool']]
        s = [read(x, 'string') for x in n.inputs['string']]
        if n.name == 'QuerySelectStringByBool':
            return s[0] if b[0] else s[1]
        if n.name == 'QueryExclusiveDisjunction':
            return b[0] != b[1]
        if n.name == 'QueryMathLessS32':
            return n.inputs['int'][0].value < out(n.inputs['int'][1].node)
        if n.name == 'QueryGetPouchContentNumByActorName':
            return 1 if s[0] in owned else 0
        if n.name == 'QueryStringIsEqual':
            return s[0] == s[1]
        raise SystemExit('node %d (%s): not a question this test knows' % (i, n.name))

    module = [n for n in nodes if n.name == three_chest.N_MODULE][0]
    return read([x for x in module.inputs['string'] if x.name == 'HolderKey'][0], 'string')


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    plain = lambda path: zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)  # noqa: E731
    table_rows = lambda t: byml.loads(plain(ground_items.table_path(t))).root   # noqa: E731
    rows = {t: {r['__RowId']: r for r in table_rows(t)} for t in ground_items.TABLES}
    world = World()
    good = True

    def in_chest(item):                                # as build_mod.main's in_chest
        if ground_items.kind_of(plain, item) == 'equipment':
            return ground_items.ground_name(item, 'held')
        return item

    # the family and its names
    good &= check('the three-level family looked at here: the bomb bags, first level first (every family: '
                  'tests/families_check.py)',
                  build_mod.THREE_LEVEL_FAMILIES.get(FAMILY) == 'BombBag'
                  and not any(set(p) & set(FAMILY) for p in build_mod.PROGRESSIVE_PAIRS))
    data = byml.loads(plain(GAME_DATA)).root['Data']
    saved = {kind: {int(e['Hash']) for e in data[kind]} for kind in ('Bool', 'Int')}
    good &= check('every level is an inventory item under its own name (PouchActorInfo, ActorName)',
                  all(x in rows['PouchActorInfo'] and rows['ActorInfo'][x]['ActorName'] == x for x in FAMILY))
    good &= check('  and is saved under it (IsGet.<name>, PouchData.<name>.StockNum): no level replaces another',
                  all(name_hash('IsGet.' + x) in saved['Bool']
                      and name_hash('PouchData.%s.StockNum' % x) in saved['Int'] for x in FAMILY))
    good &= check('  the bags hold %d, %d and %d bombs and are filled when received' % BAGS,
                  tuple(int(rows['PouchActorInfo'][x]['AfterExpansionMaxNum']) for x in FAMILY) == BAGS
                  and all(rows['PouchActorInfo'][x].get('IsItemStockMaxIfGet') is True
                          and rows['PouchActorInfo'][x].get('MaxNumGameData') == 'Bomb' for x in FAMILY))
    ok = True
    for x in FAMILY:
        files = sarc.Sarc.read(plain(ground_items.pack_path(x))).files
        comp = ground_items.resolved_components(files, x)
        ok &= ground_items.kind_of(plain, x) == 'item' and ground_items.can_hold_up(plain, x) and in_chest(x) == x
        ok &= comp['ActorNameRef'] == '?ActorSystem/ActorName/%s.engine__actor__ActorName.bgyml' % x
        # Medium and Large have no item settings of their own: the Small one's, which name no other item
        ok &= comp['PouchContentRef'] == '?Component/PouchContentParam/BombBag.game__component__PouchContentParam.bgyml'
        p = comp['PouchContentRef'][1:]
        while p in files:                              # (the last one they inherit from is outside the pack)
            root = byml.loads(files[p]).root
            ok &= 'PouchActor' not in root
            p = ground_items._parent_path(root)
    good &= check('a chest holds each level as it is: an item event actor with the get demo; the item settings '
                  'the three share name no other item', ok)
    actors = {str(int(a['Hash'])): a for a in byml.loads(plain(GAME_CHEST[0])).root['Actors']}
    good &= check("the game's own chest gives %s (Dodongo's Cavern)" % FAMILY[0],
                  actors[GAME_CHEST[1]]['Gyaml'].startswith('Obj_TBox')
                  and actors[GAME_CHEST[1]]['Dynamic']['Drop__DropActor'] == FAMILY[0])

    # the syntax: accepted in a small chest, as the family's first level
    text = '>'.join(FAMILY)
    asked = [(c, text) for c in CHECKS] + [('KF_MIDO_CHEST_04', 'Item_Boomerang')]
    got = build_mod.three_level_parse(world, asked)
    good &= check('CHECK_ID=First>Second>Third on small chests: planned as First; other assignments untouched',
                  got == {c: FAMILY for c in CHECKS}
                  and asked == [(c, FAMILY[0]) for c in CHECKS] + [('KF_MIDO_CHEST_04', 'Item_Boomerang')])
    pair = [('KF_MIDO_CHEST_01', 'Item_Scale_Silver>Item_Scale_Gold')]
    good &= check('a two-level pair is left to the game\'s checking chest',
                  build_mod.three_level_parse(world, pair) == {} and pair[0][1] == 'Item_Scale_Silver>Item_Scale_Gold'
                  and build_mod.checking_chest('Obj_TBox_A_01') == 'Obj_TBox_A_06'
                  and build_mod.checking_chest('Obj_TBox_A_06_NoBake') == 'Obj_TBox_A_06_NoBake')
    good &= check('refused: a family not in the table (another order, other items)',
                  refused(build_mod.three_level_parse, world, [(CHECKS[0], '>'.join(FAMILY[::-1]))])
                  and refused(build_mod.three_level_parse, world,
                              [(CHECKS[0], 'Item_Scale_Silver>Item_Scale_Gold>Item_Hookshot')])
                  and FAMILY[:2] not in build_mod.PROGRESSIVE_PAIRS and FAMILY[1:] not in build_mod.PROGRESSIVE_PAIRS)
    good &= check('refused: on a shelf, a pot and a Gold Skulltula',
                  all(refused(build_mod.three_level_parse, world, [(c, text)]) for c in REFUSED))
    left = [(c, text) for c in OTHER_WAYS]
    good &= check('left as it is for the other ways: on a freestanding item, a rock, a bush, a gift and a scrub',
                  build_mod.three_level_parse(world, left) == {} and left == [(c, text) for c in OTHER_WAYS])
    old = plain(MIDO[0])
    good &= check('refused: in a big chest (the Kokiri Sword chest)',
                  build_mod.three_level_parse(world, [(BIG[0], text)]) == {BIG[0]: FAMILY}
                  and refused(build_mod.patch_file, old, {BIG[1]: ('TEST', FAMILY[0], None, 'chest')},
                              {BIG[1]: FAMILY[:2]}, {BIG[1]: 'BombBag'}))

    # the maps: Mido's three chests, both ages
    ok = same = True
    for path in MIDO:
        old = plain(path)
        before = {str(int(a['Hash'])): a for a in byml.loads(old).root['Actors']}
        new, found, _ = build_mod.patch_file(
            old, {h: ('TEST', in_chest(FAMILY[0]), None, 'chest') for h in HASHES},
            {h: build_mod.pair_check(FAMILY[:2], in_chest) for h in HASHES}, {h: 'BombBag' for h in HASHES})
        back = byml.loads(new).root['Actors']
        ok &= set(HASHES) <= set(before) and len(back) == len(before)
        for a in back:
            h = str(int(a['Hash']))
            want = dict(before[h])
            if h in HASHES:
                ok &= want['Gyaml'] == 'Obj_TBox_A_01'
                want['Gyaml'] = CHEST
                want['Dynamic'] = dict(want['Dynamic'], Drop__DropActor=FAMILY[0], Drop__CheckActor=FAMILY[0],
                                       Drop__DropActor_Substitute=FAMILY[1])
                same &= set(a['Dynamic']) - {'GetEventName'} == {'Drop__CheckActor', 'Drop__DropActor',
                                                                 'Drop__DropActor_Substitute'}
            ok &= a == want
    good &= check("Mido's three chests become %s, both ages; the fourth and everything else unchanged" % CHEST, ok)
    good &= check("  with the settings of the game's own checking chests: first level, looked for, second level",
                  same)
    # a _NoBake small chest and one of the game's own checking chests
    twins = {}
    for f in sorted(glob.glob(os.path.join(romfs, 'Banc', '**', '*.bcett.byml.zs'), recursive=True)):
        rel = os.path.relpath(f, romfs).replace(os.sep, '/')[:-3]
        for a in byml.loads(plain(rel)).root.get('Actors', []):
            if a['Gyaml'] in ('Obj_TBox_A_01_NoBake', 'Obj_TBox_A_06', 'Obj_TBox_A_06_NoBake'):
                twins.setdefault(a['Gyaml'], (rel, str(int(a['Hash']))))
    ok = len(twins) >= 2 and 'Obj_TBox_A_01_NoBake' in twins
    for was, (rel, h) in sorted(twins.items()):
        new, found, _ = build_mod.patch_file(plain(rel), {h: ('TEST', FAMILY[0], None, 'chest')},
                                             {h: FAMILY[:2]}, {h: 'BombBag'})
        now = [a for a in byml.loads(new).root['Actors'] if str(int(a['Hash'])) == h][0]
        ok &= now['Gyaml'] == CHEST + ('_NoBake' if was.endswith('_NoBake') else '') \
            and now['Dynamic']['Drop__DropActor_Substitute'] == FAMILY[1]
    good &= check('a _NoBake small chest becomes %s_NoBake; a checking chest of the game the family\'s chest too'
                  % CHEST, ok)

    # the actor and its twin
    shared = sarc.Sarc.read(plain(three_chest.AI_PACK)).files
    out = build_mod.Output(romfs, None, d)
    packs = parts = rows_ok = size_ok = True
    said = []
    built = {}
    for twin in (False, True):
        base = three_chest.BASE + ('_NoBake' if twin else '')
        game = sarc.Sarc.read(plain(ground_items.pack_path(base))).files
        name, pack, new_inner, new_rows = three_chest.build('BombBag', FAMILY[1], in_chest(FAMILY[2]), plain,
                                                            table_rows, twin)
        files = sarc.Sarc.read(pack).files
        built[twin] = files
        own = {ground_items.ap_path(CHEST), shop_items.ai_info_path(CHEST), shop_items.ai_path(CHEST),
               three_chest.holder_path(CHEST)} | ({ground_items.ap_path(name)} if twin else set())
        gone = {ground_items.ap_path(three_chest.BASE), shop_items.ai_info_path(three_chest.BASE),
                shop_items.ai_path(three_chest.BASE), three_chest.holder_path(three_chest.BASE)} \
            | ({ground_items.ap_path(base)} if twin else set())
        packs &= name == CHEST + ('_NoBake' if twin else '') and name not in rows['ActorInfo'] and len(name) <= 63 \
            and not os.path.exists(os.path.join(romfs, *ground_items.pack_path(name).split('/')) + '.zs') \
            and set(files) == (set(game) - gone) | own and set(new_inner) == own \
            and all(files[p] == game[p] for p in set(files) - own) \
            and all(files[p] == x for p, (x, like) in new_inner.items())
        # every file a file of the pack names is in it, where the game's pack has its counterpart
        refs = set()
        for p, x in files.items():
            if p.endswith('.bgyml'):
                refs |= set(ground_items._refs(byml.loads(x).root))
        game_refs = set()
        for p, x in game.items():
            if p.endswith('.bgyml'):
                game_refs |= set(ground_items._refs(byml.loads(x).root))
        packs &= not [r for r in refs if r not in files and ('NX2' in r or r in game)] \
            and {r for r in refs if r not in files} <= {r for r in game_refs if r not in game}
        # the parts
        ap = byml.loads(files[ground_items.ap_path(CHEST)]).root
        game_ap = byml.loads(game[ground_items.ap_path(three_chest.BASE)]).root
        held = byml.loads(files[three_chest.holder_path(CHEST)]).root
        game_held = byml.loads(game[three_chest.holder_path(three_chest.BASE)]).root
        comp, game_comp = (ground_items.resolved_components(f, n) for f, n in ((files, name), (game, base)))
        parts &= ap['$parent'] == game_ap['$parent'] == 'Work/Actor/Obj_TBox_A_01.engine__actor__ActorParam.gyml' \
            and set(ap['Components']) == set(game_ap['Components']) \
            and comp == dict(game_comp, AIInfoRef='?' + shop_items.ai_info_path(CHEST),
                             ActorHolderRef='?' + three_chest.holder_path(CHEST)) \
            and dict(byml.loads(files[shop_items.ai_info_path(CHEST)]).root) \
            == {'RootAIRef': 'Work/AI/Root/%s.root.ain' % CHEST} \
            and held['$parent'] == game_held['$parent'] \
            and list(held['ActorHoldSettings']) == ['SubContent', 'ThirdContent'] \
            and held['ActorHoldSettings']['SubContent'] == game_held['ActorHoldSettings']['SubContent'] \
            == held['ActorHoldSettings']['ThirdContent']
        if twin:
            tp = byml.loads(files[ground_items.ap_path(name)]).root
            parts &= dict(tp) == dict(byml.loads(game[ground_items.ap_path(base)]).root,
                                      **{'$parent': 'Work/Actor/%s.engine__actor__ActorParam.gyml' % CHEST})
        # the rows: the checking chest's, under our name; as much memory again as the checking chest has over
        # the small chest
        a, g = new_rows['ActorInfo'], new_rows['GameActorInfo']
        ga, pa = rows['ActorInfo'][base], rows['ActorInfo']['Obj_TBox_A_01' + ('_NoBake' if twin else '')]
        rows_ok &= set(new_rows) == {'ActorInfo', 'GameActorInfo'} and a['__RowId'] == g['__RowId'] == name \
            and dict(a, __RowId=base, InstanceHeapSize=ga['InstanceHeapSize']) == dict(ga) \
            and int(a['InstanceHeapSize']) - int(ga['InstanceHeapSize']) \
            == int(ga['InstanceHeapSize']) - int(pa['InstanceHeapSize']) > 0 \
            and dict(g, __RowId=base) == dict(rows['GameActorInfo'][base])
        # the size entries, made as the build makes them
        path, like_pack = ground_items.pack_path(name), ground_items.pack_path(base)
        out.add(path, pack, like_pack, plain(like_pack))
        size_ok &= out.table.get(path) >= sizes.rule(path, pack)
        for inner, (x, like) in new_inner.items():
            if not twin or inner == ground_items.ap_path(name):
                out.add(inner, x, like, game[like])
        for inner, (x, like) in sorted(new_inner.items()):
            e, need = out.table.get(inner), sizes.rule(inner, x)
            size_ok &= e is not None and need is not None and e >= need and e >= out.table.get(like)
            if not twin or inner == ground_items.ap_path(name):
                said.append('  %-88s %6d bytes, entry %6d' % (inner, len(x), e))
        said.append('  %-88s %6d bytes, entry %6d' % (path, len(pack), out.table.get(path)))
    game_table = build_mod.Output(romfs, None, d).table
    size_ok &= all(out.table.get(p) == game_table.get(p) for p in built[True] if 'NX2' not in p) \
        and sum(game_table.get(p) is None for p in built[True] if 'NX2' not in p) == 1    # the debug menu's
    good &= check('the chest and its twin: the checking chest\'s pack with its four own parts replaced by ours; '
                  'the game\'s files as they are', packs)
    good &= check('  the small chest with the checking chest\'s parts, the AI and the held actors ours; '
                  'ThirdContent a copy of SubContent', parts)
    good &= check('  two table rows each: the checking chest\'s, with as much memory again as it has over the '
                  'small chest', rows_ok)
    good &= check('  every new file has a size entry that meets the rules, no smaller than the game file\'s it '
                  'is made from', size_ok)
    holders = {}
    for f in sorted(glob.glob(os.path.join(romfs, 'Pack', 'Actor', '*TBox*.pack.zs'))
                    + glob.glob(os.path.join(romfs, 'Pack', 'Actor', 'Player*.pack.zs'))
                    + glob.glob(os.path.join(romfs, 'Pack', 'Actor', 'Enemy_DungeonBoss_*.pack.zs'))
                    + glob.glob(os.path.join(romfs, 'Pack', 'Actor', 'Npc_Hylia_0*.pack.zs'))):
        for p, x in sarc.Sarc.read(zstd.decompress(open(f, 'rb').read(), d)).files.items():
            if sizes.bgyml_type(p) == 'game__component__ActorHolderParam':
                holders[p] = x
    good &= check('  the held actors\' size rule (224 a slot, 104 a bound bone) is the game\'s entry for %d of '
                  'its files (all %d: tests/size_check.py)' % (len(holders), HOLDER_KINDS),
                  len(holders) >= 20 and all(sizes.rule(p, x) == game_table.get(p) for p, x in holders.items())
                  and len({len(byml.loads(x).root.get('ActorHoldSettings', {})) for x in holders.values()}) > 4)

    # the light on the chest's bone: an entry each in the game's list, the checking chest's under our name
    rig_path = os.path.join(romfs, *three_chest.LIGHT_RIGS.split('/'))
    old = open(rig_path, 'rb').read()                  # (stored uncompressed)
    ours = [CHEST, CHEST + '_NoBake']
    new = three_chest.light_rigs(old, ours)
    was, now = (byml.loads(x).root['LightRigSettingList'] for x in (old, new))
    work = lambda n: 'Work/Actor/%s.engine__actor__ActorParam.gyml' % n   # noqa: E731
    by_actor = {e['Actor']: e for e in was}
    ok = list(now[:len(was)]) == list(was) and len(now) == len(was) + 2 and set(byml.loads(new).root) == {
        'LightRigSettingList'}
    for n, e in zip(ours, now[len(was):]):
        base = three_chest.BASE + ('_NoBake' if n.endswith('_NoBake') else '')
        ok &= dict(e) == dict(by_actor[work(base)], Actor=work(n)) and e['BonePrefix'] == 'Root' \
            and rows['GameActorInfo'][base].get('HasLightRigBone') is True
    ok &= refused(three_chest.light_rigs, new, ours[:1]) and refused(three_chest.light_rigs, old, ['Obj_TBox_A_01'])
    lights = build_mod.Output(romfs, None, d)
    lights.size(three_chest.LIGHT_RIGS, old, new)
    ok &= game_table.get(three_chest.LIGHT_RIGS) == sizes.rule(three_chest.LIGHT_RIGS, old) \
        and lights.table.get(three_chest.LIGHT_RIGS) == sizes.rule(three_chest.LIGHT_RIGS, new) \
        == game_table.get(three_chest.LIGHT_RIGS) + 2 * 160 + sizes.size32(len(new)) - sizes.size32(len(old))
    good &= check('the chest\'s light: an entry each in the game\'s list (%d -> %d), the checking chest\'s under '
                  'our name; the others as they were; its size entry by the rule (160 an entry)'
                  % (len(was), len(now)), ok)

    # the AI
    files = built[False]
    data = files[shop_items.ai_path(CHEST)]
    base_data = sarc.Sarc.read(plain(ground_items.pack_path(three_chest.BASE))).files[
        shop_items.ai_path(three_chest.BASE)]
    doc, base = ainb.loads(data), ainb.loads(base_data)
    what = three_chest.describe(data)
    at = three_chest._landmarks(base)
    n0 = len(base.nodes)
    ai_ok = doc.write() == data and base.write() == base_data and doc.filename == CHEST + '.root' \
        and n0 == 101 and len(doc.nodes) == n0 + 4 and built[True][shop_items.ai_path(CHEST)] == data \
        and shop_items._doc_state(doc) == shop_items._doc_state(base)
    for i, (o, b) in enumerate(zip(base.nodes, doc.nodes)):
        if i == at['make']:
            ai_ok &= [(l.node, l.name, l.extra) for l in b.links[2]][:-1] \
                == [(l.node, l.name, l.extra) for l in o.links[2]] and b.links[2][-1].node >= n0 \
                and (b.links[2][-1].name, b.links[2][-1].extra) == ('', ()) and shape(o) == shape(b)
        elif i == at['module']:
            ai_ok &= shape(o) == shape(b) and [x.node for x in o.inputs['string'] if x.name == 'HolderKey'] \
                == [at['select']] and [x.node for x in b.inputs['string'] if x.name == 'HolderKey'] == [n0 + 3] \
                and [(x.name, x.node) for t in ainb.PARAM_TYPES for x in o.inputs[t] if x.name != 'HolderKey'] \
                == [(x.name, x.node) for t in ainb.PARAM_TYPES for x in b.inputs[t] if x.name != 'HolderKey']
        else:
            ai_ok &= shop_items._node_state(o) == shop_items._node_state(b)
    good &= check('its AI reads back byte for byte; the 101 nodes of the checking chest\'s AI are untouched but '
                  'for two', ai_ok)
    sources = [base] + [ainb.loads(shared[p]) for p in three_chest.SOURCES.values()]
    game_shapes = {shape(n) for s in sources for n in s.nodes}
    ids = [bytes(n.guid) for n in doc.nodes]
    good &= check('  every new node is a copy of a game node of the same type; no node id twice',
                  all(shape(n) in game_shapes for n in doc.nodes[n0:]) and len(set(ids)) == len(ids)
                  and [n.name for n in doc.nodes[n0:]] == [
                      three_chest.N_CREATE, 'QueryGetPouchContentNumByActorName', 'QueryMathLessS32',
                      'QuerySelectStringByBool'])
    reach = three_chest._reached
    good &= check('  the branch: third slot made with the other two; "Link has the second level" -> the third '
                  'slot, else the checking chest\'s answer; no new node unreached',
                  what == {'name': CHEST + '.root', 'new': 4, 'key': 'ThirdContent', 'third': FAMILY[2],
                           'second': FAMILY[1], 'else': ('Content', 'SubContent'),
                           'check': [g.name for g in doc.globals['string']].index('CheckActorName')}
                  and reach(doc) == reach(base) | set(range(n0, n0 + 4)))
    # what each chest gives, worked out from the file's nodes: the game's checking chest first (seen in game),
    # then ours for every inventory and every opening order
    settings = {'Drop__DropActor': FAMILY[0], 'Drop__CheckActor': FAMILY[0],
                'Drop__DropActor_Substitute': FAMILY[1]}
    table = byml.loads(files[SETTINGS]).root
    condition = [x['InitVal'] for x in table['BlackboardParamBoolArray'] if x['BBKey'] == 'Drop__CheckCondition']
    slots = {'Content': FAMILY[0], 'SubContent': FAMILY[1], what['key']: what['third']}
    ok = condition == [True] and comp['DropRef'] == game_comp['DropRef'] \
        and slot_given(base, set(), settings, True) == 'Content' \
        and slot_given(base, {FAMILY[0]}, settings, True) == 'SubContent'
    good &= check('  worked out from the nodes, the game\'s checking chest gives the first item, then the second '
                  '(as seen in game)', ok)
    ok = True
    for n in range(4):
        for have in itertools.combinations(FAMILY, n):
            want = FAMILY[2] if FAMILY[1] in have else FAMILY[1] if FAMILY[0] in have else FAMILY[0]
            ok &= slots[slot_given(doc, set(have), settings, True)] == want
    good &= check('  ours gives: the third level when Link has the second, else the second when he has the '
                  'first, else the first (all 8 inventories)', ok)
    ok = True
    for order in itertools.permutations(range(3)):
        have = []
        for chest in order:                            # every chest has the same settings
            have.append(slots[slot_given(doc, set(have), settings, True)])
        ok &= tuple(have) == FAMILY
    good &= check('  three chests give %s, %s, %s in each of the six opening orders'
                  % tuple(x[len('Item_BombBag_'):] for x in FAMILY), ok)
    print('\n'.join(said))
    print('  %s: %d nodes (%d new), %d bytes (the game\'s: %d)' % (what['name'], len(doc.nodes), what['new'],
                                                                   len(data), len(base_data)))

    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
