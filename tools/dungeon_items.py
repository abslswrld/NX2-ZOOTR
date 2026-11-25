"""A dungeon's boss key, map or compass wherever it is found (to test in game).

Found in the game's files (2026-11-24):
- Each is a yes/no field of the dungeon's saved record: `DungeonInfo.<Dungeon>.IsGetBossKey`, `IsGetMap`,
  `IsGetCompass` (tools/dungeon_keys.py has the record). The boss door's lock (`Obj_DoorChainLock_A_02`) and
  the Map page read them.
- The items themselves (`Item_Dungeon_BossKey`, `Item_Dungeon_Map`, `Item_Dungeon_Compass`) are "not put in
  the inventory" (their item settings and their rows in PouchActorInfo: `NotPushToPouch`). What sets the field
  is the chests' shared opening event, `Dm_SY_Treasurebox`: it asks what the chest holds
  (`EventQueryTreasureBoxIsDungeonCommonItemInside`: map, compass, boss key, small key, anything else) and runs
  `GameSystemActor.EventGetDungeonMap` / `EventGetDungeonCompass` / `EventGetDungeonBossKey` /
  `EventGetDungeonSmallKey`. None of them takes a dungeon: they set the field of the dungeon Link is in.
- So in a chest of its own dungeon the game's own item works, in any chest. Anywhere else it does not: the
  game has no version of these three that lies on the ground (a pot would drop a boss key that sets nothing
  when picked up), and in a chest outside the dungeon the field set would be the wrong place's.

So `CHECK_ID=Item_Dungeon_BossKey@ForestTemple` (and `Item_Dungeon_Map@...`, `Item_Dungeon_Compass@...`):
- on a chest of that dungeon: the game's own item (tools/build_mod.py decides by the check's map);
- on the ground (a pot, a rock, a bush, a freestanding item; a Gold Skulltula), in the dungeon or outside: the
  builder's version of the item for that kind of check, with one more step in its "picked up" branch:
  `OneShotSetGameDataBool` True on the field of `DungeonInfo.<Dungeon>`, the step the Gerudo Fortress keys set
  their own flag with (`AI/Obj_Dungeon_SmallKey_GerudoFortress_01.root.ainb`);
- in a chest outside the dungeon: the item's own actor under the dungeon's name, and the chest's opening event
  gets a step after it that sets the field (tools/build_mod.py, as for a dungeon's small key).
Every version says the dungeon's name in the dungeon's colour, as a small key does (tools/dungeon_keys.py: an
item's two names; the name is the chest version, which is named itself): "You found the boss key! (Forest
Temple)".

Every new node is a copy of a game node of the same type, found by what it is and checked before it is used.
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml, ainb  # noqa: E402
import dungeon_keys  # noqa: E402
import ground_items  # noqa: E402
import once_items  # noqa: E402
import turn_items  # noqa: E402
from dungeon_keys import DUNGEONS, SEP, STRUCT, NAME_REF, COLOURED, COLOUR_END, Q_STRUCT, VALUE, FLOW  # noqa: E402
from ground_items import pack_path, ap_path  # noqa: E402
from shop_items import ai_path, ai_info_path, _node_state, _doc_state  # noqa: E402

# item -> (the letter of its versions' names, its field of the dungeon's record, a word for its AI's name,
# its texts: the game's own with the dungeon's name behind them)
ITEMS = {
    'Item_Dungeon_BossKey': ('B', 'IsGetBossKey', 'BossKey', (
        ('_Name', 'Boss Key (%s)'), ('_GetMessage', 'You found the boss key! (%s)'),
        ('_GetCaption', 'It opens the chamber where the boss\nof that place lurks, wherever you found it.'))),
    'Item_Dungeon_Map': ('M', 'IsGetMap', 'Map', (
        ('_Name', 'Dungeon Map (%s)'), ('_GetMessage', 'You found the dungeon map! (%s)'),
        ('_GetCaption', 'It is the map of that place,\nwherever you found it.'))),
    'Item_Dungeon_Compass': ('C', 'IsGetCompass', 'Compass', (
        ('_Name', 'Compass (%s)'), ('_GetMessage', 'You found the compass! (%s)'),
        ('_GetCaption', 'It shows the treasure chests and hidden\nsecrets of that place, wherever you found it.'))),
}
NAMES = {'once': 'Obj_NX2%sN_%s', 'token': 'Obj_NX2%sN_GS_%s', 'chest': 'Item_NX2%sN_%s'}   # letter, dungeon
AI_NAMES = {'once': 'NX2_%s_%s', 'token': 'NX2_%sGS_%s'}                                   # word, dungeon
NOT_PUSHED = dungeon_keys.NOT_PUSHED
N_SET = 'OneShotSetGameDataBool'
SET_SOURCE = dungeon_keys.STRUCT_SOURCE            # the Gerudo Fortress key's AI: both nodes copied
PREFIXES = tuple(n % (letter, '') for letter, _, _, _ in ITEMS.values() for n in NAMES.values())


def parse(item):
    """(the item, the dungeon) of `Item_Dungeon_BossKey@Dungeon` (or the map's, the compass's), or None for any
    other item"""
    if SEP not in item:
        return None
    base, dungeon = item.split(SEP, 1)
    if base not in ITEMS:
        return None
    if dungeon not in DUNGEONS:
        raise SystemExit('%s: no dungeon %s; the dungeons: %s' % (item, dungeon, ', '.join(DUNGEONS)))
    return base, dungeon


def field(item):
    return ITEMS[item][1]


def flag(item, dungeon):
    """the saved yes/no this item of this dungeon sets"""
    return (STRUCT % dungeon) + '.' + field(item)


def name(item, dungeon, kind):
    return NAMES[kind] % (ITEMS[item][0], dungeon)


def message_name(item, dungeon):
    """the name its texts are found under: its chest version, which is named itself"""
    return name(item, dungeon, 'chest')


def is_ours(version):
    return version.startswith(PREFIXES)


def messages(item, dungeon, place, colour=None):
    """the texts of this item of this dungeon: {label: text}; `place`: the dungeon's name as the game writes
    it; `colour`: the number of the colour the name has in the get message (None: the text's own)"""
    out = {}
    for tail, text in ITEMS[item][3]:
        shown = place
        if colour is not None and tail == COLOURED:
            shown = dungeon_keys.colour_tag(colour) + place + dungeon_keys.colour_tag(COLOUR_END)
        out[message_name(item, dungeon) + tail] = (text % shown if '%s' in text else text) + '\x00'
    return out


def templates(read_pack):
    """the two nodes copied: (OneShotSetGameDataBool True with the field's name as a fixed text,
    QueryGetNonStructGameDataStruct), each found by what it is"""
    shared = sarc.Sarc.read(read_pack(turn_items.AI_PACK)).files
    doc = ainb.loads(shared[SET_SOURCE])
    types = ainb.PARAM_TYPES
    q = dungeon_keys.templates(read_pack)[1]

    def shape(n, kind):
        return [(t, x.name) for t in types for x in getattr(n, kind)[t]]

    found = doc.nodes[once_items._one(doc, N_SET, lambda n: (
        n.name == N_SET and once_items._plain(n) and not n.flags
        and once_items._imm(n) == [('bool', 'DispError', True), ('bool', 'ExecuteEveryFrame', False)]
        and shape(n, 'inputs') == [('int', 'GameDataIndex'), ('bool', 'Value'), ('string', 'GameDataName'),
                                   ('userdefined', 'ParentStruct')]
        and n.inputs['int'][0].value == -1 and n.inputs['int'][0].node < 0
        and n.inputs['bool'][0].value is True and n.inputs['bool'][0].node < 0
        and n.inputs['userdefined'][0].node >= 0 and not shape(n, 'outputs')
        and not any(n.links)))]
    s = copy.deepcopy(found)
    # the game's node takes the field's name from its actor's settings; ours has it as a fixed text, written
    # the way the struct finder's own fixed text is
    name_in = s.inputs['string'][0]
    name_in.node, name_in.param, name_in.flags, name_in.value, name_in.sources = \
        -1, 0, q.inputs['string'][0].flags, '', None
    return s, q


def set_ai(data, tpl, ai, item, dungeon):
    """a ground item's AI with a "picked up" branch (`data`) under the name `ai`, which also sets the item's
    field of `dungeon`'s record when it is picked up: two new nodes after the file's own, one new link. Read
    back."""
    doc, orig = ainb.loads(data), ainb.loads(data)
    t_set, t_q = tpl
    both = dungeon_keys._both(doc)
    add = once_items._Adder(doc, ai)
    q = add.new(t_q, 'the dungeon\'s struct')
    a = add.new(t_set, 'the field set')
    nq, na = add.node(q), add.node(a)
    nq.inputs['string'][0].value = STRUCT % dungeon
    nq.links[VALUE] = [ainb.Link(a, 'Value', nq.links[VALUE][0].extra)]
    na.inputs['string'][0].value = field(item)
    struct_in = na.inputs['userdefined'][0]
    struct_in.node, struct_in.param, struct_in.sources = q, 0, None
    add.wants[a] = [q]
    added = add.done()
    doc.nodes[both].links[FLOW].insert(0, ainb.Link(a, '', ()))
    doc.filename = ai + '.root'
    out = doc.write()

    back = ainb.loads(out)
    if back.write() != out or back.filename != ai + '.root' or len(back.nodes) != len(orig.nodes) + added \
            or added != 2 or _doc_state(back) != _doc_state(orig) \
            or once_items._reached(back) != set(range(len(back.nodes))):
        raise SystemExit('read-back: %s differs from what was intended' % ai_path(ai))
    for i, (o, b) in enumerate(zip(orig.nodes, back.nodes)):
        if i == both:
            o.links[FLOW].insert(0, ainb.Link(a, '', ()))
        if _node_state(o) != _node_state(b):
            raise SystemExit('read-back: node %d of %s differs from what was intended' % (i, ai_path(ai)))
    if sets_of(out) != [(STRUCT % dungeon, field(item), True)]:
        raise SystemExit('read-back: %s does not set %s as intended: %r' % (ai_path(ai), flag(item, dungeon),
                                                                         sets_of(out)))
    return out


def sets_of(data):
    """what a ground item's AI sets in saved records when it is picked up, read from the file: [(struct,
    field, value)] of the OneShotSetGameDataBool nodes run at once with the mark and the death signal"""
    doc = ainb.loads(data)
    marks = [n for n in doc.nodes if n.type == once_items.SIMULTANEOUS
             and {once_items.N_MARK, once_items.N_SIGNAL} <= {doc.nodes[l.node].name for l in n.links[FLOW]}]
    out = []
    for n in marks:
        for l in n.links[FLOW]:
            x = doc.nodes[l.node]
            if x.name != N_SET:
                continue
            src = x.inputs['userdefined'][0]
            q = doc.nodes[src.node] if src.node >= 0 else None
            name_in = x.inputs['string'][0]
            if q is None or q.name != Q_STRUCT or [k.node for k in q.links[VALUE]] != [l.node] \
                    or name_in.node >= 0 or name_in.flags >> 31:
                raise SystemExit('%s: a set step whose struct or field is not named in the file' % doc.filename)
            out.append((q.inputs['string'][0].value, name_in.value,
                        next(i.value for i in x.inputs['bool'] if i.name == 'Value')))
    return out


def build(item, dungeon, kind, read_pack, read_table_rows, model_exists=lambda project: False, src=None):
    """`item` of `dungeon` for a kind of check (NAMES). Returns (name, pack data, {inner path: (data, the game
    file its size entry is worked out from, that file's contents)} for the files new to the game, {table: new
    row}, the game pack this pack is like, the loose files of its ground version as ground_items.build gives
    them: the copy of its animation that lifts it off the ground)."""
    if item not in ITEMS or dungeon not in DUNGEONS or kind not in NAMES:
        raise SystemExit('no %s of %s for %s' % (item, dungeon, kind))
    new = name(item, dungeon, kind)
    msg = message_name(item, dungeon)
    item_pack = sarc.Sarc.read(read_pack(pack_path(item)))
    shared = sarc.Sarc.read(read_pack(turn_items.AI_PACK)).files
    tables = {t: {r['__RowId']: r for r in read_table_rows(t)} for t in ground_items.TABLES}
    if new in tables['ActorInfo']:
        raise SystemExit('%s already exists in the game' % new)
    row = tables['PouchActorInfo'].get(item)
    if row is None or row.get('PouchSpecialDeal') != NOT_PUSHED or row.get('PouchStockable'):
        raise SystemExit('%s: its PouchActorInfo row is not "not put in the inventory" as expected' % item)
    # the item's own settings: already "not put in the inventory", and they name no inventory item
    settings_path = ground_items._ref_path(ground_items.item_components(item_pack.files, item)['PouchContentRef'])
    settings = item_pack.files.get(settings_path)
    sroot = byml.loads(settings).root if settings is not None else {}
    if 'PouchActor' in sroot or sroot.get('SpecialDeal') != dungeon_keys.not_pushed_value(read_pack):
        raise SystemExit('%s: its item settings (%s) are not as expected' % (item, settings_path))
    loose = {}
    if kind == 'chest':
        # the item's own actor under the dungeon's name
        like_pack, like_files, arc = pack_path(item), dict(item_pack.files), item_pack
        files = dict(item_pack.files)
        files[ap_path(new)] = files.pop(ap_path(item))
        new_inner = {ap_path(new): (files[ap_path(new)], ap_path(item), like_files[ap_path(item)])}
        rows = {t: type(tables[t][item])(tables[t][item]) for t in ground_items.TABLES if item in tables[t]}
    else:
        tpl = templates(read_pack)
        if kind == 'once':
            old, pack, inner, rows, loose = once_items.build_plain(
                item, read_pack, read_table_rows, model_exists, src or once_items.sources(read_pack))
            tpl_actor = ground_items.template_of(old)
            like_files = dict(shared)
            for actor in (tpl_actor, turn_items.DROP_TEMPLATE, once_items.HEART):
                like_files.update(sarc.Sarc.read(read_pack(pack_path(actor))).files)
            new_inner = {p: (d, like, like_files[like]) for p, (d, like) in inner.items()}
            old_ai = once_items.PLAIN_AI
            like_ai, like_info = ai_path(turn_items.BASE_AI), ai_info_path(turn_items.BASE_AI)
        else:
            old, pack, inner, rows, loose = ground_items.build(item, read_pack, read_table_rows, model_exists,
                                                               'token')
            tpl_actor = ground_items.template_of(old)
            like_files = dict(sarc.Sarc.read(read_pack(pack_path(tpl_actor))).files)
            new_inner = {p: (d, ground_items.new_file_like(p, tpl_actor)) for p, d in inner.items()}
            new_inner = {p: (d, like, like_files[like]) for p, (d, like) in new_inner.items()}
            old_ai = ground_items.TOKEN_FILES[0][len('AI/'):-len('.root.ainb')]
            like_ai, like_info = ai_path(old_ai), ai_info_path(old_ai)
        like_pack, arc = pack_path(tpl_actor), sarc.Sarc.read(pack)
        files = dict(arc.files)
        ai = AI_NAMES[kind] % (ITEMS[item][2], dungeon)
        dungeon_keys._swap_ai(files, new_inner, old, old_ai, ai, tpl, dungeon, like_ai, like_info, like_files,
                              step=lambda data: set_ai(data, tpl, ai, item, dungeon))
        if kind == 'once':                             # the plain version's AI is not used by this pack
            for p in (ai_path(old_ai), ai_info_path(old_ai)):
                del files[p]
                new_inner.pop(p, None)
        # a ground version stands for an inventory item (PouchActor), which is what the get scene would show
        # and name; ours has the item's own settings, which name none
        own = ground_items.pouch_param_path(old)
        if own not in files or own not in new_inner:
            raise SystemExit('%s: no item settings of its own found as expected' % old)
        files[own] = settings
        new_inner[own] = (settings, new_inner[own][1], new_inner[own][2])
        files = dungeon_keys.renamed(files, old, new)
        new_inner = {p.replace(old, new): (files[p.replace(old, new)], like, like_data)
                     for p, (_, like, like_data) in new_inner.items()}
    for t in rows:
        rows[t] = type(rows[t])(rows[t])
        rows[t]['__RowId'] = new
    prow = type(row)(row)                              # the item's own row: already not put in the inventory
    prow['__RowId'] = new
    rows['PouchActorInfo'] = prow
    # its name, in both places (tools/dungeon_keys.py): the chest version, which is named itself
    if rows['ActorInfo'].get('ActorName') != item:
        raise SystemExit('%s: its ActorInfo row is not named %s as expected' % (new, item))
    rows['ActorInfo']['ActorName'] = type(rows['ActorInfo']['ActorName'])(msg)
    adoc = byml.loads(files[ap_path(new)])
    adoc.root = type(adoc.root)(adoc.root)
    comp = type(adoc.root['Components'])(adoc.root['Components'])
    comp['ActorNameRef'] = NAME_REF % msg
    adoc.root['Components'] = comp
    files[ap_path(new)] = byml.dumps(adoc)
    new_inner[ap_path(new)] = (files[ap_path(new)],) + tuple(new_inner[ap_path(new)][1:])
    out = copy.copy(arc)
    out.files = files
    out.align = {p: arc.align.get(p, 8) for p in files}
    pack = out.write()

    back = sarc.Sarc.read(pack).files
    got = ground_items.resolved_components(back, new)
    game = ground_items.item_components(item_pack.files, item)
    sroot = byml.loads(back[ground_items._ref_path(got['PouchContentRef'])]).root
    if set(back) != set(files) or any(back[p] != d for p, d in files.items()) or 'PouchActor' in sroot \
            or sroot.get('SpecialDeal') != dungeon_keys.not_pushed_value(read_pack) \
            or got.get('ActorNameRef') != NAME_REF % msg or got.get('ModelInfoRef') != game['ModelInfoRef'] \
            or any(p not in back for p in new_inner):
        raise SystemExit('read-back: %s of %s (%s) differs from what was intended' % (item, dungeon, new))
    if kind != 'chest' and (got.get('AIInfoRef') != '?' + ai_info_path(ai) or sets_of(back[ai_path(ai)]) != [
            (STRUCT % dungeon, field(item), True)]):
        raise SystemExit('read-back: %s does not set %s' % (new, flag(item, dungeon)))
    return new, pack, new_inner, rows, like_pack, loose
