"""Progressive gift test: what tools/build_mod.py makes of a progressive pair on a gift (the inventory question
in the giver's own flow), on the game's own files. Only reads the game; the one whole build it runs goes to a
temporary folder that is removed again.

    python tests/gift_check.py "C:\\...\\romfs"
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
import sizes  # noqa: E402
from formats import zstd, byml, evfl, restbl  # noqa: E402
from logic.world import World  # noqa: E402

GIFT = 'KF_CIRCLE_KOKIRI_GIFT'                      # the rock-circle Kokiri: Npc_Kokiri_008_Child, Event224
FLOW = 'Event/EventFlow/Npc_Kokiri_008_Child.bfevfl'
EVENT, WAS = 'Event224', 'Obj_Rupee_Blue'
CHEST = 'KF_MIDO_CHEST_04'
MAPS = ('Banc/KokiriForest/KokiriForest_Adult_Dynamic.bcett.byml',
        'Banc/KokiriForest/KokiriForest_Child_Dynamic.bcett.byml')
PAIR = ('Item_Scale_Silver', 'Item_Scale_Gold')
OCARINAS = ('Item_Ocarina_Fairy', 'Item_Ocarina_Time')
RESTBL = build_mod.RESTBL_PATH.replace(os.sep, '/')[:-3]   # the size table, as plain() and mod() name files
FIXES = ('skippable_opening', 'bombs_without_bracelet', 'magic_is_separate', 'bombchus_without_bag',
         'kokiri_shop_full_stock', 'kokiri_circle_after_dungeons')
# gifts a pair is refused on: two gifts with no flow data (Saria's cutscene gift and the songs take families
# their own way since 2026-11-23: tests/event_families_check.py)
NO_DATA = ('LW Skull Kid', 'Deku Theater Skull Mask')
OWN_WAY = {'LW_SARIA_GIFT': 'cutscene', 'Song from Saria': 'song'}


def check(name, ok):
    print('%-98s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def refused(f, *args):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            f(*args)
    except SystemExit as e:
        return bool(e.code)
    return False


def actor_shape(a):
    return a.name, a.secondary, a.argument, a.params, a.entry_point, a.cut


def step(fc, e):
    """an event apart from its index: what it is and the names of the events it leads to"""
    name = lambda i: None if i is None else fc.events[i].name   # noqa: E731
    a = fc.actors[e.actor] if e.type in ('action', 'switch') else None
    return (e.type, actor_shape(a) if a else None, a.actions[e.action] if e.type == 'action' else None,
            a.queries[e.query] if e.type == 'switch' else None,
            list(e.params.items()) if isinstance(e.params, dict) else e.params, e.flowchart, e.entry, e.value,
            name(e.next), name(e.join), [(v, name(c)) for v, c in e.cases], [name(f) for f in e.forks])


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    rd = lambda f: zstd.decompress(open(f, 'rb').read(), d)   # noqa: E731
    plain = lambda path: rd(os.path.join(romfs, *path.split('/')) + '.zs')   # noqa: E731
    world = World()
    good = True

    # the game's own pattern
    theater = evfl.loads(plain(build_mod.GIFT_PAIR_FLOW)).flowchart
    actor, params, has, has_not = template = build_mod.gift_pair_template(theater)
    good &= check("the game's question (Deku Theater): PouchSystemActor.EventQueryIsExistInPouch {Num: 1, Actor}, "
                  '0 = has it',
                  actor.name == 'PouchSystemActor' and not actor.secondary and list(params) == ['Num', 'Actor']
                  and params['Num'] == 1 and (has, has_not) == (0, 1))
    q = theater.events[theater.event_index('Event30')]
    gives = {v: theater.events[c] for v, c in q.cases}
    good &= check('  Event30: has the medium stick bag -> gives the large one, else the medium one, same next step',
                  theater.actors[q.actor].queries[q.query] == build_mod.GIFT_PAIR_QUERY
                  and q.params['Actor'] == 'Item_StickBag_Medium'
                  and [(gives[v].flowchart, gives[v].entry, gives[v].params['ActorName']) for v in (0, 1)]
                  == [('Dm_SY_GetInEvent', 'GetInEvent_NotTurn', 'Item_StickBag_Large'),
                      ('Dm_SY_GetInEvent', 'GetInEvent_NotTurn', 'Item_StickBag_Medium')]
                  and gives[0].next == gives[1].next is not None)
    same, flows, asked, questions, fork_heads = True, 0, set(), 0, 0
    for f in sorted(glob.glob(os.path.join(romfs, 'Event', 'EventFlow', '*.bfevfl.zs'))):
        try:
            fc = evfl.loads(rd(f)).flowchart
        except Exception:
            continue                                   # flows the reader refuses (timelines): see README
        heads = {x for e in fc.events if e.type == 'fork' for x in e.forks}
        for a in fc.actors:
            if a.name == 'PouchSystemActor':
                flows += 1
                same &= actor_shape(a) == actor_shape(actor)
        for i, e in enumerate(fc.events):
            if e.type != 'switch':
                continue
            if i in heads and len(e.cases) == 2 and all(
                    fc.events[c].type == 'subflow' and fc.events[c].next is None for _, c in e.cases):
                fork_heads += 1
            if fc.actors[e.actor].queries[e.query] == build_mod.GIFT_PAIR_QUERY:
                questions += 1
                same &= sorted(e.params) == ['Actor', 'Num'] and e.params['Num'] == 1 \
                    and {v for v, _ in e.cases} <= {0, 1}
                asked.add(str(e.params['Actor']))
    good &= check('every flow of the game with a PouchSystemActor has the same entry (%d flows), every such '
                  'question the same shape (%d)' % (flows, questions), same and flows > 100 and questions > 100)
    good &= check("the game's flows ask about each pair's first item under its own name (but the magic meter: "
                  'no flow asks the inventory for it)',
                  all(p[0] in asked for p in build_mod.PROGRESSIVE_PAIRS if p[0] != 'Item_FairyBless_MP')
                  and 'Item_FairyBless_MP' not in asked)
    good &= check('the game has forks whose branch starts with a two-way switch between two calls that end the '
                  'branch (%d)' % fork_heads, fork_heads > 0)

    # where a pair goes
    good &= check('a pair is accepted on the rock-circle Kokiri\'s gift (it has flow data)',
                  build_mod.gift_pair_kind(world, GIFT) is True)
    good &= check('a chest and a freestanding item are not gifts (their own ways stay)',
                  build_mod.gift_pair_kind(world, CHEST) is False
                  and build_mod.gift_pair_kind(world, 'KF_RUPEE_NEAR_MIDO_ITEM') is False)
    good &= check('refused: gifts with no flow data; Saria\'s cutscene gift and a song are not gifts of this '
                  'kind (they take families their own way)',
                  all(refused(build_mod.gift_pair_kind, world, c) for c in NO_DATA)
                  and all(build_mod.gift_pair_kind(world, c) is False
                          and build_mod.song_pair_kind(world, c) == (k == 'song')
                          and build_mod.cutscene_pair_kind(world, c) == (k == 'cutscene')
                          for c, k in OWN_WAY.items()))
    good &= check('not gifts: a scrub (its own way: tests/pairs_more_check.py), a pot (a turning item: '
                  'tests/one_time_check.py); refused as before: a shelf',
                  build_mod.gift_pair_kind(world, 'LW_NEAR_BRIDGE_SCRUB') is False
                  and build_mod.scrub_pair_kind(world, 'LW_NEAR_BRIDGE_SCRUB') is True
                  and build_mod.gift_pair_kind(world, 'KF_HOUSE_OF_TWINS_CHILD_POT_01') is False
                  and build_mod.pair_kind(world, 'KF_HOUSE_OF_TWINS_CHILD_POT_01') == 'pot'
                  and build_mod.gift_pair_kind(world, 'KF_KOKIRI_CHILD_SHOP_01') is False
                  and refused(build_mod.pair_kind, world, 'KF_KOKIRI_CHILD_SHOP_01'))

    # the Kokiri's flow with the pair
    old = plain(FLOW)
    orig = evfl.loads(old).flowchart
    sync_steps = build_mod.sync_template(evfl.loads(plain(build_mod.SYNC_FLOW)).flowchart)

    def build(pair, tamper=None):
        direct = {x for x in pair if not ground_items.can_hold_up(plain, x)}
        sync = {x: sync_steps for x in pair if x in direct}
        ef = evfl.loads(old)
        build_mod.gift_edit(ef.flowchart, {EVENT: (GIFT, pair[0], WAS)}, direct, sync)
        first = build_mod.flow_write_checked(ef)
        said, made = build_mod.gift_pair_edit(ef.flowchart, {EVENT: (GIFT, pair)}, template, direct)
        if tamper:
            tamper(ef.flowchart, made)
        new = build_mod.flow_write_checked(ef)
        build_mod.gift_pair_read_back(FLOW, evfl.loads(first).flowchart, evfl.loads(new).flowchart,
                                      {EVENT: (GIFT, pair)}, made, template)
        return evfl.loads(first).flowchart, new, made, direct

    before, new, made, direct = build(PAIR)
    back = evfl.loads(new).flowchart
    by = {e.name: e for e in back.events}
    ask, second, gift = by[made[EVENT][0]], by[made[EVENT][1]], by[EVENT]
    good &= check('scales: two new steps and one new actor read back, nothing held up differently',
                  not direct and len(back.events) == len(orig.events) + 2
                  and [e.name for e in back.events[:len(orig.events)]] == [e.name for e in orig.events]
                  and {e.name for e in back.events[len(orig.events):]} == set(made[EVENT])
                  and len(back.actors) == len(orig.actors) + 1)
    good &= check('  the new actor is PouchSystemActor as the game\'s flows have it, with only the question',
                  actor_shape(back.actors[-1]) == actor_shape(actor)
                  and (back.actors[-1].actions, back.actors[-1].queries) == ([], [build_mod.GIFT_PAIR_QUERY])
                  and all(actor_shape(a) == actor_shape(b) and a.actions == b.actions and a.queries == b.queries
                          for a, b in zip(back.actors, orig.actors)))
    good &= check('  the question is the game\'s: EventQueryIsExistInPouch {Num: 1, Actor: Item_Scale_Silver}',
                  step(back, ask)[:5] == ('switch', actor_shape(actor), None, build_mod.GIFT_PAIR_QUERY,
                                          [('Num', 1), ('Actor', PAIR[0])]))
    good &= check('  the branch: 0 (has the Silver Scale) -> the Gold Scale, 1 (has not) -> the Silver Scale',
                  [(v, back.events[c].params['ActorName']) for v, c in ask.cases]
                  == [(0, PAIR[1]), (1, PAIR[0])] and ask.cases[1][1] == back.event_index(EVENT)
                  and back.events[ask.cases[0][1]] is second)
    o = orig.events[orig.event_index(EVENT)]
    want = [(k, v) for k, v in o.params.items()]
    good &= check('  both are the gift\'s own call of Dm_SY_GetInEvent<GetInEvent_NotTurn>, only the item differs',
                  all((e.type, e.flowchart, e.entry) == ('subflow', o.flowchart, o.entry)
                      and [(k, v) for k, v in e.params.items() if k != 'ActorName']
                      == [(k, v) for k, v in want if k != 'ActorName'] and list(e.params) == list(o.params)
                      for e in (gift, second)) and o.params['ActorName'] == WAS)
    good &= check('  both end where the gift ended (the end of its fork branch)',
                  gift.next == second.next == o.next and o.next is None)
    links = [e.name for i, e in enumerate(orig.events) if orig.event_index(EVENT) in orig.links(i)]
    good &= check('  what led to the gift (%s, a fork) now leads to the question; the gift is only reached '
                  'through it' % ', '.join(links),
                  len(links) == 1 and [e.name for i, e in enumerate(back.events)
                                       if back.event_index(ask.name) in back.links(i)] == links
                  and [e.name for i, e in enumerate(back.events)
                       if back.event_index(EVENT) in back.links(i)] == [ask.name])
    others = all(step(back, by[e.name]) == step(orig, e) for e in orig.events if e.name not in links + [EVENT])
    fork = [step(back, by[n]) for n in links] == [
        step(orig, orig.events[orig.event_index(n)])[:11] + ([ask.name if f == EVENT else f for f in
                                                              step(orig, orig.events[orig.event_index(n)])[11]],)
        for n in links]
    good &= check('  every other step of the flow is as in the game (%d steps)' % (len(orig.events) - 2),
                  others and fork)
    eps = True
    for p, po in zip(back.entry_points, orig.entry_points):
        calls = [orig.events[i].name for i in po.subflows]
        eps &= p.name == po.name and back.events[p.main].name == orig.events[po.main].name \
            and [back.events[i].name for i in p.subflows] == calls + ([second.name] if EVENT in calls else [])
    good &= check('  entry points: the same starts; the two that list the gift\'s call also list the second call',
                  eps and len(back.entry_points) == len(orig.entry_points)
                  and sum(1 for p in back.entry_points if back.event_index(second.name) in p.subflows) == 2)
    good &= check('  written twice, the same bytes; reads back as written',
                  build(PAIR)[1] == new and evfl.dumps(evfl.loads(new)) == new)
    table = restbl.Restbl.read(plain(RESTBL))
    need = sizes.entry(FLOW, new, table.get(FLOW), old)
    good &= check('  size entry: the length rounded up to 32, plus 272, as the game\'s flows (%d -> %d)'
                  % (table.get(FLOW), need),
                  need == (len(new) + 31) // 32 * 32 + 272 and table.get(FLOW) == (len(old) + 31) // 32 * 32 + 272)

    def swap(fc, made):                                # the branch the wrong way round
        e = fc.events[fc.event_index(made[EVENT][0])]
        e.cases = [(0, e.cases[1][1]), (1, e.cases[0][1])]

    def rename(fc, made):                              # the second call naming another item
        fc.events[fc.event_index(made[EVENT][1])].params['ActorName'] = 'Item_Longshot'

    good &= check('  the read-back stops a branch the wrong way round, and a second call naming another item',
                  refused(build, PAIR, swap) and refused(build, PAIR, rename))

    # the other pairs
    before, new_h, made_h, direct = build(('Item_Hookshot', 'Item_Longshot'))
    back = evfl.loads(new_h).flowchart
    by = {e.name: e for e in back.events}
    ask = by[made_h[EVENT][0]]
    good &= check('hookshots: asks for the Hookshot; has it -> the Longshot, else the Hookshot, both held up',
                  not direct and ask.params['Actor'] == 'Item_Hookshot'
                  and [(v, back.events[c].flowchart, back.events[c].params['ActorName']) for v, c in ask.cases]
                  == [(0, 'Dm_SY_GetInEvent', 'Item_Longshot'), (1, 'Dm_SY_GetInEvent', 'Item_Hookshot')])
    before, new_o, made_o, direct = build(OCARINAS)
    back = evfl.loads(new_o).flowchart
    by = {e.name: e for e in back.events}
    ask = by[made_o[EVENT][0]]
    calls = [back.events[c] for _, c in ask.cases]
    good &= check('ocarinas (Link can\'t hold them up): both given with the get window, then the same sync steps',
                  direct == set(OCARINAS) and ask.params['Actor'] == OCARINAS[0]
                  and [(e.flowchart, e.entry, dict(e.params)) for e in calls]
                  == [(build_mod.DIRECT_GET[0], build_mod.DIRECT_GET[1], {'ActorName': x}) for x in OCARINAS[::-1]]
                  and calls[0].next == calls[1].next is not None
                  and back.actors[back.events[calls[0].next].actor].actions[back.events[calls[0].next].action]
                  == 'EventWait')

    # refusals of the edit itself
    def edit(pair, direct=(), event=EVENT):
        ef = evfl.loads(old)
        if event == EVENT:
            build_mod.gift_edit(ef.flowchart, {EVENT: (GIFT, pair[0], WAS)})
        build_mod.gift_pair_edit(ef.flowchart, {event: (GIFT, pair)}, template, direct)

    good &= check('refused: one item held up and the other not; an event that is not the gift\'s call; no event',
                  not refused(edit, PAIR) and refused(edit, PAIR, {PAIR[1]})
                  and refused(edit, PAIR, (), 'Event166') and refused(edit, PAIR, (), 'Event9999'))

    # one whole build: the six usual fixes, the gift and a checking chest of the same family
    with tempfile.TemporaryDirectory() as tmp:
        fix = [x for f in FIXES for x in ('--fix', f)]

        def run(name, *assign):
            with contextlib.redirect_stdout(io.StringIO()) as said:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + fix + list(assign))
            base = os.path.join(tmp, name, 'romfs')
            return base, said.getvalue(), {os.path.relpath(f, base).replace(os.sep, '/')
                                           for f in glob.glob(os.path.join(base, '**', '*'), recursive=True)
                                           if os.path.isfile(f)}

        pair = '>'.join(PAIR)
        good &= check('the build refuses: a pair on a gift with no flow data, a pair the builder doesn\'t know, '
                      'the gift without the rock circle fix',
                      refused(run, 'no1', NO_DATA[0] + '=' + pair)
                      and refused(run, 'no2', GIFT + '=Item_Scale_Silver>Item_Longshot')
                      and refused(build_mod.main, ['--romfs', romfs, '--out', tmp, '--name', 'no3',
                                                   GIFT + '=' + pair]))
        base0, _, files0 = run('fixes')
        base, said, files = run('pair', GIFT + '=' + pair, CHEST + '=' + pair)
        mod = lambda b, path: rd(os.path.join(b, *path.split('/')) + '.zs')   # noqa: E731
        raw = lambda b, path: open(os.path.join(b, *path.split('/')), 'rb').read()   # noqa: E731
        good &= check('whole build: beside the fixes\' files only the Kokiri\'s flow and the two maps of the chest',
                      files - files0 == {f + '.zs' for f in (FLOW,) + MAPS} and files0 <= files
                      and all(raw(base, f) == raw(base0, f) for f in files0 if f != RESTBL + '.zs'))
        good &= check('  the flow is the one read back above',
                      mod(base, FLOW) == new)
        ok = True
        for m in MAPS:
            a, b = byml.loads(plain(m)).root, byml.loads(mod(base, m)).root
            diff = [(x, y) for x, y in zip(a['Actors'], b['Actors']) if x != y]
            ok &= len(a['Actors']) == len(b['Actors']) and len(diff) == 1 \
                and all(a[k] == b[k] for k in a if k != 'Actors') and list(a) == list(b)
            for x, y in diff:
                ok &= (x['Gyaml'], y['Gyaml']) == ('Obj_TBox_A_01', 'Obj_TBox_A_06') \
                    and all(x[k] == y[k] for k in x if k not in ('Gyaml', 'Dynamic')) and list(x) == list(y) \
                    and dict(y['Dynamic']) == dict(x['Dynamic'], Drop__DropActor=PAIR[0], Drop__CheckActor=PAIR[0],
                                                   Drop__DropActor_Substitute=PAIR[1])
        good &= check('  each map: one actor changed, Mido\'s chest made a checking chest for the same pair', ok)
        t0, t1 = restbl.Restbl.read(mod(base0, RESTBL)), restbl.Restbl.read(mod(base, RESTBL))
        entries = {f: t1.get(f) for f in [FLOW] + list(MAPS)}
        good &= check('  size table: only those three entries differ from the fixes\' build; each meets the rules',
                      t1.get(FLOW) == need
                      and all(t1.get(m) >= build_mod.map_entry(len(mod(base, m))) for m in MAPS)
                      and all(t0.get(f) == table.get(f) != entries[f] for f in entries)
                      and same_but(t0, t1, set(entries)))
        print('\n'.join(line for line in said.splitlines() if line.startswith((GIFT, CHEST))))

    print('\nALL OK' if good else '\nSOMETHING FAILED')
    return 0 if good else 1


def same_but(t0, t1, paths):
    """two size tables with the same entries, but for the named paths"""
    for p in paths:
        t0.set(p, t1.get(p))
    return t0.crc == t1.crc and t0.names == t1.names


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
