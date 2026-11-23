"""Progressive pairs on rocks, bushes and Deku Scrubs: what tools/build_mod.py makes of CHECK_ID=First>Second on
a liftable rock or a solid bush (its drop becomes First's turning item, tools/turn_items.py) and on a scrub that
sells one thing once (the inventory question in the scrub's own branch of Enemy_Scrub_Business_Common), on the
game's own files. Only reads the game; the whole builds it runs go to a temporary folder that is removed again.

    python tests/pairs_more_check.py "C:\\...\\romfs"
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
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import build_mod  # noqa: E402
import ground_items  # noqa: E402
import shop_items  # noqa: E402
import once_items  # noqa: E402
import turn_items  # noqa: E402
from formats import zstd, byml, sarc, evfl, restbl, msbt  # noqa: E402
from logic.world import World  # noqa: E402

CHILD_MAP = 'Banc/KokiriForest/KokiriForest_Child_Dynamic.bcett.byml'      # the rocks (and Mido's chests)
BUSH_MAP = 'Banc/KokiriForest/KokiriForest_Child_Static.bcett.byml'        # the bushes (and the scrub)
ADULT_MAP = 'Banc/KokiriForest/KokiriForest_Adult_Dynamic.bcett.byml'
ROCKS = ('KF_BEHIND_SARIAS_HOUSE_CHILD_ROCK_01', 'KF_WEST_OF_MIDOS_HOUSE_CHILD_ROCK_01')
BUSHES = ('KF_NEAR_SARIAS_HOUSE_CHILD_BUSH_01', 'KF_BEHIND_SHOP_CHILD_BUSH_01')
CLOSE = ('KF_CIRCLE_CHILD_ROCK_01', 'KF_CIRCLE_CHILD_ROCK_02')          # two rocks of the ring, 1.9 m apart
CORNERS = tuple('KF_CIRCLE_ADULT_ROCK_%02d' % n for n in (3, 6, 9, 12))  # the 4 adult corner rocks: never used
SCRUB = 'LW_NEAR_BRIDGE_SCRUB'                       # the stick-bag scrub by the bridge: 40 rupees, sells once
SCRUB_TALK, SCRUB_WAS = 'Enemy_Scrub_Business_DekuStickPouch_01', 'Item_StickBag_Medium'
SCRUB_MAPS = ('Banc/KokiriForest/KokiriForest_Adult_Static.bcett.byml',
              'Banc/KokiriForest/KokiriForest_Child_Static.bcett.byml',
              'Banc/LostWood/LostWood_Adult_Static.bcett.byml', 'Banc/LostWood/LostWood_Child_Static.bcett.byml')
REPEAT_TALK = 'Enemy_Scrub_Business_DekuSeed_01'     # a scrub that sells again and again
CHEST = 'KF_MIDO_CHEST_01'
SCALES = ('Item_Scale_Silver', 'Item_Scale_Gold')
HOOKS = ('Item_Hookshot', 'Item_Longshot')
OCARINAS = ('Item_Ocarina_Fairy', 'Item_Ocarina_Time')
# still refused: a shelf, a Gold Skulltula, a cutscene gift, a song (pots: tests/one_time_check.py)
REFUSED = ('KF_KOKIRI_CHILD_SHOP_01', 'KF_KNOW_IT_ALL_HOUSE_GS', 'LW_SARIA_GIFT', 'Song from Saria')
# the packs that hold the rock's and the bush's own actor file: they get the AI that drops once
ONCE_PACKS = ('Obj_LiftRock_A_01', 'Obj_LiftRock_A_02', 'Obj_LiftRock_A_03',
              'Obj_Plant_Grass_A_01', 'Obj_Plant_Grass_A_01_Respawn', 'Obj_Plant_Grass_A_03')
# the actors that drop what their placement names, and the drop part they share
DROPPERS = ('Obj_LiftRock_A_01', 'Obj_Plant_Grass_A_01', 'Obj_Pot_A_01')
DROP_PART = 'Component/DropParam/Drop_ResourceSupply_00.game__component__DropParam.bgyml'
RESTBL = build_mod.RESTBL_PATH.replace(os.sep, '/')[:-3]
FIXES = ('skippable_opening', 'bombs_without_bracelet', 'magic_is_separate', 'bombchus_without_bag',
         'kokiri_shop_full_stock', 'kokiri_circle_after_dungeons')


def check(name, ok):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def refused(f, *args, **kw):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            f(*args, **kw)
    except SystemExit as e:
        return bool(e.code)
    return False


def actor_shape(a):
    return a.name, a.secondary, a.argument, a.params, a.entry_point, a.cut, list(a.actions), list(a.queries)


def step(fc, e, moved=None):
    """an event apart from its index: what it is and the names of the events it leads to (moved: {name: the
    name a link to it is expected to show instead})"""
    moved = moved or {}

    def name(i):
        return None if i is None else moved.get(fc.events[i].name, fc.events[i].name)

    a = fc.actors[e.actor] if e.type in ('action', 'switch') else None
    return (e.type, (a.name, a.secondary) if a else None, a.actions[e.action] if e.type == 'action' else None,
            a.queries[e.query] if e.type == 'switch' else None,
            list(e.params.items()) if isinstance(e.params, dict) else e.params, e.flowchart, e.entry, e.value,
            name(e.next), name(e.join), [(v, name(c)) for v, c in e.cases], [name(f) for f in e.forks])


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    rd = lambda f: zstd.decompress(open(f, 'rb').read(), d)   # noqa: E731
    plain = lambda path: rd(os.path.join(romfs, *path.split('/')) + '.zs')   # noqa: E731
    table_rows = lambda t: byml.loads(plain(ground_items.table_path(t))).root   # noqa: E731
    model = lambda project: os.path.exists(os.path.join(romfs, 'Model', project + '.anim.bfres.zs'))  # noqa: E731
    pack = lambda actor: sarc.Sarc.read(plain(ground_items.pack_path(actor))).files   # noqa: E731
    world = World()
    good = True

    # ---------------------------------------------------------------------------------- rocks and bushes
    print('Rocks and bushes')
    good &= check('a pair on a rock or a bush is a turning item, as on a freestanding item',
                  [build_mod.pair_kind(world, c) for c in ROCKS + BUSHES] == ['rock', 'rock', 'bush', 'bush']
                  and all(k in build_mod.TURN_KINDS for k in ('freestanding', 'rock', 'bush'))
                  and 'skulltula' not in build_mod.PAIR_KINDS)
    good &= check('still refused: a shelf, a Gold Skulltula, a cutscene gift, a song',
                  all(refused(build_mod.pair_kind, world, c) for c in REFUSED))
    # what the game's files show: rocks, bushes and pots drop through one drop part, whose settings table holds
    # the placement's Drop__DropActor; the turning item's own drop part is built on the same base and table
    parts = {a: pack(a) for a in DROPPERS}
    same = True
    for a, files in parts.items():
        comp = ground_items.resolved_components(files, a)
        same &= comp.get('DropRef') == '?' + DROP_PART and files[DROP_PART] == parts[DROPPERS[0]][DROP_PART]
        chain, p = [], DROP_PART
        while p:
            root = byml.loads(files[p]).root
            chain.append(root)
            # 'Work/<path>.gyml' is how one settings file names another: the file in the pack is '<path>.bgyml'
            p = root['$parent'][len('Work/'):-len('.gyml')] + '.bgyml' if '$parent' in root else None
        table = byml.loads(files[turn_items.DROP_SHARED[1]]).root
        keys = {x['BBKey']: bool(x['IsInstanceParam']) for x in table['BlackboardParamStringArray']}
        same &= chain[-1] == byml.loads(files[turn_items.DROP_SHARED[0]]).root \
            and dict(chain[-1]) == {'BlackboardTableRef': turn_items._work(turn_items.DROP_SHARED[1])} \
            and keys == {'Drop__DropTable': True, 'Drop__DropActor': True, 'Drop__DropTableOverWrite': False}
    good &= check('game: a rock, a bush and a pot have the same drop part (%s), on the base whose table holds the '
                  'placement\'s Drop__DropActor' % DROP_PART.split('/')[-1].split('.')[0], same)
    name, tpack, _, _, _ = turn_items.build(SCALES, 0, plain, table_rows, model)
    tfiles = sarc.Sarc.read(tpack).files
    tdrop = byml.loads(tfiles[turn_items.drop_param_path(name)]).root
    what = turn_items.describe(tfiles[shop_items.ai_path(turn_items.ai_name(SCALES[0]))])
    good &= check('the turning item dropped is the freestanding one: its own drop part on the same base and '
                  'table, switched off on entering',
                  name == turn_items.turn_name(SCALES[0]) == 'Obj_NX2P_Scale_Silver'
                  and tdrop['$parent'] == turn_items._work(turn_items.DROP_SHARED[0])
                  and all(tfiles[p] == parts[DROPPERS[0]][p] for p in turn_items.DROP_SHARED)
                  and what['enter'] == [('OneShotDropSetDropValid', [False])] and what['own'] == SCALES[0]
                  and what['turn'] == [('OneShotDropSetDropValid', [True]), ('OneShotDropDrop', []),
                                       ('OneShotGenericDeleteThisActor', [])])
    # the game itself names a drop on rocks and bushes
    games = 0
    for m, actor in (('Banc/DesertColossus/DesertColossus_Adult_Dynamic.bcett.byml', DROPPERS[0]),
                     ('Banc/HyruleField/HyruleField_Adult_Static.bcett.byml', DROPPERS[1])):
        n = sum(1 for a in byml.loads(plain(m)).root['Actors']
                if a['Gyaml'] == actor and (a.get('Dynamic') or {}).get('Drop__DropActor'))
        games = games + n if n and games >= 0 else -1
    good &= check('game: rocks (Desert Colossus) and bushes (Hyrule Field) with a Drop__DropActor of their own '
                  '(%d placements)' % games, games >= 4)

    # the map: the rock's and the bush's placements get First's turning item as their drop, nothing else changes
    first = turn_items.turn_name(SCALES[0])
    planned = build_mod.plan(world, [(c, first) for c in (ROCKS[0], BUSHES[0])])
    kinds = {m: [v[3] for v in ch.values()] for m, ch in planned.items()}
    ok = kinds == {CHILD_MAP: ['rock'], BUSH_MAP: ['bush']}
    edits = True
    for m, changes in planned.items():
        old = plain(m)
        before = {str(int(a['Hash'])): a for a in byml.loads(old).root['Actors']}
        ok &= all('Drop__DropActor' not in (before[h].get('Dynamic') or {})
                  and 'Drop__DropTable' not in (before[h].get('Dynamic') or {})
                  and before[h]['Gyaml'] in DROPPERS[:2] for h in changes)
        new, found, _ = build_mod.patch_file(old, changes)
        back = byml.loads(new).root['Actors']
        edits &= len(back) == len(before) and all(v is None for v in found.values())
        for a in back:
            h = str(int(a['Hash']))
            want = dict(before[h])
            if h in changes:
                want['Dynamic'] = dict(want.get('Dynamic') or {}, Drop__DropActor=first)
            edits &= a == want
    good &= check('a child rock and a child bush: one placement each, in the child maps only, nothing set as '
                  'their drop', ok)
    good &= check('the two placements drop %s (Drop__DropActor added); nothing else changes' % first, edits)
    far = build_mod.turn_spacing(world, {c: SCALES for c in ROCKS + BUSHES})
    good &= check('rocks and bushes of one family 2 m apart or less are refused (two rocks of the ring); the '
                  'test spots are far apart (least %.1f m)' % min([x[2] for x in far] or [0]),
                  refused(build_mod.turn_spacing, world, {c: SCALES for c in CLOSE})
                  and len(far) == 6 and min(x[2] for x in far) > 10)

    # ---------------------------------------------------------------------------------------------- scrubs
    print('Deku Scrubs')
    good &= check('a pair on a scrub is the scrub\'s own; a chest, a rock, a gift are not scrubs',
                  build_mod.scrub_pair_kind(world, SCRUB) is True
                  and not any(build_mod.scrub_pair_kind(world, c)
                              for c in (CHEST, ROCKS[0], 'KF_CIRCLE_KOKIRI_GIFT', 'LW_SARIA_GIFT')))
    old_flow = plain(build_mod.SCRUB_FLOW)
    orig = evfl.loads(old_flow).flowchart
    (q_actor, q_params, has, has_not), (w_params, wait_actor, wait_params) = build_mod.scrub_pair_template(orig)
    q = orig.events[orig.event_index('Event319')]
    sells = {v: orig.events[c] for v, c in q.cases}
    good &= check("the game's own upgrade scrub asks before it sells (Event319): has the medium stick bag -> "
                  'sells the large one, else the medium one',
                  orig.actors[q.actor].name == 'PouchSystemActor'
                  and orig.actors[q.actor].queries[q.query] == build_mod.SCRUB_PAIR_QUERY
                  and dict(q.params) == {'Num': 1, 'Actor': SCRUB_WAS} and (has, has_not) == (0, 1)
                  and [(sells[v].entry, sells[v].params['ActorName'], sells[v].params['Price']) for v in (0, 1)]
                  == [(build_mod.SCRUB_SELL, 'Item_StickBag_Large', 40), (build_mod.SCRUB_SELL, SCRUB_WAS, 40)]
                  and {k: v for k, v in sells[0].params.items() if k != 'ActorName'}
                  == {k: v for k, v in sells[1].params.items() if k != 'ActorName'}
                  and dict(q_params) == dict(q.params) and q_actor == q.actor)
    good &= check("  the game's flow writes a scrub item name (EventTriggerSetGameDataString64) and waits "
                  '(EventSystemActor.EventWait, %d frame)' % wait_params['Frames'],
                  sorted(w_params) == ['GameDataName', 'Index', 'Value'] and w_params['Index'] == -1
                  and str(w_params['GameDataName']).startswith('Scrub_Business_TempItemName_')
                  and orig.actors[wait_actor].name == 'EventSystemActor'
                  and dict(wait_params) == {'Frames': 1, 'IsWaitEnd': True})
    sync_steps = build_mod.sync_template(evfl.loads(plain(build_mod.SYNC_FLOW)).flowchart)

    def edit(pair, sales=None, pairs=None, tamper=None):
        direct = {x for x in pair if not ground_items.can_hold_up(plain, x)}
        sync = {x: sync_steps for x in pair if x in direct}
        ef = evfl.loads(old_flow)
        said = build_mod.scrub_flow_edit(
            ef.flowchart, sales or [(SCRUB, pair[0], [(SCRUB_TALK, SCRUB_WAS)])], direct, sync,
            {SCRUB: pair} if pairs is None else pairs)
        if tamper:
            tamper(ef.flowchart)
            build_mod.scrub_pair_check(ef.flowchart, *pair)
        return evfl.loads(build_mod.flow_write_checked(ef)).flowchart, said, direct

    back, said, direct = edit(SCALES)
    by = {e.name: e for e in back.events}
    new_names = [e.name for e in back.events[len(orig.events):]]
    got = build_mod.scrub_pair_read(back, SCALES[0])
    good &= check('scales: six new steps (the name check, the question, the write, the wait, the two sales), no '
                  'new actor, action or question',
                  not direct and len(new_names) == 6 and len(back.events) == len(orig.events) + 6
                  and [e.name for e in back.events[:len(orig.events)]] == [e.name for e in orig.events]
                  and [actor_shape(a) for a in back.actors] == [actor_shape(a) for a in orig.actors])
    good &= check('  the question is the game\'s: PouchSystemActor.EventQueryIsExistInPouch {Num: 1, Actor: '
                  'Item_Scale_Silver}', got['ask'] == {'Num': 1, 'Actor': SCALES[0]} and got['second'] == SCALES[1])
    one, two = got['sells']
    good &= check('  1 (has no Silver Scale) -> the one-time sale of the Silver Scale; 0 (has it) -> of the Gold '
                  'Scale; same price (40), same line, only the item differs',
                  one['ActorName'] == SCALES[0] and two['ActorName'] == SCALES[1] and one['Price'] == 40
                  and one['SellerMessageId'] == 'EventFlowMsg/Enemy_Event:' + build_mod.SCRUB_LABEL
                  and {k: v for k, v in one.items() if k != 'ActorName'}
                  == {k: v for k, v in two.items() if k != 'ActorName'}
                  and list(one) == list(sells[1].params))
    good &= check('  before the Gold Scale\'s sale: its name written into %s, then a wait of %d frames'
                  % (build_mod.SCRUB_VAR, build_mod.SCRUB_WRITE_WAIT),
                  got['steps'] == [('GameDataActor', 'EventTriggerSetGameDataString64',
                                    {'Index': -1, 'GameDataName': build_mod.SCRUB_VAR, 'Value': SCALES[1]}),
                                   ('EventSystemActor', 'EventWait',
                                    {'Frames': build_mod.SCRUB_WRITE_WAIT, 'IsWaitEnd': True})]
                  and build_mod.SCRUB_WRITE_WAIT >= wait_params['Frames'])
    # the game's steps: all as they were, but the links to the root's first name check now go to the new one
    head = next(e for e in back.events[len(orig.events):] if e.type == 'switch' and isinstance(e.params, dict)
                and e.params.get('GameDataName') == build_mod.SCRUB_VAR and e.params.get('Value') == SCALES[0])
    old_head = back.events[dict(head.cases)[1]].name
    moved = {old_head: head.name}
    others = all(step(back, by[e.name]) == step(orig, e, moved) for e in orig.events)
    good &= check('  every step of the game\'s flow is as it was (%d steps); what led to the root\'s first name '
                  'check (%s) leads to the new one, which goes on to it for any other name'
                  % (len(orig.events), old_head),
                  others and old_head in {e.name for e in orig.events}
                  and by[old_head].params.get('GameDataName') == build_mod.SCRUB_VAR
                  and dict(head.params) == {'GameDataName': build_mod.SCRUB_VAR, 'Index': -1, 'Value': SCALES[0]})
    eps = True
    for p, po in zip(back.entry_points, orig.entry_points):
        calls = [orig.events[i].name for i in po.subflows]
        extra = [back.events[i].name for i in p.subflows if back.events[i].name not in calls]
        eps &= p.name == po.name and moved.get(orig.events[po.main].name, orig.events[po.main].name) \
            == back.events[p.main].name and [back.events[i].name for i in p.subflows][:len(calls)] == calls \
            and (len(extra) == 2 and set(extra) <= set(new_names) if p.name == build_mod.SCRUB_ROOT else not extra)
    good &= check('  entry points: the same starts; the one-time root lists the two new sales', eps
                  and len(back.entry_points) == len(orig.entry_points))
    good &= check('  the scrub\'s talk still runs the one-time root (which marks the scrub sold for good after a '
                  'buy)', by[orig.events[{p.name: p.main for p in orig.entry_points}[SCRUB_TALK]].name].entry
                  == build_mod.SCRUB_ROOT)
    print('\n'.join('  ' + line for line in said))

    # ocarinas: Link can't hold them up, so each is sorted out by name in front of the pay-and-get call
    back, said, direct = edit(OCARINAS)
    got = build_mod.scrub_pair_read(back, OCARINAS[0])
    eps_of = {p.name: p.main for p in back.entry_points}
    gets = {}
    for i in build_mod.flow_reachable(back, eps_of[build_mod.SCRUB_SELL]):
        e = back.events[i]
        if e.type == 'switch' and isinstance(e.params, dict) and e.params.get('GameDataName') == build_mod.SCRUB_VAR:
            k, names = back.events[dict(e.cases)[0]], []
            while k is not None and len(names) < 12:
                names.append((build_mod._action_name(back, k) if k.type == 'action' else k.flowchart,
                              k.params.get('ActorName') if k.type == 'subflow' else None))
                if k.type == 'subflow':
                    break
                k = back.events[k.next] if k.next is not None else None
            gets[e.params['Value']] = names
    want = lambda item: [('EventTriggerAddGameDataIntToRupee', None), ('EventWaitStableNumDisplay', None),   # noqa: E731
                         (build_mod.DIRECT_GET[0], item)]
    good &= check('ocarinas: the question asks for the Fairy Ocarina; each is paid and given with the get window '
                  'under its own name (the Ocarina of Time through the name written)',
                  direct == set(OCARINAS) and got['second'] == OCARINAS[1]
                  and got['ask'] == {'Num': 1, 'Actor': OCARINAS[0]}
                  and got['steps'][0][2]['Value'] == OCARINAS[1]
                  and gets == {x: want(x) for x in OCARINAS})

    # refusals
    good &= check('refused: a pair on a scrub that sells again and again; a scrub selling Second, or First '
                  'alone, beside the pair',
                  refused(edit, SCALES, [(SCRUB, SCALES[0], [(REPEAT_TALK, 'Item_DekuSeed')])])
                  and refused(edit, SCALES, [(SCRUB, SCALES[0], [(SCRUB_TALK, SCRUB_WAS)]),
                                             ('OTHER', SCALES[1], [(SCRUB_TALK, SCRUB_WAS)])])
                  and refused(edit, SCALES, [(SCRUB, SCALES[0], [(SCRUB_TALK, SCRUB_WAS)]),
                                             ('OTHER', SCALES[0], [(SCRUB_TALK, SCRUB_WAS)])])
                  and not refused(edit, SCALES))
    good &= check('refused: a pair whose first level is not what the scrub sells; an item the game\'s own '
                  'branches sell as Second',
                  refused(edit, SCALES, [(SCRUB, SCALES[1], [(SCRUB_TALK, SCRUB_WAS)])])
                  and refused(edit, ('Item_Scale_Silver', 'Item_StickBag_Medium')))

    def swap(fc):                                      # the two answers the wrong way round
        e = next(e for e in fc.events[len(orig.events):] if e.type == 'switch'
                 and fc.actors[e.actor].queries[e.query] == build_mod.SCRUB_PAIR_QUERY)
        e.cases = [(0, dict(e.cases)[1]), (1, dict(e.cases)[0])]

    def no_wait(fc):                                   # the name written, but no wait
        e = next(e for e in fc.events[len(orig.events):] if e.type == 'action'
                 and build_mod._action_name(fc, e) == build_mod.SCRUB_NAME_WRITE)
        e.next = fc.events[e.next].next

    def other_name(fc):                                # another name written than the one sold
        e = next(e for e in fc.events[len(orig.events):] if e.type == 'action'
                 and build_mod._action_name(fc, e) == build_mod.SCRUB_NAME_WRITE)
        e.params['Value'] = SCALES[0]

    good &= check('the read-back notices: the answers swapped, the wait missing, another name written',
                  refused(edit, SCALES, None, None, swap) and refused(edit, SCALES, None, None, no_wait)
                  and refused(edit, SCALES, None, None, other_name)
                  and not refused(edit, SCALES, None, None, lambda fc: None))

    # ------------------------------------------------------------------------------------- whole builds
    print('Whole builds')
    with tempfile.TemporaryDirectory() as tmp:
        fix = [x for f in FIXES for x in ('--fix', f)]

        def run(name, *assign):
            with contextlib.redirect_stdout(io.StringIO()) as said:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + fix + list(assign))
            base = os.path.join(tmp, name, 'romfs')
            return base, said.getvalue(), {os.path.relpath(f, base).replace(os.sep, '/')
                                           for f in glob.glob(os.path.join(base, '**', '*'), recursive=True)
                                           if os.path.isfile(f)}

        mod = lambda b, path: rd(os.path.join(b, *path.split('/')) + '.zs')   # noqa: E731
        raw = lambda b, path: open(os.path.join(b, *path.split('/')), 'rb').read()   # noqa: E731
        scales, hooks, ocarinas = ('>'.join(p) for p in (SCALES, HOOKS, OCARINAS))
        # (a pair on a pot or a Gold Skulltula builds since 2026-11-22: tests/one_time_check.py,
        # tests/skulltula_prog_check.py)
        good &= check('the build refuses: a pair on a shelf; two rocks of one family side by side',
                      refused(run, 'no3', 'KF_KOKIRI_CHILD_SHOP_01=' + scales)
                      and refused(run, 'no4', *[c + '=' + scales for c in CLOSE]))
        base0, _, files0 = run('fixes')
        base, said, files = run('pairs', *([c + '=' + scales for c in ROCKS] + [c + '=' + hooks for c in BUSHES]
                                           + [SCRUB + '=' + ocarinas, CHEST + '=' + ocarinas]))
        # the second levels' turning items (what the one-time versions turn into; a family only on rocks and
        # bushes has no first-level turning item)
        turns = [turn_items.turn_name(x) for x in (SCALES[1], HOOKS[1])]
        onces = [once_items.once_name(x) for x in SCALES + HOOKS]     # what the rocks and bushes drop: given once
        held = [ground_items.ground_name(x, 'held') for x in OCARINAS]
        mals = {'Mals/' + f for f in os.listdir(os.path.join(romfs, 'Mals')) if f.endswith('.sarc.zs')}
        new_files = files - files0
        want_files = {f + '.zs' for f in (CHILD_MAP, ADULT_MAP, build_mod.SCRUB_FLOW) + SCRUB_MAPS} | mals \
            | {ground_items.pack_path(n) + '.zs' for n in turns + onces + held + list(ONCE_PACKS)} \
            | {ground_items.table_path(t) + '.zs' for t in ground_items.TABLES} \
            | {f + '.zs' for f in (build_mod.flow_path(build_mod.TBOX_SYNC_FLOW), build_mod.EVENT_SETTING,
                                   build_mod.EVENT_INFO)}
        anims = {f for f in new_files - want_files if f.startswith('Model/NX2G') and f.endswith('.anim.bfres.zs')}
        good &= check('whole build (two rocks, two bushes, the scrub and a chest): beside the fixes\' files the '
                      'maps, the scrub flow and lines, 4 one-time versions and 2 second-level turning items, the %d packs '
                      'of the rock and the bush, 2 held-up ocarinas, their rows, %d lifted poses'
                      % (len(ONCE_PACKS), len(anims)),
                      new_files - anims == want_files - files0 and want_files - files0 <= files and files0 <= files
                      and len(anims) == 3      # both scales and the hookshots (lifted since 2026-11-22)
                      and all(raw(base, f) == raw(base0, f) for f in files0 - want_files if f != RESTBL + '.zs'))

        def changed(m):
            """what differs in a map from the fixes' build (the game's file when the fixes don't touch it):
            (rocks' and bushes' new drops, chests' (actor before, after, item looked for, item given then),
            scrubs' new items, how many placements differ in all); None when anything else differs"""
            was = mod(base0, m) if m + '.zs' in files0 else plain(m)
            a, b = byml.loads(was).root, byml.loads(mod(base, m)).root
            if len(a['Actors']) != len(b['Actors']) or list(a) != list(b) \
                    or any(a[k] != b[k] for k in a if k != 'Actors'):
                return None
            drops, chests, scrubs, n = [], [], [], 0
            for x, y in zip(a['Actors'], b['Actors']):
                if x == y:
                    continue
                n += 1
                # (a rock or bush with no settings of its own gets its first: the key Dynamic is new)
                if any(x[k] != y[k] for k in x if k not in ('Dynamic', 'Gyaml')) \
                        or [k for k in x if k != 'Dynamic'] != [k for k in y if k != 'Dynamic']:
                    return None
                dx, dy = dict(x.get('Dynamic') or {}), dict(y['Dynamic'])
                if x['Gyaml'] in DROPPERS[:2] and y['Gyaml'] == x['Gyaml'] \
                        and dy == dict(dx, Drop__DropActor=dy.get('Drop__DropActor')) and 'Drop__DropActor' not in dx:
                    drops.append((x['Gyaml'].split('_A_')[0], dy['Drop__DropActor']))
                elif x['Gyaml'] == 'Enemy_Scrub_Business' == y['Gyaml'] and dx[build_mod.SCRUB_SETTING] == SCRUB_WAS \
                        and dy == dict(dx, **{build_mod.SCRUB_SETTING: dy[build_mod.SCRUB_SETTING]}):
                    scrubs.append(dy[build_mod.SCRUB_SETTING])
                elif x['Gyaml'] != y['Gyaml']:
                    chests.append((x['Gyaml'], y['Gyaml'], dy.get('Drop__CheckActor'),
                                   dy.get('Drop__DropActor_Substitute')))
                else:
                    return None
            return sorted(drops), chests, scrubs, n

        chest = [('Obj_TBox_A_01', 'Obj_TBox_A_06', OCARINAS[0], held[1])]
        good &= check('  %s: 3 placements changed: two rocks drop %s, Mido\'s chest a checking chest for the '
                      'ocarinas' % (CHILD_MAP.split('/')[-1].split('.')[0], onces[0]),
                      changed(CHILD_MAP) == ([('Obj_LiftRock', onces[0])] * 2, chest, [], 3))
        good &= check('  %s: 3 placements changed: two bushes drop %s, the scrub sells the Fairy Ocarina (the '
                      'first level)' % (BUSH_MAP.split('/')[-1].split('.')[0], onces[2]),
                      changed(BUSH_MAP) == ([('Obj_Plant_Grass', onces[2])] * 2, [], [OCARINAS[0]], 3))
        good &= check('  the adult maps and the Lost Woods: only the chest and the scrub\'s other three placements '
                      '(the child rocks and bushes are in no other map)',
                      changed(ADULT_MAP) == ([], chest, [], 1)
                      and all(changed(m) == ([], [], [OCARINAS[0]], 1) for m in SCRUB_MAPS if m != BUSH_MAP)
                      and BUSH_MAP in SCRUB_MAPS)
        flow = evfl.loads(mod(base, build_mod.SCRUB_FLOW)).flowchart
        got = build_mod.scrub_pair_check(flow, *OCARINAS)
        texts = msbt.Msbt.read(sarc.Sarc.read(mod(base, sorted(mals)[0][:-3])).files[build_mod.SCRUB_MSG_FILE]).texts
        good &= check('  the scrub flow written holds the pair\'s branch (read back from the file), the line is '
                      'in the message archives',
                      got['second'] == OCARINAS[1] and got['sells'][0]['Price'] == 40
                      and texts.get(build_mod.SCRUB_LABEL) == build_mod.SCRUB_LINE)
        packs = True
        for n, (family, level) in zip(turns, [(SCALES, 1), (HOOKS, 1)]):
            want_name, want_pack, _, _, _ = turn_items.build(family, level, plain, table_rows, model)
            packs &= want_name == n and mod(base, ground_items.pack_path(n)) == want_pack
        t1 = restbl.Restbl.read(mod(base, RESTBL))
        rows = {t: {r['__RowId'] for r in byml.loads(mod(base, ground_items.table_path(t))).root}
                for t in ground_items.TABLES}
        good &= check('  the two turning items are the ones tools/turn_items.py makes (as on freestanding items), '
                      'each with its three rows and a size entry',
                      packs and all(n in rows[t] for n in turns for t in ground_items.TABLES)
                      and all(t1.get(ground_items.pack_path(n)) for n in turns))
        packs = True
        for n, (family, level) in zip(onces, [(SCALES, 0), (SCALES, 1), (HOOKS, 0), (HOOKS, 1)]):
            want_name, want_pack, _, _, _ = once_items.build(family, level, plain, table_rows, model)
            packs &= want_name == n and mod(base, ground_items.pack_path(n)) == want_pack
        good &= check('  the four one-time versions are the ones tools/once_items.py makes (tests/one_time_check.py), '
                      'each with its three rows and a size entry',
                      packs and all(n in rows[t] for n in onces for t in ground_items.TABLES)
                      and all(t1.get(ground_items.pack_path(n)) for n in onces))
        print('\n'.join('  ' + line[:200] for line in said.splitlines()
                        if line.startswith(ROCKS + BUSHES + (SCRUB, 'scrub flow'))))

    good &= check('the 4 adult corner rocks of the circle are used by no test or check build here',
                  not set(CORNERS) & set(ROCKS + BUSHES + CLOSE + (SCRUB, CHEST)))
    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
