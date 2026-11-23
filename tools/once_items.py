"""One-time drops: what a rock, a bush or a pot drops for us is given once (to test in game).

The problem: rocks, bushes and pots come back. Their saved flag is reset (`SupplyObject`, reset type 88), and
what they drop is only a map setting, so the item came out again each time. With a progressive family the rock
that had given the first level gave the second when it was back.

Found in the game's files and code (2026-11-22, out/RESEARCH_pots_one_time.md):
- every placement of a rock, a bush or a pot has two saved flags in `GameData/GameDataList` (`Bool64bitKey`):
  one under its placement hash (reset type 88: "gone until the area is loaded again") and one under that hash
  with bit 1 turned round (hash ^ 2), reset type 24: never reset. 1,727 of the game's 2,444 type-88 flags have
  that partner, and every rock, bush and pot check that drops something does (the build checks it);
- the Gold Skulltula's token sets both flags of the skulltula that dropped it: its AI runs
  `OneShotGoldTokenDeadAfter` when it is picked up (death reason 10), and that node (read in the game's code)
  takes a 64-bit number from the item's own blackboard (`GoldTokenGmdHash`) and, when it is not 0, sets the flag
  under that number and the flag under that number ^ 2. The skulltula's AI puts its placement's number there for
  whatever it drops: `QueryGenericMakeOverwriteParam` -> `QueryBlackboardOverwriteParamAddNoRespawnGmdHash {Key:
  GoldTokenGmdHash}` -> `OneShotDropSetOverWriteParam` (seen in game with our Gold Skulltula drops);
- the Piece of Heart is built the same way on the ground items' own AI: `Obj_Heart_Piece.root` is
  `DropItem.root` (the same 13 nodes) plus "dead of reason 10 -> `OneShotHeartPieceTakenDeadAfter`", and its
  blackboard has one 64-bit number (`RespawnGmdHash`, table `DropActorRespawnData`). That node does the same as
  the token's (read in the code). Nothing in the game fills that number, so the token's node and key are used;
- an AI reads a text of its actor's blackboard with `QueryBlackboardGetString {BlackboardType: 1}` (Dampe), asks
  "does it start with" with `QueryGenericStringStartsWith` (the chests' local module, about what they drop) and
  writes such a text with `ExecuteBlackboardSetString {BlackboardType: 1}` (the Like Like writes
  `Drop__DropTableOverWrite`, a neighbour of `Drop__DropActor` in the same table). `Drop__DropActor` is a text
  of the rock's, the bush's and the pot's own blackboard (`String128`, set by the placement);
- not usable (read in the code, 2026-11-22): no AI node reads the hash ^ 2 flag. `QueryInstanceGameDataGetBool`
  (the cow skulls' and hanging signs' "done already?") only works for actors with an
  `InstanceGameParameterSetting` (the signs' `Once`), which no rock, bush or pot has; and what it reads is a
  named flag (`InstanceGameParameter_<placement hash>`, the signs have one each), not hash ^ 2. Rocks, bushes and
  pots have no such named flag, and one cannot be added without changing the save file's layout.
  `QueryActorGetIsRespawn` and `OneShotActorChangeIsRespawn` read and write the flag under the placement hash
  itself (the one that is reset).

So the one-time rule is the Gold Skulltula's:

1. What we put on a rock, a bush or a pot marks its dropper. A plain item: its ground version with the mark
   (`Obj_NX2O_<item>`), or for an item that is a ground actor of the game (a rupee, a Piece of Heart) the
   Gold Skulltula drop version (`Obj_NX2_GS_<item>`, built from the token). A level of a family: its turning
   item with the mark (`Obj_NX2Q_<level>`). The mark: the token's 64-bit number in its blackboard, and in its
   AI the token's own branch "dead of reason 10 -> OneShotGoldTokenDeadAfter". A turning version also runs that
   node in the step in which it turns (what it drops then has no number, see below).
2. The rock, bush or pot gets an AI of its own name: the game's AI for it, unchanged, and one more branch that
   only does something when the drop its placement names is one of ours ("starts with Obj_NX2"): it hands its
   placement's number to what it drops (the skulltula's three nodes, as they are).
   Its actor file names that AI. Other placements of the same actor run the same file and take the "not ours"
   side, which does nothing.

   Taken out (2026-11-22, the game crashed in the in-game test): for a family the branch also named the next
   level's version as its drop while Link owned the level it would drop (`ExecuteBlackboardSetString` on
   `Drop__DropActor`). `Drop__DropActor` is an instance parameter of the actor's blackboard (`IsInstanceParam`:
   set by the placement), and the node's code (read in the game, 0x826632f0) marks such an entry with no change
   counter (-1) and then counts the change there: it reads address -1 and the game stops. It crashed in the
   first frame the Know-It-All rock (Bow family) ran with the Fairy Bow owned, before it was lifted. No AI of
   the game writes an instance parameter of an actor's blackboard (the Like Like writes
   `Drop__DropTableOverWrite`, which is not one); tests/one_time_check.py checks the game and every build for
   it, and dropper_files refuses such steps. So a family's version drops as its placement names it, and turns
   on the ground (marking its dropper) when Link already owns its level.

What the player should see: the item comes out once. Not picked up and left behind: nothing was marked, so
when the rock is back it drops it again (the level that is right then). Picked up: both flags of the rock are
set, as the token sets the skulltula's; the one under hash ^ 2 is never reset. NOT PROVEN: that the game then
does not make the rock again (a Gold Skulltula marked so stays gone, but its first flag is never reset either,
so that does not tell which flag keeps it away). If the rock does come back, it drops its item again (the next
level for a family), as before this change: the in-game test decides (out/RESEARCH_pots_one_time.md).

Not handed on: a number given to a drop cannot be given to what that drop drops (no node reads 64 bits back).
So a turning version that turns (Link owned its level when the rock was broken, or got it somewhere else while
it lay there) marks its dropper at that moment, and the next level lies there as an ordinary turning item. If
that one is left behind, the rock has nothing more to give.

Every new node is a copy of a game node of the same type, found by what it is and checked before it is used;
new nodes go after the file's own, so no node number changes.
"""
import copy
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml, ainb  # noqa: E402
import ground_items  # noqa: E402
import turn_items  # noqa: E402
from ground_items import pack_path, ap_path, _ref_path, resolved_components  # noqa: E402
from shop_items import ai_path, ai_info_path, _node_state, _doc_state  # noqa: E402

KINDS = ('rock', 'bush', 'pot')                   # the kinds of check whose drop is given once
PLAIN, TURN = 'once', 'once_turn'                 # the kinds of version in ground_items.VERSIONS
PLAIN_PREFIX = ground_items.VERSIONS[PLAIN][2]    # Obj_NX2O_
PREFIX = ground_items.VERSIONS[TURN][2]           # Obj_NX2Q_
OURS = 'Obj_NX2'                                  # what every drop of ours on these kinds starts with
AI_PREFIX = 'NX2_Once_'                           # the AI of a turning version with the mark
PLAIN_AI = 'NX2_Once'                             # the AI of a plain item with the mark (one for all)
DROP_AI_PREFIX = 'NX2_Drop_'                      # the AI of a rock, a bush or a pot that drops once
KEY = ground_items.TOKEN_KEY                      # GoldTokenGmdHash
DROP_KEY = 'Drop__DropActor'
AI_PACK = turn_items.AI_PACK
TOKEN_AI = ground_items.TOKEN_FILES[0]            # the token's AI: its "picked up" branch
TOKEN_TABLE = ground_items.TOKEN_FILES[1]         # its blackboard table: the 64-bit number
HEART = 'Obj_Heart_Piece'                         # a ground item with one 64-bit number: its table's shape
HEART_TABLE = ('Component/Blackboard/BlackboardParamTable/'
               'DropActorRespawnData.engine__component__BlackboardParamTable.bgyml')
BASE_INFO = 'Component/Blackboard/BlackboardInfo/Obj_Item_Base.engine__component__BlackboardInfo.bgyml'
TABLE = 'Component/Blackboard/BlackboardParamTable/NX2_Once.engine__component__BlackboardParamTable.bgyml'
INFO = 'Component/Blackboard/BlackboardInfo/NX2_Once.engine__component__BlackboardInfo.bgyml'
# where the nodes that are not in the shared AI pack are copied from: (actor pack, file)
HAND = ('Enemy_Skulltula_Gold', 'AI/Enemy_Skulltula_Gold.utility.root.ainb')        # the hand-over
NAMED = ('Npc_Hylia_Dampe_001', 'AI/Npc_Hylia_Dampe_001.event.root.ainb')           # QueryBlackboardGetString
WRITE = ('Enemy_LikeLike', 'AI/Enemy_LikeLike.utility.root.ainb')                   # ExecuteBlackboardSetString
STARTS = 'AI/_LocalModule_46ad10eacd08.module.ainb'                                 # QueryGenericStringStartsWith
ACTOR_SOURCES = {'hand': HAND, 'named': NAMED, 'write': WRITE,
                 'token': (ground_items.TOKEN, TOKEN_AI)}
SHARED_SOURCES = dict(turn_items.SOURCES, base=ai_path(turn_items.BASE_AI), starts=STARTS)

S32_SELECTOR, SEQUENTIAL, SIMULTANEOUS, BOOL_SELECTOR, SPLIT_TIMING = 1, 2, 3, 7, 500
VALUE, FLOW, STRING, INT = 0, 2, 4, 5             # link types (formats/ainb.py)
PICKED_UP = 10                                    # the death reason of a pick-up
FLAG_RESET = 88                                   # the reset type of a rock's, a bush's or a pot's own flag
N_MARK, N_SIGNAL, Q_DEAD = 'OneShotGoldTokenDeadAfter', 'ExecuteDeathSignalDeathProcedure', 'QueryDeathIsDead'
N_HAND, Q_HASH, Q_MAKE = ('OneShotDropSetOverWriteParam', 'QueryBlackboardOverwriteParamAddNoRespawnGmdHash',
                          'QueryGenericMakeOverwriteParam')
Q_NAMED, Q_STARTS = 'QueryBlackboardGetString', 'QueryGenericStringStartsWith'
N_WRITE, Q_OWNED = 'ExecuteBlackboardSetString', turn_items.Q_OWNED
N_VALID, N_DROP, N_DELETE, N_IDLE = turn_items.N_VALID, turn_items.N_DROP, turn_items.N_DELETE, turn_items.N_IDLE
FIXED = 0x800000                                  # an input whose value is set in the file
ACTOR_BLACKBOARD = 1                              # BlackboardType: the actor's own blackboard


def once_name(item):
    """the turning version with the mark of a family's level"""
    return ground_items.ground_name(item, TURN)


def plain_name(item):
    """the ground version with the mark of an item"""
    return ground_items.ground_name(item, PLAIN)


def ai_name(item):
    return AI_PREFIX + (item[5:] if item.startswith('Item_') else item)


def sources(read_pack):
    """{key: AI file} of every game AI the new nodes are copied from (read once per build)"""
    shared = sarc.Sarc.read(read_pack(AI_PACK)).files
    out = {}
    for k, p in SHARED_SOURCES.items():
        if p not in shared:
            raise SystemExit('%s: no %s' % (AI_PACK, p))
        out[k] = shared[p]
    for k, (actor, p) in ACTOR_SOURCES.items():
        d = sarc.Sarc.read(read_pack(pack_path(actor))).files.get(p)
        if d is None:
            raise SystemExit('%s: no %s in its pack' % (actor, p))
        out[k] = d
    return out


def _plain(n):
    return not n.attachments and not n.exb_count and not n.exb_size


def _imm(n):
    return [(t, x.name, x.value) for t in ainb.PARAM_TYPES for x in n.immediates[t]]


def _one(doc, what, ok):
    hits = [i for i, n in enumerate(doc.nodes) if ok(n)]
    if not hits:
        raise SystemExit('%s: no %s found as expected (game files differ from what this was made for)'
                         % (doc.filename, what))
    return hits[0]


def _reached(doc):
    seen, todo = set(), [c.left for c in doc.commands]
    while todo:
        i = todo.pop()
        if i in seen:
            continue
        seen.add(i)
        n = doc.nodes[i]
        todo += [l.node for links in n.links for l in links if l.name is not None]
        todo += [x.node for t in ainb.PARAM_TYPES for x in n.inputs[t] if x.node >= 0]
        todo += [s[0] for t in ainb.PARAM_TYPES for x in n.inputs[t] if x.sources for s in x.sources]
    return seen


class _Adder:
    """adds nodes after a file's own: copies of game nodes (one, or a group that keeps its links)"""

    def __init__(self, doc, name):
        self.doc, self.name, self.n0, self.nodes, self.wants = doc, name, len(doc.nodes), [], {}

    def node(self, i):
        return self.nodes[i - self.n0] if i >= self.n0 else self.doc.nodes[i]

    def new(self, template, what):
        n = copy.deepcopy(template)
        if not _plain(n) or any(x.flags >> 31 for kind in ('immediates', 'inputs') for t in ainb.PARAM_TYPES
                                for x in getattr(n, kind)[t]) or n.links[3]:
            raise SystemExit('%s: a node copied for "%s" (%s) is not a plain one' % (self.name, what, n.name))
        n.guid = hashlib.md5(('NX2-ZOOTR %s %s' % (self.name, what)).encode()).digest()
        n.precondition_slot = None
        n.preconditions = []
        if any(bytes(x.guid) == n.guid for x in self.doc.nodes + self.nodes):
            raise SystemExit('%s: node id already used (%s)' % (self.name, what))
        self.nodes.append(n)
        return self.n0 + len(self.nodes) - 1

    def group(self, src, indices, what):
        """copies of the nodes `indices` of the AI `src`, linked to each other as they are there: {number
        there: number here}. Every node they link to or read from must be in the group."""
        indices = list(indices)
        flagged = [i for i, n in enumerate(src.nodes) if n.flags & 1]
        to = {}
        for i in indices:
            to[i] = self.new(src.nodes[i], '%s %d' % (what, i))
        for i in indices:
            n = self.node(to[i])
            try:
                for t in ainb.PARAM_TYPES:
                    for x in n.inputs[t]:
                        if x.sources:
                            raise KeyError('several sources')
                        if x.node >= 0:
                            x.node = to[x.node]
                for links in n.links:
                    for l in links:
                        l.node = to[l.node]
                self.wants[to[i]] = [to[flagged[p]] for p in src.nodes[i].preconditions]
            except KeyError as e:
                raise SystemExit('%s: the nodes copied for "%s" lead outside themselves (%s)' % (self.name, what, e))
        return to

    def ask(self, where, query, param, param_type):
        """point a selector's one input at an output of a query node (as its only link of that kind)"""
        n = self.node(where)
        x = n.inputs[param_type]
        if len(x) != 1 or x[0].name != 'Input':
            raise SystemExit('%s: a selector without the one input expected' % self.name)
        x[0].node, x[0].param = query, param
        n.links[VALUE if param_type == 'bool' else INT] = [ainb.Link(query, 'Input', (0, 0))]
        self.wants[where] = [query]

    def flow(self, where, *children):
        n = self.node(where)
        if len(n.links[FLOW]) != len(children):
            n.links[FLOW] = [copy.deepcopy(n.links[FLOW][0]) for _ in children]
        for l, c in zip(n.links[FLOW], children):
            l.node = c

    def done(self):
        """the new nodes join the file; what each waits for is numbered as the file does (the place of a node
        among the nodes others wait for)"""
        every = self.doc.nodes + self.nodes
        for i, wanted in self.wants.items():
            self.node(i).preconditions = [sum(1 for x in every[:w] if x.flags & 1) for w in wanted]
        self.doc.nodes += self.nodes
        return len(self.nodes)


def _templates(src):
    """the single nodes copied, found by what they are: {name: node}"""
    base, counter, owned = (ainb.loads(src[k]) for k in ('base', 'counter', 'owned'))
    sel_imm = [('int', 'CalculateTiming', 0), ('bool', 'ChildFrameSync', False), ('bool', 'InputValue', False),
               ('bool', 'IsNoSelectWhenChildBusy', False)]
    t = {'bool': turn_items._element(base, BOOL_SELECTOR, sel_imm, [('True', ()), ('False', ())], other=(VALUE,)),
         'idle': turn_items._action(base, N_IDLE, [('bool', 'ExecuteEveryFrame', False)]),
         'int': turn_items._element(counter, S32_SELECTOR, [
             ('int', 'CalculateTiming', 0), ('int', 'InputValue', 0), ('bool', 'ChildFrameSync', False),
             ('bool', 'IsNoSelectIfSameInstance', False), ('bool', 'IsNoSelectWhenChildBusy', False)],
             [('', (0, 0)), ('', (0, 0))], other=(INT,))}
    t['owned'], p = turn_items._query(owned, Q_OWNED, 'int', 'Num')
    if p != 0 or len(t['bool'].inputs['bool']) != 1 or len(t['int'].inputs['int']) != 1:
        raise SystemExit('the game\'s selectors are not as expected')
    for k in ('bool', 'int'):                       # a selector's own question is replaced: start with none
        n = copy.deepcopy(t[k])
        for links in (n.links[VALUE], n.links[INT]):
            del links[:]
        x = n.inputs['bool' if k == 'bool' else 'int'][0]
        x.node, x.param = -1, 0
        t[k] = n
    token = ainb.loads(src['token'])
    t['all'] = token.nodes[_one(token, 'an "all at once" node', lambda n: (
        n.type == SIMULTANEOUS and n.flags == 0 and _plain(n) and not n.preconditions
        and _imm(n) == [('int', 'EndPolicy', 0), ('int', 'ResultPolicy', 0)]
        and all(not l.name and not l.extra for l in n.links[FLOW])
        and not any(links for k, links in enumerate(n.links) if k != FLOW)))]
    t['mark'] = turn_items._action(token, N_MARK, [('bool', 'ExecuteEveryFrame', False)])
    named = ainb.loads(src['named'])
    t['named'] = named.nodes[_one(named, Q_NAMED, lambda n: (
        n.name == Q_NAMED and n.type == 0 and n.flags == 1 and _plain(n) and not any(n.links)
        and not n.preconditions and [(k, x.name) for k in ainb.PARAM_TYPES for x in n.immediates[k]] == [
            ('int', 'BlackboardType'), ('bool', 'OutputOnlyOnEnter'), ('string', 'BlackboardKey')]
        and n.immediates['int'][0].value == ACTOR_BLACKBOARD and not n.immediates['bool'][0].value
        and [(k, x.name, x.flag) for k in ainb.PARAM_TYPES for x in n.outputs[k]] == [('string', 'String', True)]
        and not any(n.inputs[k] for k in ainb.PARAM_TYPES)))]
    starts = ainb.loads(src['starts'])
    t['starts'] = starts.nodes[_one(starts, Q_STARTS, lambda n: (
        n.name == Q_STARTS and n.type == 0 and n.flags == 1 and _plain(n)
        and _imm(n) == [('bool', 'OutputOnlyOnEnter', False)]
        and [(k, x.name) for k in ainb.PARAM_TYPES for x in n.inputs[k]] == [('string', 'Input'), ('string', 'Token')]
        and n.inputs['string'][0].node >= 0 and not n.inputs['string'][0].flags
        and n.inputs['string'][1].node < 0 and n.inputs['string'][1].flags == FIXED
        and [(k, x.name, x.flag) for k in ainb.PARAM_TYPES for x in n.outputs[k]] == [('bool', 'Result', True)]
        and [(k, [(l.name, l.extra) for l in links]) for k, links in enumerate(n.links) if links] == [
            (STRING, [('Input', ())])]))]
    write = ainb.loads(src['write'])
    t['write'] = write.nodes[_one(write, N_WRITE, lambda n: (
        n.name == N_WRITE and n.type == 0 and n.flags == 0 and _plain(n) and not any(n.links)
        and not n.preconditions and [(k, x.name, x.value) for k in ('int', 'bool') for x in n.immediates[k]] == [
            ('int', 'BlackboardType', ACTOR_BLACKBOARD), ('bool', 'ExecuteOnce', False),
            ('bool', 'IsIgnoreNotExistsError', False)]
        and [x.name for x in n.immediates['string']] == ['BlackboardKey']
        and n.immediates['string'][0].value.startswith('Drop__')
        and [(k, x.name) for k in ainb.PARAM_TYPES for x in n.inputs[k]] == [('string', 'String')]
        and n.inputs['string'][0].node < 0 and n.inputs['string'][0].flags == FIXED
        and not any(n.outputs[k] for k in ainb.PARAM_TYPES)))]
    return t


def _picked_up(token):
    """the token's own "picked up" branch: (the numbers of its nodes, the node it starts at). Read from the
    token's AI by what it is: under the root, "dead?" -> by reason: 10 -> the mark and the death signal at
    once, any other -> nothing; not dead -> nothing."""
    nodes = token.nodes

    def bad(what):
        raise SystemExit('%s: %s (game files differ from what this was made for)' % (token.filename, what))

    root = nodes[token.commands[0].left]
    tops = [l.node for l in root.links[FLOW] if nodes[l.node].type == BOOL_SELECTOR]
    if root.type != SIMULTANEOUS or len(tops) != 1:
        bad('no single yes/no question under its root')
    top = nodes[tops[0]]
    kids = {l.name: l.node for l in top.links[FLOW]}
    q = top.inputs['bool'][0].node
    if sorted(kids) != ['False', 'True'] or q < 0 or nodes[q].name != Q_DEAD \
            or nodes[q].outputs['bool'][top.inputs['bool'][0].param].name != 'IsDead':
        bad('its question is not "am I dead"')
    by = nodes[kids['True']]
    x = by.inputs['int'][0] if by.type == S32_SELECTOR and by.inputs['int'] else None
    if x is None or x.node != q or nodes[q].outputs['int'][x.param].name != 'DeathReason' \
            or [l.extra for l in by.links[FLOW]] != [(0, PICKED_UP), (0, 0)] \
            or by.links[FLOW][1].node != kids['False'] or nodes[kids['False']].name != 'ExecuteGenericSetResultNone':
        bad('"dead" does not lead to "of reason %d" and nothing else' % PICKED_UP)
    both = nodes[by.links[FLOW][0].node]
    done = [l.node for l in both.links[FLOW]]
    if both.type != SIMULTANEOUS or sorted(nodes[i].name for i in done) != sorted([N_MARK, N_SIGNAL]):
        bad('picked up does not run the mark and the death signal at once')
    group = [q, tops[0], kids['True'], kids['False'], by.links[FLOW][0].node] + done
    if len(set(group)) != 7:
        bad('its "picked up" branch is not the seven nodes expected')
    return group, tops[0]


def mark_ai(data, src, name, turning=True):
    """a ground item's AI (`data`: a turning item's, or the ground items' own, DropItem.root) under the name
    `name`, with the mark: the token's "picked up" branch under its root, and (a turning item's) the mark as the
    first thing done in every step in which the item turns. Read back: the file's nodes are as they were but
    for those links."""
    doc = ainb.loads(data)
    orig = ainb.loads(data)
    token = ainb.loads(src['token'])
    t = _templates(src)
    root_i = doc.commands[0].left
    root = doc.nodes[root_i]
    if [c.name for c in doc.commands] != ['Root'] or root.type != SIMULTANEOUS \
            or any(l.name or l.extra for l in root.links[FLOW]) or doc.exb or doc.attachments or doc.resident:
        raise SystemExit('%s: not the ground items\' AI expected' % doc.filename)
    add = _Adder(doc, name)
    group, top = _picked_up(token)
    to = add.group(token, group, 'picked up')
    turns = [i for i, n in enumerate(doc.nodes) if n.type == SEQUENTIAL
             and [doc.nodes[l.node].name for l in n.links[FLOW]] == [N_VALID, N_DROP, N_DELETE]]
    if turning != bool(turns) and turning:
        raise SystemExit('%s: no step in which it turns' % doc.filename)
    marks = {i: add.new(t['mark'], 'mark, turn %d' % i) for i in (turns if turning else [])}
    added = add.done()
    root.links[FLOW].append(ainb.Link(to[top], '', ()))
    for i, m in marks.items():
        doc.nodes[i].links[FLOW].insert(0, ainb.Link(m, '', ()))
    doc.filename = name + '.root'
    out = doc.write()

    back = ainb.loads(out)
    if back.write() != out or back.filename != name + '.root' or len(back.nodes) != len(orig.nodes) + added \
            or _doc_state(back) != _doc_state(orig) or _reached(back) != set(range(len(back.nodes))):
        raise SystemExit('read-back: %s differs from what was intended' % ai_path(name))
    for i, (o, b) in enumerate(zip(orig.nodes, back.nodes)):
        if i == root_i:
            o.links[FLOW].append(ainb.Link(to[top], '', ()))
        if i in marks:
            o.links[FLOW].insert(0, ainb.Link(marks[i], '', ()))
        if _node_state(o) != _node_state(b):
            raise SystemExit('read-back: node %d of %s differs from what was intended' % (i, ai_path(name)))
    got = marks_of(out)
    if not got['picked_up'] or got['turns'] != (len(turns) if turning else 0) \
            or got['turns_marked'] != got['turns'] or got['new'] != added:
        raise SystemExit('read-back: the mark of %s is not as intended: %r' % (ai_path(name), got))
    return out


def marks_of(data):
    """where a ground item's AI marks its dropper, read from the file by following its links: {'name',
    'picked_up' (under the root: dead -> of reason 10 -> the mark, with the death signal), 'turns' (the steps
    in which it drops the next level and deletes itself), 'turns_marked' (how many of those run the mark
    first), 'marks' (the mark nodes in the file), 'new' (the nodes that lead from the "picked up" branch and
    the marks: what the mark added)}"""
    doc = ainb.loads(data)
    nodes = doc.nodes
    root = nodes[doc.commands[0].left]
    out = {'name': doc.filename, 'picked_up': False, 'turns': 0, 'turns_marked': 0,
           'marks': sum(1 for n in nodes if n.name == N_MARK), 'new': 0}
    branch = set()
    for l in root.links[FLOW]:
        top = nodes[l.node]
        if top.type != BOOL_SELECTOR or not top.inputs['bool'] or top.inputs['bool'][0].node < 0:
            continue
        q = nodes[top.inputs['bool'][0].node]
        if q.name != Q_DEAD or q.outputs['bool'][top.inputs['bool'][0].param].name != 'IsDead':
            continue
        kids = {x.name: x.node for x in top.links[FLOW]}
        by = nodes[kids.get('True', 0)]
        if by.type != S32_SELECTOR or not by.inputs['int'] or nodes[by.inputs['int'][0].node] is not q \
                or q.outputs['int'][by.inputs['int'][0].param].name != 'DeathReason':
            continue
        for x in by.links[FLOW]:
            if x.extra == (0, PICKED_UP) and nodes[x.node].type == SIMULTANEOUS and sorted(
                    nodes[y.node].name for y in nodes[x.node].links[FLOW]) == sorted([N_MARK, N_SIGNAL]):
                out['picked_up'] = True
                branch = {l.node, top.inputs['bool'][0].node, kids['True'], kids['False'], x.node} | {
                    y.node for y in nodes[x.node].links[FLOW]}
    for n in nodes:
        if n.type != SEQUENTIAL:
            continue
        names = [nodes[l.node].name for l in n.links[FLOW]]
        if names[-3:] == [N_VALID, N_DROP, N_DELETE]:
            out['turns'] += 1
            if names == [N_MARK, N_VALID, N_DROP, N_DELETE]:
                out['turns_marked'] += 1
                branch.add(n.links[FLOW][0].node)
    out['new'] = len(branch)
    out['branch'] = sorted(branch)
    return out


def unmarked(data):
    """a ground item's AI with the mark taken out again (the links to it, and the nodes it added after the
    file's own): what tools/turn_items.py made, for turn_items.describe (which knows no mark)"""
    got = marks_of(data)
    doc = ainb.loads(data)
    n0 = len(doc.nodes) - got['new']
    if not got['picked_up'] or got['branch'] != list(range(n0, len(doc.nodes))):
        raise SystemExit('%s: the mark is not the last nodes of the file as expected' % doc.filename)
    for n in doc.nodes[:n0]:
        n.links[FLOW] = [l for l in n.links[FLOW] if l.node < n0]
        if any(l.node >= n0 for links in n.links for l in links) \
                or any(x.node >= n0 for t in ainb.PARAM_TYPES for x in n.inputs[t]):
            raise SystemExit('%s: a node of the file leads to the mark otherwise than expected' % doc.filename)
    del doc.nodes[n0:]
    return doc.write()


def _blackboard(files, name, read_pack):
    """the two files that give a ground item the token's 64-bit number: a table with that one number (the
    Piece of Heart's table file with the token's entry in it), and a list of tables: the ground items' own two
    and that one. Returns {inner path: (data, the game file it is made from)}"""
    got = resolved_components(files, name).get('BlackboardRef')
    if got != '?' + BASE_INFO or BASE_INFO not in files:
        raise SystemExit('%s: its blackboard is not the ground items\' own as expected (%s)' % (name, got))
    token = sarc.Sarc.read(read_pack(pack_path(ground_items.TOKEN))).files
    heart = sarc.Sarc.read(read_pack(pack_path(HEART))).files
    if TOKEN_TABLE not in token or HEART_TABLE not in heart:
        raise SystemExit('the token\'s or the Piece of Heart\'s blackboard table is not where expected')
    number = byml.loads(token[TOKEN_TABLE]).root.get('BlackboardParamU64Array')
    tdoc = byml.loads(heart[HEART_TABLE])
    shape = tdoc.root.get('BlackboardParamU64Array')
    if not number or len(number) != 1 or number[0].get('BBKey') != KEY or set(tdoc.root) != {
            'BlackboardParamU64Array'} or len(shape) != 1 or set(shape[0]) != set(number[0]) \
            or any(shape[0][k] != number[0][k] for k in shape[0] if k != 'BBKey') or int(number[0]['InitVal']) \
            or number[0].get('IsInstanceParam'):
        raise SystemExit('the token\'s 64-bit number or the Piece of Heart\'s table is not as expected')
    tdoc.root = type(tdoc.root)(tdoc.root)
    tdoc.root['BlackboardParamU64Array'] = type(shape)([number[0]])
    idoc = byml.loads(files[BASE_INFO])
    tables = idoc.root.get('BlackboardParamTables')
    if set(idoc.root) != {'BlackboardParamTables'} or not tables:
        raise SystemExit('%s not as expected' % BASE_INFO)
    idoc.root = type(idoc.root)(idoc.root)
    idoc.root['BlackboardParamTables'] = type(tables)(list(tables) + [turn_items._work(TABLE)])
    return {TABLE: (byml.dumps(tdoc), HEART_TABLE), INFO: (byml.dumps(idoc), BASE_INFO)}


def _finish(name, pack, files, new_inner, read_pack, ai, src, turning):
    """the last steps both kinds of version share: the mark in the AI, the number in the blackboard, the pack"""
    arc = sarc.Sarc.read(pack)
    files[ai_path(ai)] = mark_ai(files[ai_path(ai)], src, ai, turning)
    new_inner[ai_path(ai)] = (files[ai_path(ai)], ai_path(turn_items.BASE_AI))
    for p, (d, like) in _blackboard(files, name, read_pack).items():
        files[p] = d
        new_inner[p] = (d, like)
    adoc = byml.loads(files[ap_path(name)])
    adoc.root = type(adoc.root)(adoc.root)
    comp = type(adoc.root['Components'])(adoc.root['Components'])
    if 'BlackboardRef' in comp:
        raise SystemExit('%s: already has a blackboard of its own' % name)
    comp['BlackboardRef'] = '?' + INFO
    adoc.root['Components'] = comp
    files[ap_path(name)] = byml.dumps(adoc)
    new_inner[ap_path(name)] = (files[ap_path(name)], new_inner[ap_path(name)][1])
    out = sarc.Sarc.read(pack)
    out.files = files
    out.align = {p: arc.align.get(p, 8) for p in files}
    pack = out.write()

    back = sarc.Sarc.read(pack).files
    got = resolved_components(back, name)
    tables = byml.loads(back[_ref_path(got['BlackboardRef'])]).root['BlackboardParamTables']
    if set(back) != set(files) or any(back[p] != d for p, d in files.items()) \
            or got.get('AIInfoRef') != '?' + ai_info_path(ai) or got.get('BlackboardRef') != '?' + INFO \
            or list(tables) != list(byml.loads(back[BASE_INFO]).root['BlackboardParamTables']) + [
                turn_items._work(TABLE)] \
            or [x['BBKey'] for x in byml.loads(back[TABLE]).root['BlackboardParamU64Array']] != [KEY] \
            or byml.loads(back[ai_info_path(ai)]).root['RootAIRef'] != 'Work/AI/Root/%s.root.ain' % ai \
            or not marks_of(back[ai_path(ai)])['picked_up']:
        raise SystemExit('read-back: the mark of %s differs from what was intended' % name)
    return pack


def build(family, level, read_pack, read_table_rows, model_exists=lambda project: False, bundle_for=None,
          src=None):
    """the turning version with the mark of level `level` of `family`: tools/turn_items.py's turning item under
    the name Obj_NX2Q_<level>, which marks its dropper when it is picked up and when it turns; what it drops
    when it turns is the next level's ordinary turning item. Returns what turn_items.build returns."""
    item = family[level]
    ai = ai_name(item)
    name, pack, new_inner, rows, loose = turn_items.build(
        family, level, read_pack, read_table_rows, model_exists, bundle_for, version=TURN, ai=ai)
    if name != once_name(item):
        raise SystemExit('%s: name not as intended' % name)
    src = src or sources(read_pack)
    files = dict(sarc.Sarc.read(pack).files)
    new_inner = dict(new_inner)
    pack = _finish(name, pack, files, new_inner, read_pack, ai, src, level < len(family) - 1)
    back = sarc.Sarc.read(pack).files
    last = level == len(family) - 1
    if not last:
        sub = byml.loads(back[turn_items.drop_sub_path(name)]).root
        if [x['DropActorName'] for x in sub['Items']] != [turn_items._work(ap_path(turn_items.turn_name(
                family[level + 1])))]:
            raise SystemExit('read-back: %s does not turn into the next level\'s turning item' % name)
    return name, pack, new_inner, rows, loose


def build_plain(item, read_pack, read_table_rows, model_exists=lambda project: False, src=None):
    """the ground version with the mark of `item` (Obj_NX2O_<item>): tools/ground_items.py's ground version
    with the ground items' own AI under a name of ours, with the token's "picked up" branch, and the token's
    number in its blackboard. Returns (name, pack, {inner path: (data, the game file it is made from)}, rows,
    loose files as ground_items.build)."""
    name, pack, ground_new, rows, loose = ground_items.build(item, read_pack, read_table_rows, model_exists, PLAIN)
    if name != plain_name(item):
        raise SystemExit('%s: name not as intended' % name)
    src = src or sources(read_pack)
    files = dict(sarc.Sarc.read(pack).files)
    tpl_name = ground_items.template_of(name)
    new_inner = {p: (d, ground_items.new_file_like(p, tpl_name)) for p, d in ground_new.items()}
    base_info = ai_info_path(turn_items.BASE_AI)
    if resolved_components(files, name).get('AIInfoRef') != '?' + base_info or base_info not in files:
        raise SystemExit('%s: its AI is not %s as expected' % (name, turn_items.BASE_AI))
    idoc = byml.loads(files[base_info])
    if dict(idoc.root) != {'RootAIRef': 'Work/AI/Root/%s.root.ain' % turn_items.BASE_AI}:
        raise SystemExit('%s not as expected' % base_info)
    idoc.root = type(idoc.root)(idoc.root)
    idoc.root['RootAIRef'] = type(idoc.root['RootAIRef'])('Work/AI/Root/%s.root.ain' % PLAIN_AI)
    files[ai_info_path(PLAIN_AI)] = byml.dumps(idoc)
    new_inner[ai_info_path(PLAIN_AI)] = (files[ai_info_path(PLAIN_AI)], base_info)
    files[ai_path(PLAIN_AI)] = src['base']
    adoc = byml.loads(files[ap_path(name)])
    adoc.root = type(adoc.root)(adoc.root)
    comp = type(adoc.root['Components'])(adoc.root['Components'])
    if 'AIInfoRef' in comp:
        raise SystemExit('%s: already has an AI of its own' % name)
    comp['AIInfoRef'] = '?' + ai_info_path(PLAIN_AI)
    adoc.root['Components'] = comp
    files[ap_path(name)] = byml.dumps(adoc)
    pack = _finish(name, pack, files, new_inner, read_pack, PLAIN_AI, src, False)
    return name, pack, new_inner, rows, loose


# ---- the rock, the bush, the pot ----

def dropper_ai_name(root):
    return DROP_AI_PREFIX + root


def root_ai_of(files, actor):
    """(the name of the root AI an actor runs, the file that names it), read from its pack"""
    ref = resolved_components(files, actor).get('AIInfoRef')
    if not ref or _ref_path(ref) not in files:
        raise SystemExit('%s: no AI named in its pack' % actor)
    root = byml.loads(files[_ref_path(ref)]).root.get('RootAIRef', '')
    head, tail = 'Work/AI/Root/', '.root.ain'
    if not root.startswith(head) or not root.endswith(tail) or ai_path(root[len(head):-len(tail)]) not in files:
        raise SystemExit('%s: its AI (%s) is not in its pack as expected' % (actor, root))
    return root[len(head):-len(tail)], _ref_path(ref)


def instance_keys(files):
    """the blackboard keys that are instance parameters (`IsInstanceParam`: set by the placement) in any
    blackboard table of a pack. An AI must not write one of the actor's own (BlackboardType 1): the game's
    write nodes stop the game on them (see the top of this file), and no AI of the game does it."""
    out = set()
    for p, data in files.items():
        if 'BlackboardParamTable/' not in p:
            continue
        for v in byml.loads(data).root.values():
            for x in v if isinstance(v, list) else ():
                if isinstance(x, dict) and x.get('IsInstanceParam') and 'BBKey' in x:
                    out.add(x['BBKey'])
    return out


def actor_writes(data):
    """[(node name, key)] of the nodes of an AI file that write a value of the actor's own blackboard
    (`ExecuteBlackboardSet...`, BlackboardType 1)"""
    out = []
    for n in ainb.loads(data).nodes:
        if n.name and n.name.startswith('ExecuteBlackboardSet'):
            imm = {x.name: x.value for t in ainb.PARAM_TYPES for x in n.immediates[t]}
            if imm.get('BlackboardType') == ACTOR_BLACKBOARD:
                out.append((n.name, imm.get('BlackboardKey')))
    return out


def has_drop(files, actor):
    """whether an actor has a drop part (a rock that is only a prop has none)"""
    return bool(resolved_components(files, actor).get('DropRef'))


def _anchor(doc):
    """the "all at once" node of a rock's, a bush's or a pot's AI that runs every frame: its root, or what its
    root runs on "Update\""""
    root = doc.nodes[doc.commands[0].left]
    i = doc.commands[0].left
    if root.type == SPLIT_TIMING and [l.name for l in root.links[FLOW]] == ['Enter', 'Update', 'Leave']:
        i = root.links[FLOW][1].node
    n = doc.nodes[i]
    if [c.name for c in doc.commands] != ['Root'] or n.type != SIMULTANEOUS or not _plain(n) \
            or any(l.name or l.extra for l in n.links[FLOW]) \
            or any(links for k, links in enumerate(n.links) if k != FLOW) or doc.attachments or doc.resident:
        raise SystemExit('%s: no "all at once" node that runs every frame found as expected' % doc.filename)
    return i


def dropper_ai(base, src, name, steps=()):
    """a rock's, a bush's or a pot's AI (`base`: the game's) under the name `name`, with the one-time branch
    beside what it runs every frame (see the top of this file):

        the drop my placement names starts with "Obj_NX2"?
          yes -> all at once:
                   hand my placement's number to what I drop         (the Gold Skulltula's three nodes)
                   for each step (from, item, to):
                     the drop named starts with `from`? -> Link owns `item`? -> name `to` as my drop
          no  -> nothing

    steps: [(the version dropped for a level, that level's item, the version for the next level)].
    Read back: the game's nodes are as they were but for the one new link."""
    doc = ainb.loads(base)
    orig = ainb.loads(base)
    t = _templates(src)
    at = _anchor(doc)
    add = _Adder(doc, name)
    hand_src = ainb.loads(src['hand'])
    h = _one(hand_src, N_HAND, lambda n: n.name == N_HAND)
    chain = [h]
    while True:
        x = [x for k in ainb.PARAM_TYPES for x in hand_src.nodes[chain[-1]].inputs[k]]
        if not x:
            break
        if len(x) != 1 or x[0].node < 0:
            raise SystemExit('%s: the hand-over is not one chain of nodes as expected' % hand_src.filename)
        chain.append(x[0].node)
    hn = [hand_src.nodes[i] for i in chain]
    if [n.name for n in hn] != [N_HAND, Q_HASH, Q_MAKE] or _imm(hn[1]) != [
            ('bool', 'OutputOnlyOnEnter', False), ('string', 'Key', KEY)] or hn[0].links[FLOW] \
            or _imm(hn[0]) != [('bool', 'ExecuteEveryFrame', False)]:
        raise SystemExit('%s: the hand-over is not the three nodes expected' % hand_src.filename)
    hand = add.group(hand_src, chain, 'hand')[h]

    def idle(what):
        return add.new(t['idle'], 'nothing, ' + what)

    def starts(token, what):
        """a yes/no selector on "the drop named starts with `token`\""""
        q = add.new(t['starts'], 'starts ' + what)
        n = add.node(q)
        n.inputs['string'][0].node, n.inputs['string'][0].param = named, 0
        n.inputs['string'][1].value = token
        n.links[STRING][0].node = named
        add.wants[q] = [named]
        sel = add.new(t['bool'], 'is ' + what)
        add.ask(sel, q, 0, 'bool')
        return sel

    named = add.new(t['named'], 'drop named')
    add.node(named).immediates['string'][0].value = DROP_KEY
    doing = [hand]
    for k, (frm, item, to) in enumerate(steps):
        own = add.new(t['owned'], 'owned %d' % k)
        add.node(own).inputs['string'][0].value = item
        has = add.new(t['int'], 'has %d' % k)
        add.ask(has, own, 0, 'int')
        write = add.new(t['write'], 'name %d' % k)
        add.node(write).immediates['string'][0].value = DROP_KEY
        add.node(write).inputs['string'][0].value = to
        add.flow(has, idle('not owned %d' % k), write)       # "when 0", then "otherwise"
        sel = starts(frm, 'step %d' % k)
        add.flow(sel, has, idle('not step %d' % k))
        doing.append(sel)
    both = add.new(t['all'], 'ours')
    add.flow(both, *doing)
    gate = starts(OURS, 'ours')
    add.flow(gate, both, idle('not ours'))
    added = add.done()
    doc.nodes[at].links[FLOW].append(ainb.Link(gate, '', ()))
    doc.filename = name + '.root'
    out = doc.write()

    back = ainb.loads(out)
    if back.write() != out or back.filename != name + '.root' or len(back.nodes) != len(orig.nodes) + added \
            or _doc_state(back) != _doc_state(orig) \
            or _reached(back) != _reached(orig) | set(range(len(orig.nodes), len(back.nodes))):
        raise SystemExit('read-back: %s differs from what was intended' % ai_path(name))
    for i, (o, b) in enumerate(zip(orig.nodes, back.nodes)):
        if i == at:
            o.links[FLOW].append(ainb.Link(gate, '', ()))
        if _node_state(o) != _node_state(b):
            raise SystemExit('read-back: node %d of %s differs from what was intended' % (i, ai_path(name)))
    got = dropper_of(out)
    if got is None or got['ours'] != OURS or got['key'] != KEY or got['steps'] != list(steps) \
            or got['new'] != added:
        raise SystemExit('read-back: the one-time branch of %s is not as intended: %r' % (ai_path(name), got))
    return out


def step_clashes(steps):
    """the steps of a dropper's AI that would also answer for a drop they are not meant for: the question is
    "the drop named starts with", and one level's name can start with another's (Obj_NX2Q_FairyBless_MP,
    Obj_NX2Q_FairyBless_MPDouble). Returns [(the step's name, the other name)] for those that could do harm. A
    clash does no harm when the other name is what that step names anyway (it writes what is already named)
    and no step starts from the other name (two steps would write in the same frame)."""
    names = {x for frm, _, to in steps for x in (frm, to)}
    froms = {frm for frm, _, _ in steps}
    out = []
    for frm, _, to in steps:
        for y in sorted(names):
            if y != frm and y.startswith(frm) and not (y == to and y not in froms):
                out.append((frm, y))
    return out


def dropper_of(data):
    """what the one-time branch of a rock's, a bush's or a pot's AI does, read from the file by following its
    links; None when the file has no such branch. {'name', 'ours' (what the drop named must start with), 'key'
    (the blackboard key its placement's number is handed over in), 'steps' ([(the drop named starts with, the
    item Link must own, the drop it names then)]), 'new' (how many nodes the branch has)}"""
    doc = ainb.loads(data)
    nodes = doc.nodes
    try:
        at = _anchor(doc)
    except SystemExit:
        return None

    def bad(what):
        raise SystemExit('%s: %s' % (doc.filename, what))

    seen = set()

    def node(i):
        seen.add(i)
        return nodes[i]

    def starts(i):
        """(the token, the "yes" child, the "no" child) of a selector on "the drop named starts with\""""
        sel = node(i)
        x = sel.inputs['bool'][0] if sel.type == BOOL_SELECTOR and sel.inputs['bool'] else None
        q = node(x.node) if x is not None and x.node >= 0 else None
        if q is None or q.name != Q_STARTS or q.outputs['bool'][x.param].name != 'Result' \
                or [l.name for l in sel.links[FLOW]] != ['True', 'False']:
            return None
        name = node(q.inputs['string'][0].node)
        if name.name != Q_NAMED or name.immediates['int'][0].value != ACTOR_BLACKBOARD \
                or name.immediates['string'][0].value != DROP_KEY or q.inputs['string'][1].node >= 0:
            bad('a "starts with" question that is not about the drop the placement names')
        return q.inputs['string'][1].value, sel.links[FLOW][0].node, sel.links[FLOW][1].node

    def nothing(i):
        if node(i).name != N_IDLE or any(nodes[i].links):
            bad('node %d: expected a node that does nothing' % i)

    hits = [l.node for l in nodes[at].links[FLOW] if starts(l.node)]
    if not hits:
        return None
    if len(hits) != 1:
        bad('more than one one-time branch')
    seen.clear()
    ours, yes, no = starts(hits[0])
    nothing(no)
    both = node(yes)
    if both.type != SIMULTANEOUS:
        bad('the branch does not do its steps at once')
    out = {'name': doc.filename, 'ours': ours, 'key': None, 'steps': []}
    for l in both.links[FLOW]:
        n = node(l.node)
        if n.name == N_HAND:
            a = node(n.inputs['userdefined'][0].node)
            b = node(a.inputs['userdefined'][0].node)
            if a.name != Q_HASH or b.name != Q_MAKE or out['key'] is not None:
                bad('the hand-over is not the three nodes expected')
            out['key'] = a.immediates['string'][0].value
            continue
        step = starts(l.node)
        if step:
            frm, has, none = step
            nothing(none)
            sel = node(has)
            q = node(sel.inputs['int'][0].node) if sel.type == S32_SELECTOR else None
            if q is None or q.name != Q_OWNED or [x.extra for x in sel.links[FLOW]] != [(0, 0), (0, 0)]:
                bad('a step does not ask the inventory as expected')
            nothing(sel.links[FLOW][0].node)
            w = node(sel.links[FLOW][1].node)
            if w.name != N_WRITE or w.immediates['string'][0].value != DROP_KEY \
                    or w.immediates['int'][0].value != ACTOR_BLACKBOARD:
                bad('a step does not name another drop as expected')
            out['steps'].append((frm, q.inputs['string'][0].value, w.inputs['string'][0].value))
            continue
        bad('something else than the hand-over and the steps in the branch')
    out['new'] = len(seen)
    return out


def dropper_files(files, actor, src, steps=()):
    """what makes the actor `actor` (a rock, a bush or a pot; `files`: its pack) drop once: (the name of its
    game AI, {inner path: (data, the game file it is made from)} for the AI of ours and the file that names it,
    the actor's own file with that AI named: (inner path, old data, new data))"""
    root, info = root_ai_of(files, actor)
    if not has_drop(files, actor):
        raise SystemExit('%s: no drop part: it cannot drop anything' % actor)
    if steps and DROP_KEY in instance_keys(files):
        raise SystemExit('%s: %s is an instance parameter of its blackboard: writing it stops the game (seen '
                         '2026-11-22), so its AI cannot name another drop' % (actor, DROP_KEY))
    name = dropper_ai_name(root)
    idoc = byml.loads(files[info])
    idoc.root = type(idoc.root)(idoc.root)
    idoc.root['RootAIRef'] = type(idoc.root['RootAIRef'])('Work/AI/Root/%s.root.ain' % name)
    new = {ai_path(name): (dropper_ai(files[ai_path(root)], src, name, steps), ai_path(root)),
           ai_info_path(name): (byml.dumps(idoc), info)}
    adoc = byml.loads(files[ap_path(actor)])
    adoc.root = type(adoc.root)(adoc.root)
    comp = type(adoc.root['Components'])(adoc.root['Components'])
    comp['AIInfoRef'] = '?' + ai_info_path(name)
    adoc.root['Components'] = comp
    return root, new, (ap_path(actor), files[ap_path(actor)], byml.dumps(adoc))


def patch_pack(pack_data, new, changed):
    """a pack that holds the actor's own file, with that file changed and the new files added; read back"""
    arc = sarc.Sarc.read(pack_data)
    path, old, data = changed
    if arc.files.get(path) != old:
        raise SystemExit('%s: not the same in every pack that holds it' % path)
    files = dict(arc.files)
    files[path] = data
    for p, (d, _) in new.items():
        if p in files and files[p] != d:
            raise SystemExit('%s: already in the pack' % p)
        files[p] = d
    out = sarc.Sarc.read(pack_data)
    out.files = files
    out.align = {p: arc.align.get(p, 8) for p in files}
    data = out.write()
    back = sarc.Sarc.read(data).files
    if set(back) != set(files) or any(back[p] != d for p, d in files.items()) \
            or any(back[p] != d for p, d in arc.files.items() if p != path):
        raise SystemExit('read-back: the pack differs from what was intended')
    return data


def holders(romfs, actor):
    """the actor packs that hold the actor's own file: its own and those of the actors that inherit from it.
    Looked for among the packs of its kind (the same name up to its letter and number: Obj_Pot_...); the test
    looks through every pack of the game for others (tests/one_time_check.py)."""
    stem = actor[:actor.rindex('_A_') + 1] if '_A_' in actor else actor
    folder = os.path.join(romfs, 'Pack', 'Actor')
    out = []
    for fn in sorted(os.listdir(folder)):
        if fn.startswith(stem) and fn.endswith('.pack.zs'):
            out.append(fn[:-len('.pack.zs')])
    return out
