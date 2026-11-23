"""Progressive families on Gold Skulltulas, rocks, bushes and pots (to test in game).

What makes a Gold Skulltula different (out/RESEARCH_pairs_more.md, out/RESEARCH_skulltula_progressive.md): the
skulltula is not marked done when it dies but when its drop is picked up. Its AI hands the saved flag of its
placement to what it drops (`QueryBlackboardOverwriteParamAddNoRespawnGmdHash`, key `GoldTokenGmdHash`), and the
drop's own AI sets that flag when the drop is picked up (`OneShotGoldTokenDeadAfter`, the token's AI). Only the
actor the skulltula itself drops ever holds that flag: no game node reads it back to hand it to a second drop,
and a blackboard table can only start a 64-bit key with a 32-bit value (read in the game's code: the start value
of a `BlackboardParamU64Array` entry is read as 32 bits; the flag is 64). So a turning item (tools/turn_items.py)
cannot be used: the level it turns into would mark nothing, and the skulltula would come back for the next level.

So the level is chosen before anything is dropped, by the game's own drop code. Its global settings
(`GameParameter/DropGlobalParam/Default`, `DropLotteryMasterData`) have two lists:
- `DropUnlockCondition`: `{Actor, GameDataName}`: the actor is only dropped while that saved yes/no is true
  (bombs once a scrub sells them, Deku Sticks as a child, insects once a scrub sells them...);
- `ReplaceSetting`: `{TargetActor, Condition, ReplaceActor: [{Probability, ReplaceActor}]}`: when the drop would
  be `TargetActor` and `Condition` holds, `ReplaceActor` is dropped in its place. Every actor of the unlock
  list has a row with condition 8566081 (a green rupee in its place), so 8566081 is "not unlocked".
The game asks "did Link ever get X" with the saved yes/no `IsGet.<X>` (one per item; the Lost Woods target asks
`IsGet.Item_BulletBag_Medium` to give the bigger or the biggest seed bag).

A family on a Gold Skulltula: the placement's `Drop__DropActor` names the token version of the LAST level, and
the two lists get one row each per level but the first:

    DropUnlockCondition  {Actor: level k,        GameDataName: IsGet.<level k-1>}
    ReplaceSetting       {TargetActor: level k,  Condition: not unlocked, ReplaceActor: level k-1}   (highest first)

So the skulltula drops the last level if Link ever got the one before it, else the one before, and so on down
to the first. What is dropped is one token version (tools/ground_items.py, 'token'), made by the skulltula
itself: it holds the skulltula's flag and marks it when picked up, as every Gold Skulltula drop of ours does.
Nothing turns, nothing else lies on the ground, the skulltula's own files are not touched.

Every level is a token version under a name of its own, `Obj_NX2S_<level>`, so that the rows are about these
actors only, with one more branch in a copy of the token's AI (`NX2_GS_<level>.root`):

    every frame:
      dead? in an event? a main event playing? its pick-up asked for?   -> nothing   (the turning items' guards)
      Link does not own the level before (levels after the first)       -> delete itself
      Link owns this level or a later one                               -> delete itself

Two safety nets. Should the drop code not replace as read (the rows not used for a placement's `Drop__DropActor`,
or a replacement not replaced again for three levels), a level whose earlier level Link does not own removes
itself instead of being picked up: no level is skipped. And a level Link already owns removes itself (two drops
of one family lying at once, both made before either was picked up; or the level got somewhere else while the
drop lay there): no level is given twice. Either way nothing is marked, and the skulltula, rock, bush or pot
comes back and drops the level that is right then.

The Fairy Slingshot and the Fairy Bow (first levels) also get the turning item's two bag steps
(tools/turn_items.py: what a chest gives with the weapon, when its pick-up is asked for and Link doesn't own it,
and once Link owns it; both only while Link has no small bag).

Rocks, bushes and pots (2026-11-22): the same actors and rows. Their AI of our own (tools/once_items.py) hands
their placement's number to what they drop with the skulltula's own nodes, so what is dropped marks them when
picked up, as it marks a skulltula. The level is chosen by the drop code before anything is dropped: nothing
turns on the ground, and no AI writes the drop's name (`Drop__DropActor` is an instance parameter; writing one
crashed the game).

Every new node is a copy of a game node of the same type, found by what it is and checked before it is used.
"""
import copy
import hashlib
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml, ainb  # noqa: E402
import ground_items  # noqa: E402
import turn_items  # noqa: E402
from ground_items import pack_path, ap_path, resolved_components  # noqa: E402
from shop_items import ai_path, ai_info_path, _node_state, _doc_state  # noqa: E402
from turn_items import (_find, _query, _action, _element, _plain, _params, _add_of, first_get,  # noqa: E402
                        S32_SELECTOR, SEQUENTIAL, SIMULTANEOUS, BOOL_SELECTOR, VALUE, FLOW, INT,
                        Q_OWNED, Q_ASKED, N_DELETE, N_IDLE, N_ADD, GUARDS)

VERSION = 'token'                                 # the kind of version in ground_items.VERSIONS it is made from
TOKEN = ground_items.TOKEN
PREFIX = 'Obj_NX2S_'
AI_PREFIX = 'NX2_GS_'
BASE_AI = 'Item_Token_Gold'                       # the token's AI, in the token's own pack
BASE_NODES = 12                                   # its nodes: kept as they are, with their numbers
AI_PACK = turn_items.AI_PACK
# where each new node is copied from: files of the shared AI pack (the turning items' sources, and the ground
# items' AI for the yes/no selector and the node that does nothing)
SOURCES = dict({k: turn_items.SOURCES[k] for k in ('owned', 'event', 'door', 'counter')},
               ground=ai_path(turn_items.BASE_AI))
REQUEST_ACTOR, REQUEST_AI = turn_items.REQUEST_ACTOR, turn_items.REQUEST_AI
HEAP_LEAST = turn_items.HEAP_LEAST                # memory for the bigger AI, as the turning items take

DROP_GLOBAL = 'GameParameter/DropGlobalParam/Default.game__drop__DropGlobalParam.bgyml'
NOT_UNLOCKED = 8566081                            # ReplaceSetting.Condition of every actor of the unlock list
GAME_DATA = 'GameData/GameDataList.Product.110.byml'
GOT = 'IsGet.'                                    # the saved yes/no "Link ever got <name>"


def drop_name(item):
    return PREFIX + (item[5:] if item.startswith('Item_') else item)


def ai_name(item):
    return AI_PREFIX + (item[5:] if item.startswith('Item_') else item)


def _work(actor):
    return 'Work/' + ap_path(actor)[:-len('.bgyml')] + '.gyml'


def _unwork(path):
    return turn_items._actor_of(path)


def guard_ai(base, sources, request_ai, own, previous=None, bundle=None, name=None, later=()):
    """the token's AI (`base`: Item_Token_Gold.root) under the name `name`, with one more branch (see the top of
    this file). own: the level's own name; previous: the level before it (not owned -> delete itself), None for
    a first level; later: the levels after it (own or any of these owned -> delete itself); bundle: (the nodes
    that add what the game's chests give with this level, the item whose absence says it was not given yet):
    turn_items.first_get, for a first weapon.
    sources: {key of SOURCES: that AI file}; request_ai: the AI the "pick-up asked for" question is copied from.
    Read back: the 12 nodes of the game's file are as they were but for the root's new children."""
    taken = (own,) + tuple(later)                   # owned -> delete itself (a level given twice otherwise)
    doc = ainb.loads(base)
    if doc.filename != BASE_AI + '.root' or len(doc.nodes) != BASE_NODES:
        raise SystemExit('%s: not the token\'s AI expected (%s, %d nodes)' % (ai_path(BASE_AI), doc.filename,
                                                                           len(doc.nodes)))
    n0 = len(doc.nodes)
    roots = [c.left for c in doc.commands]
    if len(roots) != 1 or doc.commands[0].name != 'Root':
        raise SystemExit('%s: one entry point "Root" expected' % ai_path(BASE_AI))
    root = doc.nodes[roots[0]]
    if root.type != SIMULTANEOUS or any(l.name or l.extra for l in root.links[FLOW]) \
            or any(links for t, links in enumerate(root.links) if t != FLOW) or len(root.links[FLOW]) != 2:
        raise SystemExit('%s: its root is not the "all at once" of two children expected' % ai_path(BASE_AI))
    if doc.exb or doc.attachments or doc.resident or doc.modules or any(doc.globals[t] for t in ainb.GLOBAL_TYPES):
        raise SystemExit('%s: more in the file than nodes (expressions, attachments...): not expected'
                         % ai_path(BASE_AI))
    src = {k: ainb.loads(d) for k, d in sources.items()}

    # the templates (as tools/turn_items.py finds them)
    sel_imm = [('int', 'CalculateTiming', 0), ('bool', 'ChildFrameSync', False), ('bool', 'InputValue', False),
               ('bool', 'IsNoSelectWhenChildBusy', False)]
    g = src['ground']
    t_bool = _element(g, BOOL_SELECTOR, sel_imm, [('True', ()), ('False', ())], other=(VALUE,))
    b_in = t_bool.inputs['bool']
    if len(b_in) != 1 or b_in[0].name != 'Input' or b_in[0].flags or b_in[0].node < 0 \
            or [(l.node, l.name, l.extra) for l in t_bool.links[VALUE]] != [(b_in[0].node, 'Input', (0, 0))] \
            or g.nodes[b_in[0].node].flags != 1 or any(g.nodes[b_in[0].node].links):
        raise SystemExit('%s: its yes/no selector is not as expected' % SOURCES['ground'])
    t_idle = _action(g, N_IDLE, [('bool', 'ExecuteEveryFrame', False)])
    t_int = _element(src['counter'], S32_SELECTOR, [
        ('int', 'CalculateTiming', 0), ('int', 'InputValue', 0), ('bool', 'ChildFrameSync', False),
        ('bool', 'IsNoSelectIfSameInstance', False), ('bool', 'IsNoSelectWhenChildBusy', False)],
        [('', (0, 0)), ('', (0, 0))], other=(INT,))                     # "when 0", then "otherwise" (the last)
    i_in = t_int.inputs['int']
    if len(i_in) != 1 or i_in[0].name != 'Input' or i_in[0].flags or i_in[0].node < 0 \
            or [(l.node, l.name, l.extra) for l in t_int.links[INT]] != [(i_in[0].node, 'Input', (0, 0))]:
        raise SystemExit('%s: its number selector is not as expected' % SOURCES['counter'])
    t_seq = _find(src['counter'], 'Element_Sequential (one step)', lambda n: (
        n.type == SEQUENTIAL and n.flags == 0 and _plain(n) and _params(n, 'immediates') == [
            ('int', 'BusyPolicy', 0), ('int', 'NumLoop', 0), ('int', 'PlayPolicy', 0), ('int', 'ResultPolicy', 0),
            ('bool', 'IsDelayJudge', False), ('bool', 'IsLoop', False), ('bool', 'IsUpdateNextInFrame', True)]
        and all(not l.name and not l.extra for l in n.links[FLOW]) and n.links[FLOW]
        and not any(links for t, links in enumerate(n.links) if t != FLOW)))
    t_delete = _action(src['counter'], N_DELETE, [('bool', 'ExecuteEveryFrame', False), ('bool', 'IsFade', False)])
    t_owned, p_owned = _query(src['owned'], Q_OWNED, 'int', 'Num')
    o_in = t_owned.inputs['string']
    if [(x.name, x.node, x.sources) for t in ainb.PARAM_TYPES for x in t_owned.inputs[t]] != [
            ('ActorName', -1, None)] or not o_in[0].value or o_in[0].flags >> 31:
        raise SystemExit('%s: its inventory question does not ask for a fixed name as expected' % SOURCES['owned'])
    t_guard = {turn_items.Q_DEAD: _query(src['owned'], turn_items.Q_DEAD, 'bool', 'IsDead'),
               turn_items.Q_EVENT: _query(src['event'], turn_items.Q_EVENT, 'bool', 'IsEventMember'),
               turn_items.Q_MAIN: _query(src['door'], turn_items.Q_MAIN, 'bool', 'IsPlayingMainEvent')}
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
        n = nodes[where - n0]
        x = n.inputs[param_type][0]
        x.node, x.param = query
        n.links[VALUE if param_type == 'bool' else INT] = [ainb.Link(query[0], 'Input', (0, 0))]
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

    def give(what):
        """Link has no `bundle[1]` (the small bag) -> what a chest gives with this level, in one step"""
        sel = owned(bundle[1], 'bundle bag, ' + what)
        seq = new(t_seq, 'bundle, ' + what)
        flow(seq, *[new(t, 'bundle %d, %s' % (j, what)) for j, t in enumerate(bundle[0])])
        flow(sel, seq, idle('bundle, ' + what))
        return sel

    # the level before not owned -> delete itself; then this level or a later one owned -> delete itself (asked
    # last)
    rest = idle('rest')
    for k, item in reversed(list(enumerate(taken))):
        sel = owned(item, 'taken %d' % k)
        flow(sel, rest, new(t_delete, 'delete, taken %d owned' % k))     # when 0 -> go on, otherwise -> delete
        rest = sel
    if previous:
        sel = owned(previous, 'previous')
        flow(sel, new(t_delete, 'delete, previous not owned'), rest)
        rest = sel
    # its own pick-up asked for -> nothing more (a first weapon not owned: what a chest gives with it)
    q = new(t_asked[0], 'guard IsRequestingGetEvent')
    asked = new(t_bool, 'is IsRequestingGetEvent')
    ask((q, t_asked[1]), asked, 'bool')
    if bundle:
        mine = owned(own, 'own, asked for')
        flow(mine, give('asked for'), idle('owned, asked for'))
    else:
        mine = idle('asked for')
    flow(asked, mine, rest)                         # True -> stay, False -> go on
    top = asked
    for q_name, out in reversed(GUARDS):            # the first asked last made
        q = new(t_guard[q_name][0], 'guard ' + out)
        s = new(t_bool, 'is ' + out)
        ask((q, t_guard[q_name][1]), s, 'bool')
        flow(s, idle(out), top)                     # True -> nothing, False -> go on
        top = s
    tops = [top]
    if bundle:                                      # beside the guards: owned and no small bag -> the same
        has = owned(own, 'own, bundle')
        flow(has, idle('own, bundle'), give('owned'))
        tops = [has, top]
    for n in nodes:                                 # preconditions: the place of the query among the query nodes
        if hasattr(n, 'wants'):
            n.preconditions = [sum(1 for x in (doc.nodes + nodes)[:n.wants] if x.flags & 1)]
            del n.wants
    doc.nodes += nodes
    for t in tops:
        root.links[FLOW].append(ainb.Link(t, '', ()))
    doc.filename = name + '.root'
    data = doc.write()

    # read back
    back, orig = ainb.loads(data), ainb.loads(base)
    if back.write() != data or back.filename != name + '.root' or len(back.nodes) != n0 + len(nodes) \
            or _doc_state(back) != _doc_state(orig):
        raise SystemExit('read-back: %s differs from what was intended' % ai_path(name))
    for i, (o, b) in enumerate(zip(orig.nodes, back.nodes)):
        if i == roots[0]:
            for t in tops:
                o.links[FLOW].append(ainb.Link(t, '', ()))
        if _node_state(o) != _node_state(b):
            raise SystemExit('read-back: node %d of %s differs from what was intended' % (i, ai_path(name)))
    for k, n in enumerate(nodes):
        if _node_state(back.nodes[n0 + k]) != _node_state(n):
            raise SystemExit('read-back: new node %d of %s differs from what was intended' % (n0 + k, ai_path(name)))
    want = describe(data)
    if want['previous'] != previous or want['taken'] != list(taken) or want['new'] != len(nodes) \
            or want['guards'] != [q for q, _ in GUARDS] + [Q_ASKED] \
            or (want['bundle'] is not None) != bool(bundle) \
            or (bundle and (want['own'] != own or want['bundle']['bag'] != bundle[1]
                            or want['bundle']['gives'] != [_add_of(t) for t in bundle[0]])):
        raise SystemExit('read-back: the new branch of %s is not as intended: %r' % (ai_path(name), want))
    return data


def describe(data):
    """what the AI of a Gold Skulltula level does more than the token's, read from the file by following its
    links: {'name', 'new' (nodes after the token's 12), 'guards' (the questions that stop it, in order),
    'previous' (the name whose absence deletes it, or None), 'taken' (the names whose owning deletes it, in
    the order asked), 'own' (a first weapon: its own name, else None),
    'bundle' (None, or what it gives with itself as a chest would: {'bag', 'gives': [(actor file, number)]}),
    'token' (whether the token's own 12 nodes still mark the skulltula on a pick-up: its death branch)}. Raises
    SystemExit when the branch is not the one guard_ai makes."""
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

    def owned(i):
        q, name = source(i, 'int', INT)
        k = kids(i)
        if nodes[i].type != S32_SELECTOR or q.name != Q_OWNED or name != 'Num' \
                or [(l.name, l.extra) for l in nodes[i].links[FLOW]] != [('', (0, 0)), ('', (0, 0))]:
            bad('inventory question %d not as expected' % i)
        return q.inputs['string'][0].value, k[0][1], k[1][1]

    def gives(i):
        bag, seq, none = owned(i)
        nothing(none)
        steps = [nodes[c] for _, c in kids(seq)]
        if nodes[seq].type != SEQUENTIAL or not steps or any(s.name != N_ADD or any(s.links) for s in steps) \
                or not {x.name: x.value for x in nodes[seq].immediates['bool']}.get('IsUpdateNextInFrame'):
            bad('node %d does not add to the inventory in one step' % seq)
        return {'bag': bag, 'gives': [_add_of(s) for s in steps]}

    root = nodes[doc.commands[0].left]
    more = [l.node for l in root.links[FLOW][2:]]
    if not more or any(i < BASE_NODES for i in more) or any(l.node >= BASE_NODES for l in root.links[FLOW][:2]):
        bad('the root does not run the token\'s two children and ours after them')
    out = {'name': doc.filename, 'new': len(nodes) - BASE_NODES, 'guards': [], 'previous': None, 'taken': [],
           'own': None, 'bundle': None}
    top, stay = more[-1], []
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
    if len(stay) != 1 or out['guards'][-1:] != [Q_ASKED]:
        bad('"pick-up asked for" is not the last question')
    def deletes(i):
        return nodes[i].name == N_DELETE and not any(nodes[i].links)

    while nodes[top].type == S32_SELECTOR:         # the inventory questions after the guards, in order
        item, zero, other = owned(top)
        if deletes(zero) and out['previous'] is None and not out['taken']:
            out['previous'], top = item, other     # the level before not owned -> delete itself
        elif deletes(other):
            out['taken'].append(item)              # owned -> delete itself
            top = zero
        else:
            bad('inventory question %d neither deletes when not owned nor when owned' % top)
    nothing(top)
    if len(more) == 2:                             # a first weapon: owned, no bag -> what a chest gives with it
        out['own'], none, give = owned(more[0])
        nothing(none)
        out['bundle'] = gives(give)
        item, give, none = owned(stay[0])
        nothing(none)
        if item != out['own'] or gives(give) != out['bundle']:
            bad('"pick-up asked for" does not give what "Link owns this level" gives beside it')
    elif len(more) == 1:
        nothing(stay[0])
    else:
        bad('more beside the new branch than expected')
    # the token's own marking: dead -> reason 10 -> OneShotGoldTokenDeadAfter, among its 12 nodes
    marks = [n for n in nodes[:BASE_NODES] if n.name == 'OneShotGoldTokenDeadAfter']
    out['token'] = len(marks) == 1 and not any(n.name == 'OneShotGoldTokenDeadAfter' for n in nodes[BASE_NODES:])
    reached, todo = set(), [doc.commands[0].left]
    while todo:
        i = todo.pop()
        if i in reached:
            continue
        reached.add(i)
        todo += [l.node for links in nodes[i].links for l in links]
        todo += [x.node for t in ainb.PARAM_TYPES for x in nodes[i].inputs[t] if x.node >= 0]
    if set(range(BASE_NODES, len(nodes))) - reached:
        bad('new nodes that nothing leads to: %s' % sorted(set(range(BASE_NODES, len(nodes))) - reached))
    return out


def build(family, level, read_pack, read_table_rows, model_exists=lambda project: False, bundle_for=None):
    """the drop of level `level` (0 = the first) of `family` (the items' own names, in order) on a Gold Skulltula,
    a rock, a bush or a pot, under a name of its own: the token version of that level with the AI of guard_ai.
    bundle_for: for a first level the game's chests give more with, the name the inventory knows it by.
    Returns (name, pack data, {inner path: (data, the game file it is made from)} for the files new to the game,
    {table: new row}, loose files as ground_items.build)."""
    item = family[level]
    previous = family[level - 1] if level else None
    if bundle_for and level:
        raise SystemExit('%s: only a first level gives more with itself' % item)
    name0, pack, ground_new, rows, loose = ground_items.build(item, read_pack, read_table_rows, model_exists, VERSION)
    name = drop_name(item)
    if name0 != ground_items.ground_name(item, VERSION) or name0 in name or name in name0:
        raise SystemExit('%s: names not as intended' % name)
    arc = sarc.Sarc.read(pack)
    tpl = sarc.Sarc.read(read_pack(pack_path(TOKEN))).files

    def renamed(p):
        return p.replace(name0, name)

    files = {renamed(p): d for p, d in arc.files.items()}
    align = {renamed(p): arc.align.get(p, 8) for p in arc.files}
    new_inner = {renamed(p): (d, ground_items.new_file_like(p, TOKEN)) for p, d in ground_new.items()}
    if len(files) != len(arc.files) or ap_path(name) not in files:
        raise SystemExit('%s: files of the token version not renamed as intended' % name)
    adoc = byml.loads(files[ap_path(name)])
    adoc.root = type(adoc.root)(adoc.root)
    comp = type(adoc.root['Components'])()
    for k, v in adoc.root['Components'].items():
        comp[k] = type(v)(v.replace(name0, name)) if isinstance(v, str) else v
    for p, d in files.items():                     # nothing else names the token version
        if p != ap_path(name) and name0.encode() in d:
            raise SystemExit('%s: %s names %s' % (name, p, name0))

    # the AI: the token's own, with the new branch
    base_info = ai_info_path(BASE_AI)
    if comp.get('AIInfoRef') != '?' + base_info or base_info not in files or ai_path(BASE_AI) not in files \
            or files[ai_path(BASE_AI)] != tpl[ai_path(BASE_AI)]:
        raise SystemExit('%s: its AI is not the token\'s as expected' % name)
    idoc = byml.loads(files[base_info])
    if dict(idoc.root) != {'RootAIRef': 'Work/AI/Root/%s.root.ain' % BASE_AI}:
        raise SystemExit('%s not as expected' % base_info)
    ai = ai_name(item)
    idoc.root = type(idoc.root)(idoc.root)
    idoc.root['RootAIRef'] = type(idoc.root['RootAIRef'])('Work/AI/Root/%s.root.ain' % ai)
    shared = sarc.Sarc.read(read_pack(AI_PACK)).files
    for p in SOURCES.values():
        if p not in shared:
            raise SystemExit('%s: no %s' % (AI_PACK, p))
    request_ai = sarc.Sarc.read(read_pack(pack_path(REQUEST_ACTOR))).files.get(REQUEST_AI)
    if request_ai is None:
        raise SystemExit('%s: no %s in its pack' % (REQUEST_ACTOR, REQUEST_AI))
    bundle = None
    if bundle_for:
        adds, gives = first_get(shared, bundle_for)
        bundle = (adds, gives[0][0])                # the first thing given (the small bag) says whether it was
    ai_data = guard_ai(files[ai_path(BASE_AI)], {k: shared[p] for k, p in SOURCES.items()}, request_ai, item,
                       previous, bundle, ai, family[level + 1:])
    new_inner[ai_info_path(ai)] = (byml.dumps(idoc), base_info)
    new_inner[ai_path(ai)] = (ai_data, ai_path(BASE_AI))
    comp['AIInfoRef'] = '?' + ai_info_path(ai)
    adoc.root['Components'] = comp
    new_inner[ap_path(name)] = (byml.dumps(adoc), new_inner[ap_path(name)][1])
    for p, (d, _) in new_inner.items():
        files[p] = d
        align.setdefault(p, 8)
    # what marks the skulltula is still there: the token's blackboard (the key the flag is handed over in) and
    # death settings, and its AI's 12 nodes in ours
    got = resolved_components(files, name)
    for r, v in ground_items.TOKEN_KEEPS.items():
        if r != 'AIInfoRef' and (got.get(r) != v or v[1:] not in files):
            raise SystemExit('%s: lost the token\'s %s' % (name, r))
    if ground_items.TOKEN_FILES[1] not in files or not describe(ai_data)['token']:
        raise SystemExit('%s: lost the token\'s blackboard table or its marking' % name)

    out = sarc.Sarc.read(pack)
    out.files = files
    out.align = {p: align[p] for p in files}
    pack = out.write()

    new_rows = {}
    for t, row in rows.items():
        row = type(row)(row)
        if row['__RowId'] != name0:
            raise SystemExit('%s: row of %s not as expected' % (name, t))
        row['__RowId'] = type(row['__RowId'])(name)
        new_rows[t] = row
    row = new_rows['ActorInfo']                     # memory: the bigger AI
    row['InstanceHeapSize'] = type(row['InstanceHeapSize'])(int(row['InstanceHeapSize']) + HEAP_LEAST)

    back = sarc.Sarc.read(pack)
    if set(back.files) != set(files) or any(back.files[p] != d for p, d in files.items()):
        raise SystemExit('read-back: pack of %s differs from what was intended' % name)
    got = resolved_components(back.files, name)
    if got.get('AIInfoRef') != '?' + ai_info_path(ai) \
            or byml.loads(back.files[ai_info_path(ai)]).root['RootAIRef'] != 'Work/AI/Root/%s.root.ain' % ai \
            or describe(back.files[ai_path(ai)])['name'] != ai + '.root':
        raise SystemExit('read-back: the AI of %s differs' % name)
    return name, pack, new_inner, new_rows, loose


# ---- the drop code's two lists -------------------------------------------------------------------------------

def mm3(s):
    """the hash the saved data is listed by (MurmurHash3, 32 bits, seed 0) of a name"""
    d, h, n = s.encode(), 0, len(s.encode())
    c1, c2 = 0xcc9e2d51, 0x1b873593
    for i in range(0, n - n % 4, 4):
        k = struct.unpack_from('<I', d, i)[0]
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xffffffff
        h = (h * 5 + 0xe6546b64) & 0xffffffff
    k, t, b = 0, n % 4, n - n % 4
    if t >= 3:
        k ^= d[b + 2] << 16
    if t >= 2:
        k ^= d[b + 1] << 8
    if t >= 1:
        k ^= d[b]
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
    h ^= n
    h ^= h >> 16
    h = (h * 0x85ebca6b) & 0xffffffff
    h ^= h >> 13
    h = (h * 0xc2b2ae35) & 0xffffffff
    return h ^ (h >> 16)


def got_flag(game_data, known_as):
    """the saved yes/no "Link ever got <known_as>" (the name the inventory knows an item by): its name, checked
    to be one of the game's saved yes/no values"""
    name = GOT + known_as
    if mm3(name) not in {int(e['Hash']) for e in byml.loads(game_data).root['Data']['Bool']}:
        raise SystemExit('%s: no such saved yes/no in %s' % (name, GAME_DATA))
    return name


def chain(family, known_as):
    """[(actor dropped for a level, the saved yes/no that says Link ever got that level)] of a family on a Gold
    Skulltula, a rock, a bush or a pot, lowest level first. known_as(item): the name the inventory knows it by"""
    return [(drop_name(x), GOT + known_as(x)) for x in family]


def drop_rows_read(data):
    """{actor: (the saved yes/no it waits for, [what is dropped in its place until then])} of the drop code's
    settings: the unlock list joined with the "not unlocked" rows of the replace list; and the order of those
    rows' actors. Stops the build when the two lists are not as this was made for."""
    m = byml.loads(data).root.get('DropLotteryMasterData') or {}
    unlock, replace = m.get('DropUnlockCondition'), m.get('ReplaceSetting')
    if not unlock or not replace or any(sorted(u) != ['Actor', 'GameDataName'] for u in unlock):
        raise SystemExit('%s: its unlock and replace lists are not as expected' % DROP_GLOBAL)
    flags = {}
    for u in unlock:
        if u['Actor'] in flags:
            raise SystemExit('%s: %s is in the unlock list twice' % (DROP_GLOBAL, u['Actor']))
        flags[u['Actor']] = u['GameDataName']
    out, order = {}, []
    for r in replace:
        if r.get('Condition') != NOT_UNLOCKED:
            continue
        if sorted(r) != ['Condition', 'ReplaceActor', 'TargetActor'] or r['TargetActor'] in out \
                or any(sorted(x) != ['Probability', 'ReplaceActor'] for x in r['ReplaceActor']):
            raise SystemExit('%s: a "not unlocked" row is not as expected' % DROP_GLOBAL)
        out[_unwork(r['TargetActor'])] = (flags.get(r['TargetActor']),
                                         [(int(x['Probability']), _unwork(x['ReplaceActor']))
                                          for x in r['ReplaceActor']])
        order.append(_unwork(r['TargetActor']))
    if set(flags) - {_work(a) for a in out}:
        raise SystemExit('%s: an actor of the unlock list has no "not unlocked" row: %d is not what this was '
                         'made for' % (DROP_GLOBAL, NOT_UNLOCKED))
    return out, order


def drop_rows(data, chains):
    """the drop code's settings with the rows of these chains (chain()): for each level but the first, "only
    dropped once Link ever got the level before" and "until then the level before is dropped in its place", the
    highest level first. Read back: every row of the game is as it was, in its place; ours are after them."""
    before, _ = drop_rows_read(data)
    doc = byml.loads(data)
    root = type(doc.root)(doc.root)
    m = type(root['DropLotteryMasterData'])(root['DropLotteryMasterData'])
    unlock, replace = list(m['DropUnlockCondition']), list(m['ReplaceSetting'])
    t_unlock = unlock[0]
    t_replace = next(r for r in replace if r.get('Condition') == NOT_UNLOCKED and len(r['ReplaceActor']) == 1
                     and int(r['ReplaceActor'][0]['Probability']) == 100)
    want = {}
    for ch in chains:
        for k in range(len(ch) - 1, 0, -1):
            (actor, _), (lower, flag) = ch[k], ch[k - 1]
            if actor in before or actor in want:
                if want.get(actor, before.get(actor)) != (flag, [(100, lower)]):
                    raise SystemExit('%s: already in the drop code\'s lists with other rows' % actor)
                continue
            want[actor] = (flag, [(100, lower)])
            u = type(t_unlock)(t_unlock)
            u['Actor'] = type(t_unlock['Actor'])(_work(actor))
            u['GameDataName'] = type(t_unlock['GameDataName'])(flag)
            unlock.append(u)
            r = type(t_replace)(t_replace)
            r['TargetActor'] = type(t_replace['TargetActor'])(_work(actor))
            e = type(t_replace['ReplaceActor'][0])(t_replace['ReplaceActor'][0])
            e['ReplaceActor'] = type(e['ReplaceActor'])(_work(lower))
            r['ReplaceActor'] = [e]
            replace.append(r)
    m['DropUnlockCondition'], m['ReplaceSetting'] = unlock, replace
    root['DropLotteryMasterData'] = m
    doc.root = root
    new = byml.dumps(doc)
    # read back
    old_root, new_root = byml.loads(data).root, byml.loads(new).root
    om, nm = old_root['DropLotteryMasterData'], new_root['DropLotteryMasterData']
    if list(old_root) != list(new_root) or any(new_root[k] != old_root[k] for k in old_root
                                               if k != 'DropLotteryMasterData') \
            or list(om) != list(nm) or any(nm[k] != om[k] for k in om
                                           if k not in ('DropUnlockCondition', 'ReplaceSetting')) \
            or nm['DropUnlockCondition'][:len(om['DropUnlockCondition'])] != om['DropUnlockCondition'] \
            or nm['ReplaceSetting'][:len(om['ReplaceSetting'])] != om['ReplaceSetting'] \
            or len(nm['DropUnlockCondition']) != len(om['DropUnlockCondition']) + len(want) \
            or len(nm['ReplaceSetting']) != len(om['ReplaceSetting']) + len(want):
        raise SystemExit('read-back: %s differs from what was intended' % DROP_GLOBAL)
    after, order = drop_rows_read(new)
    if after != dict(before, **want) or order[len(before):] != list(want):
        raise SystemExit('read-back: the new rows of %s are not as intended' % DROP_GLOBAL)
    return new, want


PRELOAD = 'SharePreLoadActorList'


def preload_read(data):
    """{actor: how many} of the drop code's list of actors kept loaded everywhere (SharePreLoadActorList).
    Left as the game has it: the game loads its first 16 entries only (2026-11-22, Longshot's log), and 14 are the
    game's own. The lower levels are loaded with our drop tables instead (tools/drop_tables.py: build, loaded)"""
    return {_unwork(x['ActorName']): int(x['Num']) for x in byml.loads(data).root.get(PRELOAD) or []}


def decide(rows, nominal, got):
    """what the drop code drops for a placement that names `nominal`, as the two lists are read (see the top of
    this file): while an actor waits for a saved yes/no that is false, what is dropped in its place, again and
    again. rows: drop_rows_read()[0]; got(flag) -> bool. Used by the tests and the build's messages."""
    actor, seen = nominal, set()
    while actor in rows and rows[actor][0] is not None and not got(rows[actor][0]):
        if actor in seen or len(rows[actor][1]) != 1:
            raise SystemExit('%s: the replace rows do not lead to one actor' % nominal)
        seen.add(actor)
        actor = rows[actor][1][0][1]
    return actor
