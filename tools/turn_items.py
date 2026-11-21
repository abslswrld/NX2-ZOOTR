"""Turning items: progressive items that lie on the ground (to test in game).

A ground item has no point where it decides what it gives: what goes into the inventory, the model on the
ground and the model Link holds up all come from the one actor that is picked up (its item settings, its
model). So an item on the ground can only be "the right level" if the actor lying there is that level's.

Found in the game's files (2026-11-19, out/RESEARCH_ground_progressive.md):
- a ground item has an AI of its own that runs while it lies there (`DropItem.root`: spin, bounce, a physics
  layer change while carried; nothing about the inventory), named in its own parameter files (`AIInfoRef`), so a
  copy with another name can take its place, as the shop versions' `Shop_NX2_Once`;
- an object's AI can ask the inventory every frame: `QueryGetPouchContentNumByActorName` with a fixed name feeds
  a selector "when 0 / otherwise" in a root that always runs (`Enemy_Tentacle_Red.utility.root`, asking for
  `Item_Boomerang`). It is the question the checking chest asks (tools/build_mod.py, CHECKING_CHEST);
- an actor can turn into another through a drop table of its own: `Animal_ButterflyToFairy` (drop part
  `DropRef` -> `Component/DropParam` -> `Drop/DropTable` -> `Drop/DropSubTable`, one item: the fairy);
- an AI can drop without dying (`OneShotDropDrop`: trees, `Obj_Gerudo_CowBoneDecoration_A_01`), switch its drop
  on or off (`OneShotDropSetDropValid`: chests, `TreasureBox.event.root`) and remove its actor without
  marking its placement (`OneShotGenericDeleteThisActor`, `IsFade` false: `Obj_silverRupeeCounter.root`);
- the pick-up scene ends the item with death reason 10 (`Dm_SY_Get`: `EventTriggerRequestDeath`), which is
  `LifeDepleted` in the code's list, and the ground items' death table drops on that reason (`IsDropItem`): an
  item with a drop part would drop when picked up, so its drop is switched off as soon as it is made;
- "am I dead" (`QueryDeathIsDead`: `Obj_Heart_Piece.root`...), "am I in an event"
  (`QueryEventMemberIsEventMemberSomeReason`: `Item_Bottle_Letter.root`, an item with the same event settings,
  and the chests) and "is a main event playing" (`QueryIsPlayingMainEvent`: `Obj_Spirit_Poe.root` keeps a Poe
  soul from ending itself while one plays) are asked by the game's own item AIs.

A turning item is one actor per level of a family, `Obj_NX2P_<level without "Item_">`: the ordinary ground
version of that level (tools/ground_items.py) with a root AI of its own, `NX2_Turn_<level>.root`: a copy of
`DropItem.root` (its 13 nodes unchanged, same numbers) with one more branch under its root:

    on entering (levels with a next level): switch the drop off
    every frame:
      dead?                    -> nothing
      in an event?             -> nothing
      a main event playing?    -> nothing
      its pick-up asked for?   -> Link owns this level (levels with a next level)? -> switch the drop on
                                  otherwise nothing
      Link owns this level?    -> switch the drop on, drop the next level, delete itself (one step)
                                  (last level: only delete itself)
      Link owns a later level? -> delete itself

While Link doesn't own the level, it is a normal ground item of that level. Every check of the family gets the
first level's actor: an item can only be picked up while Link doesn't own it (no level twice), and a level
only ever comes from the level before it once that one is owned (none skipped). Nothing is remembered and
nothing of the game is changed.

The last line is for a family whose later level takes the earlier one's place in the inventory (the hookshots
share one slot): without it the first level would lie there again once the second is owned.

The three guards keep the item from turning while it is itself being picked up: between the moment it is added
to the inventory and its death it still exists, and Link owns it. Each is a copy of a game node; which of them
holds through the whole scene can only be seen in game, so all three are asked.

The fourth question, "is my pick-up being asked for" (`QueryPouchContentIsRequestingGetEvent`), is for the time
before that scene begins: Link has touched the item, the scene is asked for but not yet playing, so none of the
three guards holds yet. An item made by a drop right where Link stands (a bush cut with the sword) can be
touched in the few frames before it has turned; turning then would delete an item whose scene is on its way,
and Link is left waiting for it (seen 2026-11-20: stuck in place after a bush's Longshot, camera and menu
working). The game's only item that ends itself asks this in front of everything else: the Poe soul
(`Obj_Spirit_Poe.root`, the selector at its root: asked for -> nothing). Here the item stays, the scene plays
(Link holds up the level he already has), and so that the next level is not lost the drop is switched on: the
scene ends the item with the death the ground items drop on (reason 10, see above), which then drops the next
level. An item touched while Link doesn't own it (the normal case) does nothing here.

Every new node is a copy of a game node of the same type, found by what it is (not by its number) and checked
before it is used; new nodes go after the file's own.
"""
import copy
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml, ainb  # noqa: E402
import ground_items  # noqa: E402
from ground_items import pack_path, ap_path, _ref_path, _refs, resolved_components  # noqa: E402
from shop_items import ai_path, ai_info_path, _node_state, _doc_state  # noqa: E402

VERSION = 'turn'                                  # the kind of version in ground_items.VERSIONS
PREFIX = ground_items.VERSIONS[VERSION][2]        # Obj_NX2P_
AI_PREFIX = 'NX2_Turn_'
BASE_AI = 'DropItem'                              # the AI of every ground item
BASE_NODES = 13                                   # its nodes: kept as they are, with their numbers
AI_PACK = 'Pack/AI.Global.Product.111.pack'
# where each new node is copied from: files of the shared AI pack, and one actor's own AI
SOURCES = {
    'owned': 'AI/Enemy_Tentacle_Red.utility.root.ainb',     # QueryGetPouchContentNumByActorName, QueryDeathIsDead
    'event': 'AI/Obj_TBox_A_01.root.ainb',                  # QueryEventMemberIsEventMemberSomeReason
    'door': 'AI/Door.root.ainb',                            # QueryIsPlayingMainEvent, Element_SplitTiming
    'counter': 'AI/Obj_silverRupeeCounter.root.ainb',       # Element_S32Selector, Element_Sequential, the delete
    'chest': 'AI/TreasureBox.event.root.ainb',              # OneShotDropSetDropValid
}
DROP_ACTOR = 'Obj_Gerudo_CowBoneDecoration_A_01'            # OneShotDropDrop: its own AI, in its pack
DROP_AI = 'AI/Obj_Gerudo_CowBoneDecoration_A_01.root.ainb'
REQUEST_ACTOR = 'Obj_Spirit_Poe'                            # QueryPouchContentIsRequestingGetEvent: its own AI
REQUEST_AI = 'AI/Obj_Spirit_Poe.root.ainb'
# the actor whose drop part is copied: it turns into another actor through a drop table of its own
DROP_TEMPLATE = 'Animal_ButterflyToFairy'
DROP_SHARED = ('Component/DropParam/Default.game__component__DropParam.bgyml',
               'Component/Blackboard/BlackboardParamTable/Drop.engine__component__BlackboardParamTable.bgyml')
# memory: what the drop part and the bigger AI may take on top of the ground version. The game's own number:
# Animal_ButterflyToFairy's InstanceHeapSize over Animal_Butterfly's (the same actor plus a drop part, an actor
# holder and more AI), read from the table at build time; this is only the least accepted
HEAP_ACTORS = ('Animal_ButterflyToFairy', 'Animal_Butterfly')
HEAP_LEAST = 16384

S32_SELECTOR, SEQUENTIAL, SIMULTANEOUS, BOOL_SELECTOR, SPLIT_TIMING = 1, 2, 3, 7, 500
VALUE, FLOW, INT = 0, 2, 5                        # link types (formats/ainb.py)
Q_OWNED, Q_DEAD = 'QueryGetPouchContentNumByActorName', 'QueryDeathIsDead'
Q_EVENT, Q_MAIN = 'QueryEventMemberIsEventMemberSomeReason', 'QueryIsPlayingMainEvent'
Q_ASKED = 'QueryPouchContentIsRequestingGetEvent'  # the item's own pick-up scene is asked for
N_VALID, N_DROP, N_DELETE, N_IDLE = ('OneShotDropSetDropValid', 'OneShotDropDrop',
                                     'OneShotGenericDeleteThisActor', 'OneshotDoNothing')
GUARDS = ((Q_DEAD, 'IsDead'), (Q_EVENT, 'IsEventMember'), (Q_MAIN, 'IsPlayingMainEvent'))


def turn_name(item):
    return ground_items.ground_name(item, VERSION)


def ai_name(item):
    return AI_PREFIX + (item[5:] if item.startswith('Item_') else item)


def drop_param_path(actor):
    return 'Component/DropParam/%s.game__component__DropParam.bgyml' % actor


def drop_table_path(actor):
    return 'Drop/DropTable/%s.game__drop__DropTable.bgyml' % actor


def drop_sub_path(actor):
    return 'Drop/DropSubTable/%s.game__drop__DropSubTable.bgyml' % actor


def _work(path):
    """'Actor/X.bgyml' -> 'Work/Actor/X.gyml' (how parameter files name each other)"""
    return 'Work/' + path[:-len('.bgyml')] + '.gyml'


def _plain(n):
    """a node with nothing hung on it"""
    return not n.attachments and not n.exb_count and not n.exb_size


def _params(n, kind):
    return [(t, x.name, x.value) for t in ainb.PARAM_TYPES for x in getattr(n, kind)[t]]


def _find(doc, what, ok):
    hits = [n for n in doc.nodes if ok(n)]
    if not hits:
        raise SystemExit('%s: no %s found as expected (game files differ from what this was made for)'
                         % (doc.filename, what))
    return hits[0]


def _query(doc, name, out_type, out_name):
    """a query node with nothing linked, whose one used output is `out_name` (and its place among the outputs
    of that type)"""
    def ok(n):
        used = [(t, x.name) for t in ainb.PARAM_TYPES for x in n.outputs[t] if x.flag]
        return (n.name == name and n.type == 0 and n.flags == 1 and _plain(n) and not any(n.links)
                and not n.preconditions and used == [(out_type, out_name)]
                and _params(n, 'immediates') == [('bool', 'OutputOnlyOnEnter', False)]
                and all(x.node < 0 and x.sources is None for t in ainb.PARAM_TYPES for x in n.inputs[t]))
    n = _find(doc, name, ok)
    return n, [x.name for x in n.outputs[out_type]].index(out_name)


def _action(doc, name, immediates, inputs=()):
    """an action node with nothing linked and exactly these fixed values"""
    return _find(doc, name, lambda n: (
        n.name == name and n.type == 0 and n.flags == 0 and _plain(n) and not any(n.links)
        and not n.preconditions and _params(n, 'immediates') == list(immediates)
        and _params(n, 'inputs') == list(inputs)
        and all(x.node < 0 and x.sources is None for t in ainb.PARAM_TYPES for x in n.inputs[t])
        and not any(n.outputs[t] for t in ainb.PARAM_TYPES)))


def _element(doc, type_, immediates, flow, other=()):
    """a built-in node (selector, sequence...) with these fixed values and child links (names and extra words),
    and no links of other kinds but `other` (link types)"""
    def ok(n):
        return (n.type == type_ and n.flags == 0 and not n.name_hash and _plain(n)
                and _params(n, 'immediates') == list(immediates)
                and [(l.name, l.extra) for l in n.links[FLOW]] == list(flow)
                and all(bool(links) == (t in other) for t, links in enumerate(n.links) if t != FLOW)
                and not any(n.outputs[t] for t in ainb.PARAM_TYPES))
    return _find(doc, ainb.NODE_TYPES[type_], ok)


def turning_ai(base, sources, drop_ai, request_ai, own, later=(), drops=False, name=None):
    """the ground items' AI (`base`: DropItem.root) under the name `name`, with the turning branch (see the top
    of this file). own: the level's own name, as the inventory knows it; later: the names of the levels after
    it; drops: whether it drops the next level when it turns (it has a drop part) or only deletes itself.
    sources: {key of SOURCES: that AI file}; drop_ai: the AI the drop node is copied from; request_ai: the AI
    the "pick-up asked for" question is copied from.
    Read back: the 13 nodes of the game's file are as they were but for the root's one new child."""
    doc = ainb.loads(base)
    if doc.filename != BASE_AI + '.root':
        raise SystemExit('%s: not the ground items\' AI expected (%s)' % (ai_path(BASE_AI), doc.filename))
    src = {k: ainb.loads(d) for k, d in sources.items()}
    n0 = len(doc.nodes)
    if n0 != BASE_NODES:
        raise SystemExit('%s: %d nodes, expected %d' % (ai_path(BASE_AI), n0, BASE_NODES))
    roots = [c.left for c in doc.commands]
    if len(roots) != 1 or doc.commands[0].name != 'Root':
        raise SystemExit('%s: one entry point "Root" expected' % ai_path(BASE_AI))
    root = doc.nodes[roots[0]]
    if root.type != SIMULTANEOUS or any(l.name or l.extra for l in root.links[FLOW]) \
            or any(links for t, links in enumerate(root.links) if t != FLOW) or len(root.links[FLOW]) != 3:
        raise SystemExit('%s: its root is not the "all at once" of three children expected' % ai_path(BASE_AI))
    if doc.exb or doc.attachments or doc.resident or doc.modules or any(doc.globals[t] for t in ainb.GLOBAL_TYPES):
        raise SystemExit('%s: more in the file than nodes (expressions, attachments...): not expected'
                         % ai_path(BASE_AI))

    # the templates
    sel_imm = [('int', 'CalculateTiming', 0), ('bool', 'ChildFrameSync', False), ('bool', 'InputValue', False),
               ('bool', 'IsNoSelectWhenChildBusy', False)]
    t_bool = _element(doc, BOOL_SELECTOR, sel_imm, [('True', ()), ('False', ())], other=(VALUE,))
    b_in = t_bool.inputs['bool']
    if len(b_in) != 1 or b_in[0].name != 'Input' or b_in[0].flags or b_in[0].node < 0 \
            or [(l.node, l.name, l.extra) for l in t_bool.links[VALUE]] != [(b_in[0].node, 'Input', (0, 0))] \
            or doc.nodes[b_in[0].node].flags != 1 or any(doc.nodes[b_in[0].node].links):
        raise SystemExit('%s: its yes/no selector is not as expected' % ai_path(BASE_AI))
    t_idle = _action(doc, N_IDLE, [('bool', 'ExecuteEveryFrame', False)])
    t_int = _element(src['counter'], S32_SELECTOR, [
        ('int', 'CalculateTiming', 0), ('int', 'InputValue', 0), ('bool', 'ChildFrameSync', False),
        ('bool', 'IsNoSelectIfSameInstance', False), ('bool', 'IsNoSelectWhenChildBusy', False)],
        [('', (0, 0)), ('', (0, 0))], other=(INT,))                     # "when 0", then "otherwise" (the last)
    i_in = t_int.inputs['int']
    if len(i_in) != 1 or i_in[0].name != 'Input' or i_in[0].flags or i_in[0].node < 0 \
            or [(l.node, l.name, l.extra) for l in t_int.links[INT]] != [(i_in[0].node, 'Input', (0, 0))] \
            or any(l.node == src['counter'].nodes.index(t_int)
                   for links in src['counter'].nodes[i_in[0].node].links for l in links):
        raise SystemExit('%s: its number selector is not as expected' % SOURCES['counter'])
    t_seq = _find(src['counter'], 'Element_Sequential (one step)', lambda n: (
        n.type == SEQUENTIAL and n.flags == 0 and _plain(n) and _params(n, 'immediates') == [
            ('int', 'BusyPolicy', 0), ('int', 'NumLoop', 0), ('int', 'PlayPolicy', 0), ('int', 'ResultPolicy', 0),
            ('bool', 'IsDelayJudge', False), ('bool', 'IsLoop', False), ('bool', 'IsUpdateNextInFrame', True)]
        and all(not l.name and not l.extra for l in n.links[FLOW]) and n.links[FLOW]
        and not any(links for t, links in enumerate(n.links) if t != FLOW)))
    t_split = _element(src['door'], SPLIT_TIMING, [('int', 'ChildStateSyncPolicy', 0)],
                       [('Enter', ()), ('Update', ()), ('Leave', ())])
    t_delete = _action(src['counter'], N_DELETE, [('bool', 'ExecuteEveryFrame', False), ('bool', 'IsFade', False)])
    t_valid = _action(src['chest'], N_VALID, [('bool', 'ExecuteEveryFrame', False)], [('bool', 'IsValid', False)])
    t_drop = _action(ainb.loads(drop_ai), N_DROP, [('bool', 'ExecuteEveryFrame', False)])
    # 0x800000: a value set in the file (the game's nodes have it with true and with false)
    if t_valid.inputs['bool'][0].flags != 0x800000:
        raise SystemExit('%s: its drop switch is not a fixed value as expected' % SOURCES['chest'])
    t_owned, p_owned = _query(src['owned'], Q_OWNED, 'int', 'Num')
    o_in = t_owned.inputs['string']
    if [(x.name, x.node, x.sources) for t in ainb.PARAM_TYPES for x in t_owned.inputs[t]] != [
            ('ActorName', -1, None)] or not o_in[0].value or o_in[0].flags >> 31:
        raise SystemExit('%s: its inventory question does not ask for a fixed name as expected' % SOURCES['owned'])
    t_guard = {Q_DEAD: _query(src['owned'], Q_DEAD, 'bool', 'IsDead'),
               Q_EVENT: _query(src['event'], Q_EVENT, 'bool', 'IsEventMember'),
               Q_MAIN: _query(src['door'], Q_MAIN, 'bool', 'IsPlayingMainEvent')}
    t_asked = _query(ainb.loads(request_ai), Q_ASKED, 'bool', 'IsRequestingGetEvent')

    nodes = []                                     # the new nodes, in order: node number n0 + its place

    def new(template, what):
        n = copy.deepcopy(template)
        n.guid = hashlib.md5(('NX2-ZOOTR %s %s' % (name, what)).encode()).digest()
        n.precondition_slot = None
        n.preconditions = []
        if any(bytes(x.guid) == n.guid for x in doc.nodes + nodes):
            raise SystemExit('%s: node id already used' % name)
        nodes.append(n)
        return n0 + len(nodes) - 1

    def idle(what):
        return new(t_idle, 'nothing ' + what)

    def ask(query, where, param_type):
        """point a selector's one input at a query node"""
        n = nodes[where - n0]
        x = n.inputs[param_type][0]
        x.node, x.param = query
        lt = VALUE if param_type == 'bool' else INT
        n.links[lt] = [ainb.Link(query[0], 'Input', (0, 0))]
        n.wants = query[0]                          # its precondition, numbered once every node is placed

    def flow(where, *children):
        n = nodes[where - n0]
        if len(n.links[FLOW]) != len(children):
            n.links[FLOW] = [copy.deepcopy(n.links[FLOW][0]) for _ in children]
        for l, c in zip(n.links[FLOW], children):
            l.node = c

    def owned(item, what):
        q = new(t_owned, 'owned ' + what)
        nodes[q - n0].inputs['string'][0].value = item
        sel = new(t_int, 'has ' + what)
        ask((q, p_owned), sel, 'int')
        return sel

    def delete(what):
        return new(t_delete, 'delete ' + what)

    # the question chain, from the last question back: a later level owned -> delete itself
    after = idle('owned')
    for k, item in reversed(list(enumerate(later))):
        sel = owned(item, 'later %d' % k)
        flow(sel, after, delete('later %d' % k))
        after = sel
    # this level owned -> turn
    if drops:
        on = new(t_valid, 'drop on')
        nodes[on - n0].inputs['bool'][0].value = True
        turn = new(t_seq, 'turn')
        flow(turn, on, new(t_drop, 'drop'), delete('turned'))
    else:
        turn = delete('owned')
    sel = owned(own, 'own')
    flow(sel, after, turn)
    # the item's own pick-up asked for, its scene not yet begun: no turning (see the top of this file). With a
    # next level and this one owned, the drop is switched on, for the death that ends the scene
    q = new(t_asked[0], 'guard IsRequestingGetEvent')
    asked = new(t_bool, 'is IsRequestingGetEvent')
    ask((q, t_asked[1]), asked, 'bool')
    if drops:
        keep = new(t_valid, 'drop on, asked for')
        nodes[keep - n0].inputs['bool'][0].value = True
        mine = owned(own, 'own, asked for')
        flow(mine, idle('asked for'), keep)
    else:
        mine = idle('asked for')
    flow(asked, mine, sel)                          # True -> stay, False -> go on
    # the guards, the first asked last made
    top = asked
    for q_name, out in reversed(GUARDS):
        q = new(t_guard[q_name][0], 'guard ' + out)
        g = new(t_bool, 'is ' + out)
        ask((q, t_guard[q_name][1]), g, 'bool')
        flow(g, idle(out), top)                     # True -> nothing, False -> go on
        top = g
    if drops:
        split = new(t_split, 'timing')
        flow(split, new(t_valid, 'drop off'), top, idle('leave'))
        top = split
    for n in nodes:                                 # preconditions: the place of the query among the query nodes
        if hasattr(n, 'wants'):
            n.preconditions = [sum(1 for x in (doc.nodes + nodes)[:n.wants] if x.flags & 1)]
            del n.wants
    doc.nodes += nodes
    root.links[FLOW].append(ainb.Link(top, '', ()))
    doc.filename = name + '.root'
    data = doc.write()

    # read back
    back, orig = ainb.loads(data), ainb.loads(base)
    if back.write() != data or back.filename != name + '.root' or len(back.nodes) != n0 + len(nodes) \
            or _doc_state(back) != _doc_state(orig):
        raise SystemExit('read-back: %s differs from what was intended' % ai_path(name))
    for i, (o, b) in enumerate(zip(orig.nodes, back.nodes)):
        if i == roots[0]:
            o.links[FLOW].append(ainb.Link(top, '', ()))
        if _node_state(o) != _node_state(b):
            raise SystemExit('read-back: node %d of %s differs from what was intended' % (i, ai_path(name)))
    for k, n in enumerate(nodes):
        if _node_state(back.nodes[n0 + k]) != _node_state(n):
            raise SystemExit('read-back: new node %d of %s differs from what was intended' % (n0 + k, ai_path(name)))
    want = describe(data)
    if want['own'] != own or want['later'] != list(later) or want['drops'] != drops \
            or want['guards'] != [q for q, _ in GUARDS] + [Q_ASKED] or want['new'] != len(nodes) \
            or want['asked'] != ([(N_VALID, [True])] if drops else []):
        raise SystemExit('read-back: the turning branch of %s is not as intended: %r' % (ai_path(name), want))
    return data


def describe(data):
    """what a turning AI does, read from the file by following its links: {'name', 'new' (nodes after the
    game's 13), 'guards' (the questions that stop it, in order), 'own' (the name whose owning turns it), 'turn'
    (what it then does, in order), 'drops' (whether that drops), 'later' (the names whose owning deletes it),
    'enter' (what it does on entering), 'asked' (what it does while its own pick-up is asked for and Link
    owns it: nothing, or the drop switched on)}. Raises SystemExit when the branch is not the one turning_ai
    makes."""
    doc = ainb.loads(data)
    nodes = doc.nodes
    pre = [i for i, n in enumerate(nodes) if n.flags & 1]

    def bad(what):
        raise SystemExit('%s: %s' % (doc.filename, what))

    def kids(i):
        return [(l.name, l.node) for l in nodes[i].links[FLOW]]

    def source(i, param_type, link_type):
        n = nodes[i]
        x = n.inputs[param_type]
        if len(x) != 1 or x[0].node < 0 or [l.node for l in n.links[link_type]] != [x[0].node] \
                or [pre[p] for p in n.preconditions] != [x[0].node]:
            bad('node %d does not read one query as expected' % i)
        q = nodes[x[0].node]
        return q, q.outputs[param_type][x[0].param].name

    def nothing(i):
        if nodes[i].name != N_IDLE or any(nodes[i].links):
            bad('node %d: expected a node that does nothing' % i)

    root = nodes[doc.commands[0].left]
    top = root.links[FLOW][-1].node
    out = {'name': doc.filename, 'new': len(nodes) - BASE_NODES, 'enter': [], 'guards': [], 'later': [],
           'asked': []}
    stay = []                                      # what "pick-up asked for" leads to
    if nodes[top].type == SPLIT_TIMING:
        k = dict(kids(top))
        if list(k) != ['Enter', 'Update', 'Leave']:
            bad('timing node not as expected')
        e = nodes[k['Enter']]
        out['enter'] = [(e.name, [x.value for x in e.inputs['bool']])]
        nothing(k['Leave'])
        top = k['Update']
    while nodes[top].type == BOOL_SELECTOR:
        q, name = source(top, 'bool', VALUE)
        k = dict(kids(top))
        if list(k) != ['True', 'False']:
            bad('guard %d not as expected' % top)
        if q.name == Q_ASKED:
            stay.append(k['True'])
        else:
            nothing(k['True'])
        out['guards'].append(q.name)
        top = k['False']

    def owned(i):
        q, name = source(i, 'int', INT)
        k = kids(i)
        if nodes[i].type != S32_SELECTOR or q.name != Q_OWNED or name != 'Num' \
                or [(l.name, l.extra) for l in nodes[i].links[FLOW]] != [('', (0, 0)), ('', (0, 0))]:
            bad('inventory question %d not as expected' % i)
        return q.inputs['string'][0].value, k[0][1], k[1][1]

    out['own'], rest, turn = owned(top)
    if len(stay) != 1 or out['guards'][-1:] != [Q_ASKED]:
        bad('"pick-up asked for" is not the last question before "Link owns this level"')
    if nodes[stay[0]].type == S32_SELECTOR:        # asked for and owned: the drop switched on, nothing else
        item, none, keep = owned(stay[0])
        nothing(none)
        if item != out['own'] or nodes[keep].name != N_VALID or any(nodes[keep].links):
            bad('"pick-up asked for" does not switch the drop on for the level owned')
        out['asked'] = [(nodes[keep].name, [x.value for x in nodes[keep].inputs['bool']])]
    else:
        nothing(stay[0])
    steps = [turn] if nodes[turn].type != SEQUENTIAL else [c for _, c in kids(turn)]
    if nodes[turn].type == SEQUENTIAL and not {x.name: x.value for x in nodes[turn].immediates['bool']}.get(
            'IsUpdateNextInFrame'):
        bad('the turn is not done in one step')
    out['turn'] = [(nodes[s].name, [x.value for x in nodes[s].inputs['bool']]) for s in steps]
    out['drops'] = N_DROP in [n for n, _ in out['turn']]
    while nodes[rest].type == S32_SELECTOR:
        item, nxt, gone = owned(rest)
        if nodes[gone].name != N_DELETE:
            bad('a later level owned does not delete the item')
        out['later'].append(item)
        rest = nxt
    nothing(rest)
    want = [(N_VALID, [True]), (N_DROP, []), (N_DELETE, [])] if out['drops'] else [(N_DELETE, [])]
    if out['turn'] != want or out['enter'] != ([(N_VALID, [False])] if out['drops'] else []):
        bad('the turn or the entering step is not as expected: %r, %r' % (out['turn'], out['enter']))
    reached, todo = set(), [doc.commands[0].left]
    while todo:
        i = todo.pop()
        if i in reached:
            continue
        reached.add(i)
        todo += [l.node for links in nodes[i].links for l in links]
        todo += [x.node for t in ainb.PARAM_TYPES for x in nodes[i].inputs[t] if x.node >= 0]
    if reached != set(range(len(nodes))):
        bad('nodes that nothing leads to: %s' % sorted(set(range(len(nodes))) - reached))
    return out


def build(family, level, read_pack, read_table_rows, model_exists=lambda project: False):
    """the turning item of level `level` (0 = the first) of `family` (the items' own names, in order).
    Returns (name, pack data, {inner path: (data, the game file it is made from: its size entry's reference)}
    for the files new to the game, {table: new row}, loose files as ground_items.build)."""
    if len(family) != 2:
        # with three levels, a level whose next level is owned would have to turn too (not only delete itself)
        raise SystemExit('%s: only families of two levels yet' % '>'.join(family))
    item = family[level]
    last = level == len(family) - 1
    name, pack, ground_new, rows, loose = ground_items.build(item, read_pack, read_table_rows, model_exists, VERSION)
    if name != turn_name(item):
        raise SystemExit('%s: name not as intended' % name)
    arc = sarc.Sarc.read(pack)
    files = dict(arc.files)
    tpl_name = ground_items.template_of(name)
    tpl = sarc.Sarc.read(read_pack(pack_path(tpl_name))).files
    new_inner = {}
    for p, d in ground_new.items():                # as tools/build_mod.py does for a ground version
        like = (ground_items.anim_param_path(tpl_name) if 'AnimationParam' in p
                else ground_items.pouch_param_path(tpl_name) if 'PouchContentParam' in p
                else ap_path(tpl_name))
        new_inner[p] = (d, like)

    # the AI: the ground items' own, with the turning branch
    base_info = ai_info_path(BASE_AI)
    if resolved_components(files, name).get('AIInfoRef') != '?' + base_info or base_info not in files:
        raise SystemExit('%s: its AI is not %s as expected' % (name, BASE_AI))
    idoc = byml.loads(files[base_info])
    if dict(idoc.root) != {'RootAIRef': 'Work/AI/Root/%s.root.ain' % BASE_AI}:
        raise SystemExit('%s not as expected' % base_info)
    ai = ai_name(item)
    idoc.root = type(idoc.root)(idoc.root)
    idoc.root['RootAIRef'] = type(idoc.root['RootAIRef'])('Work/AI/Root/%s.root.ain' % ai)
    shared = sarc.Sarc.read(read_pack(AI_PACK)).files
    for p in [ai_path(BASE_AI)] + list(SOURCES.values()):
        if p not in shared:
            raise SystemExit('%s: no %s' % (AI_PACK, p))
    drop_ai = sarc.Sarc.read(read_pack(pack_path(DROP_ACTOR))).files.get(DROP_AI)
    if drop_ai is None:
        raise SystemExit('%s: no %s in its pack' % (DROP_ACTOR, DROP_AI))
    request_ai = sarc.Sarc.read(read_pack(pack_path(REQUEST_ACTOR))).files.get(REQUEST_AI)
    if request_ai is None:
        raise SystemExit('%s: no %s in its pack' % (REQUEST_ACTOR, REQUEST_AI))
    ai_data = turning_ai(shared[ai_path(BASE_AI)], {k: shared[p] for k, p in SOURCES.items()}, drop_ai,
                         request_ai, item, family[level + 1:], drops=not last, name=ai)
    new_inner[ai_info_path(ai)] = (byml.dumps(idoc), base_info)
    new_inner[ai_path(ai)] = (ai_data, ai_path(BASE_AI))
    # (the ground items' own AI settings stay in the pack: the item base's file still names them)

    # the actor: the ground version with the AI of its own and, when it has a next level, a drop part
    adoc = byml.loads(files[ap_path(name)])
    adoc.root = type(adoc.root)(adoc.root)
    comp = type(adoc.root['Components'])(adoc.root['Components'])
    if 'AIInfoRef' in comp or 'DropRef' in comp or 'DropRef' in resolved_components(files, name):
        raise SystemExit('%s: already has an AI or a drop part of its own' % name)
    comp['AIInfoRef'] = '?' + ai_info_path(ai)
    if not last:
        # the drop part: copies of the three files of an actor that turns into another, naming the next level
        src = sarc.Sarc.read(read_pack(pack_path(DROP_TEMPLATE))).files
        nxt = turn_name(family[level + 1])
        want = {drop_param_path(DROP_TEMPLATE): {
                    '$parent': _work(DROP_SHARED[0]), 'DropTableResourceList': [_work(drop_table_path(DROP_TEMPLATE))]},
                drop_table_path(DROP_TEMPLATE): {'SubTableList': [_work(drop_sub_path(DROP_TEMPLATE))]}}
        for p, w in want.items():
            if p not in src or byml.loads(src[p]).root != w:
                raise SystemExit('%s: %s is not as expected' % (DROP_TEMPLATE, p))
        sub = byml.loads(src[drop_sub_path(DROP_TEMPLATE)])
        items = sub.root.get('Items')
        if set(sub.root) != {'Items'} or len(items) != 1 or items[0].get('DropCreateCount') != 1 \
                or items[0].get('DropProbability') != 100 or not str(items[0].get('DropActorName', '')).startswith(
                    'Work/Actor/'):
            raise SystemExit('%s: its drop table is not the one actor, always, expected' % DROP_TEMPLATE)
        if byml.loads(src[DROP_SHARED[0]]).root != {'BlackboardTableRef': _work(DROP_SHARED[1])} \
                or DROP_SHARED[1] not in src:
            raise SystemExit('%s: the shared drop settings are not as expected' % DROP_TEMPLATE)
        ddoc = byml.loads(src[drop_param_path(DROP_TEMPLATE)])
        ddoc.root = type(ddoc.root)(ddoc.root)
        ddoc.root['DropTableResourceList'] = [_work(drop_table_path(name))]
        tdoc = byml.loads(src[drop_table_path(DROP_TEMPLATE)])
        tdoc.root = type(tdoc.root)(tdoc.root)
        tdoc.root['SubTableList'] = [_work(drop_sub_path(name))]
        sub.root = type(sub.root)(sub.root)
        entry = type(items[0])(items[0])
        entry['DropActorName'] = _work(ap_path(nxt))
        sub.root['Items'] = [entry]
        new_inner[drop_param_path(name)] = (byml.dumps(ddoc), drop_param_path(DROP_TEMPLATE))
        new_inner[drop_table_path(name)] = (byml.dumps(tdoc), drop_table_path(DROP_TEMPLATE))
        new_inner[drop_sub_path(name)] = (byml.dumps(sub), drop_sub_path(DROP_TEMPLATE))
        for p in DROP_SHARED:                       # the game's own files, as they are
            files[p] = src[p]
        comp['DropRef'] = '?' + drop_param_path(name)
    adoc.root['Components'] = comp
    new_inner[ap_path(name)] = (byml.dumps(adoc), new_inner[ap_path(name)][1])
    for p, (d, _) in new_inner.items():
        files[p] = d

    # every file the actor's settings name is in the pack (names and system settings are kept outside)
    missing = [p for p in set(_refs(byml.loads(files[ap_path(name)]).root)) if p not in files and not p.startswith(
        ('ActorSystem/', 'AS/', 'Component/ActorGameDataSetting/', 'Component/XLink/', 'Work/', 'Logic/'))]
    named = [ai_path(ai)]
    if not last:
        named += [drop_table_path(name), drop_sub_path(name)] + list(DROP_SHARED)
    missing += [p for p in named if p not in files]
    if missing:
        raise SystemExit('%s: files not in the pack: %s' % (name, ', '.join(sorted(missing))))

    out = sarc.Sarc.read(pack)                      # the ground version's own layout settings
    out.files = files
    out.align = {p: arc.align.get(p, 8) for p in files}
    pack = out.write()

    # memory: the drop part and the bigger AI, as much as they add to the game's own turning actor
    heap = {r['__RowId']: int(r['InstanceHeapSize']) for r in read_table_rows('ActorInfo')
            if r['__RowId'] in HEAP_ACTORS}
    extra = max(heap[HEAP_ACTORS[0]] - heap[HEAP_ACTORS[1]], HEAP_LEAST)
    row = type(rows['ActorInfo'])(rows['ActorInfo'])
    row['InstanceHeapSize'] = type(row['InstanceHeapSize'])(int(row['InstanceHeapSize']) + extra)
    rows = dict(rows, ActorInfo=row)

    # read back
    back = sarc.Sarc.read(pack)
    if set(back.files) != set(files) or any(back.files[p] != d for p, d in files.items()):
        raise SystemExit('read-back: pack of %s differs from what was intended' % name)
    got = resolved_components(back.files, name)
    if got.get('AIInfoRef') != '?' + ai_info_path(ai) \
            or byml.loads(back.files[ai_info_path(ai)]).root['RootAIRef'] != 'Work/AI/Root/%s.root.ain' % ai \
            or describe(back.files[ai_path(ai)])['name'] != ai + '.root' or ('DropRef' in got) == last:
        raise SystemExit('read-back: the AI or the drop part of %s differs' % name)
    if not last:
        d = byml.loads(back.files[_ref_path(got['DropRef'])]).root
        t = byml.loads(back.files[drop_table_path(name)]).root
        s = byml.loads(back.files[drop_sub_path(name)]).root
        if d['DropTableResourceList'] != [_work(drop_table_path(name))] \
                or t['SubTableList'] != [_work(drop_sub_path(name))] \
                or [x['DropActorName'] for x in s['Items']] != [_work(ap_path(turn_name(family[level + 1])))]:
            raise SystemExit('read-back: the drop files of %s do not lead to the next level' % name)
    return name, pack, new_inner, rows, loose
