"""Three-level chests: a small chest of our own that gives the next level of a family of three (to test in game).

The game's checking chest (`Obj_TBox_A_06`, tools/build_mod.py CHECKING_CHEST) has two held items and one
question, so two outcomes. Three chests of a three-level family must each be able to give level 1, 2 or 3 (any
of them can be opened first, second or third), so they need a third held item and a second question.

Found in the game's files (2026-11-19, out/RESEARCH_progressive.md, question A):
- the checking chest is the small chest (`$parent` `Obj_TBox_A_01`) with four parts of its own: its AI
  (`AIInfoRef`), its held actors (`ActorHolderRef`: the small chest's, plus the slot `SubContent`), its drop
  settings (`DropRef`: three more map settings) and `AffiliationRef`;
- its AI (`Obj_TBox_A_06.root`, 101 nodes) makes both items when the chest is made (one
  `OneShotActorHolderTryRequestCreateActorWithActorFileName` per slot, under one "all at once" node), and every
  frame hands the name of a slot (`HolderKey`) to the shared chest module (`TreasureBox.module`), which requests
  the opening event with the actor in that slot. The name comes from a `QuerySelectStringByBool` (true -> A,
  false -> B) on "0 < the number Link has" (`QueryMathLessS32` on `QueryGetPouchContentNumByActorName`), turned
  round by `Drop__CheckCondition` (true unless a placement sets it; none does);
- a chest is lit by a light on its bone `Root`, given to it by name in the game's lists of such lights
  (`System/GameGraphics/LocationalLightRigGroupSetting/Gimmick0`: one entry per chest actor, the checking chest
  and its twin included; `HasLightRigBone` in `RSDB/GameActorInfo` says the actor has the bone);
- a slot's name is free: `ActorHoldSettings` is a table of names (`Content`, `SubContent`, `ContentDisplay`,
  `ShopHolder`, `Obj_Bomb`, `Rupee`...), and the code has no slot name of its own (its one `SubContent` is a
  parameter name of an error node);
- the inventory question is asked with a name fixed in the file by `Enemy_Tentacle_Red.utility.root`
  (`Item_Boomerang`), and an item is made from a name fixed in the file by the chest itself (`TBox_Rupee_Green`,
  its default); a `QuerySelectStringByBool` between a fixed text and another node's text is in the chest's own
  local module (`_LocalModule_46ad10eacd08.module`).

A three-level chest is one actor per family, `Obj_TBox_NX2_<family>` (and `_NoBake`): the checking chest with
- a third slot, `ThirdContent`, a copy of `SubContent`'s settings;
- an AI of its own, `Obj_TBox_NX2_<family>.root`: the checking chest's AI (its 101 nodes with their numbers)
  and four nodes more, each a copy of a game node of the same type:

      when the chest is made:   also make level 3 in the third slot          (copy of the chest's own node)
      every frame:              Link has level 2?                            (the tentacle's question)
                                0 < that number                              (copy of the chest's own node)
                                yes -> "ThirdContent", no -> the checking chest's answer
                                                                             (the local module's node)

  and the chest module takes its slot name from the last one. So: Link has level 2 -> level 3; else the
  checking chest's own answer: Link has level 1 -> level 2 (`Drop__DropActor_Substitute`), else level 1
  (`Drop__DropActor`). Level 1 and 2 are the placement's settings, as for a two-level pair; the level-2
  question and level 3 are fixed in the AI (as a turning item's names are, tools/turn_items.py), so the game's
  drop settings and its settings table are used as they are.

Nothing of the game's chests is changed: the game's checking chest, its AI and the shared chest module stay as
they are. Besides its pack and its two table rows (the checking chest's, under its name), a chest of ours gets
its entry in the game's list of chest lights: a copy of the checking chest's, added at the end of the list.

Not done: the game's tag table (`RSDB/Tag`) has no row for our chest. The checking chest's row has `Graphics`,
`HasLightRigBone` (read by the code from `GameActorInfo`, where ours has it) and `MapIcon_Treasure`: in a
dungeon, a chest of ours would most likely not be drawn on the dungeon map.
"""
import copy
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml, ainb  # noqa: E402
from ground_items import pack_path, ap_path, _refs, resolved_components  # noqa: E402
from shop_items import ai_path, ai_info_path, _node_state, _doc_state  # noqa: E402

PREFIX = 'Obj_TBox_NX2_'
PLAIN = 'Obj_TBox_A_01'                           # the small chest
BASE = 'Obj_TBox_A_06'                            # the game's checking chest: what ours is made from
NOBAKE = '_NoBake'                                # the twin both have (its own model settings, no baked shadow)
BASE_NODES = 101                                  # nodes of the checking chest's AI: kept, with their numbers
THIRD_KEY = 'ThirdContent'                        # the third slot
SECOND_KEY = 'SubContent'                         # the checking chest's second slot
AI_PACK = 'Pack/AI.Global.Product.111.pack'
# where the new nodes that are not the chest's own are copied from (files of the shared AI pack)
SOURCES = {
    'owned': 'AI/Enemy_Tentacle_Red.utility.root.ainb',     # QueryGetPouchContentNumByActorName, a fixed name
    'select': 'AI/_LocalModule_46ad10eacd08.module.ainb',   # QuerySelectStringByBool: a fixed text or a node's
}
SIMULTANEOUS, STRING_SELECTOR = 3, 5
VALUE, FLOW, STRING, INT = 0, 2, 4, 5             # link types (formats/ainb.py)
N_CREATE = 'OneShotActorHolderTryRequestCreateActorWithActorFileName'
N_MODULE = 'TreasureBox.module'
Q_OWNED, Q_LESS, Q_SELECT = 'QueryGetPouchContentNumByActorName', 'QueryMathLessS32', 'QuerySelectStringByBool'
Q_XOR = 'QueryExclusiveDisjunction'
FIXED = 0x800000                                  # an input whose value is set in the file
# the game's list of the lights on the bones of chests (and other objects): one entry per actor
LIGHT_RIGS = ('System/GameGraphics/LocationalLightRigGroupSetting/'
              'Gimmick0.game__gfx__LocationalLightRigGroupSetting.bgyml')


def chest_name(tag, nobake=False):
    return PREFIX + tag + (NOBAKE if nobake else '')


def holder_path(actor):
    return 'Component/ActorHolderParam/%s.game__component__ActorHolderParam.bgyml' % actor


def drop_param_path(actor):
    return 'Component/DropParam/%s.game__component__DropParam.bgyml' % actor


def model_info_path(actor):
    return 'Component/ModelInfo/%s.engine__component__ModelInfo.bgyml' % actor


def _work(path):
    """'Actor/X.bgyml' -> 'Work/Actor/X.gyml' (how parameter files name each other)"""
    return 'Work/' + path[:-len('.bgyml')] + '.gyml'


def _params(n, kind):
    return [(t, x.name) for t in ainb.PARAM_TYPES for x in getattr(n, kind)[t]]


def _one(doc, what, ok):
    hits = [i for i, n in enumerate(doc.nodes) if ok(n)]
    if len(hits) != 1:
        raise SystemExit('%s: %d nodes found for %s, expected one (game files differ from what this was made for)'
                         % (doc.filename, len(hits), what))
    return hits[0]


def _plain(n):
    return not n.attachments and not n.exb_count and not n.exb_size


def _fixed(x):
    """an input with nothing linked: a value of the file (not a global parameter, not an expression)"""
    return x.node < 0 and x.sources is None and not x.flags >> 31


def _landmarks(doc):
    """the nodes of a checking chest's AI the third level hangs on, found by what they are:
    {'make': the "all at once" node that makes the held items, 'create': the node that makes the default item
    in the second slot, 'module': the chest module, 'select': the node its slot name comes from, 'less': "0 <
    the number Link has", 'owned': the inventory question}"""
    nodes = doc.nodes

    def bad(what):
        raise SystemExit('%s: %s (game files differ from what this was made for)' % (doc.filename, what))

    module = _one(doc, 'the chest module', lambda n: n.name == N_MODULE)
    key = [x for x in nodes[module].inputs['string'] if x.name == 'HolderKey']
    if len(key) != 1 or key[0].node < 0 or key[0].param != 0 or key[0].flags or key[0].sources is not None \
            or [(l.node, l.name, l.extra) for l in nodes[module].links[STRING]] != [(key[0].node, 'HolderKey', ())]:
        bad('the chest module does not take its slot name from one node')
    select = key[0].node
    s = nodes[select]
    if s.name != Q_SELECT or not s.flags & 1 or _params(s, 'inputs') != [('bool', 'Bool'), ('string', 'A'),
                                                                         ('string', 'B')] \
            or _params(s, 'outputs') != [('string', 'String')] or not s.outputs['string'][0].flag:
        bad('the slot name does not come from a choice between two texts')
    xor = nodes[s.inputs['bool'][0].node]
    less = xor.inputs['bool'][0].node if xor.name == Q_XOR and xor.inputs['bool'] else -1
    ls = nodes[less] if less >= 0 else None
    if ls is None or ls.name != Q_LESS or not _plain(ls) or ls.flags != 1 \
            or _params(ls, 'inputs') != [('int', 'S32'), ('int', 'S32Base')] \
            or not _fixed(ls.inputs['int'][0]) or ls.inputs['int'][0].value != 0 \
            or _params(ls, 'outputs') != [('bool', 'Bool')] or not ls.outputs['bool'][0].flag \
            or any(links for t, links in enumerate(ls.links) if t != INT) \
            or [(l.node, l.name, l.extra) for l in ls.links[INT]] != [(ls.inputs['int'][1].node, 'S32Base', ())]:
        bad('the choice is not made on "0 < a number" as expected')
    owned = ls.inputs['int'][1].node
    if owned < 0 or nodes[owned].name != Q_OWNED or ls.inputs['int'][1].param != 0 \
            or [x.name for x in nodes[owned].outputs['int']] != ['Num']:
        bad('the number is not the inventory\'s')
    # the two texts: each a choice whose fixed side is a slot name
    slots = []
    for x in s.inputs['string']:
        side = nodes[x.node] if x.node >= 0 else None
        if side is None or side.name != Q_SELECT or not _fixed(side.inputs['string'][1]):
            bad('the two slot names are not as expected')
        slots.append(side.inputs['string'][1].value)
    if slots != ['Content', SECOND_KEY]:
        bad('the slots are %r, expected Content and %s' % (slots, SECOND_KEY))
    create = _one(doc, 'the default item of the second slot', lambda n: (
        n.name == N_CREATE and n.type == 0 and n.flags == 0 and _plain(n) and not any(n.links)
        and not n.preconditions and _params(n, 'inputs') == [('int', 'Index'), ('string', 'ActorFileName'),
                                                             ('string', 'Key')]
        and all(_fixed(x) for t in ainb.PARAM_TYPES for x in n.inputs[t])
        and n.inputs['string'][0].flags == FIXED and n.inputs['string'][1].flags == FIXED
        and n.inputs['string'][1].value == SECOND_KEY and not any(n.outputs[t] for t in ainb.PARAM_TYPES)))
    make = _one(doc, 'the node that makes the held items', lambda n: (
        n.type == SIMULTANEOUS and len(n.links[FLOW]) == 2 and not any(l.name or l.extra for l in n.links[FLOW])
        and not any(links for t, links in enumerate(n.links) if t != FLOW)
        and all(nodes[l.node].type == STRING_SELECTOR and all(
            nodes[c.node].name == N_CREATE for c in nodes[l.node].links[FLOW]) for l in n.links[FLOW])))
    if create not in [c.node for l in nodes[make].links[FLOW] for c in nodes[l.node].links[FLOW]]:
        bad('the second slot is not made with the first')
    return {'make': make, 'create': create, 'module': module, 'select': select, 'less': less, 'owned': owned}


def _reached(doc):
    reached, todo = set(), [c.left for c in doc.commands]
    while todo:
        i = todo.pop()
        if i in reached:
            continue
        reached.add(i)
        todo += [l.node for links in doc.nodes[i].links for l in links]
        todo += [x.node for t in ainb.PARAM_TYPES for x in doc.nodes[i].inputs[t] if x.node >= 0]
    return reached


def chest_ai(base, sources, name, second, third):
    """the checking chest's AI (`base`: Obj_TBox_A_06.root) under the name `name`, with the third level (see the
    top of this file). second: the second level's own name, as the inventory knows it; third: the third level's
    actor, as a chest gives it. sources: {key of SOURCES: that AI file}.
    Read back: the 101 nodes of the game's file are as they were, but for one child more on the node that makes
    the held items and the node the chest module takes its slot name from."""
    doc = ainb.loads(base)
    if doc.filename != BASE + '.root':
        raise SystemExit('%s: not the checking chest\'s AI expected (%s)' % (ai_path(BASE), doc.filename))
    n0 = len(doc.nodes)
    if n0 != BASE_NODES:
        raise SystemExit('%s: %d nodes, expected %d' % (ai_path(BASE), n0, BASE_NODES))
    if [c.name for c in doc.commands] != ['Root'] or doc.attachments or doc.resident:
        raise SystemExit('%s: one entry point "Root" and no attachments expected' % ai_path(BASE))
    if not second or not third:
        raise SystemExit('%s: the second level\'s name and the third level\'s actor are needed' % name)
    at = _landmarks(doc)
    src = {k: ainb.loads(d) for k, d in sources.items()}

    # the templates that are not the chest's own
    t_owned = src['owned'].nodes[_one(src['owned'], 'an inventory question with a fixed name', lambda n: (
        n.name == Q_OWNED and n.type == 0 and n.flags == 1 and _plain(n) and not any(n.links)
        and not n.preconditions and _params(n, 'inputs') == [('string', 'ActorName')]
        and _fixed(n.inputs['string'][0]) and n.inputs['string'][0].value
        and [(t, x.name, x.value) for t in ainb.PARAM_TYPES for x in n.immediates[t]] == [
            ('bool', 'OutputOnlyOnEnter', False)]
        and [(t, x.name, x.flag) for t in ainb.PARAM_TYPES for x in n.outputs[t]] == [('int', 'Num', True)]))]
    t_select = src['select'].nodes[_one(src['select'], 'a choice between a fixed text and a node\'s', lambda n: (
        n.name == Q_SELECT and n.type == 0 and _plain(n) and n.flags == doc.nodes[at['select']].flags
        and _params(n, 'inputs') == [('bool', 'Bool'), ('string', 'A'), ('string', 'B')]
        and n.inputs['bool'][0].node >= 0 and not n.inputs['bool'][0].flags
        and _fixed(n.inputs['string'][0]) and n.inputs['string'][0].flags == FIXED
        and n.inputs['string'][1].node >= 0 and not n.inputs['string'][1].flags
        and [(t, x.name, x.value) for t in ainb.PARAM_TYPES for x in n.immediates[t]] == [
            ('bool', 'OutputOnlyOnEnter', False)]
        and [(t, x.name, x.flag) for t in ainb.PARAM_TYPES for x in n.outputs[t]] == [('string', 'String', True)]
        and [(t, [(l.name, l.extra) for l in links]) for t, links in enumerate(n.links) if links] == [
            (VALUE, [('Bool', ())]), (STRING, [('B', ())])]))]

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

    # made with the other two: level 3 in the third slot
    create = new(doc.nodes[at['create']], 'third slot')
    c_in = nodes[create - n0].inputs['string']
    c_in[0].value, c_in[1].value = third, THIRD_KEY
    # Link has level 2?
    owned = new(t_owned, 'owned second')
    nodes[owned - n0].inputs['string'][0].value = second
    less = new(doc.nodes[at['less']], 'has second')
    l_in = nodes[less - n0].inputs['int'][1]
    l_in.node, l_in.param = owned, 0
    nodes[less - n0].links[INT][0].node = owned
    # yes -> the third slot, no -> the checking chest's answer
    select = new(t_select, 'slot')
    s = nodes[select - n0]
    s.inputs['bool'][0].node, s.inputs['bool'][0].param = less, 0
    s.inputs['string'][0].value = THIRD_KEY
    s.inputs['string'][1].node, s.inputs['string'][1].param = at['select'], 0
    s.links[VALUE][0].node, s.links[STRING][0].node = less, at['select']

    def pre(i):                                     # the place of a node among the nodes others wait for
        return sum(1 for x in (doc.nodes + nodes)[:i] if x.flags & 1)

    nodes[less - n0].preconditions = [pre(owned)]
    s.preconditions = [pre(less), pre(at['select'])]
    doc.nodes += nodes
    # the two changes to the game's nodes
    doc.nodes[at['make']].links[FLOW].append(ainb.Link(create, '', ()))
    module = doc.nodes[at['module']]
    was = pre(at['select'])
    if module.preconditions.count(was) != 1:
        raise SystemExit('%s: the chest module does not wait for its slot name as expected' % ai_path(BASE))
    key = [x for x in module.inputs['string'] if x.name == 'HolderKey'][0]
    key.node, key.param = select, 0
    module.links[STRING][0].node = select
    module.preconditions = [pre(select) if p == was else p for p in module.preconditions]
    doc.filename = name + '.root'
    data = doc.write()

    # read back
    back, orig = ainb.loads(data), ainb.loads(base)
    reached = _reached(orig)
    if back.write() != data or back.filename != name + '.root' or len(back.nodes) != n0 + len(nodes) \
            or _doc_state(back) != _doc_state(orig):
        raise SystemExit('read-back: %s differs from what was intended' % ai_path(name))
    for i, (o, b) in enumerate(zip(orig.nodes, back.nodes)):
        if i == at['make']:
            o.links[FLOW].append(ainb.Link(create, '', ()))
        if i == at['module']:
            k = [x for x in o.inputs['string'] if x.name == 'HolderKey'][0]
            k.node, k.param = select, 0
            o.links[STRING][0].node = select
            o.preconditions = [pre(select) if p == was else p for p in o.preconditions]
        if _node_state(o) != _node_state(b):
            raise SystemExit('read-back: node %d of %s differs from what was intended' % (i, ai_path(name)))
    for k, n in enumerate(nodes):
        if _node_state(back.nodes[n0 + k]) != _node_state(n):
            raise SystemExit('read-back: new node %d of %s differs from what was intended' % (n0 + k, ai_path(name)))
    if _reached(back) != reached | set(range(n0, n0 + len(nodes))):
        raise SystemExit('read-back: %s: nodes that nothing leads to' % ai_path(name))
    want = describe(data)
    if (want['second'], want['third'], want['key'], want['new']) != (second, third, THIRD_KEY, len(nodes)):
        raise SystemExit('read-back: the third level of %s is not as intended: %r' % (ai_path(name), want))
    return data


def describe(data):
    """what a three-level chest's AI does, read from the file by following its links: {'name', 'new' (nodes
    after the game's 101), 'key' (the third slot), 'third' (the actor made in it), 'second' (the name whose
    owning gives the third slot), 'else' (the two slots the checking chest's own choice gives: Link doesn't
    have / has the item of the map setting), 'check' (where that choice's name comes from: the number of the
    global parameter)}. Raises SystemExit when the file is not the one chest_ai makes."""
    doc = ainb.loads(data)
    nodes = doc.nodes
    pre = [i for i, n in enumerate(nodes) if n.flags & 1]

    def bad(what):
        raise SystemExit('%s: %s' % (doc.filename, what))

    def waits(i, *sources):
        if sorted(pre[p] for p in nodes[i].preconditions) != sorted(sources):
            bad('node %d does not wait for the nodes it reads' % i)

    module = _one(doc, 'the chest module', lambda n: n.name == N_MODULE)
    key = [x for x in nodes[module].inputs['string'] if x.name == 'HolderKey'][0]
    top = key.node
    if top < BASE_NODES or key.param != 0 or key.flags or [l.node for l in nodes[module].links[STRING]] != [top] \
            or top not in [pre[p] for p in nodes[module].preconditions]:
        bad('the chest module does not take its slot name from a new node')
    s = nodes[top]
    b, a, rest = s.inputs['bool'][0], s.inputs['string'][0], s.inputs['string'][1]
    if s.name != Q_SELECT or not _fixed(a) or a.flags != FIXED or rest.node < 0 or rest.node >= BASE_NODES \
            or rest.param != 0 or b.node < BASE_NODES or b.param != 0 or b.flags or rest.flags \
            or [(l.node, l.name) for l in s.links[VALUE]] != [(b.node, 'Bool')] \
            or [(l.node, l.name) for l in s.links[STRING]] != [(rest.node, 'B')]:
        bad('the slot name is not "the third slot or the checking chest\'s answer"')
    waits(top, b.node, rest.node)
    ls = nodes[b.node]
    if ls.name != Q_LESS or not _fixed(ls.inputs['int'][0]) or ls.inputs['int'][0].value != 0 \
            or ls.inputs['int'][1].node < BASE_NODES or ls.inputs['int'][1].param != 0 \
            or [(l.node, l.name) for l in ls.links[INT]] != [(ls.inputs['int'][1].node, 'S32Base')]:
        bad('the third slot is not chosen on "0 < a number"')
    waits(b.node, ls.inputs['int'][1].node)
    q = nodes[ls.inputs['int'][1].node]
    if q.name != Q_OWNED or not _fixed(q.inputs['string'][0]) or [x.name for x in q.outputs['int']] != ['Num'] \
            or any(q.links) or q.preconditions:
        bad('the number is not the inventory\'s for a fixed name')
    # the checking chest's own choice, as the game's file has it
    game = nodes[rest.node]
    xor = nodes[game.inputs['bool'][0].node]
    g_less = nodes[xor.inputs['bool'][0].node] if xor.name == Q_XOR else None
    g_owned = nodes[g_less.inputs['int'][1].node] if g_less is not None and g_less.name == Q_LESS else None
    if game.name != Q_SELECT or g_owned is None or g_owned.name != Q_OWNED \
            or not g_owned.inputs['string'][0].flags >> 31:
        bad('the checking chest\'s own choice is not as expected')
    slots = [nodes[x.node].inputs['string'][1].value for x in game.inputs['string']]
    # the third slot is made with the other two
    made = [i for i in range(BASE_NODES, len(nodes)) if nodes[i].name == N_CREATE]
    if len(made) != 1 or nodes[made[0]].inputs['string'][1].value != a.value \
            or not all(_fixed(x) for t in ainb.PARAM_TYPES for x in nodes[made[0]].inputs[t]) \
            or nodes[made[0]].inputs['int'][0].value != 0:
        bad('the third slot is not made from a fixed name')
    parents = [i for i, n in enumerate(nodes) if made[0] in [l.node for l in n.links[FLOW]]]
    if len(parents) != 1 or nodes[parents[0]].type != SIMULTANEOUS or parents[0] >= BASE_NODES \
            or [nodes[l.node].type for l in nodes[parents[0]].links[FLOW]] != [STRING_SELECTOR, STRING_SELECTOR, 0]:
        bad('the third slot is not made where the other two are')
    if len(nodes) - BASE_NODES != 4 or sorted([made[0], top, b.node, ls.inputs['int'][1].node]) != list(
            range(BASE_NODES, len(nodes))):
        bad('new nodes other than the four expected')
    return {'name': doc.filename, 'new': len(nodes) - BASE_NODES, 'key': a.value,
            'third': nodes[made[0]].inputs['string'][0].value, 'second': q.inputs['string'][0].value,
            'else': tuple(slots), 'check': g_owned.inputs['string'][0].flags & 0xffff}


def light_rigs(data, names):
    """the game's list of chest lights (LIGHT_RIGS) with one entry more for each chest of ours (`names`: our
    actors), a copy of the entry of the checking chest it is made from, added at the end; read back: the
    game's entries are as they were"""
    doc = byml.loads(data)
    rigs = doc.root.get('LightRigSettingList')
    if set(doc.root) != {'LightRigSettingList'} or not rigs:
        raise SystemExit('%s: not the list of lights expected' % LIGHT_RIGS)
    by_actor = {}
    for e in rigs:
        by_actor.setdefault(e.get('Actor'), []).append(e)
    added = []
    for name in names:
        base = BASE + (NOBAKE if name.endswith(NOBAKE) else '')
        if not name.startswith(PREFIX) or _work(ap_path(name)) in by_actor:
            raise SystemExit('%s: not a chest of ours, or already in %s' % (name, LIGHT_RIGS))
        if len(by_actor.get(_work(ap_path(base)), ())) != 1:
            raise SystemExit('%s: no entry, or more than one, for %s' % (LIGHT_RIGS, base))
        entry = type(by_actor[_work(ap_path(base))][0])(by_actor[_work(ap_path(base))][0])
        entry['Actor'] = type(entry['Actor'])(_work(ap_path(name)))
        added.append(entry)
    doc.root = type(doc.root)(doc.root)
    doc.root['LightRigSettingList'] = list(rigs) + added
    new = byml.dumps(doc)
    back, old = byml.loads(new).root['LightRigSettingList'], byml.loads(data).root['LightRigSettingList']
    if list(back[:len(old)]) != list(old) or len(back) != len(old) + len(names) \
            or [dict(e) for e in back[len(old):]] != [dict(e) for e in added]:
        raise SystemExit('read-back: %s differs from what was intended' % LIGHT_RIGS)
    return new


def build(tag, second, third, read_pack, read_table_rows, nobake=False):
    """the three-level chest of the family `tag`: second: the second level's own name (what the AI asks the
    inventory about), third: the third level's actor as a chest gives it (what the AI makes in the third slot).
    nobake: the twin that takes the place of Obj_TBox_A_01_NoBake.
    Returns (name, pack data, {inner path: (data, the game file it is made from: its size entry's reference)}
    for the files new to the game, {table: new row})."""
    own, name = chest_name(tag), chest_name(tag, nobake)
    base = BASE + (NOBAKE if nobake else '')
    arc = sarc.Sarc.read(read_pack(pack_path(base)))
    files = dict(arc.files)
    align = dict(arc.align)
    new_inner = {}

    def add(path, data, like):
        new_inner[path] = (data, like)
        files[path] = data
        align[path] = arc.align.get(like, 8)

    # the checking chest's own parts, as the game has them
    want = {'$parent': _work(ap_path(PLAIN)), 'Components': {
        'AIInfoRef': '?' + ai_info_path(BASE), 'ActorHolderRef': '?' + holder_path(BASE),
        'AffiliationRef': '?Component/AffiliationParam/ObjectCommon.game__component__AffiliationParam.bgyml',
        'DropRef': '?' + drop_param_path(BASE)}}
    adoc = byml.loads(files[ap_path(BASE)])
    if adoc.root != want:
        raise SystemExit('%s: its actor file is not as expected' % BASE)
    idoc = byml.loads(files[ai_info_path(BASE)])
    if dict(idoc.root) != {'RootAIRef': 'Work/AI/Root/%s.root.ain' % BASE}:
        raise SystemExit('%s not as expected' % ai_info_path(BASE))
    hdoc = byml.loads(files[holder_path(BASE)])
    slot = hdoc.root.get('ActorHoldSettings', {}).get(SECOND_KEY)
    parent = byml.loads(files[holder_path('Obj_TBox')]).root
    if set(hdoc.root) != {'$parent', 'ActorHoldSettings'} or hdoc.root['$parent'] != _work(holder_path('Obj_TBox')) \
            or list(hdoc.root['ActorHoldSettings']) != [SECOND_KEY] or 'Actor' in slot \
            or 'Content' not in parent['ActorHoldSettings'] or THIRD_KEY in parent['ActorHoldSettings'] \
            or dict(slot) != {k: v for k, v in parent['ActorHoldSettings']['Content'].items()}:
        raise SystemExit('%s: its held actors are not the small chest\'s plus %s, a copy of Content, as expected'
                         % (BASE, SECOND_KEY))

    # the AI: the checking chest's own, with the third level
    shared = sarc.Sarc.read(read_pack(AI_PACK)).files
    for p in SOURCES.values():
        if p not in shared:
            raise SystemExit('%s: no %s' % (AI_PACK, p))
    ai_data = chest_ai(files[ai_path(BASE)], {k: shared[p] for k, p in SOURCES.items()}, own, second, third)
    idoc.root = type(idoc.root)(idoc.root)
    idoc.root['RootAIRef'] = type(idoc.root['RootAIRef'])('Work/AI/Root/%s.root.ain' % own)
    add(ai_info_path(own), byml.dumps(idoc), ai_info_path(BASE))
    add(ai_path(own), ai_data, ai_path(BASE))
    # the held actors: the checking chest's, and the third slot with the second's settings
    hdoc.root = type(hdoc.root)(hdoc.root)
    slots = type(hdoc.root['ActorHoldSettings'])(hdoc.root['ActorHoldSettings'])
    slots[THIRD_KEY] = type(slot)(slot)
    hdoc.root['ActorHoldSettings'] = slots
    add(holder_path(own), byml.dumps(hdoc), holder_path(BASE))
    # the actor: the small chest with the checking chest's four parts, two of them ours
    adoc.root = type(adoc.root)(adoc.root)
    comp = type(adoc.root['Components'])(adoc.root['Components'])
    comp['AIInfoRef'] = type(comp['AIInfoRef'])('?' + ai_info_path(own))
    comp['ActorHolderRef'] = type(comp['ActorHolderRef'])('?' + holder_path(own))
    adoc.root['Components'] = comp
    add(ap_path(own), byml.dumps(adoc), ap_path(BASE))
    for p in (ap_path(BASE), ai_info_path(BASE), ai_path(BASE), holder_path(BASE)):
        del files[p]                                # the checking chest's own: nothing of ours names them
        del align[p]
    if nobake:
        # the twin: our chest with the game's model settings for it (nothing in them names the actor)
        ndoc = byml.loads(files[ap_path(base)])
        if ndoc.root != {'$parent': _work(ap_path(BASE)), 'Components': {
                'ModelInfoRef': '?' + model_info_path(base)}} \
                or byml.loads(files[model_info_path(base)]).root != {'$parent': _work(model_info_path(PLAIN))}:
            raise SystemExit('%s: its actor file is not as expected' % base)
        ndoc.root = type(ndoc.root)(ndoc.root)
        ndoc.root['$parent'] = type(ndoc.root['$parent'])(_work(ap_path(own)))
        add(ap_path(name), byml.dumps(ndoc), ap_path(base))
        del files[ap_path(base)]
        del align[ap_path(base)]

    # every file the actor's settings name is in the pack, as far as the game's pack holds them (names and
    # system settings are kept outside it), and nothing of the checking chest's own is left that ours replace
    named, todo = set(), [ap_path(name), ai_path(own)]
    while todo:
        p = todo.pop()
        if p in named:
            continue
        named.add(p)
        if p in files and p.endswith('.bgyml'):
            todo += _refs(byml.loads(files[p]).root)
    missing = sorted(p for p in named if p not in files and (p in arc.files or p in new_inner))
    left = sorted(p for p in files if p not in named and p not in arc.files)
    if missing or left or any(p in files for p in (ap_path(BASE), ai_path(BASE), holder_path(BASE))):
        raise SystemExit('%s: files missing from the pack (%s) or left in it (%s)'
                         % (name, ', '.join(missing), ', '.join(left)))

    out = sarc.Sarc.read(read_pack(pack_path(base)))  # the game pack's own layout settings
    out.files = files
    out.align = {p: align.get(p, 8) for p in files}
    pack = out.write()

    # the rows: the checking chest's, under our name; memory: the second slot and the checking AI cost the game
    # this much over the small chest, and the third slot and four nodes more are given as much again
    rows = {}
    for t in ('ActorInfo', 'GameActorInfo'):
        by_id = {r['__RowId']: r for r in read_table_rows(t)}
        if name in by_id or base not in by_id:
            raise SystemExit('%s: table %s is not as expected' % (name, t))
        row = type(by_id[base])(by_id[base])
        row['__RowId'] = type(row['__RowId'])(name)
        if t == 'ActorInfo':
            plain = by_id[PLAIN + (NOBAKE if nobake else '')]
            if {k: v for k, v in row.items() if k not in ('__RowId', 'InstanceHeapSize', 'PreActorRenderInfoHeapSize')} \
                    != {k: v for k, v in plain.items() if k not in ('__RowId', 'InstanceHeapSize',
                                                                    'PreActorRenderInfoHeapSize')}:
                raise SystemExit('%s: the checking chest\'s row is not the small chest\'s but for its memory' % base)
            extra = int(row['InstanceHeapSize']) - int(plain['InstanceHeapSize'])
            if extra <= 0:
                raise SystemExit('%s: needs no more memory than the small chest: not expected' % base)
            row['InstanceHeapSize'] = type(row['InstanceHeapSize'])(int(row['InstanceHeapSize']) + extra)
        rows[t] = row

    # read back
    back = sarc.Sarc.read(pack)
    if set(back.files) != set(files) or any(back.files[p] != d for p, d in files.items()):
        raise SystemExit('read-back: pack of %s differs from what was intended' % name)
    got = resolved_components(back.files, name)
    base_comp = resolved_components(arc.files, base)
    if {k: v for k, v in got.items() if k not in ('AIInfoRef', 'ActorHolderRef')} \
            != {k: v for k, v in base_comp.items() if k not in ('AIInfoRef', 'ActorHolderRef')} \
            or got['AIInfoRef'] != '?' + ai_info_path(own) or got['ActorHolderRef'] != '?' + holder_path(own) \
            or byml.loads(back.files[ai_info_path(own)]).root['RootAIRef'] != 'Work/AI/Root/%s.root.ain' % own \
            or describe(back.files[ai_path(own)])['name'] != own + '.root':
        raise SystemExit('read-back: %s is not the checking chest with an AI and held actors of its own' % name)
    held = byml.loads(back.files[holder_path(own)]).root
    if list(held['ActorHoldSettings']) != [SECOND_KEY, THIRD_KEY] \
            or held['ActorHoldSettings'][THIRD_KEY] != held['ActorHoldSettings'][SECOND_KEY] \
            or held['$parent'] != _work(holder_path('Obj_TBox')):
        raise SystemExit('read-back: the held actors of %s differ' % name)
    return name, pack, new_inner, rows
