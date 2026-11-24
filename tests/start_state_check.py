"""Starting state test: the items and flags a new file has (tools/start_state.py; --start and --start-flag of
tools/build_mod.py).

Read from the game's own files: where the game sets up a new file (the new-game sequence runs
Sequence/SetPouchAndStatusForGameStart once, between the title screen's map and Kokiri Forest), what that
module gives and sets, and that the sequence has a setter node for Bool, Int and String64 flags. Then the
edit: one more push per item and one more setter per flag, read back against the game's files; what is
refused, before anything is written; and whole builds. Only reads the game; the builds it runs go to a
temporary folder that is removed again.

    python tests/start_state_check.py "C:\\...\\romfs"
"""
import contextlib
import copy
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
import sizes  # noqa: E402
import start_state  # noqa: E402
from formats import zstd, byml, ainb, restbl  # noqa: E402

OPENING = 'Sequence/Opening.module.ainb'
MODULE_NAME = 'SetPouchAndStatusForGameStart.module'
# what the game's module gives and sets on a new file
GAME_ITEMS = [('Item_Wallet_Small', 1), ('Armor_Adult_Normal', 1), ('Obj_Armor_Child_Normal', 1),
              ('Obj_Armor_Adult_Normal', 1)]
GAME_STATUS = [('Life', 12), ('MaxLife', 12), ('MP', 0), ('MPEconomy', 0), ('MPMax', 0)]
OWN_NAME = GAME_ITEMS[:3]                 # the pushes that are an inventory item under their own name
# the test build's pair: an item seen in the menu, a flag seen in the forest
ITEM, FLAG = 'Item_Boomerang', 'KokiriForest_Npc_Kokiri_Mido_Child_Blocker'
# one flag of each type that can be set (name, type, value as given, value as written)
FLAGS = [(FLAG, 'Bool', 'false', False), ('AllSage_AwakeSageCount', 'Int', '3', 3),
         ('Sequence_CurrentBanc', 'String64', 'KokiriForest', 'KokiriForest')]
ITEMS = [(ITEM, 1), ('Item_ZeldaLetter', 1), ('Item_Hookshot', 1), ('Item_Longshot', 1), ('Item_Bomb', 20)]
# (arguments, what the message must say): refused before anything is written
REFUSED = [
    (['--start', 'Item_Longshot'], 'also give --start Item_Hookshot'),
    (['--start', 'Item_BombBag_Large', '--start', 'Item_BombBag_Small'], 'also give --start Item_BombBag_Medium'),
    (['--start', 'Item_Gauntlet_Goron'], 'under another name'),      # kept as armour
    (['--start', 'Item_Wallet_Small'], 'the game never gives it as an item'),
    (['--start', 'Item_StickBag_Small'], 'the game never gives it as an item'),
    (['--start', 'Item_Range_SlingShot'], 'under another name'),
    (['--start', 'Item_Range_Bow'], 'under another name'),
    (['--start', 'Item_NoSuchThing'], 'not an inventory item'),
    (['--start', ITEM, '--start', ITEM + '=2'], 'is given twice'),
    (['--start', ITEM + '=0'], 'expected ITEM or ITEM=N'),
    (['--start', ITEM + '=two'], 'expected ITEM or ITEM=N'),
    (['--start-flag', 'NoSuchFlag=true'], 'no flag of this name'),
    (['--start-flag', FLAG], 'expected NAME=VALUE'),
    (['--start-flag', FLAG + '=2'], 'takes true or false'),
    (['--start-flag', FLAG + '=true', '--start-flag', FLAG + '=false'], 'is given twice'),
    (['--start-flag', 'AllSage_AwakeSageCount=many'], 'takes a whole number'),
    (['--start-flag', 'AllSage_AwakeSageCount=4294967296'], 'outside a 32-bit number'),
    (['--start-flag', 'Sequence_CurrentBanc=' + 'x' * 64], 'at most 63 bytes'),
    (['--start-flag', 'PlayerStatus.MaxLife=80'], 'a field of a struct'),
    (['--start-flag', 'IsGet.Item_Boomerang=true'], 'a field of a struct'),
    (['--start-flag', 'SageOfForest_IsAfter_Step08_Exp=true'], 'it is a BoolExp'),
    (['--start-flag', 'GameOverReason=1'], 'its type is Enum'),
    (['--start-flag', 'Shop_SelectItemIndex=3'], 'not saved in the save slot'),
]
RESET_ALSO = 'EnteringStore_Hello_Standby'          # a saved Bool the game also resets at other times (9)


def check(name, ok):
    print('%-104s %s' % (name, 'OK' if ok else 'FAILED'))
    return ok


def tree(folder):
    return sorted(os.path.relpath(f, folder).replace(os.sep, '/')
                  for f in glob.glob(os.path.join(folder, '**', '*'), recursive=True) if os.path.isfile(f))


def refused(fn, *args):
    try:
        fn(*args)
    except SystemExit as e:
        return str(e)
    return None


def fixed(node):
    return {x.name: x.value for t in ainb.PARAM_TYPES for x in node.inputs[t]}


def main(romfs):
    d = zstd.Dictionaries.from_pack(open(os.path.join(romfs, 'Pack', 'ZsDic.pack.zs'), 'rb').read())
    plain = lambda path: zstd.decompress(open(os.path.join(romfs, *path.split('/')) + '.zs', 'rb').read(), d)   # noqa: E731
    loose = lambda path: open(os.path.join(romfs, *path.split('/')), 'rb').read()   # noqa: E731
    module, source = loose(start_state.MODULE), loose(start_state.SETTER_SOURCE)
    data = start_state.GameData(plain(start_state.GAME_DATA))
    rows = {r['__RowId'] for r in byml.loads(plain(start_state.ITEM_TABLE)).root}
    good = True

    # ---- the game's files: where a new file is set up
    opening = ainb.Ainb.read(loose(OPENING))
    kids = lambda doc, i: [l.node for l in doc.nodes[i].links[start_state.FLOW]]   # noqa: E731
    name = lambda doc, i: doc.nodes[i].name                                         # noqa: E731
    banc = [i for i, n in enumerate(opening.nodes) if n.name == 'ChangeBanc.module']
    setup = [i for i, n in enumerate(opening.nodes) if n.name == MODULE_NAME]
    request = [i for i, n in enumerate(opening.nodes) if n.name == 'SeqOneShotRequestEvent'
               and fixed(n).get('EventName') == 'Opening_LoadingKokiriForest']
    ok = len(banc) == len(setup) == len(request) == 1
    if ok:
        after = [l for l in opening.nodes[banc[0]].links[start_state.FLOW] if l.name == 'DoAfterDestroyBanc']
        order = kids(opening, after[0].node) if len(after) == 1 else []
        ok = order[:1] == setup and request[0] in order and opening.nodes[after[0].node].type == 2
    good &= check('the new-game sequence (%s) runs %s first once the old map is gone, before it asks for the '
                  'event that loads Kokiri Forest' % (OPENING.split('/')[-1], MODULE_NAME), ok)
    users = sorted(f for f in os.listdir(os.path.join(romfs, 'Sequence')) if f.endswith('.ainb')
                   and any(n.name in (MODULE_NAME, start_state.N_PUSH)
                           for n in ainb.Ainb.read(loose('Sequence/' + f)).nodes))
    good &= check('  no other sequence runs that module or pushes items (%s)' % ', '.join(users),
                  users == sorted([OPENING.split('/')[-1], start_state.MODULE.split('/')[-1]]))
    doc = ainb.Ainb.read(module)
    status = [(fixed(n)['GameDataName'], fixed(n)['Value']) for n in doc.nodes if n.name == start_state.N_STATUS]
    good &= check('  it gives the small wallet and the three tunics and sets three hearts and no magic '
                  '(%d pushes, %d sets on PlayerStatus), and sets no plain flag'
                  % (len(GAME_ITEMS), len(GAME_STATUS)),
                  start_state.read(module) == (GAME_ITEMS, []) and status == GAME_STATUS and doc.write() == module)
    good &= check('  every push names an item of the item table; %d of the %d are in the inventory under their '
                  'own name (IsGet.<item>, PouchData.<item>.StockNum)' % (len(OWN_NAME), len(GAME_ITEMS)),
                  all(x in rows for x, _ in GAME_ITEMS)
                  and [x for x in GAME_ITEMS if data.owns(x[0])] == OWN_NAME)
    templates = start_state.setter_templates(source)
    good &= check('  the sequence has a setter for Bool, Int and String64 flags (%s uses all three): flag name, '
                  'value, nothing linked' % start_state.SETTER_SOURCE.split('/')[-1],
                  set(templates) == set(start_state.SETTERS)
                  and all(set(fixed(n)) == {'GameDataIndex', 'GameDataFullName', 'Value'}
                          and fixed(n)['GameDataIndex'] == -1 for n in templates.values()))
    mido = data.find(FLAG)
    good &= check('  a flag nothing sets is its default on a new file: %s is a saved Bool, true by default'
                  % FLAG, bool(mido) and mido[0] == 'Bool' and mido[1]['DefaultValue'] is True
                  and int(mido[1]['SaveFileIndex']) == start_state.SLOT_SAVE
                  and int(mido[1]['ResetTypeValue']) == start_state.RESET_NEW_GAME_ONLY
                  and not data.is_member(FLAG))
    good &= check('  the test item %s is an inventory item under its own name' % ITEM,
                  ITEM in rows and data.owns(ITEM))

    # ---- the edit, read back
    items = start_state.parse_items(['%s=%d' % x if x[1] != 1 else x[0] for x in ITEMS])
    start_state.check_items(items, data, rows, build_mod.NEVER_GIVEN, build_mod.UPGRADE_FAMILIES)
    flags = start_state.check_flags(start_state.parse_flags(['%s=%s' % (n, v) for n, _, v, _ in FLAGS]), data)
    good &= check('%d items and %d flags are accepted: a count, a family with every level, one flag of each type'
                  % (len(ITEMS), len(FLAGS)),
                  items == ITEMS and flags == [(n, k, w, None) for n, k, _, w in FLAGS])
    new, said = start_state.edit(module, source, items, flags)
    back = ainb.Ainb.read(new)
    n0 = len(doc.nodes)
    good &= check('the module then gives and sets them after the game\'s own, and still writes back the same '
                  '(%d -> %d bytes, %d -> %d nodes)' % (len(module), len(new), n0, len(back.nodes)),
                  start_state.read(new) == (GAME_ITEMS + ITEMS, [(n, w) for n, _, _, w in FLAGS])
                  and back.write() == new and len(back.nodes) == n0 + len(ITEMS) + len(FLAGS)
                  and len(said) == len(ITEMS) + len(FLAGS))
    game_kept = all(start_state._node(o) == start_state._node(n) for i, (o, n) in enumerate(zip(doc.nodes, back.nodes))
                    if i not in (start_state._group(doc, start_state.N_PUSH), start_state._group(doc, start_state.N_STATUS)))
    pushes, sets = start_state._group(back, start_state.N_PUSH), None
    sets = [i for i, n in enumerate(back.nodes) if n.type == start_state.SIMULTANEOUS
            and any(name(back, k) == start_state.N_STATUS for k in kids(back, i))]
    good &= check('  the game\'s %d nodes are unchanged; the pushes hang under the game\'s group of pushes, the '
                  'setters under its group of status sets' % n0,
                  game_kept and kids(back, pushes)[-len(ITEMS):] == list(range(n0, n0 + len(ITEMS)))
                  and len(sets) == 1
                  and kids(back, sets[0])[-len(FLAGS):] == list(range(n0 + len(ITEMS), len(back.nodes))))
    wallet = doc.nodes[kids(doc, start_state._group(doc, start_state.N_PUSH))[0]]
    ok = True
    for k, (item, num) in enumerate(ITEMS):
        n = back.nodes[n0 + k]
        ok &= (n.name, n.name_hash, n.type) == (wallet.name, wallet.name_hash, wallet.type) \
            and fixed(n) == {'ActorName': start_state.ACTOR_FILE % item, 'Num': num} \
            and bytes(n.guid) != bytes(wallet.guid)
    for k, (flag, kind, _, value) in enumerate(FLAGS):
        n, t = back.nodes[n0 + len(ITEMS) + k], templates[kind]
        ok &= (n.name, n.name_hash, n.type) == (t.name, t.name_hash, t.type) \
            and fixed(n) == {'GameDataIndex': -1, 'GameDataFullName': flag, 'Value': value} \
            and type(fixed(n)['Value']) is type(value)
    good &= check('  every new node is the game\'s own node of its kind (the wallet\'s push, the three setters) '
                  'with its own item and count, or flag and value, and an id of its own',
                  ok and len({bytes(n.guid) for n in back.nodes}) == len(back.nodes))
    again, _ = start_state.edit(module, source, items, flags)
    good &= check('  the same request gives the same file', again == new)

    # the read-back notices what it is there for
    def spoiled(change):
        bad = ainb.Ainb.read(new)
        change(bad)
        return refused(start_state.read_back, module, source, bad.write(), items, flags)

    def set_input(node, key, value):
        for t in ainb.PARAM_TYPES:
            for x in node.inputs[t]:
                if x.name == key:
                    x.value = value

    cases = [
        ('a game node changed', lambda b: set_input(b.nodes[kids(b, pushes)[0]], 'Num', 2)),
        ('another item pushed', lambda b: set_input(b.nodes[n0], 'ActorName', start_state.ACTOR_FILE % 'Item_Hammer')),
        ('another count', lambda b: set_input(b.nodes[n0 + len(ITEMS) - 1], 'Num', 99)),
        ('another flag set', lambda b: set_input(b.nodes[n0 + len(ITEMS)], 'GameDataFullName', 'Sequence_IsChildhood')),
        ('another value', lambda b: set_input(b.nodes[n0 + len(ITEMS)], 'Value', True)),
        ('a new node not linked', lambda b: b.nodes[pushes].links[start_state.FLOW].pop()),
        ('a new node linked twice', lambda b: b.nodes[pushes].links[start_state.FLOW].append(
            copy.deepcopy(b.nodes[pushes].links[start_state.FLOW][-1]))),
        ('a node too many', lambda b: b.nodes.append(copy.deepcopy(b.nodes[n0]))),
        ('the entry point moved', lambda b: setattr(b.commands[0], 'left', 1)),
    ]
    missed = [what for what, change in cases if not (spoiled(change) or '').startswith('read-back:')]
    good &= check('the read-back stops the build on each of %d wrong files (a game node changed, another item, '
                  'count, flag or value, a node unlinked, linked twice or too many...)' % len(cases),
                  not missed and refused(start_state.read_back, module, source, new, items, flags) is None)

    # a flag the game also resets at other times is accepted with a note
    noted = start_state.check_flags([(RESET_ALSO, 'false')], data)
    good &= check('a flag the game also resets at other times (%s, reset type %d) is set with a note'
                  % (RESET_ALSO, int(data.find(RESET_ALSO)[1]['ResetTypeValue'])),
                  len(noted) == 1 and noted[0][:3] == (RESET_ALSO, 'Bool', False) and 'reset type' in noted[0][3])

    # ---- whole builds
    with tempfile.TemporaryDirectory() as tmp:
        def run(name, *args):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                build_mod.main(['--romfs', romfs, '--out', tmp, '--name', name] + list(args))
            return out.getvalue(), os.path.join(tmp, name, 'romfs')

        wrong = []
        for args, want in REFUSED:
            said = refused(run, 'no', *args)
            if not said or want not in said or not said.startswith(args[0]):
                wrong.append('%s -> %s' % (' '.join(args), said))
        good &= check('%d requests are refused with their reason and nothing is written (a level skipped, an item '
                      'never given, another inventory name, no item, twice, a wrong value, a struct field, '
                      'a BoolExp, another type, an unsaved flag)' % len(REFUSED),
                      not wrong and os.listdir(tmp) == [])
        for line in wrong:
            print('    ' + line)

        said, folder = run('start', '--start', ITEM, '--start-flag', FLAG + '=false')
        files = tree(folder)
        written = open(os.path.join(folder, *start_state.MODULE.split('/')), 'rb').read() \
            if start_state.MODULE in files else b''
        good &= check('a build with --start %s --start-flag %s=false writes the module and the size table, '
                      'nothing else' % (ITEM, FLAG),
                      files == sorted([start_state.MODULE, build_mod.RESTBL_PATH.replace(os.sep, '/')])
                      and bool(written) and start_state.read(written) == (GAME_ITEMS + [(ITEM, 1)], [(FLAG, False)])
                      and 'start item %s x1' % ITEM in said and 'start flag %s (Bool) = False' % FLAG in said)
        table = restbl.Restbl.read(zstd.decompress(open(os.path.join(folder, build_mod.RESTBL_PATH), 'rb').read(), d)) \
            if written else None
        game_table = restbl.Restbl.read(plain(build_mod.RESTBL_PATH[:-3]))
        good &= check('  the module is stored as the game stores it (not compressed) and its size table entry '
                      'follows the rule of the game\'s own (%d bytes: %d; now %d bytes: %d)'
                      % (len(module), game_table.get(start_state.MODULE), len(written),
                         table.get(start_state.MODULE) if table else -1),
                      bool(written) and written[:4] == b'AIB '
                      and game_table.get(start_state.MODULE) == sizes.entry(start_state.MODULE, module)
                      and table.get(start_state.MODULE) == sizes.entry(start_state.MODULE, written))
        kept = {f: open(os.path.join(folder, *f.split('/')), 'rb').read() for f in files}
        said = refused(run, 'start', '--start', 'Item_Longshot')
        good &= check('  a refused request leaves the earlier build of the same name untouched, byte for byte',
                      bool(said) and tree(folder) == files
                      and all(open(os.path.join(folder, *f.split('/')), 'rb').read() == v for f, v in kept.items()))
        _, folder = run('with', '--start', ITEM, '--start-flag', FLAG + '=false', '--fix', 'skippable_opening',
                        'KF_MIDO_CHEST_01=Item_Hookshot>Item_Longshot')
        alone = tree(run('without', '--fix', 'skippable_opening', 'KF_MIDO_CHEST_01=Item_Hookshot>Item_Longshot')[1])
        both = tree(folder)
        same = all(open(os.path.join(tmp, 'with', 'romfs', *f.split('/')), 'rb').read()
                   == open(os.path.join(tmp, 'without', 'romfs', *f.split('/')), 'rb').read()
                   for f in alone if f != build_mod.RESTBL_PATH.replace(os.sep, '/'))
        good &= check('  next to placements and a fix it adds only the module (%d files without it, %d with it), '
                      'and a build without it does not touch the module' % (len(alone), len(both)),
                      start_state.MODULE not in alone and sorted(alone + [start_state.MODULE]) == both and same)

    print()
    print('ALL OK' if good else 'SOMETHING FAILED')
    return 0 if good else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
