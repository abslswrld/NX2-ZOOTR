"""A small key that belongs to one dungeon, wherever it is found (to test in game).

Found in the game's files (2026-11-24):
- A dungeon's keys are a saved number: GameData has a struct `DungeonInfo.<Dungeon>` for each dungeon
  (DUNGEONS), with the fields `SmallKeyNum` (the keys Link holds there), `IsGetBossKey`, `IsGetMap`,
  `IsGetCompass`. The Forest Temple's doors open while `DungeonInfo.ForestTemple.SmallKeyNum` is above 0.
- The game counts a key for the dungeon Link is in, and has no way to say another one: its AI nodes
  (`OneShotDungeonGetSmallKey`, `OneShotDungeonUseSmallKey`, `QueryDungeonGetSmallKeyNum`) and event actions
  (`EventGetDungeonSmallKey`, in the chests' flow) take no dungeon. A key on the ground is counted by its item
  settings (`PouchSpecialDeal: SmallKey`), in code. So the game's own key found outside its dungeon cannot count
  for it.
- The game does have a key that sets a named flag when it is picked up: the Gerudo Fortress keys. Their AI
  (`AI/Obj_Dungeon_SmallKey_GerudoFortress_01.root.ainb`): dead of reason 10 (picked up) ->
  `OneShotSetGameDataBool` on a field of the struct `QueryGetNonStructGameDataStruct` finds by its name.
  `OneShotAddGameDataInt` adds to a number the same way (`AI/NpcCommon.event.root.ainb`: the shops' sold
  counters), and event flows add to one with `GameDataActor.EventTriggerAddOrSubGameDataInt`
  (MiniGame_SequentialChoiceTreasure: the treasure chest game's own key count).
- A new inventory item is not possible: it would need saved flags of its own, which the save file has no
  place for. So the key is not an inventory item: its item settings are "not put in the inventory"
  (`NotPushToPouch`, as the treasure chest game's key, Obj_MiniGame_SmallKey), and what counts is the number.

So a key for dungeon D (`Item_Dungeon_SmallKey@D` in an assignment) is an item of its own, never the game's
small key (the game's "dungeon Link is in" code must not run for it, in D or outside):
- on the ground (a pot, a rock, a bush, a freestanding item: KIND 'once'; a Gold Skulltula: 'token'): the
  builder's own version of the key for that kind (tools/once_items.py, tools/ground_items.py) under the
  dungeon's name, with one more step in its "picked up" branch: `OneShotAddGameDataInt` SmallKeyNum + 1 on
  `DungeonInfo.D`;
- in a chest ('chest'): the key's own actor under the dungeon's name; the chest gets an opening event of our
  own around its usual one that adds 1 to `DungeonInfo.D.SmallKeyNum` (tools/build_mod.py, tbox_key_*).
Each has the key's model, name and get scene; its item settings are the key's with `NotPushToPouch`, no
inventory item named, not counted; its row in PouchActorInfo says the same.

In its own dungeon the key is the game's own small key (tools/build_mod.py decides by the check's map): there
the game counts and shows it itself, exactly as it does its own (in game 2026-11-24: a dungeon's key picked up
in its dungeon showed the count from before the key, and a chest showed none). Outside, the count on screen
is the count of the place Link is in, so a key of another dungeon cannot show its own.

The dungeon's name in the messages (every key of a dungeon placed outside it: the user, 2026-11-24; it began as
an option, `Item_Dungeon_SmallKey@D+name`, which is still read): an item's
texts are `<name>_Name`, `_GetMessage`, `_GetCaption` in ActorMsg/PouchContent.msbt. An item has that name in
two places, and the game's own item with texts of its own (the treasure chest game's key, Obj_MiniGame_SmallKey:
"Door Key") has its name in both:
- its actor file's `ActorNameRef` (`?ActorSystem/ActorName/<name>.engine__actor__ActorName.bgyml`; no such
  file exists anywhere in the game, the reference only carries the name). The item's AI hands this name to
  the get message: `EventTriggerSetOwnNameToMessage` writes `QueryGenericGetActorName`'s ActorName into the flag
  `UI_MessageTargetActorName`;
- the `ActorName` of its row in ActorInfo. In game 2026-11-24 a key with only this one changed kept the game's
  text ("You found a small key!") and lost the count on screen: the get event's "is it a small key" goes by
  the row, the text by the actor file.
A named key has a name of its own (MESSAGE_NAME) in both, and three texts under it, with the dungeon's name as
the game writes it (LocationMsg/Location.msbt, the label is the dungeon's map name).

That name must be an item that is named so itself (in game 2026-11-24, second test: a named key in a chest
showed "You found a small key! (Forest Temple)", a named key from a pot still the game's text). A key in a
chest is shown as it is. A key picked up from the ground is not: the game holds up the item its name stands
for (the game's Obj_Dungeon_SmallKey is named Item_Dungeon_SmallKey, and Item_Dungeon_SmallKey is named
itself), and the text is that item's. The second test's name was the dungeon's chest key without the name,
which is named Item_Dungeon_SmallKey. So the name is the dungeon's NAMED chest key (`Item_NX2KN_<dungeon>`),
which is named itself and is built with every named key.

The name's colour (`COLOURS`, `build_mod.py --key-colour DUNGEON=COLOUR`): the game's texts colour words with
the tag (0, 3) and a number, and end with the same tag and 0xFFFF. The number is the place in the game's list
of text colours, `MessageColorArray` in COLOUR_TABLE (a file of the pack the game loads first, COLOUR_PACK):
eight colours, each `Red`, `Green`, `Blue`, `Alpha` (left out: 0, 0, 0, 255) and a `ColorName` (a name's
hash: 1 is "Gray", 3 is "Green"; 0 has none). 0: (138, 0, 0), 1: (80, 45, 20), 2: (255, 0, 254), 3: (20, 152,
55), 4 and 5: (255, 253, 198) half and two thirds see-through, 6: (255, 53, 25), 7: (133, 125, 104). Every
language's texts use 0, 1, 3, 4 and 5 and no other (0: names and places in talk; 1: Navi's thoughts; 3: "uses
1 magic power" in the magic items' captions; 4 and 5: the staff roll).
In game 2026-11-24 (third test): the get window shows the colour; 3 is green, 0 is red, 1, 4 and 5 look gray.
The user's colours: Forest Temple green, Fire Temple red, Water Temple blue, Shadow Temple purple, Spirit
Temple orange. The game has no blue or purple.
In game 2026-11-24 (fourth test): the list cannot be made longer. With blue, purple and orange added behind
the game's eight (numbers 8, 9, 10), the game started as usual and all three names came out orange: a number
past the game's eight is not looked up in the file.
In game 2026-11-24 (fifth test): with place 2 recoloured blue and place 7 purple, the Water Temple's name
(number 2) was blue and the Shadow Temple's (7) purple.
In game 2026-11-24 (the look after it, with places 4, 6 and 7 recoloured): the Fire Temple's name (number 0)
came out in the Spirit Temple's orange (place 6) and the Bottom of the Well's (number 1) in purple (place 7).
So **in the get window the game shows place 6 for number 0 and place 7 for number 1**: 6 (255, 53, 25) is the
red and 7 (133, 125, 104) the gray for that window, 0 (138, 0, 0) and 1 (80, 45, 20) are their darker
versions. That fits every test: "red" and "gray" in the third test were places 6 and 7. Places 6 and 7 are
the game's and are never changed (a red or a gray word anywhere such a window is used would change with them).

What is left for colours of our own (OUR_COLOURS), each the three colour values of a place, made solid, its
name kept, and only when a named key of the build uses it:
- place 2 (a loud pink, 255, 0, 254; no text uses it): blue. Seen in game.
- one place behind the game's eight (number 8): purple. A number past the list shows the list's last colour
  (fourth test: 8, 9 and 10 all showed the last one added), so exactly one colour can be added there.
- the staff roll's two places, 4 (17 headings of the credits) and 5 (115 names of the credits), both (255,
  253, 198) and see-through: orange (225, 130, 0) and a darker orange (185, 85, 15). In a build with a Spirit
  Temple or a Training Ground key outside its dungeon, those lines of the credits are that orange. Place 4
  recoloured was seen in game (the Training Ground's name, "good").
The user's colours: Forest Temple green (3), Fire Temple red (0), Water Temple blue, Shadow Temple purple,
Spirit Temple orange, Gerudo Training Ground "different orange?", Bottom of the Well "gray?" (1), Ganon's
Castle none. Not seen in game: purple as the added place, the oranges in places 4 and 5.

Not yet: gifts, scrubs, shop shelves, songs.
Every new node is a copy of a game node of the same type, found by what it is and checked before it is used.
"""
import copy
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from formats import sarc, byml, ainb  # noqa: E402
import ground_items  # noqa: E402
import once_items  # noqa: E402
import turn_items  # noqa: E402
from ground_items import pack_path, ap_path, pouch_param_path, _ref_path  # noqa: E402
from shop_items import ai_path, ai_info_path, _node_state, _doc_state  # noqa: E402

KEY_ITEM = 'Item_Dungeon_SmallKey'
SEP = '@'
# the dungeons that have a key count: the name of their struct in GameData (DungeonInfo.<name>)
DUNGEONS = ('InsideTheDekuTree', 'DodongoCavern', 'InsideJabuJabuBelly', 'ForestTemple', 'FireTemple',
            'WaterTemple', 'ShadowTemple', 'SpiritTemple', 'BottomOfTheWell', 'IceCavern', 'GerudoFortress',
            'GerudoTrainingGround', 'InsideGanonCastle')
STRUCT, FIELD = 'DungeonInfo.%s', 'SmallKeyNum'
# kind -> (name of the version, the kinds of check it is for)
NAMES = {'once': 'Obj_NX2K_%s', 'token': 'Obj_NX2K_GS_%s', 'chest': 'Item_NX2K_%s'}
# the same with the dungeon's name in its messages (the +name form)
NAMED_NAMES = {'once': 'Obj_NX2KN_%s', 'token': 'Obj_NX2KN_GS_%s', 'chest': 'Item_NX2KN_%s'}
NAMED = '+name'
MESSAGE_NAME = NAMED_NAMES['chest']              # the name of a named key: its texts are <this>_Name...
COLOURED = '_GetMessage'                         # the text in which the dungeon's name is coloured
COLOUR_TAG = (0, 3)                              # the tag that colours what follows; COLOUR_END ends it
COLOUR_END = 0xFFFF
COLOUR_PACK = 'Pack/Bootup.Nin_Ounce_NVN2.pack'
COLOUR_TABLE = 'UI/Message/MessageColorTable/MessageColorTable.game__ui__MessageColorTable.bgyml'
COLOUR_LIST = 'MessageColorArray'
GAME_COLOUR_COUNT = 8                            # the game's list; a number past it shows the last colour
ADDED_PLACE = GAME_COLOUR_COUNT                  # the one place that can be added behind the game's
KEPT_PLACES = (0, 1, 3, 6, 7)                    # used by the game's texts and windows: never changed
# colours by name: name -> (its place, the (red, green, blue) that place gets)
OUR_COLOURS = {'blue': (2, (30, 80, 190)), 'purple': (ADDED_PLACE, (115, 45, 160)),
               'orange': (4, (225, 130, 0)), 'dark-orange': (5, (185, 85, 15))}
# dungeon -> the colour of its name: a place in the game's list, or one of OUR_COLOURS (the user, 2026-11-24).
# The places with small keys (the user; the game's maps agree): these seven and Ganon's Castle, whose colour
# "is not important" (none). Gerudo Fortress has keys of its own kind.
COLOURS = {'ForestTemple': 3, 'FireTemple': 0, 'WaterTemple': 'blue', 'ShadowTemple': 'purple',
           'SpiritTemple': 'orange', 'GerudoTrainingGround': 'dark-orange', 'BottomOfTheWell': 1}
NAME_REF = '?ActorSystem/ActorName/%s.engine__actor__ActorName.bgyml'   # an actor file's ActorNameRef
MESSAGE_FILE = 'ActorMsg/PouchContent.msbt'
LOCATION_FILE = 'LocationMsg/Location.msbt'      # the game's names of places, by map name
MESSAGES = (('_Name', 'Small Key (%s)'), ('_GetMessage', 'You found a small key! (%s)'),
            ('_GetCaption', 'It opens locked doors in that place,\nwherever you found it.'))
CHECK_KINDS = {'pot': 'once', 'rock': 'once', 'bush': 'once', 'freestanding': 'once', 'skulltula': 'token',
               'chest': 'chest'}
PREFIXES = tuple(n % '' for n in list(NAMES.values()) + list(NAMED_NAMES.values()))
AI_NAMES = {'once': 'NX2_Key_%s', 'token': 'NX2_KeyGS_%s'}
# where the copied nodes and values come from
ADD_SOURCE = 'AI/NpcCommon.event.root.ainb'                         # OneShotAddGameDataInt
STRUCT_SOURCE = 'AI/Obj_Dungeon_SmallKey_GerudoFortress_01.root.ainb'   # QueryGetNonStructGameDataStruct
NOT_PUSHED_ACTOR = 'Obj_MiniGame_SmallKey'                          # item settings "not put in the inventory"
NOT_PUSHED_FILE = 'Component/PouchContentParam/NotPushToPouch.game__component__PouchContentParam.bgyml'
NOT_PUSHED, SMALL_KEY = 'NotPushToPouch', 'SmallKey'                # PouchSpecialDeal (PouchActorInfo)
N_ADD, Q_STRUCT = 'OneShotAddGameDataInt', 'QueryGetNonStructGameDataStruct'
VALUE, FLOW, STRING = once_items.VALUE, once_items.FLOW, once_items.STRING


def parse(item):
    """(the dungeon, whether its messages name it) of `Item_Dungeon_SmallKey@Dungeon`, or None for any other
    item. Its messages always name it (the user, 2026-11-24: every key says its dungeon's name); the first
    form of that, `...@Dungeon+name`, is still read and means the same"""
    if SEP not in item:
        return None
    key, dungeon = item.split(SEP, 1)
    if dungeon.endswith(NAMED):
        dungeon = dungeon[:-len(NAMED)]
    named = True
    if key != KEY_ITEM:
        raise SystemExit('%s: only %s%s<dungeon> can name a dungeon' % (item, KEY_ITEM, SEP))
    if dungeon not in DUNGEONS:
        raise SystemExit('%s: no dungeon %s; the dungeons with keys: %s' % (item, dungeon, ', '.join(DUNGEONS)))
    return dungeon, named


def kind_for(check_kind, cid):
    if check_kind not in CHECK_KINDS:
        raise SystemExit('%s: a dungeon\'s key cannot be put on a %s yet (only: %s)'
                         % (cid, check_kind, ', '.join(sorted(CHECK_KINDS))))
    return CHECK_KINDS[check_kind]


def name(dungeon, kind, named=False):
    return (NAMED_NAMES if named else NAMES)[kind] % dungeon


def colour_tag(number):
    """the tag that starts colour `number` (COLOUR_END: back to the text's own), as it stands in a text"""
    return (b'\x0e' + struct.pack('<HHHH', COLOUR_TAG[0], COLOUR_TAG[1], 2, number)).decode('utf-8',
                                                                                            'surrogateescape')


def colour_number(colour):
    """the number a text names a colour by: a place in the game's list, or the place one of OUR_COLOURS has"""
    if isinstance(colour, int) and not isinstance(colour, bool) and 0 <= colour < GAME_COLOUR_COUNT:
        return colour                                  # in the get window 0 is shown as place 6 and 1 as place 7
    if colour in OUR_COLOURS:
        return OUR_COLOURS[colour][0]
    raise SystemExit('colour %r: give a place in the game\'s list of %d text colours (0 to %d) or one of %s'
                     % (colour, GAME_COLOUR_COUNT, GAME_COLOUR_COUNT - 1, ', '.join(sorted(OUR_COLOURS))))


def colour_table(table_data, colours):
    """the game's list of text colours with the places of `colours` (names of OUR_COLOURS) recoloured (its
    three colour values; solid; its name kept; the added place is a new entry behind the game's), or None when
    there are none; stops when the file is not the list this was made for"""
    doc = byml.loads(table_data)
    game = doc.root.get(COLOUR_LIST) if isinstance(doc.root, dict) else None
    fields = {'Red', 'Green', 'Blue', 'Alpha', 'ColorName'}
    if not isinstance(game, list) or len(game) != GAME_COLOUR_COUNT or set(doc.root) != {COLOUR_LIST} \
            or any(not isinstance(e, dict) or not set(map(str, e)) <= fields for e in game) \
            or byml.dumps(doc) != table_data:
        raise SystemExit('%s is not the list of text colours this was made for' % COLOUR_TABLE)
    number = type(game[0]['Red'])
    changed = {}
    for name in sorted(set(colours), key=lambda n: OUR_COLOURS[n][0]):
        place, rgb = OUR_COLOURS[name]
        if place in KEPT_PLACES or place in changed or place > ADDED_PLACE:
            raise SystemExit('colour %s: place %d of the list cannot be taken' % (name, place))
        entry = type(game[0])() if place == ADDED_PLACE else type(game[place])(game[place])
        entry.pop('Alpha', None)                       # solid (the staff roll's places are see-through)
        for k, v in zip(('Red', 'Green', 'Blue'), rgb):
            entry.pop(k, None)
            if v:                                      # as the game's entries: a 0 is left out
                entry[k] = number(v)
        entry = type(entry)(sorted(entry.items()))
        if place == ADDED_PLACE:
            game.append(entry)
        else:
            game[place] = entry
        changed[place] = rgb
    if not changed:
        return None
    new = byml.dumps(doc)
    back, was = byml.loads(new).root[COLOUR_LIST], byml.loads(table_data).root[COLOUR_LIST]
    if len(back) != len(was) + (ADDED_PLACE in changed) or any(
            (e != was[i]) if i not in changed else
            ((int(e.get('Red', 0)), int(e.get('Green', 0)), int(e.get('Blue', 0))) != changed[i]
             or 'Alpha' in e or e.get('ColorName') != (was[i].get('ColorName') if i < len(was) else None))
            for i, e in enumerate(back)):
        raise SystemExit('read-back: %s differs from what was intended' % COLOUR_TABLE)
    return new


def messages(dungeon, place, colour=None):
    """the texts of a named key: {label: text}; `place`: the dungeon's name as the game writes it; `colour`:
    the number of the colour the name has in the get message (colour_number; None: the text's own)"""
    out = {}
    for tail, text in MESSAGES:
        shown = place
        if colour is not None and tail == COLOURED:
            shown = colour_tag(colour) + place + colour_tag(COLOUR_END)
        out[(MESSAGE_NAME % dungeon) + tail] = (text % shown if '%s' in text else text) + '\x00'
    return out


def is_ours(item):
    return item.startswith(PREFIXES)


def dungeon_of(version):
    """(dungeon, kind) of a version's name"""
    for names in (NAMED_NAMES, NAMES):
        for kind, n in sorted(names.items(), key=lambda x: -len(x[1])):
            if version.startswith(n % ''):
                return version[len(n % ''):], kind
    raise KeyError(version)


def flag(dungeon):
    """the saved number a key of this dungeon adds to"""
    return (STRUCT % dungeon) + '.' + FIELD


def _walk(v, f):
    if isinstance(v, dict):
        return type(v)((k, _walk(x, f)) for k, x in v.items())
    if isinstance(v, list):
        return type(v)(_walk(x, f) for x in v)
    if isinstance(v, str):
        return type(v)(f(v))
    return v


def renamed(files, old, new):
    """the files of a pack with the actor `old` called `new`: in the names of its own files and in every text
    of its parameter files (no other file names it)"""
    out = {}
    for path, data in files.items():
        if path.endswith('.bgyml'):
            doc = byml.loads(data)
            root = _walk(doc.root, lambda s: s.replace(old, new))
            if root != doc.root:
                doc.root = root
                data = byml.dumps(doc)
        elif old.encode() in data:
            raise SystemExit('%s: %s names %s in a file that is not a parameter file' % (new, path, old))
        out[path.replace(old, new)] = data
    if len(out) != len(files) or any(old.encode() in d for d in out.values()) or any(old in p for p in out):
        raise SystemExit('read-back: %s is still named in the pack of %s' % (old, new))
    return out


def not_pushed_value(read_pack):
    """the SpecialDeal value "not put in the inventory", read from the game's own settings file"""
    files = sarc.Sarc.read(read_pack(pack_path(NOT_PUSHED_ACTOR))).files
    root = byml.loads(files[NOT_PUSHED_FILE]).root if NOT_PUSHED_FILE in files else {}
    if 'SpecialDeal' not in root:
        raise SystemExit('%s: %s not found as expected' % (NOT_PUSHED_ACTOR, NOT_PUSHED_FILE))
    return root['SpecialDeal']


def key_settings(key_files, read_pack):
    """the item settings of a dungeon's key: the game's key's own (KeyItemSmallKey) without the inventory item
    it stands for and without a count, with "not put in the inventory" """
    comp = ground_items.item_components(key_files, KEY_ITEM)
    path = _ref_path(comp['PouchContentRef'])
    doc = byml.loads(key_files[path])
    value = not_pushed_value(read_pack)
    if 'SpecialDeal' not in doc.root or 'PouchActor' not in doc.root or doc.root['SpecialDeal'] == value \
            or '$parent' not in doc.root:
        raise SystemExit('%s: its item settings (%s) are not as expected' % (KEY_ITEM, path))
    root = type(doc.root)(doc.root)
    del root['PouchActor']
    root.pop('EnableStock', None)
    root['SpecialDeal'] = type(doc.root['SpecialDeal'])(value)
    doc.root = root
    return byml.dumps(doc), path


def key_row(row, name):
    """the PouchActorInfo row of a dungeon's key: the game's key's, not put in the inventory, not counted"""
    if row.get('PouchSpecialDeal') != SMALL_KEY:
        raise SystemExit('%s: its PouchActorInfo row is not a small key\'s' % name)
    row = type(row)(row)
    row['__RowId'] = name
    row['PouchSpecialDeal'] = type(row['PouchSpecialDeal'])(NOT_PUSHED)
    row.pop('PouchStockable', None)
    return row


def templates(read_pack):
    """the two nodes copied: (OneShotAddGameDataInt, QueryGetNonStructGameDataStruct), each found by what it is"""
    shared = sarc.Sarc.read(read_pack(turn_items.AI_PACK)).files
    add_doc, q_doc = ainb.loads(shared[ADD_SOURCE]), ainb.loads(shared[STRUCT_SOURCE])
    types = ainb.PARAM_TYPES

    def shape(n, kind):
        return [(t, x.name) for t in types for x in getattr(n, kind)[t]]

    add = add_doc.nodes[once_items._one(add_doc, N_ADD, lambda n: (
        n.name == N_ADD and once_items._plain(n) and not n.flags
        and once_items._imm(n) == [('bool', 'ExecuteEveryFrame', False)]
        and shape(n, 'inputs') == [('int', 'GameDataIndex'), ('int', 'Value'), ('string', 'GameDataName'),
                                   ('userdefined', 'ParentStruct')]
        and [x.value for x in n.inputs['int']] == [-1, 1] and all(x.node < 0 for x in n.inputs['int'])
        and n.inputs['userdefined'][0].node >= 0 and not shape(n, 'outputs')))]
    q = q_doc.nodes[once_items._one(q_doc, Q_STRUCT, lambda n: (
        n.name == Q_STRUCT and once_items._plain(n) and n.flags == 1 and not n.preconditions
        and once_items._imm(n) == [('bool', 'DispError', True), ('bool', 'OutputOnlyOnEnter', False)]
        and shape(n, 'inputs') == [('int', 'GameDataIndex'), ('bool', 'IsDirect'), ('string', 'GameDataFullName')]
        and n.inputs['int'][0].value == -1 and n.inputs['bool'][0].value is False
        and n.inputs['string'][0].node < 0 and isinstance(n.inputs['string'][0].value, str)
        and shape(n, 'outputs') == [('userdefined', 'Value')]
        and [(k, [l.name for l in links]) for k, links in enumerate(n.links) if links] == [(VALUE, ['Value'])]))]
    return add, q


def _both(doc):
    """the "all at once" node of a ground item's "picked up" branch: the one that runs the mark and the death
    signal (once_items: the token's own branch)"""
    want = sorted([once_items.N_MARK, once_items.N_SIGNAL])
    hits = [i for i, n in enumerate(doc.nodes) if n.type == once_items.SIMULTANEOUS
            and sorted(doc.nodes[l.node].name for l in n.links[FLOW]) == want]
    if len(hits) != 1:
        raise SystemExit('%s: %d "picked up" steps that run the mark and the death signal, expected 1'
                         % (doc.filename, len(hits)))
    return hits[0]


def count_ai(data, tpl, ai, dungeon):
    """a ground item's AI with a "picked up" branch (`data`) under the name `ai`, which also adds 1 to the key
    count of `dungeon` when it is picked up: two new nodes after the file's own, one new link. Read back."""
    doc, orig = ainb.loads(data), ainb.loads(data)
    t_add, t_q = tpl
    both = _both(doc)
    add = once_items._Adder(doc, ai)
    q = add.new(t_q, 'the dungeon\'s struct')
    a = add.new(t_add, 'one key more')
    nq, na = add.node(q), add.node(a)
    fixed = nq.inputs['string'][0]
    fixed.value = STRUCT % dungeon
    nq.links[VALUE] = [ainb.Link(a, 'Value', nq.links[VALUE][0].extra)]
    name_in = na.inputs['string'][0]
    name_in.node, name_in.param, name_in.flags, name_in.value, name_in.sources = -1, 0, fixed.flags, FIELD, None
    na.links[STRING] = []
    struct_in = na.inputs['userdefined'][0]
    struct_in.node, struct_in.param, struct_in.sources = q, 0, None
    if any(links for k, links in enumerate(na.links)):
        raise SystemExit('%s: the node copied for "one key more" still links elsewhere' % ai)
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
    if counts_of(out) != [(STRUCT % dungeon, FIELD, 1)]:
        raise SystemExit('read-back: %s does not add one key of %s as intended: %r'
                         % (ai_path(ai), dungeon, counts_of(out)))
    return out


def counts_of(data):
    """what a ground item's AI adds to saved numbers when it is picked up, read from the file: [(struct, field,
    how much)] of the OneShotAddGameDataInt nodes run at once with the mark and the death signal"""
    doc = ainb.loads(data)
    marks = [n for n in doc.nodes if n.type == once_items.SIMULTANEOUS
             and {once_items.N_MARK, once_items.N_SIGNAL} <= {doc.nodes[l.node].name for l in n.links[FLOW]}]
    out = []
    for n in marks:
        for l in n.links[FLOW]:
            x = doc.nodes[l.node]
            if x.name != N_ADD:
                continue
            src = x.inputs['userdefined'][0]
            q = doc.nodes[src.node] if src.node >= 0 else None
            if q is None or q.name != Q_STRUCT or [k.node for k in q.links[VALUE]] != [l.node]:
                raise SystemExit('%s: a count step whose struct is not found by name' % doc.filename)
            out.append((q.inputs['string'][0].value, x.inputs['string'][0].value,
                        next(i.value for i in x.inputs['int'] if i.name == 'Value')))
    return out


def _swap_ai(files, new_inner, name, old_ai, ai, tpl, dungeon, like_ai, like_info, like_files):
    """the pack's AI `old_ai` becomes `ai` (with the count), named by an AI info file of its own, and the actor
    names that"""
    files[ai_path(ai)] = count_ai(files[ai_path(old_ai)], tpl, ai, dungeon)
    idoc = byml.loads(files[ai_info_path(old_ai)])
    want = 'Work/AI/Root/%s.root.ain' % old_ai
    if idoc.root.get('RootAIRef') != want:
        raise SystemExit('%s not as expected' % ai_info_path(old_ai))
    idoc.root = _walk(idoc.root, lambda s: s.replace(want, 'Work/AI/Root/%s.root.ain' % ai))
    files[ai_info_path(ai)] = byml.dumps(idoc)
    new_inner[ai_path(ai)] = (files[ai_path(ai)], like_ai, like_files[like_ai])
    new_inner[ai_info_path(ai)] = (files[ai_info_path(ai)], like_info, like_files[like_info])
    adoc = byml.loads(files[ap_path(name)])
    adoc.root = type(adoc.root)(adoc.root)
    comp = type(adoc.root['Components'])(adoc.root['Components'])
    comp['AIInfoRef'] = '?' + ai_info_path(ai)
    adoc.root['Components'] = comp
    files[ap_path(name)] = byml.dumps(adoc)
    new_inner[ap_path(name)] = (files[ap_path(name)],) + tuple(new_inner[ap_path(name)][1:])


def build(dungeon, kind, read_pack, read_table_rows, model_exists=lambda project: False, src=None,
          named=False):
    """the key of `dungeon` for a kind of check (NAMES). Returns (name, pack data, {inner path: (data, the
    game file its size entry is worked out from, that file's contents)} for the files new to the game, {table:
    new row}, the game pack this pack is like)."""
    if dungeon not in DUNGEONS or kind not in NAMES:
        raise SystemExit('no key of %s for %s' % (dungeon, kind))
    new = name(dungeon, kind, named)
    key_pack = sarc.Sarc.read(read_pack(pack_path(KEY_ITEM)))
    settings, settings_like = key_settings(key_pack.files, read_pack)
    shared = sarc.Sarc.read(read_pack(turn_items.AI_PACK)).files
    tables = {t: {r['__RowId']: r for r in read_table_rows(t)} for t in ground_items.TABLES}
    if new in tables['ActorInfo']:
        raise SystemExit('%s already exists in the game' % new)
    if kind == 'chest':
        # the key's own actor under the dungeon's name, with item settings of its own
        like_pack, like_files, arc = pack_path(KEY_ITEM), dict(key_pack.files), key_pack
        files = dict(key_pack.files)
        adoc = byml.loads(files.pop(ap_path(KEY_ITEM)))
        adoc.root = type(adoc.root)(adoc.root)
        comp = type(adoc.root['Components'])(adoc.root['Components'])
        comp['PouchContentRef'] = '?' + pouch_param_path(new)
        adoc.root['Components'] = comp
        files[ap_path(new)] = byml.dumps(adoc)
        files[pouch_param_path(new)] = settings
        new_inner = {ap_path(new): (files[ap_path(new)], ap_path(KEY_ITEM), like_files[ap_path(KEY_ITEM)]),
                     pouch_param_path(new): (settings, settings_like, like_files[settings_like])}
        rows = {t: type(tables[t][KEY_ITEM])(tables[t][KEY_ITEM]) for t in ground_items.TABLES
                if KEY_ITEM in tables[t]}
    else:
        tpl = templates(read_pack)
        if kind == 'once':
            old, pack, inner, rows, loose = once_items.build_plain(
                KEY_ITEM, read_pack, read_table_rows, model_exists, src or once_items.sources(read_pack))
            tpl_actor = ground_items.template_of(old)
            like_files = dict(shared)
            for actor in (tpl_actor, turn_items.DROP_TEMPLATE, once_items.HEART):
                like_files.update(sarc.Sarc.read(read_pack(pack_path(actor))).files)
            new_inner = {p: (d, like, like_files[like]) for p, (d, like) in inner.items()}
            old_ai = once_items.PLAIN_AI
            like_ai, like_info = ai_path(turn_items.BASE_AI), ai_info_path(turn_items.BASE_AI)
        else:
            old, pack, inner, rows, loose = ground_items.build(KEY_ITEM, read_pack, read_table_rows,
                                                               model_exists, 'token')
            tpl_actor = ground_items.template_of(old)
            like_files = dict(sarc.Sarc.read(read_pack(pack_path(tpl_actor))).files)
            new_inner = {p: (d, ground_items.new_file_like(p, tpl_actor)) for p, d in inner.items()}
            new_inner = {p: (d, like, like_files[like]) for p, (d, like) in new_inner.items()}
            old_ai = ground_items.TOKEN_FILES[0][len('AI/'):-len('.root.ainb')]
            like_ai, like_info = ai_path(old_ai), ai_info_path(old_ai)
        if loose:
            raise SystemExit('%s: a lifted animation was not expected for the key' % old)
        like_pack, arc = pack_path(tpl_actor), sarc.Sarc.read(pack)
        files = dict(arc.files)
        ai = AI_NAMES[kind] % dungeon
        _swap_ai(files, new_inner, old, old_ai, ai, tpl, dungeon, like_ai, like_info, like_files)
        if kind == 'once':                             # the plain version's AI is not used by this pack
            for p in (ai_path(old_ai), ai_info_path(old_ai)):
                del files[p]
                new_inner.pop(p, None)
        files[pouch_param_path(old)] = settings
        like = new_inner[pouch_param_path(old)][1]
        new_inner[pouch_param_path(old)] = (settings, like, like_files[like])
        files = renamed(files, old, new)
        new_inner = {p.replace(old, new): (files[p.replace(old, new)], like, like_data)
                     for p, (_, like, like_data) in new_inner.items()}
    for t in rows:
        rows[t] = type(rows[t])(rows[t])
        rows[t]['__RowId'] = new
    rows['PouchActorInfo'] = key_row(tables['PouchActorInfo'][KEY_ITEM], new)
    if named:                                          # its texts are found under a name of its own
        if rows['ActorInfo'].get('ActorName') != KEY_ITEM:
            raise SystemExit('%s: its ActorInfo row is not named %s as expected' % (new, KEY_ITEM))
        if (kind == 'chest') != (new == MESSAGE_NAME % dungeon):
            raise SystemExit('%s: the name of the named keys must be the named chest key' % new)
        rows['ActorInfo']['ActorName'] = type(rows['ActorInfo']['ActorName'])(MESSAGE_NAME % dungeon)
        adoc = byml.loads(files[ap_path(new)])         # and so does its actor file: the get message's name
        adoc.root = type(adoc.root)(adoc.root)
        comp = type(adoc.root['Components'])(adoc.root['Components'])
        comp['ActorNameRef'] = NAME_REF % (MESSAGE_NAME % dungeon)
        adoc.root['Components'] = comp
        files[ap_path(new)] = byml.dumps(adoc)
        new_inner[ap_path(new)] = (files[ap_path(new)],) + tuple(new_inner[ap_path(new)][1:])
    out = copy.copy(arc)
    out.files = files
    out.align = {p: arc.align.get(p, 8) for p in files}
    pack = out.write()

    back = sarc.Sarc.read(pack).files
    got = ground_items.resolved_components(back, new)
    sroot = byml.loads(back[_ref_path(got['PouchContentRef'])]).root
    if set(back) != set(files) or any(back[p] != d for p, d in files.items()) \
            or got.get('PouchContentRef') != '?' + pouch_param_path(new) or 'PouchActor' in sroot \
            or sroot.get('SpecialDeal') != not_pushed_value(read_pack) \
            or got.get('ActorNameRef') != (
                NAME_REF % (MESSAGE_NAME % dungeon) if named
                else ground_items.item_components(key_pack.files, KEY_ITEM)['ActorNameRef']) \
            or any(p not in back for p in new_inner):
        raise SystemExit('read-back: the key of %s (%s) differs from what was intended' % (dungeon, new))
    if kind != 'chest' and (got.get('AIInfoRef') != '?' + ai_info_path(ai) or counts_of(back[ai_path(ai)]) != [
            (STRUCT % dungeon, FIELD, 1)]):
        raise SystemExit('read-back: %s does not count for %s' % (new, dungeon))
    return new, pack, new_inner, rows, like_pack
