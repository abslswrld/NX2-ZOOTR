"""Event flow "add" test: add new steps to the game's event flows, write, read back, and check that what
was read is what was meant. Reads only; writes nothing to the romfs and builds no mod.

    python tests/evfl_add_check.py "C:\\...\\romfs"

1. Every event flow our reader takes (the others have timelines or entry point variables):
   - unchanged, it passes the checks, its entry point lists are what we would work out, and
     `dumps_checked` gives the game's bytes back;
   - then one event of every type, a new actor, a new action and a new query are added and linked in, and
     the file read back is compared with what was meant: old parts untouched, new parts as written.
2. Mistakes are refused (a name used twice, a link to an event that isn't there...).
3. Two worked examples, the uses we have in mind. They are examples only: nothing in the builder uses them
   and neither has been tried in the game yet.
   - `example_item_get`: the steps that give an item with its "you got ..." window.
   - `example_shop_bottle`: in `DisplayShop` (the flow every shop shares), a branch before the game's buy
     check that sells one named item itself: pay, put the item in the pouch, mark the shelf sold.
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from formats import zstd, evfl  # noqa: E402
from formats.evfl import Params  # noqa: E402

FLOWS = ('Event', 'EventFlow')


def system_actor_params():
    """the parameters the game gives its system actors (GameDataActor, PouchSystemActor...) in every flow"""
    return Params(EventMemberCreateMethod=0, IsBindNearestActor=False, IsGrounding=False, IsWorld=False,
                  UseEventModelAnime='使用しない', UseEventAS='使用しない')


def system_actor(fc, name):
    """index of a system actor, added when the flowchart doesn't have it"""
    try:
        return fc.actor_index((name, ''))
    except KeyError:
        return fc.add_actor(name, params=system_actor_params())


# ============================================================================ worked examples
def example_item_get(fc, item, next=None, count=1):
    """Give `item` with its get window, the way `Dm_Kokiri_0155` gives the Fairy Ocarina. Two steps:

      1. action  PouchSystemActor.EventTriggerAddOrRemovePouchContent
                 {Num, IsEquipDIrect: False, IsSetMessageTargetActorName: True, Actor: item, IsGetEvent: False}
                 puts the item in the pouch and remembers its name for the window
      2. subflow GetPouchContent <DisplayGetByActorName> {ActorName: item}
                 (= PouchSystemActor.EventTriggerSetForGetWindow {Actor}, then <OpenGetWindow>, which closes
                 any open dialog, picks the window by kind of item and shows it)

    One step does the same and more, as chests and pick-ups do: subflow GetPouchContent
    <GetPouchContentByActorName> {ActorName: item} (window, rupee counter, add to the pouch, autosave).
    Returns the index of the first step; the last goes to `next`."""
    show = fc.add_subflow('GetPouchContent', 'DisplayGetByActorName', Params(ActorName=item), next=next)
    return fc.add_action(system_actor(fc, 'PouchSystemActor'), 'EventTriggerAddOrRemovePouchContent',
                         Params(Num=count, IsEquipDIrect=False, IsSetMessageTargetActorName=True, Actor=item,
                                IsGetEvent=False), next=show)


SHOP_SELECTED = 'Shop_SelectItemName'           # game data: the name of the item selected on the shelves
SHOP_CHECK = 'SelectItem_CheckAvailable'        # DisplayShop's entry point holding the game's buy check


def example_shop_bottle(flow, selected, item, price):
    """`DisplayShop`: sell the shelf item `selected` without the game's buy code (which refuses a new bottle).

    The flow's `NormalFlow` runs when an item is chosen: sold out? -> callswitch <SelectItem_CheckAvailable>
    (sorts the item by kind, asks `EventQueryCheckBuyResult`: the buy check) -> "buy it?" talk -> pay -> get.
    The new branch goes in front of that callswitch:

      is Shop_SelectItemName == `selected`?            (GameDataActor.EventQueryIsGameDataString64)
        no  -> the game's callswitch, as before
        yes -> has Link `price` rupees?                (PouchSystemActor.EventQueryHasRuppe)
          no  -> the game's callswitch (it refuses, with the shopkeeper's usual lines)
          yes -> pay                                   (Npc_EventStarter.EventTriggerPayItemPriceAtShop)
                 give `item` with its get window       (example_item_get)
                 count the shelf as sold               (Npc_EventStarter.EventTriggerAddShopItemSoldNum)
                 tell the count board, wait a frame, refresh the shelf
                                                       (...SendMessageToShopBoard, EventWait, ...VisibleItemAtShop:
                                                        what the game does after a "sold out" buy)
                 back to the shelves                   (subflow <Buy_ReturnStart_NoDofReset>)

    Every existing step keeps its index; the new ones are at the end. Returns (the new events' indexes by
    role, how many links were moved).
    Not known yet (to find in game): whether Shop_SelectItemName holds the shelf's name or the name of the
    item that goes into the pouch (the game compares it with 'Weapon_Shield_Deku', whose shelf is
    'Shop_Weapon_Shield_Deku'), and whether the price talk is wanted first."""
    fc = flow.flowchart
    calls = [i for i, e in enumerate(fc.events)
             if e.type == 'callswitch' and e.entry == SHOP_CHECK and not e.flowchart]
    backs = [e for e in fc.events if e.type == 'subflow' and e.entry == 'Buy_ReturnStart_NoDofReset'
             and not e.flowchart]
    if len(calls) != 1 or not backs:
        raise ValueError('DisplayShop is not as expected: %d calls of %s' % (len(calls), SHOP_CHECK))
    check = calls[0]
    shop = fc.actor_index('Npc_EventStarter')
    for name in ('EventTriggerPayItemPriceAtShop', 'EventTriggerAddShopItemSoldNum',
                 'EventTriggerSendMessageToShopBoard', 'EventTriggerVisibleItemAtShop'):
        fc.action_index(shop, name)                     # the game's own; KeyError if one is gone
    n = {}
    # built from the last step back, so each step knows its `next`
    n['back'] = fc.add_subflow('', 'Buy_ReturnStart_NoDofReset', copy.deepcopy(backs[0].params))
    n['shelf'] = fc.add_action(shop, 'EventTriggerVisibleItemAtShop', next=n['back'])
    n['wait'] = fc.add_action(('EventSystemActor', ''), 'EventWait', Params(IsWaitEnd=True, Frames=1),
                              next=n['shelf'])
    n['board'] = fc.add_action(shop, 'EventTriggerSendMessageToShopBoard', next=n['wait'])
    n['sold'] = fc.add_action(shop, 'EventTriggerAddShopItemSoldNum', next=n['board'])
    n['give'] = example_item_get(fc, item, next=n['sold'])
    n['show'] = fc.events[n['give']].next
    n['pay'] = fc.add_action(shop, 'EventTriggerPayItemPriceAtShop', next=n['give'])
    n['rupees'] = fc.add_switch('PouchSystemActor', 'EventQueryHasRuppe', [(0, check), (1, n['pay'])],
                                Params(Value=price))
    n['is_item'] = fc.add_switch('GameDataActor', 'EventQueryIsGameDataString64',
                                 [(0, check), (1, n['rupees'])],
                                 Params(GameDataName=SHOP_SELECTED, Index=-1, Value=selected))
    # what pointed at the game's callswitch now points at the new first step (not the two new "no" cases)
    links = fc.repoint(check, n['is_item'], keep=(n['is_item'], n['rupees']))
    return n, links


# ============================================================================ the test
def check(name, ok, detail=''):
    print('%-66s %s%s' % (name, 'OK' if ok else 'FAILED', (' (%s)' % detail) if detail and not ok else ''))
    return ok


def add_everything(flow):
    """adds one event of every type, a new actor, a new action and a new query to the first flowchart, and
    links them in front of the first entry point. Returns what the new parts must read back as."""
    fc = flow.flowchart
    ne, na = len(fc.events), len(fc.actors)
    want = {'events': ne + 9, 'actors': na + 1, 'entry_points': len(fc.entry_points) + 2}
    actor = fc.add_actor('NX2_TestActor', 'second', params=system_actor_params())
    old = fc.actors[0] if na else None
    host = 0 if na else actor                           # new action and query on an existing actor when there is one
    ret_yes = fc.add_return('Yes', name='NX2_ReturnYes')
    ret_no = fc.add_return(0x12345678, name='NX2_ReturnNo')
    sw = fc.add_switch(host, 'EventQueryNX2Test', [(0, ret_yes), (1, ret_no), (7, ret_no)],
                       Params(GameDataName='NX2_Flag', Index=-1, Ratio=0.1, Names=evfl.StrArray(['a', 'bb']),
                              Arg=evfl.Argument('ActorName')), name='NX2_Switch')
    start = fc.entry_points[0].main if fc.entry_points else None
    call = fc.add_callswitch('', 'NX2_Sub', [('Yes', start if start is not None else ret_yes), (0x12345678, ret_no)],
                             Params(ASName=evfl.Argument('ASName')), name='NX2_Call')
    join = fc.add_join(next=call, name='NX2_Join')
    sub = fc.add_subflow('GetPouchContent', 'DisplayGetByActorName', Params(ActorName='Item_Bottle'),
                         name='NX2_Subflow')
    act2 = fc.add_action(actor, 'EventNX2Second', name='NX2_Action2')
    act = fc.add_action(host, 'EventNX2Test', Params(IsWaitEnd=True, Frames=3), next=act2, name='NX2_Action')
    fork = fc.add_fork([act, sub], join, name='NX2_Fork')
    # everything that started at the first entry point's start now starts at the fork (not the new callswitch)
    links = fc.repoint(start, fork, keep=(call,)) if start is not None else 0
    fc.add_entry_point('NX2_Sub', sw)
    fc.add_entry_point('NX2_Empty', None)
    want.update(links=links, start=start, old_actor=old, host=host, actor=actor, ids=dict(
        ret_yes=ret_yes, ret_no=ret_no, sw=sw, call=call, join=join, sub=sub, act2=act2, act=act, fork=fork))
    return want


def read_back_as_meant(orig, back, want):
    """compares the file read back with the original plus what add_everything meant to add; returns the
    list of what is wrong (empty = right). Written out by hand, apart from evfl.differences."""
    bad = []
    fo, fb = orig.flowchart, back.flowchart
    ne, na = len(fo.events), len(fo.actors)
    ids = want['ids']
    if (len(fb.events), len(fb.actors), len(fb.entry_points)) != (want['events'], want['actors'],
                                                                 want['entry_points']):
        return ['counts: %d events, %d actors, %d entry points' % (len(fb.events), len(fb.actors),
                                                                  len(fb.entry_points))]
    start, fork = want['start'], ids['fork']
    sw = lambda v: fork if (v == start and start is not None) else v
    moved = 0
    for i in range(ne):                                 # old events: the same, links to the old start moved
        o, b = vars(fo.events[i]), vars(fb.events[i])
        exp = dict(o, next=sw(o['next']), join=sw(o['join']), forks=[sw(f) for f in o['forks']],
                   cases=[(v, sw(e)) for v, e in o['cases']])
        moved += sum(1 for k in ('next', 'join') if exp[k] != o[k])
        moved += sum(1 for x, y in zip(exp['forks'], o['forks']) if x != y)
        moved += sum(1 for x, y in zip(exp['cases'], o['cases']) if x != y)
        if b != exp:
            bad.append('old event %d' % i)
    for i in range(na):                                 # old actors: the same, the first has two names more
        o, b = vars(fo.actors[i]), vars(fb.actors[i])
        exp = dict(o)
        if i == want['host']:
            exp = dict(o, actions=o['actions'] + ['EventNX2Test'], queries=o['queries'] + ['EventQueryNX2Test'])
        if b != exp:
            bad.append('old actor %d' % i)
    a = fb.actors[want['actor']]
    host = fb.actors[want['host']]
    extra = ['EventNX2Test'] if want['host'] == want['actor'] else []
    if (a.name, a.secondary, a.argument, a.entry_point, a.cut) != ('NX2_TestActor', 'second', '', None, 1) \
            or a.actions != ['EventNX2Second'] + extra or a.params != system_actor_params() \
            or [type(v) for v in a.params.values()] != [int, bool, bool, bool, str, str]:
        bad.append('new actor')
    E = fb.events

    def ev(key, **exp):
        e = E[ids[key]]
        for k, v in exp.items():
            if getattr(e, k) != v:
                bad.append('new %s: %s is %r, meant %r' % (key, k, getattr(e, k), v))

    ev('ret_yes', name='NX2_ReturnYes', type='return', value=0xB3A43630)
    ev('ret_no', name='NX2_ReturnNo', type='return', value=0x12345678)
    ev('sw', name='NX2_Switch', type='switch', actor=want['host'],
       query=host.queries.index('EventQueryNX2Test'),
       cases=[(0, ids['ret_yes']), (1, ids['ret_no']), (7, ids['ret_no'])])
    p = E[ids['sw']].params
    if list(p) != ['GameDataName', 'Index', 'Ratio', 'Names', 'Arg'] or p['GameDataName'] != 'NX2_Flag' \
            or p['Index'] != -1 or abs(p['Ratio'] - 0.1) > 1e-7 or p['Names'] != ['a', 'bb'] \
            or p['Arg'] != 'ActorName' \
            or [type(v) for v in p.values()] != [str, int, float, evfl.StrArray, evfl.Argument]:
        bad.append('new switch parameters: %r' % (p,))
    ev('call', name='NX2_Call', type='callswitch', flowchart='', entry='NX2_Sub',
       cases=[(0xB3A43630, start if start is not None else ids['ret_yes']), (0x12345678, ids['ret_no'])],
       params={'ASName': 'ASName'})
    if type(E[ids['call']].params['ASName']) is not evfl.Argument:
        bad.append('new callswitch parameter type')
    ev('join', name='NX2_Join', type='join', next=ids['call'])
    ev('sub', name='NX2_Subflow', type='subflow', flowchart='GetPouchContent', entry='DisplayGetByActorName',
       next=None, params={'ActorName': 'Item_Bottle'})
    ev('act2', name='NX2_Action2', type='action', actor=want['actor'],
       action=a.actions.index('EventNX2Second'), params=None, next=None)
    ev('act', name='NX2_Action', type='action', actor=want['host'], action=host.actions.index('EventNX2Test'),
       params={'IsWaitEnd': True, 'Frames': 3}, next=ids['act2'])
    if [type(v) for v in E[ids['act']].params.values()] != [bool, int]:
        bad.append('new action parameter types')
    ev('fork', name='NX2_Fork', type='fork', forks=[ids['act'], ids['sub']], join=ids['join'])
    # entry points: old ones the same name; those starting at the old start now start at the fork and list
    # the new subflow and callswitch; the two new ones
    for i, (o, b) in enumerate(zip(fo.entry_points, fb.entry_points)):
        main = sw(o.main)
        moved += main != o.main
        reach = [k for k in fb.reachable(main) if E[k].type in ('subflow', 'callswitch')]
        if b.name != o.name or b.main != main or sorted(b.subflows) != sorted(reach) \
                or [k for k in b.subflows if k < ne] != [k for k in o.subflows if k in reach]:
            bad.append('old entry point %d' % i)
        if main == fork and not {ids['sub'], ids['call']} <= set(b.subflows):
            bad.append('entry point %d does not list the new subflows' % i)
    x, y = fb.entry_points[-2], fb.entry_points[-1]
    if (x.name, x.main, x.subflows) != ('NX2_Sub', ids['sw'], []) or (y.name, y.main, y.subflows) != (
            'NX2_Empty', None, []):
        bad.append('new entry points')
    if moved != want['links']:
        bad.append('repoint said %d links, %d moved' % (want['links'], moved))
    return bad


def refused(make):
    try:
        make()
    except (ValueError, KeyError, IndexError):
        return True
    return False


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    folder = os.path.join(romfs, *FLOWS)
    rd = lambda name: zstd.decompress(open(os.path.join(folder, name + '.bfevfl.zs'), 'rb').read(), d)
    good = True

    # ---- 1. every flow
    names = sorted(n[:-len('.bfevfl.zs')] for n in os.listdir(folder) if n.endswith('.bfevfl.zs'))
    read = same = lists = added = 0
    problems = []
    for name in names:
        raw = rd(name)
        try:
            flow = evfl.loads(raw)
        except ValueError:
            continue                                    # timelines / entry point variables: refused on purpose
        read += 1
        try:
            before = [list(ep.subflows) for fc in flow.flowcharts for ep in fc.entry_points]
            for fc in flow.flowcharts:
                fc.update_entry_points()
            lists += before == [list(ep.subflows) for fc in flow.flowcharts for ep in fc.entry_points]
            same += evfl.dumps_checked(flow) == raw
        except ValueError as e:
            problems.append('%s unchanged: %s' % (name, e))
        if not flow.flowcharts:
            continue
        try:
            want = add_everything(flow)
            out = evfl.dumps_checked(flow)
            bad = read_back_as_meant(evfl.loads(raw), evfl.loads(out), want)
            if bad:
                problems.append('%s: %s' % (name, '; '.join(bad[:4])))
            else:
                added += 1
        except Exception as e:                          # noqa: BLE001  (a test: report, go on)
            problems.append('%s: %s: %s' % (name, type(e).__name__, e))
    with_fc = sum(1 for name in names if _has_flowchart(rd, name))
    for p in problems[:15]:
        print('   ' + p)
    good &= check('%d of %d event flows read' % (read, len(names)), read >= 650)
    good &= check('unchanged: entry point lists are what we work out (%d/%d)' % (lists, read), lists == read)
    good &= check('unchanged: dumps_checked gives the game\'s bytes (%d/%d)' % (same, read), same == read)
    good &= check('added to and read back as meant (%d/%d with a flowchart)' % (added, with_fc), added == with_fc)

    # ---- 2. mistakes are refused
    def fresh():
        return evfl.loads(rd('GetPouchContent'))

    def broken(change):
        f = fresh()
        change(f.flowchart)
        return lambda: evfl.dumps_checked(f)

    tests = [
        ('an event name used twice', lambda: fresh().flowchart.add_return('Yes', name='Event0')),
        ('an actor used twice', lambda: fresh().flowchart.add_actor('PouchSystemActor')),
        ('an entry point name used twice', lambda: fresh().flowchart.add_entry_point('GetPouchContent', 0)),
        ('an actor that is not there', lambda: fresh().flowchart.add_action('NoSuchActor', 'EventWait')),
        ('a link to an event that is not there', broken(lambda fc: fc.add_join(next=len(fc.events) + 5))),
        ('a case without an event', broken(lambda fc: fc.add_switch(0, 'EventQueryX', [(0, None)]))),
        ('a fork whose join is not a join', broken(lambda fc: fc.add_fork([0], 0))),
        ('an action number the actor does not have',
         broken(lambda fc: fc.add_event(evfl.Event('X', 'action', actor=0, action=99)))),
        ('a parameter the file cannot hold', broken(lambda fc: fc.add_action(0, 'EventX', Params(V=2 ** 40)))),
        ('parameters that are a plain dict', broken(lambda fc: fc.add_action(0, 'EventX', {'V': 1}))),
        ('an entry point list left out of date',
         lambda: _stale(fresh())),
    ]
    for what, make in tests:
        good &= check('refused: ' + what, refused(make))

    # ---- 3. worked examples
    good &= item_get_test(rd)
    good &= shop_bottle_test(rd)
    return 0 if good else 1


def _has_flowchart(rd, name):
    try:
        return bool(evfl.loads(rd(name)).flowcharts)
    except ValueError:
        return False


def _stale(flow):
    """a new subflow event reached from an entry point whose list wasn't brought up to date"""
    fc = flow.flowchart
    ep = fc.entry_points[0]
    ep.main = fc.add_subflow('', fc.entry_points[1].name, next=ep.main)
    out = evfl.dumps_checked(flow, update_entry_points=False)
    back = evfl.loads(out).flowchart
    if back.entry_points[0].subflows != back._subflows_from(back.entry_points[0].main):
        raise ValueError('entry point list out of date')
    return out


def item_get_test(rd):
    """the item get steps in front of the child shopkeeper's talk (a flow without a PouchSystemActor)"""
    raw = rd('Npc_Kokiri_001_Shop_Child')
    flow, orig = evfl.loads(raw), evfl.loads(raw)
    fc = flow.flowchart
    had = any(a.name == 'PouchSystemActor' for a in fc.actors)
    ep = fc.entry_points[0]
    start = ep.main
    first = example_item_get(fc, 'Item_Bottle', next=start)
    ep.main = first
    back = evfl.loads(evfl.dumps_checked(flow)).flowchart
    ne, na = len(orig.flowchart.events), len(orig.flowchart.actors)
    give, show = back.events[first], back.events[first - 1]
    pouch = back.actors[give.actor]
    ok = (len(back.events) == ne + 2 and len(back.actors) == na + (0 if had else 1)
          and all(vars(a) == vars(b) for a, b in zip(orig.flowchart.events, back.events))
          and all(vars(a) == vars(b) for a, b in zip(orig.flowchart.actors[:na - had], back.actors))
          and pouch.name == 'PouchSystemActor' and pouch.actions[give.action] == 'EventTriggerAddOrRemovePouchContent'
          and (had or pouch.params == system_actor_params())
          and give.type == 'action' and give.next == first - 1
          and list(give.params.items()) == [('Num', 1), ('IsEquipDIrect', False),
                                            ('IsSetMessageTargetActorName', True), ('Actor', 'Item_Bottle'),
                                            ('IsGetEvent', False)]
          and (show.type, show.flowchart, show.entry, show.next) == ('subflow', 'GetPouchContent',
                                                                     'DisplayGetByActorName', start)
          and show.params == {'ActorName': 'Item_Bottle'}
          and back.entry_points[0].main == first and first - 1 in back.entry_points[0].subflows
          and [e.main for e in back.entry_points[1:]] == [e.main for e in orig.flowchart.entry_points[1:]])
    return check('example: item get steps (pouch + get window) read back', ok)


def shop_bottle_test(rd):
    raw = rd('DisplayShop')
    flow, orig = evfl.loads(raw), evfl.loads(raw)
    selected, item, price = 'Shop_NX2_Bottle_5_Once', 'Item_Bottle', 5
    n, links = example_shop_bottle(flow, selected, item, price)
    out = evfl.dumps_checked(flow)
    fo, fb = orig.flowchart, evfl.loads(out).flowchart
    ne = len(fo.events)
    check_i = next(i for i, e in enumerate(fo.events) if e.type == 'callswitch' and e.entry == SHOP_CHECK)
    good = True
    # old events: the same, but the links to the buy check's callswitch go to the new first step
    moved = [i for i in range(ne) if check_i in fo.links(i)]
    same = True
    for i in range(ne):
        o, b = vars(fo.events[i]), vars(fb.events[i])
        exp = dict(o, next=n['is_item'] if o['next'] == check_i else o['next'],
                   cases=[(v, n['is_item'] if e == check_i else e) for v, e in o['cases']],
                   forks=[n['is_item'] if f == check_i else f for f in o['forks']])
        same &= b == exp
    good &= check('shop bottle: %d old events unchanged, %d link(s) to the buy check moved' % (ne, links),
                  same and len(fb.events) == ne + 10 and links == len(moved) >= 1
                  and all(n['is_item'] in fb.links(i) and check_i not in fb.links(i) for i in moved))
    # actors: none added; PouchSystemActor has one action more; nothing else changed
    acts = True
    for a, b in zip(fo.actors, fb.actors):
        exp = dict(vars(a))
        if a.name == 'PouchSystemActor':
            exp['actions'] = a.actions + ['EventTriggerAddOrRemovePouchContent']
        acts &= vars(b) == exp
    good &= check('shop bottle: actors unchanged, one new action on PouchSystemActor',
                  acts and len(fb.actors) == len(fo.actors))
    # the new steps, one by one
    E, A = fb.events, fb.actors

    def is_action(key, actor, action, nxt, params=None):
        e = E[n[key]]
        return (e.type == 'action' and A[e.actor].name == actor and A[e.actor].actions[e.action] == action
                and e.next == n.get(nxt) and e.params == params
                and (A[e.actor].secondary or '') == '')

    def is_switch(key, actor, query, cases, params):
        e = E[n[key]]
        return (e.type == 'switch' and A[e.actor].name == actor and A[e.actor].queries[e.query] == query
                and e.cases == cases and list(e.params.items()) == params)

    back = E[n['back']]
    old_back = next(e for e in fo.events if e.type == 'subflow' and e.entry == 'Buy_ReturnStart_NoDofReset')
    steps = (
        is_switch('is_item', 'GameDataActor', 'EventQueryIsGameDataString64', [(0, check_i), (1, n['rupees'])],
                  [('GameDataName', SHOP_SELECTED), ('Index', -1), ('Value', selected)])
        and is_switch('rupees', 'PouchSystemActor', 'EventQueryHasRuppe', [(0, check_i), (1, n['pay'])],
                      [('Value', price)])
        and is_action('pay', 'Npc_EventStarter', 'EventTriggerPayItemPriceAtShop', 'give')
        and is_action('give', 'PouchSystemActor', 'EventTriggerAddOrRemovePouchContent', 'show',
                      {'Num': 1, 'IsEquipDIrect': False, 'IsSetMessageTargetActorName': True, 'Actor': item,
                       'IsGetEvent': False})
        and (E[n['show']].type, E[n['show']].flowchart, E[n['show']].entry, E[n['show']].next,
             E[n['show']].params) == ('subflow', 'GetPouchContent', 'DisplayGetByActorName', n['sold'],
                                      {'ActorName': item})
        and is_action('sold', 'Npc_EventStarter', 'EventTriggerAddShopItemSoldNum', 'board')
        and is_action('board', 'Npc_EventStarter', 'EventTriggerSendMessageToShopBoard', 'wait')
        and is_action('wait', 'EventSystemActor', 'EventWait', 'shelf', {'IsWaitEnd': True, 'Frames': 1})
        and is_action('shelf', 'Npc_EventStarter', 'EventTriggerVisibleItemAtShop', 'back')
        and (back.type, back.flowchart, back.entry, back.next) == ('subflow', '', 'Buy_ReturnStart_NoDofReset',
                                                                   None)
        and evfl._norm(back.params) == evfl._norm(old_back.params)
        and len({e.name for e in E}) == len(E))
    good &= check('shop bottle: the 10 new steps read back as meant', steps)
    # entry points: same names and starts; the ones that reach the branch list its two subflow events
    eps = True
    reach_new = 0
    for o, b in zip(fo.entry_points, fb.entry_points):
        was_reaching = check_i in fo.reachable(o.main)
        exp = list(o.subflows) + ([n['back'], n['show']] if was_reaching else [])
        reach_new += was_reaching
        eps &= b.name == o.name and b.main == o.main and sorted(b.subflows) == sorted(exp) \
            and b.subflows[:len(o.subflows)] == o.subflows
    good &= check('shop bottle: entry points unchanged, %d list the new subflow steps' % reach_new,
                  eps and reach_new >= 1 and len(fb.entry_points) == len(fo.entry_points))
    # walking the new branch from the shop's NormalFlow reaches every new step, in order
    path = [n[k] for k in ('is_item', 'rupees', 'pay', 'give', 'show', 'sold', 'board', 'wait', 'shelf', 'back')]
    walk = fb.reachable(fb.entry_point('NormalFlow').main)
    good &= check('shop bottle: NormalFlow reaches the branch and still the game\'s buy check',
                  all(i in walk for i in path + [check_i])
                  and all(E[a].next == b for a, b in zip(path[2:], path[3:])))
    return good


if __name__ == '__main__':
    if len(sys.argv) < 2:
        p = os.path.join(os.path.dirname(HERE), 'romfs_path.txt')
        if os.path.exists(p):
            sys.argv.append(open(p).read().strip())
    sys.exit(main(sys.argv[1]))
