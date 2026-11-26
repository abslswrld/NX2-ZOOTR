"""The starting state of a new file: items Link has from the start and flags that are set from the start.

Where the game sets up a new file (found in its own files, 2026-11-23): the sequence that starts a new game,
Sequence/Opening.module.ainb, runs Sequence/SetPouchAndStatusForGameStart.module.ainb once, after the title
screen's map is gone and before Kokiri Forest is loaded. That module is the game's own list of what a new file
has:
- four `SeqOneShotPushToPouch` nodes: the small wallet (Item_Wallet_Small), the adult tunic
  (Armor_Adult_Normal) and the two green tunics as objects (Obj_Armor_Child_Normal, Obj_Armor_Adult_Normal),
  each named by its actor file, `Work/Actor/<item>.engine__actor__ActorParam.gyml`, with a count (`Num`);
- five `SeqOneShotSetGameDataInt` nodes on the struct PlayerStatus: Life 12 and MaxLife 12 (three hearts),
  MP, MPEconomy and MPMax 0.
Everything else a new file has is the flag's default in GameData/GameDataList (Mido's
`KokiriForest_Npc_Kokiri_Mido_Child_Blocker` is true there and no flow ever sets it to true).

So a starting item is one more `SeqOneShotPushToPouch` node (a copy of the wallet's, with the item's actor
file and count), and a starting flag is one more setter node. The sequence has a setter per flag type,
`SeqOneShotSetNonStructGameDataBool`, `...Int` and `...String64` (flag name `GameDataFullName`, `Value`):
this module has none, so they are copied from Sequence/DestroySceneCommon.module.ainb, where the game uses all
three. Nothing else changes: the game's own nodes stay as they are, the new ones are added behind them and
linked under the module's two groups (pushes, status).

What is accepted, and why:
- an item must be an inventory item: a row in RSDB/PouchActorInfo and the saved pair `IsGet.<item>` /
  `PouchData.<item>.StockNum` in GameDataList. That is true of three of the game's own four pushes; the fourth,
  Obj_Armor_Adult_Normal, has a row but no saved pair: it stands for another inventory name, the one its row in
  RSDB/ActorInfo gives as `ActorName` (Armor_Adult_Normal; its actor file's `ActorNameRef` names the same). So
  an item kept under another name is accepted when that name has the saved pair (phase 1, part 10, to test in
  game): the Fairy Slingshot and the Fairy Bow as they are placed (Item_Range_SlingShot -> Weapon_Range_SlingShot,
  Item_Range_Bow -> Weapon_Range_Bow) and the strength upgrades (Item_Gauntlet_Goron ->
  Armor_Child_Gauntlet_Goron, Item_Gauntlet_Silver, Item_Gauntlet_Gold). The push names the item as it is
  placed, as the game's own push of Obj_Armor_Adult_Normal does;
- a first weapon comes with what the game's chests give with it (tools/build_mod.py reads it from the shared
  chest module, turn_items.first_get): the Fairy Slingshot with Item_BulletBag_Small and 30 Item_DekuSeed, the
  Fairy Bow with Item_Quiver_Small and 30 Item_Arrow_Normal, as pushes of their own behind the weapon's;
- hearts and rupees (phase 1, part 10, to test in game): Link's hearts are the module's own two sets on
  PlayerStatus, `Life` and `MaxLife` (12 each: 4 per heart), so starting hearts change those two values; his
  rupees are `PlayerStatus.CurrentRupee` (an Int, saved, 0 by default), set by one more
  `SeqOneShotSetGameDataInt` node, a copy of the module's `Life` node, which reads the struct from the module's
  own finder of PlayerStatus (`status` in edit);
- not possible: a chest (or any map object) opened from the start. A placement's saved flag is an entry of
  `Bool64bitKey` in GameDataList, which has only `Hash`, `ResetTypeValue`, `SaveFileIndex` (and `ExtraByte`):
  no default value to change, and no sequence node sets a flag by its 64-bit number;
- the project's item rules hold here too: nothing the game never gives as such, and no later level of an
  upgrade family without the levels in front of it;
- a flag must be a Bool, an Int or a String64 of GameDataList, saved in the save slot (progress.sav), and no
  field of a struct (PlayerStatus.MaxLife, IsGet.<item>...: the "NonStruct" setters take plain flags). A
  BoolExp is worked out from other flags and cannot be set;
- but a field of a dungeon's record can be set (2026-11-24): `DungeonInfo.<dungeon>.SmallKeyNum` (the small
  keys Link holds there), `IsGetBossKey`, `IsGetMap`, `IsGetCompass`. That is how a file starts with a dungeon's
  keys, map and compass. A field of a struct is set the way the module sets Link's hearts: a
  `SeqOneShotSetGameDataInt` node (a Bool: `SeqOneShotSetGameDataBool`, copied from
  Sequence/DestroySceneCommon.module.ainb) whose `ParentStruct` comes from a `SeqQueryGetNonStructGameDataStruct`
  node that finds the struct by its name (the module's own finds PlayerStatus). One such node is added per
  dungeon named, and one setter per field;
- and so can a place's "visited" mark, `IsVisitLocation.<place>` (2026-11-24, to test in game): the game sets
  it when it shows a place's title, in the place's first cutscene (`UISystemActor.EventTriggerOpenLocationUI`:
  Dm_Kokiri_0045 for Kokiri Forest, Dm_ForestTemple_0000 for the Forest Temple) or from the place's
  LocationArea. The Map page's states are named WorldMap, DungeonMap, FieldMap and UnopenMap ("???").

Used by tools/build_mod.py (--start, --start-flag); tests/start_state_check.py reads it all back.
"""
import copy
import hashlib

from formats import ainb, byml

MODULE = 'Sequence/SetPouchAndStatusForGameStart.module.ainb'
SETTER_SOURCE = 'Sequence/DestroySceneCommon.module.ainb'      # where the game uses the three setters
GAME_DATA = 'GameData/GameDataList.Product.110.byml'
ITEM_TABLE = 'RSDB/PouchActorInfo.Product.111.rstbl.byml'
ACTOR_FILE = 'Work/Actor/%s.engine__actor__ActorParam.gyml'
N_PUSH = 'SeqOneShotPushToPouch'
N_STATUS = 'SeqOneShotSetGameDataInt'                          # the module's own sets on PlayerStatus
# flag type in GameDataList -> (setter node, parameter type of its Value)
SETTERS = {'Bool': ('SeqOneShotSetNonStructGameDataBool', 'bool'),
           'Int': ('SeqOneShotSetNonStructGameDataInt', 'int'),
           'String64': ('SeqOneShotSetNonStructGameDataString64', 'string')}
# fields of these structs can be set too (the dungeons' records), the way the module sets PlayerStatus:
# flag type -> (the setter that takes a struct, parameter type of its Value)
MEMBER_PREFIX = 'DungeonInfo.'
MEMBER_PREFIXES = (MEMBER_PREFIX, 'IsVisitLocation.')
MEMBER_SETTERS = {'Bool': ('SeqOneShotSetGameDataBool', 'bool'), 'Int': (N_STATUS, 'int')}
MEMBER = 'Member'                                              # kind of such a flag: 'MemberBool', 'MemberInt'
STATUS = 'PlayerStatus'                                        # the struct the module's own setters write to
HEART = 4                                                      # Life and MaxLife count quarters of a heart
HEARTS = (1, 20)
STATUS_HEARTS = ('MaxLife', 'Life')
STATUS_RUPEES = 'CurrentRupee'
STRUCT_QUERY = 'SeqQueryGetNonStructGameDataStruct'
VALUE_LINK = 0                                                 # link type: a value handed to another node
SIMULTANEOUS = 3                                               # node type Element_Simultaneous
FLOW = 2                                                       # link type: flow to child nodes
# flags of an input with nothing linked (formats/ainb.py: "0x0080/0x0180"): 0x800000 on every one, 0x1000000
# more on some of those that hold the node's default (the wallet's Num 1, most setters' GameDataIndex -1). A
# default value is found both ways in the game's sequences (Bool Value False: 31 times 0x800000, 24 times
# 0x1800000), so a value written here is always 0x800000, and an input left alone keeps what it had
SET, LEFT_AT_DEFAULT = 0x800000, 0x1000000
SLOT_SAVE = 0                                                  # SaveFileIndex of slot_NN/progress.sav
RESET_NEW_GAME_ONLY = 8                                        # ResetTypeValue of an ordinary saved flag
INT_RANGE = (-2 ** 31, 2 ** 31 - 1)
STRING64_BYTES = 63


def name_hash(name):
    """the hash a GameDataList entry is stored under (MurmurHash3, 32 bits, seed 0)"""
    key, h = name.encode('utf-8'), 0
    rot = lambda x, r: ((x << r) | (x >> (32 - r))) & 0xffffffff   # noqa: E731
    for i in range(0, len(key), 4):
        k = int.from_bytes(key[i:i + 4], 'little')
        h ^= rot(k * 0xcc9e2d51 & 0xffffffff, 15) * 0x1b873593 & 0xffffffff
        if i + 4 <= len(key):
            h = (rot(h, 13) * 5 + 0xe6546b64) & 0xffffffff
    h ^= len(key)
    h = (h ^ h >> 16) * 0x85ebca6b & 0xffffffff
    h = (h ^ h >> 13) * 0xc2b2ae35 & 0xffffffff
    return h ^ h >> 16


# ------------------------------------------------------------------------------------------ what is asked for
def parse_items(specs):
    """--start ITEM or ITEM=N -> [(item, count)]; an item is given once"""
    items = []
    for spec in specs:
        item, _, num = spec.partition('=')
        if not item or (num and not num.isdigit()) or (num and int(num) < 1):
            raise SystemExit('--start %s: expected ITEM or ITEM=N (N: how many, 1 or more)' % spec)
        if any(item == x for x, _ in items):
            raise SystemExit('--start: %s is given twice' % item)
        items.append((item, int(num) if num else 1))
    return items


def parse_flags(specs):
    """--start-flag NAME=VALUE -> [(name, value as text)]; a flag is given once"""
    flags = []
    for spec in specs:
        name, eq, value = spec.partition('=')
        if not name or not eq:
            raise SystemExit('--start-flag %s: expected NAME=VALUE' % spec)
        if any(name == x for x, _ in flags):
            raise SystemExit('--start-flag: %s is given twice' % name)
        flags.append((name, value))
    return flags


class GameData:
    """the game's flag list (GameData/GameDataList), looked up by flag name"""

    def __init__(self, data):
        root = byml.loads(data).root
        self.by_hash = {}                                # name hash -> (type, entry)
        for kind, entries in root['Data'].items():
            if kind == 'Bool64bitKey':                   # keyed by map placement, not by name
                continue
            for e in entries:
                self.by_hash[int(e['Hash'])] = (kind, e)
        self.members = {int(m['Value']) for kind, e in self.by_hash.values() if kind == 'Struct'
                        for m in e['DefaultValue']}      # flags that are a field of a struct
        self.save_files = list(root['MetaData']['SaveDirectory'])

    def find(self, name):
        """(type, entry) of the flag with this name, or None"""
        return self.by_hash.get(name_hash(name))

    def is_member(self, name):
        return name_hash(name) in self.members

    def owns(self, item):
        """the saved pair an inventory item has under its own name"""
        got, stock = self.find('IsGet.' + item), self.find('PouchData.%s.StockNum' % item)
        return bool(got and got[0] == 'Bool' and stock and stock[0] == 'Int')


def check_items(items, game_data, item_rows, never_given=(), families=(), known_as=None):
    """stops the build when a starting item is no inventory item, is never given as such (never_given: {item:
    why}) or is a later level of an upgrade family (families: tuples, lowest level first) without every level
    in front of it. known_as: {item: the name its row in RSDB/ActorInfo gives it}; an item with no saved pair
    of its own is accepted when that name has one. Returns {item: that name} for those items"""
    names = [x for x, _ in items]
    stand = {}
    for item, _ in items:
        if item in never_given:
            raise SystemExit('--start %s: cannot be given: the game never gives it as an item (%s)'
                             % (item, never_given[item]))
        if item not in item_rows:
            raise SystemExit('--start %s: has no row in %s: not an inventory item' % (item, ITEM_TABLE))
        if not game_data.owns(item):
            inv = (known_as or {}).get(item)
            if not inv or inv == item or inv not in item_rows or not game_data.owns(inv):
                raise SystemExit('--start %s: %s has no IsGet.%s / PouchData.%s.StockNum, and neither has the '
                                 'name its row in RSDB/ActorInfo gives it (%s): not an item the inventory keeps'
                                 % (item, GAME_DATA, item, item, inv))
            stand[item] = inv
        for family in families:
            if item not in family:
                continue
            missing = [x for x in family[:family.index(item)] if x not in never_given and x not in names]
            if missing:
                raise SystemExit('--start %s: it is a later level of the upgrade family %s; a family never '
                                 'skips a level: also give --start %s'
                                 % (item, ' > '.join(family), ' --start '.join(missing)))
    return stand


def check_with(items, more, game_data, item_rows):
    """stops the build when what comes with a starting item (more: [(item, count)], what the game's chests
    give with a first weapon) is no inventory item under its own name or is given twice"""
    for item, num in more:
        if item not in item_rows or not game_data.owns(item) or num < 1:
            raise SystemExit('--start: %s x%d comes with a starting item, but is no inventory item under its own '
                             'name' % (item, num))
        if [x for x, _ in list(items) + list(more)].count(item) != 1:
            raise SystemExit('--start: %s comes with a starting item and is given again' % item)


def parse_status(hearts, rupees, max_rupees):
    """--start-hearts N and --start-rupees N -> [(field of PlayerStatus, value)]. max_rupees: what the
    wallets of the new file hold"""
    out = []
    if hearts is not None:
        if not HEARTS[0] <= hearts <= HEARTS[1]:
            raise SystemExit('--start-hearts %d: give %d to %d hearts' % ((hearts,) + HEARTS))
        out += [(f, hearts * HEART) for f in STATUS_HEARTS]
    if rupees is not None:
        if not 0 <= rupees <= max_rupees:
            raise SystemExit('--start-rupees %d: the wallet of a new file holds 0 to %d' % (rupees, max_rupees))
        out.append((STATUS_RUPEES, rupees))
    return out


def check_flags(flags, game_data):
    """[(name, type, value, note or None)] of the starting flags, values as the setter takes them; stops the
    build on a flag that cannot be set this way"""
    out = []
    for name, text in flags:
        found = game_data.find(name)
        if not found:
            raise SystemExit('--start-flag %s: no flag of this name in %s' % (name, GAME_DATA))
        kind, e = found
        if kind == 'BoolExp':
            raise SystemExit('--start-flag %s: it is a BoolExp, worked out from other flags: it cannot be set '
                             '(set the flags it is made of)' % name)
        if kind not in SETTERS:
            raise SystemExit('--start-flag %s: its type is %s; only %s flags can be set at the start for now'
                             % (name, kind, ', '.join(sorted(SETTERS))))
        member = False
        if game_data.is_member(name):
            struct, _, field = name.rpartition('.')
            parent = game_data.find(struct)
            if not name.startswith(MEMBER_PREFIXES) or kind not in MEMBER_SETTERS or not parent \
                    or parent[0] != 'Struct' or not any(
                        int(m['Hash']) == name_hash(field) and int(m['Value']) == name_hash(name)
                        for m in parent[1]['DefaultValue']):
                raise SystemExit('--start-flag %s: it is a field of a struct, which the plain setters do not take '
                                 '(for an item use --start; only the fields of %s<dungeon> and %s<place> can '
                                 'be set)' % ((name,) + MEMBER_PREFIXES))
            member = True
        if int(e['SaveFileIndex']) != SLOT_SAVE:
            raise SystemExit('--start-flag %s: it is not saved in the save slot (%s; its save file index is '
                             '%d), so it would not last' % (name, game_data.save_files[SLOT_SAVE],
                                                            int(e['SaveFileIndex'])))
        if kind == 'Bool':
            if text.lower() not in ('true', 'false'):
                raise SystemExit('--start-flag %s=%s: a Bool flag takes true or false' % (name, text))
            value = text.lower() == 'true'
        elif kind == 'Int':
            try:
                value = int(text)
            except ValueError:
                raise SystemExit('--start-flag %s=%s: an Int flag takes a whole number' % (name, text))
            if not INT_RANGE[0] <= value <= INT_RANGE[1]:
                raise SystemExit('--start-flag %s=%s: outside a 32-bit number' % (name, text))
        else:
            value = text
            if len(text.encode('utf-8')) > STRING64_BYTES:
                raise SystemExit('--start-flag %s: a String64 flag holds at most %d bytes'
                                 % (name, STRING64_BYTES))
        note = None
        if int(e['ResetTypeValue']) != RESET_NEW_GAME_ONLY:
            note = ('its reset type is %d, not %d: the game also resets it at other times, back to its '
                    'default %r' % (int(e['ResetTypeValue']), RESET_NEW_GAME_ONLY, e['DefaultValue']))
        out.append((name, MEMBER + kind if member else kind, value, note))
    return out


# ------------------------------------------------------------------------------------------------ the module
def _one(nodes, ok, what, where):
    hits = [i for i, n in enumerate(nodes) if ok(n)]
    if len(hits) != 1:
        raise SystemExit('%s: expected one %s, found %d' % (where, what, len(hits)))
    return hits[0]


def _group(doc, child):
    """the Element_Simultaneous node of the module whose children are all `child` nodes"""
    def ok(n):
        kids = [doc.nodes[l.node].name for l in n.links[FLOW]]
        return n.type == SIMULTANEOUS and kids and all(k == child for k in kids)
    return _one(doc.nodes, ok, 'group of %s nodes' % child, MODULE)


def _input(node, kind, name):
    hits = [x for x in node.inputs[kind] if x.name == name]
    if len(hits) != 1 or hits[0].node >= 0 or hits[0].sources or hits[0].flags & ~(SET | LEFT_AT_DEFAULT):
        raise SystemExit('%s: no plain %s input "%s"' % (node.name, kind, name))
    return hits[0]


def _plain(n):
    """a node that only has fixed inputs: nothing linked in or out, no attachment, no expression"""
    return (not n.attachments and not n.exb_count and not n.exb_size and not n.preconditions
            and not any(n.links) and not any(n.outputs[t] for t in ainb.PARAM_TYPES)
            and all(x.node < 0 and not x.sources and not x.flags & ~(SET | LEFT_AT_DEFAULT)
                    for t in ainb.PARAM_TYPES for x in n.inputs[t])
            and all(not x.flags for t in ainb.PARAM_TYPES for x in n.immediates[t]))


def _copy(template, what, taken):
    if not _plain(template):
        raise SystemExit('%s: the node copied for "%s" is not a plain one' % (template.name, what))
    n = copy.deepcopy(template)
    n.guid = hashlib.md5(('NX2-ZOOTR start state: %s' % what).encode()).digest()
    n.precondition_slot = None
    if n.guid in taken:
        raise SystemExit('%s: node id already used (%s)' % (MODULE, what))
    taken.add(n.guid)
    return n


def _set(x, value):
    x.value, x.flags = value, SET


def setter_templates(source_data):
    """{flag type: a plain setter node of the game's} from the module the game uses all three in"""
    doc = ainb.Ainb.read(source_data)
    out = {}
    for kind, (name, _) in SETTERS.items():
        hits = [n for n in doc.nodes if n.name == name and _plain(n)]
        if not hits:
            raise SystemExit('%s: no plain %s node to copy' % (SETTER_SOURCE, name))
        out[kind] = hits[0]
    return out


def push_node(template, item, num, taken):
    n = _copy(template, 'item %s' % item, taken)
    _set(_input(n, 'string', 'ActorName'), ACTOR_FILE % item)
    if num != _input(n, 'int', 'Num').value:             # the wallet's: 1, left at the node's default
        _set(_input(n, 'int', 'Num'), num)
    return n


def setter_node(templates, name, kind, value, taken):
    n = _copy(templates[kind], 'flag %s' % name, taken)
    _set(_input(n, 'string', 'GameDataFullName'), name)
    _set(_input(n, SETTERS[kind][1], 'Value'), value)
    return n


def _split(flags):
    """(the plain flags, the fields of structs) of a list of starting flags, each in the order given"""
    return ([f for f in flags if not f[1].startswith(MEMBER)], [f for f in flags if f[1].startswith(MEMBER)])


def member_templates(doc, source_data):
    """the game's nodes copied for a field of a struct: (the module's own struct finder, {flag type: a setter
    that takes a struct}), each found by what it is"""
    def takes_struct(n, name, kind):
        return (n.name == name and not n.attachments and not n.exb_count and not n.exb_size
                and not any(n.links) and not any(n.outputs[t] for t in ainb.PARAM_TYPES)
                and [(t, x.name) for t in ainb.PARAM_TYPES for x in n.inputs[t]] == sorted(
                    [('int', 'GameDataIndex'), (kind, 'Value'), ('string', 'GameDataName'),
                     ('userdefined', 'ParentStruct')], key=lambda p: ainb.PARAM_TYPES.index(p[0]))
                and n.inputs['userdefined'][0].node >= 0 and not n.inputs['userdefined'][0].sources
                and all(x.node < 0 and not x.sources for t in ('int', 'bool', 'string') for x in n.inputs[t]))
    q = [n for n in doc.nodes if n.name == STRUCT_QUERY and n.flags == 1 and not n.preconditions
         and [(t, x.name) for t in ainb.PARAM_TYPES for x in n.inputs[t]] == [
             ('int', 'GameDataIndex'), ('bool', 'IsDirect'), ('string', 'GameDataFullName')]
         and [(t, x.name) for t in ainb.PARAM_TYPES for x in n.outputs[t]] == [('userdefined', 'Value')]
         and [(k, [l.name for l in links]) for k, links in enumerate(n.links) if links] == [(VALUE_LINK, ['Value'])]]
    if len(q) != 1:
        raise SystemExit('%s: expected one %s node, found %d' % (MODULE, STRUCT_QUERY, len(q)))
    source = ainb.Ainb.read(source_data)
    setters = {}
    for kind, (name, t) in MEMBER_SETTERS.items():
        hits = [n for n in (doc.nodes if kind == 'Int' else source.nodes) if takes_struct(n, name, t)]
        if not hits:
            raise SystemExit('%s: no %s node that takes a struct to copy' % (MODULE if kind == 'Int' else SETTER_SOURCE, name))
        setters[kind] = hits[0]
    return q[0], setters


def _copy_linked(template, what, taken):
    """a copy of a node that is linked to another (a struct finder, a setter that takes a struct)"""
    n = copy.deepcopy(template)
    n.guid = hashlib.md5(('NX2-ZOOTR start state: %s' % what).encode()).digest()
    n.precondition_slot = None
    if n.guid in taken:
        raise SystemExit('%s: node id already used (%s)' % (MODULE, what))
    taken.add(n.guid)
    return n


def member_nodes(doc, source_data, members, taken):
    """the nodes that set fields of structs, to be added behind the nodes `doc` has now: [(node, whether it is
    a child of the status group)]. One struct finder per struct (in the order first named), then its setters;
    each setter waits for its finder, as the module's own do"""
    q_tpl, setters = member_templates(doc, source_data)
    out, at = [], len(doc.nodes)
    waited = sum(1 for n in doc.nodes if n.flags & 1)         # a finder's place among the nodes others wait for
    structs = []
    for name, _, _, _ in members:
        if name.rpartition('.')[0] not in structs:
            structs.append(name.rpartition('.')[0])
    for struct in structs:
        fields = [f for f in members if f[0].rpartition('.')[0] == struct]
        q = _copy_linked(q_tpl, 'struct %s' % struct, taken)
        _set(q.inputs['string'][0], struct)
        q_at = at + len(out)
        q.links[VALUE_LINK][0].node = q_at + 1               # its first setter, as the module's own names one
        out.append((q, False))
        for name, kind, value, _ in fields:
            kind = kind[len(MEMBER):]
            n = _copy_linked(setters[kind], 'field %s' % name, taken)
            _set(n.inputs['string'][0], name.rpartition('.')[2])
            _set(next(x for x in n.inputs[MEMBER_SETTERS[kind][1]] if x.name == 'Value'), value)
            n.inputs['userdefined'][0].node, n.inputs['userdefined'][0].param = q_at, 0
            n.preconditions = [waited]
            out.append((n, True))
        waited += 1
    return out


def read_members(module_data, prefix=MEMBER_PREFIXES):
    """the fields of structs a new-game module sets, read from it by following each setter to its struct
    finder: [(struct.field, value)] of the structs whose name starts with `prefix`"""
    doc = ainb.Ainb.read(module_data)
    out = []
    for n in doc.nodes:
        kind = next((k for k, (name, _) in MEMBER_SETTERS.items() if n.name == name), None)
        if kind is None or not n.inputs['userdefined']:
            continue
        src = n.inputs['userdefined'][0]
        q = doc.nodes[src.node] if src.node >= 0 else None
        if q is None or q.name != STRUCT_QUERY:
            raise SystemExit('%s: a setter whose struct is not found by name' % MODULE)
        waits = [i for i, x in enumerate(doc.nodes) if x.flags & 1]
        if n.preconditions != [waits.index(src.node)]:
            raise SystemExit('%s: a setter that does not wait for its struct' % MODULE)
        struct = q.inputs['string'][0].value
        if (struct + '.').startswith(prefix):
            out.append(('%s.%s' % (struct, n.inputs['string'][0].value),
                        next(x.value for x in n.inputs[MEMBER_SETTERS[kind][1]] if x.name == 'Value')))
    return out


def status_nodes(doc):
    """{field: node number} of the module's own sets on PlayerStatus (Life, MaxLife, MP...), each a
    SeqOneShotSetGameDataInt that reads the struct from the module's finder of PlayerStatus"""
    out = {}
    for i, n in enumerate(doc.nodes):
        if n.name != N_STATUS or not n.inputs['userdefined'] or n.inputs['userdefined'][0].node < 0:
            continue
        q = doc.nodes[n.inputs['userdefined'][0].node]
        if q.name != STRUCT_QUERY or q.inputs['string'][0].value != STATUS:
            continue
        field = n.inputs['string'][0].value
        if field in out or any(n.links):
            raise SystemExit('%s: its sets on %s are not as expected' % (MODULE, STATUS))
        out[field] = i
    if not set(STATUS_HEARTS) <= set(out):
        raise SystemExit('%s: no sets of %s on %s' % (MODULE, ' and '.join(STATUS_HEARTS), STATUS))
    return out


def _value(n):
    hits = [x for x in n.inputs['int'] if x.name == 'Value']
    if len(hits) != 1 or hits[0].node >= 0 or hits[0].sources:
        raise SystemExit('%s: a %s node without a plain Value' % (MODULE, n.name))
    return hits[0]


def _status_split(doc, status):
    """(the fields of PlayerStatus the module sets itself, the others) of `status`, each [(field, value)]"""
    own = status_nodes(doc)
    return [s for s in status if s[0] in own], [s for s in status if s[0] not in own]


def status_node(doc, field, value, taken):
    """a set of one more field of PlayerStatus: a copy of the module's own set of Life (it reads the struct
    from the module's finder and waits for it, as the copy does)"""
    n = _copy_linked(doc.nodes[status_nodes(doc)[STATUS_HEARTS[1]]], 'status %s' % field, taken)
    n.preconditions = list(doc.nodes[status_nodes(doc)[STATUS_HEARTS[1]]].preconditions)
    _set(n.inputs['string'][0], field)
    _set(_value(n), value)
    return n


def read_status(module_data):
    """{field: value} of the fields of PlayerStatus a new-game module sets"""
    return {name[len(STATUS) + 1:]: value for name, value in read_members(module_data, STATUS + '.')}


def edit(module_data, source_data, items, flags, status=()):
    """the new-game module with a push per starting item and a setter per starting flag added.
    items: [(item, count)]; flags: [(name, type, value, note)] (check_flags); status: [(field of PlayerStatus,
    value)] (parse_status): a field the module sets itself gets the value, another one a set of its own.
    Returns (new data, lines said); read back against both game files before it is returned"""
    doc = ainb.Ainb.read(module_data)
    pushes, status_group = _group(doc, N_PUSH), _group(doc, N_STATUS)
    taken = {bytes(n.guid) for n in doc.nodes}
    template = doc.nodes[doc.nodes[pushes].links[FLOW][0].node]
    all_flags = flags
    flags, members = _split(flags)
    templates = setter_templates(source_data) if flags else {}
    said = []
    changed, more = _status_split(doc, list(status))
    own = status_nodes(doc)
    more_nodes = [status_node(doc, field, value, taken) for field, value in more]
    for field, value in changed:
        x = _value(doc.nodes[own[field]])
        said.append('start %s.%s = %d on a new file (the module\'s own set, was %d)' % (STATUS, field, value, x.value))
        _set(x, value)
    status = status_group
    for where, new, line in ([(pushes, push_node(template, item, num, taken),
                               'start item %s x%d: pushed to the inventory on a new file' % (item, num))
                              for item, num in items]
                             + [(status, setter_node(templates, name, kind, value, taken),
                                 'start flag %s (%s) = %r on a new file' % (name, kind, value))
                                for name, kind, value, _ in flags]
                             + [(status, n, 'start %s.%s = %d on a new file (one more set, a copy of the '
                                            'module\'s set of %s)' % (STATUS, field, value, STATUS_HEARTS[1]))
                                for n, (field, value) in zip(more_nodes, more)]):
        link = copy.deepcopy(doc.nodes[where].links[FLOW][0])
        link.node = len(doc.nodes)
        doc.nodes[where].links[FLOW].append(link)
        doc.nodes.append(new)
        said.append(line)
    if members:                                        # fields of structs: behind everything else
        first = copy.deepcopy(doc.nodes[status].links[FLOW][0])
        new_nodes = member_nodes(doc, source_data, members, taken)
        for k, (new, child) in enumerate(new_nodes, len(doc.nodes)):
            if child:
                link = copy.deepcopy(first)
                link.node = k
                doc.nodes[status].links[FLOW].append(link)
        doc.nodes += [new for new, _ in new_nodes]
        said += ['start flag %s (%s, a field of a struct) = %r on a new file' % (name, kind[len(MEMBER):], value)
                 for name, kind, value, _ in members]
    new_data = doc.write()
    read_back(module_data, source_data, new_data, items, all_flags, changed + more)
    return new_data, said


# ------------------------------------------------------------------------------------------------- read back
def _params(n):
    return {kind: [(t, tuple(sorted((k, repr(v)) for k, v in vars(x).items())))
                   for t in ainb.PARAM_TYPES for x in getattr(n, kind)[t]]
            for kind in ('immediates', 'inputs', 'outputs')}


def _links(n):
    return [[(l.node, l.name, tuple(l.extra)) for l in links] for links in n.links]


def _node(n):
    return (n.type, n.name, n.flags, n.name_hash, bytes(n.guid), n.exb_count, n.exb_size, list(n.attachments),
            list(n.preconditions), _params(n), _links(n))


def _around(doc):
    """everything of a file but its nodes and its string pool"""
    return ([(c.name, bytes(c.guid), c.left, c.right) for c in doc.commands],
            {t: [tuple(sorted((k, repr(v)) for k, v in vars(g).items())) for g in gs]
             for t, gs in doc.globals.items()},
            doc.version, doc.filename, doc.category, doc.category_id, list(doc.global_files),
            len(doc.attachments), list(doc.resident), bytes(doc.exb), list(doc.modules),
            list(doc.entry_strings), tuple(doc.hashes), tuple(doc.replace_head), list(doc.replacements),
            doc.output_count)


def _fixed(n):
    """a node's fixed inputs: {(type, name): (value, flags)}"""
    return {(t, x.name): (x.value, x.flags) for t in ainb.PARAM_TYPES for x in n.inputs[t]}


def read_back(module_data, source_data, new_data, items, flags, status=()):
    """the written module, read again, against the game's two files: the game's own nodes are unchanged but
    for the new children of the two groups and the values of its own sets on PlayerStatus that `status` names;
    every new node is the game's node it was copied from with only the intended inputs different; nothing else
    in the file changed. Stops the build otherwise."""
    def fail(what):
        raise SystemExit('read-back: %s: %s' % (MODULE, what))
    a, b = ainb.Ainb.read(module_data), ainb.Ainb.read(new_data)
    if ainb.Ainb.read(new_data).write() != new_data:
        fail('does not write back the same')
    flags, members = _split(flags)
    changed, more = _status_split(a, list(status))
    own = status_nodes(a)
    for field, value in changed:                       # the game's own node with the value asked for
        _set(_value(a.nodes[own[field]]), value)
    got_status = read_status(new_data)
    if any(got_status.get(field) != value for field, value in status) \
            or set(got_status) != set(own) | {field for field, _ in more}:
        fail('the fields of %s set are not the ones asked for: %r' % (STATUS, got_status))
    n0, added = len(a.nodes), len(items) + len(flags) + len(more)
    structs = []
    for name, _, _, _ in members:
        if name.rpartition('.')[0] not in structs:
            structs.append(name.rpartition('.')[0])
    if len(b.nodes) != n0 + added + len(members) + len(structs):
        fail('%d nodes, expected %d' % (len(b.nodes), n0 + added + len(members) + len(structs)))
    if _around(a) != _around(b):
        fail('something other than the nodes changed')
    pushes, status = _group(a, N_PUSH), _group(a, N_STATUS)
    setters = [k for k in range(n0 + added, len(b.nodes)) if b.nodes[k].name != STRUCT_QUERY]
    want_links = {pushes: list(range(n0, n0 + len(items))),
                  status: list(range(n0 + len(items), n0 + added)) + setters}
    if members:
        q_tpl, tpls = member_templates(a, source_data)
        by_struct = [(s, [f for f in members if f[0].rpartition('.')[0] == s]) for s in structs]
        if read_members(new_data) != [(f[0], f[2]) for _, fs in by_struct for f in fs] \
                or len(setters) != len(members):
            fail('the fields of structs set are not the ones asked for: %r' % read_members(new_data))
        k = n0 + added
        for struct, fields in by_struct:
            q = b.nodes[k]
            want_q = copy.deepcopy(q_tpl)
            _set(want_q.inputs['string'][0], struct)
            want_q.links[VALUE_LINK][0].node = k + 1
            if _node(q)[:4] + _node(q)[5:] != _node(want_q)[:4] + _node(want_q)[5:]:
                fail('the struct finder of %s is not the game\'s node with its name' % struct)
            for j, (name, kind, value, _) in enumerate(fields, k + 1):
                n, t = b.nodes[j], tpls[kind[len(MEMBER):]]
                if (n.type, n.name, n.name_hash, n.flags) != (t.type, t.name, t.name_hash, t.flags) \
                        or _params(n)['immediates'] != _params(t)['immediates'] \
                        or n.inputs['userdefined'][0].node != k or any(n.links):
                    fail('the setter of %s is not the game\'s %s node on its struct' % (name, t.name))
            k += 1 + len(fields)
    for i, (o, n) in enumerate(zip(a.nodes, b.nodes)):
        if i in want_links:
            links = _links(o)
            links[FLOW] = links[FLOW] + [(k,) + links[FLOW][0][1:] for k in want_links[i]]
            if _links(n) != links or _node(o)[:-1] != _node(n)[:-1]:
                fail('group node %d is not the game\'s plus the new children' % i)
        elif _node(o) != _node(n):
            fail('the game\'s node %d (%s) changed' % (i, o.name))
    guids = [bytes(n.guid) for n in b.nodes]
    if len(set(guids)) != len(guids):
        fail('two nodes share an id')
    wallet = a.nodes[a.nodes[pushes].links[FLOW][0].node]
    templates = setter_templates(source_data) if flags else {}
    for k, (item, num) in enumerate(items):
        n = b.nodes[n0 + k]
        want = dict(_fixed(wallet))
        want['string', 'ActorName'] = (ACTOR_FILE % item, SET)
        if num != want['int', 'Num'][0]:
            want['int', 'Num'] = (num, SET)
        if (n.type, n.name, n.name_hash, n.flags) != (wallet.type, N_PUSH, wallet.name_hash, wallet.flags) \
                or _fixed(n) != want or _params(n)['immediates'] != _params(wallet)['immediates'] or not _plain(n):
            fail('the push of %s is not the wallet\'s node with its item and count' % item)
    life = a.nodes[own[STATUS_HEARTS[1]]]
    for k, (field, value) in enumerate(more):          # the module's set of Life with another field and value
        n = b.nodes[n0 + len(items) + len(flags) + k]
        want = copy.deepcopy(life)
        _set(want.inputs['string'][0], field)
        _set(_value(want), value)
        if _node(n)[:4] + _node(n)[5:] != _node(want)[:4] + _node(want)[5:]:
            fail('the set of %s.%s is not the module\'s set of %s with its field and value'
                 % (STATUS, field, STATUS_HEARTS[1]))
    for k, (name, kind, value, _) in enumerate(flags):
        n, t = b.nodes[n0 + len(items) + k], templates[kind]
        want = dict(_fixed(t))
        want['string', 'GameDataFullName'] = (name, SET)
        want[SETTERS[kind][1], 'Value'] = (value, SET)
        if (n.type, n.name, n.name_hash, n.flags) != (t.type, SETTERS[kind][0], t.name_hash, t.flags) \
                or _fixed(n) != want or _params(n)['immediates'] != _params(t)['immediates'] or not _plain(n):
            fail('the setter of %s is not the game\'s %s node with its flag and value' % (name, SETTERS[kind][0]))


def read(module_data):
    """what a new-game module gives and sets, as written in it: ([(item, count)], [(flag, value)]); the game's
    own PlayerStatus sets are left out (they name a field of a struct, not a flag)"""
    doc = ainb.Ainb.read(module_data)
    items, flags = [], []
    tail = '.engine__actor__ActorParam.gyml'
    setters = {name for name, _ in SETTERS.values()}
    for n in doc.nodes:
        fixed = {name: v for (_, name), (v, _) in _fixed(n).items()}
        if n.name == N_PUSH:
            path = fixed['ActorName']
            if not (path.startswith('Work/Actor/') and path.endswith(tail)):
                raise SystemExit('%s: a push names %r' % (MODULE, path))
            items.append((path[len('Work/Actor/'):-len(tail)], fixed['Num']))
        elif n.name in setters:
            flags.append((fixed['GameDataFullName'], fixed['Value']))
    return items, flags + read_members(module_data)
